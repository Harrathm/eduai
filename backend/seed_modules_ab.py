"""
EDUAI Learning — Seed Script Modules A & B
==========================================
Generates comprehensive test data for ALL platform features:
  - Module A: parcours, chapitres, lecons, paragraphes, elements (all types)
  - Module B: pack_definitions, abonnements, famille, licences
  - All roles, all tiers, all pedagogical element types

Usage:
    cd backend
    python seed_modules_ab.py
"""
from __future__ import annotations

import os
import sys
import secrets
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if not os.environ.get("DATABASE_URL"):
    os.environ["DATABASE_URL"] = "postgresql+pg8000://postgres:gill4264@localhost:5432/eduai"

from sqlalchemy.orm import sessionmaker
from app.core.security import get_password_hash
from app.models import (
    Base, School, User, ParentEnfant, WalletTransaction,
    NiveauEtude, Matiere,
    # Module A
    Competence, Parcours, Chapitre, Lecon, Paragraphe,
    ElementPedagogique, ElementTexte, ElementVideo, ElementImage,
    ElementQuiz, ElementPdf, ContentWorkflow,
    # Module B
    PackDefinition, Abonnement, CompteFamille, FamilleEnfant,
    LicenceEcole, LicenceAssignation,
    # Enums
    UserRole, SchoolType, SubscriptionTier, WalletPool,
)

HASHED_PASSWORD = get_password_hash("passeword123")
NOW = datetime.now(timezone.utc)


def _lbl(created: bool) -> str:
    return "[NEW]" if created else "[EXISTS]"


def get_or_create(session, model, defaults=None, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    params = {**kwargs}
    if defaults:
        params.update(defaults)
    instance = model(**params)
    session.add(instance)
    session.flush()
    return instance, True


def seed():
    from app.db.session import engine, SessionLocal

    print("=" * 60)
    print("  EDUAI Seed — Modules A & B")
    print("=" * 60)

    session = SessionLocal()

    try:
        # ================================================================
        # SCHOOLS (already exist from seed_db.py, just fetch)
        # ================================================================
        school_a = session.query(School).filter_by(slug="carthage").first()
        school_b = session.query(School).filter_by(slug="el-jem").first()
        if not school_a or not school_b:
            print("ERROR: Run seed_db.py first to create schools and users.")
            return
        print("\n  Schools: Carthage (id=%d), El Jem (id=%d)" % (school_a.id, school_b.id))

        # ================================================================
        # USERS (fetch existing)
        # ================================================================
        def _u(email):
            return session.query(User).filter_by(email=email).first()

        superadmin = _u("superadmin@eduai.tn")
        pedago_admin = _u("pedagogical.admin@eduai.tn")
        admin_a = _u("admin.carthage@eduai.tn")
        pedago_lead_a = _u("pedago.lead.carthage@eduai.tn")
        teacher_a1 = _u("prof.maths.carthage@eduai.tn")
        teacher_a2 = _u("prof.physique.carthage@eduai.tn")
        student_a1 = _u("eleve1.carthage@eduai.tn")
        student_a2 = _u("eleve2.carthage@eduai.tn")
        student_a3 = _u("eleve3.carthage@eduai.tn")
        parent_a = _u("parent.carthage@eduai.tn")
        admin_b = _u("admin.eljem@eduai.tn")
        pedago_lead_b = _u("pedago.lead.eljem@eduai.tn")
        teacher_b1 = _u("prof.maths.eljem@eduai.tn")
        teacher_b2 = _u("prof.arabe.eljem@eduai.tn")
        student_b1 = _u("eleve1.eljem@eduai.tn")
        student_b2 = _u("eleve2.eljem@eduai.tn")
        student_b3 = _u("eleve3.eljem@eduai.tn")
        parent_b = _u("parent.eljem@eduai.tn")

        print("  Users fetched OK")

        # Reference the Matiere from adaptive pathway (created by seed_db.py)
        matiere_ref = session.query(Matiere).filter_by(nom="Mathematiques").first()

        # ================================================================
        # [1/8] COMPETENCES (global, by subject/level)
        # ================================================================
        print("\n[1/8] Creating competences ...")

        competences_data = [
            # Maths - 9eme
            ("Resoudre des equations du 1er degre", "Mathematiques", "9eme de base",
             "Savoir resoudre des equations lineaires a une inconnue"),
            ("Calculer avec des fractions", "Mathematiques", "9eme de base",
             "Addition, soustraction, multiplication et division de fractions"),
            ("Geometrie dans l'espace", "Mathematiques", "9eme de base",
             "Volume et surface des solides"),
            ("Lire et interpreter des donnees", "Mathematiques", "9eme de base",
             "Statistiques et probabilites de base"),
            # Maths - 2eme
            ("Etudier des fonctions", "Mathematiques", "2eme annee sciences",
             "Etude de fonctions du second degre"),
            ("Derivation", "Mathematiques", "2eme annee sciences",
             "Calcul de derivees et applications"),
            # Physique - 2eme
            ("Mecanique fondamentale", "Physique", "2eme annee sciences",
             "Lois de Newton et mouvement"),
            ("Circuits electriques", "Physique", "2eme annee sciences",
             "Loi d'Ohm et circuits simples"),
            # Arabe - 9eme
            ("Comprehension de texte", "Arabe", "9eme de base",
             "Lire et comprendre des textes litteraires"),
            ("Expression ecrite", "Arabe", "9eme de base",
             "Rediger des textes argumentatifs"),
            # Francais - 9eme
            ("Grammaire francaise", "Francais", "9eme de base",
             "Conjugaison et syntaxe"),
            ("Dissertation litteraire", "Francais", "9eme de base",
             "Planifier et rediger une dissertation"),
        ]

        comps = {}
        for nom, mat, niveau, desc in competences_data:
            c, is_new = get_or_create(
                session, Competence, nom=nom,
                defaults=dict(matiere=mat, niveau_scolaire=niveau, description=desc))
            comps[nom] = c
            print("  %s %s (%s)" % (_lbl(is_new), nom, mat))
        session.flush()

        # ================================================================
        # [2/8] PARCOURS + CHAPITRES + LECONS + PARAGRAPHES
        # ================================================================
        print("\n[2/8] Creating parcours hierarchy ...")

        parcours_data = [
            {
                "titre": "Algebre 9eme - Equations",
                "matiere": "Mathematiques",
                "niveau": "9eme de base",
                "difficulte": "moyen",
                "auteur": teacher_a1,
                "objectifs": {"comprendre": "Les equations du 1er degre", "resoudre": "Equations a une inconnue"},
                "chapitres": [
                    {
                        "titre": "Introduction aux equations",
                        "objectifs": {"vocabulaire": "Terme, inconnue, coefficient"},
                        "lecons": [
                            {
                                "titre": "Qu'est-ce qu'une equation ?",
                                "duree": 15,
                                "objectifs": {"definir": "Equation = egalite avec variable"},
                                "paragraphes": [
                                    {"contenu": "Une equation est une egalite mathematique comportant une ou plusieurs inconnues, representees par des lettres (x, y, z...). Resoudre une equation, c'est trouver la valeur de l'inconnue qui rend l'egalite vraie.", "type": "texte", "ordre": 1},
                                    {"contenu": "Exemple : x + 3 = 7. Ici, x est l'inconnue. Pour resoudre, on cherche x tel que l'egalite soit vraie.", "type": "texte", "ordre": 2},
                                    {"contenu": "Une equation est differente d'une identite. Une identite est vraie pour toute valeur de la variable, tandis qu'une equation n'est vraie que pour certaines valeurs.", "type": "texte", "ordre": 3},
                                ]
                            },
                            {
                                "titre": "Methodes de resolution",
                                "duree": 20,
                                "objectifs": {"methode": "Isoler l'inconnue par des transformations"},
                                "paragraphes": [
                                    {"contenu": "Pour resoudre une equation du 1er degre, on utilise des transformations equivalentes : ajouter ou soustraire un meme nombre des deux membres, multiplier ou diviser les deux membres par un meme nombre non nul.", "type": "texte", "ordre": 1},
                                    {"contenu": "Exemple : 2x + 5 = 11. On soustrait 5 des deux membres : 2x = 6. On divise par 2 : x = 3.", "type": "texte", "ordre": 2},
                                ]
                            },
                        ]
                    },
                    {
                        "titre": "Equations du 1er degre a une inconnue",
                        "objectifs": {"methodes": "Resoudre ax + b = 0"},
                        "lecons": [
                            {
                                "titre": "Forme generale ax + b = 0",
                                "duree": 25,
                                "objectifs": {"identifier": "Coefficients a et b", "resoudre": "x = -b/a"},
                                "paragraphes": [
                                    {"contenu": "Toute equation du 1er degre a une inconnue peut s'ecrire sous la forme ax + b = 0, avec a != 0. La solution est x = -b/a.", "type": "texte", "ordre": 1},
                                    {"contenu": "Application : 3x - 6 = 0. Ici a = 3, b = -6. Solution : x = -(-6)/3 = 6/3 = 2.", "type": "texte", "ordre": 2},
                                    {"contenu": "Attention : si a = 0 et b = 0, l'equation admet une infinite de solutions. Si a = 0 et b != 0, il n'y a aucune solution.", "type": "texte", "ordre": 3},
                                ]
                            },
                        ]
                    },
                ]
            },
            {
                "titre": "Physique - Mecanique Newton",
                "matiere": "Physique",
                "niveau": "2eme annee sciences",
                "difficulte": "difficile",
                "auteur": teacher_a2,
                "objectifs": {"comprendre": "Les 3 lois de Newton", "appliquer": "Problemes de mouvement"},
                "chapitres": [
                    {
                        "titre": "Lois de Newton",
                        "objectifs": {"enoncer": "Les 3 lois"},
                        "lecons": [
                            {
                                "titre": "1ere loi - Inertie",
                                "duree": 15,
                                "objectifs": {"definir": "Principe d'inertie"},
                                "paragraphes": [
                                    {"contenu": "La premiere loi de Newton (principe d'inertie) : un corps reste au repos ou en mouvement rectiligne uniforme tant qu'aucune force exterieure ne s'exerce sur lui.", "type": "texte", "ordre": 1},
                                    {"contenu": "Exemple : un livre pose sur une table reste immobile. Une balle qui roule sur un sol horizontal continue a rouler si on ne la freine pas.", "type": "texte", "ordre": 2},
                                ]
                            },
                            {
                                "titre": "2eme loi - F = ma",
                                "duree": 20,
                                "objectifs": {"formuler": "F = m * a", "calculer": "Force resultante"},
                                "paragraphes": [
                                    {"contenu": "La deuxieme loi de Newton : la force resultante appliquee a un corps est egale a la masse de ce corps multipliee par son acceleration. F = m * a (en newtons).", "type": "texte", "ordre": 1},
                                    {"contenu": "Un corps de 5 kg soumis a une force de 20 N a une acceleration de a = F/m = 20/5 = 4 m/s².", "type": "texte", "ordre": 2},
                                    {"contenu": "Cette loi permet de calculer l'acceleration d'un corps si on connait la force et la masse, ou la force si on connait l'acceleration et la masse.", "type": "texte", "ordre": 3},
                                ]
                            },
                            {
                                "titre": "3eme loi - Action-Reaction",
                                "duree": 15,
                                "objectifs": {"enoncer": "A chaque action correspond une reaction"},
                                "paragraphes": [
                                    {"contenu": "La troisieme loi de Newton : pour chaque force d'action, il existe une force de reaction de meme intensite, de meme direction, mais de sens oppose. F_AB = -F_BA.", "type": "texte", "ordre": 1},
                                    {"contenu": "Quand vous marchez, vos pieds exercent une force vers l'arriere sur le sol. Le sol exerce une force egale vers l'avant sur vos pieds, ce qui vous propulse.", "type": "texte", "ordre": 2},
                                ]
                            },
                        ]
                    },
                ]
            },
            {
                "titre": "Arabe - Expression Ecrite",
                "matiere": "Arabe",
                "niveau": "9eme de base",
                "difficulte": "basique",
                "auteur": teacher_b2,
                "objectifs": {"rediger": "Textes argumentatifs"},
                "chapitres": [
                    {
                        "titre": "Structure du texte argumentatif",
                        "objectifs": {"identifier": "Introduction, developpement, conclusion"},
                        "lecons": [
                            {
                                "titre": "L'introduction",
                                "duree": 15,
                                "objectifs": {"rédiger": "Une introduction accrocheuse"},
                                "paragraphes": [
                                    {"contenu": "L'introduction d'un texte argumentatif comprend : l'accroche (question, citation, fait), la presentation du sujet, et l'annonce du plan.", "type": "texte", "ordre": 1},
                                    {"contenu": "Exemple d'accroche : 'L'education est-elle vraiment la cle du succes ? Cette question merite une reflexion approfondie.'", "type": "texte", "ordre": 2},
                                ]
                            },
                        ]
                    },
                ]
            },
        ]

        all_paragraphes = []
        all_elements = []

        for p_data in parcours_data:
            parc, is_new = get_or_create(
                session, Parcours, titre=p_data["titre"],
                defaults=dict(
                    description="Parcours complet de %s" % p_data["titre"],
                    matiere=p_data["matiere"],
                    niveau_scolaire=p_data["niveau"],
                    difficulte=p_data["difficulte"],
                    auteur_id=p_data["auteur"].id,
                    objectifs=p_data["objectifs"],
                    est_publique=True,
                    est_actif=True,
                ))
            print("  %s Parcours: %s (id=%d)" % (_lbl(is_new), p_data["titre"], parc.id))

            for ch_data in p_data["chapitres"]:
                chap, is_new = get_or_create(
                    session, Chapitre, titre=ch_data["titre"],
                    defaults=dict(
                        parcours_id=parc.id,
                        description="Chapitre de %s" % ch_data["titre"],
                        objectifs=ch_data["objectifs"],
                        ordre=1,
                    ))
                print("    %s Chapitre: %s (id=%d)" % (_lbl(is_new), ch_data["titre"], chap.id))

                for l_data in ch_data["lecons"]:
                    lec, is_new = get_or_create(
                        session, Lecon, titre=l_data["titre"],
                        defaults=dict(
                            chapitre_id=chap.id,
                            description="Lecon de %s" % l_data["titre"],
                            duree_minutes=l_data["duree"],
                            objectifs=l_data["objectifs"],
                            ordre=1,
                        ))
                    print("      %s Lecon: %s (id=%d)" % (_lbl(is_new), l_data["titre"], lec.id))

                    for pg_data in l_data.get("paragraphes", []):
                        pg, is_new = get_or_create(
                            session, Paragraphe,
                            lecon_id=lec.id, ordre=pg_data["ordre"],
                            defaults=dict(
                                contenu=pg_data["contenu"],
                                type=pg_data["type"],
                            ))
                        all_paragraphes.append(pg)
                        print("        %s Paragraphe #%d (%s)" % (_lbl(is_new), pg_data["ordre"], pg_data["type"]))

                    # Create one element per lecon (varied types)
                    el_type_map = {
                        "Qu'est-ce qu'une equation ?": ("texte", teacher_a1),
                        "Methodes de resolution": ("video", teacher_a1),
                        "Forme generale ax + b = 0": ("quiz", teacher_a1),
                        "1ere loi - Inertie": ("image", teacher_a2),
                        "2eme loi - F = ma": ("texte", teacher_a2),
                        "3eme loi - Action-Reaction": ("pdf", teacher_a2),
                        "L'introduction": ("texte", teacher_b2),
                    }
                    if l_data["titre"] in el_type_map:
                        el_type, author = el_type_map[l_data["titre"]]
                        statut = "publie" if el_type != "quiz" else "brouillon"
                        elem, is_new = get_or_create(
                            session, ElementPedagogique,
                            titre="Element %s" % l_data["titre"],
                            defaults=dict(
                                type=el_type,
                                description="Element pedagogique pour %s" % l_data["titre"],
                                lecon_id=lec.id,
                                matiere_id=matiere_ref.id if matiere_ref else None,
                                auteur_id=author.id,
                                statut=statut,
                                difficulte="moyen",
                                est_global=False,
                                est_libre=False,
                            ))
                        all_elements.append(elem)
                        print("        %s Element %s (id=%d, statut=%s)" % (_lbl(is_new), el_type, elem.id, statut))

                        # Create subtype content
                        if el_type == "texte":
                            sub, is_new = get_or_create(
                                session, ElementTexte, element_id=elem.id,
                                defaults=dict(corps="Contenu texte complet de %s. Ce paragraphe developpe les concepts fondamentaux avec des exemples detailles." % l_data["titre"]))
                            print("          %s ElementTexte" % _lbl(is_new))
                        elif el_type == "video":
                            sub, is_new = get_or_create(
                                session, ElementVideo, element_id=elem.id,
                                defaults=dict(url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                                              duree_secondes=600,
                                              thumbnail_url="https://img.youtube.com/vi/dQw4w9WgXcQ/hqdefault.jpg"))
                            print("          %s ElementVideo" % _lbl(is_new))
                        elif el_type == "image":
                            sub, is_new = get_or_create(
                                session, ElementImage, element_id=elem.id,
                                defaults=dict(url="https://example.com/schema_newton.png",
                                              alt_text="Schema illustrant les lois de Newton"))
                            print("          %s ElementImage" % _lbl(is_new))
                        elif el_type == "quiz":
                            sub, is_new = get_or_create(
                                session, ElementQuiz, element_id=elem.id,
                                defaults=dict(
                                    questions_json={
                                        "questions": [
                                            {
                                                "texte": "Que signifie l'equation 2x + 4 = 0 ?",
                                                "options": ["x = 2", "x = -2", "x = 4", "x = -4"],
                                                "reponse_correcte": 1,
                                                "explication": "2x + 4 = 0 => 2x = -4 => x = -2"
                                            },
                                            {
                                                "texte": "Quelle est la solution de x/3 = 5 ?",
                                                "options": ["x = 15", "x = 2", "x = 8", "x = -15"],
                                                "reponse_correcte": 0,
                                                "explication": "x/3 = 5 => x = 15"
                                            }
                                        ]
                                    },
                                    score_reussite=0.6))
                            print("          %s ElementQuiz" % _lbl(is_new))
                        elif el_type == "pdf":
                            sub, is_new = get_or_create(
                                session, ElementPdf, element_id=elem.id,
                                defaults=dict(url="https://example.com/cours_newton.pdf",
                                              pages=25,
                                              taille_octets=2048000))
                            print("          %s ElementPdf" % _lbl(is_new))

                        # Add workflow entry for published elements
                        if statut == "publie":
                            wf, is_new = get_or_create(
                                session, ContentWorkflow,
                                element_id=elem.id, nouveau_statut="publie",
                                defaults=dict(
                                    ancien_statut="brouillon",
                                    commentaires="Auto-approve par l'enseignant",
                                    auteur_id=author.id,
                                ))
                            if is_new:
                                print("          %s ContentWorkflow: brouillon -> publie" % _lbl(is_new))
        session.flush()

        # ================================================================
        # [3/8] PACK DEFINITIONS (Module B)
        # ================================================================
        print("\n[3/8] Creating pack definitions ...")

        niveaux = ["9eme de base", "2eme annee sciences", "3eme annee mathematiques",
                    "1ere annee secondaire", "4eme annee secondaire"]
        tiers = [
            ("gratuit", 0, {"ai_ask": True, "ai_explain": False, "ai_quiz": False, "max_lessons_per_day": 3}),
            ("basique", 9.9, {"ai_ask": True, "ai_explain": True, "ai_quiz": False, "max_lessons_per_day": 10}),
            ("silver", 19.9, {"ai_ask": True, "ai_explain": True, "ai_quiz": True, "max_lessons_per_day": 50, "priority_support": True}),
            ("golden", 39.9, {"ai_ask": True, "ai_explain": True, "ai_quiz": True, "ai_generate": True, "max_lessons_per_day": -1, "priority_support": True, "offline_access": True}),
        ]

        packs = {}
        for niveau in niveaux:
            for tier_name, prix, features in tiers:
                key = "%s_%s" % (niveau, tier_name)
                nom = "Pack %s - %s" % (niveau.capitalize(), tier_name.capitalize())
                pack, is_new = get_or_create(
                    session, PackDefinition, nom=nom,
                    defaults=dict(
                        description="Pack %s pour %s" % (tier_name, niveau),
                        tier=tier_name,
                        niveau_scolaire=niveau,
                        matieres={"matieres": ["Mathematiques", "Physique", "Arabe", "Francais", "Anglais"]},
                        prix_tnd=prix,
                        features=features,
                        est_actif=True,
                    ))
                packs[key] = pack
                print("  %s Pack: %s (id=%d, %.2f TND)" % (_lbl(is_new), nom, pack.id, prix))
        session.flush()

        # ================================================================
        # [4/8] ABONNEMENTS (Module B)
        # ================================================================
        print("\n[4/8] Creating abonnements ...")

        abonnements_data = [
            # Student A1: Silver
            (student_a1, "9eme de base_silver", 90),
            # Student A2: Basique
            (student_a2, "2eme annee sciences_basique", 90),
            # Student A3: Gratuit (default)
            (student_a3, "9eme de base_gratuit", 365),
            # Student B1: Golden
            (student_b1, "9eme de base_golden", 90),
            # Student B2: Silver
            (student_b2, "1ere annee secondaire_silver", 90),
            # Student B3: Gratuit
            (student_b3, "9eme de base_gratuit", 365),
        ]

        for user, pack_key, days in abonnements_data:
            if not user:
                continue
            ab, is_new = get_or_create(
                session, Abonnement, user_id=user.id,
                defaults=dict(
                    pack_id=packs[pack_key].id,
                    statut="actif",
                    debut=NOW,
                    fin=NOW + timedelta(days=days),
                ))
            print("  %s Abonnement: %s -> %s (%d jours)" % (_lbl(is_new), user.full_name, pack_key, days))
        session.flush()

        # ================================================================
        # [5/8] COMPTE FAMILLE + FAMILLE ENFANTS
        # ================================================================
        print("\n[5/8] Creating famille accounts ...")

        # Parent A has 2 children (eleve1 and eleve3)
        cf_a, is_new = get_or_create(
            session, CompteFamille, parent_id=parent_a.id,
            defaults=dict(max_enfants=5, rang_famille=1))
        print("  %s CompteFamille: parent.carthage (id=%d)" % (_lbl(is_new), cf_a.id))

        fam_child_data_a = [
            (student_a1, 1, 0.0),
            (student_a3, 2, 20.0),
        ]
        for child, rang, remise in fam_child_data_a:
            if not child:
                continue
            fc, is_new = get_or_create(
                session, FamilleEnfant, eleve_id=child.id,
                defaults=dict(
                    compte_famille_id=cf_a.id,
                    rang=rang,
                    remise_pct=remise,
                ))
            print("  %s FamilleEnfant: %s (rang=%d, remise=%.0f%%)" % (_lbl(is_new), child.full_name, rang, remise))

        # Parent B has 1 child
        cf_b, is_new = get_or_create(
            session, CompteFamille, parent_id=parent_b.id,
            defaults=dict(max_enfants=3, rang_famille=1))
        print("  %s CompteFamille: parent.eljem (id=%d)" % (_lbl(is_new), cf_b.id))

        fc, is_new = get_or_create(
            session, FamilleEnfant, eleve_id=student_b1.id,
            defaults=dict(
                compte_famille_id=cf_b.id,
                rang=1,
                remise_pct=0.0,
            ))
        print("  %s FamilleEnfant: %s (rang=1, remise=0%%)" % (_lbl(is_new), student_b1.full_name))
        session.flush()

        # ================================================================
        # [6/8] LICENCES ECOLE + ASSIGNEE
        # ================================================================
        print("\n[6/8] Creating licences ...")

        # School A: 30 Silver licences
        lic_a, is_new = get_or_create(
            session, LicenceEcole,
            ecole_id=school_a.id, pack_id=packs["9eme de base_silver"].id,
            defaults=dict(
                quantite=30,
                quantite_disponible=27,
                expires_at=NOW + timedelta(days=365),
            ))
        print("  %s LicenceEcole: Carthage -> Silver 9eme (30 licences)" % _lbl(is_new))

        # Assign some licences
        for student, email in [(student_a1, "eleve1.carthage@eduai.tn"),
                               (student_a2, "eleve2.carthage@eduai.tn"),
                               (student_a3, "eleve3.carthage@eduai.tn")]:
            if not student:
                continue
            la, is_new = get_or_create(
                session, LicenceAssignation, licence_id=lic_a.id, user_id=student.id,
                defaults=dict(affecte_par_id=admin_a.id))
            print("    %s Assignation: %s" % (_lbl(is_new), email))

        # School B: 20 Golden licences
        lic_b, is_new = get_or_create(
            session, LicenceEcole,
            ecole_id=school_b.id, pack_id=packs["9eme de base_golden"].id,
            defaults=dict(
                quantite=20,
                quantite_disponible=18,
                expires_at=NOW + timedelta(days=365),
            ))
        print("  %s LicenceEcole: El Jem -> Golden 9eme (20 licences)" % _lbl(is_new))

        for student, email in [(student_b1, "eleve1.eljem@eduai.tn"),
                               (student_b2, "eleve2.eljem@eduai.tn")]:
            if not student:
                continue
            la, is_new = get_or_create(
                session, LicenceAssignation, licence_id=lic_b.id, user_id=student.id,
                defaults=dict(affecte_par_id=admin_b.id))
            print("    %s Assignation: %s" % (_lbl(is_new), email))
        session.flush()

        # ================================================================
        # [7/8] WALLET TOP-UP for parents
        # ================================================================
        print("\n[7/8] Wallet top-ups for parents ...")

        for parent_user, email in [(parent_a, "parent.carthage@eduai.tn"),
                                   (parent_b, "parent.eljem@eduai.tn")]:
            if not parent_user:
                continue
            existing = session.query(WalletTransaction).filter_by(user_id=parent_user.id).first()
            if not existing:
                session.add(WalletTransaction(
                    user_id=parent_user.id, pool=WalletPool.DT_PURCHASED, amount=100.0))
                print("  [NEW] Wallet: %s -> 100.00 DT" % email)
            else:
                print("  [EXISTS] Wallet: %s" % email)
        session.flush()

        # ================================================================
        # [8/8] DONE
        # ================================================================
        session.commit()

        print("\n" + "=" * 60)
        print("  Seed Modules A & B complete!")
        print("=" * 60)
        print("")
        print("  MODULE A:")
        print("    Parcours:         3 (Algebre 9eme, Physique 2eme, Arabe 9eme)")
        print("    Chapitres:        %d" % session.query(Chapitre).count())
        print("    Lecons:           %d" % session.query(Lecon).count())
        print("    Paragraphes:      %d" % session.query(Paragraphe).count())
        print("    Elements:         %d (texte, video, image, quiz, pdf)" % session.query(ElementPedagogique).count())
        print("    Competences:      %d" % session.query(Competence).count())
        print("    Workflows:        %d" % session.query(ContentWorkflow).count())
        print("")
        print("  MODULE B:")
        print("    Pack Definitions: %d (4 tiers x 5 niveaux)" % session.query(PackDefinition).count())
        print("    Abonnements:      %d" % session.query(Abonnement).count())
        print("    Comptes Famille:  2")
        print("    Famille Enfants:  %d" % session.query(FamilleEnfant).count())
        print("    Licences Ecole:   2 (30 Silver Carthage, 20 Golden El Jem)")
        print("    Assignations:     %d" % session.query(LicenceAssignation).count())
        print("")
        print("  ROLES:")
        print("    super_admin:      1 (superadmin@eduai.tn)")
        print("    pedagogical_admin:1 (pedagogical.admin@eduai.tn)")
        print("    admin_school:     2 (admin.carthage, admin.eljem)")
        print("    pedagogical_lead: 2 (pedago.lead.carthage, pedago.lead.eljem)")
        print("    teacher:          4 (2 per school)")
        print("    student:          6 (3 per school)")
        print("    parent:           2 (1 per school)")
        print("")
        print("  PASSWORD: passeword123 (all accounts)")
        print("=" * 60)

    except Exception as e:
        session.rollback()
        print("\n  ERROR: %s" % e)
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed()
