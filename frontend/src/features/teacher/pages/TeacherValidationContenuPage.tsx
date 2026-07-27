import { useState, useEffect, useCallback } from "react";
import { CheckCircle, XCircle, Clock, AlertTriangle, Eye } from "lucide-react";
import { useAuthStore } from "../../../store/authStore";

interface ContenuItem {
  id: number;
  notion_id: number;
  niveau_assimilation: string;
  type_ressource: string;
  statut_pedagogique: string;
  statut_validation_pedagogique: string;
  enseignant_id: number | null;
}

export default function TeacherValidationContenuPage() {
  const { token, user } = useAuthStore();
  const [contenus, setContenus] = useState<ContenuItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [rejectModal, setRejectModal] = useState<{ contenuId: number; contenuNom: string } | null>(null);
  const [commentaire, setCommentaire] = useState("");
  const [filter, setFilter] = useState<"all" | "en_attente" | "valide" | "rejete">("all");
  const [toast, setToast] = useState({ show: false, message: "", type: "success" as "success" | "error" });

  const showToast = (message: string, type: "success" | "error" = "success") => {
    setToast({ show: true, message, type });
    setTimeout(() => setToast({ show: false, message: "", type: "success" }), 3000);
  };

  const headers = { "Content-Type": "application/json", Authorization: `Bearer ${token}` };

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const payload = JSON.parse(atob(token?.split(".")[1] || ""));
      const userId = parseInt(payload.sub);
      const res = await fetch(`/api/pathway/responsables-pedagogiques/${userId}/contenus`, { headers });
      if (res.ok) {
        setContenus(await res.json());
      }
    } catch { /* ignore */ }
    setLoading(false);
  }, [token]);

  useEffect(() => { load(); }, [load]);

  const handleValider = async (contenuId: number) => {
    try {
      const res = await fetch(`/api/pathway/contenus-notion/${contenuId}/valider`, {
        method: "POST",
        headers,
      });
      if (!res.ok) {
        const err = await res.json();
        return showToast(err.detail || "Erreur", "error");
      }
      showToast("Contenu validé");
      setContenus(prev => prev.map(c =>
        c.id === contenuId ? { ...c, statut_validation_pedagogique: "valide" } : c
      ));
    } catch {
      showToast("Erreur réseau", "error");
    }
  };

  const handleRejeter = async () => {
    if (!rejectModal || !commentaire.trim()) return;
    try {
      const res = await fetch(`/api/pathway/contenus-notion/${rejectModal.contenuId}/rejeter`, {
        method: "POST",
        headers,
        body: JSON.stringify({ commentaire }),
      });
      if (!res.ok) {
        const err = await res.json();
        return showToast(err.detail || "Erreur", "error");
      }
      showToast("Contenu rejeté");
      setContenus(prev => prev.map(c =>
        c.id === rejectModal.contenuId ? { ...c, statut_validation_pedagogique: "rejete" } : c
      ));
      setRejectModal(null);
      setCommentaire("");
    } catch {
      showToast("Erreur réseau", "error");
    }
  };

  const filtered = filter === "all" ? contenus : contenus.filter(c => c.statut_validation_pedagogique === filter);
  const stats = {
    total: contenus.length,
    en_attente: contenus.filter(c => c.statut_validation_pedagogique === "en_attente").length,
    valide: contenus.filter(c => c.statut_validation_pedagogique === "valide").length,
    rejete: contenus.filter(c => c.statut_validation_pedagogique === "rejete").length,
  };

  const statusBadge = (statut: string) => {
    switch (statut) {
      case "valide":
        return <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded-full text-xs font-medium">Validé</span>;
      case "rejete":
        return <span className="px-2 py-0.5 bg-red-100 text-red-700 rounded-full text-xs font-medium">Rejeté</span>;
      default:
        return <span className="px-2 py-0.5 bg-yellow-100 text-yellow-700 rounded-full text-xs font-medium">En attente</span>;
    }
  };

  return (
    <div className="space-y-6">
      {toast.show && (
        <div className={`fixed top-4 right-4 z-50 px-4 py-3 rounded-xl shadow-lg text-sm font-medium ${
          toast.type === "success" ? "bg-green-500 text-white" : "bg-red-500 text-white"
        }`}>{toast.message}</div>
      )}

      <div>
        <h1 className="text-3xl font-display font-light text-navy">
          Validation <span className="italic text-orange">Pédagogique</span>
        </h1>
        <p className="text-gray text-sm mt-1">Valider ou rejeter les contenus de votre périmètre pédagogique</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: "Total", value: stats.total, color: "navy" },
          { label: "En attente", value: stats.en_attente, color: "yellow-600" },
          { label: "Validés", value: stats.valide, color: "green-600" },
          { label: "Rejetés", value: stats.rejete, color: "red-600" },
        ].map(s => (
          <div key={s.label} className="bg-white rounded-xl shadow-sm border border-black/5 p-4">
            <div className={`text-2xl font-bold font-display text-${s.color}`}>{s.value}</div>
            <div className="text-xs text-gray mt-0.5">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex gap-2">
        {(["all", "en_attente", "valide", "rejete"] as const).map(f => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-4 py-2 rounded-xl text-sm font-medium transition-colors ${
              filter === f
                ? "bg-navy text-white"
                : "bg-white text-gray border border-black/5 hover:bg-gray-50"
            }`}
          >
            {f === "all" ? "Tous" : f === "en_attente" ? "En attente" : f === "valide" ? "Validés" : "Rejetés"}
          </button>
        ))}
      </div>

      {/* Contenus */}
      {loading ? (
        <div className="text-center py-12 text-gray">Chargement...</div>
      ) : filtered.length === 0 ? (
        <div className="bg-white rounded-2xl shadow-sm border border-black/5 p-12 text-center">
          <Eye className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray">Aucun contenu à afficher</p>
          <p className="text-gray text-sm mt-1">
            {filter === "all" ? "Vous n'avez aucun contenu dans votre périmètre" : `Aucun contenu "${filter}"`}
          </p>
        </div>
      ) : (
        <div className="bg-white rounded-2xl shadow-sm border border-black/5 overflow-hidden">
          <div className="px-6 py-4 bg-gray-50 border-b border-black/5">
            <div className="grid grid-cols-6 gap-4 text-xs font-semibold text-gray uppercase">
              <div>ID</div>
              <div>Notion</div>
              <div>Niveau</div>
              <div>Type</div>
              <div>Statut</div>
              <div className="text-right">Actions</div>
            </div>
          </div>
          <div className="divide-y divide-gray-100">
            {filtered.map(c => (
              <div key={c.id} className="px-6 py-4 grid grid-cols-6 gap-4 items-center hover:bg-gray-50/50 transition-colors">
                <div className="text-sm text-gray font-mono">#{c.id}</div>
                <div className="text-sm text-navy font-medium">Notion #{c.notion_id}</div>
                <div className="text-xs px-2 py-0.5 bg-cream-m rounded-full text-gray inline-block w-fit">
                  {c.niveau_assimilation}
                </div>
                <div className="text-sm text-gray">{c.type_ressource}</div>
                <div>{statusBadge(c.statut_validation_pedagogique)}</div>
                <div className="flex justify-end gap-2">
                  {c.statut_validation_pedagogique !== "valide" && (
                    <button
                      onClick={() => handleValider(c.id)}
                      className="px-3 py-1.5 bg-green-50 hover:bg-green-100 text-green-700 rounded-lg text-xs font-medium flex items-center gap-1 transition-colors"
                    >
                      <CheckCircle className="w-3.5 h-3.5" /> Valider
                    </button>
                  )}
                  {c.statut_validation_pedagogique !== "rejete" && (
                    <button
                      onClick={() => setRejectModal({ contenuId: c.id, contenuNom: `Notion #${c.notion_id}` })}
                      className="px-3 py-1.5 bg-red-50 hover:bg-red-100 text-red-700 rounded-lg text-xs font-medium flex items-center gap-1 transition-colors"
                    >
                      <XCircle className="w-3.5 h-3.5" /> Rejeter
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Reject Modal */}
      {rejectModal && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl max-w-md w-full p-6 space-y-4">
            <div className="flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-red-500" />
              <h2 className="text-lg font-semibold text-navy font-display">Rejeter le contenu</h2>
            </div>
            <p className="text-sm text-gray">
              Rejeter le contenu <span className="font-medium text-navy">{rejectModal.contenuNom}</span> ?
              Le contenu repassera en statut "À valider".
            </p>
            <div>
              <label className="text-sm font-medium text-gray block mb-1">Commentaire de rejet (obligatoire)</label>
              <textarea
                value={commentaire}
                onChange={e => setCommentaire(e.target.value)}
                placeholder="Expliquez la raison du rejet..."
                rows={3}
                className="w-full px-4 py-2.5 bg-cream-m rounded-xl border border-black/5 text-sm focus:border-orange focus:outline-none resize-none"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => { setRejectModal(null); setCommentaire(""); }}
                className="px-4 py-2 text-gray border border-black/10 rounded-xl text-sm hover:bg-gray-50"
              >
                Annuler
              </button>
              <button
                onClick={handleRejeter}
                disabled={!commentaire.trim()}
                className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-xl text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Rejeter
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
