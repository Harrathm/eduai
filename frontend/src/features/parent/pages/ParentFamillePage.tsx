import { useState, useEffect } from "react";
import { useAuthStore } from "../../../store/authStore";
import { Link } from "react-router-dom";
import { Users, Percent, ArrowRight, UserPlus, Trash2 } from "lucide-react";

interface CompteFamille {
  id: number;
  parent_id: number;
  max_enfants: number;
  rang_famille: number;
}

interface EnfantFamille {
  eleve_id: number;
  full_name: string;
  email: string;
  rang: number;
  remise_pct: number;
}

interface DashboardEnfant {
  eleve_id: number;
  full_name: string;
  niveau_scolaire: string;
  dt_balance: number;
  packs_actifs_count: number;
}

export default function ParentFamillePage() {
  const { token } = useAuthStore();
  const [compte, setCompte] = useState<CompteFamille | null>(null);
  const [enfants, setEnfants] = useState<EnfantFamille[]>([]);
  const [dashboardEnfants, setDashboardEnfants] = useState<DashboardEnfant[]>([]);
  const [loading, setLoading] = useState(true);
  const [linkEmail, setLinkEmail] = useState("");
  const [linkLoading, setLinkLoading] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  useEffect(() => {
    fetchData();
  }, [token]);

  const fetchData = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const [compteRes, enfantsRes, dashRes] = await Promise.all([
        fetch("/api/famille/compte", { headers: { Authorization: `Bearer ${token}` } }),
        fetch("/api/famille/enfants", { headers: { Authorization: `Bearer ${token}` } }),
        fetch("/api/parents/me/enfants", { headers: { Authorization: `Bearer ${token}` } }),
      ]);
      if (compteRes.ok) setCompte(await compteRes.json());
      if (enfantsRes.ok) {
        const data = await enfantsRes.json();
        setEnfants(data.enfants || []);
      }
      if (dashRes.ok) {
        const data = await dashRes.json();
        setDashboardEnfants(data.enfants || []);
      }
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const handleLink = async () => {
    if (!token || !linkEmail.trim()) return;
    setLinkLoading(true);
    setMessage(null);
    try {
      const res = await fetch("/api/parents/me/enfants/lier", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({ email_eleve: linkEmail.trim() }),
      });
      if (res.ok) {
        setMessage({ type: "success", text: "Enfant lie avec succes." });
        setLinkEmail("");
        fetchData();
      } else {
        const err = await res.json();
        setMessage({ type: "error", text: err.detail || "Erreur lors de la liaison." });
      }
    } catch {
      setMessage({ type: "error", text: "Erreur reseau." });
    }
    setLinkLoading(false);
  };

  const handleUnlink = async (eleveId: number) => {
    if (!token || !confirm("Retirer cet enfant de la famille ?")) return;
    try {
      const res = await fetch(`/api/parents/me/enfants/${eleveId}/delier`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        setMessage({ type: "success", text: "Enfant retire." });
        fetchData();
      } else {
        const err = await res.json();
        setMessage({ type: "error", text: err.detail || "Erreur." });
      }
    } catch {
      setMessage({ type: "error", text: "Erreur reseau." });
    }
  };

  const DISCOUNT_INFO = [
    { rang: "1er enfant", remise: "0%", description: "Tarif plein" },
    { rang: "2eme enfant", remise: "-20%", description: "Remise famile" },
    { rang: "3eme enfant+", remise: "-25%", description: "Remise famile maximale" },
  ];

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
      <div className="bg-navy rounded-3xl p-8">
        <h1 className="text-3xl font-[300] text-white">
          Ma <span className="italic text-orange-l">Famille</span>
        </h1>
        <p className="text-white/50 mt-2">Gerez vos enfants et beneficiez des remises famille</p>
      </div>

      {message && (
        <div className={`p-4 rounded-xl text-sm ${message.type === "success" ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"}`}>
          {message.text}
        </div>
      )}

      {/* Family Discount Table */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
        <h2 className="text-lg font-semibold text-navy mb-4 flex items-center gap-2">
          <Percent className="w-5 h-5" /> Remises Famille
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {DISCOUNT_INFO.map((d) => (
            <div key={d.rang} className="p-4 bg-gray-50 rounded-xl">
              <p className="text-sm font-semibold text-navy">{d.rang}</p>
              <p className="text-2xl font-[300] text-orange">{d.remise}</p>
              <p className="text-xs text-gray-500 mt-1">{d.description}</p>
            </div>
          ))}
        </div>
        {compte && (
          <p className="text-xs text-gray-400 mt-3">
            Compte famille #{compte.id} — {enfants.length}/{compte.max_enfants} enfants rattaches
          </p>
        )}
      </div>

      {/* Link child */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
        <h2 className="text-lg font-semibold text-navy mb-4 flex items-center gap-2">
          <UserPlus className="w-5 h-5" /> Rattacher un enfant
        </h2>
        <div className="flex items-center gap-3">
          <input
            type="email"
            value={linkEmail}
            onChange={(e) => setLinkEmail(e.target.value)}
            placeholder="Email de l'eleve"
            className="flex-1 px-4 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-orange/30"
          />
          <button
            onClick={handleLink}
            disabled={linkLoading || !linkEmail.trim()}
            className="px-6 py-2 bg-navy text-white text-sm font-medium rounded-xl hover:bg-navy/90 disabled:opacity-50"
          >
            {linkLoading ? "Liaison..." : "Rattacher"}
          </button>
        </div>
      </div>

      {/* Children list */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
        <h2 className="text-lg font-semibold text-navy mb-4 flex items-center gap-2">
          <Users className="w-5 h-5" /> Enfants rattaches
        </h2>
        {enfants.length === 0 ? (
          <p className="text-gray text-sm">Aucun enfant rattache.</p>
        ) : (
          <div className="space-y-3">
            {enfants.map((enfant) => {
              const dashInfo = dashboardEnfants.find((d) => d.eleve_id === enfant.eleve_id);
              return (
                <div key={enfant.eleve_id} className="flex items-center justify-between p-4 bg-gray/5 rounded-xl">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 bg-orange/10 rounded-full flex items-center justify-center">
                      <span className="text-sm font-semibold text-orange">
                        {enfant.full_name?.charAt(0) || "?"}
                      </span>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-navy">{enfant.full_name}</p>
                      <p className="text-xs text-gray-500">{enfant.email}</p>
                      <p className="text-xs text-gray-400">
                        Rang {enfant.rang} — Remise {enfant.remise_pct}%
                        {dashInfo && ` — ${dashInfo.niveau_scolaire}`}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Link
                      to={`/dashboard/parent/enfant/${enfant.eleve_id}`}
                      className="px-3 py-1.5 text-xs font-medium text-navy bg-gray-100 rounded-xl hover:bg-gray-200 flex items-center gap-1"
                    >
                      Voir <ArrowRight className="w-3 h-3" />
                    </Link>
                    <button
                      onClick={() => handleUnlink(enfant.eleve_id)}
                      className="px-3 py-1.5 text-xs font-medium text-red-600 bg-red-50 rounded-xl hover:bg-red-100"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
