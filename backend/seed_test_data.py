"""
Seed data for EDUAI Learning — Adaptive Pathway (§5 spec).

Usage:
    cd backend && python seed_test_data.py

Idempotent: checks before inserting, safe to re-run.
"""
import os
import sys
import io

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
from datetime import datetime, timedelta, timezone

# Ensure we can import from app
sys.path.insert(0, os.path.dirname(__file__))

from app.db.session import SessionLocal
from app.models import (
    School, User, NiveauEtude, Matiere, ChapterPathway, Notion, ContenuNotion,
    ProfilAssimilationEleve, HistoriqueScoreEleve, NotificationReorientation,
    StudyPack, PackPurchase,
    SpecialitePedagogique, SpecialitePedagogiqueMatiere, ResponsablePedagogique,
    # Enums
    UserRole, SchoolType, NiveauScolaire, PackStatus, PackPurchaseStatus, PurchaserType,
    NiveauAssimilation, TypeContenu, StatutContenuPedagogique,
    StatutValidationPedagogique, SourceChangement, StatutValidationProfil,
    ActionReorientation,
)


def utcnow():
    return datetime.now(timezone.utc)


# ============================================================
# §5.1 — ÉCOLES (tenants)
# ============================================================

SCHOOLS = [
    # École A — Lycée Pilote Carthage (2ème cycle + secondaire)
    {"slug": "lycee-pilote-carthage", "name": "Lycée Pilote Carthage",
     "school_type": SchoolType.REAL.value, "cycle_scolaire": "2eme_cycle"},
    # École B — Collège El Manar (1er + 2ème cycle)
    {"slug": "college-el-manar", "name": "Collège El Manar",
     "school_type": SchoolType.REAL.value, "cycle_scolaire": "1er_cycle"},
]


def seed_schools(db):
    schools = {}
    for s in SCHOOLS:
        existing = db.query(School).filter(School.slug == s["slug"]).first()
        if existing:
            schools[s["slug"]] = existing
            continue
        school = School(
            name=s["name"], slug=s["slug"], school_type=s["school_type"],
        )
        db.add(school)
        db.flush()
        schools[s["slug"]] = school
    db.commit()
    return schools


# ============================================================
# §5.2 — UTILISATEURS (tous rôles sauf parent — pas dans UserRole)
# ============================================================

def seed_users(db, schools):
    users = {}
    password_hash = get_password_hash("password123")

    user_defs = [
        # super_admin (1)
        ("superadmin@test.com", "Super Admin", UserRole.SUPER_ADMIN, None),
        # pedagogical_admin — super_admin_pédagogique (1)
        ("pedago.admin@test.com", "Admin Pédago Plateforme", UserRole.PEDAGOGICAL_ADMIN, None),
        # admin_school — 1 par école (2)
        ("admin.lycee@test.com", "Admin Lycée", UserRole.ADMIN_SCHOOL, "lycee-pilote-carthage"),
        ("admin.college@test.com", "Admin Collège", UserRole.ADMIN_SCHOOL, "college-el-manar"),
        # admin_pédagogique (pedagogical_lead) — 1 par école (2)
        ("pedago.lycee@test.com", "Pédago Lycée", UserRole.PEDAGOGICAL_LEAD, "lycee-pilote-carthage"),
        ("pedago.college@test.com", "Pédago Collège", UserRole.PEDAGOGICAL_LEAD, "college-el-manar"),
        # teachers (4) — un par état A/B/C + un extra
        ("teacher.maths@test.com", "Enseignant Maths", UserRole.TEACHER, "lycee-pilote-carthage"),
        ("teacher.sciences@test.com", "Enseignant Sciences", UserRole.TEACHER, "lycee-pilote-carthage"),
        ("teacher.langues@test.com", "Enseignant Langues", UserRole.TEACHER, "college-el-manar"),
        ("teacher.philo@test.com", "Enseignant Philosophie", UserRole.TEACHER, "lycee-pilote-carthage"),
        # students (4) — profils variés §5.5
        ("eleve1@test.com", "Élève Fallback", UserRole.STUDENT, "lycee-pilote-carthage"),
        ("eleve2@test.com", "Élève Remédiation", UserRole.STUDENT, "lycee-pilote-carthage"),
        ("eleve3@test.com", "Élève Progression", UserRole.STUDENT, "lycee-pilote-carthage"),
        ("eleve4@test.com", "Élève Expiré", UserRole.STUDENT, "lycee-pilote-carthage"),
    ]

    for email, full_name, role, school_slug in user_defs:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            users[email] = existing
            continue
        school = schools.get(school_slug)
        user = User(
            email=email, full_name=full_name, role=role.value,
            hashed_password=password_hash, is_active=True,
            school_id=school.id if school else None,
            niveau_scolaire=NiveauScolaire.NEUVIEME_BASE.value,
        )
        db.add(user)
        db.flush()
        users[email] = user
    db.commit()
    return users


# ============================================================
# §5.2 — NIVEAUX D'ÉTUDE (couverture 1er + 2ème cycle + secondaire)
# ============================================================

NIVEAUX_DEFS = [
    # 1er cycle
    ("4ème année", 1),
    # 2ème cycle
    ("7ème de base", 7),
    ("8ème de base", 8),
    ("9ème de base", 9),
    # Secondaire
    ("1ère année secondaire", 10),
    ("2ème année sciences", 11),
    ("4ème année mathématiques", 14),
]


def seed_niveaux(db):
    niveaux = {}
    for nom, ordre in NIVEAUX_DEFS:
        existing = db.query(NiveauEtude).filter(NiveauEtude.nom == nom).first()
        if existing:
            niveaux[nom] = existing
            continue
        niv = NiveauEtude(nom=nom, ordre=ordre)
        db.add(niv)
        db.flush()
        niveaux[nom] = niv
    db.commit()
    return niveaux


# ============================================================
# §5.2 — MATIÈRES (par niveau)
# ============================================================

MATIERES_DEFS = {
    "4ème année": ["Mathématiques", "Éveil scientifique", "Langue Arabe", "Français"],
    "7ème de base": ["Mathématiques", "Éveil scientifique", "SVT", "Français", "Anglais"],
    "8ème de base": ["Mathématiques", "SVT", "Physique", "Français", "Anglais"],
    "9ème de base": ["Mathématiques", "SVT", "Physique", "Français", "Anglais"],
    "1ère année secondaire": ["Mathématiques", "Physique", "SVT", "Français", "Anglais", "Langue Arabe"],
    "2ème année sciences": ["Mathématiques", "Physique", "SVT", "Philosophie", "Français", "Anglais"],
    "4ème année mathématiques": ["Mathématiques", "Physique", "Philosophie", "Français", "Anglais"],
}


def seed_matieres(db, niveaux):
    matieres = {}  # key: (niveau_nom, matiere_nom) -> Matiere
    for niveau_nom, matiere_list in MATIERES_DEFS.items():
        niv = niveaux.get(niveau_nom)
        if not niv:
            continue
        for mat_nom in matiere_list:
            key = (niveau_nom, mat_nom)
            existing = db.query(Matiere).filter(
                Matiere.niveau_etude_id == niv.id, Matiere.nom == mat_nom
            ).first()
            if existing:
                matieres[key] = existing
                continue
            mat = Matiere(niveau_etude_id=niv.id, nom=mat_nom)
            db.add(mat)
            db.flush()
            matieres[key] = mat
    db.commit()
    return matieres


# ============================================================
# §5.2 — CHAPITRES (2+ par matière clé)
# ============================================================

CHAPTERS_DEFS = {
    # 9ème de base
    ("9ème de base", "Mathématiques"): [
        ("Nombres et calculs", 1), ("Fonctions", 2), ("Géométrie", 3),
    ],
    ("9ème de base", "SVT"): [
        ("Biologie cellulaire", 1), ("Écosystèmes", 2),
    ],
    ("9ème de base", "Physique"): [
        ("Optique", 1), ("Électricité", 2),
    ],
    # 7ème de base
    ("7ème de base", "Mathématiques"): [
        ("Nombres relatifs", 1), ("Fractions", 2),
    ],
    ("7ème de base", "Éveil scientifique"): [
        ("Corps et santé", 1), ("Vivant et environnement", 2),
    ],
    # 4ème année
    ("4ème année", "Mathématiques"): [
        ("Nombres naturels", 1), ("Géométrie plane", 2),
    ],
    ("4ème année", "Éveil scientifique"): [
        ("Corps et santé", 1), ("Société et technologie", 2),
    ],
    # 4ème année maths (Bac)
    ("4ème année mathématiques", "Mathématiques"): [
        ("Analyse", 1), ("Algèbre", 2), ("Géométrie dans l'espace", 3),
    ],
    ("4ème année mathématiques", "Physique"): [
        ("Mécanique", 1), ("Électromagnétisme", 2),
    ],
}


def seed_chapters(db, matieres):
    chapters = {}  # key: (niveau_nom, matiere_nom, chapitre_nom) -> ChapterPathway
    for (niveau_nom, matiere_nom), chap_list in CHAPTERS_DEFS.items():
        mat = matieres.get((niveau_nom, matiere_nom))
        if not mat:
            continue
        for chap_nom, ordre in chap_list:
            key = (niveau_nom, matiere_nom, chap_nom)
            existing = db.query(ChapterPathway).filter(
                ChapterPathway.matiere_id == mat.id, ChapterPathway.nom == chap_nom
            ).first()
            if existing:
                chapters[key] = existing
                continue
            ch = ChapterPathway(matiere_id=mat.id, nom=chap_nom, ordre=ordre)
            db.add(ch)
            db.flush()
            chapters[key] = ch
    db.commit()
    return chapters


# ============================================================
# §5.2 — NOTIONS (2+ par chapitre)
# ============================================================

NOTIONS_DEFS = {
    ("9ème de base", "Mathématiques", "Nombres et calculs"): [
        ("Nombres décimaux", 1), ("Fractions", 2), ("Puissances", 3),
    ],
    ("9ème de base", "Mathématiques", "Fonctions"): [
        ("Fonction linéaire", 1), ("Fonction quadratique", 2),
    ],
    ("9ème de base", "SVT", "Biologie cellulaire"): [
        ("Structure de la cellule", 1), ("Division cellulaire", 2),
    ],
    ("7ème de base", "Mathématiques", "Nombres relatifs"): [
        ("Addition et soustraction", 1), ("Multiplication et division", 2),
    ],
    ("7ème de base", "Éveil scientifique", "Corps et santé"): [
        ("Alimentation", 1), ("Corps humain", 2),
    ],
    ("4ème année", "Mathématiques", "Nombres naturels"): [
        ("Addition et soustraction", 1), ("Multiplication et division", 2),
    ],
    ("4ème année mathématiques", "Mathématiques", "Analyse"): [
        ("Limites et continuité", 1), ("Dérivation", 2),
    ],
    ("4ème année mathématiques", "Physique", "Mécanique"): [
        ("Cinématique", 1), ("Dynamique", 2),
    ],
}


def seed_notions(db, chapters):
    notions = {}
    for (niveau_nom, matiere_nom, chapitre_nom), notion_list in NOTIONS_DEFS.items():
        ch = chapters.get((niveau_nom, matiere_nom, chapitre_nom))
        if not ch:
            continue
        for not_nom, ordre in notion_list:
            key = (niveau_nom, matiere_nom, chapitre_nom, not_nom)
            existing = db.query(Notion).filter(
                Notion.chapitre_id == ch.id, Notion.nom == not_nom
            ).first()
            if existing:
                notions[key] = existing
                continue
            noti = Notion(chapitre_id=ch.id, nom=not_nom, ordre=ordre)
            db.add(noti)
            db.flush()
            notions[key] = noti
    db.commit()
    return notions


# ============================================================
# §5.3 — CONTENUS PAR NOTION (4 cas + 3 statuts validation)
# ============================================================

def seed_contenus(db, notions, users):
    """Create ContenuNotion records covering all §5.3 cases."""
    contenu_counter = 0

    def get_ens(email):
        return users.get(email)

    # Helper: create contenu if not exists
    def mk_contenu(notion_key, niveau, type_r, contenu_text, statut_ped, statut_valid, enseignant_email, valid_par_email=None, commentaire_rejet=None):
        nonlocal contenu_counter
        noti = notions.get(notion_key)
        if not noti:
            return
        existing = db.query(ContenuNotion).filter(
            ContenuNotion.notion_id == noti.id,
            ContenuNotion.niveau_assimilation == niveau,
            ContenuNotion.type_ressource == type_r,
        ).first()
        if existing:
            # Update statut_pedagogique if wrong (idempotent fix)
            if existing.statut_pedagogique != statut_ped:
                existing.statut_pedagogique = statut_ped
                existing.statut_validation_pedagogique = statut_valid
                if valid_par_email:
                    vp = get_ens(valid_par_email)
                    if vp:
                        existing.valide_par = vp.id
                        existing.date_validation = utcnow()
                if commentaire_rejet:
                    existing.commentaire_rejet = commentaire_rejet
                contenu_counter += 1
            return
        enseignant = get_ens(enseignant_email) if enseignant_email else None
        valid_par = get_ens(valid_par_email) if valid_par_email else None
        c = ContenuNotion(
            notion_id=noti.id,
            niveau_assimilation=niveau,
            type_ressource=type_r,
            contenu=contenu_text,
            enseignant_id=enseignant.id if enseignant else None,
            statut_pedagogique=statut_ped,
            statut_validation_pedagogique=statut_valid,
            valide_par=valid_par.id if valid_par else None,
            date_validation=utcnow() if statut_valid == StatutValidationPedagogique.VALIDE.value else None,
            commentaire_rejet=commentaire_rejet,
        )
        db.add(c)
        contenu_counter += 1

    # ─── CAS 1: Notion avec 3 niveaux → publiable ───
    # (9ème, Maths, Nombres et calculs, "Nombres décimaux")
    mk_contenu(
        ("9ème de base", "Mathématiques", "Nombres et calculs", "Nombres décimaux"),
        NiveauAssimilation.REMEDIATION.value, TypeContenu.FICHE.value,
        "Fiche remédiation: nombres décimaux - rappels",
        StatutContenuPedagogique.A.value, StatutValidationPedagogique.VALIDE.value,
        "teacher.maths@test.com", "pedago.lycee@test.com",
    )
    mk_contenu(
        ("9ème de base", "Mathématiques", "Nombres et calculs", "Nombres décimaux"),
        NiveauAssimilation.STANDARD.value, TypeContenu.VIDEO.value,
        "Vidéo cours: opérations sur nombres décimaux",
        StatutContenuPedagogique.A.value, StatutValidationPedagogique.VALIDE.value,
        "teacher.maths@test.com", "pedago.lycee@test.com",
    )
    mk_contenu(
        ("9ème de base", "Mathématiques", "Nombres et calculs", "Nombres décimaux"),
        NiveauAssimilation.AVANCE.value, TypeContenu.BANQUE_EXERCICES.value,
        "Exercices avancés: nombres décimaux complexes",
        StatutContenuPedagogique.A.value, StatutValidationPedagogique.VALIDE.value,
        "teacher.maths@test.com", "pedago.lycee@test.com",
    )

    # ─── CAS 2: Standard + Avancé (pas Remédiation) → publiable, niveaux_manquants=[REMEDIATION] ───
    # (9ème, Maths, Fonctions, "Fonction linéaire")
    mk_contenu(
        ("9ème de base", "Mathématiques", "Fonctions", "Fonction linéaire"),
        NiveauAssimilation.STANDARD.value, TypeContenu.VIDEO.value,
        "Cours: fonction linéaire y = ax + b",
        StatutContenuPedagogique.A.value, StatutValidationPedagogique.VALIDE.value,
        "teacher.maths@test.com", "pedago.lycee@test.com",
    )
    mk_contenu(
        ("9ème de base", "Mathématiques", "Fonctions", "Fonction linéaire"),
        NiveauAssimilation.AVANCE.value, TypeContenu.EVALUATION_IA.value,
        "Évaluation IA: fonctions linéaires avancées",
        StatutContenuPedagogique.A.value, StatutValidationPedagogique.VALIDE.value,
        "teacher.maths@test.com", "pedago.lycee@test.com",
    )

    # ─── CAS 3: Standard uniquement → brouillon ───
    # (9ème, SVT, Biologie cellulaire, "Structure de la cellule")
    mk_contenu(
        ("9ème de base", "SVT", "Biologie cellulaire", "Structure de la cellule"),
        NiveauAssimilation.STANDARD.value, TypeContenu.FICHE.value,
        "Fiche: structure de la cellule",
        StatutContenuPedagogique.A.value, StatutValidationPedagogique.VALIDE.value,
        "teacher.sciences@test.com", "pedago.lycee@test.com",
    )

    # ─── CAS 4: 3 niveaux mais contenu standard supprimé → fallback ───
    # (7ème, Maths, Nombres relatifs, "Addition et soustraction")
    # On crée Remédiation et Avancé, PAS Standard → le fallback ira chercher Standard s'il existe, sinon autre
    mk_contenu(
        ("7ème de base", "Mathématiques", "Nombres relatifs", "Addition et soustraction"),
        NiveauAssimilation.REMEDIATION.value, TypeContenu.FICHE.value,
        "Fiche: addition et soustraction de nombres relatifs",
        StatutContenuPedagogique.A.value, StatutValidationPedagogique.VALIDE.value,
        "teacher.maths@test.com", "pedago.college@test.com",
    )
    mk_contenu(
        ("7ème de base", "Mathématiques", "Nombres relatifs", "Addition et soustraction"),
        NiveauAssimilation.AVANCE.value, TypeContenu.QUIZ.value,
        "Quiz avancé: nombres relatifs complexes",
        StatutContenuPedagogique.A.value, StatutValidationPedagogique.VALIDE.value,
        "teacher.maths@test.com", "pedago.college@test.com",
    )

    # ─── STATUTS DE VALIDATION ───
    # EN_ATTENTE: contenu en attente de validation (invisible élève)
    mk_contenu(
        ("9ème de base", "Mathématiques", "Fonctions", "Fonction quadratique"),
        NiveauAssimilation.STANDARD.value, TypeContenu.VIDEO.value,
        "Cours: fonction quadratique (en attente validation)",
        StatutContenuPedagogique.A.value, StatutValidationPedagogique.EN_ATTENTE.value,
        "teacher.maths@test.com",
    )

    # REJETÉ: contenu rejeté avec commentaire
    mk_contenu(
        ("9ème de base", "SVT", "Écosystèmes", "Vivant et environnement"),
        NiveauAssimilation.STANDARD.value, TypeContenu.FICHE.value,
        "Fiche: écosystèmes (REJETÉ - contenu incomplet)",
        StatutContenuPedagogique.A.value, StatutValidationPedagogique.REJETE.value,
        "teacher.sciences@test.com",
        commentaire_rejet="Contenu incomplet, manque les diagrammes",
    )

    # ─── CONTENUS SUPPLÉMATIRES pour 4ème année maths (Bac) ───
    mk_contenu(
        ("4ème année mathématiques", "Mathématiques", "Analyse", "Limites et continuité"),
        NiveauAssimilation.STANDARD.value, TypeContenu.VIDEO.value,
        "Cours: limites et continuité",
        StatutContenuPedagogique.A.value, StatutValidationPedagogique.VALIDE.value,
        "teacher.maths@test.com", "pedago.lycee@test.com",
    )
    mk_contenu(
        ("4ème année mathématiques", "Mathématiques", "Analyse", "Dérivation"),
        NiveauAssimilation.STANDARD.value, TypeContenu.VIDEO.value,
        "Cours: dérivation",
        StatutContenuPedagogique.A.value, StatutValidationPedagogique.VALIDE.value,
        "teacher.maths@test.com", "pedago.lycee@test.com",
    )
    mk_contenu(
        ("9ème de base", "Mathématiques", "Nombres et calculs", "Nombres décimaux"),
        NiveauAssimilation.STANDARD.value, TypeContenu.VIDEO.value,
        "Vidéo cours: opérations sur nombres décimaux",
        StatutContenuPedagogique.C.value, StatutValidationPedagogique.VALIDE.value,
        "teacher.maths@test.com", "pedago.lycee@test.com",
    )
    mk_contenu(
        ("9ème de base", "Mathématiques", "Nombres et calculs", "Nombres décimaux"),
        NiveauAssimilation.AVANCE.value, TypeContenu.BANQUE_EXERCICES.value,
        "Exercices avancés: nombres décimaux complexes",
        StatutContenuPedagogique.C.value, StatutValidationPedagogique.VALIDE.value,
        "teacher.maths@test.com", "pedago.lycee@test.com",
    )

    # ─── CAS 2: Standard + Avancé (pas Remédiation) → publiable, niveaux_manquants=[REMEDIATION] ───
    # (9ème, Maths, Fonctions, "Fonction linéaire")
    mk_contenu(
        ("9ème de base", "Mathématiques", "Fonctions", "Fonction linéaire"),
        NiveauAssimilation.STANDARD.value, TypeContenu.VIDEO.value,
        "Cours: fonction linéaire y = ax + b",
        StatutContenuPedagogique.C.value, StatutValidationPedagogique.VALIDE.value,
        "teacher.maths@test.com", "pedago.lycee@test.com",
    )
    mk_contenu(
        ("9ème de base", "Mathématiques", "Fonctions", "Fonction linéaire"),
        NiveauAssimilation.AVANCE.value, TypeContenu.EVALUATION_IA.value,
        "Évaluation IA: fonctions linéaires avancées",
        StatutContenuPedagogique.C.value, StatutValidationPedagogique.VALIDE.value,
        "teacher.maths@test.com", "pedago.lycee@test.com",
    )

    # ─── CAS 3: Standard uniquement → brouillon ───
    # (9ème, SVT, Biologie cellulaire, "Structure de la cellule")
    mk_contenu(
        ("9ème de base", "SVT", "Biologie cellulaire", "Structure de la cellule"),
        NiveauAssimilation.STANDARD.value, TypeContenu.FICHE.value,
        "Fiche: structure de la cellule",
        StatutContenuPedagogique.C.value, StatutValidationPedagogique.VALIDE.value,
        "teacher.sciences@test.com", "pedago.lycee@test.com",
    )

    # ─── CAS 4: 3 niveaux mais contenu standard supprimé → fallback ───
    # (7ème, Maths, Nombres relatifs, "Addition et soustraction")
    # On crée Remédiation et Avancé, PAS Standard → le fallback ira chercher Standard s'il existe, sinon autre
    mk_contenu(
        ("7ème de base", "Mathématiques", "Nombres relatifs", "Addition et soustraction"),
        NiveauAssimilation.REMEDIATION.value, TypeContenu.FICHE.value,
        "Fiche: addition et soustraction de nombres relatifs",
        StatutContenuPedagogique.C.value, StatutValidationPedagogique.VALIDE.value,
        "teacher.maths@test.com", "pedago.college@test.com",
    )
    mk_contenu(
        ("7ème de base", "Mathématiques", "Nombres relatifs", "Addition et soustraction"),
        NiveauAssimilation.AVANCE.value, TypeContenu.QUIZ.value,
        "Quiz avancé: nombres relatifs complexes",
        StatutContenuPedagogique.C.value, StatutValidationPedagogique.VALIDE.value,
        "teacher.maths@test.com", "pedago.college@test.com",
    )

    # ─── STATUTS DE VALIDATION ───
    # EN_ATTENTE: contenu en attente de validation (invisible élève)
    mk_contenu(
        ("9ème de base", "Mathématiques", "Fonctions", "Fonction quadratique"),
        NiveauAssimilation.STANDARD.value, TypeContenu.VIDEO.value,
        "Cours: fonction quadratique (en attente validation)",
        StatutContenuPedagogique.C.value, StatutValidationPedagogique.EN_ATTENTE.value,
        "teacher.maths@test.com",
    )

    # REJETÉ: contenu rejeté avec commentaire
    mk_contenu(
        ("9ème de base", "SVT", "Écosystèmes", "Vivant et environnement"),
        NiveauAssimilation.STANDARD.value, TypeContenu.FICHE.value,
        "Fiche: écosystèmes (REJETÉ - contenu incomplet)",
        StatutContenuPedagogique.A.value, StatutValidationPedagogique.REJETE.value,
        "teacher.sciences@test.com",
        commentaire_rejet="Contenu incomplet, manque les diagrammes",
    )

    # ─── CONTENUS SUPPLÉMATIRES pour 4ème année maths (Bac) ───
    mk_contenu(
        ("4ème année mathématiques", "Mathématiques", "Analyse", "Limites et continuité"),
        NiveauAssimilation.STANDARD.value, TypeContenu.VIDEO.value,
        "Cours: limites et continuité",
        StatutContenuPedagogique.C.value, StatutValidationPedagogique.VALIDE.value,
        "teacher.maths@test.com", "pedago.lycee@test.com",
    )
    mk_contenu(
        ("4ème année mathématiques", "Mathématiques", "Analyse", "Dérivation"),
        NiveauAssimilation.STANDARD.value, TypeContenu.VIDEO.value,
        "Cours: dérivation",
        StatutContenuPedagogique.C.value, StatutValidationPedagogique.VALIDE.value,
        "teacher.maths@test.com", "pedago.lycee@test.com",
    )

    db.commit()
    return contenu_counter


# ============================================================
# §5.4 — SPÉCIALITÉS PÉDAGOGIQUES & RESPONSABLES
# ============================================================

def seed_specialites(db, schools, users, matieres):
    # École A: "Sciences" = Mathématiques + Éveil scientifique (2ème cycle)
    school_a = schools.get("lycee-pilote-carthage")
    school_b = schools.get("college-el-manar")

    # ─── École A: Spécialité "Sciences" ───
    spec_a = db.query(SpecialitePedagogique).filter(
        SpecialitePedagogique.ecole_id == school_a.id,
        SpecialitePedagogique.nom == "Sciences",
    ).first()
    if not spec_a:
        spec_a = SpecialitePedagogique(
            ecole_id=school_a.id, nom="Sciences", cycle_scolaire="2eme_cycle"
        )
        db.add(spec_a)
        db.flush()
        # Lier Mathématiques 9ème et Éveil scientifique 7ème
        mat_maths_9 = matieres.get(("9ème de base", "Mathématiques"))
        mat_eveil_7 = matieres.get(("7ème de base", "Éveil scientifique"))
        if mat_maths_9:
            db.add(SpecialitePedagogiqueMatiere(specialite_id=spec_a.id, matiere_id=mat_maths_9.id))
        if mat_eveil_7:
            db.add(SpecialitePedagogiqueMatiere(specialite_id=spec_a.id, matiere_id=mat_eveil_7.id))

    # ─── École B: Spécialité "Sciences" (Maths + Eveil + Techno = preuve que le regroupement est configurable) ───
    spec_b = db.query(SpecialitePedagogique).filter(
        SpecialitePedagogique.ecole_id == school_b.id,
        SpecialitePedagogique.nom == "Sciences",
    ).first()
    if not spec_b:
        spec_b = SpecialitePedagogique(
            ecole_id=school_b.id, nom="Sciences", cycle_scolaire="1er_cycle"
        )
        db.add(spec_b)
        db.flush()
        mat_maths_7 = matieres.get(("7ème de base", "Mathématiques"))
        mat_eveil_7b = matieres.get(("7ème de base", "Éveil scientifique"))
        if mat_maths_7:
            db.add(SpecialitePedagogiqueMatiere(specialite_id=spec_b.id, matiere_id=mat_maths_7.id))
        if mat_eveil_7b:
            db.add(SpecialitePedagogiqueMatiere(specialite_id=spec_b.id, matiere_id=mat_eveil_7b.id))

    db.commit()

    # ─── RESPONSABLES PÉDAGOGIQUES ───
    niv_7 = db.query(NiveauEtude).filter(NiveauEtude.nom == "7ème de base").first()
    niv_9 = db.query(NiveauEtude).filter(NiveauEtude.nom == "9ème de base").first()
    niv_bac = db.query(NiveauEtude).filter(NiveauEtude.nom == "4ème année mathématiques").first()

    # Resp1: Sciences École A, scope = [7ème, 9ème]
    resp1_user = users.get("pedago.lycee@test.com")
    existing_resp1 = db.query(ResponsablePedagogique).filter(
        ResponsablePedagogique.user_id == resp1_user.id,
        ResponsablePedagogique.specialite_id == spec_a.id,
    ).first() if resp1_user else None
    if not existing_resp1 and resp1_user:
        resp1 = ResponsablePedagogique(user_id=resp1_user.id, specialite_id=spec_a.id)
        db.add(resp1)
        db.flush()
        if niv_7:
            resp1.niveaux_etude_scope.append(niv_7)
        if niv_9:
            resp1.niveaux_etude_scope.append(niv_9)

    # Resp2: Sciences École A, scope = [Bac] — scopes disjoints
    resp2_user = users.get("pedago.college@test.com")
    existing_resp2 = db.query(ResponsablePedagogique).filter(
        ResponsablePedagogique.user_id == resp2_user.id,
        ResponsablePedagogique.specialite_id == spec_a.id,
    ).first() if resp2_user else None
    if not existing_resp2 and resp2_user and niv_bac:
        resp2 = ResponsablePedagogique(user_id=resp2_user.id, specialite_id=spec_a.id)
        db.add(resp2)
        db.flush()
        resp2.niveaux_etude_scope.append(niv_bac)

    db.commit()


# ============================================================
# §5.5 — ÉLÈVES — profils d'assimilation + scores + notifications
# ============================================================

def seed_student_profiles(db, users, chapters, matieres):
    now = utcnow()

    # ─── Élève 1: Aucun profil chapitre → fallback matière (Pack Mono-Matière) ───
    # Pas de ProfilAssimilationEleve → niveau_effectif retourne défaut matière
    eleve1 = users.get("eleve1@test.com")
    if eleve1:
        # Pack Mono-Matière pour 9ème
        _create_pack_purchase(db, eleve1, "Pack Mono-Mathématiques 9ème",
                              "9ème de base", ["Mathématiques"], 29.99,
                              PurchaserType.STUDENT.value, now)

    # ─── Élève 2: Profil Remédiation, scores bas stables (Pack À la Carte) ───
    eleve2 = users.get("eleve2@test.com")
    ch_maths_9 = chapters.get(("9ème de base", "Mathématiques", "Nombres et calculs"))
    if eleve2 and ch_maths_9:
        _createOrUpdate_profile(db, eleve2.id, ch_maths_9.id,
                                NiveauAssimilation.REMEDIATION.value,
                                SourceChangement.TEST_INITIAL.value,
                                StatutValidationProfil.AUTO_APPLIQUE.value)
        # 5 scores bas et stables
        for i in range(5):
            _create_score(db, eleve2.id, ch_maths_9.id, 25.0 + (i * 2), now - timedelta(days=10 - i))
        _create_pack_purchase(db, eleve2, "Pack À la Carte 9ème",
                              "9ème de base", ["Mathématiques", "SVT"], 49.99,
                              PurchaserType.STUDENT.value, now)

    # ─── Élève 3: Standard → progression vers Avancé (Pack Sur-Mesure) ───
    eleve3 = users.get("eleve3@test.com")
    if eleve3 and ch_maths_9:
        _createOrUpdate_profile(db, eleve3.id, ch_maths_9.id,
                                NiveauAssimilation.STANDARD.value,
                                SourceChangement.TEST_INITIAL.value,
                                StatutValidationProfil.AUTO_APPLIQUE.value)
        # Scores en progression franchissant le seuil avance (75)
        progression_scores = [45, 55, 65, 72, 80]
        for i, s in enumerate(progression_scores):
            _create_score(db, eleve3.id, ch_maths_9.id, float(s), now - timedelta(days=10 - i))
        # Pack Sur-Mesure: scope initial = {SVT: REMEDIATION, Maths: AVANCE}
        _create_pack_purchase(db, eleve3, "Pack Sur-Mesure 9ème",
                              "9ème de base", None, 79.99,
                              PurchaserType.STUDENT.value, now)

    # ─── Élève 4: Notification expirée, silence = acceptation (Pack Full Level) ───
    eleve4 = users.get("eleve4@test.com")
    ch_svt_9 = chapters.get(("9ème de base", "SVT", "Biologie cellulaire"))
    if eleve4 and ch_svt_9:
        profil = _createOrUpdate_profile(db, eleve4.id, ch_svt_9.id,
                                          NiveauAssimilation.AVANCE.value,
                                          SourceChangement.AJUSTEMENT_AUTO.value,
                                          StatutValidationProfil.AUTO_APPLIQUE.value)
        if profil:
            # Notification expirée (date_limite dépassée, action_prise = AUCUNE)
            existing_notif = db.query(NotificationReorientation).filter(
                NotificationReorientation.profil_assimilation_id == profil.id,
            ).first()
            if not existing_notif:
                notif = NotificationReorientation(
                    profil_assimilation_id=profil.id,
                    enseignant_id=users.get("teacher.sciences@test.com", eleve4).id,
                    date_notification=now - timedelta(days=30),
                    date_limite_action=now - timedelta(days=2),  # expirée
                    action_prise=ActionReorientation.AUCUNE.value,
                )
                db.add(notif)
        _create_pack_purchase(db, eleve4, "Pack Full Level 9ème",
                              "9ème de base", None, 99.99,
                              PurchaserType.STUDENT.value, now)

    db.commit()


def _createOrUpdate_profile(db, eleve_id, chapitre_id, niveau, source, statut):
    existing = db.query(ProfilAssimilationEleve).filter(
        ProfilAssimilationEleve.eleve_id == eleve_id,
        ProfilAssimilationEleve.chapitre_id == chapitre_id,
    ).first()
    if existing:
        return existing
    profil = ProfilAssimilationEleve(
        eleve_id=eleve_id, chapitre_id=chapitre_id,
        niveau_assimilation_courant=niveau,
        source_changement=source,
        date=utcnow(),
        statut_validation=statut,
    )
    db.add(profil)
    db.flush()
    return profil


def _create_score(db, eleve_id, chapitre_id, score, date):
    existing = db.query(HistoriqueScoreEleve).filter(
        HistoriqueScoreEleve.eleve_id == eleve_id,
        HistoriqueScoreEleve.chapitre_id == chapitre_id,
        HistoriqueScoreEleve.score == score,
    ).first()
    if existing:
        return
    h = HistoriqueScoreEleve(
        eleve_id=eleve_id, chapitre_id=chapitre_id,
        score=score, date=date,
    )
    db.add(h)


def _create_pack_purchase(db, user, pack_name, niveau_scolaire, matieres_list, price, purchaser_type, now):
    pack = db.query(StudyPack).filter(StudyPack.name == pack_name).first()
    if not pack:
        pack = StudyPack(
            name=pack_name, description=f"Pack {niveau_scolaire}",
            niveau_scolaire=niveau_scolaire, matieres=matieres_list,
            price=price, currency="TND", validity_duration_days=365,
            status=PackStatus.PUBLISHED.value, owner_type="eduai_catalog",
            created_by=user.id,
        )
        db.add(pack)
        db.flush()

    existing_purchase = db.query(PackPurchase).filter(
        PackPurchase.pack_id == pack.id,
        PackPurchase.student_id == user.id,
    ).first()
    if existing_purchase:
        return

    purchase = PackPurchase(
        pack_id=pack.id,
        purchaser_type=purchaser_type,
        student_id=user.id,
        valid_from=now,
        valid_until=now + timedelta(days=365),
        status=PackPurchaseStatus.ACTIVE.value,
        amount_paid=price,
        currency="TND",
    )
    db.add(purchase)


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 60)
    print("EDUAI Learning — Seed Adaptive Pathway Data (§5 spec)")
    print("=" * 60)

    db = SessionLocal()
    try:
        print("[1/7] Ecoles...")
        schools = seed_schools(db)
        print(f"  → {len(schools)} écoles")

        print("[2/7] Utilisateurs...")
        users = seed_users(db, schools)
        print(f"  → {len(users)} utilisateurs")

        print("[3/7] Niveaux d'étude...")
        niveaux = seed_niveaux(db)
        print(f"  → {len(niveaux)} niveaux")

        print("[4/7] Matières...")
        matieres = seed_matieres(db, niveaux)
        print(f"  → {len(matieres)} matières")

        print("[5/7] Chapitres + Notions...")
        chapters = seed_chapters(db, matieres)
        notions = seed_notions(db, chapters)
        print(f"  → {len(chapters)} chapitres, {len(notions)} notions")

        print("[6/7] Contenus par notion...")
        nb_contenus = seed_contenus(db, notions, users)
        print(f"  → {nb_contenus} contenus créés")

        print("[7/7] Spécialités + profils élèves...")
        seed_specialites(db, schools, users, matieres)
        seed_student_profiles(db, users, chapters, matieres)
        print("  → spécialités et profils créés")

        print("\n" + "=" * 60)
        print("RÉCAPITULATIF — Comptes de test")
        print("=" * 60)
        print("  Tous les mots de passe: password123\n")
        for email, user in sorted(users.items()):
            school_name = ""
            if user.school_id:
                s = db.query(School).filter(School.id == user.school_id).first()
                school_name = f" ({s.name})" if s else ""
            print(f"  {user.role:20s} {email:30s}{school_name}")

        print(f"\n  Niveaux: {', '.join(niveaux.keys())}")
        print(f"  Matières: {len(matieres)} créées")
        print(f"  Chapitres: {len(chapters)}, Notions: {len(notions)}")

        # Verify publication status
        print("\n" + "=" * 60)
        print("VÉRIFICATION — Statut publication")
        print("=" * 60)
        from app.services.adaptive_pathway import statut_publication
        for key, noti in notions.items():
            result = statut_publication(noti.id, db)
            print(f"  {key[-1]:30s} → {result['statut']:10s} manquants={result['niveaux_manquants']}")

    finally:
        db.close()

    print("\n✅ Seed terminé avec succès!")


if __name__ == "__main__":
    main()
