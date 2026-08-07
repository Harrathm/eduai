import { useState, useEffect, useCallback } from "react";
import { ChevronDown, ChevronRight, Plus, Pencil, Trash2, Check, X, Layers, BookOpen, FileText, Lightbulb } from "lucide-react";
import { Button } from "../../../components/ui";
import {
  getNiveauxEtude, createNiveauEtude, updateNiveauEtude, deleteNiveauEtude,
  getMatieres, createMatiere, updateMatiere, deleteMatiere,
  getChapters, createChapter, updateChapter, deleteChapter,
  getNotions, createNotion, updateNotion, deleteNotion,
  getStatutPublication,
} from "../../../api";
import type { NiveauEtude, Matiere, ChapterPathway, Notion, StatutPublication } from "../../../api";

type EditableItem = {
  id?: number;
  nom: string;
  ordre?: number;
  niveau_etude_id?: number;
  matiere_id?: number;
  chapitre_id?: number;
};

export default function AdminArborescencePage() {
  const [niveaux, setNiveaux] = useState<NiveauEtude[]>([]);
  const [matieres, setMatieres] = useState<Matiere[]>([]);
  const [chapters, setChapters] = useState<ChapterPathway[]>([]);
  const [notions, setNotions] = useState<Notion[]>([]);
  const [expanded, setExpanded] = useState<Record<string, number[]>>({});
  const [editing, setEditing] = useState<string | null>(null);
  const [editValue, setEditValue] = useState<EditableItem>({ nom: "" });
  const [toast, setToast] = useState({ show: false, message: "", type: "success" as "success" | "error" });

  const showToast = (message: string, type: "success" | "error" = "success") => {
    setToast({ show: true, message, type });
    setTimeout(() => setToast({ show: false, message: "", type: "success" }), 3000);
  };

  const toggle = (key: string, id: number) => {
    setExpanded(prev => {
      const arr = prev[key] || [];
      return { ...prev, [key]: arr.includes(id) ? arr.filter(x => x !== id) : [...arr, id] };
    });
  };

  const loadAll = useCallback(async () => {
    try {
      const [n, m, c, no] = await Promise.all([getNiveauxEtude(), getMatieres(), getChapters(), getNotions()]);
      setNiveaux(n); setMatieres(m); setChapters(c); setNotions(no);
    } catch { showToast("Erreur chargement", "error"); }
  }, []);

  useEffect(() => { loadAll(); }, [loadAll]);

  const save = async (type: string, data: EditableItem, parentId?: number) => {
    try {
      if (type === "niveau") {
        if (data.id) await updateNiveauEtude(data.id, { nom: data.nom, ordre: data.ordre || 0 });
        else await createNiveauEtude({ nom: data.nom, ordre: data.ordre || 0 });
      } else if (type === "matiere") {
        if (data.id) await updateMatiere(data.id, { niveau_etude_id: parentId || 0, nom: data.nom });
        else await createMatiere({ niveau_etude_id: parentId || 0, nom: data.nom });
      } else if (type === "chapitre") {
        if (data.id) await updateChapter(data.id, { matiere_id: parentId || 0, nom: data.nom, ordre: data.ordre || 0 });
        else await createChapter({ matiere_id: parentId || 0, nom: data.nom, ordre: data.ordre || 0 });
      } else if (type === "notion") {
        if (data.id) await updateNotion(data.id, { chapitre_id: parentId || 0, nom: data.nom, ordre: data.ordre || 0 });
        else await createNotion({ chapitre_id: parentId || 0, nom: data.nom, ordre: data.ordre || 0 });
      }
      showToast("Sauvegardé");
      setEditing(null);
      loadAll();
    } catch (err: any) { showToast(err.message || "Erreur", "error"); }
  };

  const remove = async (type: string, id: number) => {
    if (!confirm("Supprimer cet élément et toutes ses sous-entrées ?")) return;
    try {
      if (type === "niveau") await deleteNiveauEtude(id);
      else if (type === "matiere") await deleteMatiere(id);
      else if (type === "chapitre") await deleteChapter(id);
      else if (type === "notion") await deleteNotion(id);
      showToast("Supprimé");
      loadAll();
    } catch (err: any) { showToast(err.message || "Erreur", "error"); }
  };

  const AddForm = ({ type, parentId, onClose }: { type: string; parentId?: number; onClose: () => void }) => {
    const [val, setVal] = useState("");
    return (
      <div className="flex items-center gap-2 ms-8 py-1">
        <input autoFocus className="px-3 py-1.5 border rounded-lg text-sm flex-1" placeholder={`Nom du ${type}...`}
          value={val} onChange={e => setVal(e.target.value)}
          onKeyDown={e => { if (e.key === "Enter" && val.trim()) { save(type, { nom: val.trim() }, parentId); onClose(); } if (e.key === "Escape") onClose(); }} />
        <Button variant="success" size="sm" onClick={() => { if (val.trim()) { save(type, { nom: val.trim() }, parentId); onClose(); } }}><Check className="w-4 h-4" /></Button>
        <Button variant="ghost" size="sm" onClick={onClose}><X className="w-4 h-4" /></Button>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {toast.show && (
        <div className={`fixed top-4 right-4 z-50 px-4 py-3 rounded-xl shadow-lg text-sm font-medium ${
          toast.type === "success" ? "bg-green-500 text-white" : "bg-red-500 text-white"
        }`}>{toast.message}</div>
      )}

      <div>
        <h1 className="text-3xl font-display font-light text-navy">Arborescence <span className="italic text-orange">Pédagogique</span></h1>
        <p className="text-gray text-sm mt-1">Niveaux d'étude → Matières → Chapitres → Notions</p>
      </div>

      <div className="space-y-3">
        {niveaux.map(niv => (
          <div key={niv.id} className="bg-white rounded-2xl shadow-sm border border-black/5 overflow-hidden">
            <div className="flex items-center gap-3 px-5 py-3 cursor-pointer hover:bg-gray-50"
              onClick={() => toggle("niveaux", niv.id)}>
              <Layers className="w-5 h-5 text-purple-600" />
              {expanded.niveaux?.includes(niv.id) ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
              <span className="font-semibold text-navy flex-1">{niv.nom}</span>
              <Button variant="ghost" size="sm" onClick={e => { e.stopPropagation(); setEditing(`niv-${niv.id}`); setEditValue({ nom: niv.nom, ordre: niv.ordre }); }}><Pencil className="w-4 h-4" /></Button>
              <Button variant="danger" size="sm" onClick={e => { e.stopPropagation(); remove("niveau", niv.id); }}><Trash2 className="w-4 h-4" /></Button>
            </div>

            {editing === `niv-${niv.id}` && (
              <div className="px-5 pb-2 flex items-center gap-2">
                <input autoFocus className="px-3 py-1.5 border rounded-lg text-sm flex-1" value={editValue.nom}
                  onChange={e => setEditValue({ ...editValue, nom: e.target.value })}
                  onKeyDown={e => { if (e.key === "Enter") { save("niveau", editValue, niv.id); } }} />
                <Button variant="success" size="sm" onClick={() => save("niveau", { ...editValue, id: niv.id }, niv.id)}><Check className="w-4 h-4" /></Button>
                <Button variant="ghost" size="sm" onClick={() => setEditing(null)}><X className="w-4 h-4" /></Button>
              </div>
            )}

            {expanded.niveaux?.includes(niv.id) && (
              <div className="pl-8 pb-3">
                {matieres.filter(m => m.niveau_etude_id === niv.id).map(mat => (
                  <div key={mat.id}>
                    <div className="flex items-center gap-2 py-2 cursor-pointer hover:bg-gray-50 px-3 rounded"
                      onClick={() => toggle("matieres", mat.id)}>
                      <BookOpen className="w-4 h-4 text-blue-600" />
                      {expanded.matieres?.includes(mat.id) ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                      <span className="text-sm font-medium text-navy flex-1">{mat.nom}</span>
                      <Button variant="danger" size="sm" onClick={e => { e.stopPropagation(); remove("matiere", mat.id); }}><Trash2 className="w-3 h-3" /></Button>
                    </div>

                    {expanded.matieres?.includes(mat.id) && (
                      <div className="pl-8">
                        {chapters.filter(c => c.matiere_id === mat.id).map(ch => (
                          <div key={ch.id}>
                            <div className="flex items-center gap-2 py-1.5 cursor-pointer hover:bg-gray-50 px-3 rounded"
                              onClick={() => toggle("chapters", ch.id)}>
                              <FileText className="w-4 h-4 text-orange" />
                              {expanded.chapters?.includes(ch.id) ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                              <span className="text-sm text-navy flex-1">{ch.nom}</span>
                              <Button variant="danger" size="sm" onClick={e => { e.stopPropagation(); remove("chapitre", ch.id); }}><Trash2 className="w-3 h-3" /></Button>
                            </div>

                            {expanded.chapters?.includes(ch.id) && (
                              <div className="pl-8">
                                {notions.filter(n => n.chapitre_id === ch.id).map(notion => (
                                  <div key={notion.id} className="flex items-center gap-2 py-1 px-3">
                                    <Lightbulb className="w-3 h-3 text-yellow-500" />
                                    <span className="text-xs text-gray-700 flex-1">{notion.nom}</span>
                                    <Button variant="danger" size="sm" onClick={() => remove("notion", notion.id)}><Trash2 className="w-3 h-3" /></Button>
                                  </div>
                                ))}
                                <AddForm type="notion" parentId={ch.id} onClose={() => {}} />
                              </div>
                            )}
                          </div>
                        ))}
                        <AddForm type="chapitre" parentId={mat.id} onClose={() => {}} />
                      </div>
                    )}
                  </div>
                ))}
                <AddForm type="matiere" parentId={niv.id} onClose={() => {}} />
              </div>
            )}
          </div>
        ))}
        <Button variant="ghost" onClick={() => save("niveau", { nom: "Nouveau niveau" })} className="flex items-center gap-2 text-orange hover:bg-orange/5">
          <Plus className="w-4 h-4" /> Ajouter un niveau d'étude
        </Button>
      </div>
    </div>
  );
}
