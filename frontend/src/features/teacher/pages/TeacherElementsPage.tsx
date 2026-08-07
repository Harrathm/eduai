import { useState, useEffect, useCallback } from "react";
import { useTranslation } from 'react-i18next';
import { useAuthStore } from "../../../store/authStore";
import { Puzzle, Plus, Edit2, Send, Clock, CheckCircle, XCircle, Eye, X } from "lucide-react";
import {
  listElements, createElement, updateElement, submitElement, getWorkflow,
  createElementTexte, createElementVideo,
  type ElementPedagogique, type WorkflowEntry,
} from "../../../api";
import { Button, PageSpinner, EmptyState, Modal } from "../../../components/ui";

const STATUT_COLORS: Record<string, string> = {
  brouillon: "bg-gray-100 text-gray-600",
  en_review: "bg-yellow-100 text-yellow-700",
  publie: "bg-green-100 text-green-700",
  rejete: "bg-red-100 text-red-600",
};

const TYPE_ICONS: Record<string, string> = {
  texte: "bg-blue-100 text-blue-600",
  video: "bg-purple-100 text-purple-600",
  image: "bg-pink-100 text-pink-600",
  quiz: "bg-orange-100 text-orange-600",
  pdf: "bg-red-100 text-red-600",
};

export default function TeacherElementsPage() {
  const { t } = useTranslation();
  const { token } = useAuthStore();
  const [elements, setElements] = useState<ElementPedagogique[]>([]);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState({ show: false, message: "", type: "success" as "success" | "error" });
  const [createModal, setCreateModal] = useState(false);
  const [editModal, setEditModal] = useState<ElementPedagogique | null>(null);
  const [workflowModal, setWorkflowModal] = useState<{ element: ElementPedagogique; history: WorkflowEntry[] } | null>(null);
  const [subtypeModal, setSubtypeModal] = useState<{ element: ElementPedagogique; type: string } | null>(null);
  const [filter, setFilter] = useState<string>("all");
  const [form, setForm] = useState({ titre: "", type: "texte", description: "", lecon_id: "", difficulte: "moyen" });
  const [subtypeForm, setSubtypeForm] = useState({ contenu_html: "", url: "", duree_secondes: "" });

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
  }, [token, filter]);

  useEffect(() => { load(); }, [load]);

  const handleCreate = async () => {
    try {
      const data: any = { titre: form.titre, type: form.type, difficulte: form.difficulte };
      if (form.description) data.description = form.description;
      if (form.lecon_id) data.lecon_id = parseInt(form.lecon_id);
      const elem = await createElement(data);
      showToast(t('teacher.elements.toasts.created'));
      setCreateModal(false);
      setForm({ titre: "", type: "texte", description: "", lecon_id: "", difficulte: "moyen" });
      setElements((prev) => [elem, ...prev]);
    } catch (e: any) {
      showToast(e.message, "error");
    }
  };

  const handleSubmit = async (id: number) => {
    try {
      await submitElement(id);
      showToast(t('teacher.elements.toasts.submitted'));
      load();
    } catch (e: any) {
      showToast(e.message, "error");
    }
  };

  const handleAddSubtype = async () => {
    if (!subtypeModal) return;
    try {
      if (subtypeModal.type === "texte" && subtypeForm.contenu_html) {
        await createElementTexte(subtypeModal.element.id, { contenu_html: subtypeForm.contenu_html });
      } else if (subtypeModal.type === "video" && subtypeForm.url) {
        await createElementVideo(subtypeModal.element.id, { url: subtypeForm.url, duree_secondes: parseInt(subtypeForm.duree_secondes || "0") });
      }
      showToast(t('teacher.elements.toasts.contentAdded'));
      setSubtypeModal(null);
      setSubtypeForm({ contenu_html: "", url: "", duree_secondes: "" });
    } catch (e: any) {
      showToast(e.message, "error");
    }
  };

  const openWorkflow = async (element: ElementPedagogique) => {
    try {
      const history = await getWorkflow(element.id);
      setWorkflowModal({ element, history });
    } catch (e: any) {
      showToast(e.message, "error");
    }
  };

  const filtered = filter === "all" ? elements : elements.filter((e) => e.statut === filter);

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-3xl p-8 shadow-sm border border-black/5 flex justify-between items-center">
        <div>
            <h1 className="text-3xl font-[300] text-navy">
              {t('teacher.elements.title')} <span className="italic text-orange">{t('teacher.elements.titleSuffix')}</span>
            </h1>
            <p className="text-gray mt-2">{t('teacher.elements.subtitle')}</p>
        </div>
        <Button onClick={() => setCreateModal(true)}>
          <Plus size={16} /> {t('teacher.elements.newElement')}
        </Button>
      </div>

      {toast.show && (
        <div className={`fixed top-4 right-4 z-50 px-4 py-2 rounded-xl text-white ${toast.type === "error" ? "bg-red-500" : "bg-green-500"}`}>
          {toast.message}
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-2 flex-wrap">
        {["all", "brouillon", "en_review", "publie", "rejete"].map((f) => (
          <Button key={f} variant={filter === f ? "secondary" : "ghost"} size="sm" onClick={() => setFilter(f)}>
            {f === "all" ? t('teacher.elements.filters.all') : f === "brouillon" ? t('teacher.elements.filters.draft') : f === "en_review" ? t('teacher.elements.filters.review') : f === "publie" ? t('teacher.elements.filters.published') : t('teacher.elements.filters.rejected')}
          </Button>
        ))}
      </div>

      {loading ? (
        <PageSpinner message={t('teacher.elements.loading')} />
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={<Puzzle size={48} />}
          title={t('teacher.elements.noResults')}
        />
      ) : (
        <div className="grid gap-3">
          {filtered.map((el) => (
            <div key={el.id} className="bg-white rounded-2xl border border-black/5 p-4 flex items-center gap-4 hover:shadow-sm transition-shadow">
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center text-xs font-bold ${TYPE_ICONS[el.type] || "bg-gray-100"}`}>
                {el.type.toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-navy truncate">{el.titre}</span>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${STATUT_COLORS[el.statut] || ""}`}>{el.statut}</span>
                </div>
                {el.description && <p className="text-sm text-gray truncate mt-0.5">{el.description}</p>}
              </div>
              <div className="flex items-center gap-1">
                {el.statut === "brouillon" && (
                  <Button variant="secondary" size="sm" onClick={() => handleSubmit(el.id)} title={t('teacher.elements.btn.submit')}>
                    <Send size={14} />
                  </Button>
                )}
                <Button variant="ghost" size="sm" onClick={() => setSubtypeModal({ element: el, type: el.type })} title={t('teacher.elements.btn.addContent')}>
                  <Plus size={14} />
                </Button>
                <Button variant="ghost" size="sm" onClick={() => openWorkflow(el)} title="Workflow">
                  <Clock size={14} />
                </Button>
                <Button variant="ghost" size="sm" onClick={() => setEditModal(el)} title={t('teacher.elements.btn.edit')}>
                  <Edit2 size={14} />
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Modal */}
      <Modal open={createModal} onClose={() => setCreateModal(false)} title={t('teacher.elements.modal.newElement')}>
        <div className="space-y-3">
          <input value={form.titre} onChange={(e) => setForm({ ...form, titre: e.target.value })} placeholder={t('teacher.elements.fields.title')} className="w-full border rounded-xl px-3 py-2 text-sm" />
          <select value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })} className="w-full border rounded-xl px-3 py-2 text-sm">
            <option value="texte">{t('teacher.elements.types.texte')}</option>
            <option value="video">{t('teacher.elements.types.video')}</option>
            <option value="image">{t('teacher.elements.types.image')}</option>
            <option value="quiz">{t('teacher.elements.types.quiz')}</option>
            <option value="pdf">PDF</option>
          </select>
          <input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder={t('teacher.elements.fields.description')} className="w-full border rounded-xl px-3 py-2 text-sm" />
          <input value={form.lecon_id} onChange={(e) => setForm({ ...form, lecon_id: e.target.value })} placeholder={t('teacher.elements.fields.leconId')} type="number" className="w-full border rounded-xl px-3 py-2 text-sm" />
          <select value={form.difficulte} onChange={(e) => setForm({ ...form, difficulte: e.target.value })} className="w-full border rounded-xl px-3 py-2 text-sm">
            <option value="facile">{t('teacher.elements.difficulty.facile')}</option>
            <option value="moyen">{t('teacher.elements.difficulty.moyen')}</option>
            <option value="difficile">{t('teacher.elements.difficulty.difficile')}</option>
          </select>
        </div>
        <div className="flex gap-2 mt-4 justify-end">
          <Button variant="ghost" size="sm" onClick={() => setCreateModal(false)}>{t('teacher.elements.btn.cancel')}</Button>
          <Button size="sm" onClick={handleCreate}>{t('teacher.elements.btn.create')}</Button>
        </div>
      </Modal>

      {/* Subtype Modal */}
      <Modal open={!!subtypeModal} onClose={() => setSubtypeModal(null)} title={subtypeModal ? `${t('teacher.elements.modal.addContent')} ${subtypeModal.type}` : ''}>
        <div className="space-y-3">
          {subtypeModal?.type === "texte" && (
            <textarea value={subtypeForm.contenu_html} onChange={(e) => setSubtypeForm({ ...subtypeForm, contenu_html: e.target.value })}
              placeholder={t('teacher.elements.fields.contenuHtml')} className="w-full border rounded-xl px-3 py-2 text-sm h-32" />
          )}
          {subtypeModal?.type === "video" && (
            <>
              <input value={subtypeForm.url} onChange={(e) => setSubtypeForm({ ...subtypeForm, url: e.target.value })}
                placeholder={t('teacher.elements.fields.urlVideo')} className="w-full border rounded-xl px-3 py-2 text-sm" />
              <input value={subtypeForm.duree_secondes} onChange={(e) => setSubtypeForm({ ...subtypeForm, duree_secondes: e.target.value })}
                placeholder={t('teacher.elements.fields.duree')} type="number" className="w-full border rounded-xl px-3 py-2 text-sm" />
            </>
          )}
          {subtypeModal?.type === "quiz" && (
            <p className="text-sm text-gray">{t('teacher.elements.fields.quizSoon')}</p>
          )}
        </div>
        <div className="flex gap-2 mt-4 justify-end">
          <Button variant="ghost" size="sm" onClick={() => setSubtypeModal(null)}>{t('teacher.elements.btn.cancel')}</Button>
          <Button size="sm" onClick={handleAddSubtype}>{t('teacher.elements.btn.save')}</Button>
        </div>
      </Modal>

      {/* Workflow Modal */}
      <Modal open={!!workflowModal} onClose={() => setWorkflowModal(null)} title={workflowModal ? `${t('teacher.elements.modal.workflow')}: ${workflowModal.element.titre}` : ''}>
        {workflowModal && (
          <>
            {workflowModal.history.length === 0 ? (
              <p className="text-sm text-gray text-center py-4">{t('teacher.elements.workflow.noTransitions')}</p>
            ) : (
              <div className="space-y-2">
                {workflowModal.history.map((w) => (
                  <div key={w.id} className="flex items-center gap-2 text-sm p-2 bg-gray/5 rounded-lg">
                    <Clock size={12} className="text-gray" />
                    <span className="text-gray">{w.from_statut}</span>
                    <span className="text-navy">→</span>
                    <span className={`font-medium ${w.to_statut === "publie" ? "text-green-600" : w.to_statut === "rejete" ? "text-red-500" : "text-blue-600"}`}>{w.to_statut}</span>
                    {w.commentaire && <span className="text-gray text-xs italic">"{w.commentaire}"</span>}
                    <span className="ml-auto text-xs text-gray">{new Date(w.created_at).toLocaleDateString("fr")}</span>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </Modal>

      {/* Edit Modal */}
      <Modal open={!!editModal} onClose={() => setEditModal(null)} title={editModal ? `${t('teacher.elements.modal.edit')}: ${editModal.titre}` : ''}>
        <div className="space-y-3">
          <input defaultValue={editModal?.titre} onChange={(e) => setForm({ ...form, titre: e.target.value })} placeholder={t('teacher.elements.fields.title')} className="w-full border rounded-xl px-3 py-2 text-sm" />
          <input defaultValue={editModal?.description || ""} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder={t('teacher.elements.fields.description')} className="w-full border rounded-xl px-3 py-2 text-sm" />
          <select defaultValue={editModal?.difficulte} onChange={(e) => setForm({ ...form, difficulte: e.target.value })} className="w-full border rounded-xl px-3 py-2 text-sm">
            <option value="facile">{t('teacher.elements.difficulty.facile')}</option>
            <option value="moyen">{t('teacher.elements.difficulty.moyen')}</option>
            <option value="difficile">{t('teacher.elements.difficulty.difficile')}</option>
          </select>
        </div>
        <div className="flex gap-2 mt-4 justify-end">
          <Button variant="ghost" size="sm" onClick={() => setEditModal(null)}>{t('teacher.elements.btn.cancel')}</Button>
          <Button size="sm" onClick={async () => {
            try {
              await updateElement(editModal!.id, form);
              showToast(t('teacher.elements.toasts.modified'));
              setEditModal(null);
              load();
            } catch (e: any) { showToast(e.message, "error"); }
          }}>{t('teacher.elements.btn.save')}</Button>
        </div>
      </Modal>
    </div>
  );
}
