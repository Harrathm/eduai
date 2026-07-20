"""
Full database seed script for EDUAI Learning.
Creates all tables and populates with comprehensive test data.
Run: cd backend && .venv\Scripts\python.exe seed_full.py
"""
import os
import sys
from datetime import datetime, timedelta, timezone
from uuid import uuid4

os.environ.setdefault("DATABASE_URL", "postgresql+pg8000://postgres:gill4264@localhost:5432/eduai")

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.models_lms import LmsBase
from app.models import (
    School, User, Course, Module, Lesson, Transaction, TokenPackage,
    ClassRoom, CourseEnrollment, ClassroomEnrollment, Assignment, Submission,
    Document, Message, PlatformSetting, TeacherRegistration,
    Quiz, QuizQuestion, QuizOption, QuizAttempt, QuizAnswer,
    Note, Bookmark, Progress, Certificate,
    UserRole, SubscriptionTier, EnrollmentStatus, TransactionType,
    Currency, ContentType, CourseStatus, DocumentStatus, TeacherRegistrationStatus,
    MessageType, SchoolType, SubscriptionPlan, VerificationStatus,
    WalletTransaction, WalletPool, BillableFeature,
    AuditLog, MediaAsset, SchoolCourseAccess,
    TeacherClass, ClassCourseAccess, StudentEnrollment,
    Payment, AIContentReport, PedagogicalEscalation, TeacherReassignment,
    Subscription,
)
from app.models_ai_conversations import AIConversation, AIChatMessage
from app.core.security import get_password_hash
from app.services.wallet import add_credits

DATABASE_URL = os.environ["DATABASE_URL"]
engine = create_engine(DATABASE_URL, echo=False)

def utcnow():
    return datetime.now(timezone.utc)

def seed():
    print("Connecting to PostgreSQL...")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        print(f"  {result.scalar()}")

    print("Dropping existing tables...")
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
        conn.execute(text("GRANT ALL ON SCHEMA public TO postgres;"))
        conn.execute(text("GRANT ALL ON SCHEMA public TO public;"))

    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    LmsBase.metadata.create_all(bind=engine)

    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # ============================================================
        # SCHOOLS
        # ============================================================
        print("Seeding schools...")
        school_main = School(
            name="EDUAI Academy", slug="eduai-academy",
            domain="eduai.edu", school_type=SchoolType.REAL,
            subscription_tier=SubscriptionTier.INSTITUTION,
            primary_color="#FF6B35", max_users=1000,
        )
        school_b = School(
            name="Lycée La Réussite", slug="lycee-reussite",
            domain="reussite.edu", school_type=SchoolType.REAL,
            subscription_tier=SubscriptionTier.SCHOOL,
            primary_color="#3B82F6", max_users=200,
        )
        school_demo = School(
            name="Demo School", slug="demo-school",
            domain="demo.edu", school_type=SchoolType.DEMO,
            subscription_tier=SubscriptionTier.FREE,
            primary_color="#10B981", max_users=50,
        )
        db.add_all([school_main, school_b, school_demo])
        db.flush()

        # ============================================================
        # USERS — 6 roles + multiple students/teachers
        # ============================================================
        print("Seeding users...")
        pw = get_password_hash("password123")
        now = utcnow()

        # --- Super Admin ---
        super_admin = User(
            email="superadmin@eduai.edu", hashed_password=pw,
            full_name="Super Admin EDUAI", role=UserRole.SUPER_ADMIN,
            school_id=school_main.id, is_active=True, is_approved=True,
            token_balance=9999, dt_balance=9999,
        )
        # --- Pedagogical Admin (platform-wide) ---
        pedagogical_admin = User(
            email="pedago.admin@eduai.edu", hashed_password=pw,
            full_name="Admin Pédagogique National", role=UserRole.PEDAGOGICAL_ADMIN,
            school_id=school_main.id, is_active=True, is_approved=True,
            token_balance=500, dt_balance=200,
        )
        # --- School Admin A ---
        admin_a = User(
            email="admin.eduai@eduai.edu", hashed_password=pw,
            full_name="Directeur EDUAI Academy", role=UserRole.ADMIN_SCHOOL,
            school_id=school_main.id, is_active=True, is_approved=True,
            token_balance=200, dt_balance=100,
        )
        # --- Pedagogical Lead (scoped to school B) ---
        pedagogical_lead = User(
            email="pedago.lead@reussite.edu", hashed_password=pw,
            full_name="Référent Pédagogique Reussite", role=UserRole.PEDAGOGICAL_LEAD,
            school_id=school_b.id, is_active=True, is_approved=True,
            token_balance=150, dt_balance=80,
        )
        # --- School Admin B ---
        admin_b = User(
            email="admin.reussite@reussite.edu", hashed_password=pw,
            full_name="Directeur La Réussite", role=UserRole.ADMIN_SCHOOL,
            school_id=school_b.id, is_active=True, is_approved=True,
            token_balance=150, dt_balance=60,
        )

        # --- Teachers (4 teachers across 2 schools) ---
        teacher_1 = User(
            email="prof.math@eduai.edu", hashed_password=pw,
            full_name="Prof. Ahmed Benali", role=UserRole.TEACHER,
            school_id=school_main.id, is_active=True, is_approved=True,
            subscription_plan=SubscriptionPlan.INDEPENDENT_PAID,
            verification_status=VerificationStatus.VERIFIED,
            token_balance=300, dt_balance=150,
        )
        teacher_2 = User(
            email="prof.fr@eduai.edu", hashed_password=pw,
            full_name="Prof. Sophie Martin", role=UserRole.TEACHER,
            school_id=school_main.id, is_active=True, is_approved=True,
            subscription_plan=SubscriptionPlan.SCHOOL_AFFILIATED,
            token_balance=250, dt_balance=100,
        )
        teacher_3 = User(
            email="prof.info@reussite.edu", hashed_password=pw,
            full_name="Prof. Youssef Trabelsi", role=UserRole.TEACHER,
            school_id=school_b.id, is_active=True, is_approved=True,
            subscription_plan=SubscriptionPlan.TRIAL,
            is_demo_account=False,
            token_balance=200, dt_balance=80,
        )
        teacher_4 = User(
            email="prof.sciences@reussite.edu", hashed_password=pw,
            full_name="Prof. Leila Gharbi", role=UserRole.TEACHER,
            school_id=school_b.id, is_active=True, is_approved=True,
            subscription_plan=SubscriptionPlan.SCHOOL_AFFILIATED,
            token_balance=180, dt_balance=70,
        )

        # --- Students (6 across both schools) ---
        students = []
        student_data = [
            ("student1@eduai.edu", "Karim Mansour", school_main.id),
            ("student2@eduai.edu", "Fatma Zouari", school_main.id),
            ("student3@eduai.edu", "Ali Bouchama", school_main.id),
            ("student1@reussite.edu", "Nour Hentati", school_b.id),
            ("student2@reussite.edu", "Omar Saadi", school_b.id),
            ("student3@reussite.edu", "Amira Ben Salah", school_b.id),
        ]
        for email, name, sid in student_data:
            s = User(
                email=email, hashed_password=pw,
                full_name=name, role=UserRole.STUDENT,
                school_id=sid, is_active=True, is_approved=True,
                token_balance=100, dt_balance=0,
            )
            students.append(s)

        all_users = [super_admin, pedagogical_admin, admin_a, pedagogical_lead, admin_b,
                     teacher_1, teacher_2, teacher_3, teacher_4] + students
        db.add_all(all_users)
        db.flush()

        # ============================================================
        # WALLET TRANSACTIONS (initial credits)
        # ============================================================
        print("Seeding wallet transactions...")
        for u in all_users:
            if u.token_balance > 0:
                add_credits(db, u.id, WalletPool.SUBSCRIPTION, u.token_balance,
                           expires_at=now + timedelta(days=365))
            if u.dt_balance > 0:
                add_credits(db, u.id, WalletPool.PURCHASED, int(u.dt_balance))

        # ============================================================
        # TOKEN PACKAGES
        # ============================================================
        print("Seeding token packages...")
        packages = [
            TokenPackage(school_id=school_main.id, name="Starter", tokens=100, price_dt=10.0, bonus_tokens=10),
            TokenPackage(school_id=school_main.id, name="Pro", tokens=500, price_dt=40.0, bonus_tokens=75),
            TokenPackage(school_id=school_main.id, name="Enterprise", tokens=2000, price_dt=120.0, bonus_tokens=400),
            TokenPackage(school_id=school_b.id, name="Pack Lycée", tokens=300, price_dt=25.0, bonus_tokens=30),
        ]
        db.add_all(packages)
        db.flush()

        # ============================================================
        # COURSES (8 courses — mix of paid, free, different statuses)
        # ============================================================
        print("Seeding courses...")
        courses = []

        # --- EDUAI Academy courses ---
        c1 = Course(
            school_id=school_main.id, author_id=teacher_1.id,
            title="Mathématiques Fondamentales",
            short_description="Algèbre, géométrie et analyse pour débutants",
            description="Cours complet couvrant les bases des mathématiques : équations, fonctions, vecteurs, et introduction à l'analyse.",
            category="Sciences", level="beginner", language="fr",
            price=25.0, currency="TND", price_tokens=50, price_dt=25,
            status=CourseStatus.PUBLISHED, is_published=True,
            visibility="public_catalog", owner_type="school",
            total_modules=3, total_lessons=12, total_duration_minutes=720,
            slug="maths-fondamentales",
        )
        c2 = Course(
            school_id=school_main.id, author_id=teacher_2.id,
            title="Français — Communication Écrite",
            short_description="Maîtriser la rédaction et l'expression écrite",
            description="Techniques de rédaction, style, grammaire avancée et production de textes argumentés.",
            category="Langues", level="intermediate", language="fr",
            price=30.0, currency="TND", price_tokens=60, price_dt=30,
            status=CourseStatus.PUBLISHED, is_published=True,
            visibility="public_catalog", owner_type="school",
            total_modules=2, total_lessons=8, total_duration_minutes=480,
            slug="francais-communication",
        )
        c3 = Course(
            school_id=school_main.id, author_id=teacher_1.id,
            title="Physique — Mécanique",
            short_description="Lois de Newton, énergie, mouvement",
            description="Cours de physique sur la mécanique newtonienne, l'énergie cinétique et potentielle.",
            category="Sciences", level="intermediate", language="fr",
            price=0, currency="TND", price_tokens=0, price_dt=0,
            status=CourseStatus.PUBLISHED, is_published=True,
            visibility="public_catalog", owner_type="school",
            total_modules=2, total_lessons=6, total_duration_minutes=360,
            slug="physique-mecanique",
        )
        c4 = Course(
            school_id=school_main.id, author_id=teacher_2.id,
            title="Histoire — Tunisie Moderne",
            short_description="De l'indépendance à nos jours",
            description="L'histoire de la Tunisie depuis 1956 : politique, économie, société.",
            category="Humanités", level="beginner", language="fr",
            status=CourseStatus.DRAFT, is_published=False,
            visibility="private", owner_type="school",
            slug="histoire-tunisie",
        )

        # --- Lycée La Réussite courses ---
        c5 = Course(
            school_id=school_b.id, author_id=teacher_3.id,
            title="Informatique — Python Bases",
            short_description="Initiation à la programmation Python",
            description="Variables, boucles, fonctions, et projets pratiques en Python.",
            category="Informatique", level="beginner", language="fr",
            price=15.0, currency="TND", price_tokens=30, price_dt=15,
            status=CourseStatus.PUBLISHED, is_published=True,
            visibility="school_only", owner_type="school",
            total_modules=2, total_lessons=10, total_duration_minutes=600,
            slug="python-bases",
        )
        c6 = Course(
            school_id=school_b.id, author_id=teacher_4.id,
            title="SVT — Biologie Cellulaire",
            short_description="Cellule, mitose, métabolisme",
            description="Comprendre la structure cellulaire, la division cellulaire et les grandes voies métaboliques.",
            category="Sciences", level="intermediate", language="fr",
            price=0, currency="TND", price_tokens=0, price_dt=0,
            status=CourseStatus.PUBLISHED, is_published=True,
            visibility="school_only", owner_type="school",
            total_modules=3, total_lessons=9, total_duration_minutes=540,
            slug="svt-biologie-cellulaire",
        )

        # --- Pending review ---
        c7 = Course(
            school_id=school_main.id, author_id=teacher_1.id,
            title="Arabe — Littérature Classique",
            short_description="Poésie et prose des siècles d'or",
            description="Analyse de textes littéraires arabes classiques.",
            category="Langues", level="advanced", language="ar",
            status=CourseStatus.PENDING, is_published=False,
            visibility="private", owner_type="school",
            pedagogical_status="pending_review",
            slug="arabe-litterature",
        )

        # --- Archived ---
        c8 = Course(
            school_id=school_main.id, author_id=teacher_2.id,
            title="Anglais — Session 2024 (Archived)",
            short_description="Cours d'anglais général — session passée",
            description="Cours termine, archive pour reference.",
            category="Langues", level="beginner", language="en",
            price=20.0, currency="TND", price_tokens=40, price_dt=20,
            status=CourseStatus.ARCHIVED, is_published=False,
            visibility="private", owner_type="school",
            slug="anglais-2024-archived",
        )

        courses = [c1, c2, c3, c4, c5, c6, c7, c8]
        db.add_all(courses)
        db.flush()

        # ============================================================
        # MODULES & LESSONS (for courses c1 and c5)
        # ============================================================
        print("Seeding modules and lessons...")
        # Course c1: Maths Fondamentales
        m1 = Module(course_id=c1.id, title="Chapitre 1 — Algèbre", order=1)
        m2 = Module(course_id=c1.id, title="Chapitre 2 — Géométrie", order=2)
        m3 = Module(course_id=c1.id, title="Chapitre 3 — Analyse", order=3)
        db.add_all([m1, m2, m3])
        db.flush()

        lessons_c1 = []
        for i, (mod, titles) in enumerate([
            (m1, ["Équations du 1er degré", "Systèmes d'équations", "Inéquations", "Applications"]),
            (m2, ["Vecteurs", "Produit scalaire", "Droites et plans"]),
            (m3, ["Fonctions", "Limites", "Continuité", "Dérivation"]),
        ], 1):
            for j, title in enumerate(titles, 1):
                l = Lesson(
                    module_id=mod.id, school_id=school_main.id, teacher_id=teacher_1.id,
                    title=title, content_type=ContentType.TEXT,
                    content_text=f"Contenu de la leçon '{title}'. Ceci est un texte éducatif de base pour illustrer le système RAG.",
                    order=j, duration_minutes=30, is_free=(i == 1 and j <= 1),
                )
                lessons_c1.append(l)
        db.add_all(lessons_c1)
        db.flush()

        # Course c5: Python Bases
        m_py1 = Module(course_id=c5.id, title="Module 1 — Découverte", order=1)
        m_py2 = Module(course_id=c5.id, title="Module 2 — Structures", order=2)
        db.add_all([m_py1, m_py2])
        db.flush()

        lessons_c5 = []
        for mod, titles in [
            (m_py1, ["Installation & IDE", "Variables et types", "Entrées/Sorties", "Conditions", "Boucles"]),
            (m_py2, ["Listes et tuples", "Dictionnaires", "Fonctions", "Fichiers", "Projet final"]),
        ]:
            for j, title in enumerate(titles, 1):
                l = Lesson(
                    module_id=mod.id, school_id=school_b.id, teacher_id=teacher_3.id,
                    title=title, content_type=ContentType.TEXT,
                    content_text=f"Cours pratique de Python : {title}. Exemples de code inclus.",
                    order=j, duration_minutes=35, is_free=(j <= 2),
                )
                lessons_c5.append(l)
        db.add_all(lessons_c5)
        db.flush()

        # ============================================================
        # QUIZZES (on some lessons)
        # ============================================================
        print("Seeding quizzes...")
        quiz1 = Quiz(lesson_id=lessons_c1[0].id, title="Quiz — Équations", time_limit_seconds=300, passing_score_percent=60)
        quiz2 = Quiz(lesson_id=lessons_c5[2].id, title="Quiz — Entrées/Sorties", time_limit_seconds=600, passing_score_percent=70)
        db.add_all([quiz1, quiz2])
        db.flush()

        # Quiz 1 questions
        q1q1 = QuizQuestion(quiz_id=quiz1.id, question_text="Quelle est la solution de 2x + 4 = 10 ?", question_type="mcq", points=2, order_index=1)
        q1q2 = QuizQuestion(quiz_id=quiz1.id, question_text="Le système x+y=5, x-y=1 a combien de solutions ?", question_type="mcq", points=2, order_index=2)
        db.add_all([q1q1, q1q2])
        db.flush()

        o1a = QuizOption(question_id=q1q1.id, option_text="x = 2", is_correct=False, order_index=1)
        o1b = QuizOption(question_id=q1q1.id, option_text="x = 3", is_correct=True, order_index=2)
        o1c = QuizOption(question_id=q1q1.id, option_text="x = 4", is_correct=False, order_index=3)
        o1d = QuizOption(question_id=q1q1.id, option_text="x = 5", is_correct=False, order_index=4)

        o2a = QuizOption(question_id=q1q2.id, option_text="Aucune", is_correct=False, order_index=1)
        o2b = QuizOption(question_id=q1q2.id, option_text="Une seule", is_correct=True, order_index=2)
        o2c = QuizOption(question_id=q1q2.id, option_text="Deux", is_correct=False, order_index=3)
        o2d = QuizOption(question_id=q1q2.id, option_text="Infinies", is_correct=False, order_index=4)
        db.add_all([o1a, o1b, o1c, o1d, o2a, o2b, o2c, o2d])
        db.flush()

        # ============================================================
        # ENROLLMENTS
        # ============================================================
        print("Seeding enrollments...")
        enrollments = []
        # Students in school_main enroll in c1 and c2
        for s in students[:3]:
            enrollments.append(CourseEnrollment(student_id=s.id, course_id=c1.id, status=EnrollmentStatus.ACTIVE, progress_percent=30))
            enrollments.append(CourseEnrollment(student_id=s.id, course_id=c2.id, status=EnrollmentStatus.ACTIVE, progress_percent=15))
        # Students in school_b enroll in c5 and c6
        for s in students[3:]:
            enrollments.append(CourseEnrollment(student_id=s.id, course_id=c5.id, status=EnrollmentStatus.ACTIVE, progress_percent=40))
            enrollments.append(CourseEnrollment(student_id=s.id, course_id=c6.id, status=EnrollmentStatus.ACTIVE, progress_percent=20))
        # One completed enrollment
        enrollments.append(CourseEnrollment(
            student_id=students[0].id, course_id=c3.id,
            status=EnrollmentStatus.COMPLETED, progress_percent=100,
            completed_at=now - timedelta(days=5),
        ))
        db.add_all(enrollments)
        db.flush()

        # ============================================================
        # CLASSROOMS
        # ============================================================
        print("Seeding classrooms...")
        cr1 = ClassRoom(
            name="Maths 2025-A", description="Classe de mathématiques première année",
            invite_code="MATH-A", school_id=school_main.id, teacher_id=teacher_1.id,
            course_id=c1.id, max_students=30,
        )
        cr2 = ClassRoom(
            name="Python 2025-B", description="Atelier informatique",
            invite_code="PYTH-B", school_id=school_b.id, teacher_id=teacher_3.id,
            course_id=c5.id, max_students=25,
        )
        db.add_all([cr1, cr2])
        db.flush()

        for s in students[:3]:
            db.add(ClassroomEnrollment(student_id=s.id, classroom_id=cr1.id))
        for s in students[3:]:
            db.add(ClassroomEnrollment(student_id=s.id, classroom_id=cr2.id))
        db.flush()

        # ============================================================
        # TEACHER CLASSES (v2)
        # ============================================================
        print("Seeding teacher classes (v2)...")
        tc1 = TeacherClass(teacher_id=teacher_1.id, school_id=school_main.id,
                           name="Classe Maths Avancée", code="MATH-AV")
        tc2 = TeacherClass(teacher_id=teacher_3.id, school_id=school_b.id,
                           name="Atelier Code", code="CODE-AT")
        db.add_all([tc1, tc2])
        db.flush()

        db.add(ClassCourseAccess(class_id=tc1.id, course_id=c1.id))
        db.add(ClassCourseAccess(class_id=tc1.id, course_id=c3.id))
        db.add(ClassCourseAccess(class_id=tc2.id, course_id=c5.id))
        db.flush()

        for s in students[:2]:
            db.add(StudentEnrollment(student_id=s.id, class_id=tc1.id))
        for s in students[3:5]:
            db.add(StudentEnrollment(student_id=s.id, class_id=tc2.id))
        db.flush()

        # ============================================================
        # ASSIGNMENTS & SUBMISSIONS
        # ============================================================
        print("Seeding assignments...")
        a1 = Assignment(
            classroom_id=cr1.id, title="Devoir — Équations du 1er degré",
            description="Résoudre les exercices pages 12-15",
            instructions="Montrer tous les détails. 5 exercices obligatoires.",
            max_score=20, due_date=now + timedelta(days=7),
        )
        a2 = Assignment(
            classroom_id=cr2.id, title="TP — Premier script Python",
            description="Écrire un programme de calculatrice",
            instructions="Gérer +, -, *, / avec gestion d'erreur.",
            max_score=20, due_date=now + timedelta(days=10),
        )
        db.add_all([a1, a2])
        db.flush()

        # Submissions
        sub1 = Submission(
            assignment_id=a1.id, student_id=students[0].id,
            content="Exercice 1: x = 3. Exercice 2: x=2, y=3...",
            ai_score=16, ai_feedback="Bon travail, quelques erreurs d'arrondi.",
            is_graded=True,
        )
        sub2 = Submission(
            assignment_id=a2.id, student_id=students[3].id,
            content="def calc(a, op, b): ...",
            ai_score=18, ai_feedback="Excellente gestion des erreurs.",
            is_graded=True,
        )
        sub3 = Submission(
            assignment_id=a1.id, student_id=students[1].id,
            content="En cours de rédaction...",
            is_graded=False,
        )
        db.add_all([sub1, sub2, sub3])
        db.flush()

        # ============================================================
        # TRANSACTIONS
        # ============================================================
        print("Seeding transactions...")
        txns = [
            Transaction(school_id=school_main.id, user_id=students[0].id,
                       type=TransactionType.TOKEN_RECHARGE, amount=100,
                       currency=Currency.TOKEN, description="Recharge initiale"),
            Transaction(school_id=school_main.id, user_id=students[0].id,
                       type=TransactionType.COURSE_PURCHASE, amount=25.0,
                       currency=Currency.DT, description="Achat Mathématiques Fondamentales"),
            Transaction(school_id=school_main.id, user_id=teacher_1.id,
                       type=TransactionType.COURSE_SALE, amount=17.5,
                       currency=Currency.DT, description="Vente cours Maths (70% revenue)"),
            Transaction(school_id=school_b.id, user_id=students[3].id,
                       type=TransactionType.TOKEN_CONSUMPTION, amount=-10,
                       currency=Currency.TOKEN, description="Utilisation IA tutor"),
        ]
        db.add_all(txns)
        db.flush()

        # ============================================================
        # COURSE PURCHASES
        # ============================================================
        print("Seeding course purchases...")
        from app.models import CoursePurchase
        cp1 = CoursePurchase(
            student_id=students[0].id, course_id=c1.id,
            amount_paid=25.0, currency="TND",
            platform_fee=7.5, teacher_revenue=17.5,
            commission_rate_applied=0.30,
        )
        db.add(cp1)
        db.flush()

        # ============================================================
        # MESSAGES
        # ============================================================
        print("Seeding messages...")
        msg1 = Message(
            school_id=school_main.id, sender_id=super_admin.id,
            receiver_id=admin_a.id, type=MessageType.DIRECT,
            subject="Configuration école", body="Merci de finaliser la configuration de l'académie.",
        )
        msg2 = Message(
            school_id=school_main.id, sender_id=admin_a.id,
            receiver_id=teacher_1.id, type=MessageType.DIRECT,
            subject="Cours validé", body="Votre cours de maths a été validé. Félicitations !",
        )
        msg3 = Message(
            school_id=school_main.id, sender_id=super_admin.id,
            type=MessageType.BROADCAST, subject="Maintenance prévue",
            body="Maintenance plateforme le 25 juillet de 2h à 6h.",
            target_audience="all",
        )
        db.add_all([msg1, msg2, msg3])
        db.flush()

        # ============================================================
        # PLATFORM SETTINGS
        # ============================================================
        print("Seeding platform settings...")
        settings = [
            PlatformSetting(key="maintenance_mode", value="false", description="Mode maintenance global"),
            PlatformSetting(key="allow_registrations", value="true", description="Autoriser les inscriptions"),
            PlatformSetting(key="platform_name", value="EDUAI Learning", description="Nom de la plateforme"),
            PlatformSetting(key="support_email", value="support@eduai.edu", description="Email support"),
        ]
        db.add_all(settings)
        db.flush()

        # ============================================================
        # AI CONVERSATIONS
        # ============================================================
        print("Seeding AI conversations...")
        conv1 = AIConversation(user_id=students[0].id, title="Aide sur les équations")
        db.add(conv1)
        db.flush()

        db.add_all([
            AIChatMessage(conversation_id=conv1.id, role="user", content="Comment résoudre 3x + 6 = 0 ?", detected_language="fr"),
            AIChatMessage(conversation_id=conv1.id, role="assistant",
                         content="Pour résoudre 3x + 6 = 0 : 1) Soustraire 6 des deux côtés → 3x = -6. 2) Diviser par 3 → x = -2.", detected_language="fr"),
            AIChatMessage(conversation_id=conv1.id, role="user", content="Et si c'est 3x² + 6 = 0 ?", detected_language="fr"),
            AIChatMessage(conversation_id=conv1.id, role="assistant",
                         content="Pour 3x² + 6 = 0 : 3x² = -6 → x² = -2. Pas de solution réelle car x² est toujours ≥ 0.", detected_language="fr"),
        ])
        db.flush()

        # ============================================================
        # AUDIT LOGS
        # ============================================================
        print("Seeding audit logs...")
        from app.models import AuditAction
        audit_entries = [
            AuditLog(admin_id=super_admin.id, admin_email=super_admin.email,
                    action=AuditAction.USER_CREATE, target_type="user", target_id=teacher_1.id,
                    details="Création compte enseignant", ip_address="127.0.0.1"),
            AuditLog(admin_id=admin_a.id, admin_email=admin_a.email,
                    action=AuditAction.COURSE_PUBLISH, target_type="course", target_id=c1.id,
                    details="Publication cours Mathématiques Fondamentales"),
            AuditLog(admin_id=super_admin.id, admin_email=super_admin.email,
                    action=AuditAction.SCHOOL_CREATE, target_type="school", target_id=school_b.id,
                    details="Création école Lycée La Réussite"),
        ]
        db.add_all(audit_entries)
        db.flush()

        # ============================================================
        # COMMIT
        # ============================================================
        db.commit()

        # ============================================================
        # SUMMARY
        # ============================================================
        print("\n" + "=" * 60)
        print("SEED COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"\nSchools:       3 (EDUAI Academy, Lycée La Réussite, Demo)")
        print(f"Users:         {len(all_users)} total")
        print(f"  - 1 Super Admin (superadmin@eduai.edu)")
        print(f"  - 1 Pedagogical Admin (pedago.admin@eduai.edu)")
        print(f"  - 1 Pedagogical Lead (pedago.lead@reussite.edu)")
        print(f"  - 2 School Admins (admin.eduai@eduai.edu, admin.reussite@reussite.edu)")
        print(f"  - 4 Teachers (prof.math, prof.fr, prof.info, prof.sciences)")
        print(f"  - 6 Students (student1-3@eduai.edu, student1-3@reussite.edu)")
        print(f"\nCourses:       8 (5 published, 1 pending, 1 draft, 1 archived)")
        print(f"  - Free: 2  |  Paid: 5  |  Archived: 1")
        print(f"Modules:       5  |  Lessons: {len(lessons_c1) + len(lessons_c5)}")
        print(f"Quizzes:       2  |  Questions: 2")
        print(f"Classrooms:    2  |  TeacherClasses: 2")
        print(f"Assignments:   2  |  Submissions: 3")
        print(f"Enrollments:   {len(enrollments)}")
        print(f"Wallet txns:   ~{len(all_users) * 2 + 4}")
        print(f"\nPassword for all accounts: password123")
        print(f"\nLogin endpoints:")
        print(f"  POST /auth/login  (body: username=email, password=password123)")
        print("=" * 60)

    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    seed()
