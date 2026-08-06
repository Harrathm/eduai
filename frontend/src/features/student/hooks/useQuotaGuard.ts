import { useState, useEffect, useCallback, useRef } from "react";
import { tierApi, abonnementApi, type DashboardData } from "../../../api";

const FREE_QUOTA_LIMIT = 3;
const PAID_TIERS = ["basique", "basic", "silver", "golden"];

interface UseQuotaGuardReturn {
  tier: string | null;
  used: number;
  limit: number;
  remaining: number;
  percent: number;
  exhausted: boolean;
  isNotFree: boolean;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

export function useQuotaGuard(): UseQuotaGuardReturn {
  const [tier, setTier] = useState<string | null>(null);
  const [used, setUsed] = useState(0);
  const [isPaid, setIsPaid] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const mountedRef = useRef(true);

  const fetchQuota = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [dashData, aboData] = await Promise.allSettled([
        tierApi.dashboard(),
        abonnementApi.mesAbonnements(),
      ]);
      if (!mountedRef.current) return;

      const dashboard: DashboardData | null = dashData.status === "fulfilled" ? dashData.value : null;
      if (dashData.status === "rejected") {
        setError(dashData.reason?.message || "Erreur lors du chargement du quota");
      }

      setTier(dashboard?.tier || null);
      const freeUsed = (dashboard as any)?.free_lessons_used ?? dashboard?.lessons_completed ?? 0;
      setUsed(freeUsed);

      const aboList = aboData.status === "fulfilled" && Array.isArray(aboData.value) ? aboData.value : [];
      console.log("DEBUG ABO (QuotaGuard) - aboList:", aboList);
      const activeAbo = aboList.find((a: any) => a.statut === "actif" || a.statut === "grace");
      console.log("DEBUG ABO (QuotaGuard) - activeAbo:", activeAbo);
      const aboTier = (activeAbo as any)?.pack?.tier || activeAbo?.tier || null;
      console.log("DEBUG ABO (QuotaGuard) - aboTier:", aboTier);
      setIsPaid(aboTier ? PAID_TIERS.includes(aboTier.toLowerCase()) : false);
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
    return () => { mountedRef.current = false; };
  }, [fetchQuota]);

  if (isPaid) {
    return { tier, used: 0, limit: Infinity, remaining: Infinity, percent: 0, exhausted: false, isNotFree: true, loading, error, refresh: fetchQuota };
  }

  const isNotFree = tier !== null && tier !== "decouverte";
  const remaining = Math.max(0, FREE_QUOTA_LIMIT - used);
  const percent = Math.min(100, Math.round((used / FREE_QUOTA_LIMIT) * 100));
  const exhausted = used >= FREE_QUOTA_LIMIT;

  return { tier, used, limit: FREE_QUOTA_LIMIT, remaining, percent, exhausted, isNotFree, loading, error, refresh: fetchQuota };
}
