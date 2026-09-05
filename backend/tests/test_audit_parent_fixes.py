"""
Audit Parent — preuves de correction M1 / M2 / Écart#1 / M3 / Écart#2 / M9.

M1      : POST /auth/register accepte role ∈ {student, teacher, parent}
          (teacher routé vers le pipeline d'approbation existant).
M2      : POST /api/parents/me/enfants/lier exige le code d'invitation de
          l'élève — l'email seul ne suffit plus (IDOR fermé). Tout nouvel
          élève reçoit un code à la création.
Écart#1 : POST /api/abonnements/packs/{id}/purchase — un parent peut acheter
          pour un enfant lié via eleve_id (débit wallet parent, bénéficiaire enfant).
M3      : lier auto-crée CompteFamille + FamilleEnfant (rang + remise 0/20/25%),
          delier re-rank les rangs restants.
Écart#2 : GET /api/abonnements/mes-abonnements?eleve_id=... renvoie les
          abonnements de l'enfant lié (et non ceux du parent).
M9      : POST /api/parents/me/messages — recipient_id explicite vérifié ou
          broadcast à TOUS les enseignants/admins de l'école (plus de .first()).
"""
import os
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ENVIRONMENT"] = "development"

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import (
    User, School, ParentEnfant, PackDefinition, Abonnement,
    CompteFamille, FamilleEnfant, Message,
)
from tests.conftest import TEST_HASH, TEST_PASSWORD, _login, _auth


def _mk_user(db, school, email, role):
    """Crée un utilisateur actif directement en DB (pour teachers/admins)."""
    u = User(
        email=email, hashed_password=TEST_HASH, full_name=email.split("@")[0],
        role=role, is_active=True, is_approved=True,
        school_id=school.id,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture(scope="function")
def pf_db(_base_session):
    db = _base_session
    school = School(name="School R", slug="school-r", subscription_tier="free")
    db.add(school)
    db.commit()
    db.refresh(school)
    yield db, school


@pytest.fixture(scope="function")
def client_pf(pf_db):
    return TestClient(app)


def _register(client, email, role, school_name="School R"):
    return client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "Password123!",
            "full_name": email.split("@")[0],
            "school_name": school_name,
            "role": role,
        },
    )


# ============================================================
# M1 — création publique des comptes student / teacher / parent
# ============================================================

class TestM1RegisterRoles:
    def test_register_parent_creates_active_parent(self, pf_db, client_pf):
        r = _register(client_pf, "parent1@test.com", "parent")
        assert r.status_code == 200, f"Register parent cassé: {r.status_code} {r.text}"
        assert "access_token" in r.json()

        from app.db import Base
        # vérifie en base via la session du fixture
        db = pf_db[0]
        u = db.query(User).filter(User.email == "parent1@test.com").first()
        assert u is not None and u.role == "parent" and u.is_active

    def test_register_default_role_is_student(self, pf_db, client_pf):
        """Sans champ role => comportement historique préservé."""
        r = client_pf.post(
            "/auth/register",
            json={
                "email": "legacy@test.com",
                "password": "Password123!",
                "full_name": "Legacy",
                "school_name": "School R",
            },
        )
        assert r.status_code == 200
        db = pf_db[0]
        u = db.query(User).filter(User.email == "legacy@test.com").first()
        assert u.role == "student"

    def test_register_rejects_privileged_roles(self, pf_db, client_pf):
        for bad in ("admin_school", "super_admin", "pedagogical_admin"):
            r = _register(client_pf, f"{bad}@test.com", bad)
            assert r.status_code == 422, f"{bad} ne doit pas être créable publiquement"

    def test_register_teacher_routed_to_approval_pipeline(self, pf_db, client_pf):
        """teacher via /register est refusé (400) et orienté vers le pipeline
        d'approbation /auth/teacher-register — aucun compte teacher actif créé."""
        r = _register(client_pf, "teach1@test.com", "teacher")
        assert r.status_code == 400
        assert "teacher-register" in r.json()["detail"]
        db = pf_db[0]
        # aucun compte enseignant actif créé directement via /register
        assert db.query(User).filter(
            User.email == "teach1@test.com", User.role == "teacher"
        ).first() is None
        # le pipeline d'approbation dédié reste fonctionnel
        tr = client_pf.post(
            "/auth/teacher-register",
            json={
                "email": "teach1@test.com",
                "password": "Password123!",
                "full_name": "Teach One",
                "school_name": "School R",
            },
        )
        assert tr.status_code == 200
        from app.models import TeacherRegistration, TeacherRegistrationStatus
        reg = db.query(TeacherRegistration).filter(
            TeacherRegistration.email == "teach1@test.com"
        ).first()
        assert reg is not None and reg.status == TeacherRegistrationStatus.PENDING


# ============================================================
# M2 — code d'invitation obligatoire pour lier un enfant
# ============================================================

class TestM2InvitationCode:
    def test_new_student_receives_invitation_code(self, pf_db, client_pf):
        r = _register(client_pf, "eleve1@test.com", "student")
        assert r.status_code == 200
        db = pf_db[0]
        eleve = db.query(User).filter(User.email == "eleve1@test.com").first()
        assert eleve.invitation_code, "Aucun code généré à la création"
        assert len(eleve.invitation_code) == 6

    def test_my_invitation_code_endpoint(self, pf_db, client_pf):
        r = _register(client_pf, "eleve2@test.com", "student")
        tok = r.json()["access_token"]
        me = client_pf.get("/auth/my-invitation-code", headers=_auth(tok))
        assert me.status_code == 200
        code = me.json()["invitation_code"]
        assert code and len(code) == 6

    def test_lier_without_code_is_422(self, pf_db, client_pf):
        _register(client_pf, "eleve3@test.com", "student")
        pr = _register(client_pf, "parent3@test.com", "parent")
        h = _auth(pr.json()["access_token"])
        r = client_pf.post(
            "/api/parents/me/enfants/lier",
            headers=h,
            json={"email_eleve": "eleve3@test.com"},
        )
        assert r.status_code == 422  # invitation_code devenu requis

    def test_lier_with_wrong_code_is_403(self, pf_db, client_pf):
        """Le cœur du fix IDOR: bon email + mauvais code => 403, aucun lien créé."""
        _register(client_pf, "eleve4@test.com", "student")
        pr = _register(client_pf, "parent4@test.com", "parent")
        h = _auth(pr.json()["access_token"])
        r = client_pf.post(
            "/api/parents/me/enfants/lier",
            headers=h,
            json={"email_eleve": "eleve4@test.com", "invitation_code": "ZZZZ99"},
        )
        assert r.status_code == 403
        db = pf_db[0]
        eleve = db.query(User).filter(User.email == "eleve4@test.com").first()
        assert db.query(ParentEnfant).filter(
            ParentEnfant.eleve_id == eleve.id
        ).count() == 0

    def test_lier_with_correct_code_succeeds(self, pf_db, client_pf):
        sr = _register(client_pf, "eleve5@test.com", "student")
        stok = sr.json()["access_token"]
        code = client_pf.get("/auth/my-invitation-code", headers=_auth(stok)).json()["invitation_code"]

        pr = _register(client_pf, "parent5@test.com", "parent")
        h = _auth(pr.json()["access_token"])
        r = client_pf.post(
            "/api/parents/me/enfants/lier",
            headers=h,
            json={"email_eleve": "eleve5@test.com", "invitation_code": code.lower()},
        )
        assert r.status_code == 200, r.text
        assert r.json()["eleve_id"] > 0


# ============================================================
# Écart#1 — achat pack parent -> enfant (eleve_id)
# ============================================================

class TestParentPackPurchase:
    def test_parent_purchase_for_linked_child(self, pf_db, client_pf):
        db, school = pf_db
        sr = _register(client_pf, "child6@test.com", "student")
        stok = sr.json()["access_token"]
        code = client_pf.get("/auth/my-invitation-code", headers=_auth(stok)).json()["invitation_code"]
        pr = _register(client_pf, "parent6@test.com", "parent")

        ptok = pr.json()["access_token"]
        ph = _auth(ptok)
        link = client_pf.post(
            "/api/parents/me/enfants/lier", headers=ph,
            json={"email_eleve": "child6@test.com", "invitation_code": code},
        )
        assert link.status_code == 200, link.text

        pack = PackDefinition(
            nom="Pack Test", tier="basique", niveau_scolaire="6ème",
            prix_tnd=50.0, est_actif=True,
        )
        db.add(pack)
        db.commit()
        db.refresh(pack)

        child = db.query(User).filter(User.email == "child6@test.com").first()

        # Le parent doit avoir un solde DT réel (pool DT_PURCHASED) — les 100 DT
        # d'accueil sont en pool TRIAL et ne comptent pas pour l'achat (wallet.py:115).
        from decimal import Decimal
        from app.services.wallet import credit_dt
        parent = db.query(User).filter(User.email == "parent6@test.com").first()
        credit_dt(db, parent.id, Decimal("100"), source="test", reason="recharge")

        r = client_pf.post(
            f"/api/abonnements/packs/{pack.id}/purchase",
            headers=ph,
            json={"matieres": [], "eleve_id": child.id},
        )
        assert r.status_code in (200, 201), f"Achat parent->enfant cassé: {r.status_code} {r.text}"

        abo = db.query(Abonnement).filter(Abonnement.user_id == child.id).first()
        assert abo is not None, "L'abonnement doit être porté par l'enfant, pas le parent"

    def test_purchase_without_eleve_id_still_400(self, pf_db, client_pf):
        """Garde-fou backend intact: parent sans eleve_id => 400."""
        pr = _register(client_pf, "parent7@test.com", "parent")
        ph = _auth(pr.json()["access_token"])

        db, school = pf_db
        pack = PackDefinition(
            nom="Pack T7", tier="basique", niveau_scolaire="6ème",
            prix_tnd=50.0, est_actif=True,
        )
        db.add(pack)
        db.commit()
        db.refresh(pack)

        r = client_pf.post(f"/api/abonnements/packs/{pack.id}/purchase", headers=ph, json={})
        assert r.status_code == 400


# ============================================================
# M3 — FamilleEnfant auto-créé par lier_eleve (rang + remise)
# ============================================================

class TestM3FamilleAutoCreate:
    def test_lier_creates_famille_enfant_first_child_0pct(self, pf_db, client_pf):
        """AVANT: lier_eleve créait ParentEnfant mais PAS FamilleEnfant → 0% remise.
        APRÈS: lier crée automatiquement FamilleEnfant rang=1, remise=0%."""
        sr = _register(client_pf, "m3e1@test.com", "student")
        stok = sr.json()["access_token"]
        code = client_pf.get("/auth/my-invitation-code", headers=_auth(stok)).json()["invitation_code"]

        pr = _register(client_pf, "m3p1@test.com", "parent")
        ph = _auth(pr.json()["access_token"])
        r = client_pf.post(
            "/api/parents/me/enfants/lier", headers=ph,
            json={"email_eleve": "m3e1@test.com", "invitation_code": code},
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert "famille" in data, "La réponse doit contenir les infos famille (rang/remise)"
        assert data["famille"]["rang"] == 1
        assert data["famille"]["remise_pct"] == 0.0

        db = pf_db[0]
        parent = db.query(User).filter(User.email == "m3p1@test.com").first()
        cf = db.query(CompteFamille).filter(CompteFamille.parent_id == parent.id).first()
        assert cf is not None, "CompteFamille doit être auto-créé"
        fe = db.query(FamilleEnfant).filter(FamilleEnfant.compte_famille_id == cf.id).first()
        assert fe is not None
        assert fe.rang == 1 and fe.remise_pct == 0.0

    def test_lier_second_and_third_children_get_discount(self, pf_db, client_pf):
        """2ème enfant → rang=2/20%, 3ème → rang=3/25%."""
        db, school = pf_db
        pr = _register(client_pf, "m3p2@test.com", "parent")
        ph = _auth(pr.json()["access_token"])

        rangs_remissions = []
        for i, email in enumerate(["m3e2a@test.com", "m3e2b@test.com", "m3e2c@test.com"], 1):
            sr = _register(client_pf, email, "student")
            stok = sr.json()["access_token"]
            code = client_pf.get("/auth/my-invitation-code", headers=_auth(stok)).json()["invitation_code"]
            r = client_pf.post(
                "/api/parents/me/enfants/lier", headers=ph,
                json={"email_eleve": email, "invitation_code": code},
            )
            assert r.status_code == 200, r.text
            fam = r.json().get("famille", {})
            rangs_remissions.append((fam.get("rang"), fam.get("remise_pct")))

        assert rangs_remissions == [(1, 0.0), (2, 20.0), (3, 25.0)]

    def test_delier_reranks_remaining_children(self, pf_db, client_pf):
        """AVANT: delier supprimait FamilleEnfant sans re-rank.
        APRÈS: delier re-rank les enfants restants avec remises recalculées."""
        pr = _register(client_pf, "m3p3@test.com", "parent")
        ph = _auth(pr.json()["access_token"])
        ids = []
        for email in ["m3e3a@test.com", "m3e3b@test.com", "m3e3c@test.com"]:
            sr = _register(client_pf, email, "student")
            stok = sr.json()["access_token"]
            code = client_pf.get("/auth/my-invitation-code", headers=_auth(stok)).json()["invitation_code"]
            r = client_pf.post(
                "/api/parents/me/enfants/lier", headers=ph,
                json={"email_eleve": email, "invitation_code": code},
            )
            assert r.status_code == 200
            ids.append(r.json()["eleve_id"])

        # Avant delier: rangs = [1, 2, 3]
        # Delier le 1er → l'ex-2e devient rang=1/0%, l'ex-3e devient rang=2/20%
        r = client_pf.delete(f"/api/parents/me/enfants/{ids[0]}/delier", headers=ph)
        assert r.status_code == 200

        db = pf_db[0]
        parent = db.query(User).filter(User.email == "m3p3@test.com").first()
        cf = db.query(CompteFamille).filter(CompteFamille.parent_id == parent.id).first()
        remaining = db.query(FamilleEnfant).filter(
            FamilleEnfant.compte_famille_id == cf.id
        ).order_by(FamilleEnfant.rang).all()
        assert len(remaining) == 2
        assert (remaining[0].rang, remaining[0].remise_pct) == (1, 0.0)
        assert (remaining[1].rang, remaining[1].remise_pct) == (2, 20.0)

    def test_lier_no_duplicate_when_other_parent_already_linked(self, pf_db, client_pf):
        """Si un autre parent a déjà un FamilleEnfant pour cet eleve_id
        (contrainte unique), lier ne crée pas de doublon (pas d'IntegrityError)."""
        sr = _register(client_pf, "m3e4@test.com", "student")
        stok = sr.json()["access_token"]
        code = client_pf.get("/auth/my-invitation-code", headers=_auth(stok)).json()["invitation_code"]

        # Premier parent
        pr1 = _register(client_pf, "m3p4a@test.com", "parent")
        r1 = client_pf.post(
            "/api/parents/me/enfants/lier", headers=_auth(pr1.json()["access_token"]),
            json={"email_eleve": "m3e4@test.com", "invitation_code": code},
        )
        assert r1.status_code == 200
        # Lien ParentEnfant du parent 1 existe
        db = pf_db[0]
        p1 = db.query(User).filter(User.email == "m3p4a@test.com").first()
        assert db.query(ParentEnfant).filter(
            ParentEnfant.parent_user_id == p1.id,
        ).first() is not None

        # Deuxième parent même école — la liaison ParentEnfant fonctionne,
        # mais FamilleEnfant n'est PAS dupliqué (unique(eleve_id)).
        pr2 = _register(client_pf, "m3p4b@test.com", "parent")
        r2 = client_pf.post(
            "/api/parents/me/enfants/lier", headers=_auth(pr2.json()["access_token"]),
            json={"email_eleve": "m3e4@test.com", "invitation_code": code},
        )
        assert r2.status_code == 200, r2.text
        # Un seul FamilleEnfant pour cet eleve_id
        fe_count = db.query(FamilleEnfant).filter(
            FamilleEnfant.eleve_id == db.query(User).filter(User.email == "m3e4@test.com").first().id
        ).count()
        assert fe_count == 1


# ============================================================
# Écart#2 — GET /mes-abonnements?eleve_id= renvoie les abos
# de l'ENFANT (pas ceux du parent toujours vides)
# ============================================================

class TestEcart2MesAbonnements:
    def test_parent_sees_child_abonnements(self, pf_db, client_pf):
        db, school = pf_db
        sr = _register(client_pf, "ec2e1@test.com", "student")
        stok = sr.json()["access_token"]
        code = client_pf.get("/auth/my-invitation-code", headers=_auth(stok)).json()["invitation_code"]
        child = db.query(User).filter(User.email == "ec2e1@test.com").first()

        pr = _register(client_pf, "ec2p1@test.com", "parent")
        ph = _auth(pr.json()["access_token"])
        parent = db.query(User).filter(User.email == "ec2p1@test.com").first()
        client_pf.post(
            "/api/parents/me/enfants/lier", headers=ph,
            json={"email_eleve": "ec2e1@test.com", "invitation_code": code},
        )

        # Créer un pack actif sur l'ENFANT (pas le parent)
        from datetime import datetime, timedelta
        pack = PackDefinition(nom="Pack Écart2", tier="basique", niveau_scolaire="6ème",
                              prix_tnd=40.0, est_actif=True)
        db.add(pack)
        db.commit()
        db.refresh(pack)
        now = datetime.now(timezone.utc)
        abo = Abonnement(user_id=child.id, pack_id=pack.id, statut="actif",
                         debut=now, fin=now + timedelta(days=30))
        db.add(abo)
        db.commit()

        # Sans eleve_id → le parent n'a pas d'abonnements → 0 items
        r0 = client_pf.get("/api/abonnements/mes-abonnements", headers=ph)
        assert r0.status_code == 200
        assert r0.json()["total"] == 0

        # Avec eleve_id de l'enfant → 1 abonnement
        r1 = client_pf.get(f"/api/abonnements/mes-abonnements?eleve_id={child.id}", headers=ph)
        assert r1.status_code == 200
        assert r1.json()["total"] == 1
        assert r1.json()["items"][0]["pack"]["nom"] == "Pack Écart2"

    def test_parent_rejected_for_unlinked_child(self, pf_db, client_pf):
        db, school = pf_db
        sr = _register(client_pf, "ec2e2@test.com", "student")
        child = db.query(User).filter(User.email == "ec2e2@test.com").first()

        pr = _register(client_pf, "ec2p2@test.com", "parent")
        ph = _auth(pr.json()["access_token"])

        # Enfant non lié → 403
        r = client_pf.get(f"/api/abonnements/mes-abonnements?eleve_id={child.id}", headers=ph)
        assert r.status_code == 403


# ============================================================
# M9 — Messagerie: recipient_id ou broadcast (plus de .first())
# ============================================================

class TestM9Messaging:
    def test_broadcast_to_all_teachers(self, pf_db, client_pf):
        """Sans recipient_id → broadcast à TOUS les enseignants actifs de l'école."""
        db, school = pf_db
        t1 = _mk_user(db, school, "m9t1@test.com", "teacher")
        t2 = _mk_user(db, school, "m9t2@test.com", "teacher")

        pr = _register(client_pf, "m9p1@test.com", "parent")
        ph = _auth(pr.json()["access_token"])
        sr = _register(client_pf, "m9e1@test.com", "student")
        stok = sr.json()["access_token"]
        code = client_pf.get("/auth/my-invitation-code", headers=_auth(stok)).json()["invitation_code"]
        client_pf.post(
            "/api/parents/me/enfants/lier", headers=ph,
            json={"email_eleve": "m9e1@test.com", "invitation_code": code},
        )

        r = client_pf.post(
            "/api/parents/me/messages", headers=ph,
            json={"recipient_type": "teacher", "subject": "Sujet broadcast", "body": "Bonjour"},
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["sent"] == 2, f"Attendu 2 destinataires (broadcast), reçu {data['sent']}"
        assert data["id"] is not None

        msgs = db.query(Message).filter(
            Message.sender_id == db.query(User).filter(User.email == "m9p1@test.com").first().id,
            Message.subject == "Sujet broadcast",
        ).all()
        assert len(msgs) == 2
        receivers = {m.receiver_id for m in msgs}
        assert t1.id in receivers and t2.id in receivers

    def test_explicit_recipient_same_school(self, pf_db, client_pf):
        """Avec recipient_id → envoi ciblé, vérifié (même école + rôle enseignant)."""
        db, school = pf_db
        teacher = _mk_user(db, school, "m9t3@test.com", "teacher")

        pr = _register(client_pf, "m9p2@test.com", "parent")
        ph = _auth(pr.json()["access_token"])
        sr = _register(client_pf, "m9e2@test.com", "student")
        stok = sr.json()["access_token"]
        code = client_pf.get("/auth/my-invitation-code", headers=_auth(stok)).json()["invitation_code"]
        client_pf.post(
            "/api/parents/me/enfants/lier", headers=ph,
            json={"email_eleve": "m9e2@test.com", "invitation_code": code},
        )

        r = client_pf.post(
            "/api/parents/me/messages", headers=ph,
            json={"recipient_type": "teacher", "subject": "Ciblé", "body": "Bonjour prof",
                  "recipient_id": teacher.id},
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["sent"] == 1

    def test_cross_school_recipient_rejected(self, pf_db, client_pf):
        """Destinataire d'une autre école → 403."""
        db, school = pf_db
        school2 = School(name="School Other", slug="school-other", subscription_tier="free")
        db.add(school2)
        db.commit()
        db.refresh(school2)
        other_teacher = _mk_user(db, school2, "m9t4@test.com", "teacher")

        pr = _register(client_pf, "m9p3@test.com", "parent")
        ph = _auth(pr.json()["access_token"])
        sr = _register(client_pf, "m9e3@test.com", "student")
        stok = sr.json()["access_token"]
        code = client_pf.get("/auth/my-invitation-code", headers=_auth(stok)).json()["invitation_code"]
        client_pf.post(
            "/api/parents/me/enfants/lier", headers=ph,
            json={"email_eleve": "m9e3@test.com", "invitation_code": code},
        )

        r = client_pf.post(
            "/api/parents/me/messages", headers=ph,
            json={"recipient_type": "teacher", "subject": "Fail", "body": "Test",
                  "recipient_id": other_teacher.id},
        )
        assert r.status_code == 403, f"Cross-school doit être refusé: {r.status_code} {r.text}"
