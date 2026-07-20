"""
Seed script for EDUAI Learning Platform.
Creates initial super_admin, schools, demo users, and sample courses.
Usage: python seed.py
"""

import os
import sys
import secrets
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault("TESTING", "true")

from sqlalchemy import text
from app.db import engine, Base, SessionLocal
from app.models import (
    School, User, Course, Module, Lesson, CourseStatus, UserRole,
    CourseEnrollment, Quiz, QuizQuestion, QuizOption, QuizAttempt, QuizAnswer,
)
from app.core.security import get_password_hash
import app.models_lms  # Register LMS models with Base metadata


def seed():
    print("=" * 60)
    print("EDUAI Learning Platform - Seed Script")
    print("=" * 60)

    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"  Table creation warning (may already exist): {e}")

    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        print("  Database connection OK")
    except Exception as e:
        print(f"  Database connection failed: {e}")
        return

    now = datetime.now(timezone.utc)

    # ===== SCHOOLS =====
    print("\n[1] Creating schools...")
    schools_data = [
        ("free-academy", "Free Academy", "free"),
        ("pro-school", "Pro School", "school"),
        ("tech-institute", "Tech Institute", "institution"),
        ("demo-university", "Demo University", "teacher_pro"),
    ]
    schools = {}
    for slug, name, tier in schools_data:
        existing = db.query(School).filter(School.slug == slug).first()
        if existing:
            school = existing
            print(f"    {name} (already exists)")
        else:
            school = School(
                name=name, slug=slug, domain=f"{slug}.eduai.local",
                subscription_tier=tier, is_active=True,
                max_users={"free": 10, "teacher_pro": 50, "school": 200, "institution": 1000}.get(tier, 10),
            )
            db.add(school)
            db.flush()
            print(f"    {name} created")
        schools[slug] = school

    db.commit()

    # ===== SUPER ADMIN =====
    print("\n[2] Creating super admin...")
    super_admin = db.query(User).filter(User.email == "admin@eduai.platform").first()
    if not super_admin:
        super_admin = User(
            email="admin@eduai.platform",
            hashed_password=get_password_hash("admin123"),
            full_name="Platform Super Admin",
            role=UserRole.SUPER_ADMIN,
            is_active=True,
            school_id=schools["free-academy"].id,
            token_balance=100000,
            dt_balance=10000.0,
        )
        db.add(super_admin)
        db.flush()
        print("    admin@eduai.platform / admin123 (created)")
    else:
        print("    admin@eduai.platform (already exists)")

    # ===== SCHOOL ADMINS =====
    print("\n[3] Creating school admins...")
    school_admins = [
        ("admin@free-academy.edu", "Free Academy Admin", "free-academy"),
        ("admin@pro-school.edu", "Pro School Admin", "pro-school"),
        ("admin@tech-institute.edu", "Tech Institute Admin", "tech-institute"),
        ("admin@demo-university.edu", "Demo Uni Admin", "demo-university"),
    ]
    for email, name, slug in school_admins:
        existing = db.query(User).filter(User.email == email).first()
        if not existing:
            admin = User(
                email=email,
                hashed_password=get_password_hash("admin123"),
                full_name=name,
                role=UserRole.ADMIN_SCHOOL,
                is_active=True,
                school_id=schools[slug].id,
                token_balance=5000,
                dt_balance=500.0,
            )
            db.add(admin)
            print(f"    {email} / admin123")
    db.commit()

    # ===== DEMO USERS =====
    print("\n[4] Creating demo users...")
    users_data = [
        ("teacher@pro-school.edu", "Teacher One", UserRole.TEACHER, "pro-school", True, 2000, 200.0),
        ("student1@pro-school.edu", "Student Alpha", UserRole.STUDENT, "pro-school", False, 500, 50.0),
        ("student2@pro-school.edu", "Student Beta", UserRole.STUDENT, "pro-school", False, 300, 30.0),
        ("teacher@tech-institute.edu", "Prof Mentor", UserRole.TEACHER, "tech-institute", True, 3000, 300.0),
        ("student@tech-institute.edu", "Learner X", UserRole.STUDENT, "tech-institute", False, 400, 40.0),
        ("teacher@demo-university.edu", "Dr Lecturer", UserRole.TEACHER, "demo-university", True, 2500, 250.0),
        ("student@demo-university.edu", "Pupil Y", UserRole.STUDENT, "demo-university", False, 200, 20.0),
    ]
    for email, name, role, school_slug, is_teacher, tokens, dt in users_data:
        existing = db.query(User).filter(User.email == email).first()
        if not existing:
            user = User(
                email=email,
                hashed_password=get_password_hash("password123"),
                full_name=name,
                role=role,
                is_active=True,
                is_approved=is_teacher,
                school_id=schools[school_slug].id,
                token_balance=tokens,
                dt_balance=dt,
            )
            db.add(user)
            label = "teacher" if is_teacher else "student"
            print(f"    {email} / password123 ({label})")
    db.commit()

    # ===== DEMO COURSES =====
    print("\n[5] Creating demo courses...")
    teacher = db.query(User).filter(User.email == "teacher@pro-school.edu").first()
    if teacher:
        existing_course = db.query(Course).filter(Course.title == "Introduction à Python").first()
        if not existing_course:
            course = Course(
                school_id=teacher.school_id,
                author_id=teacher.id,
                title="Introduction à Python",
                short_description="Apprenez les bases de la programmation Python",
                description="Cours complet pour débutants: variables, boucles, fonctions, POO",
                category="programming",
                level="beginner",
                language="fr",
                status=CourseStatus.PUBLISHED,
                is_published=True,
                price_tokens=50,
                price_dt=25.0,
                max_students=100,
                published_at=now,
            )
            db.add(course)
            db.flush()
            course.slug = "introduction-a-python"

            module = Module(course_id=course.id, title="Les bases", description="Fondamentaux de Python", order=0)
            db.add(module)
            db.flush()

            lesson = Lesson(
                module_id=module.id,
                school_id=teacher.school_id,
                teacher_id=teacher.id,
                title="Variables et Types",
                description="Découvrez les variables en Python",
                lesson_type="text",
                content_type="text",
                content_text="En Python, les variables sont créées automatiquement quand on leur assigne une valeur.\n\nExemple:\nx = 5\nnom = 'Alice'\npi = 3.14",
                content_html="<h2>Variables en Python</h2><p>Les variables sont créées automatiquement.</p>",
                order=0,
                duration_minutes=15,
                is_free=True,
            )
            db.add(lesson)
            db.flush()

            quiz = Quiz(lesson_id=lesson.id, title="Quiz: Variables", description="Testez vos connaissances", passing_score_percent=70)
            db.add(quiz)
            db.flush()

            q1 = QuizQuestion(quiz_id=quiz.id, question_text="Quel est le type de x = 5 ?", question_type="mcq", points=1, order_index=0)
            db.add(q1)
            db.flush()
            db.add_all([
                QuizOption(question_id=q1.id, option_text="int", is_correct=True, order_index=0),
                QuizOption(question_id=q1.id, option_text="str", is_correct=False, order_index=1),
                QuizOption(question_id=q1.id, option_text="float", is_correct=False, order_index=2),
                QuizOption(question_id=q1.id, option_text="bool", is_correct=False, order_index=3),
            ])

            db.commit()
            print(f"    {course.title} (+ module, leçon, quiz)")
        else:
            print(f"    Introduction à Python (already exists)")

    # ===== ENROLL DEMO STUDENT =====
    print("\n[6] Enrolling demo students...")
    course = db.query(Course).filter(Course.title == "Introduction à Python").first()
    student = db.query(User).filter(User.email == "student1@pro-school.edu").first()
    if course and student:
        existing_enroll = db.query(CourseEnrollment).filter(
            CourseEnrollment.student_id == student.id,
            CourseEnrollment.course_id == course.id,
        ).first()
        if not existing_enroll:
            enroll = CourseEnrollment(student_id=student.id, course_id=course.id, status="active")
            db.add(enroll)
            db.commit()
            print(f"    {student.email} -> {course.title}")

    # ===== CREDENTIALS =====
    print("\n" + "=" * 60)
    print("SEED COMPLETE")
    print("=" * 60)
    print()
    print("  SUPER ADMIN:  admin@eduai.platform / admin123")
    print("  SCHOOL ADMIN: admin@pro-school.edu / admin123")
    print("  TEACHER:      teacher@pro-school.edu / password123")
    print("  STUDENT:      student1@pro-school.edu / password123")
    print()
    print("  Schools: Free Academy, Pro School, Tech Institute, Demo University")
    print()

    db.close()


if __name__ == "__main__":
    seed()
