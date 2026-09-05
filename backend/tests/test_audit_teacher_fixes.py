"""
Audit Teacher module — preuves de correction des 4 failles critiques.

Fix #1 : IDOR cours        — _can_access_course : un enseignant n'accède qu'à SES cours.
Fix #2 : IDOR enfants      — chapitres/leçons/paragraphes vérifient l'ownership du Parcours parent.
Fix #3 : escalade privilège— PUT /api/users/{id} : self-only enseignant ; is_active/rôle réservés admins.
Fix #4 : cross-tenant      — POST /api/pathway/scores scoping par classes enseignées / école.
"""
import os
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ENVIRONMENT"] = "development"

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import (
    User, School, Course, Parcours, Chapitre, Lecon, Paragraphe,
    TeacherClass, StudentEnrollment,
    NiveauEtude, Matiere, ChapterPathway,
)
from app.routers.admin_courses import _can_access_course

from tests.conftest import TEST_PASSWORD, TEST_HASH, _login, _auth


def _mk_user(db, school, email, role, **kw):
    u = User(
        email=email, hashed_password=TEST_HASH, full_name=email.split("@")[0],
        role=role, is_active=True, is_approved=True, school_id=school.id, **kw,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


# ============================================================
# FIX #1 — _can_access_course (test unitaire pur)
# ============================================================

class TestFix1CourseAccess:
    def _course(self, author_id, school_id):
        return Course(author_id=author_id, school_id=school_id)

    def test_teacher_non_author_same_school_denied(self):
        """AVANT: fall-through school_id accordait True. APRÈS: False."""
        teacher = User(id=99, role="teacher", school_id=1)
        assert _can_access_course(teacher, self._course(author_id=7, school_id=1)) is False

    def test_teacher_author_allowed(self):
        teacher = User(id=7, role="teacher", school_id=1)
        assert _can_access_course(teacher, self._course(author_id=7, school_id=1)) is True

    def test_admin_school_same_school_allowed(self):
        admin = User(id=10, role="admin_school", school_id=1)
        assert _can_access_course(admin, self._course(author_id=7, school_id=1)) is True

    def test_admin_school_other_school_denied(self):
        admin = User(id=10, role="admin_school", school_id=2)
        assert _can_access_course(admin, self._course(author_id=7, school_id=1)) is False

    def test_platform_roles_global(self):
        sa = User(id=1, role="super_admin", school_id=None)
        pa = User(id=2, role="pedagogical_admin", school_id=None)
        c = self._course(author_id=7, school_id=1)
        assert _can_access_course(sa, c) is True
        assert _can_access_course(pa, c) is True


# ============================================================
# FIX #2 — ownership des enfants de parcours
# ============================================================

@pytest.fixture(scope="function")
def parcours_db(_base_session):
    db = _base_session
    school = School(name="School A", slug="school-a", subscription_tier="free")
    db.add(school)
    db.commit()
    db.refresh(school)

    teacher_a = _mk_user(db, school, "owner@test.com", "teacher")
    teacher_b = _mk_user(db, school, "intruder@test.com", "teacher")
    admin = _mk_user(db, school, "sch_admin@test.com", "admin_school")

    parcours = Parcours(
        titre="Parcours A", matiere="Mathematiques",
        niveau_scolaire="6eme", difficulte="moyen",
        auteur_id=teacher_a.id,
    )
    db.add(parcours)
    db.commit()
    db.refresh(parcours)

    chapitre = Chapitre(parcours_id=parcours.id, titre="Chapitre 1", ordre=0)
    db.add(chapitre)
    db.commit()
    db.refresh(chapitre)

    lecon = Lecon(chapitre_id=chapitre.id, titre="Lecon 1", ordre=0, duree_minutes=10)
    db.add(lecon)
    db.commit()
    db.refresh(lecon)

    paragraphe = Paragraphe(lecon_id=lecon.id, contenu="Texte initial", type="texte", ordre=0)
    db.add(paragraphe)
    db.commit()
    db.refresh(paragraphe)

    yield db, school, teacher_a, teacher_b, admin, parcours, chapitre, lecon, paragraphe


@pytest.fixture(scope="function")
def client2(parcours_db):
    return TestClient(app)


class TestFix2ParcoursChildren:
    def test_intruder_cannot_delete_chapitre(self, parcours_db, client2):
        db, _, _, intruder, _, _, chapitre, *_ = parcours_db
        h = _auth(_login(client2, "intruder@test.com"))
        r = client2.delete(f"/api/pathway/chapitres/{chapitre.id}", headers=h)
        assert r.status_code == 403, f"IDOR chapitre encore présent: {r.status_code} {r.text}"

    def test_intruder_cannot_delete_lecon(self, parcours_db, client2):
        db, _, _, intruder, _, _, _, lecon, _ = parcours_db
        h = _auth(_login(client2, "intruder@test.com"))
        r = client2.delete(f"/api/pathway/lecons/{lecon.id}", headers=h)
        assert r.status_code == 403, f"IDOR leçon encore présent: {r.status_code} {r.text}"

    def test_intruder_cannot_delete_paragraphe(self, parcours_db, client2):
        db, _, _, intruder, _, _, _, _, paragraphe = parcours_db
        h = _auth(_login(client2, "intruder@test.com"))
        r = client2.delete(f"/api/pathway/paragraphes/{paragraphe.id}", headers=h)
        assert r.status_code == 403, f"IDOR paragraphe encore présent: {r.status_code} {r.text}"

    def test_intruder_cannot_create_chapitre_in_foreign_parcours(self, parcours_db, client2):
        db, _, _, intruder, _, parcours, *_ = parcours_db
        h = _auth(_login(client2, "intruder@test.com"))
        r = client2.post(
            f"/api/pathway/parcours/{parcours.id}/chapitres",
            json={"titre": "Chapitre pirate"}, headers=h,
        )
        assert r.status_code == 403, f"Création croisée encore possible: {r.status_code} {r.text}"

    def test_owner_still_can_modify(self, parcours_db, client2):
        db, _, owner, _, _, _, chapitre, _, paragraphe = parcours_db
        h = _auth(_login(client2, "owner@test.com"))
        r = client2.patch(f"/api/pathway/chapitres/{chapitre.id}", json={"titre": "Modifié"}, headers=h)
        assert r.status_code == 200, f"Le propriétaire ne doit pas être bloqué: {r.status_code} {r.text}"
        r2 = client2.delete(f"/api/pathway/paragraphes/{paragraphe.id}", headers=h)
        assert r2.status_code == 200

    def test_school_admin_can_modify_foreign_content(self, parcours_db, client2):
        db, _, _, _, admin, _, _, lecon, _ = parcours_db
        h = _auth(_login(client2, "sch_admin@test.com"))
        r = client2.patch(f"/api/pathway/lecons/{lecon.id}", json={"titre": "Admin edit"}, headers=h)
        assert r.status_code == 200, f"L'admin école doit passer: {r.status_code} {r.text}"


# ============================================================
# FIX #3 — PUT /api/users/{id}
# ============================================================

@pytest.fixture(scope="function")
def users_db(_base_session):
    db = _base_session
    school = School(name="School U", slug="school-u", subscription_tier="free")
    db.add(school)
    db.commit()
    db.refresh(school)

    admin = _mk_user(db, school, "uadmin@test.com", "admin_school")
    t_a = _mk_user(db, school, "ta@test.com", "teacher")
    t_b = _mk_user(db, school, "tb@test.com", "teacher")
    student = _mk_user(db, school, "ustud@test.com", "student")

    yield db, school, admin, t_a, t_b, student


@pytest.fixture(scope="function")
def client3(users_db):
    return TestClient(app)


class TestFix3UserUpdate:
    def test_teacher_cannot_modify_colleague(self, users_db, client3):
        db, _, _, t_a, t_b, _ = users_db
        h = _auth(_login(client3, "tb@test.com"))
        r = client3.put(f"/api/users/{t_a.id}", json={"full_name": "Pirate"}, headers=h)
        assert r.status_code == 403, f"Escalade encore possible: {r.status_code} {r.text}"
        db.refresh(t_a)
        assert t_a.full_name != "Pirate"

    def test_teacher_can_edit_own_full_name(self, users_db, client3):
        db, _, _, _, t_b, _ = users_db
        h = _auth(_login(client3, "tb@test.com"))
        r = client3.put(f"/api/users/{t_b.id}", json={"full_name": "Nouveau Nom"}, headers=h)
        assert r.status_code == 200, f"Self-edit légitime cassé: {r.status_code} {r.text}"
        assert r.json()["full_name"] == "Nouveau Nom"

    def test_teacher_cannot_deactivate_self_or_others(self, users_db, client3):
        db, _, _, t_a, t_b, _ = users_db
        h = _auth(_login(client3, "tb@test.com"))
        r_self = client3.put(f"/api/users/{t_b.id}", json={"is_active": False}, headers=h)
        assert r_self.status_code == 403
        r_other = client3.put(f"/api/users/{t_a.id}", json={"is_active": False}, headers=h)
        assert r_other.status_code == 403

    def test_school_admin_can_deactivate_teacher(self, users_db, client3):
        db, _, admin, _, t_b, _ = users_db
        h = _auth(_login(client3, "uadmin@test.com"))
        r = client3.put(f"/api/users/{t_b.id}", json={"is_active": False}, headers=h)
        assert r.status_code == 200
        db.refresh(t_b)
        assert t_b.is_active is False

    def test_role_change_reserved_to_admins_and_no_super_promo(self, users_db, client3):
        db, _, admin, _, _, student = users_db
        h_teach = _auth(_login(client3, "tb@test.com"))
        r1 = client3.put(f"/api/users/{student.id}", json={"role": "admin_school"}, headers=h_teach)
        assert r1.status_code == 403

        h_adm = _auth(_login(client3, "uadmin@test.com"))
        r2 = client3.put(f"/api/users/{student.id}", json={"role": "super_admin"}, headers=h_adm)
        assert r2.status_code == 403


# ============================================================
# FIX #4 — POST /api/pathway/scores scoping
# ============================================================

@pytest.fixture(scope="function")
def scores_db(_base_session):
    db = _base_session
    school_a = School(name="School SA", slug="school-sa", subscription_tier="free")
    school_b = School(name="School SB", slug="school-sb", subscription_tier="free")
    db.add_all([school_a, school_b])
    db.commit()
    db.refresh(school_a)
    db.refresh(school_b)

    teacher = _mk_user(db, school_a, "steacher@test.com", "teacher")
    admin_a = _mk_user(db, school_a, "sadmina@test.com", "admin_school")
    admin_b = _mk_user(db, school_b, "sadminb@test.com", "admin_school")
    student_in = _mk_user(db, school_a, "stin@test.com", "student")
    student_out = _mk_user(db, school_b, "stout@test.com", "student")

    tc = TeacherClass(name="Classe T", teacher_id=teacher.id, school_id=school_a.id)
    db.add(tc)
    db.commit()
    db.refresh(tc)
    db.add(StudentEnrollment(student_id=student_in.id, class_id=tc.id))
    db.commit()

    niveau = NiveauEtude(nom="8eme", ordre=1)
    db.add(niveau)
    db.commit()
    db.refresh(niveau)
    matiere = Matiere(niveau_etude_id=niveau.id, nom="Maths")
    db.add(matiere)
    db.commit()
    db.refresh(matiere)
    chapter = ChapterPathway(matiere_id=matiere.id, nom="Ch. Scores", ordre=1)
    db.add(chapter)
    db.commit()
    db.refresh(chapter)

    yield db, school_a, school_b, teacher, admin_a, admin_b, student_in, student_out, chapter


@pytest.fixture(scope="function")
def client4(scores_db):
    return TestClient(app)


class TestFix4ScoreScoping:
    def test_teacher_cannot_score_student_of_another_school(self, scores_db, client4):
        _, _, _, _, _, _, _, student_out, chapter = scores_db
        h = _auth(_login(client4, "steacher@test.com"))
        r = client4.post("/api/pathway/scores", json={
            "eleve_id": student_out.id, "chapitre_id": chapter.id, "score": 60.0,
        }, headers=h)
        assert r.status_code == 403, f"Cross-tenant score encore possible: {r.status_code} {r.text}"

    def test_teacher_can_score_own_class_student(self, scores_db, client4):
        _, _, _, _, _, _, student_in, _, chapter = scores_db
        h = _auth(_login(client4, "steacher@test.com"))
        r = client4.post("/api/pathway/scores", json={
            "eleve_id": student_in.id, "chapitre_id": chapter.id, "score": 88.0,
        }, headers=h)
        assert r.status_code == 200, f"Score propre classe cassé: {r.status_code} {r.text}"

    def test_admin_school_cross_school_denied(self, scores_db, client4):
        _, _, _, _, admin_a, _, _, student_out, chapter = scores_db
        h = _auth(_login(client4, "sadmina@test.com"))
        r = client4.post("/api/pathway/scores", json={
            "eleve_id": student_out.id, "chapitre_id": chapter.id, "score": 70.0,
        }, headers=h)
        assert r.status_code == 403, f"Admin cross-school score encore possible: {r.status_code} {r.text}"

    def test_admin_school_same_school_allowed(self, scores_db, client4):
        _, _, _, _, _, admin_b, _, student_out, chapter = scores_db
        h = _auth(_login(client4, "sadminb@test.com"))
        r = client4.post("/api/pathway/scores", json={
            "eleve_id": student_out.id, "chapitre_id": chapter.id, "score": 75.0,
        }, headers=h)
        assert r.status_code == 200, f"Admin même école bloqué à tort: {r.status_code} {r.text}"
