import { useState, useEffect, useCallback } from "react";
import { CheckCircle, AlertCircle, BookOpen, FileText, Eye } from "lucide-react";
import {
  getNiveauxEtude, getMatieres, getChapters, getNotions, getContenus, getStatutPublication,
} from "../../pathway/api";
import type { NiveauEtude, Matiere, ChapterPathway, Notion, ContenuNotion, StatutPublication } from "../../pathway/api";

type NotionWithStatus = Notion & {
  statut?: StatutPublication;
  chapitre_nom?: string;
  matiere_nom?: string;
};

export default function AdminPublicationStatusPage() {
  const [notions, setNotions] = useState<NotionWithStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"all" | "publiable" | "brouillon">("all");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [allNotions, allChapters, allMatieres] = await Promise.all([getNotions(), getChapters(), getMatieres()]);
      const matMap = Object.fromEntries(allMatieres.map(m => [m.id, m.nom]));
      const chapMap = Object.fromEntries(allChapters.map(c => [c.id, c.nom]));

      const enriched = await Promise.all(
        allNotions.map(async (n) => {
          const statut = await getStatutPublication(n.id);
          return {
            ...n,
            statut,
            chapitre_nom: chapMap[n.chapitre_id] || "?",
            matiere_nom: matMap[allChapters.find(c => c.id === n.chapitre_id)?.matiere_id || 0] || "?",
          };
        })
      );
      setNotions(enriched);
    } catch { /* ignore */ }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const filtered = notions.filter(n => filter === "all" || n.statut?.statut === filter);
  const publiableCount = notions.filter(n => n.statut?.statut === "publiable").length;
  const brouillonCount = notions.length - publiableCount;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-display font-light text-navy">Statut de <span className="italic text-orange">Publication</span></h1>
        <p className="text-gray text-sm mt-1">Vue d'ensemble de la complétude des notions (Standard + 1 autre niveau minimum)</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white rounded-2xl p-5 shadow-sm border border-black/5">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-blue-100 rounded-xl"><BookOpen className="w-5 h-5 text-blue-600" /></div>
            <div><p className="text-2xl font-bold text-navy">{notions.length}</p><p className="text-xs text-gray">Total Notions</p></div>
          </div>
        </div>
        <div className="bg-white rounded-2xl p-5 shadow-sm border border-black/5">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-green-100 rounded-xl"><CheckCircle className="w-5 h-5 text-green-600" /></div>
            <div><p className="text-2xl font-bold text-green-600">{publiableCount}</p><p className="text-xs text-gray">Publiables</p></div>
          </div>
        </div>
        <div className="bg-white rounded-2xl p-5 shadow-sm border border-black/5">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-amber-100 rounded-xl"><AlertCircle className="w-5 h-5 text-amber-600" /></div>
            <div><p className="text-2xl font-bold text-amber-600">{brouillonCount}</p><p className="text-xs text-gray">Brouillons</p></div>
          </div>
        </div>
      </div>

      <div className="flex gap-2">
        {(["all", "publiable", "brouillon"] as const).map(f => (
          <button key={f} onClick={() => setFilter(f)}
            className={`px-4 py-2 rounded-xl text-sm font-medium transition-colors ${
              filter === f ? "bg-orange text-white" : "bg-white text-gray border hover:bg-gray-50"
            }`}>
            {f === "all" ? "Toutes" : f === "publiable" ? "Publiables" : "Brouillons"}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="text-center py-12 text-gray">Chargement...</div>
      ) : (
        <div className="bg-white rounded-2xl shadow-sm border border-black/5 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-5 py-3 text-left text-xs font-medium text-gray uppercase">Notion</th>
                <th className="px-5 py-3 text-left text-xs font-medium text-gray uppercase">Chapitre</th>
                <th className="px-5 py-3 text-left text-xs font-medium text-gray uppercase">Matière</th>
                <th className="px-5 py-3 text-left text-xs font-medium text-gray uppercase">Statut</th>
                <th className="px-5 py-3 text-left text-xs font-medium text-gray uppercase">Niveaux manquants</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {filtered.map(n => (
                <tr key={n.id} className="hover:bg-gray-50">
                  <td className="px-5 py-3 text-sm font-medium text-navy">{n.nom}</td>
                  <td className="px-5 py-3 text-sm text-gray">{n.chapitre_nom}</td>
                  <td className="px-5 py-3 text-sm text-gray">{n.matiere_nom}</td>
                  <td className="px-5 py-3">
                    {n.statut?.statut === "publiable" ? (
                      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700">
                        <CheckCircle className="w-3 h-3" /> Publiable
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-amber-100 text-amber-700">
                        <AlertCircle className="w-3 h-3" /> Brouillon
                      </span>
                    )}
                  </td>
                  <td className="px-5 py-3 text-xs text-gray">
                    {n.statut?.niveaux_manquants?.join(", ") || "—"}</td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr><td colSpan={5} className="px-5 py-12 text-center text-gray">Aucune notion trouvée</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
