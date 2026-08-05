import { useState, useEffect, useCallback } from "react";
import { useAuthStore } from "../../../store/authStore";
import { Puzzle, Plus, Edit2, Send, Clock, CheckCircle, XCircle, Eye, X } from "lucide-react";
import {
  listElements, createElement, updateElement, submitElement, getWorkflow,
  createElementTexte, createElementVideo,
  type ElementPedagogique, type WorkflowEntry,
} from "../../../api";

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
      showToast("Élément créé");
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
      showToast("Soumis pour validation");
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
      showToast("Contenu ajouté");
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
            Éléments <span className="italic text-orange">Pédagogiques</span>
          </h1>
          <p className="text-gray mt-2">Créez et gérez vos contenus pédagogiques</p>
        </div>
        <button onClick={() => setCreateModal(true)} className="flex items-center gap-2 bg-orange text-white px-4 py-2 rounded-xl hover:bg-orange/90">
          <Plus size={16} /> Nouvel Élément
        </button>
      </div>

      {toast.show && (
        <div className={`fixed top-4 right-4 z-50 px-4 py-2 rounded-xl text-white ${toast.type === "error" ? "bg-red-500" : "bg-green-500"}`}>
          {toast.message}
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-2 flex-wrap">
        {["all", "brouillon", "en_review", "publie", "rejete"].map((f) => (
          <button key={f} onClick={() => setFilter(f)}
            className={`px-3 py-1.5 rounded-full text-sm ${filter === f ? "bg-navy text-white" : "bg-gray/10 text-gray hover:bg-gray/20"}`}>
            {f === "all" ? "Tous" : f === "brouillon" ? "Brouillon" : f === "en_review" ? "En Review" : f === "publie" ? "Publié" : "Rejeté"}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="text-center py-20 text-gray">Chargement...</div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-20 text-gray">
          <Puzzle size={48} className="mx-auto mb-4 opacity-30" />
          <p>Aucun élément trouvé</p>
        </div>
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
                  <button onClick={() => handleSubmit(el.id)} title="Soumettre" className="p-2 hover:bg-blue-50 rounded-lg text-blue-600">
                    <Send size={14} />
                  </button>
                )}
                <button onClick={() => setSubtypeModal({ element: el, type: el.type })} title="Ajouter contenu" className="p-2 hover:bg-green-50 rounded-lg text-green-600">
                  <Plus size={14} />
                </button>
                <button onClick={() => openWorkflow(el)} title="Workflow" className="p-2 hover:bg-gray-100 rounded-lg text-gray">
                  <Clock size={14} />
                </button>
                <button onClick={() => setEditModal(el)} title="Modifier" className="p-2 hover:bg-gray-100 rounded-lg text-gray">
                  <Edit2 size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Modal */}
      {createModal && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md shadow-xl">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-navy">Nouvel Élément</h3>
              <button onClick={() => setCreateModal(false)} className="p-1 hover:bg-gray/10 rounded"><X size={18} /></button>
            </div>
            <div className="space-y-3">
              <input value={form.titre} onChange={(e) => setForm({ ...form, titre: e.target.value })} placeholder="Titre" className="w-full border rounded-xl px-3 py-2 text-sm" />
              <select value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })} className="w-full border rounded-xl px-3 py-2 text-sm">
                <option value="texte">Texte</option>
                <option value="video">Vidéo</option>
                <option value="image">Image</option>
                <option value="quiz">Quiz</option>
                <option value="pdf">PDF</option>
              </select>
              <input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder="Description (optionnel)" className="w-full border rounded-xl px-3 py-2 text-sm" />
              <input value={form.lecon_id} onChange={(e) => setForm({ ...form, lecon_id: e.target.value })} placeholder="Lecon ID (optionnel)" type="number" className="w-full border rounded-xl px-3 py-2 text-sm" />
              <select value={form.difficulte} onChange={(e) => setForm({ ...form, difficulte: e.target.value })} className="w-full border rounded-xl px-3 py-2 text-sm">
                <option value="facile">Facile</option>
                <option value="moyen">Moyen</option>
                <option value="difficile">Difficile</option>
              </select>
            </div>
            <div className="flex gap-2 mt-4 justify-end">
              <button onClick={() => setCreateModal(false)} className="px-4 py-2 text-sm text-gray hover:bg-gray/10 rounded-xl">Annuler</button>
              <button onClick={handleCreate} className="px-4 py-2 text-sm bg-orange text-white rounded-xl hover:bg-orange/90">Créer</button>
            </div>
          </div>
        </div>
      )}

      {/* Subtype Modal */}
      {subtypeModal && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md shadow-xl">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-navy">Ajouter contenu {subtypeModal.type}</h3>
              <button onClick={() => setSubtypeModal(null)} className="p-1 hover:bg-gray/10 rounded"><X size={18} /></button>
            </div>
            <div className="space-y-3">
              {subtypeModal.type === "texte" && (
                <textarea value={subtypeForm.contenu_html} onChange={(e) => setSubtypeForm({ ...subtypeForm, contenu_html: e.target.value })}
                  placeholder="Contenu HTML" className="w-full border rounded-xl px-3 py-2 text-sm h-32" />
              )}
              {subtypeModal.type === "video" && (
                <>
                  <input value={subtypeForm.url} onChange={(e) => setSubtypeForm({ ...subtypeForm, url: e.target.value })}
                    placeholder="URL vidéo" className="w-full border rounded-xl px-3 py-2 text-sm" />
                  <input value={subtypeForm.duree_secondes} onChange={(e) => setSubtypeForm({ ...subtypeForm, duree_secondes: e.target.value })}
                    placeholder="Durée (secondes)" type="number" className="w-full border rounded-xl px-3 py-2 text-sm" />
                </>
              )}
              {subtypeModal.type === "quiz" && (
                <p className="text-sm text-gray">Formulaire quiz à venir</p>
              )}
            </div>
            <div className="flex gap-2 mt-4 justify-end">
              <button onClick={() => setSubtypeModal(null)} className="px-4 py-2 text-sm text-gray hover:bg-gray/10 rounded-xl">Annuler</button>
              <button onClick={handleAddSubtype} className="px-4 py-2 text-sm bg-orange text-white rounded-xl hover:bg-orange/90">Enregistrer</button>
            </div>
          </div>
        </div>
      )}

      {/* Workflow Modal */}
      {workflowModal && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md shadow-xl">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-navy">Workflow: {workflowModal.element.titre}</h3>
              <button onClick={() => setWorkflowModal(null)} className="p-1 hover:bg-gray/10 rounded"><X size={18} /></button>
            </div>
            {workflowModal.history.length === 0 ? (
              <p className="text-sm text-gray text-center py-4">Aucune transition enregistrée</p>
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
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {editModal && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md shadow-xl">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-navy">Modifier: {editModal.titre}</h3>
              <button onClick={() => setEditModal(null)} className="p-1 hover:bg-gray/10 rounded"><X size={18} /></button>
            </div>
            <div className="space-y-3">
              <input defaultValue={editModal.titre} onChange={(e) => setForm({ ...form, titre: e.target.value })} placeholder="Titre" className="w-full border rounded-xl px-3 py-2 text-sm" />
              <input defaultValue={editModal.description || ""} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder="Description" className="w-full border rounded-xl px-3 py-2 text-sm" />
              <select defaultValue={editModal.difficulte} onChange={(e) => setForm({ ...form, difficulte: e.target.value })} className="w-full border rounded-xl px-3 py-2 text-sm">
                <option value="facile">Facile</option>
                <option value="moyen">Moyen</option>
                <option value="difficile">Difficile</option>
              </select>
            </div>
            <div className="flex gap-2 mt-4 justify-end">
              <button onClick={() => setEditModal(null)} className="px-4 py-2 text-sm text-gray hover:bg-gray/10 rounded-xl">Annuler</button>
              <button onClick={async () => {
                try {
                  await updateElement(editModal.id, form);
                  showToast("Élément modifié");
                  setEditModal(null);
                  load();
                } catch (e: any) { showToast(e.message, "error"); }
              }} className="px-4 py-2 text-sm bg-orange text-white rounded-xl hover:bg-orange/90">Enregistrer</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
