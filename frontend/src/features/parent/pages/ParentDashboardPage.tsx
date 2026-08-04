import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { parentAPI, DashboardData } from "../api";
import ParentMessaging from "./ParentMessaging";
import { Wallet, Package, Users } from "lucide-react";

export default function ParentDashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [lierEmail, setLierEmail] = useState("");
  const [lierLoading, setLierLoading] = useState(false);
  const [lierMsg, setLierMsg] = useState("");
  const token = localStorage.getItem("token") || "";

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
      setLierMsg("Eleve rattache avec succes.");
      setLierEmail("");
      const refreshed = await parentAPI.getDashboard();
      setData(refreshed);
    } catch (e: unknown) {
      setLierMsg(e instanceof Error ? e.message : "Erreur inconnue");
    } finally {
      setLierLoading(false);
    }
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange"></div></div>;
  if (error) return <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl">{error}</div>;
  if (!data) return null;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-[300] text-navy">Tableau de bord <span className="italic text-orange-l">Parent</span></h1>
        <p className="text-gray-500 mt-1">Suivez la progression de vos enfants.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <div className="text-3xl font-[300] text-orange">{data.enfants.length}</div>
          <div className="text-sm text-gray-500 mt-1">Enfant{data.enfants.length > 1 ? "s" : ""} rattaché{data.enfants.length > 1 ? "s" : ""}</div>
        </div>
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <div className="text-3xl font-[300] text-navy">{data.enfants.reduce((s, e) => s + e.packs_actifs_count, 0)}</div>
          <div className="text-sm text-gray-500 mt-1">Pack{data.enfants.reduce((s, e) => s + e.packs_actifs_count, 0) !== 1 ? "s" : ""} actif{data.enfants.reduce((s, e) => s + e.packs_actifs_count, 0) !== 1 ? "s" : ""}</div>
        </div>
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <div className="text-3xl font-[300] text-green-600">{data.total_dt_depense} DT</div>
          <div className="text-sm text-gray-500 mt-1">Total depense</div>
        </div>
      </div>

      <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-medium text-navy">Mes Enfants</h2>
          <Link to="/dashboard/parent/famille" className="text-xs text-orange hover:text-orange-l flex items-center gap-1">
            <Users className="w-3.5 h-3.5" /> Ma Famille
          </Link>
        </div>
        {data.enfants.length === 0 ? (
          <p className="text-gray-400">Aucun enfant rattache. Ajoutez-en un ci-dessous.</p>
        ) : (
          <div className="space-y-3">
            {data.enfants.map((enfant) => (
              <div key={enfant.eleve_id} className="flex items-center justify-between p-4 rounded-xl border border-black/5 hover:border-orange/30 hover:bg-orange/5 transition-all">
                <Link to={`/dashboard/parent/enfant/${enfant.eleve_id}`} className="flex-1">
                  <div className="font-medium text-navy">{enfant.full_name}</div>
                  <div className="text-sm text-gray-500">{enfant.niveau_scolaire || "Non defini"}</div>
                </Link>
                <div className="flex items-center gap-2">
                  <Link to={`/dashboard/parent/enfant/${enfant.eleve_id}/wallet`} className="p-2 text-gray-400 hover:text-orange rounded-lg hover:bg-orange/5 transition-colors" title="Portefeuille">
                    <Wallet className="w-4 h-4" />
                  </Link>
                  <Link to={`/dashboard/parent/enfant/${enfant.eleve_id}/pack`} className="p-2 text-gray-400 hover:text-navy rounded-lg hover:bg-navy/5 transition-colors" title="Pack">
                    <Package className="w-4 h-4" />
                  </Link>
                  <div className="text-right ml-2">
                    <div className="text-sm font-medium text-navy">{enfant.dt_balance} DT</div>
                    <div className="text-xs text-gray-400">{enfant.packs_actifs_count} pack{enfant.packs_actifs_count !== 1 ? "s" : ""}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
        <h2 className="text-lg font-medium text-navy mb-4">Rattacher un enfant</h2>
        <form onSubmit={handleLier} className="flex gap-3">
          <input
            type="email"
            value={lierEmail}
            onChange={(e) => setLierEmail(e.target.value)}
            placeholder="Email de l'eleve"
            className="flex-1 px-4 py-2 border border-gray-200 rounded-xl focus:outline-none focus:border-orange"
            required
          />
          <button
            type="submit"
            disabled={lierLoading}
            className="px-6 py-2 bg-orange text-white rounded-xl font-medium hover:bg-orange-l transition-colors disabled:opacity-50"
          >
            {lierLoading ? "..." : "Rattacher"}
          </button>
        </form>
        {lierMsg && <p className="text-sm mt-2 text-gray-600">{lierMsg}</p>}
      </div>

      {token && <ParentMessaging token={token} />}
    </div>
  );
}
