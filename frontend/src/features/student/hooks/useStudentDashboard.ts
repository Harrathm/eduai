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

export interface SourceErrors {
  dashboard: string | null;
  abonnement: string | null;
  wallet: string | null;
  inbox: string | null;
  softSkills: string | null;
  packs: string | null;
}

interface StudentDashboardData {
  dashboard: DashboardData | null;
  packTier: string | null;
  abonnement: Abonnement | null;
  wallet: WalletBalance | null;
  unreadCount: number;
  lastMessage: InboxMessage | null;
  softSkillsCourses: CatalogCourse[];
  availablePacks: { id: number; nom: string; tier: string; prix_tnd: number; description: string | null }[];
  quota: QuotaState;
  loading: boolean;
  error: string | null;
  sourceErrors: SourceErrors;
  lastLesson: LastLesson | null;
  learningTimeMinutes: number;
  averageScore: number;
}

const PAID_TIERS = ["basique", "basic", "silver", "golden"];

function computeQuota(dashboard: DashboardData | null, activeAbo: Abonnement | null): QuotaState {
  if (!dashboard) return { tier: null, used: 0, limit: FREE_QUOTA_LIMIT, remaining: FREE_QUOTA_LIMIT, percent: 0, exhausted: false, isNotFree: false, error: null };
  const tier = dashboard.tier;
  const used = (dashboard as any).free_lessons_used ?? dashboard.lessons_completed;

  const aboTier = (activeAbo as any)?.pack?.tier || activeAbo?.tier || null;
  const isPaid = aboTier !== null && PAID_TIERS.includes(aboTier.toLowerCase());

  if (isPaid) {
    return { tier: aboTier, used: 0, limit: Infinity, remaining: Infinity, percent: 0, exhausted: false, isNotFree: true, error: null };
  }

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
    sourceErrors: { dashboard: null, abonnement: null, wallet: null, inbox: null, softSkills: null, packs: null },
    lastLesson: null,
    learningTimeMinutes: 0,
    averageScore: 0,
  });
  const mountedRef = useRef(true);
  const trimester = useTrimesterReconfiguration();

  const fetchData = useCallback(async () => {
    setData((prev) => ({ ...prev, loading: true, error: null }));

    const sourceErrors: SourceErrors = { dashboard: null, abonnement: null, wallet: null, inbox: null, softSkills: null, packs: null };

    // ── 6 endpoints en parallèle, CHACUN avec .catch() ──
    const [dashResult, aboResult, walletResult, inboxResult, softResult, packsResult] = await Promise.allSettled([
      tierApi.dashboard(),
      abonnementApi.mesAbonnements(),
      walletApi.balance(),
      inboxApi.list({ unread_only: false }),
      catalogApi.list({ category: "soft_skills", limit: 3 }),
      abonnementApi.listPacks(),
    ]);

    if (!mountedRef.current) return;

    // Extract values or set per-source errors
    const dashData = dashResult.status === "fulfilled" ? dashResult.value : null;
    if (dashResult.status === "rejected") sourceErrors.dashboard = dashResult.reason?.message || "Erreur dashboard";

    const aboData = aboResult.status === "fulfilled" ? aboResult.value : null;
    if (aboResult.status === "rejected") sourceErrors.abonnement = aboResult.reason?.message || "Erreur abonnements";

    const walletData = walletResult.status === "fulfilled" ? walletResult.value : null;
    if (walletResult.status === "rejected") sourceErrors.wallet = walletResult.reason?.message || "Erreur portefeuille";

    const inboxData = inboxResult.status === "fulfilled" ? inboxResult.value : null;
    if (inboxResult.status === "rejected") sourceErrors.inbox = inboxResult.reason?.message || "Erreur messages";

    const softData = softResult.status === "fulfilled" ? softResult.value : null;
    if (softResult.status === "rejected") sourceErrors.softSkills = softResult.reason?.message || "Erreur soft skills";

    const packsData = packsResult.status === "fulfilled" ? packsResult.value : null;
    if (packsResult.status === "rejected") sourceErrors.packs = packsResult.reason?.message || "Erreur packs";

    // ── Process abonnements ──
    const aboList = Array.isArray(aboData) ? aboData : [];
    console.log("DEBUG ABO - aboList:", aboList);
    const activeAbo = aboList.find((a: any) => a.statut === "actif" || a.statut === "grace") || null;
    console.log("DEBUG ABO - activeAbo:", activeAbo);
    console.log("DEBUG ABO - activeAbo.pack?.tier:", (activeAbo as any)?.pack?.tier);

    // ── Process inbox ──
    const messages = Array.isArray(inboxData) ? inboxData : [];
    const unread = messages.filter((m: any) => !m.is_read).length;

    // ── Process soft skills ──
    const rawSoft = Array.isArray(softData) ? softData : ((softData as any)?.items || (softData as any)?.courses || []);

    // ── Process packs ──
    const rawPacks = Array.isArray(packsData) ? packsData : ((packsData as any)?.items || []);
    const nivelScolaire = dashData?.niveau_scolaire || null;
    const filteredPacks = nivelScolaire
      ? rawPacks.filter((p: any) => !p.niveau_scolaire || p.niveau_scolaire === nivelScolaire)
      : rawPacks;

    // ── Process dashboard-derived data (null-safe) ──
    const mockLastLesson = dashData?.courses && dashData.courses.length > 0
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
    const mockLearningTime = Math.round((dashData?.lessons_completed ?? 0) * 12);
    const mockAvgScore = dashData?.overall_progress_pct ?? 0;

    setData({
      dashboard: dashData,
      packTier: activeAbo?.tier || null,
      abonnement: activeAbo || null,
      wallet: walletData,
      unreadCount: unread,
      lastMessage: messages[0] || null,
      softSkillsCourses: rawSoft.slice(0, 3),
      availablePacks: filteredPacks.slice(0, 3),
      quota: computeQuota(dashData, activeAbo),
      loading: false,
      error: null,
      sourceErrors,
      lastLesson: mockLastLesson,
      learningTimeMinutes: mockLearningTime,
      averageScore: mockAvgScore,
    });
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
