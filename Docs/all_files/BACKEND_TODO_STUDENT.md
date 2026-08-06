# BACKEND_TODO_STUDENT.md — Endpoints manquants pour le dashboard élève

> **Date** : 05/08/2026
> **Statut** : Audit uniquement — aucun code backend modifié
> **Fichiers analysés** : `backend/app/routers/learner.py` (1270 lignes), `backend/app/routers/abonnements.py` (424 lignes)

---

## 1. `GET /api/learner/free-quota`

### Problème actuel
Le frontend calcule le quota de leçons gratuites via `computeQuota()` dans `useStudentDashboard.ts`, qui utilise `free_lessons_used ?? lessons_completed` comme proxy. **Il n'existe aucun endpoint backend** qui compte les leçons gratuites terminées depuis le début du trimestre en cours.

### Ce que fait le frontend aujourd'hui
```ts
// useStudentDashboard.ts — L60-61
const free_lessons_used = dashData.free_lessons_used ?? dashData.lessons_completed;
const exhausted = !isNotFree && free_lessons_used >= FREE_QUOTA_LIMIT;  // limit=3
```
C'est un **proxy approximatif** : `lessons_completed` compte TOUTES les leçons, pas uniquement celles du trimestre.

### Solution proposée

**Fichier** : `backend/app/routers/learner.py`
**Position** : Après la ligne 1094 (fin de `get_my_subscription_status`), avant la section TIER RECOMMENDATIONS (ligne 1097)

**Endpoint** :
```python
@router.get("/free-quota")
def get_free_quota(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Nombre de leçons gratuites terminées depuis le début du trimestre en cours.
    Réservé au palier découverte (gratuit). Limite = 3 leçons/trimestre.
    """
```

**Logique** :
1. Déterminer le trimestre en cours (réutiliser `TUNISIA_TRIMESTERS_2026_2027` depuis `abonnements.py`, ou duplicater la logique car `learner.py` n'importe pas ce module)
2. Filtrer `LessonProgress` WHERE `status = 'completed'` AND `completed_at >= trimester_start AND completed_at <= trimester_end`
3. Join via `CourseEnrollment` pour vérifier que `student_id = current_user.id`
4. Retourner `{ "used": int, "limit": 3, "remaining": int, "trimester_label": "T1", "trimester_start": "2026-09-15" }`

**Requête SQL approximative** :
```python
from datetime import date
from app.models import LessonProgress, CourseEnrollment

# Trimestres (à placer en constante ou importer depuis abonnements)
TUNISIA_TRIMESTERS = [
    (date(2026, 9, 15), date(2026, 12, 19), "T1"),
    (date(2027, 1, 5),  date(2027, 3, 27),  "T2"),
    (date(2027, 4, 6),  date(2027, 6, 19),  "T3"),
]

today = date.today()
trimester_start = None
trimester_label = None
for start, end, label in TUNISIA_TRIMESTERS:
    if start <= today <= end:
        trimester_start = start
        trimester_label = label
        break

if not trimester_start:
    return {"used": 0, "limit": 3, "remaining": 3, "trimester_label": None}

# Count completed lessons in current trimester
used = db.query(LessonProgress).join(
    CourseEnrollment, LessonProgress.enrollment_id == CourseEnrollment.id
).filter(
    CourseEnrollment.student_id == current_user.id,
    LessonProgress.status == "completed",
    LessonProgress.completed_at >= datetime.combine(trimester_start, datetime.min.time()),
    LessonProgress.completed_at <= datetime.combine(trimester_start.replace(year=trimester_start.year + 1), datetime.max.time()),
).count()

return {
    "used": min(used, 3),
    "limit": 3,
    "remaining": max(0, 3 - used),
    "trimester_label": trimester_label,
    "trimester_start": trimester_start.isoformat(),
}
```

### Impact frontend
Après implémentation, modifier `useStudentDashboard.ts` pour appeler `GET /api/learner/free-quota` au lieu de calculer en dur :
```ts
// Remplacer le computeQuota() inline par :
const freeQuota = await learnerApi.freeQuota().catch(() => ({ used: 0, limit: 3 }));
```

---

## 2. `POST /api/abonnements/{id}/reconfigure`

### Problème actuel
Le frontend a un `PackConfiguratorModal` qui permet de reconfigurer les matières d'un abonnement Basic/Silver. La méthode `reconfigureMatieres(abonnementId, matieres)` dans `abonnementApi.ts` appelle `POST /api/abonnements/{id}/reconfigure`, **mais cet endpoint n'existe pas côté backend**.

### Ce que fait le frontend aujourd'hui
```ts
// abonnementApi.ts
reconfigureMatieres: (abonnementId: number, matieres: string[]) =>
  api.post(`/api/abonnements/${abonnementId}/reconfigure`, { matieres }),
```
Cet appel retournerait une 404.

### Solution proposée

**Fichier** : `backend/app/routers/abonnements.py`
**Position** : Après la ligne 345 (fin de `change_tier`), avant `cancel_scheduled_change` (ligne 348)

**Endpoint** :
```python
@router.post("/abonnements/{abonnement_id}/reconfigure")
def reconfigure_matieres(
    abonnement_id: int,
    body: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(set_tenant_context),
):
    """
    Reconfigure les matières d'un abonnement Basic/Silver.
    - Basic : max 2 matières (1 langue + 1 spécialité)
    - Silver : max 4 matières (2 langues + 2 spécialités)
    - Golden : pas de reconfiguration (accès illimité)
    - Gratuit : pas de reconfiguration
    Fenêtre : 15 premiers jours du trimestre uniquement.
    """
```

**Logique** :
1. Vérifier que `abonnement_id` appartient à `current_user.id`
2. Vérifier que `abonnement.statut == "actif"`
3. Vérifier que `abonnement.pack.tier` est `basique` ou `silver`
4. Vérifier la fenêtre de reconfiguration (15 premiers jours du trimestre)
5. Valider le nombre de matières selon le tier
6. Mettre à jour `abonnement.matieres` (nouveau champ à ajouter au modèle `Abonnement` si absent)

**Validation du body** :
```python
matieres = body.get("matieres", [])
tier = active_abo.pack.tier

if tier == "basique" and len(matieres) > 2:
    raise HTTPException(400, "Basic: max 2 matières (1 langue + 1 spécialité)")
if tier == "silver" and len(matieres) > 4:
    raise HTTPException(400, "Silver: max 4 matières (2 langues + 2 spécialités)")
```

**Champ `matieres` sur le modèle Abonnement** :
Vérifier si `Abonnement` a déjà un champ `matieres`. Si non, ajouter via migration :
```python
# Dans models.py, classe Abonnement :
matieres: Mapped[Optional[list]] = mapped_column(JSON, default=list)
```

### Impact frontend
Aucun changement frontend nécessaire — `abonnementApi.ts` est déjà prêt.

---

## 3. Checklist de mise en œuvre

| Étape | Fichier | Action | Risque |
|-------|---------|--------|--------|
| 1 | `backend/app/models.py` | Vérifier/ajouter champ `matieres` sur `Abonnement` | Faible |
| 2 | `backend/app/routers/learner.py:L1095` | Ajouter endpoint `GET /free-quota` | Faible |
| 3 | `backend/app/routers/abonnements.py:L346` | Ajouter endpoint `POST /{id}/reconfigure` | Moyen (validation fenêtre) |
| 4 | Alembic migration | Si champ `matieres` ajouté | Faible |
| 5 | Tests | 2 tests endpoint free-quota + 3 tests reconfigure | Faible |
| 6 | Frontend `useStudentDashboard.ts` | Remplacer `computeQuota()` par appel API | Faible |

---

## 4. Risques identifiés

1. **Pas de champ `matieres` sur Abonnement** — Le modèle actuel n'a pas de champ pour stocker les matières reconfigurées. Il faut vérifier en DB si la colonne existe déjà (peut-être dans une migration récente) ou l'ajouter.

2. **Trimestres hardcodés** — `TUNISIA_TRIMESTERS_2026_2027` est dupliqué entre `abonnements.py` et le hook frontend. Pour `free-quota`, il faudra soit importer depuis `abonnements.py` (circular import risk), soit créer un module partagé `app/core/trimesters.py`.

3. **Fenêtre de reconfiguration** — La logique de vérification des 15 premiers jours existe dans le frontend (`useTrimesterReconfiguration`) mais pas dans le backend. Le backend doit la dupliquer pour des raisons de sécurité (le frontend peut être contourné).

4. **Idempotence** — Si l'élève reconfigure deux fois dans la même fenêtre, la 2ème doit écraser la 1ère (pas d'erreur). À documenter dans l'endpoint.
