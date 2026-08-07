import { useState, useEffect, useCallback } from "react";
import { useTranslation } from 'react-i18next';
import { CheckCircle, XCircle, AlertTriangle } from "lucide-react";
import { useAuthStore } from "../../../store/authStore";
import { pathwayResponsables, pathwayContenus } from "../../../api";
import { Button, Modal, PageSpinner, EmptyState } from "../../../components/ui";

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
  const { t } = useTranslation();
  const { token, user } = useAuthStore();
  const [contenus, setContenus] = useState<ContenuItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [rejectModal, setRejectModal] = useState<{ contenuId: number; contenuNom: string } | null>(null);
  const [commentaire, setCommentaire] = useState("");
  const [filter, setFilter] = useState<"all" | "en_attente" | "valide" | "rejete">("all");
  const [toast, setToast] = useState({ show: false, message: "", type: "success" as "success" | "error" });

  const showToast = (message: string, type: "success" | "error" = "success") => {
    setToast({ show: true, message, type });
    setTimeout(() => setToast({ show: false, message: "", type: "success" }), 3000);
  };

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      if (!user?.id) {
        setError(t('teacher.validation.loading'));
        setLoading(false);
        return;
      }
      const data = await pathwayResponsables.listContenus(user.id);
      setContenus(data);
    } catch {
      setError(t('teacher.validation.error'));
    }
    setLoading(false);
  }, [user?.id]);

  useEffect(() => { load(); }, [load]);

  const handleValider = async (contenuId: number) => {
    try {
      await pathwayContenus.valider(contenuId);
      showToast(t('teacher.validation.toasts.validated'));
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
      await pathwayContenus.rejeter(rejectModal.contenuId, commentaire);
      showToast(t('teacher.validation.toasts.rejected'));
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
        return <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded-full text-xs font-medium">{t('teacher.validation.badges.validated')}</span>;
      case "rejete":
        return <span className="px-2 py-0.5 bg-red-100 text-red-700 rounded-full text-xs font-medium">{t('teacher.validation.badges.rejected')}</span>;
      default:
        return <span className="px-2 py-0.5 bg-yellow-100 text-yellow-700 rounded-full text-xs font-medium">{t('teacher.validation.badges.pending')}</span>;
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
          {t('teacher.validation.title')} <span className="italic text-orange">{t('teacher.validation.titleSuffix')}</span>
        </h1>
        <p className="text-gray text-sm mt-1">{t('teacher.validation.subtitle')}</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: t('teacher.validation.stats.total'), value: stats.total, className: "text-navy" },
          { label: t('teacher.validation.stats.pending'), value: stats.en_attente, className: "text-yellow-600" },
          { label: t('teacher.validation.stats.validated'), value: stats.valide, className: "text-green-600" },
          { label: t('teacher.validation.stats.rejected'), value: stats.rejete, className: "text-red-600" },
        ].map(s => (
          <div key={s.label} className="bg-white rounded-xl shadow-sm border border-black/5 p-4">
            <div className={`text-2xl font-bold font-display ${s.className}`}>{s.value}</div>
            <div className="text-xs text-gray mt-0.5">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex gap-2">
        {(["all", "en_attente", "valide", "rejete"] as const).map(f => (
          <Button
            key={f}
            onClick={() => setFilter(f)}
            variant={filter === f ? "secondary" : "ghost"}
            size="md"
          >
            {f === "all" ? t('teacher.validation.filters.all') : f === "en_attente" ? t('teacher.validation.filters.pending') : f === "valide" ? t('teacher.validation.filters.validated') : t('teacher.validation.filters.rejected')}
          </Button>
        ))}
      </div>

      {/* Contenus */}
      {loading ? (
        <PageSpinner />
      ) : error ? (
        <EmptyState
          title={error}
          description={error}
        />
      ) : filtered.length === 0 ? (
        <EmptyState
          title="Aucun contenu à afficher"
          description={filter === "all" ? "Vous n'avez aucun contenu dans votre périmètre" : `Aucun contenu "${filter}"`}
        />
      ) : (
        <div className="bg-white rounded-2xl shadow-sm border border-black/5 overflow-hidden">
          <div className="px-6 py-4 bg-gray-50 border-b border-black/5">
            <div className="grid grid-cols-6 gap-4 text-xs font-semibold text-gray uppercase">
              <div>ID</div>
              <div>Notion</div>
              <div>Niveau</div>
              <div>Type</div>
              <div>Statut</div>
              <div className="text-end">Actions</div>
            </div>
          </div>
          <div className="divide-y divide-gray-100">
            {filtered.map(c => (
              <div key={c.id} className="px-6 py-4 grid grid-cols-6 gap-4 items-center hover:bg-gray-50/50 transition-colors">
                <div className="text-sm text-gray font-mono">#{c.id}</div>
                <div className="text-sm text-navy font-medium">Contenu #{c.id}</div>
                <div className="text-xs px-2 py-0.5 bg-cream-m rounded-full text-gray inline-block w-fit">
                  {c.niveau_assimilation}
                </div>
                <div className="text-sm text-gray">{c.type_ressource}</div>
                <div>{statusBadge(c.statut_validation_pedagogique)}</div>
                <div className="flex justify-end gap-2">
                  {c.statut_validation_pedagogique !== "valide" && (
                    <Button
                      onClick={() => handleValider(c.id)}
                      variant="success"
                      size="sm"
                    >
                      <CheckCircle className="w-3.5 h-3.5" /> Valider
                    </Button>
                  )}
                  {c.statut_validation_pedagogique !== "rejete" && (
                    <Button
                      onClick={() => setRejectModal({ contenuId: c.id, contenuNom: `Contenu #${c.id}` })}
                      variant="danger"
                      size="sm"
                    >
                      <XCircle className="w-3.5 h-3.5" /> Rejeter
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Reject Modal */}
      <Modal
        open={!!rejectModal}
        onClose={() => { setRejectModal(null); setCommentaire(""); }}
        title="Rejeter le contenu"
        maxWidth="max-w-md"
      >
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-red-500" />
          </div>
          <p className="text-sm text-gray">
            Rejeter le contenu <span className="font-medium text-navy">{rejectModal?.contenuNom}</span> ?
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
            <Button
              onClick={() => { setRejectModal(null); setCommentaire(""); }}
              variant="ghost"
              size="md"
            >
              Annuler
            </Button>
            <Button
              onClick={handleRejeter}
              disabled={!commentaire.trim()}
              variant="danger"
              size="md"
            >
              Rejeter
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
