import { useState, useEffect } from "react";
import { useTranslation } from 'react-i18next';
import { useParams, Link, useNavigate } from "react-router-dom";
import { parentAPI, ProgressionData, SuiviData } from "../../../api";
import { Button, Spinner } from "../../../components/ui";
import { Wallet, ExternalLink } from "lucide-react";

const RECHARGE_AMOUNTS = [5, 10, 20, 50];

export default function ChildDetailPage() {
  const { t } = useTranslation();
  const { eleveId } = useParams<{ eleveId: string }>();
  const navigate = useNavigate();
  const id = parseInt(eleveId || "0");

  const [suivi, setSuivi] = useState<SuiviData | null>(null);
  const [progression, setProgression] = useState<ProgressionData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [rechargeOpen, setRechargeOpen] = useState(false);
  const [rechargeAmount, setRechargeAmount] = useState<number>(10);
  const [customAmount, setCustomAmount] = useState("");
  const [rechargeLoading, setRechargeLoading] = useState(false);
  const [rechargeError, setRechargeError] = useState("");

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    Promise.all([
      parentAPI.getSuivi(id),
      parentAPI.getProgression(id),
    ])
      .then(([s, p]) => { setSuivi(s); setProgression(p); })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  const handleUnlink = async () => {
    if (!confirm(t('parent.childDetail.detachConfirm'))) return;
    try {
      await parentAPI.delierEleve(id);
      navigate("/dashboard/parent");
    } catch (e: any) {
      alert(e.message);
    }
  };

  const handleRecharge = async () => {
    const amount = customAmount ? parseFloat(customAmount) : rechargeAmount;
    if (!amount || amount <= 0) return;
    setRechargeLoading(true);
    setRechargeError("");
    try {
      const { pay_url } = await parentAPI.rechargeWallet(id, amount);
      window.location.href = pay_url;
    } catch (e: any) {
      setRechargeError(e.message || "Erreur lors de la recharge");
      setRechargeLoading(false);
    }
  };

  if (loading) return <div className="flex items-center justify-center h-64"><Spinner size="lg" /></div>;
  if (error) return <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl">{error}</div>;
  if (!suivi || !progression) return null;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link to="/dashboard/parent" className="text-orange hover:text-orange-l transition-colors">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 19l-7-7 7-7" /></svg>
        </Link>
        <div>
          <h1 className="text-2xl font-[300] text-navy">{suivi.full_name}</h1>
          <p className="text-gray-500">{suivi.niveau_scolaire || t('parent.childDetail.levelUndefined')}</p>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <Link to={`/dashboard/parent/enfant/${id}/wallet`} className="px-3 py-1.5 text-xs font-medium text-navy bg-gray-100 rounded-xl hover:bg-gray-200 flex items-center gap-1">
            <Wallet className="w-3.5 h-3.5" /> {t('parent.childDetail.tabs.wallet')}
          </Link>
          <Link to={`/dashboard/parent/enfant/${id}/pack`} className="px-3 py-1.5 text-xs font-medium text-navy bg-gray-100 rounded-xl hover:bg-gray-200 flex items-center gap-1">
            <ExternalLink className="w-3.5 h-3.5" /> {t('parent.childDetail.tabs.pack')}
          </Link>
          <Button variant="danger" size="sm" onClick={handleUnlink} className="transition-colors">
            {t('parent.childDetail.detachButton')}
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-2xl p-5 shadow-sm border border-black/5">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-[300] text-orange">{suivi.dt_balance} DT</div>
              <div className="text-xs text-gray-500 mt-1">{t('parent.childDetail.walletBalance')}</div>
            </div>
            <Button
              variant="primary"
              size="sm"
              onClick={() => setRechargeOpen(!rechargeOpen)}
            >
              <Wallet className="w-4 h-4" />
              {t('parent.childDetail.rechargeButton')}
            </Button>
          </div>
        </div>
        <div className="bg-white rounded-2xl p-5 shadow-sm border border-black/5">
          <div className="text-2xl font-[300] text-navy">{suivi.packs_actifs.length}</div>
          <div className="text-xs text-gray-500 mt-1">{suivi.packs_actifs.length} {t('parent.childDetail.activePacks')}{suivi.packs_actifs.length !== 1 ? t('parent.childDetail.activePacksPlural') : ""}</div>
        </div>
        <div className="bg-white rounded-2xl p-5 shadow-sm border border-black/5">
          <div className="text-2xl font-[300] text-green-600">{progression.badges.length}</div>
          <div className="text-xs text-gray-500 mt-1">{progression.badges.length} {t('parent.childDetail.badges')}{progression.badges.length !== 1 ? t('parent.childDetail.badgesPlural') : ""}</div>
        </div>
        <div className="bg-white rounded-2xl p-5 shadow-sm border border-black/5">
          <div className="text-2xl font-[300] text-purple-600">
            {progression.scores.length > 0 ? Math.round(progression.scores.reduce((s, sc) => s + sc.score, 0) / progression.scores.length) : 0}%
          </div>
          <div className="text-xs text-gray-500 mt-1">{t('parent.childDetail.avgScore')}</div>
        </div>
      </div>

      {/* Recharge Panel */}
      {rechargeOpen && (
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-orange/20">
          <h2 className="text-lg font-medium text-navy mb-4">{t('parent.childDetail.rechargeTitle')} {suivi.full_name}</h2>
          <p className="text-sm text-gray-500 mb-4">
            {t('parent.childDetail.rechargeDesc')}
          </p>
          <div className="grid grid-cols-4 gap-3 mb-4">
            {RECHARGE_AMOUNTS.map((amt) => (
              <Button
                key={amt}
                variant={rechargeAmount === amt && !customAmount ? "primary" : "secondary"}
                size="md"
                onClick={() => { setRechargeAmount(amt); setCustomAmount(""); }}
              >
                {amt} DT
              </Button>
            ))}
          </div>
          <div className="mb-4">
            <input
              type="number"
              min="1"
              max="2000"
              step="0.5"
              value={customAmount}
              onChange={(e) => setCustomAmount(e.target.value)}
              placeholder={t('parent.childDetail.amountPlaceholder')}
              className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 focus:outline-none focus:ring-2 focus:ring-orange/30"
            />
          </div>
          {rechargeError && <p className="text-red-500 text-sm mb-3">{rechargeError}</p>}
          <div className="flex gap-3">
            <Button
              variant="primary"
              size="md"
              onClick={handleRecharge}
              loading={rechargeLoading}
            >
              <ExternalLink className="w-4 h-4" />
              {t('parent.childDetail.payButton')}
            </Button>
            <Button
              variant="secondary"
              size="md"
              onClick={() => setRechargeOpen(false)}
            >
              {t('parent.childDetail.cancelButton')}
            </Button>
          </div>
        </div>
      )}

      {suivi.packs_actifs.length > 0 && (
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <h2 className="text-lg font-medium text-navy mb-4">{t('parent.childDetail.activePacksTitle')}</h2>
          <div className="space-y-2">
            {suivi.packs_actifs.map((p, i) => (
              <div key={i} className="flex justify-between items-center p-3 rounded-lg bg-gray-50">
                <div>
                  <span className="text-sm font-medium text-navy">Pack #{p.pack_id}</span>
                  <span className="text-xs text-gray-400 ms-3">{p.amount_paid} {p.currency}</span>
                </div>
                  <span className="text-xs text-gray-500">
                    {t('parent.childDetail.validUntil')} {new Date(p.valid_until).toLocaleDateString("fr-TN")}
                  </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {progression.objectifs.length > 0 && (
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <h2 className="text-lg font-medium text-navy mb-4">{t('parent.childDetail.objectives')}</h2>
          <div className="space-y-3">
            {progression.objectifs.map((o) => (
              <div key={o.id} className="p-3 rounded-lg bg-gray-50">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium text-navy">
                    {o.matiere || o.metric_type} — {o.horizon}
                  </span>
                  <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                    o.status === "completed" ? "bg-green-100 text-green-700" :
                    o.status === "on_track" ? "bg-blue-100 text-blue-700" :
                    o.status === "behind" ? "bg-yellow-100 text-yellow-700" :
                    "bg-red-100 text-red-700"
                  }`}>
                    {o.status}
                  </span>
                </div>
                <div className="mt-2 h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full bg-orange rounded-full transition-all" style={{ width: `${Math.min(100, o.progress_pct)}%` }} />
                </div>
                <div className="text-xs text-gray-400 mt-1">{o.progress_pct}% — {t('parent.childDetail.objectivePrefix')} {o.target_value}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {progression.badges.length > 0 && (
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <h2 className="text-lg font-medium text-navy mb-4">{t('parent.childDetail.badgesObtained')}</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {progression.badges.map((b) => (
              <div key={b.badge_id} className="text-center p-3 rounded-xl border border-black/5">
                <div className="w-10 h-10 rounded-full mx-auto mb-2 flex items-center justify-center text-white text-lg" style={{ backgroundColor: b.couleur }}>
                  {b.nom.charAt(0)}
                </div>
                <div className="text-xs font-medium text-navy">{b.nom}</div>
                <div className="text-[10px] text-gray-400 mt-1">{new Date(b.date_obtention).toLocaleDateString("fr-TN")}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {progression.scores.length > 0 && (
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <h2 className="text-lg font-medium text-navy mb-4">{t('parent.childDetail.recentScores')}</h2>
          <div className="space-y-2">
            {progression.scores.slice(0, 10).map((s, i) => (
              <div key={i} className="flex justify-between items-center p-2 rounded-lg text-sm">
                <span className="text-gray-600">Chapitre #{s.chapitre_id}</span>
                <span className={`font-medium ${s.score >= 75 ? "text-green-600" : s.score >= 40 ? "text-yellow-600" : "text-red-600"}`}>
                  {Math.round(s.score)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
