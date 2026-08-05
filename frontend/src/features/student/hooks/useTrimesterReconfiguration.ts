import { useState, useEffect, useCallback, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { api } from "../../../utils/apiClient";

interface TrimesterDateRange {
  label: string;
  start: { month: number; day: number };
  end: { month: number; day: number };
  reconfigWindowDays: number;
}

const TRIMESTER_CALENDAR: TrimesterDateRange[] = [
  { label: "T1", start: { month: 9, day: 15 }, end: { month: 12, day: 19 }, reconfigWindowDays: 15 },
  { label: "T2", start: { month: 1, day: 5 }, end: { month: 3, day: 27 }, reconfigWindowDays: 15 },
  { label: "T3", start: { month: 4, day: 6 }, end: { month: 6, day: 19 }, reconfigWindowDays: 15 },
];

interface MonPackData {
  current_tier: string;
  current_pack: { id: number; tier: string; nom: string; matieres: any } | null;
  abonnement: { id: number; statut: string; debut: string; fin: string } | null;
  niveau_scolaire: string | null;
}

interface TrimesterInfo {
  label: string;
  number: number;
  startDate: Date;
  endDate: Date;
}

export interface UseTrimesterReconfigurationReturn {
  currentTrimester: TrimesterInfo | null;
  isInReconfigWindow: boolean;
  daysRemainingInWindow: number;
  isEligible: boolean;
  isGolden: boolean;
  isFree: boolean;
  alreadyReconfigured: boolean;
  canReconfigure: boolean;
  loading: boolean;
  error: string | null;
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

  useEffect(() => { fetchPack(); }, [fetchPack]);

  const currentTrimester = useMemo((): TrimesterInfo | null => {
    const now = new Date();
    const cm = now.getMonth() + 1;
    const cd = now.getDate();
    for (let i = 0; i < TRIMESTER_CALENDAR.length; i++) {
      const cal = TRIMESTER_CALENDAR[i];
      const inRange = cm > cal.start.month || (cm === cal.start.month && cd >= cal.start.day)
        ? (cm < cal.end.month || (cm === cal.end.month && cd <= cal.end.day))
        : false;
      if (inRange) {
        return {
          label: cal.label,
          number: i + 1,
          startDate: new Date(now.getFullYear(), cal.start.month - 1, cal.start.day),
          endDate: new Date(now.getFullYear(), cal.end.month - 1, cal.end.day),
        };
      }
    }
    return null;
  }, []);

  const reconfigWindowState = useMemo(() => {
    if (!currentTrimester) return { isInWindow: false, daysRemaining: 0 };
    const now = new Date();
    const diffDays = Math.floor((now.getTime() - currentTrimester.startDate.getTime()) / (1000 * 60 * 60 * 24));
    const windowDays = TRIMESTER_CALENDAR[currentTrimester.number - 1].reconfigWindowDays;
    if (diffDays < 0) return { isInWindow: false, daysRemaining: 0 };
    if (diffDays < windowDays) return { isInWindow: true, daysRemaining: windowDays - diffDays };
    return { isInWindow: false, daysRemaining: 0 };
  }, [currentTrimester]);

  const currentTier = packData?.current_tier || "gratuit";
  const packTier = packData?.current_pack?.tier || "gratuit";
  const isGolden = packTier === "golden";
  const isFree = currentTier === "decouverte" || packTier === "gratuit";
  const isEligible = !isGolden && !isFree;
  const alreadyReconfigured = false;
  const canReconfigure = isEligible && reconfigWindowState.isInWindow && !alreadyReconfigured && !loading;

  return {
    currentTrimester,
    isInReconfigWindow: reconfigWindowState.isInWindow,
    daysRemainingInWindow: reconfigWindowState.daysRemaining,
    isEligible, isGolden, isFree, alreadyReconfigured, canReconfigure, loading, error, refresh: fetchPack,
  };
}
