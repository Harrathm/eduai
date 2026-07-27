"""
Tests proof-based : Parcours Pédagogique Adaptatif
6 tests couvrant les règles métier du prompt.
"""
import os
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ENVIRONMENT"] = "development"

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app.models import (
    User, School, StudyPack, PackPurchase, PackPurchaseStatus, PackStatus,
    PurchaserType,
    NiveauEtude, Matiere, ChapterPathway, Notion, ContenuNotion,
    ProfilAssimilationEleve, HistoriqueScoreEleve, NotificationReorientation,
    NiveauAssimilation, TypeContenu, SourceChangement, StatutValidationProfil,
    ActionReorientation,
)
from app.core.security import get_password_hash
from app.services.adaptive_pathway import (
    statut_publication, niveau_effectif, evaluer_reorientation,
    contenu_a_servir, acces_effectif,
)

TEST_PASSWORD = "password123"
TEST_HASH = get_password_hash(TEST_PASSWORD)


@pytest.fixture(scope="function")
def test_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    db = TestingSessionLocal()

    # --- School + Users ---
    school = School(name="Ecole Test", slug="ecole-test", subscription_tier="free")
    db.add(school)
    db.commit()
    db.refresh(school)

    admin = User(
        email="admin@test.com", hashed_password=TEST_HASH,
        full_name="Admin", role="super_admin", is_active=True, is_approved=True,
    )
    db.add(admin)

    teacher = User(
        email="teacher@test.com", hashed_password=TEST_HASH,
        full_name="Teacher", role="teacher", is_active=True, is_approved=True,
        school_id=school.id,
    )
    db.add(teacher)

    student = User(
        email="student@test.com", hashed_password=TEST_HASH,
        full_name="Student", role="student", is_active=True, is_approved=True,
        school_id=school.id, niveau_scolaire="9eme de base",
        dt_balance=200.0,
    )
    db.add(student)
    db.commit()
    db.refresh(admin)
    db.refresh(teacher)
    db.refresh(student)

    # --- Arborescence pédagogique ---
    niveau = NiveauEtude(nom="9ème de base", ordre=9)
    db.add(niveau)
    db.commit()
    db.refresh(niveau)

    matiere = Matiere(niveau_etude_id=niveau.id, nom="Mathématiques")
    db.add(matiere)
    db.commit()
    db.refresh(matiere)

    chapitre = ChapterPathway(matiere_id=matiere.id, nom="Chapitre 1 - Fractions", ordre=1)
    db.add(chapitre)
    db.commit()
    db.refresh(chapitre)

    notion = Notion(chapitre_id=chapitre.id, nom="Addition de fractions", ordre=1)
    db.add(notion)
    db.commit()
    db.refresh(notion)

    # --- Pack pour accès ---
    pack = StudyPack(
        name="Pack 9eme", niveau_scolaire="9eme de base",
        matieres=["Mathématiques"],
        price=50.0, validity_duration_days=365,
        status=PackStatus.PUBLISHED.value,
        created_by=admin.id, school_id=school.id,
    )
    db.add(pack)
    db.commit()
    db.refresh(pack)

    now = datetime.now(timezone.utc)
    purchase = PackPurchase(
        pack_id=pack.id, purchaser_type=PurchaserType.SCHOOL.value,
        school_id=school.id,
        valid_from=now, valid_until=now + timedelta(days=365),
        status=PackPurchaseStatus.ACTIVE.value,
        amount_paid=pack.price, currency=pack.currency,
    )
    db.add(purchase)
    db.commit()

    yield db, school, admin, teacher, student, niveau, matiere, chapitre, notion, pack, purchase

    app.dependency_overrides.clear()
    db.close()


@pytest.fixture(scope="function")
def client(test_db):
    return TestClient(app)


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ============================================================
# TEST 1: Notion avec seulement STANDARD → statut = brouillon
# ============================================================
class TestStatutPublicationBrouillon:

    def test_standard_seul_brouillon(self, test_db):
        """Notion avec seulement Standard → statut = brouillon."""
        db, school, admin, teacher, student, niveau, matiere, chapitre, notion, pack, purchase = test_db

        contenu_std = ContenuNotion(
            notion_id=notion.id,
            niveau_assimilation=NiveauAssimilation.STANDARD.value,
            type_ressource=TypeContenu.FICHE.value,
            contenu="Contenu standard fractions",
            enseignant_id=teacher.id,
            statut_pedagogique="a",
        )
        db.add(contenu_std)
        db.commit()

        result = statut_publication(notion.id, db)
        assert result["statut"] == "brouillon", f"Attendu brouillon, recu {result['statut']}"
        assert "STANDARD" not in result["niveaux_manquants"], "STANDARD ne devrait pas manquer"
        assert "REMEDIATION" in result["niveaux_manquants"], "REMEDIATION devrait manquer"
        assert "AVANCE" in result["niveaux_manquants"], "AVANCE devrait manquer"


# ============================================================
# TEST 2: Standard + Avancé → publiable, manquants = [REMEDIATION]
# ============================================================
class TestStatutPublicationPubliable:

    def test_standard_plus_avance_publiable(self, test_db):
        """Notion avec Standard + Avancé → statut = publiable, niveaux_manquants = [REMEDIATION]."""
        db, school, admin, teacher, student, niveau, matiere, chapitre, notion, pack, purchase = test_db

        contenu_std = ContenuNotion(
            notion_id=notion.id,
            niveau_assimilation=NiveauAssimilation.STANDARD.value,
            type_ressource=TypeContenu.FICHE.value,
            contenu="Standard fractions",
            enseignant_id=teacher.id,
            statut_pedagogique="a",
        )
        contenu_av = ContenuNotion(
            notion_id=notion.id,
            niveau_assimilation=NiveauAssimilation.AVANCE.value,
            type_ressource=TypeContenu.VIDEO.value,
            contenu="Avancé fractions",
            enseignant_id=teacher.id,
            statut_pedagogique="a",
        )
        db.add_all([contenu_std, contenu_av])
        db.commit()

        result = statut_publication(notion.id, db)
        assert result["statut"] == "publiable", f"Attendu publiable, recu {result['statut']}"
        assert result["niveaux_manquants"] == ["REMEDIATION"], (
            f"Attendu ['REMEDIATION'], recu {result['niveaux_manquants']}"
        )


# ============================================================
# TEST 3: Élève sans profil → niveau_effectif retombe sur défaut matière
# ============================================================
class TestNiveauEffectifDefaut:

    def test_sans_profil_retombe_defaut(self, test_db):
        """Élève sans profil chapitre → niveau_effectif = défaut matière (STANDARD)."""
        db, school, admin, teacher, student, niveau, matiere, chapitre, notion, pack, purchase = test_db

        result = niveau_effectif(student.id, chapitre.id, db)
        assert result["niveau_effectif"] == NiveauAssimilation.STANDARD.value, (
            f"Attendu STANDARD, recu {result['niveau_effectif']}"
        )
        assert result["source"] == "defaut_matiere", (
            f"Attendu source='defaut_matiere', recu {result['source']}"
        )


# ============================================================
# TEST 4: Réorientation auto s'applique immédiatement + génère notification
# ============================================================
class TestReorientationAuto:

    def test_reorientation_auto_appliquee(self, test_db):
        """Scores faibles → réorientation vers REMEDIATION immédiate + notification enseignant."""
        db, school, admin, teacher, student, niveau, matiere, chapitre, notion, pack, purchase = test_db

        # Record 5 scores of 20 → moyenne = 20 → REMEDIATION
        for _ in range(5):
            score_row = HistoriqueScoreEleve(
                eleve_id=student.id,
                chapitre_id=chapitre.id,
                score=20.0,
            )
            db.add(score_row)
        db.commit()

        result = evaluer_reorientation(
            student.id, chapitre.id, db,
            enseignant_id=teacher.id,
            config_n=5,
            config_seuils={"remediation": 0, "standard": 40, "avance": 75},
        )

        assert result is not None, "Une réorientation devrait se produire"
        assert result["nouveau_niveau"] == NiveauAssimilation.REMEDIATION.value
        assert result["ancien_niveau"] == NiveauAssimilation.STANDARD.value
        assert result["notification_envoyee"] is True

        # Check profile was created
        profil = db.query(ProfilAssimilationEleve).filter(
            ProfilAssimilationEleve.eleve_id == student.id,
            ProfilAssimilationEleve.chapitre_id == chapitre.id,
        ).first()
        assert profil is not None
        assert profil.statut_validation == StatutValidationProfil.AUTO_APPLIQUE.value
        assert profil.source_changement == SourceChangement.AJUSTEMENT_AUTO.value

        # Check notification
        notif = db.query(NotificationReorientation).filter(
            NotificationReorientation.profil_assimilation_id == profil.id,
        ).first()
        assert notif is not None, "Notification devrait exister"
        assert notif.enseignant_id == teacher.id
        assert notif.action_prise == ActionReorientation.AUCUNE.value


# ============================================================
# TEST 5: Pack Sur-Mesure : profil progresse au-delà du scope_achat
# ============================================================
class TestAccesEffectifDynamique:

    def test_acces_refleete_nouveau_niveau(self, test_db):
        """Après une réorientation vers AVANCE, acces_effectif retourne AVANCE (pas le scope figé)."""
        db, school, admin, teacher, student, niveau, matiere, chapitre, notion, pack, purchase = test_db

        # Simulate: student has active school pack for 9eme/Mathématiques
        # Manually set profile to AVANCE
        profil = ProfilAssimilationEleve(
            eleve_id=student.id,
            chapitre_id=chapitre.id,
            niveau_assimilation_courant=NiveauAssimilation.AVANCE.value,
            source_changement=SourceChangement.OVERRIDE_ENSEIGNANT.value,
            statut_validation=StatutValidationProfil.CONFIRME_ENSEIGNANT.value,
        )
        db.add(profil)
        db.commit()

        result = acces_effectif(student.id, matiere.id, chapitre.id, db)

        assert result["acces"] is True, "L'accès devrait être accordé via le pack"
        assert result["niveau_effectif"] == NiveauAssimilation.AVANCE.value, (
            f"Le niveau effectif devrait être AVANCE (profil dynamique), recu {result['niveau_effectif']}"
        )


# ============================================================
# TEST 6: Contenu manquant → fallback vers Standard
# ============================================================
class TestContenuFallback:

    def test_fallback_vers_standard(self, test_db):
        """Si le contenu au niveau assigné manque, on fallback sur Standard."""
        db, school, admin, teacher, student, niveau, matiere, chapitre, notion, pack, purchase = test_db

        # Student is at REMEDIATION level (via profile)
        profil = ProfilAssimilationEleve(
            eleve_id=student.id,
            chapitre_id=chapitre.id,
            niveau_assimilation_courant=NiveauAssimilation.REMEDIATION.value,
            source_changement=SourceChangement.AJUSTEMENT_AUTO.value,
            statut_validation=StatutValidationProfil.AUTO_APPLIQUE.value,
        )
        db.add(profil)

        # Only STANDARD content exists (no REMEDIATION content)
        contenu_std = ContenuNotion(
            notion_id=notion.id,
            niveau_assimilation=NiveauAssimilation.STANDARD.value,
            type_ressource=TypeContenu.FICHE.value,
            contenu="Contenu standard fallback",
            enseignant_id=teacher.id,
            statut_pedagogique="a",
        )
        db.add(contenu_std)
        db.commit()

        result = contenu_a_servir(notion.id, student.id, db)

        assert result is not None, "Un contenu devrait être servi"
        assert result["fallback"] is True, "Le fallback devrait être activé"
        assert result["niveau_servi"] == NiveauAssimilation.STANDARD.value, (
            f"Le contenu servi devrait être STANDARD, recu {result['niveau_servi']}"
        )
