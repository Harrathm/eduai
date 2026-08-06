# STUDENT_FEATURES_CODE.md — Phase 1 (Trigger Conversion) & Phase 3 (Reconfiguration Trimestrielle)

> **Date :** 05 Août 2026
> **Référence :** `STUDENT_JOURNEY_AUDIT.md`
> **Architecture :** Custom Hooks + Design System `src/components/ui/` + i18n `t()`

---

## CONVENTIONS UTILISÉES

| Convention | Détail |
|-----------|--------|
| Design System | `<Modal>`, `<Button>`, `<Spinner>`, `<PageSpinner>` depuis `src/components/ui/` |
| Props Modal | `open` (boolean), `onClose`, `title` |
| Props Button | `variant` : primary / secondary / ghost / danger / success ; `size` : sm / md / lg |
| i18n | `useTranslation()` + `t("student.quota.*")` / `t("student.trimester.*")` |
| Hooks | Toute la logique métier dans des Custom Hooks, zéro logique dans les composants UI |
| API | Aucun `fetch()` inline, uniquement via `src/api/` |

---

# PARTIE 1 — PHASE 1 : TRIGGER CONVERSION (Quota Gratuit)

---

## 1.1 Hook : `useQuotaGuard.ts`

**Fichier :** `src/features/student/hooks/useQuotaGuard.ts`

**Rôle :** Vérifie si l'élève est sur le pack Gratuit, calcule le quota restant (3 leçons/trimestre), et déclenche un état `exhausted` quand le quota est atteint.

**Note backend :** L'endpoint `/api/learner/dashboard` retourne `tier` et `lessons_completed` (total toutes matières). Le compteur de leçons gratuites par trimestre n'est pas encore exposé par un endpoint dédié. Ce hook utilise le champ `free_lessons_used` qui sera ajouté au backend (voir section 1.6). En attendant, il fallback sur `lessons_completed` comme proxy.

```typescript
// src/features/student/hooks/useQuotaGuard.ts

import { useState, useEffect, useCallback, useRef } from "react";
import { tierApi, type DashboardData } from "../../../api";

const FREE_QUOTA_LIMIT = 3;

interface UseQuotaGuardReturn {
  /** Tier actuel de l'élève (decouverte / excellence / etablissement) */
  tier: string | null;
  /** Nombre de leçons gratuites utilisées ce trimestre */
  used: number;
  /** Limite du quota gratuit (toujours 3) */
  limit: number;
  /** Nombre de leçons restantes (min 0) */
  remaining: number;
  /** Pourcentage de consommation (0-100) */
  percent: number;
  /** true si le quota est épuisé (used >= limit) */
  exhausted: boolean;
  /** true si l'élève n'est PAS sur le pack gratuit */
  isNotFree: boolean;
  /** true si les données sont en cours de chargement */
  loading: boolean;
  /** Erreur éventuelle */
  error: string | null;
  /** Force un rechargement des données */
  refresh: () => Promise<void>;
}

export function useQuotaGuard(): UseQuotaGuardReturn {
  const [tier, setTier] = useState<string | null>(null);
  const [used, setUsed] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const mountedRef = useRef(true);

  const fetchQuota = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data: DashboardData = await tierApi.dashboard();
      if (!mountedRef.current) return;

      setTier(data.tier);

      // Le champ `free_lessons_used` sera ajouté au backend.
      // Pour l'instant, on utilise `lessons_completed` comme proxy
      // car les élèves gratuits n'ont accès qu'à 3 leçons.
      // Quand le backend exposera `free_lessons_used`, remplacer :
      //   setUsed((data as any).free_lessons_used ?? 0);
      // Par :
      const freeUsed = (data as any).free_lessons_used ?? data.lessons_completed;
      setUsed(freeUsed);
    } catch (err: any) {
      if (mountedRef.current) {
        setError(err.message || "Erreur lors du chargement du quota");
      }
    } finally {
      if (mountedRef.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    fetchQuota();
    return () => {
      mountedRef.current = false;
    };
  }, [fetchQuota]);

  const isNotFree = tier !== null && tier !== "decouverte";
  const remaining = Math.max(0, FREE_QUOTA_LIMIT - used);
  const percent = Math.min(100, Math.round((used / FREE_QUOTA_LIMIT) * 100));
  const exhausted = used >= FREE_QUOTA_LIMIT;

  return {
    tier,
    used,
    limit: FREE_QUOTA_LIMIT,
    remaining,
    percent,
    exhausted,
    isNotFree,
    loading,
    error,
    refresh: fetchQuota,
  };
}
```

---

## 1.2 Composant : `QuotaGauge.tsx`

**Fichier :** `src/features/student/components/quota/QuotaGauge.tsx`

**Rôle :** Affiche une jauge visuelle "X/3 leçons utilisées" avec une barre de progression colorée.

```tsx
// src/features/student/components/quota/QuotaGauge.tsx

import { useTranslation } from "react-i18next";

interface QuotaGaugeProps {
  /** Nombre de leçons utilisées */
  used: number;
  /** Limite totale (3) */
  limit: number;
  /** Pourcentage de consommation (0-100) */
  percent: number;
}

export function QuotaGauge({ used, limit, percent }: QuotaGaugeProps) {
  const { t } = useTranslation();

  const barColor =
    percent >= 100
      ? "bg-red-500"
      : percent >= 66
      ? "bg-orange"
      : percent >= 33
      ? "bg-amber-400"
      : "bg-green-500";

  const textColor =
    percent >= 100
      ? "text-red-600"
      : percent >= 66
      ? "text-orange"
      : "text-navy";

  return (
    <div className="bg-white rounded-2xl p-5 shadow-sm border border-black/5">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-navy">
          {t("student.quota.title")}
        </h3>
        <span className={`text-lg font-bold ${textColor}`}>
          {used}/{limit}
        </span>
      </div>

      {/* Barre de progression */}
      <div className="w-full bg-gray-100 rounded-full h-3 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ease-out ${barColor}`}
          style={{ width: `${percent}%` }}
        />
      </div>

      {/* Label sous la barre */}
      <p className="text-xs text-gray mt-2">
        {t("student.quota.subtitle", { used, limit })}
      </p>
    </div>
  );
}
```

---

## 1.3 Composant : `QuotaExhaustedModal.tsx`

**Fichier :** `src/features/student/components/quota/QuotaExhaustedModal.tsx`

**Rôle :** Modale de conversion affichée quand le quota gratuit est épuisé. Redirige vers la boutique.

```tsx
// src/features/student/components/quota/QuotaExhaustedModal.tsx

import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Modal, Button } from "../../../../components/ui";
import { AlertTriangle } from "lucide-react";

interface QuotaExhaustedModalProps {
  /** Contrôle l'ouverture de la modale */
  open: boolean;
  /** Appelé pour fermer la modale */
  onClose: () => void;
}

export function QuotaExhaustedModal({
  open,
  onClose,
}: QuotaExhaustedModalProps) {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const handleGoToPacks = () => {
    onClose();
    navigate("/dashboard/packs");
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={t("student.quota.exhaustedTitle")}
    >
      <div className="space-y-6">
        {/* Icône d'avertissement */}
        <div className="flex justify-center">
          <div className="w-16 h-16 bg-orange/10 rounded-full flex items-center justify-center">
            <AlertTriangle className="w-8 h-8 text-orange" />
          </div>
        </div>

        {/* Message principal */}
        <div className="text-center space-y-2">
          <p className="text-navy font-medium">
            {t("student.quota.exhaustedMessage")}
          </p>
          <p className="text-sm text-gray">
            {t("student.quota.exhaustedDescription")}
          </p>
        </div>

        {/* Avantages */}
        <div className="bg-cream rounded-2xl p-4 space-y-2">
          <p className="text-xs font-semibold text-navy uppercase tracking-wide">
            {t("student.quota.unlockBenefits")}
          </p>
          <ul className="space-y-1.5">
            {[
              t("student.quota.benefit1"),
              t("student.quota.benefit2"),
              t("student.quota.benefit3"),
            ].map((benefit) => (
              <li
                key={benefit}
                className="flex items-center gap-2 text-sm text-gray-700"
              >
                <span className="w-1.5 h-1.5 bg-orange rounded-full flex-shrink-0" />
                {benefit}
              </li>
            ))}
          </ul>
        </div>

        {/* Actions */}
        <div className="flex gap-3">
          <Button
            variant="ghost"
            size="md"
            onClick={onClose}
            className="flex-1"
          >
            {t("student.quota.later")}
          </Button>
          <Button
            variant="primary"
            size="md"
            onClick={handleGoToPacks}
            className="flex-1"
          >
            {t("student.quota.discoverPacks")}
          </Button>
        </div>
      </div>
    </Modal>
  );
}
```

---

## 1.4 barrel export : `quota/index.ts`

**Fichier :** `src/features/student/components/quota/index.ts`

```ts
export { QuotaGauge } from "./QuotaGauge";
export { QuotaExhaustedModal } from "./QuotaExhaustedModal";
```

---

## 1.5 Intégration dans `StudentDashboard.tsx`

**Fichier :** `src/features/student/pages/StudentDashboard.tsx`

**Modifications :**
1. Importer `useQuotaGuard`, `QuotaGauge`, `QuotaExhaustedModal`
2. Ajouter le hook dans le composant
3. Afficher `QuotaGauge` après le header (si Gratuit)
4. Afficher `QuotaExhaustedModal` quand `exhausted` est true

```tsx
// ─── IMPORTS À AJOUTER en haut du fichier ────────────────────────────────────
import { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { useAuthStore } from "../../../store/authStore";
import { tierApi, type DashboardData, type DailyObjective } from "../../../api";
const tierAPI = tierApi;
import { tokenStorage } from "../../../utils/tokenStorage";
// ── NOUVEAUX IMPORTS ──
import { useQuotaGuard } from "../hooks/useQuotaGuard";
import { QuotaGauge } from "../components/quota/QuotaGauge";
import { QuotaExhaustedModal } from "../components/quota/QuotaExhaustedModal";

// ─── DANS LE COMPOSANT StudentDashboard ──────────────────────────────────────

export default function StudentDashboard() {
  const { t } = useTranslation();
  const { user } = useAuthStore();
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [packTier, setPackTier] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // ── NOUVEAU : Hook quota guard ──
  const quota = useQuotaGuard();
  const [showQuotaModal, setShowQuotaModal] = useState(false);

  // Déclencher la modale quand le quota passe à épuisé
  useEffect(() => {
    if (quota.exhausted && !quota.isNotFree && !loading) {
      setShowQuotaModal(true);
    }
  }, [quota.exhausted, quota.isNotFree, loading]);

  useEffect(() => {
    async function fetchData() {
      try {
        const [dashData, aboData] = await Promise.all([
          tierAPI.dashboard(),
          fetch("/api/abonnements/mes-abonnements", {
            headers: { Authorization: `Bearer ${tokenStorage.getToken()}` },
          }).then((r) => (r.ok ? r.json() : { items: [] })).catch(() => ({ items: [] })),
        ]);
        setDashboard(dashData);
        const activeAbo = (aboData.items || []).find(
          (a: any) => a.statut === "actif" || a.statut === "grace"
        );
        if (activeAbo?.pack?.tier) setPackTier(activeAbo.pack.tier);
      } catch (err: any) {
        setError(err.message || t("student.dashboard.erreurChargement"));
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="bg-navy rounded-3xl p-8">
        <h1 className="text-4xl font-[300] text-white">
          {t("student.dashboard.title")}
        </h1>
        <p className="text-white/50 mt-2">
          {t("student.dashboard.welcome", { name: user?.full_name })}
        </p>
        {dashboard?.tier && (
          <div className="mt-3 flex items-center gap-2">
            <PalierBadge tier={dashboard.tier} />
            {packTier && <PackBadge tier={packTier} />}
          </div>
        )}
      </div>

      {/* ── NOUVEAU : Jauge de quota gratuit ── */}
      {!loading && !quota.isNotFree && !quota.error && (
        <QuotaGauge
          used={quota.used}
          limit={quota.limit}
          percent={quota.percent}
        />
      )}

      {/* ── NOUVEAU : Modale de conversion ── */}
      <QuotaExhaustedModal
        open={showQuotaModal}
        onClose={() => setShowQuotaModal(false)}
      />

      {/* Daily Objective — first section */}
      {loading ? (
        <ObjectiveSkeleton />
      ) : dashboard?.daily_objective ? (
        <DailyObjectiveCard objective={dashboard.daily_objective} />
      ) : null}

      {/* ... le reste du composant reste inchangé ... */}
    </div>
  );
}
```

---

## 1.6 Note Backend (à implémenter)

Pour que le compteur de leçons gratuites soit précis par trimestre, ajouter au backend :

**Option A — Ajouter un champ à l'endpoint `/api/learner/dashboard` :**

```python
# Dans learner.py, fonction learner_dashboard()
# Après le calcul de total_lessons_completed :

if tier == "decouverte":
    # Compter les leçons complétées depuis le début du trimestre en cours
    trimester_start = _get_current_trimester_start(today)
    free_lessons_used = db.query(LessonProgress).join(CourseEnrollment).filter(
        CourseEnrollment.student_id == current_user.id,
        LessonProgress.status == "completed",
        LessonProgress.completed_at >= trimester_start,
    ).count()
    dashboard["free_lessons_used"] = min(free_lessons_used, 3)
```

**Option B — Endpoint dédié (recommandé) :**

```python
# Ajouter dans learner.py :
@router.get("/free-quota")
def get_free_quota(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tier = get_student_tier(current_user, db)
    if tier != "decouverte":
        return {"tier": tier, "is_free": False, "used": 0, "limit": 3}

    trimester_start = _get_current_trimester_start(datetime.now(timezone.utc).date())
    used = db.query(LessonProgress).join(CourseEnrollment).filter(
        CourseEnrollment.student_id == current_user.id,
        LessonProgress.status == "completed",
        LessonProgress.completed_at >= trimester_start,
    ).count()

    return {
        "tier": tier,
        "is_free": True,
        "used": min(used, 3),
        "limit": 3,
        "trimester": _get_current_trimester_name(),
    }
```

**Dans ce cas, modifier `useQuotaGuard.ts` pour appeler `/api/learner/free-quota` au lieu de `/api/learner/dashboard`.**

---

# PARTIE 2 — PHASE 3 : RECONFIGURATION TRIMESTRIELLE

---

## 2.1 Hook : `useTrimesterReconfiguration.ts`

**Fichier :** `src/features/student/hooks/useTrimesterReconfiguration.ts`

**Rôle :** Calcule le trimestre actuel (T1/T2/T3) selon le calendrier scolaire tunisien, détermine si on est dans la fenêtre de reconfiguration (15 premiers jours), et vérifie si l'élève a un pack Basic/Silver éligible.

```typescript
// src/features/student/hooks/useTrimesterReconfiguration.ts

import { useState, useEffect, useCallback, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { api } from "../../../utils/apiClient";

// ─── Calendrier scolaire tunisien (par défaut, ajustable) ────────────────────
// Les dates exactes sont définies par le Ministère chaque année.
// Ces valeurs correspondent à l'année scolaire 2026-2027.

interface TrimesterDateRange {
  label: string;
  start: { month: number; day: number }; // 1-indexed
  end: { month: number; day: number };
  reconfigWindowDays: number; // Nombre de jours au début du trimestre pour reconfigurer
}

const TRIMESTER_CALENDAR: TrimesterDateRange[] = [
  {
    label: "T1",
    start: { month: 9, day: 15 },  // 15 septembre
    end: { month: 12, day: 19 },   // 19 décembre
    reconfigWindowDays: 15,
  },
  {
    label: "T2",
    start: { month: 1, day: 5 },   // 5 janvier
    end: { month: 3, day: 27 },    // 27 mars
    reconfigWindowDays: 15,
  },
  {
    label: "T3",
    start: { month: 4, day: 6 },   // 6 avril
    end: { month: 6, day: 19 },    // 19 juin
    reconfigWindowDays: 15,
  },
];

// ─── Types ───────────────────────────────────────────────────────────────────

interface MonPackData {
  current_tier: string;
  current_pack: {
    id: number;
    tier: string;
    nom: string;
    matieres: any;
  } | null;
  abonnement: {
    id: number;
    statut: string;
    debut: string;
    fin: string;
  } | null;
  niveau_scolaire: string | null;
}

interface TrimesterInfo {
  /** Label du trimestre (T1, T2, T3) */
  label: string;
  /** Numéro du trimestre (1, 2, 3) */
  number: number;
  /** Date de début du trimestre */
  startDate: Date;
  /** Date de fin du trimestre */
  endDate: Date;
}

export interface UseTrimesterReconfigurationReturn {
  /** Informations sur le trimestre actuel */
  currentTrimester: TrimesterInfo | null;
  /** true si on est dans les 15 premiers jours du trimestre */
  isInReconfigWindow: boolean;
  /** Nombre de jours restants dans la fenêtre de reconfiguration (0 si hors fenêtre) */
  daysRemainingInWindow: number;
  /** true si l'élève a un pack Basic ou Silver (éligible à la reconfiguration) */
  isEligible: boolean;
  /** true si le pack est Golden (pas besoin de reconfigurer) */
  isGolden: boolean;
  /** true si le pack est Gratuit (pas de reconfiguration) */
  isFree: boolean;
  /** true si une reconfiguration a déjà été faite ce trimestre */
  alreadyReconfigured: boolean;
  /** true si la reconfiguration est possible maintenant */
  canReconfigure: boolean;
  /** true si les données sont en cours de chargement */
  loading: boolean;
  /** Erreur éventuelle */
  error: string | null;
  /** Charge les données depuis l'API */
  refresh: () => Promise<void>;
}

export function useTrimesterReconfiguration(): UseTrimesterReconfigurationReturn {
  const { t } = useTranslation();
  const [packData, setPackData] = useState<MonPackData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPack = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get<MonPackData>("/api/abonnements/mon-pack");
      setPackData(res);
    } catch (err: any) {
      setError(err.message || t("student.trimester.errorLoading"));
    } finally {
      setLoading(false);
    }
  }, [t]);

  useEffect(() => {
    fetchPack();
  }, [fetchPack]);

  // ─── Calcul du trimestre actuel ──────────────────────────────────────────

  const currentTrimester = useMemo((): TrimesterInfo | null => {
    const now = new Date();
    const currentMonth = now.getMonth() + 1; // 1-indexed
    const currentDay = now.getDate();

    for (let i = 0; i < TRIMESTER_CALENDAR.length; i++) {
      const cal = TRIMESTER_CALENDAR[i];
      const startMonth = cal.start.month;
      const startDay = cal.start.day;
      const endMonth = cal.end.month;
      const endDay = cal.end.day;

      let isInRange = false;

      // Cas normal (start < end dans le même calendrier)
      if (startMonth <= endMonth) {
        isInRange =
          (currentMonth > startMonth ||
            (currentMonth === startMonth && currentDay >= startDay)) &&
          (currentMonth < endMonth ||
            (currentMonth === endMonth && currentDay <= endDay));
      }
      // Cas跨界 (T3: avril → juin, ou si on gère des tranches qui passent l'année)
      else {
        isInRange =
          currentMonth > startMonth ||
          (currentMonth === startMonth && currentDay >= startDay) ||
          currentMonth < endMonth ||
          (currentMonth === endMonth && currentDay <= endDay);
      }

      if (isInRange) {
        return {
          label: cal.label,
          number: i + 1,
          startDate: new Date(now.getFullYear(), startMonth - 1, startDay),
          endDate: new Date(now.getFullYear(), endMonth - 1, endDay),
        };
      }
    }

    // Hors trimestre (vacances ou période non définie)
    return null;
  }, []);

  // ─── Calcul de la fenêtre de reconfiguration ──────────────────────────────

  const reconfigWindowState = useMemo(() => {
    if (!currentTrimester) {
      return { isInWindow: false, daysRemaining: 0 };
    }

    const now = new Date();
    const trimesterStart = currentTrimester.startDate;
    const diffTime = now.getTime() - trimesterStart.getTime();
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

    const cal = TRIMESTER_CALENDAR[currentTrimester.number - 1];
    const windowDays = cal.reconfigWindowDays;

    if (diffDays < 0) {
      // Le trimestre n'a pas encore commencé
      return { isInWindow: false, daysRemaining: 0 };
    }

    if (diffDays < windowDays) {
      return {
        isInWindow: true,
        daysRemaining: windowDays - diffDays,
      };
    }

    return { isInWindow: false, daysRemaining: 0 };
  }, [currentTrimester]);

  // ─── Éligibilité au pack ──────────────────────────────────────────────────

  const currentTier = packData?.current_tier || "gratuit";
  const packTier = packData?.current_pack?.tier || "gratuit";

  const isGolden = packTier === "golden";
  const isFree = currentTier === "decouverte" || packTier === "gratuit";
  const isEligible = !isGolden && !isFree; // Basique ou Silver

  // Vérifier si une reconfiguration a déjà été faite ce trimestre
  // (à connecter à un endpoint backend quand il existera)
  const alreadyReconfigured = false;

  const canReconfigure =
    isEligible &&
    reconfigWindowState.isInWindow &&
    !alreadyReconfigured &&
    !loading;

  return {
    currentTrimester,
    isInReconfigWindow: reconfigWindowState.isInWindow,
    daysRemainingInWindow: reconfigWindowState.daysRemaining,
    isEligible,
    isGolden,
    isFree,
    alreadyReconfigured,
    canReconfigure,
    loading,
    error,
    refresh: fetchPack,
  };
}
```

---

## 2.2 Composant : `TrimesterBadge.tsx`

**Fichier :** `src/features/student/components/trimester/TrimesterBadge.tsx`

**Rôle :** Petit badge affichant "Trimestre 1" (ou 2/3) avec les dates.

```tsx
// src/features/student/components/trimester/TrimesterBadge.tsx

import { useTranslation } from "react-i18next";

interface TrimesterBadgeProps {
  /** Label du trimestre (T1, T2, T3) */
  label: string;
  /** Numéro du trimestre */
  number: number;
  /** Date de début */
  startDate: Date;
  /** Date de fin */
  endDate: Date;
}

export function TrimesterBadge({
  label,
  number,
  startDate,
  endDate,
}: TrimesterBadgeProps) {
  const { t } = useTranslation();

  const formatDate = (date: Date) =>
    date.toLocaleDateString("fr-TN", { day: "numeric", month: "short" });

  return (
    <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-navy/10 rounded-full">
      <span className="w-2 h-2 bg-navy rounded-full" />
      <span className="text-xs font-semibold text-navy">
        {t("student.trimester.badge", { label })}
      </span>
      <span className="text-xs text-gray">
        {formatDate(startDate)} — {formatDate(endDate)}
      </span>
    </div>
  );
}
```

---

## 2.3 Composant : `TrimesterReconfigBanner.tsx`

**Fichier :** `src/features/student/components/trimester/TrimesterReconfigBanner.tsx`

**Rôle :** Bannière conditionnelle affichée quand la reconfiguration est possible, avec un CTA.

```tsx
// src/features/student/components/trimester/TrimesterReconfigBanner.tsx

import { useTranslation } from "react-i18next";
import { Button } from "../../../../components/ui";
import { RefreshCw, Clock } from "lucide-react";

interface TrimesterReconfigBannerProps {
  /** true si la reconfiguration est possible */
  canReconfigure: boolean;
  /** Nombre de jours restants dans la fenêtre */
  daysRemaining: number;
  /** Nom du trimestre actuel */
  trimesterLabel: string;
  /** Appelé quand l'utilisateur clique sur "Reconfigurer" */
  onReconfigure: () => void;
}

export function TrimesterReconfigBanner({
  canReconfigure,
  daysRemaining,
  trimesterLabel,
  onReconfigure,
}: TrimesterReconfigBannerProps) {
  const { t } = useTranslation();

  if (!canReconfigure) return null;

  return (
    <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-2xl p-5">
      <div className="flex items-start gap-4">
        {/* Icône */}
        <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center flex-shrink-0">
          <RefreshCw className="w-5 h-5 text-blue-600" />
        </div>

        {/* Contenu */}
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-blue-900 text-sm">
            {t("student.trimester.newTrimester", { trimester: trimesterLabel })}
          </h3>
          <p className="text-sm text-blue-700 mt-1">
            {t("student.trimester.reconfigDescription")}
          </p>
          <div className="flex items-center gap-1.5 mt-2">
            <Clock className="w-3.5 h-3.5 text-blue-500" />
            <span className="text-xs text-blue-600">
              {t("student.trimester.daysRemaining", { count: daysRemaining })}
            </span>
          </div>
        </div>

        {/* CTA */}
        <Button
          variant="secondary"
          size="sm"
          onClick={onReconfigure}
          className="flex-shrink-0"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          {t("student.trimester.reconfigure")}
        </Button>
      </div>
    </div>
  );
}
```

---

## 2.4 Composant : `TrimesterInfo.tsx`

**Fichier :** `src/features/student/components/trimester/TrimesterInfo.tsx`

**Rôle :** Encart complet affichant les informations du trimestre dans la page StudentPackPage.

```tsx
// src/features/student/components/trimester/TrimesterInfo.tsx

import { useTranslation } from "react-i18next";
import { Calendar, CheckCircle, Lock } from "lucide-react";

interface TrimesterInfoProps {
  /** Label du trimestre (T1, T2, T3) */
  trimesterLabel: string;
  /** Date de début */
  startDate: Date;
  /** Date de fin */
  endDate: Date;
  /** true si dans la fenêtre de reconfiguration */
  isInWindow: boolean;
  /** true si déjà reconfiguré */
  alreadyReconfigured: boolean;
  /** Pack tier (pour afficher le bon message) */
  packTier: string;
}

export function TrimesterInfo({
  trimesterLabel,
  startDate,
  endDate,
  isInWindow,
  alreadyReconfigured,
  packTier,
}: TrimesterInfoProps) {
  const { t } = useTranslation();

  const formatDate = (date: Date) =>
    date.toLocaleDateString("fr-TN", {
      day: "numeric",
      month: "long",
      year: "numeric",
    });

  const isGolden = packTier === "golden";
  const isFree = packTier === "gratuit";

  return (
    <div className="bg-white rounded-2xl p-5 shadow-sm border border-black/5">
      <div className="flex items-center gap-3 mb-4">
        <Calendar className="w-5 h-5 text-navy" />
        <h3 className="font-semibold text-navy">
          {t("student.trimester.currentTrimester", { label: trimesterLabel })}
        </h3>
      </div>

      <div className="space-y-3">
        {/* Dates */}
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray">{t("student.trimester.period")}</span>
          <span className="font-medium text-navy">
            {formatDate(startDate)} — {formatDate(endDate)}
          </span>
        </div>

        {/* Statut de reconfiguration */}
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray">{t("student.trimester.reconfigStatus")}</span>
          {isGolden ? (
            <span className="flex items-center gap-1.5 text-amber-600">
              <CheckCircle className="w-4 h-4" />
              {t("student.trimester.goldenNoNeed")}
            </span>
          ) : isFree ? (
            <span className="flex items-center gap-1.5 text-gray">
              <Lock className="w-4 h-4" />
              {t("student.trimester.freeNotEligible")}
            </span>
          ) : alreadyReconfigured ? (
            <span className="flex items-center gap-1.5 text-green-600">
              <CheckCircle className="w-4 h-4" />
              {t("student.trimester.alreadyReconfigured")}
            </span>
          ) : isInWindow ? (
            <span className="text-blue-600 font-medium">
              {t("student.trimester.windowOpen")}
            </span>
          ) : (
            <span className="text-gray">
              {t("student.trimester.windowClosed")}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
```

---

## 2.5 barrel export : `trimester/index.ts`

**Fichier :** `src/features/student/components/trimester/index.ts`

```ts
export { TrimesterBadge } from "./TrimesterBadge";
export { TrimesterReconfigBanner } from "./TrimesterReconfigBanner";
export { TrimesterInfo } from "./TrimesterInfo";
```

---

## 2.6 Intégration dans `StudentPackPage.tsx`

**Fichier :** `src/features/student/pages/StudentPackPage.tsx`

**Modifications :**
1. Importer `useTrimesterReconfiguration`, `TrimesterReconfigBanner`, `TrimesterInfo`
2. Ajouter le hook dans le composant
3. Afficher `TrimesterReconfigBanner` après les messages d'erreur/succès
4. Afficher `TrimesterInfo` dans la section du pack actuel

```tsx
// ─── IMPORTS À AJOUTER en haut du fichier ────────────────────────────────────
import { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { useAuthStore } from "../../../store/authStore";
import { api } from "../../../utils/apiClient";
import { Package, AlertTriangle, CheckCircle, Clock, RefreshCw, ArrowUpCircle, ArrowDownCircle, XCircle } from "lucide-react";
// ── NOUVEAUX IMPORTS ──
import { useTrimesterReconfiguration } from "../hooks/useTrimesterReconfiguration";
import { TrimesterReconfigBanner } from "../components/trimester/TrimesterReconfigBanner";
import { TrimesterInfo } from "../components/trimester/TrimesterInfo";

// ─── DANS LE COMPOSANT StudentPackPage ───────────────────────────────────────

export default function StudentPackPage() {
  const { t } = useTranslation();
  const { user } = useAuthStore();
  const [data, setData] = useState<MonPackData | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // ── NOUVEAU : Hook reconfiguration trimestrielle ──
  const trimester = useTrimesterReconfiguration();

  const fetchMonPack = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get<MonPackData>("/api/abonnements/mon-pack");
      setData(res);
    } catch (err: any) {
      setError(err.message || t("pack.loadingError"));
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchMonPack();
  }, [fetchMonPack]);

  // ... (handleChangeTier et handleCancelScheduled restent inchangés) ...

  const handleReconfigure = () => {
    // Ouvrir la page de reconfiguration ou un modal
    // À connecter quand la page MatiereReconfigurationPage sera créée
    window.location.href = "/dashboard/reconfigure-pack";
  };

  // ... (now, currentTier, abo, isGrace, etc. restent inchangés) ...

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-navy rounded-3xl p-8">
        <h1 className="text-3xl font-[300] text-white">
          {t("pack.title")}
        </h1>
        <p className="text-white/50 mt-2">
          {data?.niveau_scolaire
            ? t("pack.niveauLabel", { niveau: data.niveau_scolaire })
            : t("pack.manageSubscription")}
        </p>
      </div>

      {/* Messages */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-2xl p-4 flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0" />
          <p className="text-sm text-red-700">{error}</p>
          <button
            onClick={() => setError(null)}
            className="ml-auto text-red-400 hover:text-red-600"
          >
            <XCircle className="w-4 h-4" />
          </button>
        </div>
      )}
      {successMsg && (
        <div className="bg-green-50 border border-green-200 rounded-2xl p-4 flex items-center gap-3">
          <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0" />
          <p className="text-sm text-green-700">{successMsg}</p>
          <button
            onClick={() => setSuccessMsg(null)}
            className="ml-auto text-green-400 hover:text-green-600"
          >
            <XCircle className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* ── NOUVEAU : Bannière reconfiguration trimestrielle ── */}
      {!loading && trimester.currentTrimester && (
        <TrimesterReconfigBanner
          canReconfigure={trimester.canReconfigure}
          daysRemaining={trimester.daysRemainingInWindow}
          trimesterLabel={trimester.currentTrimester.label}
          onReconfigure={handleReconfigure}
        />
      )}

      {/* Grace period warning (existant) */}
      {isGrace && (
        <div className="bg-amber-50 border border-amber-200 rounded-2xl p-5 flex items-start gap-4">
          <AlertTriangle className="w-6 h-6 text-amber-500 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold text-amber-800">
              {t("pack.gracePeriodActive")}
            </h3>
            <p className="text-sm text-amber-700 mt-1">
              {t("pack.gracePeriodDesc", { days: daysLeft })}
            </p>
            {graceEnd && (
              <p className="text-xs text-amber-600 mt-2">
                {t("pack.graceEndsOn")} {graceEnd.toLocaleDateString("fr-TN")}
              </p>
            )}
          </div>
        </div>
      )}

      {/* Scheduled downgrade notification (existant) */}
      {scheduled && (
        <div className="bg-blue-50 border border-blue-200 rounded-2xl p-5 flex items-start gap-4">
          <Clock className="w-6 h-6 text-blue-500 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <h3 className="font-semibold text-blue-800">
              {t("pack.scheduledChange")}
            </h3>
            <p className="text-sm text-blue-700 mt-1">
              {t("pack.passageTo")}{" "}
              <span className="font-bold">
                {TIER_LABELS[scheduled.target_tier] || scheduled.target_tier}
              </span>{" "}
              {t("pack.on")} {scheduledDate?.toLocaleDateString("fr-TN")}
            </p>
            <p className="text-xs text-blue-600 mt-1">
              {t("pack.scheduledChangeNote")}
            </p>
          </div>
          <button
            onClick={handleCancelScheduled}
            disabled={actionLoading}
            className="px-3 py-1.5 text-xs font-medium text-blue-600 border border-blue-300 rounded-xl hover:bg-blue-100 disabled:opacity-50"
          >
            {t("pack.cancel")}
          </button>
        </div>
      )}

      {/* Current Pack */}
      {data?.current_pack && (
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-navy">
              {t("pack.activePack")}
            </h2>
            <span
              className={`px-3 py-1 text-xs font-semibold rounded-full border ${
                TIER_COLORS[currentTier] || "bg-gray-100 text-gray-600"
              }`}
            >
              {TIER_ICONS[currentTier]} {TIER_LABELS[currentTier] || currentTier}
            </span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <p className="text-xs text-gray-500">{t("pack.packLabel")}</p>
              <p className="text-sm font-medium text-navy">
                {data.current_pack.nom}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500">{t("pack.accessLabel")}</p>
              <p className="text-sm font-medium text-navy">
                {data.quota_info[currentTier] || "N/A"}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500">{t("pack.expirationLabel")}</p>
              <p className="text-sm font-medium text-navy">
                {abo?.fin
                  ? new Date(abo.fin).toLocaleDateString("fr-TN")
                  : "N/A"}
              </p>
            </div>
          </div>

          {/* ── NOUVEAU : Infos trimestre ── */}
          {trimester.currentTrimester && (
            <div className="mt-4 pt-4 border-t border-gray-100">
              <TrimesterInfo
                trimesterLabel={trimester.currentTrimester.label}
                startDate={trimester.currentTrimester.startDate}
                endDate={trimester.currentTrimester.endDate}
                isInWindow={trimester.isInReconfigWindow}
                alreadyReconfigured={trimester.alreadyReconfigured}
                packTier={currentTier}
              />
            </div>
          )}

          {/* ... features restent inchangées ... */}
          {data.current_pack.features && (
            <div className="mt-4 pt-4 border-t border-gray-100">
              <p className="text-xs text-gray-500 mb-2">
                {t("pack.includedFeatures")}
              </p>
              <div className="flex flex-wrap gap-2">
                {Object.entries(data.current_pack.features).map(
                  ([key, val]) => (
                    <span
                      key={key}
                      className="px-2 py-1 bg-gray-50 text-gray-600 text-xs rounded-full"
                    >
                      {key.replace(/_/g, " ")}: {String(val)}
                    </span>
                  )
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ... Available Packs et Quota Grid restent inchangés ... */}
    </div>
  );
}
```

---

# PARTIE 3 — CLÉS I18N

---

## 3.1 Clés à ajouter dans `fr.json`

```json
{
  "student": {
    "quota": {
      "title": "Quota Gratuit",
      "subtitle": "{{used}}/{{limit}} leçons utilisées ce trimestre",
      "exhaustedTitle": "Quota Épuisé",
      "exhaustedMessage": "Vous avez consommé votre quota gratuit du trimestre.",
      "exhaustedDescription": "Vous avez utilisé vos 3 leçons gratuites. Pour continuer à apprendre, découvrez nos offres d'abonnement.",
      "unlockBenefits": "En débloquant un pack, vous accédez à :",
      "benefit1": "L'accès illimité à toutes les leçons de vos matières",
      "benefit2": "L'IA avancée (exercices, génération de contenu)",
      "benefit3": "La reconfiguration trimestrielle de vos matières",
      "later": "Plus tard",
      "discoverPacks": "Découvrir les packs"
    },
    "trimester": {
      "badge": "{{label}}",
      "currentTrimester": "Trimestre {{label}}",
      "period": "Période",
      "reconfigStatus": "Reconfiguration",
      "newTrimester": "Nouveau trimestre {{trimester}} !",
      "reconfigDescription": "Vous pouvez modifier le choix de vos matières pour ce trimestre.",
      "daysRemaining": "{{count}} jour(s) restant(s) pour reconfigurer",
      "reconfigure": "Reconfigurer",
      "goldenNoNeed": "Pas nécessaire (pack Golden)",
      "freeNotEligible": "Non disponible (pack Gratuit)",
      "alreadyReconfigured": "Déjà reconfiguré ce trimestre",
      "windowOpen": "Fenêtre ouverte",
      "windowClosed": "Fenêtre fermée",
      "errorLoading": "Erreur lors du chargement des informations de trimestre"
    }
  }
}
```

## 3.2 Clés à ajouter dans `en.json`

```json
{
  "student": {
    "quota": {
      "title": "Free Quota",
      "subtitle": "{{used}}/{{limit}} lessons used this trimester",
      "exhaustedTitle": "Quota Exhausted",
      "exhaustedMessage": "You have used your free trimester quota.",
      "exhaustedDescription": "You've used your 3 free lessons. To keep learning, check out our subscription plans.",
      "unlockBenefits": "By unlocking a plan, you get:",
      "benefit1": "Unlimited access to all lessons in your subjects",
      "benefit2": "Advanced AI (exercises, content generation)",
      "benefit3": "Trimester subject reconfiguration",
      "later": "Later",
      "discoverPacks": "Discover Plans"
    },
    "trimester": {
      "badge": "{{label}}",
      "currentTrimester": "Trimester {{label}}",
      "period": "Period",
      "reconfigStatus": "Reconfiguration",
      "newTrimester": "New trimester {{trimester}}!",
      "reconfigDescription": "You can change your subject selection for this trimester.",
      "daysRemaining": "{{count}} day(s) remaining to reconfigure",
      "reconfigure": "Reconfigure",
      "goldenNoNeed": "Not needed (Golden plan)",
      "freeNotEligible": "Not available (Free plan)",
      "alreadyReconfigured": "Already reconfigured this trimester",
      "windowOpen": "Window open",
      "windowClosed": "Window closed",
      "errorLoading": "Error loading trimester information"
    }
  }
}
```

## 3.3 Clés à ajouter dans `ar.json`

```json
{
  "student": {
    "quota": {
      "title": "الحصة المجانية",
      "subtitle": "{{used}}/{{limit}} دروس مستخدمة هذا الفصل",
      "exhaustedTitle": "الحصة مستنفدت",
      "exhaustedMessage": "لقد استنفدت حصتك المجانية لهذا الفصل.",
      "exhaustedDescription": "لقد استخدمت دروسك المجانية الثلاثة. للمتابعة في التعلم، اكتشف خطط الاشتراك.",
      "unlockBenefits": "بفتح باقة، تحصل على:",
      "benefit1": "وصول غير محدود لجميع الدروس في موادك",
      "benefit2": "الذكاء الاصطناعي المتقدم (تمارين، إنشاء محتوى)",
      "benefit3": "إعادة تكوين المواد الفصلية",
      "later": "لاحقاً",
      "discoverPacks": "اكتشف الباقات"
    },
    "trimester": {
      "badge": "{{label}}",
      "currentTrimester": "الفصل {{label}}",
      "period": "الفترة",
      "reconfigStatus": "إعادة التكوين",
      "newTrimester": "فصل جديد {{trimester}}!",
      "reconfigDescription": "يمكنك تغيير اختيار موادك لهذا الفصل.",
      "daysRemaining": "{{count}} يوم (أيام) متبقية لإعادة التكوين",
      "reconfigure": "إعادة التكوين",
      "goldenNoNeed": "غير ضروري (باقة Golden)",
      "freeNotEligible": "غير متاح (باقة مجانية)",
      "alreadyReconfigured": "تمت إعادة التكوين بالفعل هذا الفصل",
      "windowOpen": "النافذة مفتوحة",
      "windowClosed": "النافذة مغلقة",
      "errorLoading": "خطأ في تحميل معلومات الفصل"
    }
  }
}
```

---

# PARTIE 4 — RÉSUMÉ DES FICHIERS

## Fichiers à créer

```
src/features/student/hooks/
  └── useQuotaGuard.ts
  └── useTrimesterReconfiguration.ts

src/features/student/components/
  ├── quota/
  │   ├── index.ts
  │   ├── QuotaGauge.tsx
  │   └── QuotaExhaustedModal.tsx
  └── trimester/
      ├── index.ts
      ├── TrimesterBadge.tsx
      ├── TrimesterReconfigBanner.tsx
      └── TrimesterInfo.tsx
```

## Fichiers à modifier

```
src/features/student/pages/
  ├── StudentDashboard.tsx       ← +useQuotaGuard, +QuotaGauge, +QuotaExhaustedModal
  └── StudentPackPage.tsx        ← +useTrimesterReconfiguration, +TrimesterReconfigBanner, +TrimesterInfo

src/i18n/locales/
  ├── fr.json                    ← +student.quota.*, +student.trimester.*
  ├── en.json                    ← +student.quota.*, +student.trimester.*
  └── ar.json                    ← +student.quota.*, +student.trimester.*
```

## Checklist de validation

| # | Critère | Status |
|---|---------|--------|
| 1 | Toute la logique métier est dans des Custom Hooks | ✅ |
| 2 | Aucun `fetch()` inline dans les composants | ✅ |
| 3 | Utilisation exclusive de `src/components/ui/` (Button, Modal, Spinner) | ✅ |
| 4 | Tous les textes utilisent `t()` avec la nomenclature `student.quota.*` / `student.trimester.*` | ✅ |
| 5 | Les hooks exposent un état clair (loading, error, data) | ✅ |
| 6 | Les composants sont purement UI (reçoivent des props, n'appellent pas d'API) | ✅ |
| 7 | barrel exports pour chaque dossier de composants | ✅ |
| 8 | Intégration propre dans les pages existantes (StudentDashboard, StudentPackPage) | ✅ |
| 9 | Note backend pour l'endpoint `/api/learner/free-quota` à implémenter | ✅ |
