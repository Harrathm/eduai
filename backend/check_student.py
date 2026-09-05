import unicodedata
from app.db import SessionLocal
from app.models import User, Abonnement, PackDefinition, Course, CourseEnrollment, Matiere

def _strip_accents(s):
    return unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode("ascii").lower().strip()

db = SessionLocal()

# Find test student
student = db.query(User).filter(User.email == "eleve.test@eduai.tn").first()
if not student:
    print("Student not found")
    db.close()
    exit()

print(f"Student: {student.email} (id={student.id})")
print(f"  niveau_scolaire: {student.niveau_scolaire}")
print(f"  role: {student.role}")

# Find active abonnement
abos = db.query(Abonnement).filter(
    Abonnement.user_id == student.id,
    Abonnement.statut.in_(["actif", "grace"]),
).all()

for abo in abos:
    pack = db.query(PackDefinition).filter(PackDefinition.id == abo.pack_id).first()
    print(f"\n  Abonnement id={abo.id} statut={abo.statut}")
    print(f"    pack: {pack.nom if pack else '?'} (tier={pack.tier if pack else '?'}, niveau={pack.niveau_scolaire if pack else '?'})")
    print(f"    matieres_config: {abo.matieres_config}")

# Find existing enrollments
enrollments = db.query(CourseEnrollment).filter(CourseEnrollment.student_id == student.id).all()
print(f"\n  Existing enrollments: {len(enrollments)}")
for e in enrollments:
    course = db.query(Course).filter(Course.id == e.course_id).first()
    print(f"    course_id={e.course_id} title={course.title if course else '?'} category={course.category if course else '?'}")

# Find matching courses
if student.niveau_scolaire:
    courses = db.query(Course).filter(
        Course.status == "published",
        Course.niveau_scolaire == student.niveau_scolaire,
    ).all()
    print(f"\n  Published courses for niveau '{student.niveau_scolaire}': {len(courses)}")
    for c in courses:
        print(f"    id={c.id} title={c.title} category={c.category}")

db.close()
