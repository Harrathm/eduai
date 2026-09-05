# -*- coding: utf-8 -*-
"""
cleanup_packs.py - Clean up PackDefinition duplicates and normalize tiers.
Uses raw SQL to avoid ORM cascade issues with relationship delete-orphan.
Idempotent. Migrates abonnements + licences before deleting obsolete packs.
"""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timezone
from sqlalchemy import text
from app.db import SessionLocal

OFFICIAL_TIERS = ["Gratuit", "Basique", "Silver", "Golden"]

TIER_CANONICAL = {
    "gratuit": "Gratuit", "basic": "Basique", "basique": "Basique",
    "silver": "Silver", "golden": "Golden",
}


def canonical_tier(tier):
    return TIER_CANONICAL.get((tier or "").lower(), tier)


db = SessionLocal()
try:
    # 1. Normalize all tiers first
    result = db.execute(text("SELECT id, tier FROM pack_definitions"))
    updates = 0
    for row in result:
        ct = canonical_tier(row.tier)
        if ct != row.tier:
            db.execute(text("UPDATE pack_definitions SET tier = :tier WHERE id = :id"), {"tier": ct, "id": row.id})
            updates += 1
    print(f"Tier normalization: {updates} packs updated")

    # 2. Get groups
    result = db.execute(text("SELECT id, niveau_scolaire, tier FROM pack_definitions ORDER BY id"))
    groups = {}
    for row in result:
        groups.setdefault(row.niveau_scolaire, []).append({"id": row.id, "tier": row.tier})

    total_deleted = 0
    total_abo_migrated = 0
    total_lic_migrated = 0

    for niveau, packs in sorted(groups.items()):
        if len(packs) <= 4:
            continue

        tier_map = {}
        for p in packs:
            tier_map.setdefault(p["tier"], []).append(p)

        # For each official tier, keep the best pack
        to_keep = {}
        to_delete_ids = []

        for tier in OFFICIAL_TIERS:
            candidates = tier_map.get(tier, [])
            if not candidates:
                continue
            if len(candidates) == 1:
                to_keep[tier] = candidates[0]["id"]
                continue

            # Prefer pack with most abonnements, then licences, then lowest id
            best_id = candidates[0]["id"]
            best_abo = 0
            best_lic = 0
            for c in candidates:
                abo_r = db.execute(text("SELECT COUNT(*) FROM abonnements WHERE pack_id = :pid"), {"pid": c["id"]}).scalar()
                lic_r = db.execute(text("SELECT COUNT(*) FROM licences_ecole WHERE pack_id = :pid"), {"pid": c["id"]}).scalar()
                if (abo_r > best_abo) or (abo_r == best_abo and lic_r > best_lic) or (abo_r == best_abo and lic_r == best_lic and c["id"] < best_id):
                    best_id = c["id"]
                    best_abo = abo_r
                    best_lic = lic_r

            to_keep[tier] = best_id
            for c in candidates:
                if c["id"] != best_id:
                    to_delete_ids.append(c["id"])

        # Non-official tiers -> delete all
        for tier, candidates in tier_map.items():
            if tier not in OFFICIAL_TIERS:
                for c in candidates:
                    to_delete_ids.append(c["id"])

        # Migrate abonnements from deleted packs to kept packs
        now = datetime.now(timezone.utc).isoformat()
        for del_id in to_delete_ids:
            # Find the tier of this deleted pack
            del_tier = next((p["tier"] for p in packs if p["id"] == del_id), None)
            target_id = to_keep.get(del_tier)
            if not target_id or target_id == del_id:
                continue

            abo_result = db.execute(text("SELECT id FROM abonnements WHERE pack_id = :pid"), {"pid": del_id})
            abo_ids = [r.id for r in abo_result]
            if abo_ids:
                db.execute(
                    text("UPDATE abonnements SET pack_id = :target, updated_at = :now WHERE pack_id = :old"),
                    {"target": target_id, "now": now, "old": del_id},
                )
                total_abo_migrated += len(abo_ids)

            lic_result = db.execute(text("SELECT id FROM licences_ecole WHERE pack_id = :pid"), {"pid": del_id})
            lic_ids = [r.id for r in lic_result]
            if lic_ids:
                db.execute(
                    text("UPDATE licences_ecole SET pack_id = :target WHERE pack_id = :old"),
                    {"target": target_id, "old": del_id},
                )
                total_lic_migrated += len(lic_ids)

            # Delete licence_assignations that reference licences being moved
            for lic_id in lic_ids:
                db.execute(text("DELETE FROM licence_assignations WHERE licence_id = :lid"), {"lid": lic_id})

        # Delete packs (raw SQL, no ORM cascade)
        for del_id in to_delete_ids:
            db.execute(text("DELETE FROM abonnements WHERE pack_id = :pid"), {"pid": del_id})
            db.execute(text("DELETE FROM licence_assignations WHERE licence_id IN (SELECT id FROM licences_ecole WHERE pack_id = :pid)"), {"pid": del_id})
            db.execute(text("DELETE FROM licences_ecole WHERE pack_id = :pid"), {"pid": del_id})
            db.execute(text("DELETE FROM pack_definitions WHERE id = :pid"), {"pid": del_id})
            total_deleted += 1

    db.commit()

    print(f"\n=== SUMMARY ===")
    print(f"Packs deleted: {total_deleted}")
    print(f"Abonnements migrated: {total_abo_migrated}")
    print(f"Licences migrated: {total_lic_migrated}")

    total = db.execute(text("SELECT COUNT(*) FROM pack_definitions")).scalar()
    print(f"Total packs remaining: {total}")

    print("\n=== PACKS PER NIVEAU (after cleanup) ===")
    result = db.execute(text("SELECT niveau_scolaire, COUNT(*) as cnt FROM pack_definitions GROUP BY niveau_scolaire ORDER BY niveau_scolaire"))
    for row in result:
        mark = " *** DUPLICATE ***" if row.cnt > 4 else ""
        print(f"  [{row.cnt}] {row.niveau_scolaire}{mark}")

    print("\n=== PACKS FOR 'Bac Sciences Expérimentales' ===")
    result = db.execute(text(
        "SELECT p.id, p.nom, p.tier, p.prix_tnd, "
        "(SELECT COUNT(*) FROM abonnements a WHERE a.pack_id = p.id) as abo_count "
        "FROM pack_definitions p WHERE p.niveau_scolaire = 'Bac Sciences Expérimentales' ORDER BY p.tier"
    ))
    for row in result:
        print(f"  Pack {row.id}: nom={repr(row.nom)}, tier={repr(row.tier)}, prix={row.prix_tnd}, abonnements={row.abo_count}")

    print("\n=== STUDENT2@EDUAI.EDU PACKS (verification) ===")
    result = db.execute(text(
        "SELECT p.id, p.nom, p.tier, p.niveau_scolaire, p.prix_tnd "
        "FROM pack_definitions p "
        "WHERE p.niveau_scolaire = 'Bac Sciences Expérimentales' AND p.est_actif = true "
        "ORDER BY p.tier"
    ))
    for row in result:
        print(f"  Pack {row.id}: {repr(row.nom)}, tier={repr(row.tier)}, prix={row.prix_tnd}")

finally:
    db.close()
