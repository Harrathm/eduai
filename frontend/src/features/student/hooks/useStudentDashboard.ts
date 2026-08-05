import { useState, useEffect, useCallback, useRef } from "react";
import {
  tierApi, abonnementApi, walletApi, inboxApi, catalogApi,
  type DashboardData, type Abonnement, type WalletBalance, type CatalogCourse,
} from "../../../api";
import type { InboxMessage } from "../../../api/inboxApi";
import { useTrimesterReconfiguration } from "./useTrimesterReconfiguration";

const FREE_QUOTA_LIMIT = 3;

interface QuotaState {
  tier: string | null;
  used: number;
  limit: number;
  remaining: number;
  percent: number;
  exhausted: boolean;
  isNotFree: boolean;
  error: string | null;
}

export interface LastLesson {
  title: string;
  courseTitle: string;
  progressPct: number;
}

interface StudentDashboardData {
  dashboard: DashboardData | null;
  packTier: string | null;
  abonnement: Abonnement | null;
  wallet: WalletBalance | null;
  unreadCount: number;
  lastMessage: InboxMessage | null;
  softSkillsCourses: CatalogCourse[];
  availablePacks: { id: number; name: string; tier: string; price: number; description: string | null }[];
  quota: QuotaState;
  loading: boolean;
  error: string | null;
  lastLesson: LastLesson | null;
  learningTimeMinutes: number;
  averageScore: number;
}

function computeQuota(dashboard: DashboardData | null): QuotaState {
  if (!dashboard) return { tier: null, used: 0, limit: FREE_QUOTA_LIMIT, remaining: FREE_QUOTA_LIMIT, percent: 0, exhausted: false, isNotFree: false, error: null };
  const tier = dashboard.tier;
  const used = (dashboard as any).free_lessons_used ?? dashboard.lessons_completed;
  const remaining = Math.max(0, FREE_QUOTA_LIMIT - used);
  const percent = Math.min(100, Math.round((used / FREE_QUOTA_LIMIT) * 100));
  const exhausted = used >= FREE_QUOTA_LIMIT;
  const isNotFree = tier !== null && tier !== "decouverte";
  return { tier, used, limit: FREE_QUOTA_LIMIT, remaining, percent, exhausted, isNotFree, error: null };
}

export function useStudentDashboard() {
  const [data, setData] = useState<StudentDashboardData>({
    dashboard: null,
    packTier: null,
    abonnement: null,
    wallet: null,
    unreadCount: 0,
    lastMessage: null,
    softSkillsCourses: [],
    availablePacks: [],
    quota: { tier: null, used: 0, limit: FREE_QUOTA_LIMIT, remaining: FREE_QUOTA_LIMIT, percent: 0, exhausted: false, isNotFree: false, error: null },
    loading: true,
    error: null,
    lastLesson: null,
    learningTimeMinutes: 0,
    averageScore: 0,
  });
  const mountedRef = useRef(true);
  const trimester = useTrimesterReconfiguration();

  const fetchData = useCallback(async () => {
    setData((prev) => ({ ...prev, loading: true, error: null }));
    try {
      // ── APPEL UNIQUE : 6 endpoints en parallèle, /api/learner/dashboard 1 fois ──
      const [dashData, aboData, walletData, inboxData, softData, packsData] = await Promise.all([
        tierApi.dashboard(),                                    // ← UNIQUE appel à /api/learner/dashboard
        abonnementApi.mesAbonnements().catch(() => []),
        walletApi.balance().catch(() => null),
        inboxApi.list({ unread_only: false }).catch(() => []),
        catalogApi.list({ category: "soft_skills", limit: 3 }).catch(() => []),
        abonnementApi.listPacks().catch(() => []),
      ]);

      if (!mountedRef.current) return;

      const activeAbo = Array.isArray(aboData)
        ? aboData.find((a) => a.status === "active" || a.status === "grace")
        : null;

      const nivelScolaire = (dashData as any).niveau_scolaire || null;
      const filteredPacks = nivelScolaire
        ? packsData.filter((p: any) => !p.niveau_scolaire || p.niveau_scolaire === nivelScolaire)
        : packsData;

      const messages = Array.isArray(inboxData) ? inboxData : [];
      const unread = messages.filter((m) => !m.is_read).length;

      // Mock data — will be replaced by real backend endpoints
      const mockLastLesson = dashData.courses && dashData.courses.length > 0
        ? (() => {
            const last = dashData.courses.reduce((a, b) =>
              (a.progress_pct ?? 0) > (b.progress_pct ?? 0) ? a : b
            );
            return {
              title: last.title || "Dernière leçon",
              courseTitle: last.title,
              progressPct: last.progress_pct ?? 0,
            };
          })()
        : null;
      const mockLearningTime = Math.round((dashData.lessons_completed ?? 0) * 12);
      const mockAvgScore = dashData.overall_progress_pct ?? 0;

      setData({
        dashboard: dashData,
        packTier: activeAbo?.tier || null,
        abonnement: activeAbo || null,
        wallet: walletData,
        unreadCount: unread,
        lastMessage: messages[0] || null,
        softSkillsCourses: Array.isArray(softData) ? softData.slice(0, 3) : [],
        availablePacks: filteredPacks.slice(0, 3),
        quota: computeQuota(dashData),
        loading: false,
        error: null,
        lastLesson: mockLastLesson,
        learningTimeMinutes: mockLearningTime,
        averageScore: mockAvgScore,
      });
    } catch (err: any) {
      if (mountedRef.current) {
        setData((prev) => ({
          ...prev,
          loading: false,
          error: err.message || "Erreur lors du chargement",
        }));
      }
    } finally {
      if (mountedRef.current) {
        setData((prev) => ({ ...prev, loading: false }));
      }
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    fetchData();
    return () => { mountedRef.current = false; };
  }, [fetchData]);

  const isFreePack = data.packTier === "gratuit" || data.packTier === null;
  const isBasicOrSilver = data.packTier === "basique" || data.packTier === "silver";
  const isGolden = data.packTier === "golden";

  const matieresCount = data.dashboard?.courses?.length ?? 0;
  const globalProgress = data.dashboard?.overall_progress_pct ?? 0;

  return {
    ...data,
    trimester,
    isFreePack,
    isBasicOrSilver,
    isGolden,
    matieresCount,
    globalProgress,
    lastLesson: data.lastLesson,
    learningTimeMinutes: data.learningTimeMinutes,
    averageScore: data.averageScore,
    refresh: fetchData,
  };
}
