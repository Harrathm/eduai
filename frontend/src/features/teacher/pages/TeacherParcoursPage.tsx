import { useState, useEffect, useCallback } from "react";
import { useAuthStore } from "../../../store/authStore";
import { BookOpen, Plus, ChevronDown, ChevronRight, Edit2, FileText, Layers, GraduationCap, X } from "lucide-react";
import {
  listParcours, createParcours, updateParcours,
  listChapitres, createChapitre, updateChapitre,
  listLecons, createLecon, updateLecon,
  listParagraphes, createParagraphe, updateParagraphe,
  type Parcours, type Chapitre, type Lecon, type Paragraphe,
} from "../api/moduleApi";

type TreeItem = {
  parcours: Parcours;
  chapitres: (Chapitre & { lecons: (Lecon & { paragraphes: Paragraphe[] })[] })[];
};

export default function TeacherParcoursPage() {
  const { token } = useAuthStore();
  const [tree, setTree] = useState<TreeItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState({ show: false, message: "", type: "success" as "success" | "error" });
  const [expanded, setExpanded] = useState<Record<number, boolean>>({});
  const [editItem, setEditItem] = useState<{ type: string; item: any } | null>(null);
  const [form, setForm] = useState<Record<string, string>>({});

  const showToast = (message: string, type: "success" | "error" = "success") => {
    setToast({ show: true, message, type });
    setTimeout(() => setToast({ show: false, message: "", type: "success" }), 3000);
  };

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const { items: parcoursList } = await listParcours();
      const treeData: TreeItem[] = await Promise.all(
        parcoursList.map(async (p) => {
          const { items: chapList } = await listChapitres(p.id);
          const chapitres = await Promise.all(
            chapList.map(async (c) => {
              const { items: lecList } = await listLecons(c.id);
              const lecons = await Promise.all(
                lecList.map(async (l) => {
                  const { items: paraList } = await listParagraphes(l.id);
                  return { ...l, paragraphes: paraList };
                })
              );
              return { ...c, lecons };
            })
          );
          return { parcours: p, chapitres };
        })
      );
      setTree(treeData);
    } catch (e: any) {
      showToast(e.message, "error");
    }
    setLoading(false);
  }, [token]);

  useEffect(() => { load(); }, [load]);

  const toggle = (id: number) => setExpanded((p) => ({ ...p, [id]: !p[id] }));

  const openCreate = (type: string, parentId?: number) => {
    setEditItem({ type, item: { id: 0, parent_id: parentId } });
    setForm({});
  };

  const openEdit = (type: string, item: any) => {
    setEditItem({ type, item });
    const f: Record<string, string> = {};
    if (item.titre) f.titre = item.titre;
    if (item.description) f.description = item.description;
    if (item.matiere) f.matiere = item.matiere;
    if (item.niveau_scolaire) f.niveau_scolaire = item.niveau_scolaire;
    if (item.contenu) f.contenu = item.contenu;
    setForm(f);
  };

  const handleSave = async () => {
    if (!editItem) return;
    const { type, item } = editItem;
    try {
      if (type === "parcours") {
        if (item.id) {
          await updateParcours(item.id, form);
        } else {
          await createParcours({ ...form, matiere: form.matiere || "General", niveau_scolaire: form.niveau_scolaire || "1ere annee" });
        }
      } else if (type === "chapitre") {
        if (item.id) {
          await updateChapitre(item.id, form);
        } else {
          await createChapitre(item.parent_id, form);
        }
      } else if (type === "lecon") {
        if (item.id) {
          await updateLecon(item.id, form);
        } else {
          await createLecon(item.parent_id, form);
        }
      } else if (type === "paragraphe") {
        if (item.id) {
          await updateParagraphe(item.id, form);
        } else {
          await createParagraphe(item.parent_id, form);
        }
      }
      showToast(type === "parcours" && !item.id ? "Parcours créé" : "Modifié");
      setEditItem(null);
      load();
    } catch (e: any) {
      showToast(e.message, "error");
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-3xl p-8 shadow-sm border border-black/5 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-[300] text-navy">
            Mes <span className="italic text-orange">Parcours</span>
          </h1>
          <p className="text-gray mt-2">Créez et gérez vos parcours pédagogiques</p>
        </div>
        <button onClick={() => openCreate("parcours")} className="flex items-center gap-2 bg-orange text-white px-4 py-2 rounded-xl hover:bg-orange/90">
          <Plus size={16} /> Nouveau Parcours
        </button>
      </div>

      {toast.show && (
        <div className={`fixed top-4 right-4 z-50 px-4 py-2 rounded-xl text-white ${toast.type === "error" ? "bg-red-500" : "bg-green-500"}`}>
          {toast.message}
        </div>
      )}

      {loading ? (
        <div className="text-center py-20 text-gray">Chargement...</div>
      ) : tree.length === 0 ? (
        <div className="text-center py-20 text-gray">
          <BookOpen size={48} className="mx-auto mb-4 opacity-30" />
          <p>Aucun parcours. Créez-en un pour commencer.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {tree.map((item) => (
            <div key={item.parcours.id} className="bg-white rounded-2xl border border-black/5 overflow-hidden">
              {/* Parcours */}
              <div className="p-4 flex items-center gap-3 hover:bg-gray/5 cursor-pointer" onClick={() => toggle(item.parcours.id)}>
                {expanded[item.parcours.id] ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
                <GraduationCap size={20} className="text-orange" />
                <div className="flex-1">
                  <span className="font-semibold text-navy">{item.parcours.titre}</span>
                  <span className="ml-2 text-xs px-2 py-0.5 rounded-full bg-navy/10 text-navy">{item.parcours.matiere}</span>
                  <span className="ml-2 text-xs text-gray">{item.parcours.niveau_scolaire}</span>
                </div>
                <span className="text-xs text-gray">{item.chapitres.length} chapitres</span>
                <button onClick={(e) => { e.stopPropagation(); openEdit("parcours", item.parcours); }} className="p-1 hover:bg-gray/10 rounded">
                  <Edit2 size={14} />
                </button>
              </div>

              {/* Chapitres */}
              {expanded[item.parcours.id] && (
                <div className="pl-8 pb-2">
                  {item.chapitres.map((chap) => (
                    <div key={chap.id}>
                      <div className="p-3 flex items-center gap-2 hover:bg-gray/5 cursor-pointer" onClick={() => toggle(chap.id)}>
                        {expanded[chap.id] ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                        <Layers size={16} className="text-blue-500" />
                        <span className="flex-1 text-sm">{chap.titre}</span>
                        <button onClick={(e) => { e.stopPropagation(); openEdit("chapitre", chap); }} className="p-1 hover:bg-gray/10 rounded">
                          <Edit2 size={12} />
                        </button>
                      </div>

                      {/* Lecons */}
                      {expanded[chap.id] && (
                        <div className="pl-6">
                          {chap.lecons.map((lec) => (
                            <div key={lec.id}>
                              <div className="p-2 flex items-center gap-2 hover:bg-gray/5 cursor-pointer" onClick={() => toggle(lec.id)}>
                                {expanded[lec.id] ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                                <BookOpen size={14} className="text-green-500" />
                                <span className="flex-1 text-sm">{lec.titre}</span>
                                <button onClick={(e) => { e.stopPropagation(); openEdit("lecon", lec); }} className="p-1 hover:bg-gray/10 rounded">
                                  <Edit2 size={12} />
                                </button>
                              </div>

                              {/* Paragraphes */}
                              {expanded[lec.id] && (
                                <div className="pl-5">
                                  {lec.paragraphes.map((para) => (
                                    <div key={para.id} className="p-2 flex items-center gap-2 text-sm hover:bg-gray/5">
                                      <FileText size={12} className="text-purple-500" />
                                      <span className="flex-1">{para.titre}</span>
                                      <button onClick={() => openEdit("paragraphe", para)} className="p-1 hover:bg-gray/10 rounded">
                                        <Edit2 size={10} />
                                      </button>
                                    </div>
                                  ))}
                                  <button onClick={() => openCreate("paragraphe", lec.id)} className="ml-2 mt-1 text-xs text-blue-500 hover:underline flex items-center gap-1">
                                    <Plus size={10} /> Ajouter un paragraphe
                                  </button>
                                </div>
                              )}
                            </div>
                          ))}
                          <button onClick={() => openCreate("lecon", chap.id)} className="ml-2 mt-1 text-xs text-blue-500 hover:underline flex items-center gap-1">
                            <Plus size={10} /> Ajouter une leçon
                          </button>
                        </div>
                      )}
                    </div>
                  ))}
                  <button onClick={() => openCreate("chapitre", item.parcours.id)} className="ml-2 mt-1 text-xs text-blue-500 hover:underline flex items-center gap-1">
                    <Plus size={10} /> Ajouter un chapitre
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Modal */}
      {editItem && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md shadow-xl">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-navy">
                {editItem.item.id ? "Modifier" : "Créer"} {editItem.type}
              </h3>
              <button onClick={() => setEditItem(null)} className="p-1 hover:bg-gray/10 rounded"><X size={18} /></button>
            </div>
            <div className="space-y-3">
              <input value={form.titre || ""} onChange={(e) => setForm({ ...form, titre: e.target.value })}
                placeholder="Titre" className="w-full border rounded-xl px-3 py-2 text-sm" />
              {editItem.type === "parcours" && (
                <>
                  <input value={form.matiere || ""} onChange={(e) => setForm({ ...form, matiere: e.target.value })}
                    placeholder="Matière" className="w-full border rounded-xl px-3 py-2 text-sm" />
                  <input value={form.niveau_scolaire || ""} onChange={(e) => setForm({ ...form, niveau_scolaire: e.target.value })}
                    placeholder="Niveau scolaire" className="w-full border rounded-xl px-3 py-2 text-sm" />
                  <textarea value={form.description || ""} onChange={(e) => setForm({ ...form, description: e.target.value })}
                    placeholder="Description" className="w-full border rounded-xl px-3 py-2 text-sm h-20" />
                </>
              )}
              {editItem.type === "paragraphe" && (
                <textarea value={form.contenu || ""} onChange={(e) => setForm({ ...form, contenu: e.target.value })}
                  placeholder="Contenu" className="w-full border rounded-xl px-3 py-2 text-sm h-32" />
              )}
            </div>
            <div className="flex gap-2 mt-4 justify-end">
              <button onClick={() => setEditItem(null)} className="px-4 py-2 text-sm text-gray hover:bg-gray/10 rounded-xl">Annuler</button>
              <button onClick={handleSave} className="px-4 py-2 text-sm bg-orange text-white rounded-xl hover:bg-orange/90">Enregistrer</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
