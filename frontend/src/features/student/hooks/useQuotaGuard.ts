import { useState, useEffect, useCallback, useRef } from "react";
import { tierApi, type DashboardData } from "../../../api";

const FREE_QUOTA_LIMIT = 3;

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
    return () => { mountedRef.current = false; };
  }, [fetchQuota]);

  const isNotFree = tier !== null && tier !== "decouverte";
  const remaining = Math.max(0, FREE_QUOTA_LIMIT - used);
  const percent = Math.min(100, Math.round((used / FREE_QUOTA_LIMIT) * 100));
  const exhausted = used >= FREE_QUOTA_LIMIT;

  return { tier, used, limit: FREE_QUOTA_LIMIT, remaining, percent, exhausted, isNotFree, loading, error, refresh: fetchQuota };
}
