"""
Sync script: retroactively enroll students in courses matching their active abonnements.

Usage: python sync_enrollments.py [--dry-run]
"""
import sys
import unicodedata
from app.db import SessionLocal
from app.models import User, Abonnement, PackDefinition, Course, CourseEnrollment, Matiere

def _strip_accents(s: str) -> str:
    return unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode("ascii").lower().strip()

def _match_matiere(matiere_name: str, course_category: str) -> bool:
    """Fuzzy match matiere name to course category."""
    if not matiere_name or not course_category:
        return False
    return _strip_accents(matiere_name) == _strip_accents(course_category)

def sync_enrollments(dry_run=False):
    db = SessionLocal()
    
    active_abos = db.query(Abonnement).filter(
        Abonnement.statut.in_(["actif", "grace"])
    ).all()
    
    total_enrolled = 0
    students_affected = set()
    
    for abo in active_abos:
        user = db.query(User).filter(User.id == abo.user_id).first()
        if not user or user.role != "student":
            continue
        
        pack = db.query(PackDefinition).filter(PackDefinition.id == abo.pack_id).first()
        if not pack:
            continue
        
        matieres_config = abo.matieres_config or {}
        matiere_ids = matieres_config.get("matieres", []) if isinstance(matieres_config, dict) else []
        
        if not matiere_ids:
            continue
        
        # Get matiere names from IDs
        matieres = db.query(Matiere).filter(Matiere.id.in_(matiere_ids)).all()
        matiere_names = {m.id: m.nom for m in matieres}
        
        # Find courses matching the student's niveau AND the selected matieres
        niveau = user.niveau_scolaire
        if not niveau:
            continue
        
        all_courses = db.query(Course).filter(
            Course.status == "published",
        ).all()
        
        matching_courses = []
        for course in all_courses:
            # Match niveau (accent-insensitive)
            if not _match_matiere(niveau, course.niveau_scolaire or ""):
                continue
            # Match matiere (accent-insensitive)
            course_matiere = course.category or ""
            if any(_match_matiere(mn, course_matiere) for mn in matiere_names.values()):
                matching_courses.append(course)
        
        for course in matching_courses:
            existing = db.query(CourseEnrollment).filter(
                CourseEnrollment.student_id == user.id,
                CourseEnrollment.course_id == course.id,
            ).first()
            
            if not existing:
                matiere_name = matiere_names.get("?")
                print(f"  {'[DRY RUN] ' if dry_run else ''}Enroll student {user.email} (id={user.id}) in course '{course.title}' (id={course.id}, category={course.category})")
                if not dry_run:
                    db.add(CourseEnrollment(student_id=user.id, course_id=course.id))
                total_enrolled += 1
                students_affected.add(user.email)
    
    if not dry_run:
        db.commit()
    
    print(f"\n{'[DRY RUN] ' if dry_run else ''}Summary:")
    print(f"  Students affected: {len(students_affected)}")
    print(f"  Enrollments created: {total_enrolled}")
    
    db.close()

if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    sync_enrollments(dry_run=dry_run)
