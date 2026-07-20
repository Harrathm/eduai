import { useState, useEffect } from "react";
import { useAuthStore } from "../../../store/authStore";
import { Wallet, Coins, TrendingUp, Clock } from "lucide-react";

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

export default function StudentWallet() {
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
    ({ trial: "Essai", subscription: "Abonnement", school_allocated: "École", purchased: "Acheté" })[p] || p;

  const getPoolData = (poolName: string): PoolEntry | undefined =>
    balance?.pools?.find((p) => p.pool === poolName);

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-3xl p-8 shadow-sm border border-black/5">
        <h1 className="text-3xl font-[300] text-navy">
          Mon <span className="italic text-orange">Portefeuille</span>
        </h1>
        <p className="text-gray mt-2">Solde de crédits IA et tokens</p>
      </div>

      {/* Solde total */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-gradient-to-br from-orange-p to-cream rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-2">
            <Coins className="w-5 h-5 text-orange" />
            <span className="text-sm text-gray">Crédits IA</span>
          </div>
          <div className="text-3xl font-[300] text-navy">{balance?.total ?? 0}</div>
          <div className="text-xs text-gray mt-1">1 crédit = 500 tokens</div>
        </div>
        <div className="bg-gradient-to-br from-yellow-50 to-cream rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-2">
            <Wallet className="w-5 h-5 text-yellow-600" />
            <span className="text-sm text-gray">Tokens</span>
          </div>
          <div className="text-3xl font-[300] text-navy">{(balance?.total ?? 0) * 500}</div>
        </div>
      </div>

      {/* Détail par pool */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
        <h2 className="text-lg font-semibold text-navy mb-4">Détail par source</h2>
        <div className="space-y-3">
          {(["trial", "subscription", "school_allocated", "purchased"] as const).map((pool) => {
            const data = getPoolData(pool);
            if (!data || data.balance === 0) return null;
            return (
              <div key={pool} className="flex items-center justify-between p-3 bg-gray/5 rounded-xl">
                <div>
                  <span className="font-medium text-navy">{poolLabel(pool)}</span>
                  {data.expires_at && (
                    <span className="ml-2 text-xs text-gray flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      expire le {new Date(data.expires_at).toLocaleDateString("fr-TN")}
                    </span>
                  )}
                </div>
                <div className="text-right">
                  <span className="font-semibold text-navy">{data.balance} crédits</span>
                  <span className="text-xs text-gray ml-2">({data.balance * 500} tokens)</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Historique */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
        <h2 className="text-lg font-semibold text-navy mb-4">Historique récent</h2>
        {history.length === 0 ? (
          <p className="text-gray text-sm">Aucune transaction</p>
        ) : (
          <div className="space-y-2">
            {history.map((tx) => (
              <div key={tx.id} className="flex items-center justify-between py-2 border-b border-black/5 last:border-0">
                <div>
                  <span className="text-sm font-medium text-navy">{tx.feature}</span>
                  <span className="ml-2 text-xs text-gray">{poolLabel(tx.pool)}</span>
                </div>
                <div className="text-right">
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

      {/* Info */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
        <h2 className="text-lg font-semibold text-navy mb-4">Comment obtenir des crédits?</h2>
        <div className="space-y-3 text-gray text-sm">
          <p>• <b>Essai</b> : 100 crédits offerts à l'inscription (30 jours)</p>
          <p>• <b>Abonnement</b> : 200 crédits/mois inclus dans votre plan</p>
          <p>• <b>École</b> : alloués par votre administration</p>
          <p>• <b>Acheté</b> : achetez via Stripe (paiement sécurisé)</p>
        </div>
      </div>
    </div>
  );
}
