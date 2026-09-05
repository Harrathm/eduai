import { useState, useEffect, useCallback } from "react";
import { useTranslation } from 'react-i18next';
import { Search, Library, BookOpen, Award } from "lucide-react";
import { useAuthStore } from "../../../store/authStore";
import { searchElements, listCompetences, type ElementPedagogique, type Competence } from "../../../api";
import { Button, EmptyState } from "../../../components/ui";

const STATUT_COLORS: Record<string, string> = {
  brouillon: "bg-gray-100 text-gray-600",
  en_review: "bg-yellow-100 text-yellow-700",
  publie: "bg-green-100 text-green-700",
  rejete: "bg-red-100 text-red-600",
};

const TYPE_COLORS: Record<string, string> = {
  texte: "bg-blue-50 text-blue-600",
  video: "bg-purple-50 text-purple-600",
  image: "bg-pink-50 text-pink-600",
  quiz: "bg-orange-50 text-orange-600",
  pdf: "bg-red-50 text-red-600",
};

export default function TeacherBibliothequePage() {
  const { t } = useTranslation();
  const { token } = useAuthStore();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<ElementPedagogique[]>([]);
  const [competences, setCompetences] = useState<Competence[]>([]);
  const [loading, setLoading] = useState(false);
  const [tab, setTab] = useState<"search" | "competences">("search");
  const [toast, setToast] = useState({ show: false, message: "", type: "success" as "success" | "error" });

  const showToast = (message: string, type: "success" | "error" = "success") => {
    setToast({ show: true, message, type });
    setTimeout(() => setToast({ show: false, message: "", type: "success" }), 3000);
  };

  const doSearch = useCallback(async () => {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const { items } = await searchElements({ q: query.trim() });
      setResults(items);
    } catch (e: any) {
      showToast(e.message, "error");
    }
    setLoading(false);
  }, [query]);

  const loadCompetences = useCallback(async () => {
    try {
      const { items } = await listCompetences();
      setCompetences(items);
    } catch (e: any) {
      showToast(e.message, "error");
    }
  }, [token]);

  useEffect(() => { if (tab === "competences") loadCompetences(); }, [tab, loadCompetences]);

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-3xl p-8 shadow-sm border border-black/5">
        <h1 className="text-3xl font-[300] text-navy">
          {t('teacher.bibliotheque.title')} <span className="italic text-orange">{t('teacher.bibliotheque.titleSuffix')}</span>
        </h1>
        <p className="text-gray mt-2">{t('teacher.bibliotheque.subtitle')}</p>
      </div>

      {toast.show && (
        <div className={`fixed top-4 right-4 z-50 px-4 py-2 rounded-xl text-white ${toast.type === "error" ? "bg-red-500" : "bg-green-500"}`}>
          {toast.message}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2">
        <Button
          variant={tab === "search" ? "secondary" : "ghost"}
          size="sm"
          onClick={() => setTab("search")}
        >
          <Search size={16} /> {t('teacher.bibliotheque.tabs.search')}
        </Button>
        <Button
          variant={tab === "competences" ? "secondary" : "ghost"}
          size="sm"
          onClick={() => setTab("competences")}
        >
          <Award size={16} /> {t('teacher.bibliotheque.tabs.skills')}
        </Button>
      </div>

      {/* Search Tab */}
      {tab === "search" && (
        <div className="space-y-4">
          <div className="flex gap-2">
            <div className="flex-1 relative">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray" />
              <input value={query} onChange={(e) => setQuery(e.target.value)} onKeyDown={(e) => e.key === "Enter" && doSearch()}
                placeholder={t('teacher.bibliotheque.searchPlaceholder')} className="w-full ps-9 pe-4 py-2.5 border rounded-xl text-sm" />
            </div>
            <Button variant="primary" size="sm" onClick={doSearch}>{t('teacher.bibliotheque.searchButton')}</Button>
          </div>

          {loading ? (
            <div className="text-center py-10 text-gray">{t('teacher.bibliotheque.searching')}</div>
          ) : results.length === 0 ? (
            <EmptyState
              icon={<Library size={40} />}
              title={query ? t('teacher.bibliotheque.noResults') : t('teacher.bibliotheque.noResultsHint')}
            />
          ) : (
            <div className="grid gap-2">
              {results.map((el) => (
                <div key={el.id} className="bg-white rounded-xl border border-black/5 p-3 flex items-center gap-3">
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold ${TYPE_COLORS[el.type] || "bg-gray-100"}`}>
                    {el.type.slice(0, 3).toUpperCase()}
                  </div>
                  <div className="flex-1 min-w-0">
                    <span className="text-sm font-medium text-navy truncate block">{el.titre}</span>
                    {el.description && <span className="text-xs text-gray truncate block">{el.description}</span>}
                  </div>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${STATUT_COLORS[el.statut] || ""}`}>{el.statut}</span>
                  {el.est_global && <span className="text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-600">{t('teacher.bibliotheque.globalBadge')}</span>}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Competences Tab */}
      {tab === "competences" && (
        <div>
          {competences.length === 0 ? (
            <EmptyState
              icon={<Award size={40} />}
              title={t('teacher.bibliotheque.noSkills')}
            />
          ) : (
            <div className="grid gap-2">
              {competences.map((c) => (
                <div key={c.id} className="bg-white rounded-xl border border-black/5 p-4">
                  <div className="flex items-center gap-2 mb-1">
                    <Award size={14} className="text-orange" />
                    <span className="font-semibold text-navy text-sm">{c.nom}</span>
                  </div>
                  {c.description && <p className="text-xs text-gray ms-5">{c.description}</p>}
                  <div className="flex gap-2 mt-2 ms-5">
                    {c.matiere && <span className="text-xs px-2 py-0.5 rounded-full bg-blue-50 text-blue-600">{c.matiere}</span>}
                    {c.niveau_scolaire && <span className="text-xs px-2 py-0.5 rounded-full bg-green-50 text-green-600">{c.niveau_scolaire}</span>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
