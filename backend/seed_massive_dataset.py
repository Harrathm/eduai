"""
Seed massive dataset for stress-testing EDUAI Learning platform.
IDEMPOTENT: uses try/except and existence checks — safe to run multiple times.

Creates:
  - Courses for every niveau × matiere (official arborescence)
  - PackDefinition (Gratuit/Basique/Silver/Golden) per niveau
  - ~20 test students with varied subscription/progression scenarios
  - 4 teachers covering all states
  - Enrollments, abonnements, wallet transactions

Usage:
    cd backend
    python seed_massive_dataset.py
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if not os.environ.get("DATABASE_URL"):
    os.environ["DATABASE_URL"] = "postgresql+pg8000://postgres:gill4264@localhost:5432/eduai"

from sqlalchemy import text
from app.db.session import engine, SessionLocal
from app.models import (
    Base, School, User, Course, Module, Lesson,
    PackDefinition, Abonnement,
    CourseEnrollment, WalletTransaction,
    NiveauEtude, Matiere,
    UserRole, SubscriptionPlan, VerificationStatus,
    EnrollmentStatus, WalletPool, CourseStatus, ContentType,
    SchoolType,
)
from app.core.security import get_password_hash

PASSWORD = "passeword123"
NOW = datetime.now(timezone.utc)


def utcnow():
    return datetime.now(timezone.utc)


# ============================================================
# 1. SCHOOL & ADMIN
# ============================================================
def ensure_school_and_admin(db):
    """Create or get the test school and super admin."""
    school = db.query(School).filter(School.slug == "eduai-massive-test").first()
    if not school:
        school = School(
            name="EDUAI Massive Test School",
            slug="eduai-massive-test",
            domain="massive-test.eduai.tn",
            school_type=SchoolType.DEMO,
            subscription_tier="institution",
            max_users=5000,
            is_active=True,
        )
        db.add(school)
        db.flush()
        print(f"  [NEW] School: {school.name} (id={school.id})")
    else:
        print(f"  [EXISTS] School: {school.name} (id={school.id})")

    admin = db.query(User).filter(User.email == "admin.massive@eduai.tn").first()
    if not admin:
        admin = User(
            email="admin.massive@eduai.tn",
            hashed_password=get_password_hash(PASSWORD),
            full_name="Admin Massive Test",
            role=UserRole.SUPER_ADMIN,
            school_id=school.id,
            is_active=True,
            is_approved=True,
        )
        db.add(admin)
        db.flush()
        print(f"  [NEW] Admin: {admin.email}")
    else:
        print(f"  [EXISTS] Admin: {admin.email}")

    return school, admin


# ============================================================
# 2. TEACHERS (all states)
# ============================================================
def ensure_teachers(db, school):
    """Create 4 teachers covering all subscription/approval states."""
    teachers_spec = [
        {
            "email": "teacher.state.a@eduai.tn",
            "full_name": "Prof. State A (Approved, Paid)",
            "is_approved": True,
            "subscription_plan": SubscriptionPlan.INDEPENDENT_PAID.value,
            "verification_status": VerificationStatus.VERIFIED.value,
            "is_partner": True,
        },
        {
            "email": "teacher.state.b@eduai.tn",
            "full_name": "Prof. State B (Not Approved)",
            "is_approved": False,
            "subscription_plan": SubscriptionPlan.TRIAL.value,
            "verification_status": VerificationStatus.UNVERIFIED.value,
            "is_partner": False,
        },
        {
            "email": "teacher.state.c@eduai.tn",
            "full_name": "Prof. State C (Trial)",
            "is_approved": True,
            "subscription_plan": SubscriptionPlan.TRIAL.value,
            "verification_status": VerificationStatus.PENDING.value,
            "is_partner": False,
        },
        {
            "email": "teacher.partner@eduai.tn",
            "full_name": "Prof. Partner (Revenue Share)",
            "is_approved": True,
            "subscription_plan": SubscriptionPlan.INDEPENDENT_PAID.value,
            "verification_status": VerificationStatus.VERIFIED.value,
            "is_partner": True,
        },
    ]

    teachers = []
    for spec in teachers_spec:
        existing = db.query(User).filter(User.email == spec["email"]).first()
        if existing:
            print(f"  [EXISTS] Teacher: {spec['email']}")
            teachers.append(existing)
            continue

        t = User(
            email=spec["email"],
            hashed_password=get_password_hash(PASSWORD),
            full_name=spec["full_name"],
            role=UserRole.TEACHER,
            school_id=school.id,
            is_active=True,
            is_approved=spec["is_approved"],
            subscription_plan=spec["subscription_plan"],
            verification_status=spec["verification_status"],
            is_partner=spec["is_partner"],
        )
        db.add(t)
        db.flush()
        print(f"  [NEW] Teacher: {spec['email']} (approved={spec['is_approved']}, plan={spec['subscription_plan']})")
        teachers.append(t)

    return teachers


# ============================================================
# 3. COURSES (1 per niveau × matiere)
# ============================================================
def ensure_courses(db, school, teachers):
    """Create 1 Course + 1 Module + 1 Lesson for every niveau × matiere."""
    niveaux = db.query(NiveauEtude).order_by(NiveauEtude.ordre).all()
    if not niveaux:
        print("  [WARN] No NiveauEtude found — run seed_arborescence_officielle.py first!")
        return 0

    author = teachers[0]  # Use the approved teacher as author
    count = 0
    batch = []

    for niv in niveaux:
        matieres = db.query(Matiere).filter(Matiere.niveau_etude_id == niv.id).all()
        for mat in matieres:
            title = f"Cours de {mat.nom} - {niv.nom}"
            slug = f"cours-{mat.nom[:30].strip()}-{niv.nom[:30].strip()}".replace(" ", "-").replace("/", "-").lower()

            existing = db.query(Course).filter(
                Course.school_id == school.id,
                Course.niveau_scolaire == niv.nom,
                Course.category == mat.nom,
            ).first()
            if existing:
                continue

            course = Course(
                school_id=school.id,
                author_id=author.id,
                title=title,
                short_description=f"Cours de {mat.nom} pour le niveau {niv.nom}",
                slug=slug,
                category=mat.nom,
                niveau_scolaire=niv.nom,
                category_cible="Scolaire",
                tag_pack_requis="Basic",
                language="fr",
                status=CourseStatus.PUBLISHED,
                is_published=True,
                is_active_version=True,
                visibility="public_catalog",
                owner_type="eduai_catalog",
                total_modules=1,
                total_lessons=1,
                total_duration_minutes=45,
            )
            db.add(course)
            db.flush()

            module = Module(
                course_id=course.id,
                title="Module 1: Introduction",
                order=1,
            )
            db.add(module)
            db.flush()

            lesson = Lesson(
                module_id=module.id,
                school_id=school.id,
                teacher_id=author.id,
                title="Leçon 1: Introduction",
                content_type=ContentType.TEXT,
                content_text=f"Contenu d'introduction au cours de {mat.nom} pour le niveau {niv.nom}.",
                order=1,
                duration_minutes=45,
            )
            db.add(lesson)
            batch.append(course)
            count += 1

            if count % 50 == 0:
                db.flush()
                print(f"    ... {count} courses created so far")

    db.flush()
    return count


# ============================================================
# 4. PACK DEFINITIONS (4 per niveau)
# ============================================================
def ensure_pack_definitions(db):
    """Create 4 PackDefinition per niveau: Gratuit, Basique, Silver, Golden."""
    niveaux = db.query(NiveauEtude).order_by(NiveauEtude.ordre).all()
    pack_specs = [
        {
            "tier": "Gratuit",
            "nom_template": "Pack Gratuit - {niveau}",
            "description": "Accès limité : 3 leçons par trimestre",
            "prix_tnd": 0.0,
            "features": {"max_lessons_per_trimester": 3, "matieres_count": 0},
        },
        {
            "tier": "Basique",
            "nom_template": "Pack Basique - {niveau}",
            "description": "Accès à 2 matières au choix",
            "prix_tnd": 9.9,
            "features": {"max_matieres": 2},
        },
        {
            "tier": "Silver",
            "nom_template": "Pack Silver - {niveau}",
            "description": "Accès à 4 matières au choix",
            "prix_tnd": 19.9,
            "features": {"max_matieres": 4},
        },
        {
            "tier": "Golden",
            "nom_template": "Pack Golden - {niveau}",
            "description": "Accès illimité + Soft Skills",
            "prix_tnd": 39.9,
            "features": {"unlimited": True, "soft_skills": True},
        },
    ]

    count = 0
    for niv in niveaux:
        for spec in pack_specs:
            nom = spec["nom_template"].format(niveau=niv.nom)
            existing = db.query(PackDefinition).filter(
                PackDefinition.niveau_scolaire == niv.nom,
                PackDefinition.tier == spec["tier"],
            ).first()
            if existing:
                continue

            pack = PackDefinition(
                nom=nom,
                description=spec["description"],
                tier=spec["tier"],
                niveau_scolaire=niv.nom,
                prix_tnd=spec["prix_tnd"],
                features=spec["features"],
                est_actif=True,
            )
            db.add(pack)
            count += 1

    db.flush()
    return count


# ============================================================
# 5. STUDENTS (20 with varied scenarios)
# ============================================================
def ensure_students(db, school, teachers):
    """Create ~20 test students covering all edge-case scenarios."""
    # Pick a few different niveaux for variety
    niveaux = db.query(NiveauEtude).order_by(NiveauEtude.ordre).all()
    niv_7 = next((n for n in niveaux if "7" in n.nom), niveaux[0])
    niv_9 = next((n for n in niveaux if "9" in n.nom), niveaux[0])
    niv_1s = next((n for n in niveaux if "1ère Année Secondaire" in n.nom), niveaux[-1])
    niv_2s = next((n for n in niveaux if "2ème Sciences" in n.nom), niveaux[-1])
    niv_bac = next((n for n in niveaux if "Bac Math" in n.nom), niveaux[-1])

    student_specs = [
        # ── Progression scenarios ──
        {
            "email": "student.progress.0@eduai.tn",
            "full_name": "Élève Progress 0%",
            "niveau": niv_7.nom,
            "progress": 0,
            "enrolled": False,
            "abonnement": None,
        },
        {
            "email": "student.progress.50@eduai.tn",
            "full_name": "Élève Progress 50%",
            "niveau": niv_9.nom,
            "progress": 50,
            "enrolled": True,
            "abonnement": None,
        },
        {
            "email": "student.progress.100@eduai.tn",
            "full_name": "Élève Progress 100%",
            "niveau": niv_1s.nom,
            "progress": 100,
            "enrolled": True,
            "abonnement": None,
        },
        # ── Payment & quota scenarios ──
        {
            "email": "student.paid.t1@eduai.tn",
            "full_name": "Élève Payé T1",
            "niveau": niv_2s.nom,
            "abonnement_tier": "Basique",
            "abonnement_statut": "actif",
            "enrolled": True,
            "progress": 30,
            "wallet_credits": 50,
        },
        {
            "email": "student.unpaid.t1@eduai.tn",
            "full_name": "Élève Impayé T1",
            "niveau": niv_9.nom,
            "abonnement_tier": "Basique",
            "abonnement_statut": "grace",
            "enrolled": False,
        },
        {
            "email": "student.expired@eduai.tn",
            "full_name": "Élève Abonnement Expiré",
            "niveau": niv_7.nom,
            "abonnement_tier": "Silver",
            "abonnement_statut": "expire",
            "enrolled": False,
        },
        {
            "email": "student.invalidated@eduai.tn",
            "full_name": "Élève Invalide (changement niveau)",
            "niveau": niv_1s.nom,
            "abonnement_tier": "Basique",
            "abonnement_statut": "invalide",
            "enrolled": False,
        },
        # ── ABAC (matieres) scenarios ──
        {
            "email": "student.abac.basic1@eduai.tn",
            "full_name": "Élève Basic Maths+Physique",
            "niveau": niv_2s.nom,
            "abonnement_tier": "Basique",
            "abonnement_statut": "actif",
            "matieres_config": ["رياضيات", "علوم فيزيائية"],
            "enrolled": True,
            "progress": 20,
        },
        {
            "email": "student.abac.basic2@eduai.tn",
            "full_name": "Élève Basic Arabe+Français",
            "niveau": niv_9.nom,
            "abonnement_tier": "Basique",
            "abonnement_statut": "actif",
            "matieres_config": ["العربية", "الفرنسية"],
            "enrolled": True,
            "progress": 15,
        },
        {
            "email": "student.abac.silver1@eduai.tn",
            "full_name": "Élève Silver 4 matières",
            "niveau": niv_1s.nom,
            "abonnement_tier": "Silver",
            "abonnement_statut": "actif",
            "matieres_config": ["رياضيات", "علوم طبيعية", "علوم فيزيائية", "العربية"],
            "enrolled": True,
            "progress": 40,
        },
        # ── Tier scenarios ──
        {
            "email": "student.golden@eduai.tn",
            "full_name": "Élève Golden (illimité)",
            "niveau": niv_bac.nom,
            "abonnement_tier": "Golden",
            "abonnement_statut": "actif",
            "enrolled": True,
            "progress": 60,
            "wallet_credits": 200,
        },
        {
            "email": "student.free@eduai.tn",
            "full_name": "Élève Gratuit (bloqué 3 leçons)",
            "niveau": niv_7.nom,
            "abonnement_tier": "Gratuit",
            "abonnement_statut": "actif",
            "enrolled": True,
            "progress": 10,
        },
        # ── Extra students for volume ──
        {
            "email": "student.extra.1@eduai.tn",
            "full_name": "Élève Extra 1",
            "niveau": niv_9.nom,
            "enrolled": True,
            "progress": 25,
        },
        {
            "email": "student.extra.2@eduai.tn",
            "full_name": "Élève Extra 2",
            "niveau": niv_1s.nom,
            "enrolled": True,
            "progress": 70,
        },
        {
            "email": "student.extra.3@eduai.tn",
            "full_name": "Élève Extra 3",
            "niveau": niv_2s.nom,
            "enrolled": True,
            "progress": 45,
        },
        {
            "email": "student.extra.4@eduai.tn",
            "full_name": "Élève Extra 4",
            "niveau": niv_bac.nom,
            "enrolled": True,
            "progress": 80,
        },
        {
            "email": "student.extra.5@eduai.tn",
            "full_name": "Élève Extra 5",
            "niveau": niv_7.nom,
            "enrolled": True,
            "progress": 55,
        },
        {
            "email": "student.extra.6@eduai.tn",
            "full_name": "Élève Extra 6",
            "niveau": niv_9.nom,
            "enrolled": True,
            "progress": 35,
        },
        {
            "email": "student.extra.7@eduai.tn",
            "full_name": "Élève Extra 7",
            "niveau": niv_1s.nom,
            "enrolled": True,
            "progress": 90,
        },
        {
            "email": "student.extra.8@eduai.tn",
            "full_name": "Élève Extra 8",
            "niveau": niv_2s.nom,
            "enrolled": True,
            "progress": 10,
        },
    ]

    created_students = []
    for spec in student_specs:
        email = spec["email"]
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print(f"  [EXISTS] Student: {email}")
            created_students.append((existing, spec))
            continue

        student = User(
            email=email,
            hashed_password=get_password_hash(PASSWORD),
            full_name=spec["full_name"],
            role=UserRole.STUDENT,
            school_id=school.id,
            niveau_scolaire=spec.get("niveau"),
            is_active=True,
            is_approved=True,
        )
        db.add(student)
        db.flush()
        print(f"  [NEW] Student: {email} (niveau={spec.get('niveau', 'N/A')})")
        created_students.append((student, spec))

    return created_students


# ============================================================
# 6. ABONNEMENTS, ENROLLMENTS, WALLET
# ============================================================
def ensure_subscriptions_and_enrollments(db, school, students_with_specs, teachers):
    """Create abonnements, enrollments, and wallet transactions per student spec."""
    enroll_count = 0
    abonnement_count = 0
    wallet_count = 0

    for student, spec in students_with_specs:
        # ── Abonnement ──
        tier = spec.get("abonnement_tier")
        statut = spec.get("abonnement_statut")
        if tier:
            pack = db.query(PackDefinition).filter(
                PackDefinition.niveau_scolaire == spec.get("niveau"),
                PackDefinition.tier == tier,
            ).first()

            existing_ab = db.query(Abonnement).filter(
                Abonnement.user_id == student.id,
                Abonnement.pack_id == pack.id if pack else -1,
            ).first()

            if not existing_ab and pack:
                debut = NOW - timedelta(days=90)
                fin = debut + timedelta(days=365)
                grace_fin = fin + timedelta(days=30) if statut == "grace" else None

                ab = Abonnement(
                    user_id=student.id,
                    pack_id=pack.id,
                    statut=statut or "actif",
                    debut=debut,
                    fin=fin,
                    grace_fin=grace_fin,
                    matieres_config=spec.get("matieres_config"),
                )
                db.add(ab)
                abonnement_count += 1

                # Wallet credit for paid students
                credits = spec.get("wallet_credits", 0)
                if credits > 0:
                    wt = WalletTransaction(
                        user_id=student.id,
                        pool=WalletPool.PURCHASED,
                        amount=float(credits),
                    )
                    db.add(wt)
                    wallet_count += 1

        # ── Enrollment ──
        if spec.get("enrolled"):
            niveau_nom = spec.get("niveau")
            course = db.query(Course).filter(
                Course.niveau_scolaire == niveau_nom,
                Course.school_id == school.id,
            ).first()

            if course:
                existing_enr = db.query(CourseEnrollment).filter(
                    CourseEnrollment.student_id == student.id,
                    CourseEnrollment.course_id == course.id,
                ).first()

                if not existing_enr:
                    progress = spec.get("progress", 0)
                    status = EnrollmentStatus.COMPLETED if progress == 100 else EnrollmentStatus.ACTIVE
                    enr = CourseEnrollment(
                        student_id=student.id,
                        course_id=course.id,
                        status=status,
                        progress_percent=progress,
                        completed_at=NOW - timedelta(days=5) if progress == 100 else None,
                    )
                    db.add(enr)
                    enroll_count += 1

    db.flush()
    return enroll_count, abonnement_count, wallet_count


# ============================================================
# 7. REPORT
# ============================================================
def print_report(db, school, admin, teachers, students, course_count, pack_count,
                 enroll_count, abonnement_count, wallet_count):
    total_courses = db.query(Course).filter(Course.school_id == school.id).count()
    total_packs = db.query(PackDefinition).count()
    total_enrollments = db.query(CourseEnrollment).count()
    total_users = db.query(User).filter(User.school_id == school.id).count()
    total_abonnements = db.query(Abonnement).count()
    total_wallet = db.query(WalletTransaction).count()

    print("\n" + "=" * 70)
    print("  RAPPORT FINAL - JEU DE DONNEES MASSIF")
    print("=" * 70)

    print("\n  School: %s (id=%d)" % (school.name, school.id))
    print("  Admin: %s" % admin.email)

    print(f"\n  -- Cours & Parcours --")
    print(f"  Cours crees cette execution:   {course_count}")
    print(f"  Total cours en base:           {total_courses}")
    print(f"  Chaque cours a: 1 Module + 1 Lesson rattaches")
    print(f"  category_cible = 'Scolaire', tag_pack_requis = 'Basic'")
    print(f"  is_published = True, visibility = 'public_catalog'")

    print(f"\n  -- Packs Commerciaux --")
    print(f"  Packs crees cette execution:   {pack_count}")
    print(f"  Total packs en base:           {total_packs}")
    print(f"  4 packs par niveau: Gratuit (0 TND), Basique (9.9 TND),")
    print(f"                        Silver (19.9 TND), Golden (39.9 TND)")

    print(f"\n  -- Enseignants --")
    for t in teachers:
        status = "Approved" if t.is_approved else "Pending"
        partner = " (Partner)" if t.is_partner else ""
        print("    %-40s %-12s plan=%-20s%s" % (t.email, status, t.subscription_plan, partner))

    print(f"\n  -- Eleves de Test ({len(students)}) --")
    for student, spec in students:
        niveau = spec.get("niveau", "N/A")[:25]
        tier = spec.get("abonnement_tier", "--")
        statut = spec.get("abonnement_statut", "--")
        progress = spec.get("progress", "--")
        matieres = ""
        if spec.get("matieres_config"):
            matieres = " matieres=%s" % len(spec["matieres_config"])
        print("    %-40s niv=%-25s tier=%-10s statut=%-10s prog=%s%s" % (
            student.email, niveau, tier, statut, progress, matieres
        ))

    print(f"\n  -- Statistiques Globales --")
    print(f"  Utilisateurs totaux:     {total_users}")
    print(f"  Cours en base:           {total_courses}")
    print(f"  PackDefinitions:         {total_packs}")
    print(f"  Abonnements:             {total_abonnements}")
    print(f"  Enrollments:             {total_enrollments}")
    print(f"  WalletTransactions:      {total_wallet}")

    print(f"\n  Mot de passe pour tous les comptes: {PASSWORD}")
    print(f"  Endpoint login: POST /auth/login (username=email, password={PASSWORD})")
    print("=" * 70)


# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 70)
    print("  SEED MASSIVE DATASET — EDUAI Learning")
    print("  Idempotent: safe to run multiple times")
    print("=" * 70)

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        print("\n[1/6] School & Admin ...")
        school, admin = ensure_school_and_admin(db)

        print("\n[2/6] Teachers ...")
        teachers = ensure_teachers(db, school)

        print("\n[3/6] Courses (niveau × matiere) ...")
        course_count = ensure_courses(db, school, teachers)
        print("  Nouveaux cours crees: %d" % course_count)

        print("\n[4/6] Pack Definitions ...")
        pack_count = ensure_pack_definitions(db)
        print("  Nouveaux packs crees: %d" % pack_count)

        print("\n[5/6] Students & Scenarios ...")
        students = ensure_students(db, school, teachers)

        print("\n[6/6] Subscriptions, Enrollments, Wallet ...")
        enroll_count, abonnement_count, wallet_count = ensure_subscriptions_and_enrollments(
            db, school, students, teachers
        )
        print(f"  Nouveaux enrollments: {enroll_count}")
        print(f"  Nouveaux abonnements: {abonnement_count}")
        print(f"  Nouvelles wallet txns: {wallet_count}")

        db.commit()

        print_report(db, school, admin, teachers, students, course_count, pack_count,
                     enroll_count, abonnement_count, wallet_count)

    except Exception as e:
        db.rollback()
        print(f"\n  ERREUR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
