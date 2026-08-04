import { useState, useEffect } from "react";
import { useAuthStore } from "../../../store/authStore";
import { Wallet, Coins, Clock } from "lucide-react";

const API_URL = "";

interface PoolEntry {
  pool: string;
  balance: number;
  expires_at: string | null;
}

interface WalletBalance {
  user_id: number;
  total: number;
  pools: PoolEntry[];
}

interface TxRecord {
  id: number;
  pool: string;
  feature: string;
  amount: number;
  expires_at: string | null;
  created_at: string;
}

export default function TeacherWallet() {
  const { token } = useAuthStore();
  const [balance, setBalance] = useState<WalletBalance | null>(null);
  const [history, setHistory] = useState<TxRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, [token]);

  const fetchData = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const [balRes, histRes] = await Promise.all([
        fetch(`${API_URL}/api/wallet/balance`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        fetch(`${API_URL}/api/wallet/history?page=1&page_size=20`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
      ]);
      if (balRes.ok) setBalance(await balRes.json());
      if (histRes.ok) {
        const data = await histRes.json();
        setHistory(data.transactions || []);
      }
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const poolLabel = (p: string) =>
    ({ trial: "Essai", subscription: "Abonnement", school_allocated: "École", purchased: "Acheté", dt_purchased: "DT Achetés" })[p] || p;

  const poolColor = (p: string) =>
    ({ trial: "bg-blue-100 text-blue-700", subscription: "bg-purple-100 text-purple-700", school_allocated: "bg-green-100 text-green-700", purchased: "bg-orange-100 text-orange-700", dt_purchased: "bg-yellow-100 text-yellow-700" })[p] || "bg-gray-100 text-gray-700";

  const getPoolData = (poolName: string): PoolEntry | undefined =>
    balance?.pools?.find((p) => p.pool === poolName);

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-3xl p-8 shadow-sm border border-black/5">
        <h1 className="text-3xl font-[300] text-navy">
          Mon <span className="italic text-orange">Portefeuille</span>
        </h1>
        <p className="text-gray mt-2">Crédits IA et historique d'utilisation</p>
      </div>

      {/* Empty State */}
      {!loading && balance && balance.total === 0 && history.length === 0 && (
        <div className="bg-white rounded-2xl p-12 shadow-sm border border-black/5 text-center">
          <Wallet className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-navy mb-2">Aucun crédit IA</h3>
          <p className="text-gray">
            Vous n'avez pas encore de crédits IA. Contactez votre école ou achetez des crédits.
          </p>
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        <div className="bg-gradient-to-br from-orange-p to-cream rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-2">
            <Coins className="w-5 h-5 text-orange" />
            <span className="text-sm text-gray">Crédits IA</span>
          </div>
          <div className="text-3xl font-[300] text-navy">{balance?.total ?? 0}</div>
        </div>
        <div className="bg-gradient-to-br from-yellow-50 to-cream rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-2">
            <Wallet className="w-5 h-5 text-yellow-600" />
            <span className="text-sm text-gray">Tokens</span>
          </div>
          <div className="text-3xl font-[300] text-navy">{getPoolData("purchased")?.balance ?? 0}</div>
        </div>
      </div>

      <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
        <h2 className="text-lg font-semibold text-navy mb-4">Détail par source</h2>
        <div className="space-y-3">
          {(["trial", "subscription", "school_allocated", "purchased", "dt_purchased"] as const).map((pool) => {
            const data = getPoolData(pool);
            if (!data || data.balance === 0) return null;
            return (
              <div key={pool} className="flex items-center justify-between p-3 bg-gray/5 rounded-xl">
                <div>
                  <span className={`px-2 py-1 text-xs rounded-full ${poolColor(pool)}`}>{poolLabel(pool)}</span>
                  {data.expires_at && (
                    <span className="ml-2 text-xs text-gray flex items-center gap-1 inline-flex">
                      <Clock className="w-3 h-3" />
                      expire le {new Date(data.expires_at).toLocaleDateString("fr-TN")}
                    </span>
                  )}
                </div>
                <div className="text-end">
                  <span className="font-semibold text-navy">{data.balance} crédits</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
        <h2 className="text-lg font-semibold text-navy mb-4">Historique récent</h2>
        {loading ? (
          <div className="text-center py-8 text-gray">Chargement...</div>
        ) : history.length === 0 ? (
          <div className="text-center py-8 text-gray">Aucune transaction</div>
        ) : (
          <div className="space-y-2">
            {history.map((tx) => (
              <div key={tx.id} className="flex items-center justify-between py-2 border-b border-black/5 last:border-0">
                <div>
                  <span className="text-sm font-medium text-navy">{tx.feature}</span>
                  <span className={`ml-2 px-2 py-0.5 text-xs rounded-full ${poolColor(tx.pool)}`}>{poolLabel(tx.pool)}</span>
                </div>
                <div className="text-end">
                  <span className={`text-sm font-semibold ${tx.amount > 0 ? "text-green-600" : "text-red-500"}`}>
                    {tx.amount > 0 ? "+" : ""}{tx.amount}
                  </span>
                  <div className="text-xs text-gray">{tx.created_at ? new Date(tx.created_at).toLocaleDateString("fr-TN") : ""}</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
