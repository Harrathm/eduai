import { useState, useEffect, useCallback } from "react";
import { Settings, Save, RotateCcw } from "lucide-react";
import { tokenStorage } from "../../../utils/tokenStorage";

interface MatiereThreshold {
  matiere_id: number;
  matiere_nom: string;
  remediation_threshold: number;
  standard_threshold: number;
  avance_threshold: number;
}

const DEFAULT_THRESHOLDS = [
  { matiere_id: 0, matiere_nom: "Défaut (toutes matières)", remediation_threshold: 40, standard_threshold: 75, avance_threshold: 75 },
];

export default function AdminSeuilsConfigPage() {
  const [thresholds, setThresholds] = useState<MatiereThreshold[]>(DEFAULT_THRESHOLDS);
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState({ show: false, message: "", type: "success" as "success" | "error" });

  const showToast = (message: string, type: "success" | "error" = "success") => {
    setToast({ show: true, message, type });
    setTimeout(() => setToast({ show: false, message: "", type: "success" }), 3000);
  };

  const load = useCallback(async () => {
    const token = tokenStorage.getToken();
    try {
      const res = await fetch("/api/pathway/matieres", { headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) {
        const matieres = await res.json();
        setThresholds(matieres.map((m: any) => ({
          matiere_id: m.id,
          matiere_nom: m.nom,
          remediation_threshold: m.remediation_threshold ?? 40,
          standard_threshold: m.standard_threshold ?? 75,
          avance_threshold: m.avance_threshold ?? 75,
        })));
      }
    } catch { /* use defaults */ }
  }, []);

  useEffect(() => { load(); }, [load]);

  const updateThreshold = (index: number, field: string, value: number) => {
    setThresholds(prev => prev.map((t, i) => i === index ? { ...t, [field]: value } : t));
  };

  const handleSave = async () => {
    setSaving(true);
    const token = tokenStorage.getToken();
    try {
      for (const t of thresholds) {
        if (t.matiere_id === 0) continue;
        await fetch(`/api/pathway/matieres/${t.matiere_id}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
          body: JSON.stringify({
            remediation_threshold: t.remediation_threshold,
            standard_threshold: t.standard_threshold,
            avance_threshold: t.avance_threshold,
          }),
        });
      }
      showToast("Seuils enregistrés");
    } catch {
      showToast("Erreur d'enregistrement", "error");
    }
    setSaving(false);
  };

  const handleReset = () => {
    setThresholds(prev => prev.map(t => ({
      ...t,
      remediation_threshold: 40,
      standard_threshold: 75,
      avance_threshold: 75,
    })));
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
          <h1 className="text-3xl font-display font-light text-navy">Configuration des <span className="italic text-orange">Seuils</span></h1>
          <p className="text-gray text-sm mt-1">Seuils de bascule entre niveaux d'assimilation par matière</p>
        </div>
        <div className="flex gap-2">
          <button onClick={handleReset} className="px-4 py-2 text-gray hover:text-navy border border-black/10 rounded-xl text-sm flex items-center gap-2">
            <RotateCcw className="w-4 h-4" /> Réinitialiser
          </button>
          <button onClick={handleSave} disabled={saving} className="px-4 py-2 bg-gradient-to-r from-orange to-orange-l text-white rounded-xl text-sm font-medium flex items-center gap-2 disabled:opacity-50">
            <Save className="w-4 h-4" /> {saving ? "Enregistrement..." : "Enregistrer"}
          </button>
        </div>
      </div>

      <div className="bg-white rounded-2xl shadow-sm border border-black/5 overflow-hidden">
        <div className="px-6 py-4 bg-gray-50 border-b border-black/5">
          <div className="grid grid-cols-4 gap-4 text-xs font-semibold text-gray uppercase">
            <div>Matière</div>
            <div>Seuil Remédiation (&lt;)</div>
            <div>Seuil Standard (&lt;)</div>
            <div>Seuil Avancé (≥)</div>
          </div>
        </div>
        <div className="divide-y divide-gray-100">
          {thresholds.map((t, i) => (
            <div key={t.matiere_id} className={`px-6 py-4 grid grid-cols-4 gap-4 items-center ${i === 0 ? "bg-orange/5" : ""}`}>
              <div className="flex items-center gap-2">
                {i === 0 && <Settings className="w-4 h-4 text-orange" />}
                <span className={`text-sm ${i === 0 ? "font-semibold text-navy" : "text-gray"}`}>{t.matiere_nom}</span>
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <input
                    type="number"
                    min={0} max={100}
                    value={t.remediation_threshold}
                    onChange={(e) => updateThreshold(i, "remediation_threshold", Number(e.target.value))}
                    className="w-20 px-3 py-2 bg-cream-m rounded-lg border border-black/5 text-sm text-center focus:border-orange focus:outline-none"
                  />
                  <span className="text-xs text-gray">%</span>
                </div>
                <p className="text-xs text-gray mt-0.5">En dessous → Remédiation</p>
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <input
                    type="number"
                    min={0} max={100}
                    value={t.standard_threshold}
                    onChange={(e) => updateThreshold(i, "standard_threshold", Number(e.target.value))}
                    className="w-20 px-3 py-2 bg-cream-m rounded-lg border border-black/5 text-sm text-center focus:border-orange focus:outline-none"
                  />
                  <span className="text-xs text-gray">%</span>
                </div>
                <p className="text-xs text-gray mt-0.5">En dessous → Standard</p>
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <input
                    type="number"
                    min={0} max={100}
                    value={t.avance_threshold}
                    onChange={(e) => updateThreshold(i, "avance_threshold", Number(e.target.value))}
                    className="w-20 px-3 py-2 bg-cream-m rounded-lg border border-black/5 text-sm text-center focus:border-orange focus:outline-none"
                  />
                  <span className="text-xs text-gray">%</span>
                </div>
                <p className="text-xs text-gray mt-0.5">Au dessus → Avancé</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 text-sm text-blue-800">
        <p className="font-semibold mb-1">Comment ça marche ?</p>
        <ul className="list-disc list-inside space-y-0.5 text-blue-700">
          <li><b>Remédiation</b> : score moyen du chapitre &lt; seuil remédiation</li>
          <li><b>Standard</b> : seuil remédiation ≤ score moyen &lt; seuil standard</li>
          <li><b>Avancé</b> : score moyen ≥ seuil standard</li>
          <li>Le recalcul se fait automatiquement après chaque quiz</li>
        </ul>
      </div>
    </div>
  );
}
