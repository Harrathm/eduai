"""
Module B — Abonnements (packs + souscription + upgrade/downgrade)
- Packs scoped by niveau_scolaire of the student
- Upgrade = immediate
- Downgrade = deferred to next trimester
- Trimester auto-apply on login
"""
from datetime import datetime, timedelta, timezone, date
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.db import get_db
from app.auth import get_current_user
from app.deps import set_tenant_context, require_admin, require_super_admin, get_user_role
from app.models import (
    User, PackDefinition, Abonnement,
    CompteFamille, FamilleEnfant,
)
from app.schemas import (
    PackDefinitionCreate, PackDefinitionRead, PackDefinitionUpdate,
    AbonnementCreate, AbonnementRead, ChangeTierRequest,
)

router = APIRouter(tags=["Module B - Abonnements"])

utcnow = lambda: datetime.now(timezone.utc)

TIER_ORDER = {"gratuit": 0, "basique": 1, "silver": 2, "golden": 3}

TUNISIA_TRIMESTERS_2026_2027 = [
    (date(2026, 9, 15), date(2026, 12, 19)),   # T1
    (date(2027, 1, 5),  date(2027, 3, 27)),     # T2
    (date(2027, 4, 6),  date(2027, 6, 19)),     # T3
    (date(2027, 9, 15), date(2027, 12, 19)),    # T1 next year
    (date(2028, 1, 5),  date(2028, 3, 27)),     # T2 next year
]

QUOTA_INFO = {
    "gratuit": "3 lecons / trimestre",
    "basique": "2 matieres au choix",
    "silver": "4 matieres au choix",
    "golden": "Acces illimite + Soft Skills",
}


def _next_trimester_start(from_date: date) -> date:
    """Return the start date of the next trimester after from_date."""
    for t_start, t_end in TUNISIA_TRIMESTERS_2026_2027:
        if from_date <= t_end:
            idx = TUNISIA_TRIMESTERS_2026_2027.index((t_start, t_end))
            if idx + 1 < len(TUNISIA_TRIMESTERS_2026_2027):
                return TUNISIA_TRIMESTERS_2026_2027[idx + 1][0]
            return date(2028, 9, 15)
    return date(2028, 9, 15)


def _apply_scheduled_tier_changes(db: Session) -> int:
    """Apply any deferred tier changes whose effective date has passed. Returns count applied."""
    now = utcnow()
    pending = db.query(Abonnement).filter(
        Abonnement.scheduled_tier.isnot(None),
        Abonnement.scheduled_effective_date.isnot(None),
        Abonnement.scheduled_effective_date <= now,
        Abonnement.statut == "actif",
    ).all()

    count = 0
    for ab in pending:
        target_pack = db.query(PackDefinition).filter(
            PackDefinition.tier == ab.scheduled_tier,
            PackDefinition.niveau_scolaire == ab.pack.niveau_scolaire,
            PackDefinition.est_actif == True,
        ).first()
        if target_pack:
            ab.pack_id = target_pack.id
        ab.scheduled_tier = None
        ab.scheduled_effective_date = None
        ab.updated_at = now
        count += 1

    if count:
        db.commit()
    return count


def _serialize_pack(pack: Optional[PackDefinition]) -> Optional[dict]:
    if not pack:
        return None
    # matieres can be {"matieres": [...]} or [...] or None
    raw = pack.matieres
    if isinstance(raw, dict):
        matieres = raw.get("matieres", [])
    elif isinstance(raw, list):
        matieres = raw
    else:
        matieres = []
    return {
        "id": pack.id,
        "nom": pack.nom,
        "description": pack.description,
        "tier": pack.tier,
        "prix_tnd": float(pack.prix_tnd) if pack.prix_tnd else 0,
        "niveau_scolaire": pack.niveau_scolaire,
        "features": pack.features,
        "matieres": matieres,
    }


# ============================================================
# PACKS
# ============================================================

@router.get("/abonnements/packs")
def list_packs(
    tier: Optional[str] = None,
    niveau_scolaire: Optional[str] = None,
    est_actif: bool = True,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(set_tenant_context),
):
    q = db.query(PackDefinition).filter(PackDefinition.est_actif == est_actif)
    if tier:
        q = q.filter(PackDefinition.tier == tier)
    if niveau_scolaire:
        q = q.filter(PackDefinition.niveau_scolaire == niveau_scolaire)
    total = q.count()
    items = q.order_by(PackDefinition.prix_tnd).offset(skip).limit(limit).all()

    # Check active abonnement
    active_abo_pack_id = None
    active_abo = db.query(Abonnement).filter(
        Abonnement.user_id == current_user.id,
        Abonnement.statut.in_(["actif", "grace"]),
    ).first()
    if active_abo:
        active_abo_pack_id = active_abo.pack_id

    serialized = []
    for p in items:
        d = _serialize_pack(p)
        d["validity_duration_days"] = 90 if p.tier != "gratuit" else 365
        d["currency"] = "TND"
        d["already_included_by_school"] = False
        d["is_current"] = p.id == active_abo_pack_id
        serialized.append(d)

    return {"total": total, "skip": skip, "limit": limit, "items": serialized}


@router.get("/abonnements/packs/{pack_id}", response_model=PackDefinitionRead)
def get_pack(
    pack_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(set_tenant_context),
):
    pack = db.query(PackDefinition).filter(PackDefinition.id == pack_id).first()
    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found")
    return pack


@router.post("/abonnements/packs/{pack_id}/purchase")
def purchase_pack(
    pack_id: int,
    body: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(set_tenant_context),
):
    """Purchase a pack with selected matieres.

    If the buyer is a parent and provides `eleve_id`, the pack is attributed
    to the child and the family discount (remise_pct) is applied to the price.
    """
    pack = db.query(PackDefinition).filter(PackDefinition.id == pack_id).first()
    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found")

    matieres = body.get("matieres")
    eleve_id = body.get("eleve_id")

    # SECURITY FIX #4 : gate RBAC strict — seuls les élèves (pour eux-mêmes)
    # et les parents (pour un enfant lié, eleve_id requis) peuvent souscrire.
    # Un teacher/admin ne doit jamais pouvoir créer d'Abonnement étudiant
    # pour lui-même (corruption de l'ABAC basé sur Abonnement/PackDefinition).
    buyer_role = get_user_role(current_user)
    if buyer_role not in ("student", "parent"):
        raise HTTPException(
            status_code=403,
            detail="Seuls les élèves ou les parents peuvent souscrire à un abonnement",
        )

    # Determine beneficiary and apply family discount
    beneficiary_id = current_user.id
    remise_pct = 0.0
    if buyer_role == "parent":
        if not eleve_id:
            raise HTTPException(
                status_code=400,
                detail="Un parent doit fournir eleve_id pour souscrire pour son enfant",
            )
        from app.models import ParentEnfant
        link = db.query(ParentEnfant).filter(
            ParentEnfant.parent_user_id == current_user.id,
            ParentEnfant.eleve_id == eleve_id,
        ).first()
        if not link:
            raise HTTPException(status_code=403, detail="Cet eleve n est pas lie a votre compte parent")
        beneficiary_id = eleve_id
        # Lookup family discount
        cf = db.query(CompteFamille).filter(CompteFamille.parent_id == current_user.id).first()
        if cf:
            fe = db.query(FamilleEnfant).filter(
                FamilleEnfant.compte_famille_id == cf.id,
                FamilleEnfant.eleve_id == eleve_id,
            ).first()
            if fe:
                remise_pct = fe.remise_pct
    elif eleve_id and eleve_id != current_user.id:
        # Un élève ne peut souscrire QUE pour lui-même (jamais pour un tiers)
        raise HTTPException(
            status_code=403,
            detail="Un eleve ne peut souscrire que pour lui-meme",
        )

    existing = db.query(Abonnement).filter(
        Abonnement.user_id == beneficiary_id,
        Abonnement.statut.in_(["actif", "grace"]),
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="You already have an active subscription")

    now = utcnow()
    duration_days = 90 if pack.tier != "gratuit" else 365
    abonnement = Abonnement(
        user_id=beneficiary_id,
        pack_id=pack.id,
        statut="actif",
        debut=now,
        fin=now + timedelta(days=duration_days),
        matieres_config={"matieres": matieres} if matieres else None,
    )
    db.add(abonnement)
    db.flush()

    # Debit wallet of the buyer (parent) with family discount applied
    price = float(pack.prix_tnd or 0)
    final_price = round(price * (1 - remise_pct / 100), 3) if remise_pct > 0 else price
    if final_price > 0:
        from app.services.wallet import debit_dt, InsufficientCreditsError
        from decimal import Decimal
        try:
            debit_dt(
                db, current_user.id, Decimal(str(final_price)),
                source="abonnement",
                reason=f"Achat pack {pack.nom} (remise {remise_pct}%)" if remise_pct else f"Achat pack {pack.nom}",
                commit=False,
            )
        except InsufficientCreditsError:
            raise HTTPException(
                status_code=402,
                detail=f"Solde insuffisant. Prix: {final_price} TND"
                + (f" (remise famille {remise_pct}% appliquee)" if remise_pct else ""),
            )

    # Auto-enroll beneficiary in published courses matching selected matieres + niveau.
    # matieres_config contient des IDs de la table Matiere → on les résout en noms
    # normalisés (sans accents, minuscules) pour les comparer à Course.category
    # qui stocke le nom libre (ex: "Mathématiques").
    if matieres:
        from app.models import Course, CourseEnrollment, Matiere
        from app.services.course_access import _normalize_niveau

        beneficiary = db.query(User).filter(User.id == beneficiary_id).first()
        niveau = beneficiary.niveau_scolaire if beneficiary else None
        if niveau:
            # 1. Résout les IDs → noms de matières normalisés (tolère les noms bruts)
            ids = [m for m in matieres if isinstance(m, int) or str(m).strip().isdigit()]
            names = [m for m in matieres if isinstance(m, str) and not m.strip().isdigit()]
            if ids:
                names.extend(m.nom for m in db.query(Matiere).filter(Matiere.id.in_(ids)).all())
            allowed = {_normalize_niveau(n) for n in names}
            niveau_norm = _normalize_niveau(niveau)

            # 2. Candidats : cours publiés du niveau de l'élève, filtrés en Python
            #    sur la catégorie normalisée (SQL ne peut pas normaliser les accents).
            candidates = db.query(Course).filter(
                Course.status == "published",
                Course.niveau_scolaire.isnot(None),
                Course.category.isnot(None),
            ).all()
            enrolled_count = 0
            for course in candidates:
                if _normalize_niveau(course.niveau_scolaire) != niveau_norm:
                    continue
                if _normalize_niveau(course.category) not in allowed:
                    continue
                existing_enrollment = db.query(CourseEnrollment).filter(
                    CourseEnrollment.student_id == beneficiary_id,
                    CourseEnrollment.course_id == course.id,
                ).first()
                if not existing_enrollment:
                    db.add(CourseEnrollment(
                        student_id=beneficiary_id,
                        course_id=course.id,
                    ))
                    enrolled_count += 1
            if enrolled_count:
                db.flush()

    db.commit()
    db.refresh(abonnement)
    return {
        "id": abonnement.id,
        "pack_id": abonnement.pack_id,
        "statut": abonnement.statut,
        "debut": abonnement.debut.isoformat(),
        "fin": abonnement.fin.isoformat(),
        "matieres_config": abonnement.matieres_config,
        "remise_pct": remise_pct,
        "price_paid": final_price,
    }


@router.post("/abonnements/packs", response_model=PackDefinitionRead)
def create_pack(
    pack_in: PackDefinitionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    pack = PackDefinition(**pack_in.model_dump())
    db.add(pack)
    db.commit()
    db.refresh(pack)
    return pack


@router.put("/abonnements/packs/{pack_id}", response_model=PackDefinitionRead)
def update_pack(
    pack_id: int,
    pack_update: PackDefinitionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    pack = db.query(PackDefinition).filter(PackDefinition.id == pack_id).first()
    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found")
    for field, value in pack_update.model_dump(exclude_unset=True).items():
        setattr(pack, field, value)
    db.commit()
    db.refresh(pack)
    return pack


# ============================================================
# MON PACK (scoped by niveau_scolaire)
# ============================================================

@router.get("/abonnements/mon-pack")
def mon_pack(
    db: Session = Depends(get_db),
    current_user: User = Depends(set_tenant_context),
):
    """Return the student's current pack, available packs scoped by niveau_scolaire, and any scheduled change."""
    _apply_scheduled_tier_changes(db)

    niveau = getattr(current_user, "niveau_scolaire", None)

    active_abo = db.query(Abonnement).filter(
        Abonnement.user_id == current_user.id,
        Abonnement.statut.in_(["actif", "grace"]),
    ).order_by(Abonnement.created_at.desc()).first()

    current_tier = active_abo.pack.tier if active_abo and active_abo.pack else "gratuit"
    current_pack = _serialize_pack(active_abo.pack) if active_abo else None

    abonnement_data = None
    if active_abo:
        abonnement_data = {
            "id": active_abo.id,
            "statut": active_abo.statut,
            "debut": active_abo.debut.isoformat() if active_abo.debut else None,
            "fin": active_abo.fin.isoformat() if active_abo.fin else None,
            "grace_fin": active_abo.grace_fin.isoformat() if active_abo.grace_fin else None,
        }

    scheduled_change = None
    if active_abo and active_abo.scheduled_tier:
        scheduled_change = {
            "target_tier": active_abo.scheduled_tier,
            "effective_date": active_abo.scheduled_effective_date.isoformat() if active_abo.scheduled_effective_date else None,
        }

    q_packs = db.query(PackDefinition).filter(PackDefinition.est_actif == True)
    if niveau:
        q_packs = q_packs.filter(PackDefinition.niveau_scolaire == niveau)
    available = q_packs.order_by(PackDefinition.prix_tnd).all()

    return {
        "current_tier": current_tier,
        "current_pack": current_pack,
        "abonnement": abonnement_data,
        "available_packs": [_serialize_pack(p) for p in available],
        "scheduled_change": scheduled_change,
        "niveau_scolaire": niveau,
        "quota_info": QUOTA_INFO,
    }


# ============================================================
# ABONNEMENTS (subscribe)
# ============================================================

@router.post("/abonnements", response_model=AbonnementRead)
def subscribe(
    body: AbonnementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(set_tenant_context),
):
    pack = db.query(PackDefinition).filter(PackDefinition.id == body.pack_id).first()
    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found")

    existing = db.query(Abonnement).filter(
        Abonnement.user_id == current_user.id,
        Abonnement.statut.in_(["actif", "grace"]),
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="You already have an active subscription")

    now = utcnow()
    duration_days = 90 if pack.tier != "gratuit" else 365
    abonnement = Abonnement(
        user_id=current_user.id,
        pack_id=pack.id,
        statut="actif",
        debut=now,
        fin=now + timedelta(days=duration_days),
    )
    db.add(abonnement)
    db.commit()
    db.refresh(abonnement)
    return abonnement


@router.get("/abonnements/mes-abonnements")
def my_abonnements(
    eleve_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(set_tenant_context),
):
    """Abonnements de l'utilisateur courant.

    Écart#2 FIX — un parent qui consulte la page pack d'un enfant doit voir
    les abonnements de l'ENFANT (portés par user_id=eleve_id), pas les siens
    (toujours vides). Avec eleve_id + rôle parent, on vérifie le lien
    ParentEnfant puis on renvoie les abonnements de l'enfant.
    """
    _apply_scheduled_tier_changes(db)

    target_user_id = current_user.id
    if eleve_id is not None and get_user_role(current_user) == "parent":
        from app.models import ParentEnfant

        link = db.query(ParentEnfant).filter(
            ParentEnfant.parent_user_id == current_user.id,
            ParentEnfant.eleve_id == eleve_id,
        ).first()
        if not link:
            raise HTTPException(
                status_code=403,
                detail="Cet eleve n'est pas rattache a votre compte parent.",
            )
        target_user_id = eleve_id

    items = db.query(Abonnement).filter(
        Abonnement.user_id == target_user_id
    ).order_by(Abonnement.created_at.desc()).all()

    result = []
    for ab in items:
        d = {
            "id": ab.id,
            "user_id": ab.user_id,
            "pack_id": ab.pack_id,
            "statut": ab.statut,
            "debut": ab.debut.isoformat() if ab.debut else None,
            "fin": ab.fin.isoformat() if ab.fin else None,
            "grace_fin": ab.grace_fin.isoformat() if ab.grace_fin else None,
            "scheduled_tier": ab.scheduled_tier,
            "scheduled_effective_date": ab.scheduled_effective_date.isoformat() if ab.scheduled_effective_date else None,
            "matieres_config": ab.matieres_config,
            "created_at": ab.created_at.isoformat() if ab.created_at else None,
            "updated_at": ab.updated_at.isoformat() if ab.updated_at else None,
            "pack": None,
        }
        if ab.pack:
            d["pack"] = _serialize_pack(ab.pack)
        result.append(d)

    return {"total": len(result), "items": result}


# ============================================================
# TIER CHANGE (upgrade immediate, downgrade deferred)
# ============================================================

@router.post("/abonnements/change-tier")
def change_tier(
    body: ChangeTierRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(set_tenant_context),
):
    """Upgrade = immediate. Downgrade = scheduled to next trimester start."""
    _apply_scheduled_tier_changes(db)

    active_abo = db.query(Abonnement).filter(
        Abonnement.user_id == current_user.id,
        Abonnement.statut.in_(["actif", "grace"]),
    ).first()

    new_pack = db.query(PackDefinition).filter(PackDefinition.id == body.target_pack_id).first()
    if not new_pack:
        raise HTTPException(status_code=404, detail="Target pack not found")

    # Aucun abonnement actif (ex: pack invalidé) → on en crée un nouveau directement
    if not active_abo:
        previous = db.query(Abonnement).filter(
            Abonnement.user_id == current_user.id,
        ).order_by(Abonnement.created_at.desc()).first()
        now = utcnow()
        duration_days = 90 if new_pack.tier != "gratuit" else 365
        new_abo = Abonnement(
            user_id=current_user.id,
            pack_id=new_pack.id,
            statut="actif",
            debut=now,
            fin=now + timedelta(days=duration_days),
            matieres_config=previous.matieres_config if previous else None,
        )
        db.add(new_abo)
        db.commit()
        db.refresh(new_abo)
        return {
            "message": "New subscription created",
            "abonnement_id": new_abo.id,
            "new_tier": new_pack.tier,
        }

    if active_abo.pack:
        niveau = active_abo.pack.niveau_scolaire
        if new_pack.niveau_scolaire != niveau:
            raise HTTPException(status_code=400, detail="Target pack must match your niveau_scolaire")

    current_rank = TIER_ORDER.get(active_abo.pack.tier if active_abo.pack else "gratuit", 0)
    target_rank = TIER_ORDER.get(new_pack.tier, 0)

    now = utcnow()

    if target_rank > current_rank:
        active_abo.pack_id = new_pack.id
        active_abo.scheduled_tier = None
        active_abo.scheduled_effective_date = None
        active_abo.updated_at = now
        db.commit()
        db.refresh(active_abo)
        return {"message": "Upgrade applied immediately", "abonnement_id": active_abo.id, "new_tier": new_pack.tier}
    elif target_rank < current_rank:
        next_start = _next_trimester_start(now.date())
        active_abo.scheduled_tier = new_pack.tier
        active_abo.scheduled_effective_date = datetime.combine(next_start, datetime.min.time())
        active_abo.updated_at = now
        db.commit()
        db.refresh(active_abo)
        return {"message": "Downgrade scheduled", "abonnement_id": active_abo.id, "scheduled_tier": new_pack.tier, "effective_date": next_start.isoformat()}
    else:
        raise HTTPException(status_code=400, detail="Cannot change to the same tier")


@router.delete("/abonnements/cancel-scheduled-change")
def cancel_scheduled_change(
    db: Session = Depends(get_db),
    current_user: User = Depends(set_tenant_context),
):
    """Cancel any pending deferred downgrade."""
    active_abo = db.query(Abonnement).filter(
        Abonnement.user_id == current_user.id,
        Abonnement.statut.in_(["actif", "grace"]),
    ).first()
    if not active_abo:
        raise HTTPException(status_code=404, detail="No active subscription found")
    if not active_abo.scheduled_tier:
        raise HTTPException(status_code=400, detail="No scheduled change to cancel")

    active_abo.scheduled_tier = None
    active_abo.scheduled_effective_date = None
    active_abo.updated_at = utcnow()
    db.commit()
    return {"message": "Scheduled change cancelled"}


@router.get("/abonnements/scheduled-changes")
def get_scheduled_changes(
    db: Session = Depends(get_db),
    current_user: User = Depends(set_tenant_context),
):
    """Check for pending deferred tier changes."""
    _apply_scheduled_tier_changes(db)

    active_abo = db.query(Abonnement).filter(
        Abonnement.user_id == current_user.id,
        Abonnement.statut.in_(["actif", "grace"]),
    ).first()
    if not active_abo or not active_abo.scheduled_tier:
        return {"scheduled_change": None}

    return {
        "scheduled_change": {
            "target_tier": active_abo.scheduled_tier,
            "effective_date": active_abo.scheduled_effective_date.isoformat() if active_abo.scheduled_effective_date else None,
        }
    }


# ============================================================
# CANCEL ABONNEMENT
# ============================================================

@router.put("/abonnements/{abonnement_id}/cancel", response_model=AbonnementRead)
def cancel_abonnement(
    abonnement_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(set_tenant_context),
):
    ab = db.query(Abonnement).filter(
        Abonnement.id == abonnement_id,
        Abonnement.user_id == current_user.id,
    ).first()
    if not ab:
        raise HTTPException(status_code=404, detail="Abonnement not found")
    if ab.statut not in ("actif", "grace"):
        raise HTTPException(status_code=400, detail="Abonnement already cancelled/expired")

    now = utcnow()
    if ab.pack and ab.pack.tier != "gratuit":
        ab.statut = "grace"
        ab.grace_fin = now + timedelta(days=7)
    else:
        ab.statut = "annule"
        ab.fin = now
    ab.scheduled_tier = None
    ab.scheduled_effective_date = None
    ab.updated_at = utcnow()
    db.commit()
    db.refresh(ab)
    return ab
