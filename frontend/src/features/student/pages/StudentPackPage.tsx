import { useState, useEffect } from "react";
import { useAuthStore } from "../../../store/authStore";
import { Link } from "react-router-dom";
import { Package, AlertTriangle, CheckCircle, Clock, RefreshCw } from "lucide-react";

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

const TIER_COLORS: Record<string, string> = {
  gratuit: "bg-gray-100 text-gray-700",
  basique: "bg-blue-100 text-blue-700",
  silver: "bg-gray-200 text-gray-700",
  golden: "bg-amber-100 text-amber-700",
};

const TIER_LABELS: Record<string, string> = {
  gratuit: "Gratuit",
  basique: "Basique",
  silver: "Silver",
  golden: "Golden",
};

export default function StudentPackPage() {
  const { token } = useAuthStore();
  const [abonnements, setAbonnements] = useState<Abonnement[]>([]);
  const [loading, setLoading] = useState(true);
  const [availablePacks, setAvailablePacks] = useState<any[]>([]);

  useEffect(() => {
    fetchData();
  }, [token]);

  const fetchData = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const [aboRes, packsRes] = await Promise.all([
        fetch("/api/abonnements/mes-abonnements", {
          headers: { Authorization: `Bearer ${token}` },
        }),
        fetch("/api/abonnements/packs", {
          headers: { Authorization: `Bearer ${token}` },
        }),
      ]);
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

  const now = new Date();
  const activeAbo = abonnements.find((a) => a.statut === "actif" || a.statut === "grace");
  const currentTier = activeAbo?.pack?.tier || "gratuit";
  const isGrace = activeAbo?.statut === "grace";
  const graceEnd = activeAbo?.grace_fin ? new Date(activeAbo.grace_fin) : null;
  const daysLeft = graceEnd ? Math.max(0, Math.ceil((graceEnd.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))) : 0;

  const quotaInfo: Record<string, string> = {
    gratuit: "3 lecons / trimestre",
    basique: "2 matieres au choix",
    silver: "4 matieres au choix",
    golden: "Acces illimité + Soft Skills",
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-navy rounded-3xl p-8">
        <h1 className="text-3xl font-[300] text-white">
          Mon <span className="italic text-orange-l">Pack</span>
        </h1>
        <p className="text-white/50 mt-2">Gerez votre abonnement et votre acces aux contenus</p>
      </div>

      {/* Grace period warning */}
      {isGrace && (
        <div className="bg-amber-50 border border-amber-200 rounded-2xl p-5 flex items-start gap-4">
          <AlertTriangle className="w-6 h-6 text-amber-500 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold text-amber-800">Periode de grace active</h3>
            <p className="text-sm text-amber-700 mt-1">
              Votre abonnement est en periode de grace. Il expirera dans{" "}
              <span className="font-bold">{daysLeft} jour{daysLeft > 1 ? "s" : ""}</span>.
              Souscrivez a un nouveau pack pour conserver votre acces.
            </p>
            {graceEnd && (
              <p className="text-xs text-amber-600 mt-2">
                Fin de grace : {graceEnd.toLocaleDateString("fr-TN")}
              </p>
            )}
          </div>
        </div>
      )}

      {/* Current Pack */}
      {activeAbo && (
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-navy">Pack Actif</h2>
            <span className={`px-3 py-1 text-xs font-semibold rounded-full ${TIER_COLORS[currentTier] || "bg-gray-100 text-gray-600"}`}>
              {TIER_LABELS[currentTier] || currentTier}
            </span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <p className="text-xs text-gray-500">Pack</p>
              <p className="text-sm font-medium text-navy">{activeAbo.pack?.nom || "N/A"}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Acces</p>
              <p className="text-sm font-medium text-navy">{quotaInfo[currentTier] || "N/A"}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Expiration</p>
              <p className="text-sm font-medium text-navy">
                {new Date(activeAbo.fin).toLocaleDateString("fr-TN")}
              </p>
            </div>
          </div>
          {activeAbo.pack?.features && (
            <div className="mt-4 pt-4 border-t border-gray-100">
              <p className="text-xs text-gray-500 mb-2">Fonctionnalites incluses</p>
              <div className="flex flex-wrap gap-2">
                {Object.entries(activeAbo.pack.features).map(([key, val]) => (
                  <span key={key} className="px-2 py-1 bg-gray-50 text-gray-600 text-xs rounded-full">
                    {key.replace(/_/g, " ")}: {String(val)}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Available Packs */}
      <div>
        <h2 className="text-lg font-semibold text-navy mb-4">Changer de pack</h2>
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="bg-white rounded-2xl p-6 shadow-sm border border-black/5 animate-pulse">
                <div className="h-5 w-32 bg-gray-200 rounded mb-3" />
                <div className="h-4 w-48 bg-gray-100 rounded mb-4" />
                <div className="h-8 w-24 bg-gray-200 rounded" />
              </div>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {availablePacks.map((pack) => {
              const isActive = activeAbo?.pack?.id === pack.id;
              return (
                <div
                  key={pack.id}
                  className={`bg-white rounded-2xl p-6 shadow-sm border transition-all ${
                    isActive ? "border-orange/30 ring-2 ring-orange/10" : "border-black/5 hover:shadow-md"
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-semibold text-navy">{pack.nom || pack.name}</h3>
                    <span className={`px-2 py-0.5 text-xs font-semibold rounded-full ${TIER_COLORS[pack.tier] || "bg-gray-100"}`}>
                      {TIER_LABELS[pack.tier] || pack.tier}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 mb-3">{pack.niveau_scolaire}</p>
                  {pack.matieres && pack.matieres.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-3">
                      {(Array.isArray(pack.matieres) ? pack.matieres : []).map((m: string) => (
                        <span key={m} className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full">{m}</span>
                      ))}
                    </div>
                  )}
                  <div className="flex items-center justify-between pt-3 border-t border-gray-100">
                    <span className="text-xl font-[300] text-navy">
                      {pack.prix_tnd || pack.price || 0} <span className="text-sm text-gray-400">TND</span>
                    </span>
                    {isActive ? (
                      <span className="px-3 py-1.5 bg-green-100 text-green-700 text-xs font-medium rounded-xl">Actif</span>
                    ) : (
                      <Link
                        to="/dashboard/packs"
                        className="px-3 py-1.5 bg-navy text-white text-xs font-medium rounded-xl hover:bg-navy/90 inline-block"
                      >
                        Souscrire
                      </Link>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Quota info */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
        <h2 className="text-lg font-semibold text-navy mb-3">Grille des packs</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          {(["gratuit", "basique", "silver", "golden"] as const).map((tier) => (
            <div key={tier} className={`p-4 rounded-xl ${currentTier === tier ? "ring-2 ring-orange" : "bg-gray-50"}`}>
              <h3 className="font-semibold text-navy text-sm">{TIER_LABELS[tier]}</h3>
              <p className="text-xs text-gray-500 mt-1">{quotaInfo[tier]}</p>
              {currentTier === tier && (
                <span className="inline-block mt-2 px-2 py-0.5 bg-orange/10 text-orange text-xs rounded-full font-medium">
                  Actuel
                </span>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
