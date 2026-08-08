import { useState, useEffect, useCallback } from "react";
import { Plus, Trash2, Users, BookOpen } from "lucide-react";
import { Button, Modal, EmptyState, Spinner } from "../../../components/ui";
import { pathwayMatieres, pathwaySpecialites, pathwayResponsables } from "../../../api";

interface Specialite {
  id: number;
  nom: string;
  cycle_scolaire: string;
  ecole_id: number | null;
  matiere_ids: number[];
}

interface MatiereOption {
  id: number;
  nom: string;
  niveau_etude_nom: string;
}

export default function AdminSpecialitesPedagogiquesPage() {
  const [specialites, setSpecialites] = useState<Specialite[]>([]);
  const [matieres, setMatieres] = useState<MatiereOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newSpec, setNewSpec] = useState({ nom: "", cycle_scolaire: "2eme_cycle", matiere_ids: [] as number[] });
  const [assignModal, setAssignModal] = useState<{ specId: number; specNom: string } | null>(null);
  const [assignData, setAssignData] = useState({ user_id: 0, niveaux_etude_ids: [] as number[] });
  const [toast, setToast] = useState({ show: false, message: "", type: "success" as "success" | "error" });

  const showToast = (message: string, type: "success" | "error" = "success") => {
    setToast({ show: true, message, type });
    setTimeout(() => setToast({ show: false, message: "", type: "success" }), 3000);
  };

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [specData, matData] = await Promise.all([
        pathwaySpecialites.list(),
        pathwayMatieres.list(),
      ]);
      setSpecialites(specData);
      setMatieres(matData.map((m: any) => ({
        id: m.id,
        nom: m.nom,
        niveau_etude_nom: m.niveau_etude_nom || `Niveau ${m.niveau_etude_id}`,
      })));
    } catch { /* ignore */ }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleCreate = async () => {
    if (!newSpec.nom.trim()) return showToast("Nom requis", "error");
    try {
      await pathwaySpecialites.create(newSpec);
      showToast("Spécialité créée");
      setShowCreate(false);
      setNewSpec({ nom: "", cycle_scolaire: "2eme_cycle", matiere_ids: [] });
      load();
    } catch {
      showToast("Erreur réseau", "error");
    }
  };

  const handleAssign = async () => {
    if (!assignData.user_id) return showToast("Enseignant requis", "error");
    try {
      await pathwayResponsables.assign({ specialite_id: assignModal!.specId, ...assignData });
      showToast("Responsable assigné");
      setAssignModal(null);
      setAssignData({ user_id: 0, niveaux_etude_ids: [] });
    } catch {
      showToast("Erreur réseau", "error");
    }
  };

  const toggleMatiere = (matiereId: number) => {
    setNewSpec(prev => ({
      ...prev,
      matiere_ids: prev.matiere_ids.includes(matiereId)
        ? prev.matiere_ids.filter(id => id !== matiereId)
        : [...prev.matiere_ids, matiereId],
    }));
  };

  return (
    <div className="space-y-6">
      {toast.show && (
        <div className={`fixed top-4 right-4 z-50 px-4 py-3 rounded-xl shadow-lg text-sm font-medium ${
          toast.type === "success" ? "bg-green-500 text-white" : "bg-red-500 text-white"
        }`}>{toast.message}</div>
      )}

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-display font-light text-navy">
            Spécialités <span className="italic text-orange">Pédagogiques</span>
          </h1>
          <p className="text-gray text-sm mt-1">Gérer les spécialités et assigner les responsables</p>
        </div>
        <Button
          variant="primary"
          onClick={() => setShowCreate(true)}
        >
          <Plus className="w-4 h-4" /> Nouvelle Spécialité
        </Button>
      </div>

      {loading ? (
        <div className="text-center py-12"><Spinner size="lg" /></div>
      ) : specialites.length === 0 ? (
        <EmptyState icon={<BookOpen className="w-12 h-12" />} title="Aucune spécialité pédagogique créée" description="Créez une spécialité pour grouper les matières par domaine" />
      ) : (
        <div className="grid gap-4">
          {specialites.map(spec => (
            <div key={spec.id} className="bg-white rounded-2xl shadow-sm border border-black/5 p-6">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-navy font-display">{spec.nom}</h3>
                  <div className="flex items-center gap-3 mt-1">
                    <span className="text-xs px-2 py-0.5 bg-cream-m rounded-full text-gray">
                      {spec.cycle_scolaire === "2eme_cycle" ? "2ème cycle (Collège)" :
                       spec.cycle_scolaire === "3eme_cycle" ? "3ème cycle (Lycée)" : spec.cycle_scolaire}
                    </span>
                    <span className="text-xs text-gray">
                      {spec.matiere_ids.length} matière{spec.matiere_ids.length !== 1 ? "s" : ""}
                    </span>
                  </div>
                </div>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setAssignModal({ specId: spec.id, specNom: spec.nom })}
                >
                  <Users className="w-4 h-4" /> Assigner
                </Button>
              </div>

              {spec.matiere_ids.length > 0 && (
                <div className="mt-4 flex flex-wrap gap-2">
                  {spec.matiere_ids.map(mid => {
                    const m = matieres.find(mat => mat.id === mid);
                    return (
                      <span key={mid} className="px-3 py-1 bg-orange/10 text-orange rounded-full text-xs font-medium">
                        {m ? `${m.nom} (${m.niveau_etude_nom})` : `Matière #${mid}`}
                      </span>
                    );
                  })}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="Nouvelle Spécialité">
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium text-gray block mb-1">Nom</label>
            <input
              type="text"
              value={newSpec.nom}
              onChange={e => setNewSpec(prev => ({ ...prev, nom: e.target.value }))}
              placeholder="Ex: Sciences, Lettres, Mathématiques..."
              className="w-full px-4 py-2.5 bg-cream-m rounded-xl border border-black/5 text-sm focus:border-orange focus:outline-none"
            />
          </div>
          <div>
            <label className="text-sm font-medium text-gray block mb-1">Cycle scolaire</label>
            <select
              value={newSpec.cycle_scolaire}
              onChange={e => setNewSpec(prev => ({ ...prev, cycle_scolaire: e.target.value }))}
              className="w-full px-4 py-2.5 bg-cream-m rounded-xl border border-black/5 text-sm focus:border-orange focus:outline-none"
            >
              <option value="2eme_cycle">2ème cycle (Collège - 7ème à 9ème)</option>
              <option value="3eme_cycle">3ème cycle (Lycée - 1ère à 4ème année)</option>
            </select>
          </div>
          <div>
            <label className="text-sm font-medium text-gray block mb-2">Matières associées</label>
            <div className="max-h-48 overflow-y-auto space-y-1 bg-cream-m rounded-xl p-3 border border-black/5">
              {matieres.length === 0 && (
                <p className="text-xs text-gray">Aucune matière disponible</p>
              )}
              {matieres.map(m => (
                <label key={m.id} className="flex items-center gap-2 cursor-pointer py-1">
                  <input
                    type="checkbox"
                    checked={newSpec.matiere_ids.includes(m.id)}
                    onChange={() => toggleMatiere(m.id)}
                    className="rounded border-gray-300 text-orange focus:ring-orange"
                  />
                  <span className="text-sm text-gray">{m.nom}</span>
                  <span className="text-xs text-gray/50">({m.niveau_etude_nom})</span>
                </label>
              ))}
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={() => setShowCreate(false)}>Annuler</Button>
            <Button variant="primary" onClick={handleCreate}>Créer</Button>
          </div>
        </div>
      </Modal>

      <Modal open={!!assignModal} onClose={() => setAssignModal(null)} title={`Assigner un responsable — ${assignModal?.specNom ?? ""}`} maxWidth="max-w-md">
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium text-gray block mb-1">ID de l'enseignant</label>
            <input
              type="number"
              value={assignData.user_id || ""}
              onChange={e => setAssignData(prev => ({ ...prev, user_id: parseInt(e.target.value) || 0 }))}
              placeholder="ID utilisateur"
              className="w-full px-4 py-2.5 bg-cream-m rounded-xl border border-black/5 text-sm focus:border-orange focus:outline-none"
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={() => setAssignModal(null)}>Annuler</Button>
            <Button variant="primary" onClick={handleAssign}>Assigner</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
