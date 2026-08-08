import { useState, useRef } from "react";
import { Button } from "@/components/ui";
import { useAuthStore } from "../../../store/authStore";

const API_URL = "";

interface ImportResult {
  created: number;
  errors: number;
  items_created: { email: string; full_name: string; id: number }[];
  items_errors: { line: number; error: string }[];
}

export default function CsvImportStudents() {
  const { token } = useAuthStore();
  const fileRef = useRef<HTMLInputElement>(null);
  const [csvText, setCsvText] = useState("");
  const [result, setResult] = useState<ImportResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      setCsvText(ev.target?.result as string);
    };
    reader.readAsText(file);
  };

  const handleImport = async () => {
    if (!csvText.trim()) {
      setError("Veuillez sélectionner un fichier CSV ou coller le contenu.");
      return;
    }
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const res = await fetch(`${API_URL}/api/admin/import-students`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ csv_content: csvText }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Import failed");
      }
      setResult(await res.json());
    } catch (err) {
      setError(err.message);
    }
    setLoading(false);
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-navy mb-1">Import CSV d'élèves</h3>
        <p className="text-sm text-gray">
          Format attendu : <code className="bg-cream-m px-1 rounded">email, full_name, password, niveau_scolaire</code> (optionnel).
          La première ligne peut être un en-tête.
        </p>
      </div>

      <div className="flex gap-4">
        <input
          ref={fileRef}
          type="file"
          accept=".csv,.txt"
          onChange={handleFileChange}
          className="hidden"
        />
        <Button variant="ghost" onClick={() => fileRef.current?.click()}>
          Sélectionner un fichier CSV
        </Button>
        {csvText && (
          <span className="text-sm text-gray self-center">
            Fichier chargé ({csvText.split("\n").length} lignes)
          </span>
        )}
      </div>

      <div>
        <label className="block text-xs font-semibold text-gray tracking-wide uppercase mb-2">
          Ou coller le contenu CSV
        </label>
        <textarea
          value={csvText}
          onChange={(e) => setCsvText(e.target.value)}
          rows={8}
          className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 focus:border-orange focus:outline-none transition-colors font-mono text-sm"
          placeholder="email,full_name,password,niveau_scolaire
eleve1@ecole.tn,Ahmed Ben Ali,password123,7ème de base
eleve2@ecole.tn,Sara Trabelsi,password123,1ère année secondaire"
        />
      </div>

      {error && (
        <div className="bg-orange-p border border-orange/30 text-orange text-sm px-5 py-3 rounded-xl">
          {error}
        </div>
      )}

      <Button variant="primary" onClick={handleImport} disabled={!csvText.trim()} loading={loading}>
        {loading ? "Import en cours..." : "Importer les élèves"}
      </Button>

      {result && (
        <div className="bg-white rounded-2xl border border-black/5 p-6 space-y-4">
          <h4 className="font-semibold text-navy">Résultat de l'import</h4>
          <div className="flex gap-6">
            <div className="text-center">
              <div className="text-3xl font-[300] text-green-600">{result.created}</div>
              <div className="text-xs text-gray uppercase tracking-wide">Créés</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-[300] text-orange">{result.errors}</div>
              <div className="text-xs text-gray uppercase tracking-wide">Erreurs</div>
            </div>
          </div>

          {result.items_created.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-gray uppercase mb-2">Élèves créés</p>
              <div className="max-h-40 overflow-y-auto space-y-1">
                {result.items_created.map((item) => (
                  <div key={item.id} className="flex items-center gap-2 text-sm">
                    <svg className="w-4 h-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    <span className="text-navy">{item.full_name}</span>
                    <span className="text-gray">({item.email})</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {result.items_errors.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-gray uppercase mb-2">Erreurs</p>
              <div className="max-h-40 overflow-y-auto space-y-1">
                {result.items_errors.map((item, idx) => (
                  <div key={idx} className="flex items-center gap-2 text-sm">
                    <svg className="w-4 h-4 text-orange" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                    <span className="text-gray">Ligne {item.line}:</span>
                    <span className="text-orange">{item.error}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
