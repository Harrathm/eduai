"""
Seed Packs with Varied Content + Courses
=========================================
Creates differentiated packs per niveau_scolaire with distinct matieres per tier:
  - Gratuit: 2 matieres (Math + 1 autre)
  - Basique: 3 matieres
  - Silver: 4 matieres
  - Golden: 5 matieres + Soft Skills

Also creates courses per niveau_scolaire with matching categories.

Usage:
    cd backend
    python seed_packs_content.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if not os.environ.get("DATABASE_URL"):
    os.environ["DATABASE_URL"] = "postgresql+pg8000://postgres:gill4264@localhost:5432/eduai"

from app.db.session import SessionLocal
from app.models import PackDefinition, Course, School, User

MATERIES_PAR_NIVEAU = {
    # Accented variants (matching student data)
    "7ème de base": {
        "core": ["Mathematiques", "Arabe", "Francais", "Sciences"],
        "extras": ["Anglais", "Histoire-Geographie"],
    },
    "8ème de base": {
        "core": ["Mathematiques", "Arabe", "Francais", "Sciences"],
        "extras": ["Anglais", "Histoire-Geographie"],
    },
    "9ème de base": {
        "core": ["Mathematiques", "Physique", "Arabe", "Francais"],
        "extras": ["Anglais", "SVT", "Informatique"],
    },
    "1ère année secondaire": {
        "core": ["Mathematiques", "Physique-Chimie", "Arabe", "Francais"],
        "extras": ["Anglais", "SVT", "Informatique", "Histoire-Geographie"],
    },
    # Non-accented variants (existing data)
    "7eme annee de base": {
        "core": ["Mathematiques", "Arabe", "Francais", "Sciences"],
        "extras": ["Anglais", "Histoire-Geographie"],
    },
    "8eme annee de base": {
        "core": ["Mathematiques", "Arabe", "Francais", "Sciences"],
        "extras": ["Anglais", "Histoire-Geographie"],
    },
    "9eme de base": {
        "core": ["Mathematiques", "Physique", "Arabe", "Francais"],
        "extras": ["Anglais", "SVT", "Informatique"],
    },
    "1ere annee secondaire": {
        "core": ["Mathematiques", "Physique-Chimie", "Arabe", "Francais"],
        "extras": ["Anglais", "SVT", "Informatique", "Histoire-Geographie"],
    },
    "2eme annee sciences": {
        "core": ["Mathematiques", "Physique", "Chimie", "Francais"],
        "extras": ["Anglais", "SVT", "Informatique", "Arabe"],
    },
    "3eme annee mathematiques": {
        "core": ["Mathematiques", "Physique", "Chimie", "Anglais"],
        "extras": ["Informatique", "Francais", "Arabe"],
    },
    "4eme annee secondaire": {
        "core": ["Mathematiques", "Physique", "Chimie", "Anglais"],
        "extras": ["Informatique", "Francais", "SVT"],
    },
}

COURSES_PAR_NIVEAU = {
    "7eme annee de base": [
        {"title": "SVT - Biologie cellulaire", "category": "Sciences", "author_id": 1},
        {"title": "Mathematiques - Equations du 1er degre", "category": "Mathematiques", "author_id": 1},
        {"title": "Arabe - Comprehension de texte", "category": "Arabe", "author_id": 1},
        {"title": "Francais - Le compose passe", "category": "Francais", "author_id": 1},
        {"title": "Sciences - Le milieu terrestre", "category": "Sciences", "author_id": 1},
        {"title": "Anglais - Present simple", "category": "Anglais", "author_id": 1},
    ],
    "8eme annee de base": [
        {"title": "Mathematiques - Fractions et proportions", "category": "Mathematiques", "author_id": 1},
        {"title": "Physique - Constitution de la matiere", "category": "Sciences", "author_id": 1},
        {"title": "Arabe - Textes litteraires", "category": "Arabe", "author_id": 1},
        {"title": "Francais - Le subjonctif", "category": "Francais", "author_id": 1},
        {"title": "Sciences - L'univers et la Terre", "category": "Sciences", "author_id": 1},
        {"title": "Anglais - Past tense", "category": "Anglais", "author_id": 1},
    ],
    "9eme de base": [
        {"title": "Mathematiques - Polynomes", "category": "Mathematiques", "author_id": 1},
        {"title": "Physique - Electricite", "category": "Physique", "author_id": 1},
        {"title": "Arabe - Rhetorique et style", "category": "Arabe", "author_id": 1},
        {"title": "Francais - La dissertation", "category": "Francais", "author_id": 1},
        {"title": "Anglais - Conditionals", "category": "Anglais", "author_id": 1},
        {"title": "SVT - Reproduction humaine", "category": "SVT", "author_id": 1},
        {"title": "Informatique - Bases de Python", "category": "Informatique", "author_id": 1},
    ],
    "1ere annee secondaire": [
        {"title": "Mathematiques - Nombres complexes", "category": "Mathematiques", "author_id": 1},
        {"title": "Physique-Chimie - Forces et mouvement", "category": "Physique-Chimie", "author_id": 1},
        {"title": "Arabe - Al-Muallaqat", "category": "Arabe", "author_id": 1},
        {"title": "Francais - Argumentation", "category": "Francais", "author_id": 1},
        {"title": "Anglais - Active and passive voice", "category": "Anglais", "author_id": 1},
        {"title": "SVT - Genetique humaine", "category": "SVT", "author_id": 1},
        {"title": "Informatique - Algorithmique", "category": "Informatique", "author_id": 1},
    ],
    "2eme annee sciences": [
        {"title": "Mathematiques - Fonctions sinus et cosinus", "category": "Mathematiques", "author_id": 1},
        {"title": "Physique - Cinematique", "category": "Physique", "author_id": 1},
        {"title": "Chimie - Liaisons chimiques", "category": "Chimie", "author_id": 1},
        {"title": "Francais - Texte argumentatif", "category": "Francais", "author_id": 1},
        {"title": "Anglais - Essay writing", "category": "Anglais", "author_id": 1},
        {"title": "SVT - Biodiversite et ecosystemes", "category": "SVT", "author_id": 1},
        {"title": "Informatique - Structures de donnees", "category": "Informatique", "author_id": 1},
    ],
    "3eme annee mathematiques": [
        {"title": "Mathematiques - Matrices et determinants", "category": "Mathematiques", "author_id": 1},
        {"title": "Physique - Optique geometrique", "category": "Physique", "author_id": 1},
        {"title": "Chimie - Thermochimie", "category": "Chimie", "author_id": 1},
        {"title": "Anglais - Scientific English", "category": "Anglais", "author_id": 1},
        {"title": "Informatique - POO en Python", "category": "Informatique", "author_id": 1},
    ],
    "4eme annee secondaire": [
        {"title": "Mathematiques - Espaces vectoriels", "category": "Mathematiques", "author_id": 1},
        {"title": "Physique - Electromagnetisme", "category": "Physique", "author_id": 1},
        {"title": "Chimie - Chimie organique", "category": "Chimie", "author_id": 1},
        {"title": "Anglais - Business English", "category": "Anglais", "author_id": 1},
        {"title": "Informatique - Bases de donnees", "category": "Informatique", "author_id": 1},
        {"title": "SVT - Biologie moleculaire", "category": "SVT", "author_id": 1},
    ],
}

SOFT_SKILLS_PACK = [
    "Gestion du stress et examens",
    "Methodes d'apprentissage efficaces",
    "Communication et prise de parole",
    "Travail en equipe et collaboration",
    "Orientation scolaire et professionnelle",
    "Gestion du temps et organisation",
    "Leadership et initiative",
    "Pensee critique et resolution de problemes",
]

# Students to set niveau_scolaire if not already set
STUDENT_NIVEAU_MAP = {
    "eleve1.carthage@eduai.tn": "9ème de base",
    "eleve2.carthage@eduai.tn": "9ème de base",
    "eleve3.carthage@eduai.tn": "7ème de base",
    "eleve1.eljem@eduai.tn": "9ème de base",
    "eleve2.eljem@eduai.tn": "1ère année secondaire",
    "eleve3.eljem@eduai.tn": "9ème de base",
    "karim.mansour@eduai.tn": "2eme annee sciences",
    "omar.saadi@eduai.tn": "1ere annee secondaire",
    "nour.hentati@eduai.tn": "9eme de base",
    "amira.ben.salah@eduai.tn": "4eme annee secondaire",
    "fatma.zouari@eduai.tn": "3eme annee mathematiques",
    "ali.bouchama@eduai.tn": "1ère année secondaire",
    "harrath.mohamed@eduai.tn": "7ème de base",
    "fatma.trabelsi@eduai.tn": "2eme annee sciences",
    "youssef.khelifi@eduai.tn": "9eme de base",
    "amira.bouazizi@eduai.tn": "9eme de base",
    "omar.mansour@eduai.tn": "1ere annee secondaire",
    "nour.haddad@eduai.tn": "9eme de base",
    "ahmed.ben.ali@eduai.tn": "9eme de base",
}


def seed():
    session = SessionLocal()
    school_a = session.query(School).filter_by(slug="carthage").first()
    if not school_a:
        print("ERROR: Run seed_db.py first.")
        return

    # 1. Update existing packs with varied matieres
    print("=== Updating packs with varied matieres ===")
    packs = session.query(PackDefinition).all()
    for p in packs:
        niveau = p.niveau_scolaire
        if niveau not in MATERIES_PAR_NIVEAU:
            continue
        data = MATERIES_PAR_NIVEAU[niveau]
        core = data["core"]
        extras = data["extras"]

        if p.tier == "gratuit":
            matieres = core[:2]  # 2 matieres
            desc = "Acces limita : %s. Pour decouvrir la plateforme." % ", ".join(matieres)
            prix = 0
            features = {"ai_ask": True, "ai_explain": False, "ai_quiz": False, "max_lessons_per_day": 3}
        elif p.tier == "basique":
            matieres = core[:3]  # 3 matieres
            desc = "Pack de base : %s. Pour un suivi regulier." % ", ".join(matieres)
            prix = 9.9
            features = {"ai_ask": True, "ai_explain": True, "ai_quiz": False, "max_lessons_per_day": 10}
        elif p.tier == "silver":
            matieres = core[:4]  # 4 matieres
            desc = "Pack avance : %s. Pour progresser dans toutes les matieres." % ", ".join(matieres)
            prix = 19.9
            features = {"ai_ask": True, "ai_explain": True, "ai_quiz": True, "max_lessons_per_day": 50, "priority_support": True}
        else:  # golden
            matieres = core + extras  # all matieres
            desc = "Pack complet : %s. Plus les Soft Skills pour developper votre potentiel." % ", ".join(matieres)
            prix = 39.9
            features = {"ai_ask": True, "ai_explain": True, "ai_quiz": True, "ai_generate": True, "max_lessons_per_day": -1, "priority_support": True, "offline_access": True, "soft_skills": True}

        p.matieres = {"matieres": matieres}
        p.description = desc
        p.prix_tnd = prix
        p.features = features
        p.est_actif = True
        print("  Updated: %s | %d matieres | %.1f TND" % (p.nom, len(matieres), prix))

    session.flush()

    # 1b. Create packs for accented variants that don't exist yet
    ACCENTED_NIVEAUX = ["7ème de base", "8ème de base", "9ème de base", "1ère année secondaire"]
    for niveau in ACCENTED_NIVEAUX:
        if niveau not in MATERIES_PAR_NIVEAU:
            continue
        existing = session.query(PackDefinition).filter_by(niveau_scolaire=niveau).first()
        if existing:
            print("  [EXISTS] Packs for %s" % niveau)
            continue
        data = MATERIES_PAR_NIVEAU[niveau]
        core = data["core"]
        extras = data["extras"]
        tier_configs = [
            ("gratuit", 0, core[:2], {"ai_ask": True, "ai_explain": False, "ai_quiz": False, "max_lessons_per_day": 3}),
            ("basique", 9.9, core[:3], {"ai_ask": True, "ai_explain": True, "ai_quiz": False, "max_lessons_per_day": 10}),
            ("silver", 19.9, core[:4], {"ai_ask": True, "ai_explain": True, "ai_quiz": True, "max_lessons_per_day": 50, "priority_support": True}),
            ("golden", 39.9, core + extras, {"ai_ask": True, "ai_explain": True, "ai_quiz": True, "ai_generate": True, "max_lessons_per_day": -1, "priority_support": True, "offline_access": True, "soft_skills": True}),
        ]
        for tier, prix, matieres, features in tier_configs:
            nom = "Pack %s - %s" % (niveau.capitalize(), tier.capitalize())
            desc = "Pack %s : %s" % (tier, ", ".join(matieres))
            pack = PackDefinition(
                nom=nom, description=desc, tier=tier,
                niveau_scolaire=niveau,
                matieres={"matieres": matieres},
                prix_tnd=prix, features=features, est_actif=True,
            )
            session.add(pack)
            print("  [NEW] %s (%d matieres, %.1f TND)" % (nom, len(matieres), prix))
    session.flush()

    # 1c. Set student niveau_scolaire
    print("\n=== Setting student niveau_scolaire ===")
    updated_students = 0
    for email, niveau in STUDENT_NIVEAU_MAP.items():
        student = session.query(User).filter_by(email=email).first()
        if student and not student.niveau_scolaire:
            student.niveau_scolaire = niveau
            updated_students += 1
            print("  [SET] %s -> %s" % (student.full_name, niveau))
    print("  Updated %d students" % updated_students)
    session.flush()

    # 2. Create courses per niveau_scolaire
    print("\n=== Creating courses per niveau ===")
    total_created = 0
    for niveau, courses_data in COURSES_PAR_NIVEAU.items():
        for c_data in courses_data:
            title = c_data["title"]
            existing = session.query(Course).filter_by(title=title).first()
            if existing:
                continue
            course = Course(
                title=title,
                niveau_scolaire=niveau,
                category=c_data["category"],
                school_id=school_a.id,
                author_id=c_data["author_id"],
                status="published",
                visibility="public_catalog",
                owner_type="school",
                description="Cours de %s pour le niveau %s" % (c_data["category"], niveau),
            )
            session.add(course)
            total_created += 1
            print("  [NEW] %s (%s)" % (title, niveau))

    session.flush()

    # 3. Verify
    total_packs = session.query(PackDefinition).filter_by(est_actif=True).count()
    total_courses = session.query(Course).filter_by(status="published").count()
    print("\n=== Summary ===")
    print("  Active packs: %d" % total_packs)
    print("  Published courses: %d" % total_courses)
    print("  New courses created: %d" % total_created)

    session.commit()
    print("\nDONE - Packs updated, courses created.")


if __name__ == "__main__":
    seed()
