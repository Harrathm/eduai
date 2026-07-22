# LIVRABLE — EDUAI Learning : Sécurité + Système de Paliers Élèves

**Branche** : `phase1-critical`
**Date** : 2026-07-21
**Tests** : 100/100 passent | Frontend : build OK

---

## 1. Audit RBAC — Corrections de sécurité

### 1.1 Multi-Tenancy (C1)
- **Fichier** : `db/session.py`
- **Mécanisme** : Event listener SQLAlchemy `do_orm_execute` qui injecte `WHERE school_id = :tid` automatiquement
- **Portée** : Toutes les tables avec `school_id` (User, Course, Lesson, etc.)
- **Contournement** : `current_tenant_id.set(None)` pour les rôles globaux (super_admin, pedagogical_admin)
- **Tests** : `test_tenant_filter.py` — 8 tests

### 1.2 Login is_active (M1)
- **Fichier** : `auth.py:258-260`
- **Correction** : Vérification `user.is_active` avant émission du token JWT
- **Impact** : Les comptes désactivés sont rejetés au login

### 1.3 Account Lockout (F3/F4)
- **Fichiers** : `core/rate_limiter.py`, `auth.py`
- **Mécanisme** : 5 tentatives échouées → lockout 15 min (configurable)
- **Tests** : `test_account_lockout.py` — 5 tests

### 1.4 Cross-School Isolation
- **Tests** : `test_tenant_filter.py` — Vérifie qu'un admin d'école A ne voit pas les données de l'école B

---

## 2. Câblage Système d'Accès aux Cours

### 2.1 has_course_access()
- **Fichier** : `services/course_access.py`
- **Utilisé dans** : `learner.py` (4 appels — lignes 301, 411, 576, 621)
- **Logique** :
  - Cours gratuit → accès immédiat
  - Leçon gratuite dans cours payant → bypass
  - Vérification `CoursePurchase` ou `CourseEnrollment`
  - Vérification `PackPurchase` (pack école actif)
- **Tests** : `test_course_access.py` — 19 tests

### 2.2 purchase_course
- **Fichier** : `routers/courses.py:341`
- **Mécanisme** : Débit `dt_balance` + création `CourseEnrollment` + `Transaction`
- **Tests** : Intégrés dans les tests d'accès

### 2.3 Catalog Visibility
- **Fichier** : `routers/catalog.py`
- **Filtrage** : `visibility != "school_only"` pour le catalogue public
- **Impact** : Les cours `school_only` n'apparaissent pas dans le catalogue général

---

## 3. Système de Paliers Élèves

### 3.1 Modèle de Données
- **Pas de nouvelles tables** pour les paliers
- **Source de vérité** : `get_student_tier(user, db)` → calcule dynamiquement depuis `PackPurchase`
- **Priorité** : etablissement > excellence > decouverte (default)

### 3.2 Fonction get_student_tier()
```python
# services/student_tier.py
def get_student_tier(user, db):
    # 1. Vérifier PackPurchase actif pour niveau_scolaire de l'élève
    # 2. Pack "etablissement" → etablissement
    # 3. Pack "excellence" → excellence
    # 4. Sinon → decouverte
```

### 3.3 Fonction get_ai_feature_level()
```python
# services/student_tier.py
def get_ai_feature_level(user, db):
    tier = get_student_tier(user, db)
    return {
        "decouverte": "basic",           # ask + explain
        "excellence": "adaptive",        # + exercises
        "etablissement": "curriculum_aligned",  # + generate
    }[tier]
```

### 3.4 Paliers

| Palier | AI Access | Features |
|--------|-----------|----------|
| **Découverte** | ask, explain | Parcours guidé, objectifs quotidiens |
| **Excellence** | + exercises | Recommandations adaptatives, analytics, test positionnement |
| **Établissement** | + generate | Contenu personnalisé, parcours programme national |

---

## 4. Endpoints Backend Ajoutés

| Endpoint | Méthode | Rôle |
|----------|---------|------|
| `/api/learner/dashboard` | GET | Dashboard différencié par palier |
| `/api/learner/daily-objective` | GET | Objectif quotidien |
| `/api/learner/recommended-path` | GET | Parcours recommandé |
| `/api/placement/tests` | GET | Liste tests de positionnement |
| `/api/placement/tests/{id}` | GET | Détail test |
| `/api/placement/tests/{id}/submit` | POST | Soumettre réponses → niveau compétence |
| `/api/ai/exercises` | POST | **Bloqué** si palier < excellence |
| `/api/ai/generate` | POST | **Bloqué** si palier < etablissement |

---

## 5. Frontend

### 5.1 Fichiers créés
| Fichier | Rôle |
|---------|------|
| `api/tier.ts` | Couche API (types + fonctions fetch) |
| `components/TierBadge.tsx` | Badge palier réutilisable |
| `components/DailyObjective.tsx` | Widget objectif quotidien |
| `components/RecommendedPath.tsx` | Widget parcours recommandé |
| `features/student/pages/StudentTierPage.tsx` | Page complète palier |
| `App.tsx` | Route `/dashboard/tier` ajoutée |
| `StudentDashboard.tsx` | Bouton "Mon Palier" dans accès rapide |

### 5.2 StudentTierPage
- Header gradient par palier
- Stats : cours inscrits, progression, leçons complétées
- Fonctionnalités incluses dans le palier
- Objectif quotidien + parcours recommandé
- Progression par matière (excellence/etablissement)
- Cours suggérés de l'établissement (etablissement)
- Prompt upgrade palier

---

## 6. Tables créées (Migration SQL)

```sql
CREATE TABLE placement_tests (
    id SERIAL PRIMARY KEY,
    matiere VARCHAR(100) NOT NULL,
    niveau VARCHAR(50) NOT NULL,
    title VARCHAR(255),
    questions JSON NOT NULL,
    created_by INTEGER REFERENCES users(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE placement_test_results (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    placement_test_id INTEGER NOT NULL REFERENCES placement_tests(id) ON DELETE CASCADE,
    competency_level VARCHAR(30) NOT NULL,  -- debutant/intermediaire/avance
    answers JSON,
    score FLOAT,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 7. Tests

| Fichier | Tests | Couverture |
|---------|-------|------------|
| `test_tier_restrictions.py` | 10 | Dashboard, objectives, placement, AI restrictions |
| `test_tenant_filter.py` | 8 | Multi-tenancy ORM |
| `test_account_lockout.py` | 5 | Lockout après tentatives échouées |
| `test_course_access.py` | 19 | Accès cours (has_course_access) |
| `test_role_rejection.py` | 13 | Rejet par rôle |
| `test_pack_access.py` | 15 | Accès par pack |
| `test_api.py` | 30 | Endpoints API |
| **Total** | **100** | **100% passent** |

---

## 8. Commits

| # | Hash | Description |
|---|------|-------------|
| 1 | `8b7cf8c` | feat(tier): système paliers élèves complet — backend |
| 2 | `b8a70fc` | feat(tier-frontend): page palier élèves + composants UI |

---

## 9. Prochaines Étapes

1. **Tests d'intégration** : Peupler des données de test (StudyPack + PackPurchase) pour tester les 3 paliers dans le navigateur
2. **Placement tests** : Créer des questions de test de positionnement dans la base
3. **A/B testing** : Mesurer l'engagement par palier
4. **Notifications** : Push notification pour objectifs quotidiens
5. **Gamification** : Badges, streaks, classements par palier
