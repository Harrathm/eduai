"""
Seed arborescence pedagogique officielle tunisienne (noms arabes exacts).
Remplace les donnees existantes dans niveaux_etude et matieres.

LANGUES = communes a tous les niveaux (type_matiere='langue')
SPECIALITES = specifiques a chaque filiere (type_matiere='specialite')
Bac = meme specialites que la 3eme correspondante.

Usage:
    cd backend
    python seed_arborescence_officielle.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if not os.environ.get("DATABASE_URL"):
    os.environ["DATABASE_URL"] = "postgresql+pg8000://postgres:gill4264@localhost:5432/eduai"

from sqlalchemy import text
from app.db.session import engine, SessionLocal
from app.models import Base, NiveauEtude, Matiere


# ============================================================
# LANGUES — communes a TOUS les niveaux
# ============================================================
LANGUES = ["العربية", "الفرنسية", "الانقليزية", "الإسبانية", "الألمانية"]

# ============================================================
# SPECIALITES par niveau (type_matiere='specialite')
# ============================================================
SPECIALITES = {
    # --- 7eme, 8eme, 9eme Base : toutes les memes specialites ---
    "7ème Année Base": [
        "تاريخ / جغرافيا", "تفكير إسلامي", "تربية مدنية",
        "رياضيات", "علوم طبيعية", "علوم فيزيائية",
        "تكنولوجيا", "إعلامية", "تربية تشكيلية", "تربية موسيقية",
    ],
    "8ème Année Base": [
        "تاريخ / جغرافيا", "تفكير إسلامي", "تربية مدنية",
        "رياضيات", "علوم طبيعية", "علوم فيزيائية",
        "تكنولوجيا", "إعلامية", "تربية تشكيلية", "تربية موسيقية",
    ],
    "9ème Année Base": [
        "تاريخ / جغرافيا", "تفكير إسلامي", "تربية مدنية",
        "رياضيات", "علوم طبيعية", "علوم فيزيائية",
        "تكنولوجيا", "إعلامية", "تربية تشكيلية", "تربية موسيقية",
    ],
    # --- 1ere Annee Secondaire ---
    "1ère Année Secondaire": [
        "تاريخ / جغرافيا", "تفكير إسلامي", "تربية مدنية",
        "رياضيات", "علوم طبيعية", "علوم فيزيائية",
        "تكنولوجيا", "إعلامية",
    ],
    # --- 2eme Annee : specialites par filiere ---
    "2ème Lettres": [
        "تاريخ / جغرافيا", "تفكير إسلامي", "تربية مدنية",
        "رياضيات", "علوم طبيعية", "إعلامية",
    ],
    "2ème Sciences": [
        "تاريخ / جغرافيا", "تفكير إسلامي", "تربية مدنية",
        "رياضيات", "علوم طبيعية", "علوم فيزيائية",
        "تكنولوجيا", "إعلامية",
    ],
    "2ème Technologie": [
        "تاريخ / جغرافيا", "تفكير إسلامي", "تربية مدنية",
        "رياضيات", "علوم فيزيائية", "تكنولوجيا", "إعلامية",
    ],
    "2ème Économie et Services": [
        "تاريخ / جغرافيا", "تفكير إسلامي", "تربية مدنية",
        "رياضيات", "اقتصاد / تصرف", "إعلامية",
    ],
    # --- 3eme Annee : specialites par filiere ---
    "3ème Lettres": [
        "تاريخ / جغرافيا", "تفكير إسلامي", "تربية مدنية",
        "فلسفة", "إعلامية",
    ],
    "3ème Mathématiques": [
        "تاريخ / جغرافيا", "تفكير إسلامي",
        "فلسفة", "رياضيات", "علوم طبيعية", "علوم فيزيائية", "إعلامية",
    ],
    "3ème Sciences Expérimentales": [
        "تاريخ / jغرافيا", "تفكير إسلامي",
        "فلسفة", "رياضيات", "علوم طبيعية", "علوم فيزيائية", "إعلامية",
    ],
    "3ème Économie et Gestion": [
        "تاريخ / جغرافيا", "فلسفة",
        "رياضيات", "اقتصاد / تصرف", "إعلامية",
    ],
    "3ème Sciences de l'Informatique": [
        "تاريخ / جغرافيا", "فلسفة",
        "رياضيات", "علوم فيزيائية", "إعلامية",
    ],
    "3ème Sciences Techniques": [
        "تاريخ / جغرافيا", "فلسفة",
        "رياضيات", "علوم فيزيائية", "كهرباء / ميكانيك", "إعلامية",
    ],
    # --- Bac = meme specialites que 3eme correspondante ---
    "Bac Lettres": [
        "تاريخ / جغرافيا", "تفكير إسلامي", "تربية مدنية",
        "فلسفة", "إعلامية",
    ],
    "Bac Mathématiques": [
        "تاريخ / جغرافيا", "تفكير إسلامي",
        "فلسفة", "رياضيات", "علوم طبيعية", "علوم فيزيائية", "إعلامية",
    ],
    "Bac Sciences Expérimentales": [
        "تاريخ / jغرافيا", "تفكير إسلامي",
        "فلسفة", "رياضيات", "علوم طبيعية", "علوم فيزيائية", "إعلامية",
    ],
    "Bac Économie et Gestion": [
        "تاريخ / جغرافيا", "فلسفة",
        "رياضيات", "اقتصاد / تصرف", "إعلامية",
    ],
    "Bac Sciences de l'Informatique": [
        "تاريخ / جغرافيا", "فلسفة",
        "رياضيات", "علوم فيزيائية", "إعلامية",
    ],
    "Bac Sciences Techniques": [
        "تاريخ / جغرافيا", "فلسفة",
        "رياضيات", "علوم فيزيائية", "كهرباء / ميكانيك", "إعلامية",
    ],
}


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        print("=" * 60)
        print("  Arborescence Officielle Tunisienne (Noms Arabes)")
        print("  + type_matiere (langue / specialite)")
        print("=" * 60)

        # --- 1. Supprimer les anciennes donnees ---
        print("\n[1/4] Nettoyage des anciennes donnees ...")
        old_matieres_count = db.query(Matiere).delete()
        old_niveaux_count = db.query(NiveauEtude).delete()
        db.flush()
        print("  Supprime: %d matieres, %d niveaux" % (old_matieres_count, old_niveaux_count))

        # --- 2. Inserer les niveaux ---
        print("\n[2/4] Insertion des niveaux ...")
        niveaux = {}
        for ordre, niveau_nom in enumerate(SPECIALITES.keys(), 1):
            niv = NiveauEtude(nom=niveau_nom, ordre=ordre)
            db.add(niv)
            db.flush()
            niveaux[niveau_nom] = niv
            safe_nom = niveau_nom.encode('ascii', 'replace').decode('ascii')
            print("  [NEW] Niveau: %s (ordre=%d)" % (safe_nom, ordre))

        # --- 3. Inserer les matieres ---
        print("\n[3/4] Insertion des matieres ...")
        total_langues = 0
        total_specialites = 0

        for niveau_nom, spec_list in SPECIALITES.items():
            niv = niveaux[niveau_nom]

            # 3a. Langues communes (type_matiere='langue')
            for lang_nom in LANGUES:
                mat = Matiere(
                    niveau_etude_id=niv.id,
                    nom=lang_nom,
                    type_matiere="langue",
                )
                db.add(mat)
                total_langues += 1

            # 3b. Specialites specifiques (type_matiere='specialite')
            for spec_nom in spec_list:
                mat = Matiere(
                    niveau_etude_id=niv.id,
                    nom=spec_nom,
                    type_matiere="specialite",
                )
                db.add(mat)
                total_specialites += 1

            safe_niveau = niveau_nom.encode('ascii', 'replace').decode('ascii')
            print("  [NEW] %s: %d langues + %d specialites = %d total" % (
                safe_niveau, len(LANGUES), len(spec_list), len(LANGUES) + len(spec_list)
            ))

        db.flush()

        # --- 4. Verification ---
        print("\n[4/4] Verification ...")
        total = total_langues + total_specialites
        print("  Total: %d matieres (%d langues + %d specialites)" % (
            total, total_langues, total_specialites
        ))

        db.commit()

        # --- Resume ---
        print("\n" + "=" * 60)
        print("  RESUME")
        print("=" * 60)
        print("  Niveaux: %d" % len(SPECIALITES))
        print("  Matieres: %d total" % total)
        print("    Langues: %d (communes a tous les niveaux)" % total_langues)
        print("    Specialites: %d (specifiques par filiere)" % total_specialites)
        print()
        for niveau_nom, spec_list in SPECIALITES.items():
            safe_nom = niveau_nom.encode('ascii', 'replace').decode('ascii')
            print("  %s: %d langues + %d specialites" % (
                safe_nom, len(LANGUES), len(spec_list)
            ))
        print("=" * 60)
        print("  Termine!")
        print("=" * 60)

    except Exception as e:
        db.rollback()
        print("\n  ERREUR: %s" % e)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
