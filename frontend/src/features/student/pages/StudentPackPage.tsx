import { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { useAuthStore } from "../../../store/authStore";
import { api } from "../../../utils/apiClient";
import { Package, AlertTriangle, CheckCircle, Clock, RefreshCw, ArrowUpCircle, ArrowDownCircle, XCircle, X, Check } from "lucide-react";
import { useTrimesterReconfiguration } from "../hooks/useTrimesterReconfiguration";
import { TrimesterReconfigBanner } from "../components/trimester/TrimesterReconfigBanner";
import { TrimesterInfo } from "../components/trimester/TrimesterInfo";
import { Button, EmptyState, PageWrapper } from "../../../components/ui";

interface MonPackData {
  current_tier: string;
  current_pack: {
    id: number;
    tier: string;
    nom: string;
    prix_tnd: number;
    niveau_scolaire: string;
    features: Record<string, any>;
    matieres: any;
  } | null;
  abonnement: {
    id: number;
    statut: string;
    debut: string;
    fin: string;
    grace_fin: string | null;
  } | null;
  available_packs: {
    id: number;
    tier: string;
    nom: string;
    prix_tnd: number;
    niveau_scolaire: string;
    features: Record<string, any>;
    matieres: any;
  }[];
  scheduled_change: {
    target_tier: string;
    effective_date: string;
  } | null;
  niveau_scolaire: string | null;
  quota_info: Record<string, string>;
}

const TIER_COLORS: Record<string, string> = {
  gratuit: "bg-gray-100 text-gray-700 border-gray-200",
  basique: "bg-blue-50 text-blue-700 border-blue-200",
  silver: "bg-gray-100 text-gray-600 border-gray-300",
  golden: "bg-amber-50 text-amber-700 border-amber-200",
};

const TIER_LABELS: Record<string, string> = {
  gratuit: "Gratuit",
  basique: "Basique",
  silver: "Silver",
  golden: "Golden",
};

const TIER_ICONS: Record<string, string> = {
  gratuit: "🎓",
  basique: "📘",
  silver: "🥈",
  golden: "🥇",
};

const FEATURE_LABELS: Record<string, string> = {
  ai_ask: "Questions au Tuteur IA",
  ai_quiz: "Génération de Quiz",
  ai_explain: "Explications IA",
  max_lessons_per_day: "Leçons / jour",
  max_quiz_per_day: "Quiz / jour",
  soft_skills: "Soft Skills",
  teacher_training: "Formation Enseignants",
  premium_content: "Contenu Premium",
  priority_support: "Support Prioritaire",
  analytics: "Analyses & Statistiques",
};

function formatFeatureValue(key: string, val: any): { label: string; enabled: boolean; display: string } {
  const label = FEATURE_LABELS[key] || key.replace(/_/g, " ");
  if (typeof val === "boolean") {
    return { label, enabled: val, display: "" };
  }
  return { label, enabled: true, display: String(val) };
}

export default function StudentPackPage() {
  const { t } = useTranslation();
  const { user } = useAuthStore();
  const [data, setData] = useState<MonPackData | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const trimester = useTrimesterReconfiguration();

  const fetchMonPack = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get<MonPackData>("/api/abonnements/mon-pack");
      setData(res);
    } catch (err: any) {
      setError(err.message || t('pack.loadingError'));
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchMonPack();
  }, [fetchMonPack]);

  const handleChangeTier = async (targetPackId: number) => {
    if (!data) return;
    setActionLoading(true);
    setError(null);
    setSuccessMsg(null);
    try {
      const res = await api.post<{ message: string; new_tier?: string; scheduled_tier?: string; effective_date?: string }>(
        "/api/abonnements/change-tier",
        { target_pack_id: targetPackId }
      );
      setSuccessMsg(res.message);
      await fetchMonPack();
    } catch (err: any) {
      setError(err.message || t('pack.changeError'));
    }
    setActionLoading(false);
  };

  const handleCancelScheduled = async () => {
    setActionLoading(true);
    setError(null);
    setSuccessMsg(null);
    try {
      const res = await api.delete<{ message: string }>("/api/abonnements/cancel-scheduled-change");
      setSuccessMsg(res.message);
      await fetchMonPack();
    } catch (err: any) {
      setError(err.message || t('pack.cancelError'));
    }
    setActionLoading(false);
  };

  const now = new Date();
  const currentTier = data?.current_tier || "gratuit";
  const abo = data?.abonnement;
  const isGrace = abo?.statut === "grace";
  const graceEnd = abo?.grace_fin ? new Date(abo.grace_fin) : null;
  const daysLeft = graceEnd ? Math.max(0, Math.ceil((graceEnd.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))) : 0;
  const scheduled = data?.scheduled_change;
  const scheduledDate = scheduled?.effective_date ? new Date(scheduled.effective_date) : null;

  const getTierRank = (tier: string) => ({ gratuit: 0, basique: 1, silver: 2, golden: 3 }[tier] ?? 0);

  const handleReconfigure = () => {
    window.location.href = "/dashboard/reconfigure-pack";
  };

  if (loading) {
    return (
      <PageWrapper title={t('pack.title')} icon={<Package className="w-8 h-8" />}>
        <div className="bg-white rounded-3xl p-8 animate-pulse">
          <div className="h-8 w-48 bg-gray-200 rounded mb-2" />
          <div className="h-4 w-64 bg-gray-100 rounded" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-white rounded-2xl p-6 shadow-sm border border-black/5 animate-pulse">
              <div className="h-5 w-32 bg-gray-200 rounded mb-3" />
              <div className="h-4 w-48 bg-gray-100 rounded mb-4" />
              <div className="h-8 w-24 bg-gray-200 rounded" />
            </div>
          ))}
        </div>
      </PageWrapper>
    );
  }

  return (
    <PageWrapper
      title={t('pack.title')}
      subtitle={data?.niveau_scolaire ? t('pack.niveauLabel', { niveau: data.niveau_scolaire }) : t('pack.manageSubscription')}
      icon={<Package className="w-8 h-8" />}
    >

      {/* Messages */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-2xl p-4 flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0" />
          <p className="text-sm text-red-700">{error}</p>
          <Button variant="ghost" size="sm" onClick={() => setError(null)}>
            <XCircle className="w-4 h-4" />
          </Button>
        </div>
      )}
      {successMsg && (
        <div className="bg-green-50 border border-green-200 rounded-2xl p-4 flex items-center gap-3">
          <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0" />
          <p className="text-sm text-green-700">{successMsg}</p>
          <Button variant="ghost" size="sm" onClick={() => setSuccessMsg(null)}>
            <XCircle className="w-4 h-4" />
          </Button>
        </div>
      )}

      {/* Trimester Reconfiguration Banner */}
      {!loading && trimester.currentTrimester && (
        <TrimesterReconfigBanner
          canReconfigure={trimester.canReconfigure}
          daysRemaining={trimester.daysRemainingInWindow}
          trimesterLabel={trimester.currentTrimester.label}
          onReconfigure={handleReconfigure}
        />
      )}

      {/* Grace period warning */}
      {isGrace && (
        <div className="bg-amber-50 border border-amber-200 rounded-2xl p-5 flex items-start gap-4">
          <AlertTriangle className="w-6 h-6 text-amber-500 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold text-amber-800">{t('pack.gracePeriodActive')}</h3>
            <p className="text-sm text-amber-700 mt-1">
              {t('pack.gracePeriodDesc', { days: daysLeft })}
            </p>
            {graceEnd && (
              <p className="text-xs text-amber-600 mt-2">
                {t('pack.graceEndsOn')} {graceEnd.toLocaleDateString("fr-TN")}
              </p>
            )}
          </div>
        </div>
      )}

      {/* Scheduled downgrade notification */}
      {scheduled && (
        <div className="bg-blue-50 border border-blue-200 rounded-2xl p-5 flex items-start gap-4">
          <Clock className="w-6 h-6 text-blue-500 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <h3 className="font-semibold text-blue-800">{t('pack.scheduledChange')}</h3>
            <p className="text-sm text-blue-700 mt-1">
              {t('pack.passageTo')}{" "}
              <span className="font-bold">{TIER_LABELS[scheduled.target_tier] || scheduled.target_tier}</span>{" "}
              {t('pack.on')} {scheduledDate?.toLocaleDateString("fr-TN")}
            </p>
            <p className="text-xs text-blue-600 mt-1">
              {t('pack.scheduledChangeNote')}
            </p>
          </div>
          <Button
            variant="secondary"
            size="sm"
            onClick={handleCancelScheduled}
            disabled={actionLoading}
          >
            {t('pack.cancel')}
          </Button>
        </div>
      )}

      {/* Current Pack */}
      {data?.current_pack && abo?.statut !== "invalide" ? (
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-navy">{t('pack.activePack')}</h2>
            <span className={`px-3 py-1 text-xs font-semibold rounded-full border ${TIER_COLORS[currentTier] || "bg-gray-100 text-gray-600"}`}>
              {TIER_ICONS[currentTier]} {TIER_LABELS[currentTier] || currentTier}
            </span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <p className="text-xs text-gray-500">{t('pack.packLabel')}</p>
              <p className="text-sm font-medium text-navy">{data.current_pack.nom}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">{t('pack.accessLabel')}</p>
              <p className="text-sm font-medium text-navy">{data.quota_info[currentTier] || "N/A"}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">{t('pack.expirationLabel')}</p>
              <p className="text-sm font-medium text-navy">
                {abo?.fin ? new Date(abo.fin).toLocaleDateString("fr-TN") : "N/A"}
              </p>
            </div>
          </div>
          {/* Trimester Info */}
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
          {data.current_pack.features && Object.keys(data.current_pack.features).length > 0 && (
            <div className="mt-4 pt-4 border-t border-gray-100">
              <p className="text-xs text-gray-500 mb-2">{t('pack.includedFeatures')}</p>
              <div className="space-y-1.5">
                {Object.entries(data.current_pack.features).map(([key, val]) => {
                  const feat = formatFeatureValue(key, val);
                  return (
                    <div key={key} className="flex items-center gap-2">
                      {feat.enabled ? (
                        <Check className="w-3.5 h-3.5 text-green-500 flex-shrink-0" />
                      ) : (
                        <X className="w-3.5 h-3.5 text-gray-300 flex-shrink-0" />
                      )}
                      <span className={`text-sm ${feat.enabled ? "text-navy" : "text-gray-400 line-through"}`}>
                        {feat.label}
                        {feat.display && <span className="text-gray-400 ml-1">({feat.display})</span>}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="bg-amber-50 border border-amber-200 rounded-2xl p-6 text-center">
          <AlertTriangle className="w-8 h-8 text-amber-500 mx-auto mb-3" />
          <h3 className="font-semibold text-amber-800 mb-1">{t('pack.noActivePack')}</h3>
          <p className="text-sm text-amber-700">{t('pack.noActivePackDesc')}</p>
        </div>
      )}

      {/* Available Packs scoped by niveau_scolaire */}
      <div>
        <h2 className="text-lg font-semibold text-navy mb-4">
          {t('pack.changePack')}
          {data?.niveau_scolaire && (
            <span className="text-sm font-normal text-gray-400 ms-2">({data.niveau_scolaire})</span>
          )}
        </h2>
        {data?.available_packs && data.available_packs.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {data.available_packs.map((pack) => {
              const isActive = data.current_pack?.id === pack.id;
              const isScheduled = scheduled?.target_tier === pack.tier;
              const targetRank = getTierRank(pack.tier);
              const currentRank = getTierRank(currentTier);
              const isUpgrade = targetRank > currentRank;
              const isDowngrade = targetRank < currentRank;

              return (
                <div
                  key={pack.id}
                  className={`bg-white rounded-2xl p-6 shadow-sm border transition-all ${
                    isActive ? "border-orange/30 ring-2 ring-orange/10" : "border-black/5 hover:shadow-md"
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-semibold text-navy">
                      {TIER_ICONS[pack.tier]} {pack.nom}
                    </h3>
                    <span className={`px-2 py-0.5 text-xs font-semibold rounded-full border ${TIER_COLORS[pack.tier] || "bg-gray-100"}`}>
                      {TIER_LABELS[pack.tier] || pack.tier}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 mb-1">{pack.niveau_scolaire}</p>
                  <p className="text-xs text-gray-400 mb-3">{data.quota_info[pack.tier] || ""}</p>

                  <div className="flex items-center justify-between pt-3 border-t border-gray-100">
                    <span className="text-xl font-[300] text-navy">
                      {pack.prix_tnd} <span className="text-sm text-gray-400">TND</span>
                    </span>
                    <div>
                      {isActive ? (
                        <span className="px-3 py-1.5 bg-green-100 text-green-700 text-xs font-medium rounded-xl flex items-center gap-1">
                          <CheckCircle className="w-3 h-3" /> {t('pack.active')}
                        </span>
                      ) : isScheduled ? (
                        <span className="px-3 py-1.5 bg-blue-100 text-blue-700 text-xs font-medium rounded-xl flex items-center gap-1">
                          <Clock className="w-3 h-3" /> {t('pack.scheduled')}
                        </span>
                      ) : isUpgrade ? (
                        <Button
                          variant="primary"
                          size="sm"
                          onClick={() => handleChangeTier(pack.id)}
                          disabled={actionLoading}
                        >
                          <ArrowUpCircle className="w-3 h-3" /> {t('pack.upgrade')}
                        </Button>
                      ) : isDowngrade ? (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleChangeTier(pack.id)}
                          disabled={actionLoading}
                        >
                          <ArrowDownCircle className="w-3 h-3" />
                        </Button>
                      ) : null}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <EmptyState
            icon={<Package className="w-12 h-12" />}
            title={
              data?.niveau_scolaire
                ? t('pack.noPacksForLevel', { level: data.niveau_scolaire })
                : t('pack.noPacksAvailable')
            }
          />
        )}
      </div>

      {/* Quota grid */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
        <h2 className="text-lg font-semibold text-navy mb-3">{t('pack.packGrid')}</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          {(["gratuit", "basique", "silver", "golden"] as const).map((tier) => (
            <div key={tier} className={`p-4 rounded-xl ${currentTier === tier ? "ring-2 ring-orange bg-orange/5" : "bg-gray-50"}`}>
              <h3 className="font-semibold text-navy text-sm">{TIER_ICONS[tier]} {TIER_LABELS[tier]}</h3>
              <p className="text-xs text-gray-500 mt-1">{data?.quota_info[tier] || ""}</p>
              {currentTier === tier && (
                <span className="inline-block mt-2 px-2 py-0.5 bg-orange/10 text-orange text-xs rounded-full font-medium">
                  {t('pack.current')}
                </span>
              )}
              {scheduled?.target_tier === tier && (
                <span className="inline-block mt-2 px-2 py-0.5 bg-blue-100 text-blue-600 text-xs rounded-full font-medium">
                  {t('pack.scheduled')}
                </span>
              )}
            </div>
          ))}
        </div>
      </div>
    </PageWrapper>
  );
}
