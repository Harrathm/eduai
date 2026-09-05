"""
Audit P2 + H — preuves de correction.

Fix P2  : Course.author_id passe de ON DELETE CASCADE -> SET NULL.
          Supprimer un enseignant préserve ses cours/éléments (propriété institutionnelle).
Fix H   : POST /api/teacher/classes/{class_id}/message — envoi de messages
          à tous les élèves actifs d'une classe ou à un élève ciblé.
"""
import os
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ENVIRONMENT"] = "development"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event

from app.main import app
from app.db import Base
from app.models import (
    User, School, Course, TeacherClass, StudentEnrollment, Message,
    ElementPedagogique,
)
from tests.conftest import TEST_HASH, _login, _auth


def _mk_user(db, school, email, role):
    u = User(
        email=email, hashed_password=TEST_HASH, full_name=email.split("@")[0],
        role=role, is_active=True, is_approved=True,
        **({"school_id": school.id} if school else {}),
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


# ============================================================
# FIX P2 — CASCADE -> SET NULL (test au niveau contrainte DB)
# ============================================================

def _fk_engine():
    """Engine SQLite dédiée avec foreign_keys=ON pour que les ON DELETE
    du modèle soient réellement appliqués (SQLite les ignore sinon)."""
    engine = create_engine("sqlite://")

    @event.listens_for(engine, "connect")
    def _enable_fk(dbapi_conn, _rec):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    Base.metadata.create_all(engine)
    return engine


class TestFixP2CascadeSetNull:
    def test_deleting_teacher_preserves_courses_and_elements(self):
        """AVANT: DELETE user -> courses/éléments supprimés en cascade (perte de contenu).
        APRÈS: DELETE user -> contenu préservé, author_id/auteur_id = NULL."""
        from sqlalchemy.orm import sessionmaker

        engine = _fk_engine()
        Session = sessionmaker(bind=engine)
        db = Session()

        school = School(name="School FK", slug="school-fk", subscription_tier="free")
        db.add(school)
        db.commit()
        db.refresh(school)

        teacher = User(
            email="fkteacher@test.com", hashed_password=TEST_HASH,
            full_name="FK Teacher", role="teacher", is_active=True,
            is_approved=True, school_id=school.id,
        )
        db.add(teacher)
        db.commit()
        db.refresh(teacher)

        course = Course(
            title="Cours Préservé", school_id=school.id, author_id=teacher.id,
            status="draft",
        )
        element = ElementPedagogique(
            type="texte", titre="Élément Préservé",
            auteur_id=teacher.id, statut="publie", est_global=True,
        )
        db.add_all([course, element])
        db.commit()

        course_id, element_id = course.id, element.id

        # Suppression de l'enseignant — c'est ici que la contrainte DB décide
        db.delete(teacher)
        db.commit()

        surviving_course = db.query(Course).filter(Course.id == course_id).first()
        assert surviving_course is not None, \
            "Course supprimé en cascade: perte de données toujours présente !"
        assert surviving_course.author_id is None

        surviving_element = db.query(ElementPedagogique).filter(
            ElementPedagogique.id == element_id
        ).first()
        assert surviving_element is not None, \
            "Element supprimé en cascade: perte de données toujours présente !"
        assert surviving_element.auteur_id is None

        db.close()


# ============================================================
# FIX H — Messagerie enseignant (envoi)
# ============================================================

@pytest.fixture(scope="function")
def messaging_db(_base_session):
    db = _base_session
    school = School(name="School M", slug="school-m", subscription_tier="free")
    db.add(school)
    db.commit()
    db.refresh(school)

    teacher = _mk_user(db, school, "mteacher@test.com", "teacher")
    other_teacher = _mk_user(db, school, "mother@test.com", "teacher")

    tc = TeacherClass(
        teacher_id=teacher.id, school_id=school.id,
        name="Classe Msg", code="MSG01",
    )
    db.add(tc)
    db.commit()
    db.refresh(tc)

    empty_tc = TeacherClass(
        teacher_id=teacher.id, school_id=school.id,
        name="Classe Vide", code="MSG02",
    )
    db.add(empty_tc)
    db.commit()
    db.refresh(empty_tc)

    students = []
    for i in range(3):
        s = _mk_user(db, school, f"mstudent{i}@test.com", "student")
        students.append(s)
        db.add(StudentEnrollment(class_id=tc.id, student_id=s.id))
    db.commit()

    yield db, school, teacher, other_teacher, tc, empty_tc, students


@pytest.fixture(scope="function")
def client_messaging(messaging_db):
    return TestClient(app)


class TestFixHMessaging:
    def test_send_to_whole_class(self, messaging_db, client_messaging):
        """L'enseignant envoie à toute la classe: un Message par élève actif."""
        db, _, teacher, _, tc, _, students = messaging_db
        h = _auth(_login(client_messaging, "mteacher@test.com"))

        r = client_messaging.post(
            f"/api/teacher/classes/{tc.id}/message",
            headers=h,
            json={"subject": "Contrôle vendredi", "body": "Révisez le chapitre 3."},
        )

        assert r.status_code == 200, f"Envoi cassé: {r.status_code} {r.text}"
        data = r.json()
        assert data["sent"] == len(students)
        assert data["targeted_only"] is False

        msgs = db.query(Message).filter(Message.subject == "Contrôle vendredi").all()
        assert len(msgs) == len(students)
        receivers = {m.receiver_id for m in msgs}
        assert receivers == {s.id for s in students}
        assert all(m.sender_id == teacher.id for m in msgs)
        assert all(m.body == "Révisez le chapitre 3." for m in msgs)
        assert all(not m.is_read for m in msgs)

    def test_send_to_targeted_student(self, messaging_db, client_messaging):
        db, _, teacher, _, tc, _, students = messaging_db
        h = _auth(_login(client_messaging, "mteacher@test.com"))
        target = students[1]

        r = client_messaging.post(
            f"/api/teacher/classes/{tc.id}/message",
            headers=h,
            json={"subject": "Rattrapage", "body": "RDV lundi 14h.", "student_id": target.id},
        )

        assert r.status_code == 200, f"Ciblage cassé: {r.status_code} {r.text}"
        data = r.json()
        assert data["sent"] == 1
        assert data["targeted_only"] is True

        msg = db.query(Message).filter(Message.subject == "Rattrapage").one()
        assert msg.sender_id == teacher.id
        assert msg.receiver_id == target.id

    def test_cannot_message_class_of_another_teacher(self, messaging_db, client_messaging):
        """_own_class_or_403: la classe d'un autre enseignant est inaccessible."""
        db, _, _, other_teacher, tc, _, _ = messaging_db
        h = _auth(_login(client_messaging, "mother@test.com"))

        r = client_messaging.post(
            f"/api/teacher/classes/{tc.id}/message",
            headers=h,
            json={"subject": "X", "body": "Y"},
        )

        assert r.status_code == 404

    def test_cannot_message_unenrolled_student(self, messaging_db, client_messaging):
        """Un student_id hors de la classe (même école) est refusé."""
        db, school, teacher, _, tc, empty_tc, _ = messaging_db
        outsider = _mk_user(db, school, "outsider@test.com", "student")
        h = _auth(_login(client_messaging, "mteacher@test.com"))

        r = client_messaging.post(
            f"/api/teacher/classes/{tc.id}/message",
            headers=h,
            json={"subject": "X", "body": "Y", "student_id": outsider.id},
        )

        assert r.status_code == 404
        assert db.query(Message).filter(Message.subject == "X").count() == 0

    def test_empty_class_rejected(self, messaging_db, client_messaging):
        db, _, _, _, _, empty_tc, _ = messaging_db
        h = _auth(_login(client_messaging, "mteacher@test.com"))

        r = client_messaging.post(
            f"/api/teacher/classes/{empty_tc.id}/message",
            headers=h,
            json={"subject": "X", "body": "Y"},
        )

        assert r.status_code == 400
        assert "No active students" in r.json()["detail"]

    def test_blank_subject_or_body_rejected(self, messaging_db, client_messaging):
        db, _, teacher, _, tc, _, _ = messaging_db
        h = _auth(_login(client_messaging, "mteacher@test.com"))

        r1 = client_messaging.post(
            f"/api/teacher/classes/{tc.id}/message",
            headers=h, json={"subject": "", "body": "Y"},
        )
        r2 = client_messaging.post(
            f"/api/teacher/classes/{tc.id}/message",
            headers=h, json={"subject": "S", "body": ""},
        )
        assert r1.status_code == 422
        assert r2.status_code == 422
