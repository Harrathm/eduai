"""
Tests critiques — Phase 5 : Scénarios d'accès dynamique par pack.
Vérifie qu'AUCUNE inscription individuelle n'est créée pour un pack école,
et que l'accès est toujours recalculé dynamiquement.
"""
import os
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ENVIRONMENT"] = "development"

import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base
from app.models import (
    User, School, Course, CourseStatus, StudyPack, PackPurchase,
    PackPurchaseStatus, PackStatus, PurchaserType, CourseEnrollment,
)
from app.services.course_access import has_course_access, expire_pack_purchases


TEST_PASSWORD = "password123"


@pytest.fixture(scope="function")
def db():
    """In-memory test DB with all tables."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()

    # Créer une école
    school = School(name="École Test", slug="ecole-test", subscription_tier="free")
    session.add(school)
    session.commit()

    yield session, school
    session.close()


def _create_student(db, school, email, niveau_scolaire="9ème de base"):
    from app.core.security import get_password_hash
    student = User(
        email=email,
        hashed_password=get_password_hash(TEST_PASSWORD),
        full_name=f"Student {email}",
        role="student",
        is_active=True,
        school_id=school.id,
        niveau_scolaire=niveau_scolaire,
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


def _create_course(db, school, title, niveau_scolaire="9ème de base", category="Mathématiques", price=10.0, author_id=9999):
    course = Course(
        title=title,
        school_id=school.id,
        author_id=author_id,
        niveau_scolaire=niveau_scolaire,
        category=category,
        level="beginner",
        price=price,
        status=CourseStatus.PUBLISHED,
        is_published=True,
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


def _create_pack(db, name, niveau_scolaire, price=50.0, matieres=None, days=365):
    pack = StudyPack(
        name=name,
        niveau_scolaire=niveau_scolaire,
        matieres=matieres,
        price=price,
        validity_duration_days=days,
        status=PackStatus.PUBLISHED.value,
        created_by=1,
    )
    db.add(pack)
    db.commit()
    db.refresh(pack)
    return pack


def _create_pack_purchase(db, pack, school_id=None, student_id=None, days_valid=365, status=PackPurchaseStatus.ACTIVE.value):
    now = datetime.now(timezone.utc)
    purchase = PackPurchase(
        pack_id=pack.id,
        purchaser_type=PurchaserType.SCHOOL.value if school_id else PurchaserType.STUDENT.value,
        student_id=student_id,
        school_id=school_id,
        valid_from=now,
        valid_until=now + timedelta(days=days_valid),
        status=status,
        amount_paid=pack.price,
        currency=pack.currency,
    )
    db.add(purchase)
    db.commit()
    db.refresh(purchase)
    return purchase


# ============================================================
# SCÉNARIO 1 : Pack école → cours ajouté APRÈS l'achat
# ============================================================

class TestScenario1_NewCourseAfterPackPurchase:
    """
    Un élève dont l'école a acheté un pack pour son niveau
    accède bien à un cours ajouté APRÈS l'achat du pack,
    sans aucune action manuelle.
    """

    def test_access_to_course_added_after_pack(self, db):
        session, school = db
        student = _create_student(session, school, "s1@test.com", "9ème de base")
        pack = _create_pack(session, "Pack 9ème", "9ème de base")
        _create_pack_purchase(session, pack, school_id=school.id)

        # Le cours est créé APRÈS l'achat du pack
        course = _create_course(session, school, "Maths 9ème avancé", "9ème de base")

        # L'élève a accès sans inscription
        assert has_course_access(student, course, session) is True

        # Vérifier qu'AUCUNE inscription n'a été créée
        enrollment = session.query(CourseEnrollment).filter(
            CourseEnrollment.student_id == student.id,
            CourseEnrollment.course_id == course.id,
        ).first()
        assert enrollment is None, "Aucune inscription ne doit être créée pour un accès via pack"


# ============================================================
# SCÉNARIO 2 : Nouvel élève → accès immédiat
# ============================================================

class TestScenario2_NewStudentGetsAccess:
    """
    Un nouvel élève inscrit dans une école APRÈS l'achat d'un pack
    pour son niveau obtient l'accès immédiatement, sans création
    manuelle d'enrollment.
    """

    def test_new_student_enrolled_after_pack_purchase(self, db):
        session, school = db
        pack = _create_pack(session, "Pack 9ème", "9ème de base")
        _create_pack_purchase(session, pack, school_id=school.id)
        course = _create_course(session, school, "Sciences 9ème", "9ème de base")

        # Nouvel élève inscrit APRÈS l'achat du pack
        new_student = _create_student(session, school, "new_student@test.com", "9ème de base")

        assert has_course_access(new_student, course, session) is True

        # Pas d'inscription créée
        enrollment = session.query(CourseEnrollment).filter(
            CourseEnrollment.student_id == new_student.id,
            CourseEnrollment.course_id == course.id,
        ).first()
        assert enrollment is None


# ============================================================
# SCÉNARIO 3 : Changement de niveau → perte/gain d'accès
# ============================================================

class TestScenario3_LevelChange:
    """
    Un élève qui change de niveau (promotion ou redoublement) perd
    l'accès aux cours de son ancien niveau et gagne l'accès à ceux
    de son nouveau niveau, automatiquement.
    """

    def test_student_who_changes_level_loses_old_access(self, db):
        session, school = db
        student = _create_student(session, school, "chameleon@test.com", "9ème de base")
        pack_9 = _create_pack(session, "Pack 9ème", "9ème de base")
        _create_pack_purchase(session, pack_9, school_id=school.id)

        course_9 = _create_course(session, school, "Maths 9ème", "9ème de base")
        course_7 = _create_course(session, school, "Maths 7ème", "7ème de base")

        # Accès initial au niveau 9ème
        assert has_course_access(student, course_9, session) is True
        assert has_course_access(student, course_7, session) is False

        # L'élève change de niveau (promotion vers 7ème — ou redoublement)
        student.niveau_scolaire = "7ème de base"
        session.commit()

        # Pack 9ème ne couvre plus (niveau de l'élève ≠ niveau du pack)
        assert has_course_access(student, course_9, session) is False

        # Pas de pack pour 7ème → pas d'accès non plus
        assert has_course_access(student, course_7, session) is False

    def test_student_gets_access_after_level_change_with_new_pack(self, db):
        session, school = db
        student = _create_student(session, school, "promo@test.com", "9ème de base")
        pack_9 = _create_pack(session, "Pack 9ème", "9ème de base")
        _create_pack_purchase(session, pack_9, school_id=school.id)

        course_9 = _create_course(session, school, "Maths 9ème", "9ème de base")
        course_7 = _create_course(session, school, "Maths 7ème", "7ème de base")

        assert has_course_access(student, course_9, session) is True

        # Changement de niveau
        student.niveau_scolaire = "7ème de base"
        session.commit()

        # Nouveau pack pour 7ème
        pack_7 = _create_pack(session, "Pack 7ème", "7ème de base")
        _create_pack_purchase(session, pack_7, school_id=school.id)

        # Accès au nouveau niveau
        assert has_course_access(student, course_7, session) is True
        assert has_course_access(student, course_9, session) is False


# ============================================================
# SCÉNARIO 4 : Pack expiré → blocage
# ============================================================

class TestScenario4_ExpiredPack:
    """
    Un pack expiré (valid_until dépassé) bloque bien l'accès
    dès le lendemain de l'expiration, pour tous les élèves concernés.
    """

    def test_expired_pack_blocks_access(self, db):
        session, school = db
        student = _create_student(session, school, "expired@test.com", "9ème de base")
        pack = _create_pack(session, "Pack 9ème", "9ème de base")
        _create_pack_purchase(session, pack, school_id=school.id, days_valid=1)

        course = _create_course(session, school, "Maths 9ème", "9ème de base")

        # Accès immédiat
        assert has_course_access(student, course, session) is True

        # Expirer le pack manuellement
        purchase = session.query(PackPurchase).filter(PackPurchase.pack_id == pack.id).first()
        purchase.status = PackPurchaseStatus.EXPIRED.value
        session.commit()

        # Plus d'accès
        assert has_course_access(student, course, session) is False

    def test_expire_pack_purchases_function(self, db):
        session, school = db
        student = _create_student(session, school, "auto_expire@test.com", "9ème de base")
        pack = _create_pack(session, "Pack 9ème", "9ème de base")

        # Créer un achat qui expire dans 0 jours (déjà expiré)
        purchase = _create_pack_purchase(session, pack, school_id=school.id, days_valid=-1)
        assert purchase.status == PackPurchaseStatus.ACTIVE.value

        # La fonction d'expiration doit le passer à expired
        count = expire_pack_purchases(session)
        assert count >= 1

        session.refresh(purchase)
        assert purchase.status == PackPurchaseStatus.EXPIRED.value

        course = _create_course(session, school, "Maths 9ème", "9ème de base")
        assert has_course_access(student, course, session) is False


# ============================================================
# SCÉNARIO 5 : Pack individuel → accès indépendant de l'école
# ============================================================

class TestScenario5_IndividualPackOverridesSchool:
    """
    Un élève individuel qui a acheté son propre pack garde l'accès
    même si son école n'a pas de contrat pack pour ce niveau.
    """

    def test_individual_pack_works_without_school_pack(self, db):
        session, school = db
        student = _create_student(session, school, "indiv@test.com", "9ème de base")
        pack = _create_pack(session, "Pack 9ème", "9ème de base")

        # Achat individuel (pas d'école)
        _create_pack_purchase(session, pack, student_id=student.id)

        course = _create_course(session, school, "Maths 9ème", "9ème de base")

        # Accès via pack individuel
        assert has_course_access(student, course, session) is True

        # Pas de pack école — l'élève a toujours accès
        school_packs = session.query(PackPurchase).filter(
            PackPurchase.school_id == school.id,
            PackPurchase.purchaser_type == PurchaserType.SCHOOL.value,
        ).all()
        assert len(school_packs) == 0

    def test_individual_and_school_pack_coexist(self, db):
        session, school = db
        student = _create_student(session, school, "both@test.com", "9ème de base")

        # Pack individuel
        pack_indiv = _create_pack(session, "Pack 9ème Individuel", "9ème de base")
        _create_pack_purchase(session, pack_indiv, student_id=student.id)

        # Pack école
        pack_school = _create_pack(session, "Pack 9ème École", "9ème de base")
        _create_pack_purchase(session, pack_school, school_id=school.id)

        course = _create_course(session, school, "Maths 9ème", "9ème de base")

        # Les deux donnent accès (cumul)
        assert has_course_access(student, course, session) is True


# ============================================================
# SCÉNARIOS SUPPLÉMENTAIRES
# ============================================================

class TestAdditionalScenarios:

    def test_free_course_always_accessible(self, db):
        session, school = db
        student = _create_student(session, school, "free@test.com", "9ème de base")
        course = _create_course(session, school, "Cours gratuit", "9ème de base", price=0.0)
        assert has_course_access(student, course, session) is True

    def test_wrong_level_no_access(self, db):
        session, school = db
        student = _create_student(session, school, "wrong@test.com", "7ème de base")
        pack = _create_pack(session, "Pack 9ème", "9ème de base")
        _create_pack_purchase(session, pack, school_id=school.id)
        course = _create_course(session, school, "Maths 9ème", "9ème de base")
        assert has_course_access(student, course, session) is False

    def test_matieres_filter(self, db):
        session, school = db
        student = _create_student(session, school, "mat@test.com", "9ème de base")
        pack = _create_pack(session, "Pack Maths", "9ème de base", matieres=["Mathématiques"])
        _create_pack_purchase(session, pack, school_id=school.id)

        course_math = _create_course(session, school, "Maths 9ème", "9ème de base", category="Mathématiques")
        course_sci = _create_course(session, school, "Sciences 9ème", "9ème de base", category="Sciences")

        assert has_course_access(student, course_math, session) is True
        assert has_course_access(student, course_sci, session) is False

    def test_matieres_null_means_all(self, db):
        session, school = db
        student = _create_student(session, school, "all@test.com", "9ème de base")
        pack = _create_pack(session, "Pack Toutes matières", "9ème de base", matieres=None)
        _create_pack_purchase(session, pack, school_id=school.id)

        course_math = _create_course(session, school, "Maths 9ème", "9ème de base", category="Mathématiques")
        course_sci = _create_course(session, school, "Sciences 9ème", "9ème de base", category="Sciences")

        assert has_course_access(student, course_math, session) is True
        assert has_course_access(student, course_sci, session) is True

    def test_no_pack_no_enrollment_no_access(self, db):
        session, school = db
        student = _create_student(session, school, "noaccess@test.com", "9ème de base")
        course = _create_course(session, school, "Cours payant", "9ème de base", price=20.0)
        assert has_course_access(student, course, session) is False

    def test_author_always_has_access(self, db):
        session, school = db
        student = _create_student(session, school, "author@test.com", "9ème de base")
        course = _create_course(session, school, "Son cours", "9ème de base", price=50.0)
        course.author_id = student.id
        session.commit()
        assert has_course_access(student, course, session) is True

    def test_enrollment_always_grants_access(self, db):
        session, school = db
        student = _create_student(session, school, "enrolled@test.com", "9ème de base")
        course = _create_course(session, school, "Cours inscrit", "9ème de base", price=50.0)

        enrollment = CourseEnrollment(
            student_id=student.id,
            course_id=course.id,
            status="active",
        )
        session.add(enrollment)
        session.commit()

        assert has_course_access(student, course, session) is True
