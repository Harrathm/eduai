# LIVRABLE — Suivi d'Objectifs Pédagogiques Élèves

**Branche** : `phase1-critical`
**Commit** : `25ed2b6`
**Date** : 2026-07-22
**Tests** : 115/115 passent (15 nouveaux goal-tracking)

---

## 1. Schéma Complet — LearningGoal et Enums

```python
class GoalHorizon(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"

class GoalStatus(str, Enum):
    ON_TRACK = "on_track"
    BEHIND = "behind"
    COMPLETED = "completed"
    MISSED = "missed"

class GoalMetricType(str, Enum):
    LESSONS_COMPLETED = "lessons_completed"
    QUIZ_AVERAGE_SCORE = "quiz_average_score"
    STUDY_TIME_MINUTES = "study_time_minutes"
    CHAPTER_COMPLETION = "chapter_completion"
    CURRICULUM_COVERAGE_PERCENT = "curriculum_coverage_percent"

class GoalSource(str, Enum):
    AUTO_GENERATED = "auto_generated"
    TEACHER_ASSIGNED = "teacher_assigned"
    PEDAGOGICAL_LEAD_ASSIGNED = "pedagogical_lead_assigned"
    STUDENT_SELF = "student_self"

class LearningGoal(Base):
    # Pas de champ "status" — toujours calculé à la volée
    id, user_id, matiere, horizon, metric_type,
    target_value, period_start, period_end,
    source, created_by, created_at, updated_at
```

### Table `learning_goals` (migration SQL)
```sql
CREATE TABLE learning_goals (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    matiere VARCHAR(100),          -- null = objectif transversal
    horizon VARCHAR(20) NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    target_value NUMERIC(10,2) NOT NULL,
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    source VARCHAR(30) NOT NULL DEFAULT 'auto_generated',
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 2. Tous les Endpoints

| Méthode | Endpoint | Rôle requis | Description |
|---------|----------|-------------|-------------|
| GET | `/api/learner/goals?horizon=daily` | student | Objectifs avec statut calculé |
| GET | `/api/learner/goals/summary` | student | Synthèse 5 horizons |
| GET | `/api/learner/goals/report?horizon=weekly` | student | Bilan de fin de période |
| POST | `/api/learner/goals/annual` | student/pedagogical_lead | Objectif annuel |
| POST | `/api/pedagogical-lead/goals/quarterly` | pedagogical_lead | Assigner objectif trimestriel à une classe |
| GET | `/api/pedagogical-lead/goals/quarterly-overview` | pedagogical_lead | Vue agrégée par classe/élève |

---

## 3. Migrations DB (ordre d'exécution)

1. `learning_goals` table (voir schéma ci-dessus)
2. Index : `ix_learning_goals_user_id`, `ix_learning_goals_horizon`, `ix_learning_goals_period`

---

## 4. Tests

| # | Test | Ce qu'il vérifie |
|---|------|------------------|
| 1 | `test_enums` | Valeurs des enums GoalHorizon/GoalStatus/GoalMetricType/GoalSource |
| 2 | `test_school_calendar` | get_current_trimester(), get_period_for_horizon() |
| 3 | `test_status_messages` | Messages constructifs (pas culpabilisants) |
| 4 | `test_compute_goal_status_no_data` | Statut calculé même sans données → behind |
| 5 | `test_compute_goal_status_completed` | Période dépassée sans progrès → missed |
| 6 | `test_generate_daily_goal_excellence` | Excellence reçoit objectif daily |
| 7 | `test_generate_daily_goal_decouverte_returns_none` | **Découverte ne reçoit PAS d'objectif daily** |
| 8 | `test_generate_weekly_goal_decouverte_returns_none` | **Découverte ne reçoit PAS d'objectif weekly** |
| 9 | `test_generate_weekly_goal_excellence` | Excellence reçoit objectif weekly (5h = 300 min) |
| 10 | `test_ensure_goals_exist` | ensure_goals_exist crée daily + weekly |
| 11 | `test_decouverte_never_gets_custom_goals` | **Pack Découverte = jamais d'objectifs personnalisés** |
| 12 | `test_status_recalculates_dynamically` | **Statut recalculé à la volée, pas stocké** |
| 13 | `test_goals_endpoint` | GET /goals fonctionne |
| 14 | `test_goals_summary_endpoint` | GET /goals/summary retourne les 5 horizons |
| 15 | `test_goals_report_endpoint` | GET /goals/report fonctionne |

---

## 5. Règles Fondamentales Respectées

| Règle | Implémentation |
|-------|----------------|
| **Statut jamais stocké** | `compute_goal_status()` interroge LessonProgress/QuizAttempt à chaque appel |
| **Cache court** | Cache mémoire 5 min max, jamais en base |
| **Découverte = pas d'objectifs** | `generate_daily_goal()` et `generate_weekly_goal()` retournent None pour decouverte |
| **Messages constructifs** | `STATUS_MESSAGES` dict centralisé, pas de formulation culpabilisante |
| **Calendrier tunisien** | `school_calendar.py` avec 3 trimestres configurables |

---

## 6. Fichiers Créés/Modifiés

| Fichier | Type | Rôle |
|---------|------|------|
| `models.py` | modifié | Enums + LearningGoal model |
| `services/school_calendar.py` | **nouveau** | Calendrier scolaire tunisien |
| `services/goal_tracking.py` | **nouveau** | compute_goal_status + auto-generate |
| `services/notifications.py` | **nouveau** | Notifications douces |
| `routers/goals.py` | **nouveau** | Endpoints learner + pedagogical_lead |
| `main.py` | modifié | Router registrations |
| `tests/test_goal_tracking.py` | **nouveau** | 15 tests |

---

## 7. Décisions Nécessitant Votre Arbitrage

1. **Dates calendrier scolaire tunisien** : Utilisées par défaut :
   - T1 : 15 sept → 15 déc
   - T2 : 5 jan → 31 mars
   - T3 : 1 avril → 15 juin
   - ** À ajuster chaque année selon le bulletin officiel du Ministère**

2. **Objectif temps d'étude hebdomadaire** : 5h/semaine par défaut (300 minutes). Adaptatif possible selon l'historique de l'élève — à implémenter si souhaité.

3. **Notifications** : Pour l'instant, les notifications sont générées à la volée (pas de stockage persistant). Si un vrai système de notifications push est nécessaire, il faudra créer une table `notification_log`.
