import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { useAuthStore } from "../../../store/authStore";
import { ArrowLeft, Wallet, Coins, Clock, AlertCircle, CreditCard } from "lucide-react";
import { parentEnfants, parentWallet } from "../../../api";

interface WalletBalance {
  user_id: number;
  total: number;
  pools: { pool: string; balance: number; expires_at: string | null }[];
}

interface ChildInfo {
  eleve_id: number;
  full_name: string;
  email: string;
  niveau_scolaire: string;
  dt_balance: number;
  packs_actifs_count: number;
}

const POOL_LABELS: Record<string, string> = {
  trial: "Essai",
  subscription: "Abonnement",
  school_allocated: "Ecole",
  purchased: "Achete",
  dt_purchased: "DT Achetes",
};

export default function ParentWalletPage() {
  const { eleveId } = useParams();
  const { token } = useAuthStore();
  const [wallet, setWallet] = useState<WalletBalance | null>(null);
  const [childInfo, setChildInfo] = useState<ChildInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [rechargeAmount, setRechargeAmount] = useState<number>(10);
  const [rechargeLoading, setRechargeLoading] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const childId = Number(eleveId);

  useEffect(() => {
    fetchData();
  }, [childId, token]);

  const fetchData = async () => {
    if (!token || !childId) return;
    setLoading(true);
    try {
      const [suivi, enfantData] = await Promise.all([
        parentEnfants.suivi(childId),
        parentEnfants.list(),
      ]);
      setWallet({
        user_id: childId,
        total: suivi.dt_balance || 0,
        pools: [
          { pool: "dt_purchased", balance: suivi.dt_balance || 0, expires_at: null },
        ],
      });
      const child = (enfantData.enfants || []).find((e: any) => e.eleve_id === childId);
      if (child) setChildInfo(child);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const handleRecharge = async () => {
    if (!token || !childId || rechargeAmount <= 0) return;
    setRechargeLoading(true);
    setMessage(null);
    try {
      const data = await parentWallet.creditWallet(childId, rechargeAmount);
      if (data.pay_url) {
        window.open(data.pay_url, "_blank");
        setMessage({ type: "success", text: "Redirection vers Konnect pour le paiement..." });
      } else {
        setMessage({ type: "success", text: "Recharge effectuee avec succes." });
      }
      fetchData();
    } catch {
      setMessage({ type: "error", text: "Erreur reseau." });
    }
    setRechargeLoading(false);
  };

  const PRESETS = [5, 10, 20, 50, 100];

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
        <ArrowLeft className="w-4 h-4" /> Retour au tableau de bord
      </Link>

      <div className="bg-navy rounded-3xl p-8">
        <h1 className="text-3xl font-[300] text-white">
          Portefeuille de <span className="italic text-orange-l">{childInfo?.full_name || "l'enfant"}</span>
        </h1>
        <p className="text-white/50 mt-2">Solde de credits IA et rechargement</p>
      </div>

      {/* Balance */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gradient-to-br from-orange-p to-cream rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-2">
            <Coins className="w-5 h-5 text-orange" />
            <span className="text-sm text-gray">Credits IA</span>
          </div>
          <div className="text-3xl font-[300] text-navy">{wallet?.total ?? 0}</div>
        </div>
        <div className="bg-gradient-to-br from-yellow-50 to-cream rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-2">
            <Wallet className="w-5 h-5 text-yellow-600" />
            <span className="text-sm text-gray">DT Achetes</span>
          </div>
          <div className="text-3xl font-[300] text-navy">
            {wallet?.pools?.find((p) => p.pool === "dt_purchased")?.balance ?? 0}
          </div>
        </div>
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <div className="flex items-center gap-2 mb-2">
            <AlertCircle className="w-5 h-5 text-gray-400" />
            <span className="text-sm text-gray">Packs actifs</span>
          </div>
          <div className="text-3xl font-[300] text-navy">{childInfo?.packs_actifs_count ?? 0}</div>
        </div>
      </div>

      {/* Recharge */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
        <h2 className="text-lg font-semibold text-navy mb-4 flex items-center gap-2">
          <CreditCard className="w-5 h-5" /> Recharger le portefeuille
        </h2>

        <div className="flex flex-wrap gap-2 mb-4">
          {PRESETS.map((amt) => (
            <button
              key={amt}
              onClick={() => setRechargeAmount(amt)}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-colors ${
                rechargeAmount === amt ? "bg-navy text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              {amt} TND
            </button>
          ))}
        </div>

        <div className="flex items-center gap-3">
          <input
            type="number"
            min={1}
            max={2000}
            value={rechargeAmount}
            onChange={(e) => setRechargeAmount(Number(e.target.value))}
            className="w-32 px-4 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-orange/30"
          />
          <span className="text-sm text-gray-500">TND</span>
          <button
            onClick={handleRecharge}
            disabled={rechargeLoading || rechargeAmount <= 0}
            className="px-6 py-2 bg-orange text-white text-sm font-medium rounded-xl hover:bg-orange/90 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {rechargeLoading ? "Redirection..." : "Recharger via Konnect"}
          </button>
        </div>

        {message && (
          <div className={`mt-3 p-3 rounded-xl text-sm ${
            message.type === "success" ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"
          }`}>
            {message.text}
          </div>
        )}
      </div>

      {/* Pool detail */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
        <h2 className="text-lg font-semibold text-navy mb-4">Detail par source</h2>
        <div className="space-y-3">
          {(wallet?.pools || []).filter((p) => p.balance > 0).map((pool) => (
            <div key={pool.pool} className="flex items-center justify-between p-3 bg-gray/5 rounded-xl">
              <div>
                <span className="font-medium text-navy">{POOL_LABELS[pool.pool] || pool.pool}</span>
                {pool.expires_at && (
                  <span className="ml-2 text-xs text-gray flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    expire le {new Date(pool.expires_at).toLocaleDateString("fr-TN")}
                  </span>
                )}
              </div>
              <span className="font-semibold text-navy">{pool.balance} credits</span>
            </div>
          ))}
          {(!wallet?.pools || wallet.pools.filter((p) => p.balance > 0).length === 0) && (
            <p className="text-gray text-sm">Aucun credit disponible.</p>
          )}
        </div>
      </div>
    </div>
  );
}
