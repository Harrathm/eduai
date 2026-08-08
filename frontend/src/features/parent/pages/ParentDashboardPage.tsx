import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { parentAPI, DashboardData } from "../../../api";
import ParentMessaging from "./ParentMessaging";
import { Wallet, Package, Users } from "lucide-react";
import { tokenStorage } from "../../../utils/tokenStorage";
import { Button, Spinner } from "../../../components/ui";

export default function ParentDashboardPage() {
  const { t } = useTranslation();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [lierEmail, setLierEmail] = useState("");
  const [lierLoading, setLierLoading] = useState(false);
  const [lierMsg, setLierMsg] = useState("");
  const token = tokenStorage.getToken() || "";

  useEffect(() => {
    parentAPI.getDashboard()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const handleLier = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!lierEmail.trim()) return;
    setLierLoading(true);
    setLierMsg("");
    try {
      await parentAPI.lierEleve(lierEmail);
      setLierMsg(t('parent.linkSuccess'));
      setLierEmail("");
      const refreshed = await parentAPI.getDashboard();
      setData(refreshed);
    } catch (e: unknown) {
      setLierMsg(e instanceof Error ? e.message : t('parent.unknownError'));
    } finally {
      setLierLoading(false);
    }
  };

  if (loading) return <div className="flex items-center justify-center h-64"><Spinner size="lg" /></div>;
  if (error) return <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl">{error}</div>;
  if (!data) return null;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-[300] text-navy">{t('parent.dashboardTitle')}</h1>
        <p className="text-gray-500 mt-1">{t('parent.dashboardSubtitle')}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <div className="text-3xl font-[300] text-orange">{data.enfants.length}</div>
          <div className="text-sm text-gray-500 mt-1">{t('parent.childrenAttached', { count: data.enfants.length })}</div>
        </div>
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <div className="text-3xl font-[300] text-navy">{data.enfants.reduce((s, e) => s + e.packs_actifs_count, 0)}</div>
          <div className="text-sm text-gray-500 mt-1">{t('parent.activePacks', { count: data.enfants.reduce((s, e) => s + e.packs_actifs_count, 0) })}</div>
        </div>
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <div className="text-3xl font-[300] text-green-600">{data.total_dt_depense} DT</div>
          <div className="text-sm text-gray-500 mt-1">{t('parent.totalSpent')}</div>
        </div>
      </div>

      <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-medium text-navy">{t('parent.myChildren')}</h2>
          <Link to="/dashboard/parent/famille" className="text-xs text-orange hover:text-orange-l flex items-center gap-1">
            <Users className="w-3.5 h-3.5" /> {t('parent.myFamily')}
          </Link>
        </div>
        {data.enfants.length === 0 ? (
          <p className="text-gray-400">{t('parent.noChildren')}</p>
        ) : (
          <div className="space-y-3">
            {data.enfants.map((enfant) => (
              <div key={enfant.eleve_id} className="flex items-center justify-between p-4 rounded-xl border border-black/5 hover:border-orange/30 hover:bg-orange/5 transition-all">
                <Link to={`/dashboard/parent/enfant/${enfant.eleve_id}`} className="flex-1">
                  <div className="font-medium text-navy">{enfant.full_name}</div>
                  <div className="text-sm text-gray-500">{enfant.niveau_scolaire || t('parent.notDefined')}</div>
                </Link>
                <div className="flex items-center gap-2">
                  <Link to={`/dashboard/parent/enfant/${enfant.eleve_id}/wallet`} className="p-2 text-gray-400 hover:text-orange rounded-lg hover:bg-orange/5 transition-colors" title={t('parent.wallet')}>
                    <Wallet className="w-4 h-4" />
                  </Link>
                  <Link to={`/dashboard/parent/enfant/${enfant.eleve_id}/pack`} className="p-2 text-gray-400 hover:text-navy rounded-lg hover:bg-navy/5 transition-colors" title={t('parent.pack')}>
                    <Package className="w-4 h-4" />
                  </Link>
                  <div className="text-end ms-2">
                    <div className="text-sm font-medium text-navy">{enfant.dt_balance} DT</div>
                    <div className="text-xs text-gray-400">{enfant.packs_actifs_count} {t('parent.packs', { count: enfant.packs_actifs_count })}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
        <h2 className="text-lg font-medium text-navy mb-4">{t('parent.linkChild')}</h2>
        <form onSubmit={handleLier} className="flex gap-3">
          <input
            type="email"
            value={lierEmail}
            onChange={(e) => setLierEmail(e.target.value)}
            placeholder={t('parent.studentEmailPlaceholder')}
            className="flex-1 px-4 py-2 border border-gray-200 rounded-xl focus:outline-none focus:border-orange"
            required
          />
          <Button
            type="submit"
            disabled={lierLoading}
            variant="primary"
            loading={lierLoading}
          >
            {t('parent.link')}
          </Button>
        </form>
        {lierMsg && <p className="text-sm mt-2 text-gray-600">{lierMsg}</p>}
      </div>

      {token && <ParentMessaging token={token} />}
    </div>
  );
}
