"""
Tests preuve-based : Corrections sécurité #1, #2, #3, #8.

#1  POST /auth/register ne crée plus jamais d'école (lookup-only).
#2  school.is_active == False -> login ET get_current_user refusés (403),
    sauf platform-admins (super_admin/pedagogical_admin).
#3  GET /api/pathway/notions/{id}/contenu : gate ABAC sur couverture
    packs/abonnements de l'élève (402 sinon).
(#8 est frontend : vérifié par npm run build + revue de code App.tsx.)
"""
import os
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ENVIRONMENT"] = "development"

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from app.db import Base  # noqa: F401
from app.main import app
from app.models import (
    User, School,
    NiveauEtude, Matiere, ChapterPathway, Notion, ContenuNotion,
    NiveauAssimilation, TypeContenu,
    StudyPack, PackPurchase, PackPurchaseStatus, PurchaserType, PackStatus,
    Abonnement, PackDefinition,
)

from app.core.security import get_password_hash
from tests.conftest import TEST_PASSWORD


STRONG_PASSWORD = "Str0ng!Passw0rd"


@pytest.fixture(scope="function")
def client(sec_db):
    """TestClient branché via l'override de dépendance de _base_session."""
    return TestClient(app)


@pytest.fixture(scope="function")
def sec_db(_base_session):
    """École + élève + admin plateforme + arborescence pédagogique."""
    db = _base_session

    school = School(name="Ecole Sec", slug="ecole-sec")
    db.add(school)
    db.commit()
    db.refresh(school)

    student = User(
        email="secstudent@test.com", hashed_password=get_password_hash(TEST_PASSWORD),
        full_name="Sec Student", role="student", is_active=True, is_approved=True,
        school_id=school.id, niveau_scolaire="9eme de base",
    )
    db.add(student)

    super_admin = User(
        email="secadmin@test.com", hashed_password=get_password_hash(TEST_PASSWORD),
        full_name="Sec Admin", role="super_admin", is_active=True, is_approved=True,
        school_id=school.id,
    )
    db.add(super_admin)
    db.commit()
    db.refresh(student)
    db.refresh(super_admin)

    # Arborescence : niveau NON couvert par défaut par l'élève
    niveau = NiveauEtude(nom="9ème de base", ordre=9)
    db.add(niveau)
    db.commit()
    db.refresh(niveau)

    matiere = Matiere(niveau_etude_id=niveau.id, nom="Mathématiques")
    db.add(matiere)
    db.commit()
    db.refresh(matiere)

    chapitre = ChapterPathway(matiere_id=matiere.id, nom="Chapitre Sec", ordre=1)
    db.add(chapitre)
    db.commit()
    db.refresh(chapitre)

    notion = Notion(chapitre_id=chapitre.id, nom="Notion Sec", ordre=1)
    db.add(notion)
    db.commit()
    db.refresh(notion)

    contenu = ContenuNotion(
        notion_id=notion.id,
        niveau_assimilation=NiveauAssimilation.STANDARD.value,
        type_ressource=TypeContenu.FICHE.value,
        contenu="Contenu de test",
        statut_validation_pedagogique="valide",
    )
    db.add(contenu)
    db.commit()

    yield {
        "db": db, "school": school, "student": student,
        "super_admin": super_admin, "niveau": niveau, "notion": notion,
    }


def _login(client, email, password):
    return client.post("/auth/login", data={"username": email, "password": password})


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


# -------------------------------------------------------------------
# #1 — /register ne crée plus d'école
# -------------------------------------------------------------------
class TestRegisterNoSchoolCreation:
    def test_unknown_school_rejected(self, client, _base_session):
        before = _base_session.query(School).count()
        resp = client.post("/auth/register", json={
            "email": "ghost@test.com",
            "password": STRONG_PASSWORD,
            "full_name": "Ghost Student",
            "school_name": "Ecole Fantome Inexistante",
            "niveau_scolaire": "9eme de base",
        })
        assert resp.status_code in (400, 404), resp.text
        assert _base_session.query(School).count() == before

    def test_inactive_school_rejected_at_register(self, client, sec_db):
        school = sec_db["school"]
        school.is_active = False
        sec_db["db"].commit()

        resp = client.post("/auth/register", json={
            "email": "joiner@test.com",
            "password": STRONG_PASSWORD,
            "full_name": "Joiner",
            "school_name": "Ecole Sec",
        })
        assert resp.status_code in (400, 403), resp.text

    def test_register_school_creates_pending_school(self, client, _base_session):
        resp = client.post("/auth/register-school", json={
            "school_name": "Nouvelle Ecole",
            "email": "director@nouvelle.tn",
            "password": STRONG_PASSWORD,
            "full_name": "Director",
        })
        assert resp.status_code == 200, resp.text
        school = _base_session.query(School).filter(School.name == "Nouvelle Ecole").first()
        assert school is not None
        assert school.is_active is False
        assert school.pending_validation is True


# -------------------------------------------------------------------
# #2 — school.is_active enforced au login et dans get_current_user
# -------------------------------------------------------------------
class TestInactiveSchoolBlocked:
    def test_login_blocked_when_school_inactive(self, client, sec_db):
        school, student = sec_db["school"], sec_db["student"]
        school.is_active = False
        sec_db["db"].commit()

        resp = _login(client, student.email, TEST_PASSWORD)
        assert resp.status_code == 403, resp.text
        assert "école est désactivée" in resp.json()["detail"]

    def test_existing_token_rejected_when_school_deactivated(self, client, sec_db):
        student = sec_db["student"]
        login = _login(client, student.email, TEST_PASSWORD)
        assert login.status_code == 200
        token = login.json()["access_token"]

        school = sec_db["school"]
        school.is_active = False
        sec_db["db"].commit()

        me = client.get("/auth/me", headers=_auth_headers(token))
        assert me.status_code == 403, me.text

    def test_platform_admin_not_blocked_by_own_school(self, client, sec_db):
        admin = sec_db["super_admin"]
        login = _login(client, admin.email, TEST_PASSWORD)
        assert login.status_code == 200
        token = login.json()["access_token"]

        school = sec_db["school"]
        school.is_active = False
        sec_db["db"].commit()

        me = client.get("/auth/me", headers=_auth_headers(token))
        assert me.status_code == 200, me.text

    def test_login_ok_again_after_reactivation(self, client, sec_db):
        school, student = sec_db["school"], sec_db["student"]
        school.is_active = False
        sec_db["db"].commit()
        assert _login(client, student.email, TEST_PASSWORD).status_code == 403

        school.is_active = True
        sec_db["db"].commit()
        assert _login(client, student.email, TEST_PASSWORD).status_code == 200


# -------------------------------------------------------------------
# #3 — Gate ABAC sur le contenu adaptatif
# -------------------------------------------------------------------
class TestAdaptiveContentGate:
    def _endpoint(self, notion_id, eleve_id):
        return f"/api/pathway/notions/{notion_id}/contenu?eleve_id={eleve_id}"

    def _student_token(self, client, sec_db):
        login = _login(client, sec_db["student"].email, TEST_PASSWORD)
        assert login.status_code == 200
        return login.json()["access_token"]

    def test_blocked_without_any_coverage(self, client, sec_db):
        token = self._student_token(client, sec_db)
        resp = client.get(
            self._endpoint(sec_db["notion"].id, sec_db["student"].id),
            headers=_auth_headers(token),
        )
        assert resp.status_code == 402, resp.text
        body = resp.json()["detail"]
        assert "message" in body and "required_pack" in body

    def test_allowed_via_school_pack_purchase(self, client, sec_db):
        db = sec_db["db"]
        admin_user = db.query(User).filter(User.role == "super_admin").first()
        pack = StudyPack(
            name="Pack Sec 9eme", niveau_scolaire="9eme de base",
            matieres=["Mathématiques"],
            price=50.0, validity_duration_days=365,
            status=PackStatus.PUBLISHED.value,
            created_by=admin_user.id, school_id=sec_db["school"].id,
        )
        db.add(pack)
        db.commit()
        db.refresh(pack)

        now = datetime.now(timezone.utc)
        db.add(PackPurchase(
            pack_id=pack.id, purchaser_type=PurchaserType.SCHOOL.value,
            school_id=sec_db["school"].id,
            valid_from=now, valid_until=now + timedelta(days=365),
            status=PackPurchaseStatus.ACTIVE.value,
            amount_paid=pack.price, currency=pack.currency,
        ))
        db.commit()

        token = self._student_token(client, sec_db)
        resp = client.get(
            self._endpoint(sec_db["notion"].id, sec_db["student"].id),
            headers=_auth_headers(token),
        )
        assert resp.status_code != 402, resp.text
        assert resp.status_code == 200, resp.text

    def test_allowed_via_abonnement_pack_definition(self, client, sec_db):
        db = sec_db["db"]
        pack_def = PackDefinition(
            nom="Basique 9eme", tier="basique", niveau_scolaire="9eme de base",
            prix_tnd=20.0, est_actif=True,
        )
        db.add(pack_def)
        db.commit()
        db.refresh(pack_def)

        now = datetime.now(timezone.utc)
        db.add(Abonnement(
            user_id=sec_db["student"].id, pack_id=pack_def.id,
            statut="actif", debut=now, fin=now + timedelta(days=180),
        ))
        db.commit()

        token = self._student_token(client, sec_db)
        resp = client.get(
            self._endpoint(sec_db["notion"].id, sec_db["student"].id),
            headers=_auth_headers(token),
        )
        assert resp.status_code != 402, resp.text
        assert resp.status_code == 200, resp.text

    def test_expired_abonnement_does_not_cover(self, client, sec_db):
        db = sec_db["db"]
        pack_def = PackDefinition(
            nom="Basique 9eme Expire", tier="basique", niveau_scolaire="9eme de base",
            prix_tnd=20.0, est_actif=True,
        )
        db.add(pack_def)
        db.commit()
        db.refresh(pack_def)

        now = datetime.now(timezone.utc)
        db.add(Abonnement(
            user_id=sec_db["student"].id, pack_id=pack_def.id,
            statut="actif", debut=now - timedelta(days=360),
            fin=now - timedelta(days=5),
        ))
        db.commit()

        token = self._student_token(client, sec_db)
        resp = client.get(
            self._endpoint(sec_db["notion"].id, sec_db["student"].id),
            headers=_auth_headers(token),
        )
        assert resp.status_code == 402, resp.text

    def test_cross_student_access_still_403(self, client, sec_db):
        db = sec_db["db"]
        other = User(
            email="otherstudent@test.com",
            hashed_password=get_password_hash(TEST_PASSWORD),
            full_name="Other Student", role="student", is_active=True,
            is_approved=True, school_id=sec_db["school"].id,
        )
        db.add(other)
        db.commit()
        db.refresh(other)

        token = self._student_token(client, sec_db)
        resp = client.get(
            self._endpoint(sec_db["notion"].id, other.id),
            headers=_auth_headers(token),
        )
        assert resp.status_code == 403, resp.text
