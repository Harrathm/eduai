"""
EDUAI Learning — Seed Script
============================
Populates the database with realistic test data for full-platform testing.
Idempotent: checks existence by email/slug before inserting.

Usage:
    cd backend
    python seed_db.py
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
    Base, School, User, Course, Module, Lesson, Quiz, QuizQuestion, QuizOption,
    WalletTransaction, CourseEnrollment, StudyPack, PackPurchase,
    NiveauEtude, Matiere, ChapterPathway, ParentEnfant,
    BulkSeatVoucher, TeacherRevenueLedger,
    UserRole, SubscriptionTier, SchoolType, WalletPool,
    CourseStatus, PedagogicalStatus, CourseOwnerType, CourseVisibility,
    EnrollmentStatus, PackStatus, PackPurchaseStatus, PurchaserType,
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
    print("  EDUAI Learning — Seed Script")
    print("=" * 60)

    print("\n[1/9] Creating tables ...")
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()

    try:
        # ── SCHOOLS ────────────────────────────────────────────────────
        print("\n[2/9] Creating schools ...")

        school_a, created = get_or_create(
            session, School, slug="carthage",
            defaults=dict(name="Lycee Carthage", school_type=SchoolType.REAL.value,
                          subscription_tier=SubscriptionTier.SCHOOL.value,
                          is_active=True, max_users=200),
        )
        print("  %s Lycee Carthage (id=%d)" % (_lbl(created), school_a.id))

        school_b, created = get_or_create(
            session, School, slug="el-jem",
            defaults=dict(name="Lycee El Jem", school_type=SchoolType.REAL.value,
                          subscription_tier=SubscriptionTier.SCHOOL.value,
                          is_active=True, max_users=200),
        )
        print("  %s Lycee El Jem (id=%d)" % (_lbl(created), school_b.id))
        session.flush()

        # ── USERS ──────────────────────────────────────────────────────
        print("\n[3/9] Creating users ...")

        users_data = [
            dict(email="superadmin@eduai.tn", full_name="Super Admin EDUAI",
                 role=UserRole.SUPER_ADMIN.value, school_id=None),
            dict(email="pedagogical.admin@eduai.tn", full_name="Admin Pedagogique Global",
                 role=UserRole.PEDAGOGICAL_ADMIN.value, school_id=None),
            dict(email="admin.carthage@eduai.tn", full_name="Directeur Carthage",
                 role=UserRole.ADMIN_SCHOOL.value, school_id=school_a.id),
            dict(email="pedago.lead.carthage@eduai.tn", full_name="Resp Pedagogique Carthage",
                 role=UserRole.PEDAGOGICAL_LEAD.value, school_id=school_a.id),
            dict(email="prof.maths.carthage@eduai.tn", full_name="Prof Maths Carthage",
                 role=UserRole.TEACHER.value, school_id=school_a.id, is_approved=True),
            dict(email="prof.physique.carthage@eduai.tn", full_name="Prof Physique Carthage",
                 role=UserRole.TEACHER.value, school_id=school_a.id, is_approved=True),
            dict(email="eleve1.carthage@eduai.tn", full_name="Ahmed Ben Ali",
                 role=UserRole.STUDENT.value, school_id=school_a.id, niveau_scolaire="9eme de base"),
            dict(email="eleve2.carthage@eduai.tn", full_name="Fatma Trabelsi",
                 role=UserRole.STUDENT.value, school_id=school_a.id, niveau_scolaire="2eme annee sciences"),
            dict(email="eleve3.carthage@eduai.tn", full_name="Youssef Khelifi",
                 role=UserRole.STUDENT.value, school_id=school_a.id, niveau_scolaire="9eme de base"),
            dict(email="parent.carthage@eduai.tn", full_name="Parent Ben Ali",
                 role=UserRole.PARENT.value, school_id=school_a.id),
            dict(email="admin.eljem@eduai.tn", full_name="Directeur El Jem",
                 role=UserRole.ADMIN_SCHOOL.value, school_id=school_b.id),
            dict(email="pedago.lead.eljem@eduai.tn", full_name="Resp Pedagogique El Jem",
                 role=UserRole.PEDAGOGICAL_LEAD.value, school_id=school_b.id),
            dict(email="prof.maths.eljem@eduai.tn", full_name="Prof Maths El Jem",
                 role=UserRole.TEACHER.value, school_id=school_b.id, is_approved=True),
            dict(email="prof.arabe.eljem@eduai.tn", full_name="Prof Arabe El Jem",
                 role=UserRole.TEACHER.value, school_id=school_b.id, is_approved=True),
            dict(email="eleve1.eljem@eduai.tn", full_name="Amira Bouazizi",
                 role=UserRole.STUDENT.value, school_id=school_b.id, niveau_scolaire="9eme de base"),
            dict(email="eleve2.eljem@eduai.tn", full_name="Omar Mansour",
                 role=UserRole.STUDENT.value, school_id=school_b.id, niveau_scolaire="1ere annee secondaire"),
            dict(email="eleve3.eljem@eduai.tn", full_name="Nour Haddad",
                 role=UserRole.STUDENT.value, school_id=school_b.id, niveau_scolaire="9eme de base"),
            dict(email="parent.eljem@eduai.tn", full_name="Parent Bouazizi",
                 role=UserRole.PARENT.value, school_id=school_b.id),
        ]

        U = {}
        for ud in users_data:
            user, is_new = get_or_create(
                session, User, email=ud["email"],
                defaults=dict(full_name=ud["full_name"], role=ud["role"],
                              school_id=ud.get("school_id"), hashed_password=HASHED_PASSWORD,
                              is_active=True, onboarding_complete=True,
                              niveau_scolaire=ud.get("niveau_scolaire"),
                              is_approved=ud.get("is_approved")),
            )
            U[ud["email"]] = user
            print("  %s %s (%s)" % (_lbl(is_new), ud["email"], ud["role"]))
        session.flush()

        # ── PARENT–STUDENT LINKS ───────────────────────────────────────
        print("\n[4/9] Linking parent -> students ...")

        parent_a = U["parent.carthage@eduai.tn"]
        for child_email in ["eleve1.carthage@eduai.tn", "eleve3.carthage@eduai.tn"]:
            link, is_new = get_or_create(
                session, ParentEnfant,
                parent_user_id=parent_a.id, eleve_id=U[child_email].id,
            )
            print("  %s parent.carthage -> %s" % (_lbl(is_new), U[child_email].full_name))

        parent_b = U["parent.eljem@eduai.tn"]
        link, is_new = get_or_create(
            session, ParentEnfant,
            parent_user_id=parent_b.id, eleve_id=U["eleve1.eljem@eduai.tn"].id,
        )
        print("  %s parent.eljem -> %s" % (_lbl(is_new), U["eleve1.eljem@eduai.tn"].full_name))
        session.flush()

        # ── WALLET TRANSACTIONS ────────────────────────────────────────
        print("\n[5/9] Creating wallet transactions ...")

        wallet_emails = [
            "eleve1.carthage@eduai.tn", "eleve2.carthage@eduai.tn", "eleve3.carthage@eduai.tn",
            "eleve1.eljem@eduai.tn", "eleve2.eljem@eduai.tn", "eleve3.eljem@eduai.tn",
            "prof.maths.carthage@eduai.tn", "prof.physique.carthage@eduai.tn",
            "prof.maths.eljem@eduai.tn", "prof.arabe.eljem@eduai.tn",
        ]

        for email in wallet_emails:
            uid = U[email].id
            existing = session.query(WalletTransaction).filter_by(user_id=uid).first()
            if existing:
                print("  [EXISTS] Wallet for %s" % email)
                continue
            session.add(WalletTransaction(
                user_id=uid, pool=WalletPool.TRIAL, amount=100.0,
                expires_at=NOW + timedelta(days=30)))
            session.add(WalletTransaction(
                user_id=uid, pool=WalletPool.DT_PURCHASED, amount=50.0))
            print("  [NEW] Wallet for %s: 100 tokens (trial) + 50.00 DT" % email)
        session.flush()

        # ── ADAPTIVE PATHWAY ───────────────────────────────────────────
        print("\n[6/9] Creating adaptive pathway ...")

        niveau, is_new = get_or_create(
            session, NiveauEtude, nom="9eme de base", defaults=dict(ordre=9))
        print("  %s NiveauEtude: 9eme de base (id=%d)" % (_lbl(is_new), niveau.id))

        matiere, is_new = get_or_create(
            session, Matiere, nom="Mathematiques",
            defaults=dict(niveau_etude_id=niveau.id, remediation_threshold=40,
                          standard_threshold=75, avance_threshold=75))
        print("  %s Matiere: Mathematiques (id=%d)" % (_lbl(is_new), matiere.id))

        chapitre, is_new = get_or_create(
            session, ChapterPathway, nom="Algebre",
            defaults=dict(matiere_id=matiere.id, ordre=1))
        print("  %s ChapterPathway: Algebre (id=%d)" % (_lbl(is_new), chapitre.id))
        session.flush()

        # ── COURSES + LMS ──────────────────────────────────────────────
        print("\n[7/9] Creating courses with LMS content ...")

        t_a1 = U["prof.maths.carthage@eduai.tn"]
        t_a2 = U["prof.physique.carthage@eduai.tn"]
        t_b1 = U["prof.maths.eljem@eduai.tn"]
        t_b2 = U["prof.arabe.eljem@eduai.tn"]
        superadmin = U["superadmin@eduai.tn"]

        courses_data = [
            dict(title="Algebre - 9eme de base", slug="algebre-9eme-carthage",
                 school_id=school_a.id, author_id=t_a1.id,
                 owner_type=CourseOwnerType.SCHOOL.value, niveau_scolaire="9eme de base",
                 price=None, visibility=CourseVisibility.SCHOOL_ONLY.value),
            dict(title="Physique - 2eme annee sciences", slug="physique-2eme-carthage",
                 school_id=school_a.id, author_id=t_a2.id,
                 owner_type=CourseOwnerType.SCHOOL.value, niveau_scolaire="2eme annee sciences",
                 price=None, visibility=CourseVisibility.SCHOOL_ONLY.value),
            dict(title="Algebre - 9eme (El Jem)", slug="algebre-9eme-eljem",
                 school_id=school_b.id, author_id=t_b1.id,
                 owner_type=CourseOwnerType.SCHOOL.value, niveau_scolaire="9eme de base",
                 price=None, visibility=CourseVisibility.SCHOOL_ONLY.value),
            dict(title="Arabe - 9eme (El Jem)", slug="arabe-9eme-eljem",
                 school_id=school_b.id, author_id=t_b2.id,
                 owner_type=CourseOwnerType.SCHOOL.value, niveau_scolaire="9eme de base",
                 price=None, visibility=CourseVisibility.SCHOOL_ONLY.value),
            dict(title="Cours Particulier Maths - 3eme", slug="cours-particulier-maths-3eme",
                 school_id=school_a.id, author_id=t_a1.id,
                 owner_type=CourseOwnerType.INDEPENDENT_TEACHER.value,
                 niveau_scolaire="3eme annee mathematiques",
                 price=15.0, visibility=CourseVisibility.PUBLIC_CATALOG.value),
        ]

        created_courses = []
        for cd in courses_data:
            course, is_new = get_or_create(
                session, Course, slug=cd["slug"],
                defaults=dict(
                    title=cd["title"], school_id=cd["school_id"], author_id=cd["author_id"],
                    owner_type=cd["owner_type"], niveau_scolaire=cd["niveau_scolaire"],
                    price=cd["price"], visibility=cd["visibility"],
                    status=CourseStatus.PUBLISHED.value,
                    pedagogical_status=PedagogicalStatus.APPROVED_LOCAL.value,
                    is_published=True, total_modules=1, total_lessons=2,
                    description="Cours de %s pour le programme tunisien." % cd["title"]),
            )
            created_courses.append(course)
            print("  %s Course: %s (id=%d)" % (_lbl(is_new), cd["title"], course.id))
        session.flush()

        # LMS content per course
        for course in created_courses:
            existing_mod = session.query(Module).filter_by(course_id=course.id).first()
            if existing_mod:
                print("    [EXISTS] LMS for course %d" % course.id)
                continue

            mod = Module(course_id=course.id, title="Module 1 - %s" % course.title,
                         description="Module principal", order=1)
            session.add(mod)
            session.flush()

            lt = Lesson(module_id=mod.id, school_id=course.school_id, teacher_id=course.author_id,
                        title="Lecon 1 - Introduction", lesson_type="text", content_type="text",
                        content_text="Contenu de %s. Concepts fondamentaux." % course.title,
                        order=1, duration_minutes=15, is_free=True)
            session.add(lt)
            session.flush()

            lv = Lesson(module_id=mod.id, school_id=course.school_id, teacher_id=course.author_id,
                        title="Lecon 2 - Video", lesson_type="video", content_type="video",
                        video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                        video_duration_seconds=600, order=2, duration_minutes=10)
            session.add(lv)
            session.flush()

            quiz = Quiz(lesson_id=lt.id, title="Quiz - %s" % course.title,
                        description="Quiz de validation", passing_score_percent=70, total_points=2,
                        school_id=course.school_id)
            session.add(quiz)
            session.flush()

            q1 = QuizQuestion(quiz_id=quiz.id, question_text="Solution de x + 3 = 7 ?",
                              question_type="mcq", points=1, order_index=1)
            session.add(q1)
            session.flush()
            session.add_all([
                QuizOption(question_id=q1.id, option_text="x = 3", is_correct=False, order_index=1),
                QuizOption(question_id=q1.id, option_text="x = 4", is_correct=True, order_index=2),
                QuizOption(question_id=q1.id, option_text="x = 5", is_correct=False, order_index=3),
                QuizOption(question_id=q1.id, option_text="x = 10", is_correct=False, order_index=4),
            ])

            q2 = QuizQuestion(quiz_id=quiz.id, question_text="Que vaut 2^5 ?",
                              question_type="mcq", points=1, order_index=2)
            session.add(q2)
            session.flush()
            session.add_all([
                QuizOption(question_id=q2.id, option_text="16", is_correct=False, order_index=1),
                QuizOption(question_id=q2.id, option_text="32", is_correct=True, order_index=2),
                QuizOption(question_id=q2.id, option_text="64", is_correct=False, order_index=3),
                QuizOption(question_id=q2.id, option_text="10", is_correct=False, order_index=4),
            ])

            print("    [NEW] Module + 2 Lessons + Quiz for course %d" % course.id)
        session.flush()

        # ── STUDY PACK ─────────────────────────────────────────────────
        print("\n[8/9] Creating study packs ...")

        pack, is_new = get_or_create(
            session, StudyPack, name="Pack 9eme de base - Toutes matieres",
            defaults=dict(description="Acces a tous les cours du 9eme de base (2025-2026).",
                          niveau_scolaire="9eme de base", price=30.0, currency="TND",
                          validity_duration_days=365, status=PackStatus.PUBLISHED.value,
                          owner_type="eduai_catalog", created_by=superadmin.id))
        print("  %s StudyPack: Pack 9eme (id=%d)" % (_lbl(is_new), pack.id))

        student_a1 = U["eleve1.carthage@eduai.tn"]
        existing_purchase = session.query(PackPurchase).filter_by(
            pack_id=pack.id, student_id=student_a1.id).first()
        if not existing_purchase:
            session.add(PackPurchase(
                pack_id=pack.id, purchaser_type=PurchaserType.STUDENT.value,
                student_id=student_a1.id, valid_from=NOW, valid_until=NOW + timedelta(days=30),
                status=PackPurchaseStatus.ACTIVE.value, amount_paid=30.0, currency="TND",
                transaction_id="seed_%s" % secrets.token_hex(6)))
            print("  [NEW] PackPurchase: eleve1.carthage -> Pack 9eme (30 TND)")
        else:
            print("  [EXISTS] PackPurchase: eleve1.carthage -> Pack 9eme")
        session.flush()

        # ── SOFT SKILLS CATALOG ───────────────────────────────────────
        print("\n[8.5/9] Creating soft skills courses ...")
        soft_skills_data = [
            ("Gestion du stress et examens", "Techniques de gestion du stress avant les examens et periodes intenses.", "beginner"),
            ("Methodes d'apprentissage efficaces", "Strategies pedagogiques pour optimiser la memorisation et la comprehension.", "intermediate"),
            ("Communication et prise de parole", "Developper ses competences en communication orale et ecrite.", "beginner"),
            ("Travail en equipe et collaboration", "Techniques de travail collaboratif et resolution de conflits.", "intermediate"),
            ("Orientation scolaire et professionnelle", "Decouvrir son profil et choisir son parcours d'orientation.", "beginner"),
            ("Gestion du temps et organisation", "Planification, priorisation et outils d'organisation personnelle.", "beginner"),
            ("Leadership et initiative", "Developper ses qualites de leader et prendre des initiatives.", "advanced"),
            ("Pensee critique et resolution de problemes", "Methodes d'analyse et prise de decision rationnelle.", "intermediate"),
        ]
        for ss_name, ss_desc, ss_level in soft_skills_data:
            ss, is_new = get_or_create(
                session, Course, title=ss_name,
                defaults=dict(description=ss_desc, category="soft_skills", level=ss_level,
                              status=CourseStatus.PUBLISHED.value, is_published=True,
                              owner_type=CourseOwnerType.EDUAI_CATALOG.value,
                              visibility=CourseVisibility.PUBLIC_CATALOG.value,
                              school_id=school_a.id,
                              author_id=superadmin.id))
            print("  %s SoftSkill: %s (id=%d)" % (_lbl(is_new), ss_name, ss.id))
        session.flush()

        # ── ENROLLMENTS ────────────────────────────────────────────────
        print("\n[9/9] Creating enrollments ...")

        course_a = created_courses[0]
        existing = session.query(CourseEnrollment).filter_by(
            student_id=student_a1.id, course_id=course_a.id).first()
        if not existing:
            session.add(CourseEnrollment(
                student_id=student_a1.id, course_id=course_a.id,
                status=EnrollmentStatus.ACTIVE.value, progress_percent=0))
            print("  [NEW] Enrollment: eleve1.carthage -> %s" % course_a.title)
        else:
            print("  [EXISTS] Enrollment: eleve1.carthage -> %s" % course_a.title)

        student_b1 = U["eleve1.eljem@eduai.tn"]
        course_b = created_courses[2]
        existing2 = session.query(CourseEnrollment).filter_by(
            student_id=student_b1.id, course_id=course_b.id).first()
        if not existing2:
            session.add(CourseEnrollment(
                student_id=student_b1.id, course_id=course_b.id,
                status=EnrollmentStatus.ACTIVE.value, progress_percent=0))
            print("  [NEW] Enrollment: eleve1.eljem -> %s" % course_b.title)
        else:
            print("  [EXISTS] Enrollment: eleve1.eljem -> %s" % course_b.title)
        session.flush()

        # ── GOVERNANCE TEST DATA ─────────────────────────────────────
        print("\n[10/10] Creating governance test data ...")

        # --- 1. Multi-role user (Context Switcher) ---
        multirole, is_new = get_or_create(
            session, User, email="multirole@eduai.tn",
            defaults=dict(
                full_name="Admin Multi-Roles Carthage",
                role=UserRole.ADMIN_SCHOOL.value,
                school_id=school_a.id,
                hashed_password=HASHED_PASSWORD,
                is_active=True, onboarding_complete=True,
                roles=["admin_school", "pedagogical_lead"],
                active_context_role="admin_school",
            ),
        )
        print("  %s multirole@eduai.tn (roles=['admin_school','pedagogical_lead'])" % _lbl(is_new))

        # --- 2. Teacher Partner (Revenue Share) ---
        partner, is_new = get_or_create(
            session, User, email="partner@eduai.tn",
            defaults=dict(
                full_name="Prof Partenaire Maths",
                role=UserRole.TEACHER.value,
                school_id=school_a.id,
                hashed_password=HASHED_PASSWORD,
                is_active=True, onboarding_complete=True,
                is_approved=True,
                is_partner=True,
            ),
        )
        print("  %s partner@eduai.tn (is_partner=True)" % _lbl(is_new))
        session.flush()

        # Ensure partner has at least one course with lessons
        partner_course, is_new = get_or_create(
            session, Course, slug="algo-partner-carthage",
            defaults=dict(
                title="Algorithmique Avancee - Partner",
                school_id=school_a.id, author_id=partner.id,
                owner_type=CourseOwnerType.INDEPENDENT_TEACHER.value,
                niveau_scolaire="9eme de base",
                price=10.0, visibility=CourseVisibility.PUBLIC_CATALOG.value,
                status=CourseStatus.PUBLISHED.value,
                pedagogical_status=PedagogicalStatus.APPROVED_LOCAL.value,
                is_published=True, total_modules=1, total_lessons=1,
                description="Cours d'algo par un enseignant partenaire."),
        )
        print("  %s Course partner: %s (id=%d)" % (_lbl(is_new), partner_course.title, partner_course.id))

        existing_partner_mod = session.query(Module).filter_by(course_id=partner_course.id).first()
        if not existing_partner_mod:
            pm = Module(course_id=partner_course.id, title="Module Algo Partner",
                        description="Module principal", order=1)
            session.add(pm)
            session.flush()
            pl = Lesson(module_id=pm.id, school_id=school_a.id, teacher_id=partner.id,
                        title="Lecon Algorithmique Base", lesson_type="text", content_type="text",
                        content_text="Introduction aux algorithmes fondamentaux.",
                        order=1, duration_minutes=20, is_free=True)
            session.add(pl)
            session.flush()
            print("    [NEW] Module + Lesson for partner course %d" % partner_course.id)
        session.flush()

        # --- 3. Course ABAC tag_pack_requis=Golden (Upsell 402) ---
        golden_course, is_new = get_or_create(
            session, Course, slug="cours-exclusive-golden",
            defaults=dict(
                title="Cours Exclusif Golden - Physique Quantique",
                school_id=school_a.id, author_id=t_a2.id,
                owner_type=CourseOwnerType.SCHOOL.value,
                niveau_scolaire="9eme de base",
                price=None, visibility=CourseVisibility.PUBLIC_CATALOG.value,
                status=CourseStatus.PUBLISHED.value,
                pedagogical_status=PedagogicalStatus.APPROVED_LOCAL.value,
                is_published=True, total_modules=1, total_lessons=1,
                tag_pack_requis="Golden",
                description="Cours avance reserve aux abonnes Golden."),
        )
        print("  %s Course Golden (tag_pack_requis=Golden): %s (id=%d)" % (
            _lbl(is_new), golden_course.title, golden_course.id))
        session.flush()

        # --- 4. Teacher Training course (Bulk Seats) ---
        teacher_training, is_new = get_or_create(
            session, Course, slug="teacher-training-pedagogie",
            defaults=dict(
                title="Formation Enseignants - Pedagogie Numerique",
                school_id=school_a.id, author_id=superadmin.id,
                owner_type=CourseOwnerType.EDUAI_CATALOG.value,
                niveau_scolaire="9eme de base",
                price=None, visibility=CourseVisibility.PUBLIC_CATALOG.value,
                status=CourseStatus.PUBLISHED.value,
                pedagogical_status=PedagogicalStatus.APPROVED_LOCAL.value,
                is_published=True, total_modules=1, total_lessons=1,
                category_cible="Teacher_Training",
                description="Formation pour enseignants sur les outils numeriques."),
        )
        print("  %s Teacher Training (category_cible=Teacher_Training): %s (id=%d)" % (
            _lbl(is_new), teacher_training.title, teacher_training.id))
        session.flush()

        # --- 5. Bulk Seat Vouchers ---
        voucher_codes = ["BULK-SEED-0001", "BULK-SEED-0002", "BULK-SEED-0003"]
        for code in voucher_codes:
            existing_v = session.query(BulkSeatVoucher).filter_by(code=code).first()
            if not existing_v:
                session.add(BulkSeatVoucher(
                    school_id=school_a.id,
                    formation_id=teacher_training.id,
                    code=code,
                    status="unused",
                ))
                print("  [NEW] Voucher: %s (school=Carthage, formation=Teacher Training)" % code)
            else:
                print("  [EXISTS] Voucher: %s" % code)
        session.flush()

        # ── DONE ───────────────────────────────────────────────────────
        session.commit()

        print("\n" + "=" * 60)
        print("  Seed complete!")
        print("=" * 60)
        print("  Schools:         2 (Carthage, El Jem)")
        print("  Users:           %d" % (len(U) + 2))  # +2 for multirole + partner
        print("  Courses:         %d" % (len(created_courses) + 3))  # +3 governance courses
        print("  Wallet entries:  %d" % (len(wallet_emails) * 2))
        print("  Study Packs:     1")
        print("  Enrollments:     2")
        print("  Vouchers:        3 (unused)")
        print("  Password:        passeword123")
        print()
        print("  Governance users:")
        print("    multirole@eduai.tn / passeword123  (Context Switcher)")
        print("    partner@eduai.tn / passeword123    (Revenue Share)")
        print("  ABAC course:  tag_pack_requis=Golden -> 402 UpsellModal")
        print("  Bulk Seats:   3 vouchers BULK-SEED-* (Teacher Training)")
        print("=" * 60)

    except Exception as e:
        session.rollback()
        print("\n  ERROR: %s" % e)
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed()
