import { useState, useEffect, useCallback } from "react";
import { Search, Copy, RefreshCw, Check, Key, Building2 } from "lucide-react";
import { Button, EmptyState, PageSpinner, Spinner } from "../../../components/ui";
import { adminSchools } from "../../../api";
import type { AdminSchool, PaginatedResponse } from "../../../api";

export default function AdminInviteCodesPage() {
  const [result, setResult] = useState<PaginatedResponse<AdminSchool> | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [copiedId, setCopiedId] = useState<number | null>(null);
  const [regeneratingId, setRegeneratingId] = useState<number | null>(null);
  const [toast, setToast] = useState({ show: false, message: "", type: "success" as "success" | "error" });

  const showToast = (message: string, type: "success" | "error" = "success") => {
    setToast({ show: true, message, type });
    setTimeout(() => setToast({ show: false, message: "", type: "success" }), 3500);
  };

  const fetchSchools = useCallback(async () => {
    setLoading(true);
    try {
      const data = await adminSchools.list({ search: search || undefined, per_page: 100 });
      setResult(data);
    } catch (err) {
      showToast("Erreur chargement", "error");
    }
    setLoading(false);
  }, [search]);

  useEffect(() => { fetchSchools(); }, [fetchSchools]);

  const handleCopy = (code: string, schoolId: number) => {
    navigator.clipboard.writeText(code);
    setCopiedId(schoolId);
    setTimeout(() => setCopiedId(null), 2000);
    showToast("Code copié !");
  };

  const handleRegenerate = async (schoolId: number, schoolName: string) => {
    if (!confirm(`Régénérer le code d'invitation pour "${schoolName}" ? L'ancien code cessera de fonctionner.`)) return;
    setRegeneratingId(schoolId);
    try {
      const { invite_code } = await adminSchools.regenerateInviteCode(schoolId);
      setResult(prev => prev ? {
        ...prev,
        items: prev.items.map(s => s.id === schoolId ? { ...s, invite_code } : s),
      } : prev);
      showToast("Nouveau code généré");
    } catch (err: any) {
      showToast(err.message || "Erreur", "error");
    }
    setRegeneratingId(null);
  };

  const schools = result?.items || [];

  return (
    <div className="space-y-6">
      {toast.show && (
        <div className={`fixed top-4 right-4 z-50 px-4 py-3 rounded-xl shadow-lg text-sm font-medium transition-all ${
          toast.type === "success" ? "bg-green-500 text-white" : "bg-red-500 text-white"
        }`}>{toast.message}</div>
      )}

      <div>
        <h1 className="text-3xl font-display font-light text-navy">Codes d'<span className="italic text-orange">Invitation</span></h1>
        <p className="text-gray text-sm mt-1">Gérez les codes d'invitation des écoles. Les étudiants utilisent ces codes pour s'inscrire.</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white rounded-2xl p-5 shadow-sm border border-black/5">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-purple-100 rounded-xl"><Building2 className="w-5 h-5 text-purple-600" /></div>
            <div><p className="text-2xl font-bold text-navy">{schools.length}</p><p className="text-xs text-gray">Écoles</p></div>
          </div>
        </div>
        <div className="bg-white rounded-2xl p-5 shadow-sm border border-black/5">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-green-100 rounded-xl"><Key className="w-5 h-5 text-green-600" /></div>
            <div><p className="text-2xl font-bold text-navy">{schools.filter(s => s.invite_code).length}</p><p className="text-xs text-gray">Codes actifs</p></div>
          </div>
        </div>
        <div className="bg-white rounded-2xl p-5 shadow-sm border border-black/5">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-orange-100 rounded-xl"><Key className="w-5 h-5 text-orange-600" /></div>
            <div><p className="text-2xl font-bold text-navy">{schools.filter(s => !s.invite_code).length}</p><p className="text-xs text-gray">Sans code</p></div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-2xl p-4 shadow-sm border border-black/5">
        <div className="relative max-w-sm">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray" />
          <input
            type="text"
            placeholder="Rechercher une école..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full ps-12 pe-4 py-2.5 bg-cream rounded-xl border-0 text-sm focus:ring-2 focus:ring-orange/30 outline-none"
          />
        </div>
      </div>

      <div className="bg-white rounded-2xl shadow-sm border border-black/5 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-black/5">
              <th className="text-start px-6 py-4 text-xs font-medium text-gray uppercase tracking-wider">École</th>
              <th className="text-start px-6 py-4 text-xs font-medium text-gray uppercase tracking-wider">Plan</th>
              <th className="text-start px-6 py-4 text-xs font-medium text-gray uppercase tracking-wider">Code d'invitation</th>
              <th className="text-end px-6 py-4 text-xs font-medium text-gray uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={4} className="px-6 py-12 text-center"><Spinner /></td></tr>
            ) : schools.length === 0 ? (
              <tr><td colSpan={4} className="px-6 py-12 text-center text-gray">Aucune école trouvée</td></tr>
            ) : schools.map((school) => (
              <tr key={school.id} className="border-b border-black/5 hover:bg-cream/50 transition-colors">
                <td className="px-6 py-4">
                  <div className="font-medium text-navy">{school.name}</div>
                  <div className="text-xs text-gray">{school.domain || school.slug}</div>
                </td>
                <td className="px-6 py-4">
                  <span className="px-2.5 py-1 text-xs rounded-full font-medium bg-purple-50 text-purple-600">
                    {school.subscription_tier?.replace("_", " ")}
                  </span>
                </td>
                <td className="px-6 py-4">
                  {school.invite_code ? (
                    <div className="flex items-center gap-2">
                      <code className="px-3 py-1.5 bg-navy/5 rounded-lg text-sm font-mono text-navy select-all">
                        {school.invite_code}
                      </code>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleCopy(school.invite_code!, school.id)}
                        className="p-1.5 rounded-lg transition-colors"
                        title="Copier"
                      >
                        {copiedId === school.id ? (
                          <Check className="w-4 h-4 text-green-500" />
                        ) : (
                          <Copy className="w-4 h-4 text-gray" />
                        )}
                      </Button>
                    </div>
                  ) : (
                    <span className="text-xs text-gray italic">Aucun code</span>
                  )}
                </td>
                <td className="px-6 py-4 text-end">
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => handleRegenerate(school.id, school.name)}
                    disabled={regeneratingId === school.id}
                    loading={regeneratingId === school.id}
                    className="flex items-center gap-1.5 ms-auto"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                    Régénérer
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
