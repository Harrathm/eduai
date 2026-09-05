"""
Script de synchronisation pour eleve.test@eduai.tn
1. Remet le niveau_scolaire a "9eme Annee Base" (aligne avec le pack actif)
2. Reactiver l'abonnement invalide (niveau correspond maintenant)
3. Inscrit au cours ID 90 s'il ne l'est pas deja
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.db import SessionLocal
from app.models import User, Abonnement, PackDefinition, Course, CourseEnrollment
from datetime import datetime, timezone

db = SessionLocal()

EMAIL = "eleve.test@eduai.tn"
NEW_NIVEAU = "9eme Annee Base"
COURSE_ID = 89  # Mathematiques - 9eme de base - Tronc Commun

try:
    # 1. Trouver l'eleve
    student = db.query(User).filter(User.email == EMAIL).first()
    if not student:
        print(f"[ERREUR] Utilisateur {EMAIL} non trouve")
        sys.exit(1)

    print(f"[INFO] Student: id={student.id}, email={student.email}, niveau={student.niveau_scolaire}, role={student.role}")

    # 2. Remettre le niveau_scolaire
    old_niveau = student.niveau_scolaire
    student.niveau_scolaire = NEW_NIVEAU
    print(f"[UPDATE] niveau_scolaire: '{old_niveau}' -> '{NEW_NIVEAU}'")

    # 3. Trouver l'abonnement (tous statuts)
    abo = db.query(Abonnement).filter(
        Abonnement.user_id == student.id,
    ).order_by(Abonnement.created_at.desc()).first()

    if not abo:
        print("[ERREUR] Aucun abonnement trouve")
        sys.exit(1)

    pack = db.query(PackDefinition).filter(PackDefinition.id == abo.pack_id).first()
    print(f"[INFO] Abonnement: id={abo.id}, pack_id={abo.pack_id}, pack_nom={pack.nom if pack else '?'}, statut={abo.statut}, matieres_config={abo.matieres_config}")

    # 4. Reactiver si invalide (le niveau correspond maintenant)
    if abo.statut == "invalide":
        abo.statut = "actif"
        print(f"[UPDATE] abonnement statut: 'invalide' -> 'actif'")
    elif abo.statut == "actif":
        print(f"[SKIP] Abonnement deja actif")
    else:
        print(f"[INFO] Abonnement statut={abo.statut}, pas de modification")

    # 5. Verifier le cours cible
    course = db.query(Course).filter(Course.id == COURSE_ID).first()
    if not course:
        print(f"[ERREUR] Cours ID {COURSE_ID} non trouve")
        sys.exit(1)

    print(f"[INFO] Cours cible: id={course.id}, title={course.title}, niveau_scolaire={course.niveau_scolaire}, category={course.category}")

    # 6. Incrire si pas deja inscrit
    existing = db.query(CourseEnrollment).filter(
        CourseEnrollment.student_id == student.id,
        CourseEnrollment.course_id == COURSE_ID,
    ).first()

    if existing:
        print(f"[SKIP] Deja inscrit au cours {COURSE_ID} (enrollment id={existing.id})")
    else:
        enrollment = CourseEnrollment(
            student_id=student.id,
            course_id=COURSE_ID,
            status="active",
            enrolled_at=datetime.now(timezone.utc),
        )
        db.add(enrollment)
        db.flush()
        print(f"[CREATE] Enrollment id={enrollment.id} pour cours {COURSE_ID}")

    # 7. Verifier les inscriptions existantes
    all_enrollments = db.query(CourseEnrollment).filter(
        CourseEnrollment.student_id == student.id
    ).all()
    print(f"[INFO] Total inscriptions: {len(all_enrollments)}")
    for e in all_enrollments:
        c = db.query(Course).filter(Course.id == e.course_id).first()
        print(f"  - enrollment id={e.id}, course_id={e.course_id}, title={c.title if c else '?'}, status={e.status}")

    # 8. Verifier etat final
    db.commit()
    final_niveau = db.query(User).filter(User.id == student.id).first().niveau_scolaire
    final_abo = db.query(Abonnement).filter(Abonnement.id == abo.id).first()
    final_enrollments = db.query(CourseEnrollment).filter(CourseEnrollment.student_id == student.id).count()

    print(f"\n=== ETAT FINAL ===")
    print(f"niveau_scolaire: {final_niveau}")
    print(f"abonnement statut: {final_abo.statut}")
    print(f"total enrollments: {final_enrollments}")
    print("[OK] Synchronisation terminee avec succes!")

except Exception as e:
    db.rollback()
    print(f"[ERREUR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    db.close()
