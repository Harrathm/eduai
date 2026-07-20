"""
Seed script: creates the demo school and fictional students.

Idempotent — safe to run multiple times without duplicating data.

Usage:
    cd backend && python scripts/seed_demo_school.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.db import Base, get_db
from app.models import School, User, SchoolType, UserRole, SubscriptionPlan
from app.core.security import get_password_hash

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+pg8000://postgres:@localhost:5432/eduai")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()

DEMO_SCHOOL_NAME = "École de démonstration EDUAI"
DEMO_SCHOOL_SLUG = "ecole-demo-eduai"
DEMO_SCHOOL_DOMAIN = "demo.eduai.tn"

DEMO_STUDENTS = [
    {"full_name": "Élève Démo 1 — Ahmed", "email": "eleve1@demo.eduai.tn", "level": "3ème"},
    {"full_name": "Élève Démo 2 — Fatma", "email": "eleve2@demo.eduai.tn", "level": "4ème"},
    {"full_name": "Élève Démo 3 — Youssef", "email": "eleve3@demo.eduai.tn", "level": "5ème"},
    {"full_name": "Élève Démo 4 — Amira", "email": "eleve4@demo.eduai.tn", "level": "6ème"},
    {"full_name": "Élève Démo 5 — Karim", "email": "eleve5@demo.eduai.tn", "level": "3ème"},
    {"full_name": "Élève Démo 6 — Ines", "email": "eleve6@demo.eduai.tn", "level": "4ème"},
    {"full_name": "Élève Démo 7 — Mohamed", "email": "eleve7@demo.eduai.tn", "level": "5ème"},
    {"full_name": "Élève Démo 8 — Salma", "email": "eleve8@demo.eduai.tn", "level": "6ème"},
]

DEMO_PASSWORD = "DemoStudent2024!"


def run():
    # 1. Create or find demo school
    demo_school = db.query(School).filter(School.school_type == SchoolType.DEMO).first()
    if demo_school:
        print(f"Demo school already exists: id={demo_school.id} '{demo_school.name}'")
    else:
        # Verify no other demo school exists (app-level constraint)
        count = db.query(School).filter(School.school_type == SchoolType.DEMO).count()
        if count > 0:
            print("ERROR: Multiple demo schools found — aborting to prevent inconsistency.")
            sys.exit(1)

        demo_school = School(
            name=DEMO_SCHOOL_NAME,
            slug=DEMO_SCHOOL_SLUG,
            domain=DEMO_SCHOOL_DOMAIN,
            school_type=SchoolType.DEMO,
            is_active=True,
            allow_teacher_registration=True,
            allow_new_signups=True,
        )
        db.add(demo_school)
        db.commit()
        db.refresh(demo_school)
        print(f"Created demo school: id={demo_school.id} '{demo_school.name}'")

    # 2. Create demo students
    created = 0
    for s in DEMO_STUDENTS:
        existing = db.query(User).filter(User.email == s["email"]).first()
        if existing:
            continue
        student = User(
            email=s["email"],
            full_name=s["full_name"],
            hashed_password=get_password_hash(DEMO_PASSWORD),
            role=UserRole.STUDENT,
            school_id=demo_school.id,
            is_active=True,
            is_approved=True,
            is_demo_account=True,
            subscription_plan=SubscriptionPlan.TRIAL,
        )
        db.add(student)
        created += 1
    if created:
        db.commit()
        print(f"Created {created} demo students")
    else:
        print("All demo students already exist")

    # 3. Create a demo teacher account (for quick testing)
    teacher_email = "prof.demo@demo.eduai.tn"
    existing_teacher = db.query(User).filter(User.email == teacher_email).first()
    if not existing_teacher:
        teacher = User(
            email=teacher_email,
            full_name="Professeur Démo",
            hashed_password=get_password_hash("ProfDemo2024!"),
            role=UserRole.TEACHER,
            school_id=demo_school.id,
            is_active=True,
            is_approved=True,
            is_demo_account=True,
            subscription_plan=SubscriptionPlan.TRIAL,
        )
        db.add(teacher)
        db.commit()
        print(f"Created demo teacher: {teacher_email}")
    else:
        print(f"Demo teacher already exists: {teacher_email}")

    print("\n--- Summary ---")
    print(f"Demo school: {demo_school.name} (id={demo_school.id}, type={demo_school.school_type})")
    students = db.query(User).filter(User.school_id == demo_school.id, User.role == UserRole.STUDENT).all()
    print(f"Demo students: {len(students)}")
    for st in students:
        print(f"  - {st.full_name} ({st.email})")
    teacher = db.query(User).filter(User.email == teacher_email).first()
    if teacher:
        print(f"Demo teacher: {teacher.full_name} ({teacher.email})")
    print(f"\nAll accounts are is_demo_account=True, subscription_plan='trial'")
    db.close()


if __name__ == "__main__":
    run()
