"""
Audit contenu — preuves de correction des 2 failles de modération/bibliothèque.

Fix #1 : publish-version ne s'auto-valide plus (validation préalable obligatoire).
Fix #2 : promote-global crée une COPIE globale indépendante (snapshot-copy-only),
         l'original reste local (est_global=False) ; traçabilité source→copie.
"""
import os
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ENVIRONMENT"] = "development"

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import (
    User, School, Course,
    Parcours, Chapitre, Lecon,
    ElementPedagogique, ElementTexte, ContentPromotion,
)
from tests.conftest import TEST_PASSWORD, TEST_HASH, _login, _auth


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


def _mk_course(db, school, author, title, *, ped_status="draft", active=False, status="draft"):
    c = Course(
        title=title, school_id=school.id, author_id=author.id,
        status=status, pedagogical_status=ped_status,
        is_active_version=active, version_number=1,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


# ============================================================
# FIX #1 — publish-version : verrou de modération
# ============================================================

@pytest.fixture(scope="function")
def courses_db(_base_session):
    db = _base_session
    school = School(name="School C", slug="school-c", subscription_tier="free")
    db.add(school)
    db.commit()
    db.refresh(school)
    teacher = _mk_user(db, school, "cauthor@test.com", "teacher")
    yield db, school, teacher


@pytest.fixture(scope="function")
def client_courses(courses_db):
    return TestClient(app)


class TestFix1PublishVersion:
    def test_unvalidated_course_cannot_publish(self, courses_db, client_courses):
        """AVANT: publish-version posait approved_local tout seul → publication libre.
        APRÈS: 403 tant que la modération n'a pas validé."""
        db, _, teacher = courses_db
        course = _mk_course(db, school=None or courses_db[1], author=teacher, title="Cours Test")
        h = _auth(_login(client_courses, "cauthor@test.com"))

        r = client_courses.post(f"/api/courses/{course.id}/publish-version", headers=h)

        assert r.status_code == 403, f"Bypass toujours possible: {r.status_code} {r.text}"
        assert "modération" in r.json()["detail"]
        db.refresh(course)
        assert course.status == "draft"
        assert course.is_published is False

    def test_approved_course_publishes_without_touching_validation_fields(
        self, courses_db, client_courses
    ):
        """APRÈS validation: publication OK mais pedagogical_status/validated_by restent intacts."""
        db, school, teacher = courses_db
        course = _mk_course(db, school, teacher, "Cours Validé", ped_status="approved_local")
        h = _auth(_login(client_courses, "cauthor@test.com"))

        r = client_courses.post(f"/api/courses/{course.id}/publish-version", headers=h)

        assert r.status_code == 200, f"Publication légitime cassée: {r.status_code} {r.text}"
        data = r.json()
        assert data["is_active_version"] is True
        db.refresh(course)
        assert course.status == "published"
        assert course.is_published is True
        assert course.pedagogical_status == "approved_local"
        assert course.validated_by is None
        assert course.validated_at is None

    def test_new_version_archives_previous(self, courses_db, client_courses):
        """La bascule multi-versions fonctionne toujours (v1 archivée, v2 active)."""
        db, school, teacher = courses_db
        v1 = _mk_course(db, school, teacher, "Cours Multi", ped_status="approved_local",
                        active=True, status="published")
        v2 = _mk_course(db, school, teacher, "Cours Multi (V2)", ped_status="approved_for_b2b",
                        active=False, status="draft")
        v1.is_active_version = True
        v2.is_active_version = False
        db.commit()

        h = _auth(_login(client_courses, "cauthor@test.com"))
        r = client_courses.post(f"/api/courses/{v2.id}/publish-version", headers=h)

        assert r.status_code == 200, f"Switch version cassé: {r.status_code} {r.text}"
        db.refresh(v1)
        db.refresh(v2)
        assert v2.is_active_version is True and v2.status == "published"
        assert v1.is_active_version is False and v1.status == "archived"


# ============================================================
# FIX #2 — promote-global : snapshot-copy-only
# ============================================================

@pytest.fixture(scope="function")
def elements_db(_base_session):
    db = _base_session
    school = School(name="School E", slug="school-e", subscription_tier="free")
    db.add(school)
    db.commit()
    db.refresh(school)

    teacher = _mk_user(db, school, "eauthor@test.com", "teacher")
    lead = _mk_user(db, school, "elead@test.com", "pedagogical_lead")

    parcours = Parcours(titre="Parcours E", matiere="Mathematiques",
                        niveau_scolaire="6eme", auteur_id=teacher.id)
    db.add(parcours)
    db.commit()
    db.refresh(parcours)
    chapitre = Chapitre(parcours_id=parcours.id, titre="Ch. E", ordre=0)
    db.add(chapitre)
    db.commit()
    db.refresh(chapitre)
    lecon = Lecon(chapitre_id=chapitre.id, titre="Leçon E", ordre=0, duree_minutes=5)
    db.add(lecon)
    db.commit()
    db.refresh(lecon)

    def mk_element(title, statut):
        el = ElementPedagogique(
            type="texte", titre=title, description="Desc",
            lecon_id=lecon.id, auteur_id=teacher.id,
            statut=statut, difficulte="moyen",
            metadonnees={"origine": "test"},
        )
        db.add(el)
        db.commit()
        db.refresh(el)
        db.add(ElementTexte(element_id=el.id, corps=f"Corps de {title}"))
        db.commit()
        return el

    published = mk_element("Cours Original", "publie")
    draft = mk_element("Brouillon Local", "brouillon")

    yield db, school, teacher, lead, published, draft


@pytest.fixture(scope="function")
def client_elements(elements_db):
    return TestClient(app)


class TestFix2SnapshotCopyOnly:
    def test_promote_creates_independent_copy_and_keeps_original_local(
        self, elements_db, client_elements
    ):
        """AVANT: promote-global basculait est_global=True SUR l'original (référence live).
        APRÈS: copie globale indépendante; original intact; traçabilité source→copie."""
        db, _, _, lead, original, _ = elements_db
        h = _auth(_login(client_elements, "elead@test.com"))

        r = client_elements.post(
            f"/api/pathway/elements/{original.id}/promote-global", headers=h
        )

        assert r.status_code == 200, f"Promotion cassée: {r.status_code} {r.text}"
        copy_id = r.json()["id"]
        assert copy_id != original.id

        db.refresh(original)
        assert original.est_global is False
        assert original.statut == "publie"

        copy = db.query(ElementPedagogique).get(copy_id)
        assert copy.est_global is True
        assert copy.statut == "publie"
        assert copy.titre == "Cours Original"
        assert copy.lecon_id is None

        src_texts = db.query(ElementTexte).filter(ElementTexte.element_id == original.id).all()
        copy_texts = db.query(ElementTexte).filter(ElementTexte.element_id == copy_id).all()
        assert len(src_texts) == 1 and len(copy_texts) == 1
        assert copy_texts[0].corps == src_texts[0].corps
        assert copy_texts[0].id != src_texts[0].id

        promo = db.query(ContentPromotion).filter(
            ContentPromotion.element_source_id == original.id
        ).first()
        assert promo is not None
        assert promo.element_promoted_id == copy_id

    def test_bibliotheque_lists_copy_not_original(self, elements_db, client_elements):
        db, _, _, lead, original, _ = elements_db
        h = _auth(_login(client_elements, "elead@test.com"))
        r = client_elements.post(
            f"/api/pathway/elements/{original.id}/promote-global", headers=h
        )
        copy_id = r.json()["id"]

        resp = client_elements.get("/api/pathway/search?q=Cours Original", headers=_auth(_login(client_elements, "elead@test.com")))
        ids = [item["id"] for item in resp.json()["items"]]
        assert copy_id in ids
        assert original.id not in ids

    def test_editing_original_after_promotion_leaves_global_copy_untouched(
        self, elements_db, client_elements
    ):
        """Le cœur du snapshot-copy-only: l'auteur modifie son élément local,
        la bibliothèque globale reste stable."""
        db, _, teacher, lead, original, _ = elements_db
        h_lead = _auth(_login(client_elements, "elead@test.com"))
        r = client_elements.post(
            f"/api/pathway/elements/{original.id}/promote-global", headers=h_lead
        )
        copy_id = r.json()["id"]

        original.titre = "Retitré côté auteur"
        db.commit()

        resp = client_elements.get("/api/pathway/search", headers=_auth(_login(client_elements, "elead@test.com")))
        titles = {item["id"]: item["titre"] for item in resp.json()["items"]}
        assert titles[copy_id] == "Cours Original"

    def test_draft_element_still_rejected(self, elements_db, client_elements):
        db, _, _, lead, _, draft = elements_db
        h = _auth(_login(client_elements, "elead@test.com"))
        r = client_elements.post(
            f"/api/pathway/elements/{draft.id}/promote-global", headers=h
        )
        assert r.status_code == 400

    def test_plain_teacher_cannot_promote(self, elements_db, client_elements):
        db, _, teacher, _, original, _ = elements_db
        h = _auth(_login(client_elements, "eauthor@test.com"))
        r = client_elements.post(
            f"/api/pathway/elements/{original.id}/promote-global", headers=h
        )
        assert r.status_code == 403
