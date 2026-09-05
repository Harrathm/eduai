"""
Seed SVT course templates for the Tunisian official curriculum.
IDEMPOTENT: checks for existing courses by slug before inserting.

Creates 3 model courses (7ème, 8ème, 9ème Année Base) with full module/lesson structure.
All courses: category_cible="Scolaire", category="علوم طبيعية", is_published=True.

Usage:
    cd backend
    python seed_svt_templates.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if not os.environ.get("DATABASE_URL"):
    os.environ["DATABASE_URL"] = "postgresql+pg8000://postgres:gill4264@localhost:5432/eduai"

from sqlalchemy import text
from app.db.session import engine, SessionLocal
from app.models import (
    Base, School, User, Course, Module, Lesson,
    UserRole, CourseStatus, ContentType,
    SchoolType, NiveauEtude, Matiere,
)

# ── Course definitions ──────────────────────────────────────────
COURSES = [
    {
        "title": "Modèle Cours SVT - 7ème Année Base",
        "slug": "modele-svt-7eme-base",
        "niveau_scolaire": "سابعة أساسي",
        "modules": [
            {
                "title": "دراسة الوسط البيئي",
                "lessons": [
                    "دراسة وسط بيئي محلّي",
                    "تنوّع الأوساط البيئية",
                ],
            },
            {
                "title": "دراسة بعض مكوّنات الوسط",
                "lessons": [
                    "الصّخور",
                    "الترّبة وعلاقتها بالكائنات الحيّة",
                ],
            },
            {
                "title": "التنوّع البيولوجي",
                "lessons": [
                    "تنوّع الفطريّات وتصنيفها",
                    "تنوّع اللاّ فقريّات وتصنيفها",
                    "تنوّع النّباتات اليّهريّات وتصنيفها",
                    "تنوّع الكائنات الدّقيقة",
                    "الوحدة التركيبية للكائنات الحية (الخلية)",
                    "دور الإنسان في المحافظة على التنوّع البيولوجي",
                ],
            },
        ],
    },
    {
        "title": "Modèle Cours SVT - 8ème Année Base",
        "slug": "modele-svt-8eme-base",
        "niveau_scolaire": "ثامنة أساسي",
        "modules": [
            {
                "title": "تحسين الإنتاج النباتي",
                "lessons": [
                    "التغذية المعدنية عند النبات الأخضر",
                    "التغذية الكربونية عند النبات الأخضر",
                    "التكاثر والنموّ عند النبات الأخضر",
                    "الفلاحة البيولوجية",
                ],
            },
            {
                "title": "تحسين الإنتاج الحيواني",
                "lessons": [
                    "التغذية عند الحيوان (الأنظمة الغذائية)",
                    "التكاثر عند الحيوان (التكاثر مثلي عند الطيور)",
                    "النمو عند الحيوان (النمو المتواصل عند حيوان ثديي)",
                ],
            },
            {
                "title": "العلاقات الغذائية والتوازن البيئي",
                "lessons": [
                    "العلاقات الغذائية بين الكائنات الحية",
                    "التوازن البيئي",
                ],
            },
        ],
    },
    {
        "title": "Modèle Cours SVT - 9ème Année Base",
        "slug": "modele-svt-9eme-base",
        "niveau_scolaire": "تاسعة أساسي",
        "modules": [
            {
                "title": "الاتصال بالوسط",
                "lessons": [
                    "مفهوم وظيفة الاتصال",
                    "دراسة حركية انعكسية",
                    "دراسة حسية (شعور الإبصار)",
                ],
            },
            {
                "title": "وظائف التغذية",
                "lessons": [
                    "الهضم",
                    "الدم والدوران",
                    "التنفس",
                    "الإخراج",
                ],
            },
            {
                "title": "التكاثر والصحة (الإنجابية)",
                "lessons": [
                    "مظاهر النضج الجنسي",
                    "الجهاز التناسلي",
                    "الخلايا الجنسية",
                    "الدورة الجنسية (دور المبيض والرحم)",
                    "الإخصاب",
                    "التعشيش",
                    "تنظيم الولادات",
                ],
            },
        ],
    },
]

LESSON_DURATION_MINUTES = 45


def ensure_school_and_author(db):
    """Return (school, author) or raise if missing."""
    school = db.query(School).filter(School.slug == "eduai-svt-templates").first()
    if not school:
        school = School(
            name="EDUAI SVT Templates",
            slug="eduai-svt-templates",
            domain="svt-templates.eduai.tn",
            school_type=SchoolType.DEMO,
            subscription_tier="institution",
            max_users=100,
            is_active=True,
        )
        db.add(school)
        db.flush()
        print(f"  [NEW] School: {school.name} (id={school.id})")
    else:
        print(f"  [EXISTS] School: {school.name} (id={school.id})")

    author = db.query(User).filter(User.email == "admin.svt-templates@eduai.tn").first()
    if not author:
        from app.core.security import get_password_hash
        author = User(
            email="admin.svt-templates@eduai.tn",
            hashed_password=get_password_hash("passeword123"),
            full_name="Admin SVT Templates",
            role=UserRole.SUPER_ADMIN,
            school_id=school.id,
            is_active=True,
            is_approved=True,
        )
        db.add(author)
        db.flush()
        print(f"  [NEW] Author: {author.email}")
    else:
        print(f"  [EXISTS] Author: {author.email}")

    return school, author


def seed_svt_courses(db, school, author):
    """Create 3 SVT model courses with modules and lessons. Idempotent by slug."""
    total_modules = 0
    total_lessons = 0

    for course_def in COURSES:
        existing = db.query(Course).filter(Course.slug == course_def["slug"]).first()
        if existing:
            print(f"  [EXISTS] {course_def['slug']}")
            mod_ids = [m.id for m in db.query(Module.id).filter(Module.course_id == existing.id).all()]
            total_modules += len(mod_ids)
            total_lessons += db.query(Lesson).filter(Lesson.module_id.in_(mod_ids)).count() if mod_ids else 0
            continue

        course = Course(
            school_id=school.id,
            author_id=author.id,
            title=course_def["title"],
            slug=course_def["slug"],
            short_description=f" cours نموذجي للعلوم الطبيعية — {course_def['niveau_scolaire']}",
            description=f"دورة نموذجية مبنية على البرنامج الرسمي للعلوم الطبيعية والحياة والأرض ({course_def['niveau_scolaire']}). تشمل الدورة دروساً منظمة في وحدات دراسية تغطي المنهاج الدراسي.",
            category="علوم طبيعية",
            niveau_scolaire=course_def["niveau_scolaire"],
            category_cible="Scolaire",
            tag_pack_requis="Basic",
            language="ar",
            status=CourseStatus.PUBLISHED,
            is_published=True,
            is_active_version=True,
            visibility="public_catalog",
            owner_type="eduai_catalog",
            total_modules=0,
            total_lessons=0,
            total_duration_minutes=0,
        )
        db.add(course)
        db.flush()

        course_module_count = 0
        course_lesson_count = 0

        for mod_idx, mod_def in enumerate(course_def["modules"], start=1):
            module = Module(
                course_id=course.id,
                title=mod_def["title"],
                order=mod_idx,
            )
            db.add(module)
            db.flush()
            course_module_count += 1

            for les_idx, les_title in enumerate(mod_def["lessons"], start=1):
                lesson = Lesson(
                    module_id=module.id,
                    school_id=school.id,
                    teacher_id=author.id,
                    title=les_title,
                    content_type=ContentType.TEXT,
                    content_text=f"محتوى درس: {les_title}\n\n(محتوى نموذجي — يمكن للمعلم تعديله وإثرائه حسب حاجة التلاميذ)",
                    order=les_idx,
                    duration_minutes=LESSON_DURATION_MINUTES,
                )
                db.add(lesson)
                course_lesson_count += 1

        course.total_modules = course_module_count
        course.total_lessons = course_lesson_count
        course.total_duration_minutes = course_lesson_count * LESSON_DURATION_MINUTES

        total_modules += course_module_count
        total_lessons += course_lesson_count

        print(f"  [NEW] {course_def['slug']}: {course_module_count} modules, {course_lesson_count} lessons")

    return total_modules, total_lessons


def main():
    print("=" * 60)
    print("  SEED SVT TEMPLATES — EDUAI Learning")
    print("  Idempotent: safe to run multiple times")
    print("=" * 60)

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        print("\n[1/2] School & Author ...")
        school, author = ensure_school_and_author(db)

        print("\n[2/2] SVT Courses ...")
        total_modules, total_lessons = seed_svt_courses(db, school, author)

        db.commit()

        print("\n" + "=" * 60)
        print("  RAPPORT")
        print("=" * 60)
        print(f"  Cours créés      : {len(COURSES)}")
        print(f"  Modules créés    : {total_modules}")
        print(f"  Leçons créées    : {total_lessons}")
        print(f"  Durée par leçon  : {LESSON_DURATION_MINUTES} min")
        print(f"  Durée totale     : {total_lessons * LESSON_DURATION_MINUTES} min")
        print("=" * 60)

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
