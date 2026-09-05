import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { ChevronDown, ChevronRight, Target, Sparkles } from "lucide-react";
import { pathwayApi } from "../../../api";
import { Button, Spinner, EmptyState } from "../../../components/ui";
import { useTranslation } from "react-i18next";

interface NotionCoverage {
  id: number;
  nom: string;
  is_covered: boolean;
  contenus_count: number;
  published_count: number;
}

interface ChapitreCoverage {
  id: number;
  nom: string;
  ordre: number;
  notions: NotionCoverage[];
  total_notions: number;
  covered_notions: number;
}

interface MatiereCoverage {
  niveau: string;
  matiere: string;
  matiere_id: number;
  chapitres: ChapitreCoverage[];
  total_notions: number;
  covered_notions: number;
  coverage_pct: number;
}

export default function CurriculumCoveragePage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [niveaux, setNiveaux] = useState<any[]>([]);
  const [matieres, setMatieres] = useState<any[]>([]);
  const [selectedNiveau, setSelectedNiveau] = useState("");
  const [selectedMatiere, setSelectedMatiere] = useState("");
  const [data, setData] = useState<MatiereCoverage[]>([]);
  const [loading, setLoading] = useState(false);
  const [expandedChapitres, setExpandedChapitres] = useState<Set<number>>(new Set());

  useEffect(() => {
    pathwayApi.getNiveaux().then((res) => setNiveaux(res)).catch(() => {});
  }, []);

  useEffect(() => {
    if (!selectedNiveau) { setMatieres([]); setSelectedMatiere(""); return; }
    pathwayApi.getMatieresByNiveau(selectedNiveau).then((res) => setMatieres(res)).catch(() => {});
    setSelectedMatiere("");
  }, [selectedNiveau]);

  const fetchData = useCallback(async () => {
    if (!selectedNiveau) return;
    setLoading(true);
    try {
      const res = await pathwayApi.getCurriculumCoverage({
        niveau_scolaire: selectedNiveau,
        matiere: selectedMatiere || undefined,
      });
      setData(res.matieres || []);
    } catch { setData([]); }
    setLoading(false);
  }, [selectedNiveau, selectedMatiere]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const toggleChapitre = (id: number) => {
    setExpandedChapitres((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const totalNotions = data.reduce((s, m) => s + m.total_notions, 0);
  const totalCovered = data.reduce((s, m) => s + m.covered_notions, 0);
  const globalPct = totalNotions ? Math.round(totalCovered / totalNotions * 100) : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-display font-light text-navy">
            Couverture <span className="italic text-orange">Programme</span>
          </h1>
          <p className="text-gray text-sm mt-1">
            {t("admin.curriculumCoverage.subtitle", "Visualisez l'avancement de la création de contenu par rapport au programme officiel")}
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-2xl p-5 shadow-sm border border-black/5">
        <div className="flex flex-wrap gap-4 items-end">
          <div className="flex-1 min-w-[200px]">
            <label className="block text-xs font-medium text-gray mb-1.5">{t("admin.curriculumCoverage.level", "Niveau scolaire")}</label>
            <select value={selectedNiveau} onChange={(e) => setSelectedNiveau(e.target.value)}
              className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none focus:ring-2 focus:ring-orange/20">
              <option value="">— {t("admin.curriculumCoverage.selectLevel", "Sélectionner un niveau")} —</option>
              {niveaux.map((n) => <option key={n.id} value={n.nom}>{n.nom}</option>)}
            </select>
          </div>
          <div className="flex-1 min-w-[200px]">
            <label className="block text-xs font-medium text-gray mb-1.5">{t("admin.curriculumCoverage.subject", "Matière")}</label>
            <select value={selectedMatiere} onChange={(e) => setSelectedMatiere(e.target.value)}
              className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none focus:ring-2 focus:ring-orange/20"
              disabled={!selectedNiveau}>
              <option value="">— {t("admin.curriculumCoverage.allSubjects", "Toutes les matières")} —</option>
              {matieres.map((m) => <option key={m.id} value={m.nom}>{m.nom}</option>)}
            </select>
          </div>
        </div>
      </div>

      {/* Global stats */}
      {data.length > 0 && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white rounded-2xl p-5 shadow-sm border border-black/5">
            <span className="text-xs text-gray font-medium uppercase tracking-wider">{t("admin.curriculumCoverage.totalSubjects", "Matières")}</span>
            <div className="text-2xl font-bold text-navy mt-1">{data.length}</div>
          </div>
          <div className="bg-white rounded-2xl p-5 shadow-sm border border-black/5">
            <span className="text-xs text-gray font-medium uppercase tracking-wider">{t("admin.curriculumCoverage.totalChapters", "Chapitres")}</span>
            <div className="text-2xl font-bold text-navy mt-1">{data.reduce((s, m) => s + m.chapitres.length, 0)}</div>
          </div>
          <div className="bg-white rounded-2xl p-5 shadow-sm border border-black/5">
            <span className="text-xs text-gray font-medium uppercase tracking-wider">{t("admin.curriculumCoverage.totalNotions", "Notions")}</span>
            <div className="text-2xl font-bold text-navy mt-1">{totalNotions}</div>
          </div>
          <div className="bg-white rounded-2xl p-5 shadow-sm border border-black/5">
            <span className="text-xs text-gray font-medium uppercase tracking-wider">{t("admin.curriculumCoverage.globalCoverage", "Couverture globale")}</span>
            <div className={`text-2xl font-bold mt-1 ${globalPct >= 70 ? "text-green-600" : globalPct >= 40 ? "text-orange" : "text-red-500"}`}>
              {globalPct}%
            </div>
          </div>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex justify-center py-12"><Spinner size="lg" /></div>
      )}

      {/* Empty */}
      {!loading && data.length === 0 && selectedNiveau && (
        <EmptyState icon={<Target className="w-12 h-12" />} title={t("admin.curriculumCoverage.noData", "Aucune donnée de couverture")} />
      )}

      {!loading && !selectedNiveau && (
        <EmptyState icon={<Target className="w-12 h-12" />} title={t("admin.curriculumCoverage.selectPrompt", "Sélectionnez un niveau pour visualiser la couverture du programme")} />
      )}

      {/* Coverage tree */}
      {!loading && data.map((m) => (
        <div key={m.matiere_id} className="bg-white rounded-2xl shadow-sm border border-black/5 overflow-hidden">
          {/* Matiere header */}
          <div className="px-5 py-4 border-b border-black/5 flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-navy">{m.matiere}</h3>
              <span className="text-xs text-gray">{m.niveau}</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-sm text-gray">
                {m.covered_notions}/{m.total_notions} {t("admin.curriculumCoverage.notionsCovered", "notions")}
              </span>
              <div className="w-24 h-2 bg-gray-100 rounded-full overflow-hidden">
                <div className={`h-full rounded-full ${m.coverage_pct >= 70 ? "bg-green-500" : m.coverage_pct >= 40 ? "bg-orange" : "bg-red-500"}`}
                  style={{ width: `${m.coverage_pct}%` }} />
              </div>
              <span className={`text-sm font-semibold ${m.coverage_pct >= 70 ? "text-green-600" : m.coverage_pct >= 40 ? "text-orange" : "text-red-500"}`}>
                {m.coverage_pct}%
              </span>
            </div>
          </div>

          {/* Chapitres */}
          {m.chapitres.length === 0 ? (
            <div className="px-5 py-4 text-sm text-gray italic">
              {t("admin.curriculumCoverage.noChapters", "Aucun chapitre défini pour cette matière")}
            </div>
          ) : (
            m.chapitres.map((ch) => {
              const isExpanded = expandedChapitres.has(ch.id);
              return (
                <div key={ch.id} className="border-b border-black/5 last:border-b-0">
                  <button onClick={() => toggleChapitre(ch.id)}
                    className="w-full px-5 py-3 flex items-center justify-between hover:bg-cream/30 transition-colors">
                    <div className="flex items-center gap-3">
                      {isExpanded ? <ChevronDown className="w-4 h-4 text-gray" /> : <ChevronRight className="w-4 h-4 text-gray" />}
                      <span className="font-medium text-navy text-sm">{ch.nom}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-gray">
                        {ch.covered_notions}/{ch.total_notions}
                      </span>
                      <div className={`w-2 h-2 rounded-full ${ch.covered_notions === ch.total_notions && ch.total_notions > 0 ? "bg-green-500" : ch.covered_notions > 0 ? "bg-orange" : "bg-red-400"}`} />
                    </div>
                  </button>
                  {isExpanded && (
                    <div className="px-5 pb-3">
                      <div className="ml-7 space-y-1">
                        {ch.notions.map((no) => (
                          <div key={no.id} className="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-cream/30">
                            <span className="text-sm text-navy">{no.nom}</span>
                            <div className="flex items-center gap-2">
                              {no.is_covered ? (
                                <span className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded-full bg-green-50 text-green-700">
                                  <span className="w-1.5 h-1.5 rounded-full bg-green-500" />
                                  {t("admin.curriculumCoverage.done", "Réalisé")} ({no.published_count})
                                </span>
                              ) : (
                                <span className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded-full bg-red-50 text-red-600">
                                  <span className="w-1.5 h-1.5 rounded-full bg-red-400" />
                                  {t("admin.curriculumCoverage.todo", "Non réalisé")}
                                </span>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      ))}

      {/* Generate missing content button */}
      {!loading && data.length > 0 && totalCovered < totalNotions && (
        <div className="flex justify-center">
          <Button variant="primary" onClick={() => navigate("/dashboard/admin/ai-factory")}>
            <Sparkles className="w-4 h-4 mr-2" />
            {t("admin.curriculumCoverage.generateMissing", "Générer le contenu manquant")}
          </Button>
        </div>
      )}
    </div>
  );
}
