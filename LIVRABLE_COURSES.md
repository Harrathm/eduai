# LIVRABLE FINAL — MODULE COURS (SYSTÈME DE PROPRIÉTÉ, TARIFICATION, DISTRIBUTION)

**Date**: 10 Juillet 2026
**Version**: 1.0

---

## 1. SCHÉMA DE BASE DE DONNÉES

### 1.1 Table `courses` (modifiée)

| Colonne | Type | Description |
|---------|------|-------------|
| id | SERIAL PK | Identifiant unique |
| title | VARCHAR(255) | Titre du cours |
| description | TEXT | Description |
| subject | VARCHAR(100) | Matière |
| level | VARCHAR(50) | Niveau |
| status | VARCHAR(30) | Statut de publication (draft/published/archived) |
| **owner_type** | VARCHAR(30) | Type propriétaire: `school`, `independent_teacher`, `eduai_catalog` |
| **owner_id** | INTEGER (nullable) | ID du propriétaire (school_id ou teacher_id selon owner_type) |
| **price** | FLOAT (nullable) | Prix en TND (null = gratuit, 0 = gratuit) |
| **currency** | VARCHAR(10) | Devise (défaut: "TND") |
| **commission_rate** | FLOAT (nullable) | Taux commission EDUAI en % (défaut: 30%) |
| **visibility** | VARCHAR(30) | Visibilité: `private`, `school_only`, `public_catalog` |
| **pedagogical_status** | VARCHAR(30) | Statut pédagogique (voir 1.2) |
| **validated_by** | INTEGER (nullable) | ID du validateur |
| **validated_by_role** | VARCHAR(30) | Rôle du validateur |
| **validated_at** | TIMESTAMP (nullable) | Date de validation |
| approved_for_b2b | BOOLEAN | Approuvé pour distribution B2B |
| school_id | INTEGER (nullable) | FK → schools.id (null pour catalog) |
| author_id | INTEGER | FK → users.id |
| ... | ... | Autres champs existants |

### 1.2 Enum `PedagogicalStatus`

| Valeur | Description |
|--------|-------------|
| `draft` | Brouillon, pas encore soumis |
| `pending_review` | Soumis, en attente de review |
| `rejected` | Rejeté par le pédagogue |
| `approved_for_platform` | Approuvé pour la plateforme |
| **approved_for_b2b** | Approuvé pour distribution B2B |
| `revision_requested` | Révision demandée |

### 1.3 Table `course_purchases` (modifiée)

| Colonne | Type | Description |
|---------|------|-------------|
| id | SERIAL PK | Identifiant unique |
| student_id | INTEGER FK | Élève acheteur |
| course_id | INTEGER FK | Cours acheté |
| amount_paid | FLOAT | Montant payé |
| currency | VARCHAR(10) | Devise |
| transaction_id | VARCHAR(255) | ID transaction externe |
| purchased_at | TIMESTAMP | Date d'achat |
| **platform_fee** | FLOAT | Commission EDUAI |
| **teacher_revenue** | FLOAT | Revenu enseignant |
| **commission_rate_applied** | FLOAT | Taux appliqué |
| **refunded** | BOOLEAN | Remboursé (défaut: false) |
| **refund_reason** | TEXT (nullable) | Raison du remboursement |
| **refunded_at** | TIMESTAMP (nullable) | Date du remboursement |

### 1.4 Table `teacher_contracts` (nouvelle)

| Colonne | Type | Description |
|---------|------|-------------|
| id | SERIAL PK | Identifiant unique |
| teacher_id | INTEGER FK | Enseignant concerné |
| status | VARCHAR(30) | `active`, `suspended`, `terminated` |
| started_at | TIMESTAMP | Début du contrat |
| ended_at | TIMESTAMP (nullable) | Fin du contrat |
| terminated_by | INTEGER (nullable) | ID super_admin |
| termination_reason | TEXT (nullable) | Raison de la résiliation |

---

## 2. MATRICE DE TRANSITION DES STATUTS PÉDAGOGIQUES

`course_lifecycle.py` est la **SEULE source de vérité** pour toutes les transitions.

| De | Vers | Checker |
|----|------|---------|
| `draft` | `pending_review` | `can_submit()` |
| `pending_review` | `approved_for_platform` | `can_approve_for_platform()` |
| `pending_review` | `approved_for_b2b` | `can_approve_for_b2b()` — **uniquement pedagogical_admin** |
| `pending_review` | `rejected` | `can_reject()` |
| `pending_review` | `revision_requested` | `can_request_revision()` |
| `rejected` | `draft` | `can_revise()` |
| `revision_requested` | `draft` | `can_revise()` |
| `approved_for_platform` | `approved_for_b2b` | `can_approve_for_b2b()` |
| `approved_for_platform` | `draft` | `can_deactivate()` |
| `approved_for_b2b` | `draft` | `can_deactivate()` |

**Règle critique**: `pedagogical_lead` ne peut **JAMAIS** approuver pour B2B.

---

## 3. ENDPOINTS API

### 3.1 Courses (`/api/courses`)

| Méthode | Endpoint | Rôle requis | Description |
|---------|----------|-------------|-------------|
| GET | `/courses/` | Tous | Liste des cours |
| GET | `/courses/{id}` | Tous | Détail d'un cours |
| POST | `/courses/` | teacher, admin_school, super_admin | Créer un cours |
| PUT | `/courses/{id}` | owner, admin | Modifier un cours |
| DELETE | `/courses/{id}` | owner, admin | Supprimer un cours |
| **PUT** | **`/courses/{id}/price`** | **independent_teacher (owner)** | **Fixer le prix** |
| **POST** | **`/courses/{id}/purchase`** | **Tous (authentifié)** | **Acheter un cours payant** |
| **GET** | **`/courses/my-sales`** | **independent_teacher** | **Consulter ses revenus** |
| **POST** | **`/courses/{id}/refund-request`** | **student** | **Demander un remboursement** |

### 3.2 Pedagogical Admin (`/api/pedagogical`)

| Méthode | Endpoint | Rôle requis | Description |
|---------|----------|-------------|-------------|
| GET | `/pedagogical/courses/pending` | pedagogical_admin | Cours en attente de review |
| PUT | `/pedagogical/courses/{id}/review` | pedagogical_admin | Valider/rejeter un cours |
| GET | `/pedagogical/reports/curriculum-coverage` | pedagogical_admin | Rapport de couverture |
| POST | `/pedagogical/ai/reports` | pedagogical_admin | Signaler un contenu IA |
| GET | `/pedagogical/reports` | pedagogical_admin | Consulter les signalements |
| PUT | `/pedagogical/reports/{id}/resolve` | pedagogical_admin | Résoudre un signalement |
| GET | `/pedagogical/escalations` | pedagogical_admin | Escalations |
| PUT | `/pedagogical/escalations/{id}/resolve` | pedagogical_admin | Résoudre une escalation |

### 3.3 Pedagogical Lead (`/api/pedagogical-lead`)

| Méthode | Endpoint | Rôle requis | Description |
|---------|----------|-------------|-------------|
| GET | `/pedagogical-lead/progress-report` | pedagogical_lead | Rapport de progression école |
| PUT | `/pedagogical-lead/courses/{id}/review-local` | pedagogical_lead | Review local (pas B2B) |
| POST | `/pedagogical-lead/escalate/{course_id}` | pedagogical_lead | Escalader vers pedagogical_admin |
| POST | `/pedagogical-lead/classes/{id}/reassign-teacher` | pedagogical_lead | Réassigner un prof |
| PUT | `/pedagogical-lead/assignments/{id}/postpone` | pedagogical_lead | Reporter une assignment |
| GET | `/pedagogical-lead/performance` | pedagogical_lead | Performance de l'école |
| GET | `/pedagogical-lead/ai-questions-analysis` | pedagogical_lead | Analyse des questions IA |

### 3.4 Admin Schools B2B (`/api/admin-courses`)

| Méthode | Endpoint | Rôle requis | Description |
|---------|----------|-------------|-------------|
| POST | `/admin-courses/schools/{id}/grant-course` | super_admin | Attribuer un cours (B2B) |

**Restriction B2B ajoutée**: Le cours doit être `approved_for_b2b` ET `owner_type != "independent_teacher"`.

---

## 4. LOGIQUE MÉTIER

### 4.1 Fixation de prix

```
PUT /courses/{id}/price?price=29.99
```

- Réservé à `owner_type="independent_teacher"` ET `owner_id=current_user.id`
- Prix max: 500 TND (configurable via `MAX_INDEPENDENT_COURSE_PRICE`)
- `owner_type="school"` et `"eduai_catalog"` → prix fixé par le super admin via `admin_courses.py`

### 4.2 Achat d'un cours

```
POST /courses/{id}/purchase
```

**Répartition financière**:
```
platform_fee = price × (commission_rate / 100)
teacher_revenue = price - platform_fee
```

Exemple avec prix=29.99, commission=30%:
- platform_fee = 8.997 TND
- teacher_revenue = 20.993 TND

### 4.3 Remboursement

```
POST /courses/{id}/refund-request?reason=...
```

**Règles**:
1. L'élève ne doit pas avoir dépassé 20% de progression (configurable)
2. `owner_type="eduai_catalog"` → remboursement automatique
3. `owner_type="independent_teacher"` ou `"school"` → validation super_admin requise

### 4.4 Distribution B2B

```
POST /admin-courses/schools/{school_id}/grant-course
```

**Vérifications**:
1. Le cours doit être `approved_for_b2b`
2. Le cours ne doit PAS être `owner_type="independent_teacher"`

### 4.5 Fin de contrat enseignant indépendant

Quand un enseignant indépendant quitte la plateforme:
1. Ses cours passent en `status="archived"`
2. Les élèves qui ont acheté ces cours conservent l'accès (owned)
3. Aucune réattribution possible (propriété perso)

---

## 5. ORDRE DE MIGRATION

```sql
-- PHASE 1: Enums et champs propriétés
ALTER TABLE courses ADD COLUMN owner_type VARCHAR(30) DEFAULT 'school';
ALTER TABLE courses ADD COLUMN owner_id INTEGER;
ALTER TABLE courses ADD COLUMN price FLOAT;
ALTER TABLE courses ADD COLUMN currency VARCHAR(10) DEFAULT 'TND';
ALTER TABLE courses ADD COLUMN commission_rate FLOAT DEFAULT 30.0;
ALTER TABLE courses ADD COLUMN pedagogical_status VARCHAR(30) DEFAULT 'draft';
ALTER TABLE courses ADD COLUMN validated_by INTEGER;
ALTER TABLE courses ADD COLUMN validated_by_role VARCHAR(30);
ALTER TABLE courses ADD COLUMN validated_at TIMESTAMP;
ALTER TABLE courses ADD COLUMN visibility VARCHAR(30) DEFAULT 'school_only';

-- PHASE 1: Course purchases
ALTER TABLE course_purchases ADD COLUMN platform_fee FLOAT;
ALTER TABLE course_purchases ADD COLUMN teacher_revenue FLOAT;
ALTER TABLE course_purchases ADD COLUMN commission_rate_applied FLOAT;
ALTER TABLE course_purchases ADD COLUMN refunded BOOLEAN DEFAULT FALSE;
ALTER TABLE course_purchases ADD COLUMN refund_reason TEXT;
ALTER TABLE course_purchases ADD COLUMN refunded_at TIMESTAMP;

-- PHASE 2: Teacher contracts (optionnel)
CREATE TABLE teacher_contracts (
    id SERIAL PRIMARY KEY,
    teacher_id INTEGER REFERENCES users(id),
    status VARCHAR(30) DEFAULT 'active',
    started_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP,
    terminated_by INTEGER REFERENCES users(id),
    termination_reason TEXT
);
```

---

## 6. TABLEAU DE TESTS

| Scénario | Endpoint | Rôle | Résultat attendu |
|----------|----------|------|------------------|
| Enseignant fixe le prix de son cours | PUT /courses/{id}/price | independent_teacher (owner) | 200 OK |
| Enseignant fixe le prix > 500 TND | PUT /courses/{id}/price | independent_teacher (owner) | 400 "prix max dépassé" |
| Admin fixe le prix d'un cours school | PUT /courses/{id}/price | admin_school | 403 "propriétaire seulement" |
| Élève achète cours gratuit | POST /courses/{id}/purchase | student | 400 "pas besoin d'acheter" |
| Élève achète cours payant | POST /courses/{id}/purchase | student | 200 OK |
| Élève rachète un cours déjà acheté | POST /courses/{id}/purchase | student | 400 "déjà acheté" |
| Enseignant consulte ses ventes | GET /courses/my-sales | independent_teacher | 200 OK |
| Élève demande remboursement (< 20% progrès) | POST /courses/{id}/refund-request | student | 200 "refunded" ou "pending" |
| Élève demande remboursement (> 20% progrès) | POST /courses/{id}/refund-request | student | 400 "progression trop avancée" |
| Super admin grant cours non-approuvé B2B | POST /admin-courses/schools/{id}/grant-course | super_admin | 400 "pas approuvé B2B" |
| Super admin grant cours independent_teacher | POST /admin-courses/schools/{id}/grant-course | super_admin | 400 "enseignant indépendant" |
| Super admin grant cours approuvé B2B | POST /admin-courses/schools/{id}/grant-course | super_admin | 200 OK |

---

## 7. RÉSUMÉ DES FICHIERS MODIFIÉS

| Fichier | Changements |
|---------|-------------|
| `backend/app/models.py` | `CourseOwnerType`, `CourseVisibility` enums; champs `price`, `currency`, `commission_rate`, `owner_type`, `owner_id`, `pedagogical_status`, `validated_by/at/role`; `CoursePurchase` financiarisé |
| `backend/app/core/config.py` | `MAX_INDEPENDENT_COURSE_PRICE`, `REFUND_MAX_PROGRESS_PERCENT`, `DEFAULT_COMMISSION_RATE` |
| `backend/app/services/course_lifecycle.py` | Matrice de transition complète avec `can_transition_status()` |
| `backend/app/routers/courses.py` | 4 nouveaux endpoints: `set_course_price`, `purchase_course`, `my_sales`, `refund_request` |
| `backend/app/routers/catalog.py` | Filtrage `visibility == "public_catalog"` |
| `backend/app/routers/admin_courses.py` | Vérification B2B dans `grant_course_to_school` |
| `backend/app/deps.py` | `check_course_ownership()` avec 3 owner_types |

---

## 8. CONFIGURATION

```python
# backend/app/core/config.py
max_independent_course_price: float = 500.0        # TND
refund_max_progress_percent: float = 20.0           # %
default_commission_rate: float = 30.0               # %
```
