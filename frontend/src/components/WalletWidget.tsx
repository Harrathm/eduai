import { useEffect, useState } from "react";
import { getWalletBalance } from "../api/wallet";
import { useAuthStore } from "../store/authStore";

interface PoolBalance {
  pool: string;
  balance: number;
  expires_at: string | null;
}

interface WalletData {
  total: number;
  pools: PoolBalance[];
}

const POOL_LABELS: Record<string, { label: string; color: string }> = {
  trial: { label: "Essai", color: "text-blue-600 bg-blue-50" },
  school_allocated: { label: "École", color: "text-purple-600 bg-purple-50" },
  purchased: { label: "Achetés", color: "text-green-600 bg-green-50" },
  subscription: { label: "Abonnement", color: "text-orange-600 bg-orange-50" },
};

export default function WalletWidget({ compact = false }: { compact?: boolean }) {
  const token = useAuthStore((s) => s.token);
  const [wallet, setWallet] = useState<WalletData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    getWalletBalance(token)
      .then(setWallet)
      .catch(() => setWallet(null))
      .finally(() => setLoading(false));
  }, [token]);

  if (loading) {
    return (
      <div className="animate-pulse bg-gray-100 rounded-2xl p-4 h-24" />
    );
  }

  if (!wallet) return null;

  const alertLevel =
    wallet.total <= 0 ? "critical" :
    wallet.total <= 20 ? "warning" : null;

  return (
    <div className={`rounded-2xl border p-4 ${alertLevel === "critical" ? "border-red-300 bg-red-50" : alertLevel === "warning" ? "border-orange-300 bg-orange-50" : "border-black/5 bg-white"}`}>
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray uppercase tracking-wide">
          Portefeuille
        </h3>
        <span className={`text-2xl font-bold ${alertLevel === "critical" ? "text-red-600" : alertLevel === "warning" ? "text-orange-600" : "text-navy"}`}>
          {wallet.total}
        </span>
      </div>

      {alertLevel && (
        <div className={`text-xs px-3 py-1.5 rounded-lg mb-3 ${alertLevel === "critical" ? "bg-red-100 text-red-700" : "bg-orange-100 text-orange-700"}`}>
          {alertLevel === "critical"
            ? "Solde épuisé — Rechargez ou contactez votre école"
            : "Solde faible — Consommation limitée"}
        </div>
      )}

      {!compact && (
        <div className="grid grid-cols-2 gap-2">
          {wallet.pools.map((p) => {
            const info = POOL_LABELS[p.pool] || { label: p.pool, color: "text-gray bg-gray-50" };
            if (p.balance <= 0) return null;
            return (
              <div key={p.pool} className={`rounded-xl px-3 py-2 ${info.color}`}>
                <div className="text-xs font-medium">{info.label}</div>
                <div className="text-lg font-bold">{p.balance}</div>
                {p.expires_at && (
                  <div className="text-[10px] opacity-70">
                    Exp: {new Date(p.expires_at).toLocaleDateString("fr-TN")}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
