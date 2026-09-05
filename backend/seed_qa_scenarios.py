"""
Script de seed QA — comble les scénarios manquants de la base de test EDUAI.

Idempotent : ne crée une ressource que si elle n'existe pas déjà.
Tous les mots de passe : passeword123

Scénarios couverts :
  1. Rôles & RBAC
     - teacher.qa.pending@eduai.tn   : enseignant État B (is_approved=False)
     - teacher.qa.trial@eduai.tn     : enseignant État C (subscription_plan='trial')
     - multirole.qa@eduai.tn         : admin_school + pedagogical_lead
  2. Monétisation & ABAC
     - student.qa.free@eduai.tn      : pack Gratuit (quota 3 leçons / Upsell)
     - student.qa.basic@eduai.tn     : pack Basic (matières configurées)
     - student.qa.silver@eduai.tn    : pack Silver
     - student.qa.golden@eduai.tn    : pack Golden (accès illimité + Soft Skills)
     - student.qa.invalid@eduai.tn   : pack invalidé (changement de niveau)
     - Revenue Share : CoursePurchase + LessonProgress sur cours partner (86)
     - Voucher consommé Teacher_Training
  3. CMS & Modération
     - Cours Scolaire draft (dédié QA)
     - Cours Scolaire pending_review
     - Cours Soft_Skill publié
     - Cours Teacher_Training publié
     - Cours versioning : V1 publiée + V2 brouillon
  4. Parent & Famille
     - parent.qa.famille@eduai.tn rattaché à 3 élèves (remises 20% et 25%)
"""
import sys
import os
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(__file__))

from app.db import SessionLocal
from app.core.security import get_password_hash
from app.models import (
    User, School, Course, Module, Lesson, CourseEnrollment,
    PackDefinition, Abonnement, BulkSeatVoucher,
    ParentEnfant, CompteFamille, FamilleEnfant,
    CoursePurchase, LessonProgress,
    ChapterPathway, Matiere, NiveauEtude,
)

PASSWORD = get_password_hash("passeword123")
NOW = datetime.now(timezone.utc)

# École cible : Lycee Carthage (slug 'carthage')
SCHOOL_SLUG = "carthage"

# Niveau tunisien ciblé (aligne avec les packs "9eme de base")
NIVEAU = "9eme de base"

# Cours existants utilisés (vérifiés présents)
PARTNER_COURSE_ID = 86      # Algorithmique Avancee - Partner (owner partner@eduai.tn)
PARTNER_LESSON_ID = 163     # Lecon Algorithmique Base (teacher_id=87)
TRAINING_COURSE_ID = 88     # Formation Enseignants - Pedagogie Numerique

db = SessionLocal()


# ──────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────

def get_or_create_user(email, role, school_id=None, **kwargs):
    user = db.query(User).filter(User.email == email).first()
    if user:
        print(f"  [SKIP] user {email} (id={user.id})")
        return user
    defaults = dict(
        hashed_password=PASSWORD,
        is_active=True,
        language="fr",
    )
    defaults.update(kwargs)
    user = User(email=email, role=role, school_id=school_id, **defaults)
    db.add(user)
    db.flush()
    print(f"  [CREATE] user {email} (id={user.id}, role={role})")
    return user


def get_pack(niveau, tier):
    pack = db.query(PackDefinition).filter(
        PackDefinition.niveau_scolaire == niveau,
        PackDefinition.tier == tier,
    ).first()
    if not pack:
        raise RuntimeError(f"Pack introuvable niveau={niveau} tier={tier}")
    return pack


def get_or_create_abonnement(user, pack, statut="actif", matieres_config=None):
    abo = db.query(Abonnement).filter(
        Abonnement.user_id == user.id,
        Abonnement.pack_id == pack.id,
    ).first()
    if abo:
        print(f"  [SKIP] abonnement user={user.id} pack={pack.id} (id={abo.id})")
        return abo
    abo = Abonnement(
        user_id=user.id,
        pack_id=pack.id,
        statut=statut,
        debut=NOW - timedelta(days=30),
        fin=NOW + timedelta(days=330),
        matieres_config=matieres_config,
    )
    db.add(abo)
    db.flush()
    print(f"  [CREATE] abonnement user={user.id} pack={pack.id} statut={statut}")
    return abo


def get_or_create_course(title, slug, category, category_cible, status, pedagogical_status,
                         school_id, author_id, visibility="school_only",
                         niveau_scolaire=None, tag_pack_requis="Basic",
                         version_number=1, is_active_version=True,
                         is_published=None, **kwargs):
    course = db.query(Course).filter(Course.slug == slug).first()
    if course:
        print(f"  [SKIP] course {slug} (id={course.id})")
        return course
    if is_published is None:
        is_published = status == "published"
    course = Course(
        title=title,
        slug=slug,
        category=category,
        category_cible=category_cible,
        status=status,
        pedagogical_status=pedagogical_status,
        school_id=school_id,
        author_id=author_id,
        visibility=visibility,
        niveau_scolaire=niveau_scolaire,
        tag_pack_requis=tag_pack_requis,
        version_number=version_number,
        is_active_version=is_active_version,
        is_published=is_published,
        owner_type="school",
        language="fr",
        **kwargs,
    )
    db.add(course)
    db.flush()
    print(f"  [CREATE] course {slug} (id={course.id}, status={status}, pedago={pedagogical_status})")
    return course


def get_or_create_module_lesson(course, module_title, lesson_title):
    module = db.query(Module).filter(
        Module.course_id == course.id,
        Module.title == module_title,
    ).first()
    if module:
        lesson = db.query(Lesson).filter(
            Lesson.module_id == module.id,
            Lesson.title == lesson_title,
        ).first()
        if lesson:
            print(f"  [SKIP] module/lesson for course {course.id}")
            return
        lesson = Lesson(
            module_id=module.id,
            school_id=course.school_id,
            title=lesson_title,
            order=0,
            duration_minutes=15,
        )
        db.add(lesson)
        db.flush()
        print(f"  [CREATE] lesson {lesson.title} (id={lesson.id})")
        return
    module = Module(course_id=course.id, title=module_title, order=0)
    db.add(module)
    db.flush()
    lesson = Lesson(
        module_id=module.id,
        school_id=course.school_id,
        title=lesson_title,
        order=0,
        duration_minutes=15,
    )
    db.add(lesson)
    db.flush()
    print(f"  [CREATE] module {module.title} (id={module.id}) + lesson {lesson.title} (id={lesson.id})")


def get_or_create_enrollment(student, course, status="active"):
    enr = db.query(CourseEnrollment).filter(
        CourseEnrollment.student_id == student.id,
        CourseEnrollment.course_id == course.id,
    ).first()
    if enr:
        print(f"  [SKIP] enrollment student={student.id} course={course.id} (id={enr.id})")
        return enr
    enr = CourseEnrollment(
        student_id=student.id,
        course_id=course.id,
        status=status,
        enrolled_at=NOW - timedelta(days=15),
    )
    db.add(enr)
    db.flush()
    print(f"  [CREATE] enrollment student={student.id} course={course.id} (id={enr.id})")
    return enr


def get_or_create_voucher(code, school_id, formation_id, status, consumed_by=None):
    voucher = db.query(BulkSeatVoucher).filter(BulkSeatVoucher.code == code).first()
    if voucher:
        print(f"  [SKIP] voucher {code} (id={voucher.id})")
        return voucher
    voucher = BulkSeatVoucher(
        school_id=school_id,
        formation_id=formation_id,
        code=code,
        status=status,
        consumed_by=consumed_by,
    )
    db.add(voucher)
    db.flush()
    print(f"  [CREATE] voucher {code} (id={voucher.id}, status={status})")
    return voucher


def get_niveau_etude(nom):
    n = db.query(NiveauEtude).filter(NiveauEtude.nom == nom).first()
    if not n:
        raise RuntimeError(f"NiveauEtude introuvable: {nom}")
    return n


def get_matiere(niveau, nom):
    mat = db.query(Matiere).filter(
        Matiere.niveau_etude_id == niveau.id,
        Matiere.nom == nom,
    ).first()
    if not mat:
        raise RuntimeError(f"Matiere introuvable niveau={niveau.nom} nom={nom}")
    return mat


# ──────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────

def main():
    print(f"=== Seed QA Scénarios ===\n")

    # École cible
    school = db.query(School).filter(School.slug == SCHOOL_SLUG).first()
    if not school:
        print(f"[ERREUR] École slug={SCHOOL_SLUG} introuvable")
        sys.exit(1)
    school_id = school.id
    print(f"[INFO] École: {school.name} (id={school_id})")

    # Auteur "super admin" du catalogue
    super_admin = db.query(User).filter(User.email == "superadmin@eduai.tn").first()
    if not super_admin:
        super_admin = db.query(User).filter(User.role == "super_admin").first()
    if not super_admin:
        super_admin = get_or_create_user("superadmin@eduai.tn", "super_admin")
    author_id = super_admin.id

    # ── 1. Rôles & RBAC ──────────────────────────────────
    print("\n--- 1. Rôles & RBAC ---")

    teacher_pending = get_or_create_user(
        "teacher.qa.pending@eduai.tn", "teacher", school_id=school_id,
        full_name="QA Teacher État B", is_approved=False,
        subscription_plan="trial",
    )

    teacher_trial = get_or_create_user(
        "teacher.qa.trial@eduai.tn", "teacher", school_id=school_id,
        full_name="QA Teacher État C", is_approved=True,
        subscription_plan="trial",
    )

    multirole = get_or_create_user(
        "multirole.qa@eduai.tn", "admin_school", school_id=school_id,
        full_name="QA Multi-Rôles",
        roles=["admin_school", "pedagogical_lead"],
        active_context_role="admin_school",
    )

    # ── 2. Monétisation & ABAC ───────────────────────────
    print("\n--- 2. Monétisation & ABAC ---")

    # Niveau 9eme de base — matières officielles (niveau_etude "9ème Année Base")
    niveau = get_niveau_etude("9ème Année Base")
    mat_math = get_matiere(niveau, "رياضيات")       # spécialité
    mat_physique = get_matiere(niveau, "علوم فيزيائية")  # spécialité
    mat_arabe = get_matiere(niveau, "العربية")      # langue
    mat_fr = get_matiere(niveau, "الفرنسية")        # langue
    mat_anglais = get_matiere(niveau, "الانقليزية") # langue
    print(f"[INFO] Matières 9ème: math={mat_math.id} physique={mat_physique.id} arabe={mat_arabe.id} fr={mat_fr.id} anglais={mat_anglais.id}")

    # Packs du niveau
    pack_free = get_pack(NIVEAU, "gratuit")
    pack_basic = get_pack(NIVEAU, "basique")
    pack_silver = get_pack(NIVEAU, "silver")
    pack_golden = get_pack(NIVEAU, "golden")

    # Élèves par pack
    student_free = get_or_create_user(
        "student.qa.free@eduai.tn", "student", school_id=school_id,
        full_name="QA Élève Gratuit", niveau_scolaire=NIVEAU,
    )
    student_basic = get_or_create_user(
        "student.qa.basic@eduai.tn", "student", school_id=school_id,
        full_name="QA Élève Basic", niveau_scolaire=NIVEAU,
    )
    student_silver = get_or_create_user(
        "student.qa.silver@eduai.tn", "student", school_id=school_id,
        full_name="QA Élève Silver", niveau_scolaire=NIVEAU,
    )
    student_golden = get_or_create_user(
        "student.qa.golden@eduai.tn", "student", school_id=school_id,
        full_name="QA Élève Golden", niveau_scolaire=NIVEAU,
    )
    student_invalid = get_or_create_user(
        "student.qa.invalid@eduai.tn", "student", school_id=school_id,
        full_name="QA Élève Pack Invalidé", niveau_scolaire=NIVEAU,
    )

    # Abonnements
    abo_free = get_or_create_abonnement(student_free, pack_free, "actif",
                                        matieres_config=[mat_arabe.id, mat_math.id])
    abo_basic = get_or_create_abonnement(student_basic, pack_basic, "actif",
                                         matieres_config=[mat_arabe.id, mat_fr.id, mat_math.id])
    abo_silver = get_or_create_abonnement(student_silver, pack_silver, "actif",
                                          matieres_config=[mat_arabe.id, mat_fr.id, mat_math.id, mat_physique.id])
    abo_golden = get_or_create_abonnement(student_golden, pack_golden, "actif",
                                          matieres_config=[mat_arabe.id, mat_fr.id, mat_anglais.id, mat_math.id, mat_physique.id])
    abo_invalid = get_or_create_abonnement(student_invalid, pack_basic, "invalide",
                                           matieres_config=[mat_math.id])

    # Revenue Share : CoursePurchase + LessonProgress sur le cours partner
    print("  -- Revenue Share (cours partner) --")
    partner_course = db.query(Course).filter(Course.id == PARTNER_COURSE_ID).first()
    if not partner_course:
        print("  [ERREUR] Cours partner 86 introuvable")
    else:
        purchase = db.query(CoursePurchase).filter(
            CoursePurchase.student_id == student_silver.id,
            CoursePurchase.course_id == partner_course.id,
        ).first()
        if purchase:
            print(f"  [SKIP] CoursePurchase student={student_silver.id} course={partner_course.id} (id={purchase.id})")
        else:
            purchase = CoursePurchase(
                student_id=student_silver.id,
                course_id=partner_course.id,
                amount_paid=10.00,
                currency="TND",
                platform_fee=3.00,
                teacher_revenue=7.00,
                commission_rate_applied=30.00,
                purchased_at=NOW - timedelta(days=10),
            )
            db.add(purchase)
            db.flush()
            print(f"  [CREATE] CoursePurchase id={purchase.id} (revenue teacher=7.00)")

        # Inscription + progression de l'élève silver sur le cours partner
        enr = get_or_create_enrollment(student_silver, partner_course)
        progress = db.query(LessonProgress).filter(
            LessonProgress.enrollment_id == enr.id,
            LessonProgress.lesson_id == PARTNER_LESSON_ID,
        ).first()
        if progress:
            print(f"  [SKIP] LessonProgress enr={enr.id} lesson={PARTNER_LESSON_ID}")
        else:
            progress = LessonProgress(
                enrollment_id=enr.id,
                lesson_id=PARTNER_LESSON_ID,
                status="completed",
                video_completed=True,
                content_completed=True,
                quiz_completed=True,
                quiz_passed=True,
                quiz_score=0.85,
                started_at=NOW - timedelta(days=10),
                completed_at=NOW - timedelta(days=9),
                time_spent_seconds=900,
            )
            db.add(progress)
            db.flush()
            print(f"  [CREATE] LessonProgress id={progress.id} (status=completed)")

    # Vouchers : unused + consumed pour Teacher_Training
    print("  -- Vouchers Bulk Seats --")
    get_or_create_voucher("BULK-QA-TRAIN-0001", school_id, TRAINING_COURSE_ID, "unused")
    get_or_create_voucher("BULK-QA-TRAIN-0002", school_id, TRAINING_COURSE_ID, "consumed",
                          consumed_by=teacher_trial.id)

    # ── 3. CMS & Modération ──────────────────────────────
    print("\n--- 3. CMS & Modération ---")

    # Cours Scolaire draft (dédié QA)
    draft_course = get_or_create_course(
        "QA - Algèbre 9ème (brouillon)", "qa-algebre-9eme-draft",
        category="Mathematiques", category_cible="Scolaire",
        status="draft", pedagogical_status="draft",
        school_id=school_id, author_id=author_id,
        niveau_scolaire=NIVEAU, tag_pack_requis="Basic",
    )

    # Cours Scolaire pending_review (validation locale par un Leader)
    pending_course = get_or_create_course(
        "QA - Géométrie 9ème (en attente validation)",
        "qa-geometrie-9eme-pending",
        category="Mathematiques", category_cible="Scolaire",
        status="pending", pedagogical_status="pending_review",
        school_id=school_id, author_id=author_id,
        niveau_scolaire=NIVEAU, tag_pack_requis="Basic",
    )

    # Cours Scolaire approved_for_b2b (dédié QA)
    b2b_course = get_or_create_course(
        "QA - SVT 9ème (validé B2B)", "qa-svt-9eme-b2b",
        category="Sciences", category_cible="Scolaire",
        status="published", pedagogical_status="approved_for_b2b",
        school_id=school_id, author_id=author_id,
        visibility="public_catalog",
        niveau_scolaire=NIVEAU, tag_pack_requis="Silver",
    )

    # Cours Soft_Skill publié
    soft_course = get_or_create_course(
        "QA - Communication efficace", "qa-communication-softskill",
        category="Soft_Skill", category_cible="Soft_Skill",
        status="published", pedagogical_status="approved_local",
        school_id=school_id, author_id=author_id,
        visibility="public_catalog",
        niveau_scolaire=None, tag_pack_requis="Golden",
    )

    # Cours Teacher_Training publié (dédié QA)
    training_course = get_or_create_course(
        "QA - Formation enseignants (numérique)", "qa-formation-enseignants",
        category="Teacher_Training", category_cible="Teacher_Training",
        status="published", pedagogical_status="approved_local",
        school_id=school_id, author_id=author_id,
        visibility="public_catalog",
        niveau_scolaire=None, tag_pack_requis="Golden",
    )

    # Versioning : V1 publiée + V2 brouillon
    ver_v1 = get_or_create_course(
        "QA - Physique 9ème (V1)", "qa-physique-9eme-v1",
        category="Physique", category_cible="Scolaire",
        status="published", pedagogical_status="approved_local",
        school_id=school_id, author_id=author_id,
        niveau_scolaire=NIVEAU, tag_pack_requis="Basic",
        version_number=1, is_active_version=True,
    )
    ver_v2 = get_or_create_course(
        "QA - Physique 9ème (V2)", "qa-physique-9eme-v2",
        category="Physique", category_cible="Scolaire",
        status="draft", pedagogical_status="draft",
        school_id=school_id, author_id=author_id,
        niveau_scolaire=NIVEAU, tag_pack_requis="Basic",
        version_number=2, is_active_version=False,
    )

    # Modules + leçons pour les cours QA (éviter les écrans vides)
    for course, mt, lt in [
        (draft_course, "Module Algèbre", "Leçon : Résoudre une équation"),
        (pending_course, "Module Géométrie", "Leçon : Théorème de Pythagore"),
        (b2b_course, "Module SVT", "Leçon : La cellule vivante"),
        (soft_course, "Module Communication", "Leçon : Écoute active"),
        (training_course, "Module Pédagogie", "Leçon : Outils numériques"),
        (ver_v1, "Module Mécanique", "Leçon : Les forces"),
    ]:
        get_or_create_module_lesson(course, mt, lt)

    # ── 4. Parent & Famille ──────────────────────────────
    print("\n--- 4. Parent & Famille ---")

    parent = get_or_create_user(
        "parent.qa.famille@eduai.tn", "parent", school_id=school_id,
        full_name="QA Parent Famille",
    )

    children = []
    for i, (email, name) in enumerate([
        ("child.qa1@eduai.tn", "QA Enfant 1"),
        ("child.qa2@eduai.tn", "QA Enfant 2"),
        ("child.qa3@eduai.tn", "QA Enfant 3"),
    ], start=1):
        child = get_or_create_user(email, "student", school_id=school_id,
                                   full_name=name, niveau_scolaire=NIVEAU)
        children.append(child)

        link = db.query(ParentEnfant).filter(
            ParentEnfant.parent_user_id == parent.id,
            ParentEnfant.eleve_id == child.id,
        ).first()
        if not link:
            db.add(ParentEnfant(parent_user_id=parent.id, eleve_id=child.id))
            db.flush()
            print(f"  [CREATE] ParentEnfant parent={parent.id} eleve={child.id}")

    # Compte famille + remises (rang 2 → 20%, rang 3 → 25%)
    cf = db.query(CompteFamille).filter(CompteFamille.parent_id == parent.id).first()
    if not cf:
        cf = CompteFamille(parent_id=parent.id, max_enfants=5, rang_famille=1)
        db.add(cf)
        db.flush()
        print(f"  [CREATE] CompteFamille parent={parent.id} (id={cf.id})")

    for i, child in enumerate(children, start=1):
        fe = db.query(FamilleEnfant).filter(
            FamilleEnfant.compte_famille_id == cf.id,
            FamilleEnfant.eleve_id == child.id,
        ).first()
        remise = 0.0 if i == 1 else (20.0 if i == 2 else 25.0)
        if not fe:
            db.add(FamilleEnfant(
                compte_famille_id=cf.id,
                eleve_id=child.id,
                rang=i,
                remise_pct=remise,
            ))
            db.flush()
            print(f"  [CREATE] FamilleEnfant eleve={child.id} rang={i} remise={remise}%")

    # ── Commit ────────────────────────────────────────────
    db.commit()
    print(f"\n=== Seed QA terminé avec succès ===")
    print(f"\n--- RÉCAPITULATIF DES COMPTES DE TEST ---")
    print(f"  Tous les mots de passe : passeword123")
    for u in [teacher_pending, teacher_trial, multirole,
              student_free, student_basic, student_silver, student_golden, student_invalid,
              parent] + children:
        print(f"  {u.email:<32} {u.role:<18} id={u.id}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        db.rollback()
        print(f"[ERREUR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()
