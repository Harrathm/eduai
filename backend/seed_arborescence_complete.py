#!/usr/bin/env python3
"""
seed_arborescence_complete.py
=============================
Insère l'arborescence pédagogique complète tunisienne dans la base de données :
  - Niveaux d'étude (NiveauEtude)
  - Matières par niveau (Matiere)

Usage :
    cd backend && python seed_arborescence_complete.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.db.session import engine, SessionLocal
from app.models import Base, NiveauEtude, Matiere


# ============================================================
# DÉFINITIONS — Niveaux d'étude (ordre = séquence d'affichage)
# ============================================================

NIVEAUX_DEFS = [
    # 2ème Cycle (Enseignement de Base)
    ("7ème année base", 1),
    ("8ème année base", 2),
    ("9ème année base", 3),
    # Secondaire — 1ère année (général)
    ("1ère année secondaire", 4),
    # Secondaire — 2ème année (filières)
    ("2ème année lettres", 5),
    ("2ème année sciences", 6),
    ("2ème année technologie", 7),
    ("2ème année économie et services", 8),
    # Secondaire — 3ème année (filières)
    ("3ème année lettres", 9),
    ("3ème année mathématiques", 10),
    ("3ème année sciences expérimentales", 11),
    ("3ème année économie et gestion", 12),
    ("3ème année sciences de l'informatique", 13),
    ("3ème année sciences techniques", 14),
    # Baccalauréat — 4ème année (filières)
    ("4ème année lettres", 15),
    ("4ème année mathématiques", 16),
    ("4ème année sciences expérimentales", 17),
    ("4ème année économie et gestion", 18),
    ("4ème année sciences de l'informatique", 19),
]


# ============================================================
# DÉFINITIONS — Matières par niveau
# ============================================================

MATIERES_DEFS = {
    # ─── 2ème Cycle (Base) ───
    "7ème année base": [
        "Langue Arabe",
        "Langue Française",
        "Langue Anglaise",
        "Histoire - Géographie",
        "Éducation Islamique",
        "Éducation Civique",
        "Mathématiques",
        "Sciences de la Vie et de la Terre",
        "Sciences Physiques",
        "Technologie",
        "Informatique",
        "Éducation Plastique",
        "Éducation Musicale",
    ],
    "8ème année base": [
        "Langue Arabe",
        "Langue Française",
        "Langue Anglaise",
        "Histoire - Géographie",
        "Éducation Islamique",
        "Éducation Civique",
        "Mathématiques",
        "Sciences de la Vie et de la Terre",
        "Sciences Physiques",
        "Technologie",
        "Informatique",
        "Éducation Plastique",
        "Éducation Musicale",
    ],
    "9ème année base": [
        "Langue Arabe",
        "Langue Française",
        "Langue Anglaise",
        "Histoire - Géographie",
        "Éducation Islamique",
        "Éducation Civique",
        "Mathématiques",
        "Sciences de la Vie et de la Terre",
        "Sciences Physiques",
        "Technologie",
        "Informatique",
        "Éducation Plastique",
        "Éducation Musicale",
    ],
    # ─── Secondaire — 1ère année (Général) ───
    "1ère année secondaire": [
        "Langue Arabe",
        "Langue Française",
        "Langue Anglaise",
        "Histoire - Géographie",
        "Éducation Islamique",
        "Éducation Civique",
        "Mathématiques",
        "Sciences de la Vie et de la Terre",
        "Sciences Physiques",
        "Technologie",
        "Informatique",
    ],
    # ─── Secondaire — 2ème année (Filières) ───
    "2ème année lettres": [
        "Langue Arabe",
        "Langue Française",
        "Langue Anglaise",
        "Histoire - Géographie",
        "Éducation Islamique",
        "Éducation Civique",
        "Mathématiques",
        "Sciences de la Vie et de la Terre",
        "Informatique",
    ],
    "2ème année sciences": [
        "Langue Arabe",
        "Langue Française",
        "Langue Anglaise",
        "Histoire - Géographie",
        "Éducation Islamique",
        "Éducation Civique",
        "Mathématiques",
        "Sciences de la Vie et de la Terre",
        "Sciences Physiques",
        "Technologie",
        "Informatique",
    ],
    "2ème année technologie": [
        "Langue Arabe",
        "Langue Française",
        "Langue Anglaise",
        "Histoire - Géographie",
        "Éducation Islamique",
        "Éducation Civique",
        "Mathématiques",
        "Sciences Physiques",
        "Technologie",
        "Informatique",
    ],
    "2ème année économie et services": [
        "Langue Arabe",
        "Langue Française",
        "Langue Anglaise",
        "Histoire - Géographie",
        "Éducation Islamique",
        "Éducation Civique",
        "Mathématiques",
        "Économie / T",
        "Informatique",
    ],
    # ─── Secondaire — 3ème année (Filières) ───
    "3ème année lettres": [
        "Langue Arabe",
        "Langue Française",
        "Langue Anglaise",
        "Histoire - Géographie",
        "Éducation Islamique",
        "Éducation Civique",
        "Philosophie",
        "Informatique",
    ],
    "3ème année mathématiques": [
        "Langue Arabe",
        "Langue Française",
        "Langue Anglaise",
        "Histoire - Géographie",
        "Éducation Islamique",
        "Philosophie",
        "Mathématiques",
        "Sciences de la Vie et de la Terre",
        "Sciences Physiques",
        "Informatique",
    ],
    "3ème année sciences expérimentales": [
        "Langue Arabe",
        "Langue Française",
        "Langue Anglaise",
        "Histoire - Géographie",
        "Éducation Islamique",
        "Philosophie",
        "Mathématiques",
        "Sciences de la Vie et de la Terre",
        "Sciences Physiques",
        "Informatique",
    ],
    "3ème année économie et gestion": [
        "Langue Arabe",
        "Langue Française",
        "Langue Anglaise",
        "Histoire - Géographie",
        "Philosophie",
        "Mathématiques",
        "Économie / T",
        "Informatique",
    ],
    "3ème année sciences de l'informatique": [
        "Langue Arabe",
        "Langue Française",
        "Langue Anglaise",
        "Histoire - Géographie",
        "Philosophie",
        "Mathématiques",
        "Sciences Physiques",
        "Informatique",
    ],
    "3ème année sciences techniques": [
        "Langue Arabe",
        "Langue Française",
        "Langue Anglaise",
        "Histoire - Géographie",
        "Philosophie",
        "Mathématiques",
        "Sciences Physiques",
        "Électricité / Mécanique",
        "Informatique",
    ],
    # ─── Baccalauréat — 4ème année (Filières) ───
    "4ème année lettres": [
        "Langue Arabe",
        "Langue Française",
        "Langue Anglaise",
        "Histoire - Géographie",
        "Éducation Islamique",
        "Philosophie",
        "Informatique",
    ],
    "4ème année mathématiques": [
        "Langue Arabe",
        "Langue Française",
        "Langue Anglaise",
        "Philosophie",
        "Mathématiques",
        "Sciences de la Vie et de la Terre",
        "Sciences Physiques",
        "Informatique",
    ],
    "4ème année sciences expérimentales": [
        "Langue Arabe",
        "Langue Française",
        "Langue Anglaise",
        "Philosophie",
        "Mathématiques",
        "Sciences de la Vie et de la Terre",
        "Sciences Physiques",
        "Informatique",
    ],
    "4ème année économie et gestion": [
        "Langue Arabe",
        "Langue Française",
        "Langue Anglaise",
        "Histoire - Géographie",
        "Philosophie",
        "Mathématiques",
        "Économie / T",
        "Informatique",
    ],
    "4ème année sciences de l'informatique": [
        "Langue Arabe",
        "Langue Française",
        "Langue Anglaise",
        "Philosophie",
        "Mathématiques",
        "Sciences Physiques",
        "Informatique",
    ],
}


# ============================================================
# SEED
# ============================================================

def seed_niveaux(db) -> dict:
    """Crée les niveaux d'étude. Retourne {nom: NiveauEtude}."""
    niveaux = {}
    for nom, ordre in NIVEAUX_DEFS:
        existing = db.query(NiveauEtude).filter(NiveauEtude.nom == nom).first()
        if existing:
            niveaux[nom] = existing
            print(f"  [exists] Niveau: {nom}")
            continue
        niv = NiveauEtude(nom=nom, ordre=ordre)
        db.add(niv)
        db.flush()
        niveaux[nom] = niv
        print(f"  [created] Niveau: {nom} (ordre={ordre})")
    db.commit()
    return niveaux


def seed_matieres(db, niveaux: dict) -> dict:
    """Crée les matières par niveau. Retourne {(niveau_nom, matiere_nom): Matiere}."""
    matieres = {}
    total_created = 0
    total_exists = 0
    for niveau_nom, matiere_list in MATIERES_DEFS.items():
        niv = niveaux.get(niveau_nom)
        if not niv:
            print(f"  [skip] Niveau introuvable: {niveau_nom}")
            continue
        for i, mat_nom in enumerate(matiere_list, 1):
            key = (niveau_nom, mat_nom)
            existing = db.query(Matiere).filter(
                Matiere.niveau_etude_id == niv.id,
                Matiere.nom == mat_nom,
            ).first()
            if existing:
                matieres[key] = existing
                total_exists += 1
                continue
            mat = Matiere(
                niveau_etude_id=niv.id,
                nom=mat_nom,
                remediation_threshold=40,
                standard_threshold=75,
                avance_threshold=75,
            )
            db.add(mat)
            db.flush()
            matieres[key] = mat
            total_created += 1
    db.commit()
    print(f"  Matières: {total_created} créées, {total_exists} existantes")
    return matieres


def main():
    print("=" * 60)
    print("Arborescence Pédagogique Complète — Tunisie")
    print("=" * 60)

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        print("\n[1/2] Niveaux d'étude…")
        niveaux = seed_niveaux(db)
        print(f"  Total: {len(niveaux)} niveaux")

        print("\n[2/2] Matières par niveau…")
        matieres = seed_matieres(db, niveaux)
        print(f"  Total: {len(matieres)} associations niveau×matière")

        # Résumé
        print("\n" + "=" * 60)
        print("RÉSUMÉ")
        print("=" * 60)
        for nom, ordre in NIVEAUX_DEFS:
            niv = niveaux.get(nom)
            if not niv:
                continue
            count = db.query(Matiere).filter(Matiere.niveau_etude_id == niv.id).count()
            print(f"  {order_prefix(ordre)} {nom}: {count} matières")
        print("=" * 60)
        print("Terminé ✓")

    except Exception as e:
        db.rollback()
        print(f"\nERREUR: {e}")
        raise
    finally:
        db.close()


def order_prefix(ordre: int) -> str:
    """Format: pad avec des espaces pour alignement."""
    return f"[{ordre:2d}]"


if __name__ == "__main__":
    main()
