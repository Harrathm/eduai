"""Seed database with initial data"""
import sys
import os

# Ensure we're in the right directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from app.models import Base, School, User, Course, Module, Lesson, TokenPackage
from app.db.session import engine, SessionLocal
from app.models import UserRole, SubscriptionTier, CourseStatus
from app.core.security import get_password_hash


def seed_database():
    """Create all tables and seed initial data"""
    
    print("Creating database tables...")
    
    # Import all models to register them with Base
    from app.models import (
        School, User, Course, Module, Lesson, ClassRoom,
        Assignment, Submission, Transaction, TokenPackage,
        CourseEnrollment, ClassroomEnrollment, CoursePurchase,
        Document, Message, PlatformSetting, TeacherRegistration
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Tables created!")
    
    db = SessionLocal()
    
    try:
        # Check if demo school exists
        school = db.query(School).filter(School.slug == "demo-academy").first()
        if school:
            print("Demo data already exists!")
            return
        
        # Create demo school
        print("Creating demo school...")
        school = School(
            name="Demo Academy",
            slug="demo-academy",
            subscription_tier=SubscriptionTier.SCHOOL,
            is_active=True
        )
        db.add(school)
        db.commit()
        db.refresh(school)
        
        # Create admin user
        print("Creating admin user...")
        admin = User(
            school_id=school.id,
            email="admin@demo-academy.edu",
            hashed_password=get_password_hash("admin123"),
            full_name="Admin User",
            role=UserRole.ADMIN_SCHOOL,
            is_active=True,
            is_approved=True,
            token_balance=10000,
            dt_balance=1000.0
        )
        db.add(admin)
        
        # Create teacher user
        print("Creating teacher user...")
        teacher = User(
            school_id=school.id,
            email="teacher@demo-academy.edu",
            hashed_password=get_password_hash("teacher123"),
            full_name="Mohamed Trabelsi",
            role=UserRole.TEACHER,
            is_active=True,
            is_approved=True,
            token_balance=5000,
            dt_balance=500.0
        )
        db.add(teacher)
        
        # Create student user
        print("Creating student user...")
        student = User(
            school_id=school.id,
            email="student@demo-academy.edu",
            hashed_password=get_password_hash("student123"),
            full_name="Ahmed Ben Ali",
            role=UserRole.STUDENT,
            is_active=True,
            is_approved=True,
            token_balance=1000,
            dt_balance=100.0
        )
        db.add(student)
        
        db.commit()
        
        # Create a demo course
        print("Creating demo course...")
        course = Course(
            school_id=school.id,
            author_id=teacher.id,
            title="Python pour les débutants",
            description="Apprenez les bases de Python depuis zéro.",
            price_tokens=50,
            price_dt=25,
            status=CourseStatus.PUBLISHED,
            is_published=True,
            total_modules=3,
            total_lessons=15
        )
        db.add(course)
        db.commit()
        db.refresh(course)
        
        # Create modules
        print("Creating course modules...")
        modules = [
            Module(course_id=course.id, title="Introduction à Python", order=1),
            Module(course_id=course.id, title="Les variables et types", order=2),
            Module(course_id=course.id, title="Les boucles et conditions", order=3),
        ]
        for m in modules:
            db.add(m)
        db.commit()
        
        # Create token packages
        print("Creating token packages...")
        packages = [
            TokenPackage(school_id=school.id, name="Starter", tokens=100, price_dt=5, bonus_tokens=10),
            TokenPackage(school_id=school.id, name="Standard", tokens=500, price_dt=20, bonus_tokens=50),
            TokenPackage(school_id=school.id, name="Pro", tokens=1000, price_dt=35, bonus_tokens=100),
        ]
        for p in packages:
            db.add(p)
        
        db.commit()
        
        print("\n" + "="*50)
        print("DEMO DATA CREATED SUCCESSFULLY!")
        print("="*50)
        print("\nLOGIN CREDENTIALS:")
        print("-"*30)
        print("ADMIN:")
        print("  Email: admin@demo-academy.edu")
        print("  Password: admin123")
        print("\nTEACHER:")
        print("  Email: teacher@demo-academy.edu")
        print("  Password: teacher123")
        print("\nSTUDENT:")
        print("  Email: student@demo-academy.edu")
        print("  Password: student123")
        print("="*50)
        
    except Exception as e:
        print(f"Error seeding database: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()