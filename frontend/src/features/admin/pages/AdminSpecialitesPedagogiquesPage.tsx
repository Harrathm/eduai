import { useState, useEffect, useCallback, useMemo } from "react";
import { Plus, Trash2, Users, BookOpen, Pencil } from "lucide-react";
import { Button, Modal, ConfirmModal, EmptyState, Spinner } from "../../../components/ui";
import { pathwaySpecialites, pathwayResponsables, pathwayApi, adminUsersAll } from "../../../api";
import { CYCLE_NIVEAUX } from "../constants/cycles";

interface Responsable {
  user_id: number;
  full_name: string;
  email: string;
}

interface Specialite {
  id: number;
  nom: string;
  cycle_scolaire: string;
  ecole_id: number | null;
  matiere_ids: number[];
  responsables: Responsable[];
}

interface MatiereOption {
  id: number;
  nom: string;
  niveau_etude_nom: string;
}

export default function AdminSpecialitesPedagogiquesPage() {
  const [specialites, setSpecialites] = useState<Specialite[]>([]);
  const [niveauxFromDB, setNiveauxFromDB] = useState<{ id: number; nom: string }[]>([]);
  const [selectedCycle, setSelectedCycle] = useState<string>("");
  const [selectedNiveau, setSelectedNiveau] = useState<string>("");
  const [filteredMatieres, setFilteredMatieres] = useState<MatiereOption[]>([]);
  const [loadingMatieres, setLoadingMatieres] = useState(false);
  const [eligibleUsers, setEligibleUsers] = useState<{ id: number; full_name: string; email: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newSpec, setNewSpec] = useState({ nom: "", cycle_scolaire: "preparatoire", matiere_ids: [] as number[] });
  const [editSpec, setEditSpec] = useState<Specialite | null>(null);
  const [editCycle, setEditCycle] = useState("");
  const [editNiveau, setEditNiveau] = useState("");
  const [editFilteredMatieres, setEditFilteredMatieres] = useState<MatiereOption[]>([]);
  const [deleteSpec, setDeleteSpec] = useState<Specialite | null>(null);
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
      const [specData, niveauData, teachersRes, leadsRes] = await Promise.all([
        pathwaySpecialites.list(),
        pathwayApi.getNiveaux(),
        adminUsersAll.list({ role: "teacher", limit: 200 }),
        adminUsersAll.list({ role: "pedagogical_lead", limit: 200 }),
      ]);
      setSpecialites(specData);
      setNiveauxFromDB(niveauData.map((n: any) => ({ id: n.id, nom: n.nom })));
      const teachers = (teachersRes?.items || []).map((u: any) => ({ id: u.id, full_name: u.full_name, email: u.email }));
      const leads = (leadsRes?.items || []).map((u: any) => ({ id: u.id, full_name: u.full_name, email: u.email }));
      const merged = [...teachers, ...leads].filter((u, i, arr) => arr.findIndex(x => x.id === u.id) === i);
      setEligibleUsers(merged);
    } catch { /* ignore */ }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const availableNiveaux = useMemo(() => {
    if (!selectedCycle) return [];
    const allowed = CYCLE_NIVEAUX[selectedCycle] || [];
    return niveauxFromDB.filter(n => allowed.includes(n.nom));
  }, [selectedCycle, niveauxFromDB]);

  useEffect(() => {
    if (!selectedNiveau) {
      setFilteredMatieres([]);
      return;
    }
    setLoadingMatieres(true);
    pathwayApi.getMatieresByNiveau(selectedNiveau)
      .then((data: any) => {
        const raw: any[] = Array.isArray(data) ? data : [
          ...(Array.isArray(data?.langues) ? data.langues : []),
          ...(Array.isArray(data?.specialites) ? data.specialites : []),
        ];
        const unique = raw
          .filter((m: any, i: number, arr: any[]) => arr.findIndex((x: any) => x.id === m.id) === i)
          .map((m: any) => ({
            id: m.id,
            nom: m.nom,
            niveau_etude_nom: m.niveau_etude_nom || selectedNiveau,
          }));
        setFilteredMatieres(unique);
      })
      .catch(() => setFilteredMatieres([]))
      .finally(() => setLoadingMatieres(false));
  }, [selectedNiveau]);

  useEffect(() => {
    if (!editNiveau) {
      setEditFilteredMatieres([]);
      return;
    }
    pathwayApi.getMatieresByNiveau(editNiveau)
      .then((data: any) => {
        const raw: any[] = Array.isArray(data) ? data : [
          ...(Array.isArray(data?.langues) ? data.langues : []),
          ...(Array.isArray(data?.specialites) ? data.specialites : []),
        ];
        const unique = raw
          .filter((m: any, i: number, arr: any[]) => arr.findIndex((x: any) => x.id === m.id) === i)
          .map((m: any) => ({ id: m.id, nom: m.nom, niveau_etude_nom: m.niveau_etude_nom || editNiveau }));
        setEditFilteredMatieres(unique);
      })
      .catch(() => setEditFilteredMatieres([]));
  }, [editNiveau]);

  const handleCreate = async () => {
    if (!newSpec.nom.trim()) return showToast("Nom requis", "error");
    try {
      await pathwaySpecialites.create(newSpec);
      showToast("Spécialité créée");
      setShowCreate(false);
      setNewSpec({ nom: "", cycle_scolaire: "preparatoire", matiere_ids: [] });
      setSelectedCycle("");
      setSelectedNiveau("");
      setFilteredMatieres([]);
      load();
    } catch {
      showToast("Erreur réseau", "error");
    }
  };

  const openEdit = (spec: Specialite) => {
    setEditSpec({ ...spec, matiere_ids: [...spec.matiere_ids] });
    setEditCycle(spec.cycle_scolaire);
    setEditNiveau("");
  };

  const handleUpdate = async () => {
    if (!editSpec || !editSpec.nom.trim()) return showToast("Nom requis", "error");
    try {
      await pathwaySpecialites.update(editSpec.id, {
        nom: editSpec.nom,
        cycle_scolaire: editCycle,
        matiere_ids: editSpec.matiere_ids,
      });
      showToast("Spécialité mise à jour");
      setEditSpec(null);
      setEditCycle("");
      setEditNiveau("");
      setEditFilteredMatieres([]);
      load();
    } catch {
      showToast("Erreur réseau", "error");
    }
  };

  const handleDelete = async () => {
    if (!deleteSpec) return;
    try {
      await pathwaySpecialites.delete(deleteSpec.id);
      showToast("Spécialité supprimée");
      setDeleteSpec(null);
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

  const toggleEditMatiere = (matiereId: number) => {
    if (!editSpec) return;
    setEditSpec(prev => prev ? {
      ...prev,
      matiere_ids: prev.matiere_ids.includes(matiereId)
        ? prev.matiere_ids.filter(id => id !== matiereId)
        : [...prev.matiere_ids, matiereId],
    } : prev);
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
                      {spec.cycle_scolaire === "primaire" ? "Primaire" :
                       spec.cycle_scolaire === "preparatoire" ? "Préparatoire (Collège)" :
                       spec.cycle_scolaire === "secondaire" ? "Secondaire (Lycée)" : spec.cycle_scolaire}
                    </span>
                    <span className="text-xs text-gray">
                      {spec.matiere_ids.length} matière{spec.matiere_ids.length !== 1 ? "s" : ""}
                    </span>
                  </div>
                  {spec.responsables && spec.responsables.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {spec.responsables.map(r => (
                        <span key={r.user_id} className="px-2 py-0.5 bg-navy/10 text-navy rounded-full text-xs">
                          {r.full_name}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <Button variant="ghost" size="sm" onClick={() => openEdit(spec)}>
                    <Pencil className="w-4 h-4" />
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => setDeleteSpec(spec)}>
                    <Trash2 className="w-4 h-4 text-red-500" />
                  </Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => setAssignModal({ specId: spec.id, specNom: spec.nom })}
                  >
                    <Users className="w-4 h-4" /> Assigner
                  </Button>
                </div>
              </div>

              {spec.matiere_ids.length > 0 && (
                <div className="mt-4 flex flex-wrap gap-2">
                  {spec.matiere_ids.map(mid => {
                    const m = filteredMatieres.find(mat => mat.id === mid) || niveauxFromDB.find(n => n.id === mid);
                    return (
                      <span key={mid} className="px-3 py-1 bg-orange/10 text-orange rounded-full text-xs font-medium">
                        {m ? m.nom : `Matière #${mid}`}
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
              value={selectedCycle}
              onChange={e => {
                setSelectedCycle(e.target.value);
                setSelectedNiveau("");
                setNewSpec(prev => ({ ...prev, cycle_scolaire: e.target.value, matiere_ids: [] }));
              }}
              className="w-full px-4 py-2.5 bg-cream-m rounded-xl border border-black/5 text-sm focus:border-orange focus:outline-none"
            >
              <option value="">— Sélectionnez un cycle —</option>
              <option value="primaire">Primaire (1ère à 6ème Année Base)</option>
              <option value="preparatoire">Préparatoire (7ème à 9ème Année Base)</option>
              <option value="secondaire">Secondaire (1ère à Bac)</option>
            </select>
          </div>
          <div>
            <label className="text-sm font-medium text-gray block mb-1">Niveau scolaire</label>
            <select
              value={selectedNiveau}
              onChange={e => {
                setSelectedNiveau(e.target.value);
                setNewSpec(prev => ({ ...prev, matiere_ids: [] }));
              }}
              disabled={!selectedCycle}
              className="w-full px-4 py-2.5 bg-cream-m rounded-xl border border-black/5 text-sm focus:border-orange focus:outline-none disabled:opacity-50"
            >
              <option value="">{!selectedCycle ? "Choisissez d'abord un cycle" : "— Sélectionnez un niveau —"}</option>
              {availableNiveaux.map(n => (
                <option key={n.id} value={n.nom}>{n.nom}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-sm font-medium text-gray block mb-2">Matières associées</label>
            <div className={`max-h-48 overflow-y-auto space-y-1 bg-cream-m rounded-xl p-3 border border-black/5 ${!selectedNiveau ? "opacity-50" : ""}`}>
              {!selectedNiveau ? (
                <p className="text-xs text-gray">Sélectionnez d'abord un niveau scolaire</p>
              ) : loadingMatieres ? (
                <div className="flex items-center gap-2 py-2">
                  <Spinner size="sm" /> <span className="text-xs text-gray">Chargement des matières...</span>
                </div>
              ) : filteredMatieres.length === 0 ? (
                <p className="text-xs text-gray">Aucune matière disponible pour ce niveau</p>
              ) : (
                filteredMatieres.map(m => (
                  <label key={m.id} className="flex items-center gap-2 cursor-pointer py-1">
                    <input
                      type="checkbox"
                      checked={newSpec.matiere_ids.includes(m.id)}
                      onChange={() => toggleMatiere(m.id)}
                      className="rounded border-gray-300 text-orange focus:ring-orange"
                    />
                    <span className="text-sm text-gray">{m.nom}</span>
                  </label>
                ))
              )}
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
            <label className="text-sm font-medium text-gray block mb-1">Responsable pédagogique</label>
            <select
              value={assignData.user_id || ""}
              onChange={e => setAssignData(prev => ({ ...prev, user_id: parseInt(e.target.value) || 0 }))}
              className="w-full px-4 py-2.5 bg-cream-m rounded-xl border border-black/5 text-sm focus:border-orange focus:outline-none"
            >
              <option value="">— Sélectionnez un responsable —</option>
              {eligibleUsers.map(u => (
                <option key={u.id} value={u.id}>{u.full_name} ({u.email})</option>
              ))}
            </select>
            {eligibleUsers.length === 0 && (
              <p className="text-xs text-gray mt-1">Aucun enseignant ou responsable pédagogique disponible</p>
            )}
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={() => setAssignModal(null)}>Annuler</Button>
            <Button variant="primary" onClick={handleAssign}>Assigner</Button>
          </div>
        </div>
      </Modal>

      <Modal open={!!editSpec} onClose={() => { setEditSpec(null); setEditCycle(""); setEditNiveau(""); setEditFilteredMatieres([]); }} title="Éditer la Spécialité">
        {editSpec && (
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-gray block mb-1">Nom</label>
              <input
                type="text"
                value={editSpec.nom}
                onChange={e => setEditSpec(prev => prev ? { ...prev, nom: e.target.value } : prev)}
                className="w-full px-4 py-2.5 bg-cream-m rounded-xl border border-black/5 text-sm focus:border-orange focus:outline-none"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray block mb-1">Cycle scolaire</label>
              <select
                value={editCycle}
                onChange={e => {
                  setEditCycle(e.target.value);
                  setEditNiveau("");
                  setEditSpec(prev => prev ? { ...prev, matiere_ids: [] } : prev);
                }}
                className="w-full px-4 py-2.5 bg-cream-m rounded-xl border border-black/5 text-sm focus:border-orange focus:outline-none"
              >
                <option value="">— Sélectionnez un cycle —</option>
                <option value="primaire">Primaire (1ère à 6ème Année Base)</option>
                <option value="preparatoire">Préparatoire (7ème à 9ème Année Base)</option>
                <option value="secondaire">Secondaire (1ère à Bac)</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-medium text-gray block mb-1">Niveau scolaire</label>
              <select
                value={editNiveau}
                onChange={e => {
                  setEditNiveau(e.target.value);
                  setEditSpec(prev => prev ? { ...prev, matiere_ids: [] } : prev);
                }}
                disabled={!editCycle}
                className="w-full px-4 py-2.5 bg-cream-m rounded-xl border border-black/5 text-sm focus:border-orange focus:outline-none disabled:opacity-50"
              >
                <option value="">{!editCycle ? "Choisissez d'abord un cycle" : "— Sélectionnez un niveau —"}</option>
                {(CYCLE_NIVEAUX[editCycle] || []).map(n => (
                  <option key={n} value={n}>{n}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-sm font-medium text-gray block mb-2">Matières associées</label>
              <div className={`max-h-48 overflow-y-auto space-y-1 bg-cream-m rounded-xl p-3 border border-black/5 ${!editNiveau ? "opacity-50" : ""}`}>
                {!editNiveau ? (
                  <p className="text-xs text-gray">Sélectionnez d'abord un niveau scolaire</p>
                ) : editFilteredMatieres.length === 0 ? (
                  <p className="text-xs text-gray">Aucune matière disponible pour ce niveau</p>
                ) : (
                  editFilteredMatieres.map(m => (
                    <label key={m.id} className="flex items-center gap-2 cursor-pointer py-1">
                      <input
                        type="checkbox"
                        checked={editSpec.matiere_ids.includes(m.id)}
                        onChange={() => toggleEditMatiere(m.id)}
                        className="rounded border-gray-300 text-orange focus:ring-orange"
                      />
                      <span className="text-sm text-gray">{m.nom}</span>
                    </label>
                  ))
                )}
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="ghost" onClick={() => { setEditSpec(null); setEditCycle(""); setEditNiveau(""); setEditFilteredMatieres([]); }}>Annuler</Button>
              <Button variant="primary" onClick={handleUpdate}>Sauvegarder</Button>
            </div>
          </div>
        )}
      </Modal>

      <ConfirmModal
        open={!!deleteSpec}
        onClose={() => setDeleteSpec(null)}
        onConfirm={handleDelete}
        title="Supprimer la spécialité"
        message={`Êtes-vous sûr de vouloir supprimer « ${deleteSpec?.nom ?? ""} » ? Cette action est irréversible.`}
        confirmLabel="Supprimer"
      />
    </div>
  );
}
