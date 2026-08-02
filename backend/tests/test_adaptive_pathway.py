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

from tests.conftest import TEST_PASSWORD, TEST_HASH, _auth


@pytest.fixture(scope="function")
def test_db(_base_session):
    """Custom test DB with arborescence pédagogique, pack, and purchase."""
    db = _base_session

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


@pytest.fixture(scope="function")
def client(test_db):
    return TestClient(app)


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


# ============================================================
# TESTS RBAC PÉDAGOGIQUE (Scénarios 7-10)
# ============================================================

class TestRBACPedagogique:
    """Tests proof-based pour la RBAC pédagogique par spécialité."""

    def setup_method(self):
        from app.db import Base as TestBase
        self.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        TestBase.metadata.create_all(bind=self.engine)
        self.TestSession = sessionmaker(bind=self.engine)

    def _db(self):
        return self.TestSession()

    def _seed(self):
        db = self._db()
        from app.core.security import get_password_hash
        from app.models import (
            SpecialitePedagogique, SpecialitePedagogiqueMatiere, ResponsablePedagogique,
            NiveauEtude, Matiere, ChapterPathway, Notion, ContenuNotion, User,
        )

        # School
        school = School(name="Test", slug="test", school_type="REAL", invite_code="T")
        db.add(school)
        db.flush()

        # Niveaux
        niv1 = NiveauEtude(nom="7eme", ordre=1)
        niv2 = NiveauEtude(nom="Bac", ordre=5)
        db.add_all([niv1, niv2])
        db.flush()

        # Matieres: Maths 7eme, Eveil 7eme, Maths Bac
        mat_maths_7eme = Matiere(niveau_etude_id=niv1.id, nom="Maths 7eme")
        mat_eveil = Matiere(niveau_etude_id=niv1.id, nom="Eveil Scientifique")
        mat_maths_bac = Matiere(niveau_etude_id=niv2.id, nom="Maths Bac")
        db.add_all([mat_maths_7eme, mat_eveil, mat_maths_bac])
        db.flush()

        # Users
        resp1_user = User(email="resp1@test", full_name="Resp1", school_id=school.id,
                          hashed_password=get_password_hash("pw"), role="pedagogical_admin", is_active=True)
        resp2_user = User(email="resp2@test", full_name="Resp2", school_id=school.id,
                          hashed_password=get_password_hash("pw"), role="pedagogical_admin", is_active=True)
        teacher_user = User(email="teacher@test", full_name="Teacher", school_id=school.id,
                            hashed_password=get_password_hash("pw"), role="teacher", is_active=True)
        student_user = User(email="student@test", full_name="Student", school_id=school.id,
                            hashed_password=get_password_hash("pw"), role="student", is_active=True)
        db.add_all([resp1_user, resp2_user, teacher_user, student_user])
        db.flush()

        # Specialite "Sciences" = Maths 7eme + Eveil + Maths Bac
        spec_sciences = SpecialitePedagogique(ecole_id=school.id, nom="Sciences", cycle_scolaire="1er_cycle")
        db.add(spec_sciences)
        db.flush()
        db.add_all([
            SpecialitePedagogiqueMatiere(specialite_id=spec_sciences.id, matiere_id=mat_maths_7eme.id),
            SpecialitePedagogiqueMatiere(specialite_id=spec_sciences.id, matiere_id=mat_eveil.id),
            SpecialitePedagogiqueMatiere(specialite_id=spec_sciences.id, matiere_id=mat_maths_bac.id),
        ])

        # Responsable 1: Sciences, scope = [7eme]
        resp1 = ResponsablePedagogique(user_id=resp1_user.id, specialite_id=spec_sciences.id)
        db.add(resp1)
        db.flush()
        resp1.niveaux_etude_scope.append(niv1)

        # Responsable 2: Sciences, scope = [Bac] (disjoint)
        resp2 = ResponsablePedagogique(user_id=resp2_user.id, specialite_id=spec_sciences.id)
        db.add(resp2)
        db.flush()
        resp2.niveaux_etude_scope.append(niv2)

        # Chapters + Notions
        ch_maths_7eme = ChapterPathway(matiere_id=mat_maths_7eme.id, nom="Chap Maths 7eme", ordre=1)
        ch_eveil = ChapterPathway(matiere_id=mat_eveil.id, nom="Chap Eveil", ordre=1)
        ch_maths_bac = ChapterPathway(matiere_id=mat_maths_bac.id, nom="Chap Maths Bac", ordre=1)
        db.add_all([ch_maths_7eme, ch_eveil, ch_maths_bac])
        db.flush()

        n_maths_7eme = Notion(chapitre_id=ch_maths_7eme.id, nom="Notion Maths 7eme", ordre=1)
        n_eveil = Notion(chapitre_id=ch_eveil.id, nom="Notion Eveil", ordre=1)
        n_maths_bac = Notion(chapitre_id=ch_maths_bac.id, nom="Notion Maths Bac", ordre=1)
        db.add_all([n_maths_7eme, n_eveil, n_maths_bac])
        db.flush()

        # Contenus
        c_maths_7eme = ContenuNotion(notion_id=n_maths_7eme.id, niveau_assimilation="standard",
                                      type_ressource="cours", contenu="Maths 7eme C",
                                      enseignant_id=teacher_user.id, statut_pedagogique="c",
                                      statut_validation_pedagogique="en_attente")
        c_eveil = ContenuNotion(notion_id=n_eveil.id, niveau_assimilation="standard",
                                 type_ressource="cours", contenu="Eveil C",
                                 enseignant_id=teacher_user.id, statut_pedagogique="c",
                                 statut_validation_pedagogique="en_attente")
        c_maths_bac = ContenuNotion(notion_id=n_maths_bac.id, niveau_assimilation="standard",
                                     type_ressource="cours", contenu="Maths Bac C",
                                     enseignant_id=teacher_user.id, statut_pedagogique="c",
                                     statut_validation_pedagogique="en_attente")
        db.add_all([c_maths_7eme, c_eveil, c_maths_bac])
        db.commit()

        return {
            "db": db, "school": school,
            "resp1_user": resp1_user, "resp2_user": resp2_user,
            "teacher_user": teacher_user, "student_user": student_user,
            "mat_maths_7eme": mat_maths_7eme, "mat_eveil": mat_eveil, "mat_maths_bac": mat_maths_bac,
            "n_maths_7eme": n_maths_7eme, "n_eveil": n_eveil, "n_maths_bac": n_maths_bac,
            "c_maths_7eme": c_maths_7eme, "c_eveil": c_eveil, "c_maths_bac": c_maths_bac,
            "spec_sciences": spec_sciences,
            "niv1": niv1, "niv2": niv2,
        }

    def test_7_responsable_sciences_voit_deux_matieres(self):
        """Test 7: Un responsable avec specialite 'Sciences' (Maths + Eveil) voit le contenu des deux matières dans son scope."""
        d = self._seed()
        from app.services.adaptive_pathway import get_contenus_for_responsable

        # resp1 scope = [7eme] -> voit Maths 7eme et Eveil (les deux dans son scope)
        contenus = get_contenus_for_responsable(d["resp1_user"].id, d["db"])
        contenu_ids = [c.id for c in contenus]

        assert d["c_maths_7eme"].id in contenu_ids, "Le responsable Sciences devrait voir le contenu Maths 7eme"
        assert d["c_eveil"].id in contenu_ids, "Le responsable Sciences devrait voir le contenu Eveil"
        # Maths Bac n'est PAS dans le scope 7eme
        assert d["c_maths_bac"].id not in contenu_ids, "Le responsable Sciences (scope 7eme) ne devrait PAS voir Maths Bac"

    def test_8_deux_responsables_scopes_disjoints(self):
        """Test 8: Deux responsables sur la même specialite avec scopes disjoints ne voient pas le contenu de l'autre."""
        d = self._seed()
        from app.services.adaptive_pathway import get_contenus_for_responsable

        # Resp1 scope = [7eme] -> voit Maths 7eme et Eveil (7eme), PAS Maths Bac
        contenus_resp1 = get_contenus_for_responsable(d["resp1_user"].id, d["db"])
        ids_resp1 = [c.id for c in contenus_resp1]

        # Resp2 scope = [Bac] -> voit Maths Bac, PAS Maths 7eme ni Eveil
        contenus_resp2 = get_contenus_for_responsable(d["resp2_user"].id, d["db"])
        ids_resp2 = [c.id for c in contenus_resp2]

        assert d["c_maths_7eme"].id in ids_resp1, "Resp1 (7eme) devrait voir Maths 7eme"
        assert d["c_eveil"].id in ids_resp1, "Resp1 (7eme) devrait voir Eveil (7eme)"
        assert d["c_maths_bac"].id in ids_resp2, "Resp2 (Bac) devrait voir Maths Bac"
        assert d["c_maths_bac"].id not in ids_resp1, "Resp1 (7eme) ne devrait PAS voir Maths Bac"
        assert d["c_maths_7eme"].id not in ids_resp2, "Resp2 (Bac) ne devrait PAS voir Maths 7eme"
        assert d["c_eveil"].id not in ids_resp2, "Resp2 (Bac) ne devrait PAS voir Eveil (7eme)"

    def test_9_contenu_en_attente_non_visible_eleve(self):
        """Test 9: Un contenu en statut C mais validation EN_ATTENTE n'est PAS visible_eleve."""
        d = self._seed()
        from app.services.adaptive_pathway import visible_eleve

        assert visible_eleve(d["c_maths_7eme"]) is False, (
            "Le contenu avec statut_validation_pedagogique='en_attente' ne devrait pas être visible"
        )

    def test_10_rejet_remet_statut_a(self):
        """Test 10: Un rejet remet statut_pedagogique à A, efface valide_par/date_validation, avec commentaire."""
        d = self._seed()
        from app.services.adaptive_pathway import rejeter_contenu

        contenu = d["c_maths_7eme"]
        assert contenu.statut_pedagogique == "c"
        assert contenu.valide_par is None
        assert contenu.date_validation is None

        rejeter_contenu(contenu, d["resp1_user"].id, "Contenu incomplet", d["db"])

        d["db"].refresh(contenu)
        assert contenu.statut_pedagogique == "a", (
            f"Après rejet, statut_pedagogique devrait être 'a', recu '{contenu.statut_pedagogique}'"
        )
        assert contenu.statut_validation_pedagogique == "rejete"
        assert contenu.valide_par is None
        assert contenu.date_validation is None
        assert contenu.commentaire_rejet == "Contenu incomplet"
