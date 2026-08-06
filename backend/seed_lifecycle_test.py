"""
Seed du cycle de vie complet : elements pedagogiques -> lecon -> cours -> pack -> eleve test.
Idempotent : verifie l'existence avant d'inserer.

Usage:
    cd backend
    python seed_lifecycle_test.py
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if not os.environ.get("DATABASE_URL"):
    os.environ["DATABASE_URL"] = "postgresql+pg8000://postgres:gill4264@localhost:5432/eduai"

from sqlalchemy.orm import sessionmaker
from app.core.security import get_password_hash
from app.models import (
    Base, School, User, Course, Module, Lesson, Quiz, QuizQuestion, QuizOption,
    Parcours, Chapitre, Lecon,
    ElementPedagogique, ElementTexte, ElementVideo, ElementQuiz,
    ContentWorkflow,
    PackDefinition, Abonnement,
    WalletTransaction,
    UserRole, CourseStatus, PedagogicalStatus, CourseOwnerType, CourseVisibility,
    WalletPool,
)

HASHED_PASSWORD = get_password_hash("passeword123")
NOW = datetime.now(timezone.utc)


def _lbl(created: bool) -> str:
    return "[NEW]" if created else "[EXISTS]"


def get_or_create(session, model, defaults=None, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    params = {**kwargs}
    if defaults:
        params.update(defaults)
    instance = model(**params)
    session.add(instance)
    session.flush()
    return instance, True


def seed():
    from app.db.session import engine, SessionLocal

    print("=" * 60)
    print("  Seed Cycle de Vie: Elements -> Cours -> Pack -> Eleve")
    print("=" * 60)

    Base.metadata.create_all(bind=engine)
    session = SessionLocal()

    try:
        # ── ETAPE 0 : Ecole de test ────────────────────────────────
        print("\n[1/8] Ecole de test ...")
        school, _ = get_or_create(
            session, School, slug="carthage",
            defaults=dict(name="Lycee Carthage", is_active=True, max_users=200),
        )
        print("  %s Ecole: %s (id=%d)" % (_lbl(False), school.name, school.id))

        # ── ETAPE 1 : Auteur (enseignant) ─────────────────────────
        print("\n[2/8] Auteur (enseignant) ...")
        teacher, is_new = get_or_create(
            session, User, email="prof.maths.lifecycle@eduai.tn",
            defaults=dict(
                full_name="Prof Maths Lifecycle",
                role=UserRole.TEACHER.value,
                school_id=school.id,
                hashed_password=HASHED_PASSWORD,
                is_active=True, onboarding_complete=True, is_approved=True,
            ),
        )
        print("  %s %s (id=%d)" % (_lbl(is_new), teacher.email, teacher.id))

        # ── ETAPE 2 : Elements pedagogiques (bibliotheque globale) ─
        print("\n[3/8] Elements pedagogiques ...")

        # 2a. Parcours -> Chapitre -> Lecon
        parcours, is_new = get_or_create(
            session, Parcours, titre="Fractions - Parcours Complet",
            defaults=dict(
                matiere="Mathematiques", niveau_scolaire="9eme de base",
                difficulte="moyen", auteur_id=teacher.id,
                est_publique=True, est_actif=True,
                description="Parcours complet sur les fractions pour le 9eme de base."),
        )
        print("  %s Parcours: %s (id=%d)" % (_lbl(is_new), parcours.titre, parcours.id))

        chapitre, is_new = get_or_create(
            session, Chapitre, titre="Introduction aux Fractions",
            defaults=dict(parcours_id=parcours.id, ordre=1,
                          description="Decouverte des fractions et leurs proprietes."),
        )
        print("  %s Chapitre: %s (id=%d)" % (_lbl(is_new), chapitre.titre, chapitre.id))

        lecon, is_new = get_or_create(
            session, Lecon, titre="Comprendre les fractions",
            defaults=dict(chapitre_id=chapitre.id, ordre=1, duree_minutes=30,
                          description="Lecon complete sur la definition et les operations sur les fractions."),
        )
        print("  %s Lecon: %s (id=%d)" % (_lbl(is_new), lecon.titre, lecon.id))

        # 2b. Element Texte
        elem_texte, is_new = get_or_create(
            session, ElementPedagogique, titre="Definition des fractions",
            defaults=dict(
                type="texte", lecon_id=lecon.id, auteur_id=teacher.id,
                statut="publie", difficulte="facile", est_global=True,
                description="Element texte : definition des fractions."),
        )
        if is_new:
            session.add(ElementTexte(
                element_id=elem_texte.id,
                corps="Une fraction est un nombre qui represente une partie d'un tout. "
                      "Elle s'ecrit sous la forme a/b où 'a' est le numerateur et 'b' le denominateur. "
                      "Exemple : 3/4 signifie 3 parts sur 4."),
            )
            session.add(ContentWorkflow(
                element_id=elem_texte.id, ancien_statut="brouillon",
                nouveau_statut="publie", auteur_id=teacher.id,
                commentaires="Auto- publie par l'enseignant."))
        print("  %s Element Texte: %s (id=%d)" % (_lbl(is_new), elem_texte.titre, elem_texte.id))

        # 2c. Element Video
        elem_video, is_new = get_or_create(
            session, ElementPedagogique, titre="Video sur les fractions",
            defaults=dict(
                type="video", lecon_id=lecon.id, auteur_id=teacher.id,
                statut="publie", difficulte="moyen", est_global=True,
                description="Element video : explication visuelle des fractions."),
        )
        if is_new:
            session.add(ElementVideo(
                element_id=elem_video.id,
                url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                duree_secondes=600,
                thumbnail_url="https://img.youtube.com/vi/dQw4w9WgXcQ/hqdefault.jpg"))
            session.add(ContentWorkflow(
                element_id=elem_video.id, ancien_statut="brouillon",
                nouveau_statut="publie", auteur_id=teacher.id,
                commentaires="Auto- publie par l'enseignant."))
        print("  %s Element Video: %s (id=%d)" % (_lbl(is_new), elem_video.titre, elem_video.id))

        # 2d. Element Quiz
        elem_quiz, is_new = get_or_create(
            session, ElementPedagogique, titre="Quiz Fractions",
            defaults=dict(
                type="quiz", lecon_id=lecon.id, auteur_id=teacher.id,
                statut="publie", difficulte="moyen", est_global=True,
                description="Element quiz : evaluation rapide sur les fractions."),
        )
        if is_new:
            session.add(ElementQuiz(
                element_id=elem_quiz.id,
                questions_json={
                    "questions": [
                        {
                            "texte": "Que vaut 1/2 + 1/4 ?",
                            "options": ["2/6", "3/4", "2/4", "1/6"],
                            "reponse_correcte": 1,
                            "explication": "1/2 = 2/4, donc 2/4 + 1/4 = 3/4"
                        }
                    ]
                },
                score_reussite=0.6))
            session.add(ContentWorkflow(
                element_id=elem_quiz.id, ancien_statut="brouillon",
                nouveau_statut="publie", auteur_id=teacher.id,
                commentaires="Auto- publie par l'enseignant."))
        print("  %s Element Quiz: %s (id=%d)" % (_lbl(is_new), elem_quiz.titre, elem_quiz.id))
        session.flush()

        # ── ETAPE 3 : Cours (course builder) ──────────────────────
        print("\n[4/8] Cours (Course Builder) ...")
        course, is_new = get_or_create(
            session, Course, slug="maths-9eme-tronc-commun",
            defaults=dict(
                title="Mathematiques - 9eme de base - Tronc Commun",
                school_id=school.id, author_id=teacher.id,
                owner_type=CourseOwnerType.SCHOOL.value,
                niveau_scolaire="9eme de base",
                category="Mathematiques",
                tag_pack_requis="Basic",
                price=None,
                visibility=CourseVisibility.PUBLIC_CATALOG.value,
                status=CourseStatus.PUBLISHED.value,
                pedagogical_status=PedagogicalStatus.APPROVED_LOCAL.value,
                is_published=True,
                is_active_version=True,
                version_number=1,
                total_modules=1, total_lessons=1,
                description="Cours complet de mathematiques pour le 9eme de base - Tronc Commun."))
        print("  %s Course: %s (id=%d)" % (_lbl(is_new), course.title, course.id))

        # Module
        module, is_new = get_or_create(
            session, Module, title="Module 1 - Les Fractions",
            defaults=dict(course_id=course.id, description="Introduction aux fractions", order=1))
        print("  %s Module: %s (id=%d)" % (_lbl(is_new), module.title, module.id))

        # Lesson (course builder)
        lesson, is_new = get_or_create(
            session, Lesson, title="Comprendre les fractions",
            defaults=dict(
                module_id=module.id, school_id=school.id, teacher_id=teacher.id,
                lesson_type="text", content_type="text",
                content_text="Contenu de la lecon sur les fractions. "
                             "Une fraction represente une partie d'un tout.",
                order=1, duration_minutes=30, is_free=False))
        print("  %s Lesson: %s (id=%d)" % (_lbl(is_new), lesson.title, lesson.id))

        # Quiz lie a la lesson
        quiz, is_new = get_or_create(
            session, Quiz, title="Quiz Fractions - Cours",
            defaults=dict(
                lesson_id=lesson.id, description="Quiz de validation",
                passing_score_percent=70, total_points=2, school_id=school.id))
        if is_new:
            q1 = QuizQuestion(quiz_id=quiz.id, question_text="Que vaut 3/4 + 1/4 ?",
                              question_type="mcq", points=1, order_index=1)
            session.add(q1)
            session.flush()
            session.add_all([
                QuizOption(question_id=q1.id, option_text="4/8", is_correct=False, order_index=1),
                QuizOption(question_id=q1.id, option_text="1", is_correct=True, order_index=2),
                QuizOption(question_id=q1.id, option_text="4/4", is_correct=False, order_index=3),
                QuizOption(question_id=q1.id, option_text="2/4", is_correct=False, order_index=4),
            ])
        print("  %s Quiz: %s (id=%d)" % (_lbl(is_new), quiz.title, quiz.id))
        session.flush()

        # ── ETAPE 4 : Pack Commercial ──────────────────────────────
        print("\n[5/8] Pack Commercial (PackDefinition) ...")
        pack, is_new = get_or_create(
            session, PackDefinition, tier="Basic", niveau_scolaire="9eme de base",
            defaults=dict(
                nom="Pack Basic Mathematiques - 9eme",
                description="Acces aux cours de mathematiques de niveau 9eme de base.",
                matieres={"matieres": ["Mathematiques"]},
                prix_tnd=19.99,
                features={"ai_tutor": True, "quizzes": True},
                est_actif=True))
        print("  %s Pack: %s (id=%d, %.2f TND)" % (_lbl(is_new), pack.nom, pack.id, float(pack.prix_tnd)))
        session.flush()

        # ── ETAPE 5 : Eleve de test ───────────────────────────────
        print("\n[6/8] Eleve de test (sans abonnement) ...")
        student, is_new = get_or_create(
            session, User, email="eleve.test@eduai.tn",
            defaults=dict(
                full_name="Eleve Test Lifecycle",
                role=UserRole.STUDENT.value,
                school_id=school.id,
                hashed_password=HASHED_PASSWORD,
                niveau_scolaire="9eme de base",
                is_active=True, onboarding_complete=True))
        print("  %s %s (id=%d, niveau=%s)" % (
            _lbl(is_new), student.email, student.id, student.niveau_scolaire))

        # ── ETAPE 6 : Wallet (100 TND DT_PURCHASED) ──────────────
        print("\n[7/8] Wallet (100 TND DT_PURCHASED) ...")
        existing_wallet = session.query(WalletTransaction).filter_by(
            user_id=student.id, pool=WalletPool.DT_PURCHASED).first()
        if not existing_wallet:
            session.add(WalletTransaction(
                user_id=student.id,
                pool=WalletPool.DT_PURCHASED,
                amount=100.0))
            print("  [NEW] Wallet: 100.00 TND (DT_PURCHASED) pour %s" % student.email)
        else:
            print("  [EXISTS] Wallet DT_PURCHASED pour %s" % student.email)
        session.flush()

        # ── VERIFICATION : pas d'abonnement actif ─────────────────
        print("\n[8/8] Verification : pas d'abonnement actif ...")
        existing_abo = session.query(Abonnement).filter_by(user_id=student.id).first()
        if existing_abo:
            print("  [WARN] Un abonnement existe deja pour %s (id=%d)" % (student.email, existing_abo.id))
        else:
            print("  [OK] Aucun abonnement pour %s - statut 'Gratuit'" % student.email)

        # ── COMMIT ────────────────────────────────────────────────
        session.commit()

        print("\n" + "=" * 60)
        print("  Seed Cycle de Vie - Termine !")
        print("=" * 60)
        print()
        print("  Entites creees :")
        print("    - Parcours     : Fractions - Parcours Complet (id=%d)" % parcours.id)
        print("    - Chapitre     : Introduction aux Fractions (id=%d)" % chapitre.id)
        print("    - Lecon        : Comprendre les fractions (id=%d)" % lecon.id)
        print("    - Element Texte: Definition des fractions (id=%d)" % elem_texte.id)
        print("    - Element Video: Video sur les fractions (id=%d)" % elem_video.id)
        print("    - Element Quiz : Quiz Fractions (id=%d)" % elem_quiz.id)
        print("    - Course       : Maths 9eme Tronc Commun (id=%d)" % course.id)
        print("    - Module       : Module 1 - Les Fractions (id=%d)" % module.id)
        print("    - Lesson       : Comprendre les fractions (id=%d)" % lesson.id)
        print("    - Quiz Cours   : Quiz Fractions - Cours (id=%d)" % quiz.id)
        print("    - Pack         : Pack Basic Maths 9eme (id=%d, 19.99 TND)" % pack.id)
        print("    - Student      : eleve.test@eduai.tn (id=%d)" % student.id)
        print()
        print("  Identifiants de connexion :")
        print("    Email    : eleve.test@eduai.tn")
        print("    Password : passeword123")
        print("    Wallet   : 100.00 TND (DT_PURCHASED)")
        print("    Pack     : Basic - 19.99 TND - 0 abonnement actif")
        print()
        print("  Tag ABAC : tag_pack_requis='Basic' sur le cours")
        print("  -> Un eleve 'Gratuit' verra l'UpsellModal (402)")
        print("  -> Apres achat du pack Basic, acces accorde")
        print("=" * 60)

    except Exception as e:
        session.rollback()
        print("\n  ERROR: %s" % e)
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed()
