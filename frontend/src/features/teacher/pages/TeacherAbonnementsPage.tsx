import { useState, useEffect, useCallback } from "react";
import { useAuthStore } from "../../../store/authStore";
import { ShoppingCart, Check, X, ArrowUpCircle, AlertCircle, Package, CreditCard } from "lucide-react";

interface Pack {
  id: number;
  nom: string;
  description?: string;
  tier: string;
  prix_tnd: number;
  niveau_scolaire: string;
  features?: Record<string, any>;
  est_actif: boolean;
}

interface Abonnement {
  id: number;
  user_id: number;
  pack_id: number;
  statut: string;
  debut: string;
  fin?: string;
  grace_fin?: string;
  created_at?: string;
  updated_at?: string;
  pack?: Pack;
}

const TIER_COLORS: Record<string, string> = {
  gratuit: "bg-gray-100 text-gray-600 border-gray-200",
  basique: "bg-blue-50 text-blue-700 border-blue-200",
  silver: "bg-slate-50 text-slate-600 border-slate-300",
  golden: "bg-amber-50 text-amber-700 border-amber-200",
};

const TIER_LABELS: Record<string, string> = {
  gratuit: "Gratuit",
  basique: "Basique",
  silver: "Silver",
  golden: "Golden",
};

const STATUT_COLORS: Record<string, string> = {
  actif: "bg-green-100 text-green-700",
  expire: "bg-gray-100 text-gray-600",
  annule: "bg-red-100 text-red-600",
  grace: "bg-amber-100 text-amber-700",
};

export default function TeacherAbonnementsPage() {
  const { token } = useAuthStore();
  const [packs, setPacks] = useState<Pack[]>([]);
  const [abonnements, setAbonnements] = useState<Abonnement[]>([]);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState({ show: false, message: "", type: "success" as "success" | "error" });
  const [confirmModal, setConfirmModal] = useState<{ action: string; abonnementId?: number; packId?: number } | null>(null);

  const showToast = (message: string, type: "success" | "error" = "success") => {
    setToast({ show: true, message, type });
    setTimeout(() => setToast({ show: false, message: "", type: "success" }), 3000);
  };

  const headers = { "Content-Type": "application/json", Authorization: `Bearer ${token}` };

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [packsRes, abRes] = await Promise.all([
        fetch(`${API}/api/abonnements/packs`, { headers }),
        fetch(`${API}/api/abonnements/mes-abonnements`, { headers }),
      ]);
      if (packsRes.ok) {
        const data = await packsRes.json();
        setPacks(data.items || data);
      }
      if (abRes.ok) {
        const data = await abRes.json();
        setAbonnements(data.items || data);
      }
    } catch (e: any) {
      showToast(e.message, "error");
    }
    setLoading(false);
  }, [token]);

  useEffect(() => { load(); }, [load]);

  const handleSubscribe = async (packId: number) => {
    try {
      const res = await fetch(`${API}/api/abonnements`, {
        method: "POST", headers, body: JSON.stringify({ pack_id: packId }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        return showToast(err.detail || "Erreur", "error");
      }
      showToast("Abonnement créé !");
      setConfirmModal(null);
      load();
    } catch { showToast("Erreur réseau", "error"); }
  };

  const handleUpgrade = async (abId: number) => {
    try {
      const res = await fetch(`${API}/api/abonnements/${abId}/upgrade`, {
        method: "PUT", headers,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        return showToast(err.detail || "Erreur", "error");
      }
      showToast("Upgrade effectué !");
      setConfirmModal(null);
      load();
    } catch { showToast("Erreur réseau", "error"); }
  };

  const handleCancel = async (abId: number) => {
    try {
      const res = await fetch(`${API}/api/abonnements/${abId}/cancel`, {
        method: "PUT", headers,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        return showToast(err.detail || "Erreur", "error");
      }
      showToast("Abonnement annulé (grâce 7 jours)");
      setConfirmModal(null);
      load();
    } catch { showToast("Erreur réseau", "error"); }
  };

  const activePackIds = new Set(abonnements.filter((a) => a.statut === "actif").map((a) => a.pack_id));

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-3xl p-8 shadow-sm border border-black/5">
        <h1 className="text-3xl font-[300] text-navy">
          Mes <span className="italic text-orange">Abonnements</span>
        </h1>
        <p className="text-gray mt-2">Gérez vos abonnements et découvrez les packs disponibles</p>
      </div>

      {toast.show && (
        <div className={`fixed top-4 right-4 z-50 px-4 py-2 rounded-xl text-white ${toast.type === "error" ? "bg-red-500" : "bg-green-500"}`}>
          {toast.message}
        </div>
      )}

      {/* Mes abonnements actifs */}
      <div>
        <h2 className="text-lg font-semibold text-navy mb-3 flex items-center gap-2">
          <CreditCard size={18} /> Mes abonnements
        </h2>
        {abonnements.length === 0 ? (
          <div className="bg-white rounded-2xl border border-black/5 p-6 text-center text-gray text-sm">
            Aucun abonnement actif
          </div>
        ) : (
          <div className="grid gap-3">
            {abonnements.map((ab) => (
              <div key={ab.id} className="bg-white rounded-2xl border border-black/5 p-4 flex items-center gap-4">
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-xs font-bold ${TIER_COLORS[ab.pack?.tier || "basique"]}`}>
                  {TIER_LABELS[ab.pack?.tier || "?"]?.slice(0, 3)}
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-navy text-sm">{ab.pack?.nom || `Pack #${ab.pack_id}`}</span>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${STATUT_COLORS[ab.statut] || ""}`}>{ab.statut}</span>
                  </div>
                  <div className="text-xs text-gray mt-0.5">
                    Du {new Date(ab.debut).toLocaleDateString("fr")}
                    {ab.fin && ` au ${new Date(ab.fin).toLocaleDateString("fr")}`}
                  </div>
                </div>
                <div className="flex gap-1">
                  {ab.statut === "actif" && (
                    <>
                      <button onClick={() => setConfirmModal({ action: "upgrade", abonnementId: ab.id })}
                        className="text-xs px-3 py-1.5 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 flex items-center gap-1">
                        <ArrowUpCircle size={12} /> Upgrade
                      </button>
                      <button onClick={() => setConfirmModal({ action: "cancel", abonnementId: ab.id })}
                        className="text-xs px-3 py-1.5 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 flex items-center gap-1">
                        <X size={12} /> Annuler
                      </button>
                    </>
                  )}
                  {ab.statut === "grace" && (
                    <span className="text-xs text-amber-600 flex items-center gap-1">
                      <AlertCircle size={12} /> Période de grâce
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Catalogue packs */}
      <div>
        <h2 className="text-lg font-semibold text-navy mb-3 flex items-center gap-2">
          <Package size={18} /> Packs disponibles
        </h2>
        {loading ? (
          <div className="text-center py-10 text-gray">Chargement...</div>
        ) : packs.length === 0 ? (
          <div className="text-center py-10 text-gray">
            <Package size={40} className="mx-auto mb-3 opacity-30" />
            <p>Aucun pack disponible</p>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {packs.filter((p) => p.est_actif).map((pack) => {
              const isSubscribed = activePackIds.has(pack.id);
              return (
                <div key={pack.id} className={`bg-white rounded-2xl border-2 p-5 transition-shadow hover:shadow-md ${isSubscribed ? "border-green-300" : "border-black/5"}`}>
                  <div className="flex items-center justify-between mb-3">
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${TIER_COLORS[pack.tier]}`}>
                      {TIER_LABELS[pack.tier] || pack.tier}
                    </span>
                    {isSubscribed && <Check size={16} className="text-green-500" />}
                  </div>
                  <h3 className="font-semibold text-navy mb-1">{pack.nom}</h3>
                  {pack.description && <p className="text-xs text-gray mb-3 line-clamp-2">{pack.description}</p>}
                  <div className="space-y-1 text-xs text-gray mb-4">
                    <div className="flex justify-between"><span>Niveau</span><span className="text-navy">{pack.niveau_scolaire}</span></div>
                    {pack.features?.ai_ask && <div className="flex justify-between"><span>AI Questions</span><span className="text-navy">Inclus</span></div>}
                    {pack.features?.ai_quiz && <div className="flex justify-between"><span>AI Quiz</span><span className="text-navy">Inclus</span></div>}
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-lg font-bold text-navy">{pack.prix_tnd} <span className="text-xs font-normal text-gray">TND</span></span>
                    {isSubscribed ? (
                      <span className="text-xs text-green-600 font-medium">Abonné</span>
                    ) : (
                      <button onClick={() => setConfirmModal({ action: "subscribe", packId: pack.id })}
                        className="text-xs px-3 py-1.5 bg-orange text-white rounded-lg hover:bg-orange/90 flex items-center gap-1">
                        <ShoppingCart size={12} /> Souscrire
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Confirmation modal */}
      {confirmModal && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-sm shadow-xl text-center">
            <AlertCircle size={40} className="mx-auto text-amber-400 mb-3" />
            <h3 className="text-lg font-semibold text-navy mb-2">
              {confirmModal.action === "subscribe" && "Souscrire à ce pack ?"}
              {confirmModal.action === "upgrade" && "Upgrade cet abonnement ?"}
              {confirmModal.action === "cancel" && "Annuler cet abonnement ?"}
            </h3>
            <p className="text-sm text-gray mb-4">
              {confirmModal.action === "cancel" && "L'annulation prendra effet à la fin de la période de grâce (7 jours)."}
              {confirmModal.action === "subscribe" && "Le pack sera activé immédiatement."}
              {confirmModal.action === "upgrade" && "Le changement de tier sera appliqué."}
            </p>
            <div className="flex gap-2 justify-center">
              <button onClick={() => setConfirmModal(null)} className="px-4 py-2 text-sm text-gray hover:bg-gray/10 rounded-xl">Annuler</button>
              <button onClick={() => {
                if (confirmModal.action === "subscribe" && confirmModal.packId) handleSubscribe(confirmModal.packId);
                if (confirmModal.action === "upgrade" && confirmModal.abonnementId) handleUpgrade(confirmModal.abonnementId);
                if (confirmModal.action === "cancel" && confirmModal.abonnementId) handleCancel(confirmModal.abonnementId);
              }} className="px-4 py-2 text-sm bg-orange text-white rounded-xl hover:bg-orange/90">Confirmer</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
