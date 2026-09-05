"""
seed_harrath_env.py — Repair environment for teacher Harrath Mourad (id=18)

Idempotent: safe to run multiple times.

What it does:
  1. Aligns all 3 students' niveau_scolaire to "Bac Sciences Expérimentales"
  2. Creates a Golden PackDefinition for "Bac Sciences Expérimentales" if missing
  3. Creates/updates Abonnement (statut=actif) for all 3 students on that pack
  4. Publishes course 20, sets visibility to public_catalog
  5. Adds 1 Lesson per module in course 20 (3 modules, 0 lessons each)
  6. Generates an invitation code for class 12 if null
"""
import sys, io, os, secrets

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timedelta, timezone
from app.db import SessionLocal
from app.models import (
    User, TeacherClass, Course, Module, Lesson,
    PackDefinition, Abonnement,
)

NIVEAU = "Bac Sciences Expérimentales"
TEACHER_ID = 18
STUDENT_IDS = [10, 11, 12]
COURSE_ID = 20
CLASS_ID = 12

db = SessionLocal()
teacher = db.query(User).filter(User.id == TEACHER_ID).first()

def log(msg):
    print(f"  {msg}")

try:
    print("=" * 60)
    print("SEED HARRATH ENVIRONMENT — REPAIR SCRIPT")
    print("=" * 60)

    # ── 1. Fix student niveau_scolaire ───────────────────────────────
    print("\n[1/6] Fixing student niveau_scolaire...")
    for sid in STUDENT_IDS:
        s = db.query(User).filter(User.id == sid).first()
        if not s:
            log(f"  Student {sid}: NOT FOUND — skipping")
            continue
        old = s.niveau_scolaire
        if old != NIVEAU:
            s.niveau_scolaire = NIVEAU
            log(f"  Student {sid} ({s.full_name}): '{old}' → '{NIVEAU}'")
        else:
            log(f"  Student {sid} ({s.full_name}): already '{NIVEAU}' — OK")

    # ── 2. Create Golden Pack for Bac Sciences Expérimentales ────────
    print("\n[2/6] Ensuring Golden Pack exists...")
    pack = db.query(PackDefinition).filter(
        PackDefinition.tier == "golden",
        PackDefinition.niveau_scolaire == NIVEAU,
    ).first()
    if not pack:
        pack = PackDefinition(
            nom=f"Pack {NIVEAU} - Golden",
            description=f"Pack Golden pour le niveau {NIVEAU}",
            tier="golden",
            niveau_scolaire=NIVEAU,
            matieres=None,
            prix_tnd=39.90,
            features={"live_sessions": True, "ai_factory": True, "tutoring": True},
            est_actif=True,
        )
        db.add(pack)
        db.flush()
        log(f"  Created pack id={pack.id} nom='{pack.nom}'")
    else:
        log(f"  Pack id={pack.id} '{pack.nom}' already exists — OK")

    # ── 3. Create / update Abonnements ──────────────────────────────
    print("\n[3/6] Ensuring active Abonnements for students...")
    now = datetime.now(timezone.utc)
    for sid in STUDENT_IDS:
        s = db.query(User).filter(User.id == sid).first()
        abo = db.query(Abonnement).filter(
            Abonnement.user_id == sid,
            Abonnement.pack_id == pack.id,
        ).first()
        if abo:
            if abo.statut != "actif":
                abo.statut = "actif"
                abo.fin = now + timedelta(days=365)
                log(f"  Student {sid}: reactivated abono id={abo.id} (was '{abo.statut}')")
            else:
                log(f"  Student {sid}: abono id={abo.id} already active — OK")
        else:
            # Check if student has any abonnement at all
            existing_abo = db.query(Abonnement).filter(Abonnement.user_id == sid).first()
            if existing_abo:
                # Update existing to point to correct pack
                existing_abo.pack_id = pack.id
                existing_abo.statut = "actif"
                existing_abo.debut = now
                existing_abo.fin = now + timedelta(days=365)
                log(f"  Student {sid}: updated existing abono id={existing_abo.id} → pack={pack.id} statut=actif")
            else:
                new_abo = Abonnement(
                    user_id=sid,
                    pack_id=pack.id,
                    statut="actif",
                    debut=now,
                    fin=now + timedelta(days=365),
                )
                db.add(new_abo)
                log(f"  Student {sid}: created new abono → pack={pack.id} statut=actif")

    # ── 4. Publish Course 20 ────────────────────────────────────────
    print("\n[4/6] Publishing course 20...")
    course = db.query(Course).filter(Course.id == COURSE_ID).first()
    if course:
        changed = False
        if str(course.status.value if hasattr(course.status, "value") else course.status).upper() != "PUBLISHED":
            from app.models import CourseStatus
            course.status = CourseStatus.PUBLISHED
            changed = True
            log(f"  status → PUBLISHED")
        if course.visibility != "public_catalog":
            course.visibility = "public_catalog"
            changed = True
            log(f"  visibility → public_catalog")
        if not changed:
            log(f"  Course 20 already published + public_catalog — OK")
    else:
        log(f"  Course 20 NOT FOUND!")

    # ── 5. Add Lessons to empty modules ─────────────────────────────
    print("\n[5/6] Populating empty modules in course 20...")
    if course:
        modules = db.query(Module).filter(Module.course_id == COURSE_ID).order_by(Module.order).all()
        lesson_counter = 1
        for mod in modules:
            existing = db.query(Lesson).filter(Lesson.module_id == mod.id).count()
            if existing == 0:
                lesson = Lesson(
                    module_id=mod.id,
                    school_id=teacher.school_id,
                    teacher_id=TEACHER_ID,
                    title=f"Leçon introductive — {mod.title}",
                    description=f"Contenu pédagogique pour {mod.title}. Ce contenu a été généré automatiquement pour la démonstration.",
                    lesson_type="cours",
                    content_type="text",
                    content_html="<p>Contenu de la leçon en cours de rédaction par l'enseignant.</p>",
                    duration_minutes=30,
                    order=1,
                    is_free=True,
                )
                db.add(lesson)
                log(f"  Module {mod.id} ('{mod.title}'): added lesson '{lesson.title}'")
            else:
                log(f"  Module {mod.id} ('{mod.title}'): already has {existing} lessons — OK")

    # ── 6. Generate class code for class 12 ─────────────────────────
    print("\n[6/6] Generating class code...")
    tc = db.query(TeacherClass).filter(TeacherClass.id == CLASS_ID).first()
    if tc:
        if not tc.code:
            tc.code = f"H{TEACHER_ID}{secrets.token_hex(3).upper()}"
            log(f"  Class 12 code → '{tc.code}'")
        else:
            log(f"  Class 12 code already '{tc.code}' — OK")
    else:
        log(f"  Class 12 NOT FOUND!")

    # ── Commit ──────────────────────────────────────────────────────
    db.commit()
    print("\n" + "=" * 60)
    print("ALL CHANGES COMMITTED SUCCESSFULLY")
    print("=" * 60)

    # ── Verification ────────────────────────────────────────────────
    print("\n--- VERIFICATION ---")
    for sid in STUDENT_IDS:
        s = db.query(User).filter(User.id == sid).first()
        abo = db.query(Abonnement).filter(Abonnement.user_id == sid, Abonnement.statut == "actif").first()
        if abo:
            pack_obj = db.query(PackDefinition).filter(PackDefinition.id == abo.pack_id).first()
            pack_name = pack_obj.nom if pack_obj else "UNKNOWN"
        else:
            pack_name = "NONE"
        abo_statut = abo.statut if abo else "N/A"
        print(f"  {s.full_name} (id={sid}): niveau='{s.niveau_scolaire}' pack='{pack_name}' statut='{abo_statut}'")

    course = db.query(Course).filter(Course.id == COURSE_ID).first()
    lesson_count = sum(
        db.query(Lesson).filter(Lesson.module_id == m.id).count()
        for m in db.query(Module).filter(Module.course_id == COURSE_ID).all()
    )
    print(f"  Course 20: status={course.status} visibility={course.visibility} lessons_total={lesson_count}")

    tc = db.query(TeacherClass).filter(TeacherClass.id == CLASS_ID).first()
    print(f"  Class 12: code={tc.code}")

finally:
    db.close()
