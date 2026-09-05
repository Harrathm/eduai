import { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { CheckCircle, XCircle, Clock, Eye, RefreshCw, Filter, Library, AlertTriangle } from "lucide-react";
import { useAuthStore } from "../../../store/authStore";
import { listElements, validateElement, rejectElement, type ElementPedagogique } from "../../../api";
import { Button, PageSpinner, EmptyState, Modal } from "../../../components/ui";

const STATUT_COLORS: Record<string, string> = {
  brouillon: "bg-gray-100 text-gray-600",
  brouillon_ia: "bg-purple-100 text-purple-600",
  en_review: "bg-yellow-100 text-yellow-700",
  publie: "bg-green-100 text-green-700",
  rejete: "bg-red-100 text-red-600",
};

const TYPE_COLORS: Record<string, string> = {
  texte: "bg-blue-50 text-blue-600",
  video: "bg-purple-50 text-purple-600",
  image: "bg-pink-50 text-pink-600",
  quiz: "bg-orange-50 text-orange-600",
  pdf: "bg-red-50 text-red-600",
};

export default function AdminLibraryReviewPage() {
  const { t } = useTranslation();
  const { token, user } = useAuthStore();
  const [elements, setElements] = useState<ElementPedagogique[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>("en_review");
  const [processing, setProcessing] = useState<number | null>(null);
  const [detailModal, setDetailModal] = useState<ElementPedagogique | null>(null);
  const [rejectComment, setRejectComment] = useState("");
  const [toast, setToast] = useState({ show: false, message: "", type: "success" as "success" | "error" });

  const showToast = (message: string, type: "success" | "error" = "success") => {
    setToast({ show: true, message, type });
    setTimeout(() => setToast({ show: false, message: "", type: "success" }), 3000);
  };

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      if (filter !== "all") params.statut = filter;
      const { items } = await listElements(params);
      setElements(items);
    } catch (e: any) {
      showToast(e.message, "error");
    }
    setLoading(false);
  }, [filter]);

  useEffect(() => { load(); }, [load]);

  const handleValidate = async (id: number) => {
    setProcessing(id);
    try {
      await validateElement(id, "Approuvé par l'administration");
      showToast("Élément approuvé");
      load();
    } catch (e: any) {
      showToast(e.message, "error");
    }
    setProcessing(null);
  };

  const handleReject = async (id: number) => {
    setProcessing(id);
    try {
      await rejectElement(id, rejectComment || "Non conforme");
      showToast("Élément rejeté");
      setRejectComment("");
      setDetailModal(null);
      load();
    } catch (e: any) {
      showToast(e.message, "error");
    }
    setProcessing(null);
  };

  const filtered = filter === "all" ? elements : elements.filter((e) => e.statut === filter);

  if (user?.role?.toUpperCase() !== "PEDAGOGICAL_ADMIN" && user?.role?.toUpperCase() !== "SUPER_ADMIN") {
    return (
      <div className="space-y-6">
        <div className="bg-white rounded-3xl p-8 shadow-sm border border-black/5">
          <h1 className="text-3xl font-[300] text-navy">
            Validation <span className="italic text-orange">Bibliothèque</span>
          </h1>
        </div>
        <div className="bg-white rounded-2xl p-12 shadow-sm border border-black/5 text-center">
          <AlertTriangle className="w-16 h-16 text-yellow-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-700 mb-2">Accès restreint</h3>
          <p className="text-gray-500">Cette page est réservée aux administrateurs pédagogiques.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-3xl p-8 shadow-sm border border-black/5 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-[300] text-navy">
            Validation <span className="italic text-orange">Bibliothèque</span>
          </h1>
          <p className="text-gray mt-2">Approuvez ou rejetez les éléments pédagogiques soumis pour validation</p>
        </div>
        <Button variant="ghost" size="sm" onClick={load} disabled={loading}>
          <RefreshCw className={`w-5 h-5 text-gray ${loading ? "animate-spin" : ""}`} />
        </Button>
      </div>

      {toast.show && (
        <div className={`fixed top-4 right-4 z-50 px-4 py-2 rounded-xl text-white ${toast.type === "error" ? "bg-red-500" : "bg-green-500"}`}>
          {toast.message}
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-2xl p-4 shadow-sm border border-black/5 flex items-center gap-4">
        <Filter className="w-5 h-5 text-gray" />
        {["en_review", "brouillon_ia", "all", "publie", "rejete"].map((f) => (
          <Button key={f} variant={filter === f ? "secondary" : "ghost"} size="sm" onClick={() => setFilter(f)}>
            {f === "all" ? "Tous" : f === "en_review" ? "En revue" : f === "brouillon_ia" ? "Brouillon IA" : f === "publie" ? "Publiés" : "Rejetés"}
          </Button>
        ))}
      </div>

      {/* Element List */}
      {loading ? (
        <PageSpinner message="Chargement..." />
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={<Library size={48} />}
          title={filter === "en_review" || filter === "brouillon_ia" ? "Aucun élément en attente de validation" : "Aucun élément trouvé"}
        />
      ) : (
        <div className="grid gap-3">
          {filtered.map((el) => (
            <div key={el.id} className="bg-white rounded-2xl border border-black/5 p-4 flex items-center gap-4 hover:shadow-sm transition-shadow">
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center text-xs font-bold ${TYPE_COLORS[el.type] || "bg-gray-100"}`}>
                {el.type.toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-navy truncate">{el.titre}</span>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${STATUT_COLORS[el.statut] || ""}`}>
                    {el.statut === "brouillon_ia" ? "Brouillon IA" : el.statut}
                  </span>
                  <span className="text-xs text-gray">#{el.id}</span>
                </div>
                {el.description && <p className="text-sm text-gray truncate mt-0.5">{el.description}</p>}
                <div className="flex items-center gap-3 mt-1">
                  {el.matiere_id && <span className="text-xs text-gray">Matière #{el.matiere_id}</span>}
                  {el.niveau_etude_id && <span className="text-xs text-gray">Niveau #{el.niveau_etude_id}</span>}
                  {el.difficulte && <span className="text-xs text-gray">{el.difficulte}</span>}
                </div>
              </div>
              <div className="flex items-center gap-1">
                <Button variant="ghost" size="sm" onClick={() => setDetailModal(el)} title="Voir détails">
                  <Eye size={14} />
                </Button>
                {(el.statut === "en_review" || el.statut === "brouillon_ia") && (
                  <>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => handleValidate(el.id)}
                      disabled={processing === el.id}
                      title="Approuver"
                      className="text-green-600 hover:bg-green-50"
                    >
                      <CheckCircle size={14} />
                    </Button>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => { setDetailModal(el); setRejectComment(""); }}
                      disabled={processing === el.id}
                      title="Rejeter"
                      className="text-red-500 hover:bg-red-50"
                    >
                      <XCircle size={14} />
                    </Button>
                  </>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Detail Modal */}
      <Modal open={!!detailModal} onClose={() => { setDetailModal(null); setRejectComment(""); }} title={detailModal ? `Détail: ${detailModal.titre}` : ""}>
        {detailModal && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray">Type</span>
                <p className="font-medium text-navy">{detailModal.type}</p>
              </div>
              <div>
                <span className="text-gray">Statut</span>
                <p><span className={`text-xs px-2 py-0.5 rounded-full ${STATUT_COLORS[detailModal.statut] || ""}`}>{detailModal.statut}</span></p>
              </div>
              <div>
                <span className="text-gray">Difficulté</span>
                <p className="font-medium text-navy">{detailModal.difficulte}</p>
              </div>
              <div>
                <span className="text-gray">Auteur ID</span>
                <p className="font-medium text-navy">{detailModal.auteur_id || "—"}</p>
              </div>
            </div>
            {detailModal.description && (
              <div>
                <span className="text-gray text-sm">Description</span>
                <p className="text-sm text-navy mt-1">{detailModal.description}</p>
              </div>
            )}
            <div className="flex items-center gap-4 text-xs text-gray">
              <span>Créé le {detailModal.created_at ? new Date(detailModal.created_at).toLocaleDateString("fr-FR") : "—"}</span>
              {detailModal.est_global && <span className="px-2 py-0.5 rounded-full bg-blue-100 text-blue-600">Global</span>}
              {detailModal.est_libre && <span className="px-2 py-0.5 rounded-full bg-green-100 text-green-600">Libre</span>}
            </div>

            {(detailModal.statut === "en_review" || detailModal.statut === "brouillon_ia") && (
              <div className="border-t border-black/5 pt-4 space-y-3">
                <div className="flex gap-2">
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => handleValidate(detailModal.id)}
                    disabled={processing === detailModal.id}
                    className="text-green-600 hover:bg-green-50"
                  >
                    <CheckCircle size={14} /> Approuver
                  </Button>
                </div>
                <div>
                  <label className="text-sm text-gray mb-1 block">Commentaire de rejet (optionnel)</label>
                  <textarea
                    value={rejectComment}
                    onChange={(e) => setRejectComment(e.target.value)}
                    placeholder="Raison du rejet..."
                    className="w-full border rounded-xl px-3 py-2 text-sm h-20"
                  />
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => handleReject(detailModal.id)}
                    disabled={processing === detailModal.id}
                    className="mt-2 bg-red-500 hover:bg-red-600"
                  >
                    <XCircle size={14} /> Rejeter
                  </Button>
                </div>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
}
