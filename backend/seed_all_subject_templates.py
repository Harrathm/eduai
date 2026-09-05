"""
Seed all-subject course templates for the entire Tunisian official curriculum.
For every (NiveauEtude × Matiere) pair, creates a model course with
3 modules × 2 lessons each.

IDEMPOTENT: checks slug before inserting.

Usage:
    cd backend
    python seed_all_subject_templates.py
"""
from __future__ import annotations

import os
import sys
import unicodedata
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if not os.environ.get("DATABASE_URL"):
    os.environ["DATABASE_URL"] = "postgresql+pg8000://postgres:gill4264@localhost:5432/eduai"

from app.db.session import engine, SessionLocal
from app.models import (
    Base, School, User, Course, Module, Lesson,
    NiveauEtude, Matiere,
    UserRole, CourseStatus, ContentType,
    SchoolType,
)

import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

from app.core.security import get_password_hash

LESSON_DURATION_MINUTES = 45

MODULE_TITLES = [
    "الفصل الأول: التقييم و الدعم",
    "الفصل الثاني: التعميق",
    "الفصل الثالث: الإعداد للامتحان",
]

LESSON_TITLES = [
    "درس 1: المفاهيم الأساسية",
    "درس 2: التطبيقات",
]


def slugify(text: str) -> str:
    """Remove accents, lowercase, replace non-alphanum with hyphens."""
    nfkd = unicodedata.normalize("NFKD", text)
    ascii_text = nfkd.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")


def ensure_school_and_author(db):
    school = db.query(School).filter(School.slug == "eduai-all-templates").first()
    if not school:
        school = School(
            name="EDUAI All Subject Templates",
            slug="eduai-all-templates",
            domain="all-templates.eduai.tn",
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

    author = db.query(User).filter(User.email == "admin.all-templates@eduai.tn").first()
    if not author:
        author = User(
            email="admin.all-templates@eduai.tn",
            hashed_password=get_password_hash("passeword123"),
            full_name="Admin All Templates",
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


def seed_all(db, school, author):
    niveaux = db.query(NiveauEtude).order_by(NiveauEtude.ordre).all()
    print(f"  Niveaux trouvés: {len(niveaux)}")

    total_courses = 0
    total_modules = 0
    total_lessons = 0
    skipped = 0

    for niv in niveaux:
        matieres = db.query(Matiere).filter(Matiere.niveau_etude_id == niv.id).all()
        niv_courses = 0

        for mat in matieres:
            slug = f"modele-{mat.id}-{niv.id}"

            existing = db.query(Course).filter(Course.slug == slug).first()
            if existing:
                skipped += 1
                continue

            course = Course(
                school_id=school.id,
                author_id=author.id,
                title=f"Modèle Cours {mat.nom} - {niv.nom}",
                slug=slug,
                short_description=f" cours نموذجي لـ {mat.nom} — {niv.nom}",
                description=f"دورة نموذجية للمنهج التونسي: {mat.nom} ({niv.nom}).",
                category=mat.nom,
                niveau_scolaire=niv.nom,
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

            for mod_idx, mod_title in enumerate(MODULE_TITLES, start=1):
                module = Module(
                    course_id=course.id,
                    title=mod_title,
                    order=mod_idx,
                )
                db.add(module)
                db.flush()

                for les_idx, les_title in enumerate(LESSON_TITLES, start=1):
                    lesson = Lesson(
                        module_id=module.id,
                        school_id=school.id,
                        teacher_id=author.id,
                        title=les_title,
                        content_type=ContentType.TEXT,
                        content_text=f"محتوى نموذجي — {les_title}",
                        order=les_idx,
                        duration_minutes=LESSON_DURATION_MINUTES,
                    )
                    db.add(lesson)

            course.total_modules = 3
            course.total_lessons = 6
            course.total_duration_minutes = 6 * LESSON_DURATION_MINUTES
            niv_courses += 1

        if niv_courses:
            print(f"  {niv.nom}: {niv_courses} cours, {niv_courses * 3} modules, {niv_courses * 6} leçons")
            total_courses += niv_courses

    total_modules = total_courses * 3
    total_lessons = total_courses * 6

    return total_courses, total_modules, total_lessons, skipped


def main():
    print("=" * 60)
    print("  SEED ALL SUBJECT TEMPLATES — EDUAI Learning")
    print("  Idempotent: safe to run multiple times")
    print("=" * 60)

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        print("\n[1/2] School & Author ...")
        school, author = ensure_school_and_author(db)

        print("\n[2/2] Generating courses ...")
        total_courses, total_modules, total_lessons, skipped = seed_all(db, school, author)

        db.commit()

        print("\n" + "=" * 60)
        print("  RAPPORT FINAL")
        print("=" * 60)
        print(f"  Cours générés   : {total_courses}")
        print(f"  Modules créés   : {total_modules}")
        print(f"  Leçons créées   : {total_lessons}")
        print(f"  Ignorés (existants) : {skipped}")
        print("=" * 60)

        # Print one example
        if total_courses > 0:
            example = db.query(Course).filter(
                Course.slug.like("modele-%"),
                Course.category == "Mathématiques",
                Course.niveau_scolaire.like("%9ème%"),
            ).first()
            if not example:
                example = db.query(Course).filter(Course.slug.like("modele-%")).first()
            if example:
                mods = db.query(Module).filter(Module.course_id == example.id).order_by(Module.order).all()
                print(f"\n  Exemple:")
                print(f"    Titre : {example.title}")
                print(f"    Slug  : {example.slug}")
                print(f"    Matière : {example.category}")
                print(f"    Niveau  : {example.niveau_scolaire}")
                for m in mods:
                    les = db.query(Lesson).filter(Lesson.module_id == m.id).order_by(Lesson.order).all()
                    print(f"      Module {m.order}: {m.title}")
                    for l in les:
                        print(f"        Leçon {l.order}: {l.title}")
                print()

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
