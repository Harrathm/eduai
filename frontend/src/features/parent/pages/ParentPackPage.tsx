import { useState, useEffect } from "react";
import { useTranslation } from 'react-i18next';
import { useParams, Link } from "react-router-dom";
import { useAuthStore } from "../../../store/authStore";
import { ArrowLeft, Package, AlertTriangle, CheckCircle } from "lucide-react";

interface ChildInfo {
  eleve_id: number;
  full_name: string;
  niveau_scolaire: string;
}

interface Abonnement {
  id: number;
  statut: string;
  debut: string;
  fin: string;
  grace_fin: string | null;
  pack: {
    id: number;
    tier: string;
    nom: string;
    prix_tnd: number;
    niveau_scolaire: string;
    features: Record<string, any>;
  };
}

const TIER_KEYS: Record<string, string> = {
  gratuit: "parent.pack.tiers.gratuit", basique: "parent.pack.tiers.basique", silver: "parent.pack.tiers.silver", golden: "parent.pack.tiers.golden",
};
const TIER_COLORS: Record<string, string> = {
  gratuit: "bg-gray-100 text-gray-700",
  basique: "bg-blue-100 text-blue-700",
  silver: "bg-gray-200 text-gray-700",
  golden: "bg-amber-100 text-amber-700",
};

export default function ParentPackPage() {
  const { t } = useTranslation();
  const { eleveId } = useParams();
  const { token } = useAuthStore();
  const [childInfo, setChildInfo] = useState<ChildInfo | null>(null);
  const [abonnements, setAbonnements] = useState<Abonnement[]>([]);
  const [availablePacks, setAvailablePacks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const childId = Number(eleveId);

  useEffect(() => {
    fetchData();
  }, [childId, token]);

  const fetchData = async () => {
    if (!token || !childId) return;
    setLoading(true);
    try {
      const [enfantsRes, aboRes, packsRes] = await Promise.all([
        fetch("/api/parents/me/enfants", { headers: { Authorization: `Bearer ${token}` } }),
        // Écart#2 FIX — demander les abonnements de l'ENFANT consulté
        // (sans eleve_id l'API renvoyait ceux du parent, toujours vides).
        fetch(`/api/abonnements/mes-abonnements?eleve_id=${childId}`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch("/api/abonnements/packs", { headers: { Authorization: `Bearer ${token}` } }),
      ]);
      if (enfantsRes.ok) {
        const data = await enfantsRes.json();
        const child = (data.enfants || []).find((e: any) => e.eleve_id === childId);
        if (child) setChildInfo(child);
      }
      if (aboRes.ok) {
        const data = await aboRes.json();
        setAbonnements(data.items || []);
      }
      if (packsRes.ok) {
        const data = await packsRes.json();
        setAvailablePacks(Array.isArray(data) ? data : data.items || []);
      }
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const childAbo = abonnements.find((a) => a.statut === "actif" || a.statut === "grace");
  const now = new Date();
  const isGrace = childAbo?.statut === "grace";
  const graceEnd = childAbo?.grace_fin ? new Date(childAbo.grace_fin) : null;
  const daysLeft = graceEnd ? Math.max(0, Math.ceil((graceEnd.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))) : 0;

  const QUOTA_KEYS: Record<string, string> = {
    gratuit: "parent.pack.features.freeQuota",
    basique: "parent.pack.features.basicQuota",
    silver: "parent.pack.features.silverQuota",
    golden: "parent.pack.features.goldenQuota",
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-10 w-48 bg-gray-200 rounded animate-pulse" />
        <div className="h-32 bg-gray-100 rounded animate-pulse" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Link to="/dashboard/parent" className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-navy">
        <ArrowLeft className="w-4 h-4" /> {t('parent.pack.backButton')}
      </Link>

      <div className="bg-navy rounded-3xl p-8">
        <h1 className="text-3xl font-[300] text-white">
          {t('parent.pack.title')} <span className="italic text-orange-l">{childInfo?.full_name || "l'enfant"}</span>
        </h1>
        <p className="text-white/50 mt-2">
            {childInfo?.niveau_scolaire || ""} — {t('parent.pack.subtitle')}
        </p>
      </div>

      {/* Grace warning */}
      {isGrace && (
        <div className="bg-amber-50 border border-amber-200 rounded-2xl p-5 flex items-start gap-4">
          <AlertTriangle className="w-6 h-6 text-amber-500 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold text-amber-800">{t('parent.pack.gracePeriod')}</h3>
            <p className="text-sm text-amber-700 mt-1">
              {t('parent.pack.graceMessage')} <span className="font-bold">{daysLeft} {t('parent.pack.graceDays')}</span>.
              {t('parent.pack.graceHint')}
            </p>
          </div>
        </div>
      )}

      {/* Current Pack */}
      {childAbo && (
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-navy flex items-center gap-2">
              <Package className="w-5 h-5" /> {t('parent.pack.activePack')}
            </h2>
            <span className={`px-3 py-1 text-xs font-semibold rounded-full ${TIER_COLORS[childAbo.pack?.tier] || "bg-gray-100"}`}>
              {t(TIER_KEYS[childAbo.pack?.tier] || childAbo.pack?.tier)}
            </span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <p className="text-xs text-gray-500">{t('parent.pack.packLabel')}</p>
              <p className="font-medium text-navy">{childAbo.pack?.nom}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">{t('parent.pack.accessLabel')}</p>
              <p className="font-medium text-navy">{t(QUOTA_KEYS[childAbo.pack?.tier] || "N/A")}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">{t('parent.pack.expirationLabel')}</p>
              <p className="font-medium text-navy">{new Date(childAbo.fin).toLocaleDateString("fr-TN")}</p>
            </div>
          </div>
        </div>
      )}

      {/* Available Packs */}
      <div>
        <h2 className="text-lg font-semibold text-navy mb-4">{t('parent.pack.availablePacksFor')} {childInfo?.niveau_scolaire || t('parent.pack.levelLabel')}</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {availablePacks
            .filter((p) => !childInfo?.niveau_scolaire || p.niveau_scolaire === childInfo.niveau_scolaire)
            .map((pack) => {
              const isActive = childAbo?.pack?.id === pack.id;
              return (
                <div key={pack.id} className={`bg-white rounded-2xl p-6 shadow-sm border ${isActive ? "border-orange/30" : "border-black/5"}`}>
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-semibold text-navy">{pack.nom || pack.name}</h3>
                    <span className={`px-2 py-0.5 text-xs font-semibold rounded-full ${TIER_COLORS[pack.tier] || "bg-gray-100"}`}>
                      {t(TIER_KEYS[pack.tier] || pack.tier)}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 mb-3">{pack.niveau_scolaire}</p>
                  <div className="flex items-center justify-between pt-3 border-t border-gray-100">
                    <span className="text-xl font-[300] text-navy">{pack.prix_tnd || pack.price || 0} <span className="text-sm text-gray-400">TND</span></span>
                    {isActive ? (
                      <span className="px-3 py-1.5 bg-green-100 text-green-700 text-xs font-medium rounded-xl flex items-center gap-1">
                        <CheckCircle className="w-3.5 h-3.5" /> {t('parent.pack.activeStatus')}
                      </span>
                    ) : (
                      <Link to="/dashboard/packs" className="px-3 py-1.5 bg-navy text-white text-xs font-medium rounded-xl hover:bg-navy/90 inline-block">
                        {t('parent.pack.subscribeButton')}
                      </Link>
                    )}
                  </div>
                </div>
              );
            })}
        </div>
      </div>
    </div>
  );
}
