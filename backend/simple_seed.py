"""Simple seed for EDUAI - works with SQLAlchemy created tables"""
from app.db import SessionLocal
from app.models import School, User, Course, Module, Lesson, SubscriptionTier, CourseStatus, UserRole
from app.core.security import get_password_hash

def seed():
    db = SessionLocal()
    try:
        print("=" * 50)
        print("EDUAI Simple Seed")
        print("=" * 50)
        
        # Check existing
        if db.query(School).first():
            print("Schools already exist!")
            return
        
        # Schools
        print("\n[1] Creating Schools...")
        schools = [
            School(name="Free Academy", slug="free-academy", subscription_tier=SubscriptionTier.FREE),
            School(name="Pro School", slug="pro-school", subscription_tier=SubscriptionTier.TEACHER_PRO),
            School(name="Tech Institute", slug="tech-institute", subscription_tier=SubscriptionTier.SCHOOL),
            School(name="University", slug="university", subscription_tier=SubscriptionTier.INSTITUTION),
        ]
        for s in schools:
            db.add(s)
        db.commit()
        for s in schools:
            db.refresh(s)
        print(f"  Created {len(schools)} schools")
        
        # Super Admin
        print("\n[2] Creating Super Admin...")
        admin = User(
            email="admin@eduai.platform",
            hashed_password=get_password_hash("password123"),
            full_name="Platform Admin",
            role=UserRole.SUPER_ADMIN.value,
            is_active=True,
            is_approved=True,
            token_balance=100000,
            dt_balance=10000.0,
            school_id=schools[0].id
        )
        db.add(admin)
        db.commit()
        print(f"  admin@eduai.platform / password123")
        
        # School Admins
        print("\n[3] Creating School Admins...")
        admins = [
            ("admin@free-academy.edu", "Free Admin", schools[0].id),
            ("admin@pro-school.edu", "Pro Admin", schools[1].id),
            ("admin@tech-institute.edu", "Tech Admin", schools[2].id),
            ("admin@university.edu", "Uni Admin", schools[3].id),
        ]
        for email, name, sid in admins:
            u = User(
                email=email,
                hashed_password=get_password_hash("password123"),
                full_name=name,
                role=UserRole.ADMIN_SCHOOL.value,
                is_active=True,
                is_approved=True,
                token_balance=5000,
                dt_balance=500.0,
                school_id=sid
            )
            db.add(u)
        db.commit()
        print(f"  Created {len(admins)} admins")
        
        # Teachers
        print("\n[4] Creating Teachers...")
        teachers = [
            ("teacher@free-academy.edu", "Teacher One", schools[0].id),
            ("teacher1@pro-school.edu", "Teacher 1", schools[1].id),
            ("teacher2@pro-school.edu", "Teacher 2", schools[1].id),
            ("prof1@tech-institute.edu", "Prof 1", schools[2].id),
            ("instructor1@university.edu", "Dr 1", schools[3].id),
        ]
        for email, name, sid in teachers:
            u = User(
                email=email,
                hashed_password=get_password_hash("password123"),
                full_name=name,
                role=UserRole.TEACHER.value,
                is_active=True,
                is_approved=True,
                token_balance=2000,
                dt_balance=200.0,
                school_id=sid
            )
            db.add(u)
        db.commit()
        print(f"  Created {len(teachers)} teachers")
        
        # Students
        print("\n[5] Creating Students...")
        for i in range(1, 6):
            u = User(
                email=f"student{i}@pro-school.edu",
                hashed_password=get_password_hash("password123"),
                full_name=f"Student {i}",
                role=UserRole.STUDENT.value,
                is_active=True,
                is_approved=True,
                token_balance=500,
                dt_balance=50.0,
                school_id=schools[1].id
            )
            db.add(u)
        db.commit()
        print(f"  Created 5 students")
        
        # Courses
        print("\n[6] Creating Sample Courses...")
        teacher = db.query(User).filter(User.role == "TEACHER").first()
        if teacher:
            courses_data = [
                ("Introduction à la Programmation", "Learn programming basics", "programming", "beginner"),
                ("Mathématiques Avancées", "Advanced math course", "math", "intermediate"),
                ("Physique", "Physics fundamentals", "science", "intermediate"),
            ]
            for title, desc, cat, level in courses_data:
                c = Course(
                    school_id=teacher.school_id,
                    author_id=teacher.id,
                    title=title,
                    short_description=desc,
                    description=desc * 2,
                    category=cat,
                    level=level,
                    status=CourseStatus.PUBLISHED,
                    is_published=True,
                    price_tokens=50,
                    price_dt=25.0
                )
                db.add(c)
            db.commit()
            
            # Add modules and lessons
            for c in db.query(Course).all():
                m = Module(course_id=c.id, title="Module 1", order=1)
                db.add(m)
            db.commit()
            
            for m in db.query(Module).all():
                l = Lesson(
                    module_id=m.id,
                    title="Lesson 1",
                    lesson_type="text",
                    order=1,
                    duration_minutes=15,
                    content_text="Welcome to this lesson!"
                )
                db.add(l)
            db.commit()
            print(f"  Created {len(courses_data)} courses with modules")
        
        print("\n" + "=" * 50)
        print("CREDENTIALS")
        print("=" * 50)
        print("Super Admin:  admin@eduai.platform / password123")
        print("School Adm:  admin@pro-school.edu / password123")
        print("Teacher:     teacher1@pro-school.edu / password123")
        print("Student:    student1@pro-school.edu / password123")
        print("\n[OK] Done!")
        
    except Exception as e:
        db.rollback()
        print(f"[ERROR] {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed()