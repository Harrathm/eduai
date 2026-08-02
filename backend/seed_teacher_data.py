"""Seed data for teacher id=18 (harrathmourad@gmail.com)"""
import sys
sys.path.insert(0, ".")

from datetime import datetime, timezone, timedelta
from app.db.session import SessionLocal
from app.models import (
    User, Course, TeacherClass, WalletTransaction, WalletPool,
    CourseStatus, UserRole, ClassCourseAccess, CoursePurchase, ResponsablePedagogique,
    SpecialitePedagogique, Notion, ContenuNotion, NotificationReorientation,
    ProfilAssimilationEleve,
)

db = SessionLocal()
TEACHER_ID = 18
SCHOOL_ID = 1

teacher = db.query(User).filter(User.id == TEACHER_ID).first()
assert teacher, f"Teacher {TEACHER_ID} not found"
print(f"Teacher: {teacher.full_name} (id={teacher.id}, school_id={teacher.school_id})")

# ═══ 1. Cours ═══
courses_data = [
    {
        "title": "Mathématiques - Équations du 1er degré",
        "short_description": "Maîtrisez la résolution des équations du premier degré.",
        "category": "pedagogy",
        "level": "intermediate",
        "niveau_scolaire": "3ème année de base",
        "status": CourseStatus.PUBLISHED,
        "is_published": True,
        "visibility": "school_only",
        "owner_type": "school",
        "total_modules": 4,
        "total_lessons": 12,
        "total_duration_minutes": 480,
    },
    {
        "title": "Français - La dissertation argumentée",
        "short_description": "Méthodologie de la dissertation en français.",
        "category": "pedagogy",
        "level": "advanced",
        "niveau_scolaire": "1ère année secondaire",
        "status": CourseStatus.PUBLISHED,
        "is_published": True,
        "visibility": "school_only",
        "owner_type": "school",
        "total_modules": 3,
        "total_lessons": 9,
        "total_duration_minutes": 360,
    },
    {
        "title": "SVT - Biologie cellulaire",
        "short_description": "Structure et fonctionnement des cellules vivantes.",
        "category": "pedagogy",
        "level": "beginner",
        "niveau_scolaire": "7ème année de base",
        "status": CourseStatus.DRAFT,
        "is_published": False,
        "visibility": "private",
        "owner_type": "school",
        "total_modules": 5,
        "total_lessons": 15,
        "total_duration_minutes": 600,
    },
]

for cd in courses_data:
    existing = db.query(Course).filter(
        Course.author_id == TEACHER_ID, Course.title == cd["title"]
    ).first()
    if not existing:
        course = Course(school_id=SCHOOL_ID, author_id=TEACHER_ID, owner_id=SCHOOL_ID, **cd)
        db.add(course)
        print(f"  + Course: {cd['title']}")
    else:
        print(f"  = Course exists: {cd['title']}")

db.commit()

# ═══ 2. Classes ═══
classes_data = [
    {"name": "3ème Base - Section A", "description": "Classe de 3ème année de base"},
    {"name": "1ère Secondaire - Sciences", "description": "Classe de 1ère année secondaire sciences"},
]

for cl in classes_data:
    existing = db.query(TeacherClass).filter(
        TeacherClass.teacher_id == TEACHER_ID, TeacherClass.name == cl["name"]
    ).first()
    if not existing:
        tc = TeacherClass(
            teacher_id=TEACHER_ID, school_id=SCHOOL_ID,
            code=f"T{TEACHER_ID}{len(classes_data):03d}", **cl
        )
        db.add(tc)
        print(f"  + Class: {cl['name']}")
    else:
        print(f"  = Class exists: {cl['name']}")

db.commit()

# ═══ 3. Assign courses to classes ═══
courses = db.query(Course).filter(Course.author_id == TEACHER_ID).all()
classes = db.query(TeacherClass).filter(TeacherClass.teacher_id == TEACHER_ID).all()

for c in courses[:2]:
    for cl in classes[:1]:
        existing = db.query(ClassCourseAccess).filter(
            ClassCourseAccess.class_id == cl.id, ClassCourseAccess.course_id == c.id
        ).first()
        if not existing:
            db.add(ClassCourseAccess(class_id=cl.id, course_id=c.id))
            print(f"  + Assigned: {c.title} -> {cl.name}")

db.commit()

# ═══ 4. Wallet transactions ═══
txns = [
    (WalletPool.TRIAL, 500, "ai_generate", datetime.now(timezone.utc) + timedelta(days=30)),
    (WalletPool.SCHOOL_ALLOCATED, 200, "ai_ask", datetime.now(timezone.utc) + timedelta(days=90)),
    (WalletPool.PURCHASED, 100, "ai_ingest", None),
]
for pool, amount, feature, expires in txns:
    db.add(WalletTransaction(
        user_id=TEACHER_ID, pool=pool, amount=amount,
        feature=feature, expires_at=expires
    ))
    print(f"  + Wallet: {pool.value} +{amount}")

db.commit()

# ═══ 5. Independent course + sales ═══
ind_course = db.query(Course).filter(
    Course.author_id == TEACHER_ID, Course.owner_type == "independent_teacher"
).first()

if not ind_course:
    ind_course = Course(
        school_id=SCHOOL_ID, author_id=TEACHER_ID,
        title="Cours Avancé - Algèbre Linéaire",
        short_description="Cours complet d'algèbre linéaire pour étudiants avancés.",
        category="pedagogy", level="advanced", niveau_scolaire="Terminale",
        status=CourseStatus.PUBLISHED, is_published=True,
        visibility="public_catalog",
        owner_type="independent_teacher", owner_id=TEACHER_ID,
        price=25.0, price_tokens=50, price_dt=25.0,
        total_modules=6, total_lessons=18, total_duration_minutes=720,
    )
    db.add(ind_course)
    db.flush()
    print(f"  + Independent course: {ind_course.title}")
else:
    print(f"  = Independent course exists: {ind_course.title}")

# Add sales with unique student_ids
existing_purchases = db.query(CoursePurchase).filter(
    CoursePurchase.course_id == ind_course.id
).all()
existing_student_ids = {p.student_id for p in existing_purchases}
# Find available student IDs
all_students = db.query(User).filter(User.role == UserRole.STUDENT).all()
available_ids = [s.id for s in all_students if s.id not in existing_student_ids]

for i, sid in enumerate(available_ids[:3]):
    db.add(CoursePurchase(
        student_id=sid, course_id=ind_course.id,
        amount_paid=25.0, platform_fee=5.0, teacher_revenue=20.0,
        purchased_at=datetime.now(timezone.utc) - timedelta(days=i * 7),
    ))
    print(f"  + Sale: student {sid} bought independent course")

if not available_ids:
    print("  = All students already purchased")

db.commit()

# ═══ 6. Assign as ResponsablePedagogique ═══
resp = db.query(ResponsablePedagogique).filter(
    ResponsablePedagogique.user_id == TEACHER_ID
).first()

if not resp:
    spec = db.query(SpecialitePedagogique).first()
    if spec:
        rp = ResponsablePedagogique(
            user_id=TEACHER_ID,
            specialite_id=spec.id,
        )
        db.add(rp)
        db.flush()
        print(f"  + Assigned as ResponsablePedagogique (specialite: {spec.nom})")

        # Link niveaux_etude via association table
        from app.models import NiveauEtude
        niveaux = db.query(NiveauEtude).filter(
            NiveauEtude.nom.in_(["3ème année de base", "7ème année de base", "1ère année secondaire"])
        ).all()
        rp.niveaux_etude_scope = niveaux
        print(f"  + Linked {len(niveaux)} niveaux_etude to RP")

        # Create pending reorientation notification if there are any
        profil = db.query(ProfilAssimilationEleve).first()
        if profil:
            existing_notif = db.query(NotificationReorientation).filter(
                NotificationReorientation.enseignant_id == TEACHER_ID,
                NotificationReorientation.action_prise == "aucune",
            ).first()
            if not existing_notif:
                db.add(NotificationReorientation(
                    profil_assimilation_id=profil.id,
                    enseignant_id=TEACHER_ID,
                    date_notification=datetime.now(timezone.utc),
                    date_limite_action=datetime.now(timezone.utc) + timedelta(days=7),
                    action_prise="aucune",
                ))
                print(f"  + Added reorientation notification")
    else:
        print("  ! No SpecialitePedagogique found, skipping RP assignment")

db.commit()

# ═══ Verify ═══
courses = db.query(Course).filter(Course.author_id == TEACHER_ID).all()
classes = db.query(TeacherClass).filter(TeacherClass.teacher_id == TEACHER_ID).all()
wallet = db.query(WalletTransaction).filter(WalletTransaction.user_id == TEACHER_ID).all()
ind = db.query(Course).filter(
    Course.author_id == TEACHER_ID, Course.owner_type == "independent_teacher"
).all()
sales = db.query(CoursePurchase).join(Course).filter(Course.author_id == TEACHER_ID).all()
rp = db.query(ResponsablePedagogique).filter(ResponsablePedagogique.user_id == TEACHER_ID).count()
reorientations = db.query(NotificationReorientation).filter(
    NotificationReorientation.enseignant_id == TEACHER_ID,
    NotificationReorientation.action_prise == "aucune",
).count()

print(f"\n=== Verification ===")
print(f"Courses authored: {len(courses)}")
print(f"Independent courses: {len(ind)}")
print(f"Classes: {len(classes)}")
print(f"Wallet txns: {len(wallet)}")
print(f"Sales: {len(sales)}")
print(f"ResponsablePedagogique: {rp}")
print(f"Pending reorientations: {reorientations}")

db.close()
print("\nDone!")
