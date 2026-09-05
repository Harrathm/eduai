import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useAuthStore } from "../../../store/authStore";
import { api } from "../../../utils/apiClient";
import { Wallet, Coins, TrendingUp, Clock } from "lucide-react";
import { PageWrapper } from "../../../components/ui";

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
  const { t } = useTranslation();
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
      const [balData, histData] = await Promise.all([
        api.get("/api/wallet/balance"),
        api.get("/api/wallet/history?page=1&page_size=20"),
      ]);
      setBalance(balData);
      setHistory(histData.items || []);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const poolLabel = (p: string) =>
    ({ trial: t("student.wallet.poolTrial"), subscription: t("student.wallet.poolSubscription"), school_allocated: t("student.wallet.poolSchool"), purchased: t("student.wallet.poolPurchased"), dt_purchased: t("student.wallet.poolPurchased") })[p] || p;

  const getPoolData = (poolName: string): PoolEntry | undefined =>
    balance?.pools?.find((p) => p.pool === poolName);

  return (
    <PageWrapper
      title={t('wallet.title')}
      subtitle={t('wallet.subtitle')}
      icon={<Wallet className="w-8 h-8" />}
    >

      {/* Solde total */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-gradient-to-br from-orange-p to-cream rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-2">
            <Coins className="w-5 h-5 text-orange" />
            <span className="text-sm text-gray">{t('wallet.aiCredits')}</span>
          </div>
          <div className="text-3xl font-[300] text-navy">{balance?.total ?? 0}</div>
          <div className="text-xs text-gray mt-1">{t('student.wallet.creditTokenRatio')}</div>
        </div>
        <div className="bg-gradient-to-br from-yellow-50 to-cream rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-2">
            <Wallet className="w-5 h-5 text-yellow-600" />
            <span className="text-sm text-gray">{t('wallet.tokens')}</span>
          </div>
          <div className="text-3xl font-[300] text-navy">{(balance?.total ?? 0) * 500}</div>
        </div>
      </div>

      {/* Détail par pool */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
        <h2 className="text-lg font-semibold text-navy mb-4">{t('wallet.detailBySource')}</h2>
        <div className="space-y-3">
          {(["trial", "subscription", "school_allocated", "purchased", "dt_purchased"] as const).map((pool) => {
            const data = getPoolData(pool);
            if (!data || data.balance === 0) return null;
            return (
              <div key={pool} className="flex items-center justify-between p-3 bg-gray/5 rounded-xl">
                <div>
                  <span className="font-medium text-navy">{poolLabel(pool)}</span>
                  {data.expires_at && (
                    <span className="ml-2 text-xs text-gray flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {t('wallet.expiresOn')} {new Date(data.expires_at).toLocaleDateString("fr-TN")}
                    </span>
                  )}
                </div>
                <div className="text-end">
                  <span className="font-semibold text-navy">{data.balance} {t('wallet.credits')}</span>
                  <span className="text-xs text-gray ms-2">({data.balance * 500} {t('wallet.tokens')})</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Historique */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
        <h2 className="text-lg font-semibold text-navy mb-4">{t('wallet.recentHistory')}</h2>
        {history.length === 0 ? (
          <p className="text-gray text-sm">{t('wallet.noTransactions')}</p>
        ) : (
          <div className="space-y-2">
            {history.map((tx) => (
              <div key={tx.id} className="flex items-center justify-between py-2 border-b border-black/5 last:border-0">
                <div>
                  <span className="text-sm font-medium text-navy">{tx.feature}</span>
                  <span className="ml-2 text-xs text-gray">{poolLabel(tx.pool)}</span>
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

      {/* Info */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
        <h2 className="text-lg font-semibold text-navy mb-4">{t('wallet.howToGetCredits')}</h2>
        <div className="space-y-3 text-gray text-sm">
          <p>• <b>{t('wallet.poolTrial')}</b> : {t('wallet.poolTrialDesc')}</p>
          <p>• <b>{t('wallet.poolSubscription')}</b> : {t('wallet.poolSubscriptionDesc')}</p>
          <p>• <b>{t('wallet.poolSchool')}</b> : {t('wallet.poolSchoolDesc')}</p>
          <p>• <b>{t('wallet.poolPurchased')}</b> : {t('wallet.poolPurchasedDesc')}</p>
        </div>
      </div>
    </PageWrapper>
  );
}
