import { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { GraduationCap, ChevronDown, ChevronRight, Star, BookOpen, Clock, CheckCircle, AlertCircle, TrendingUp } from "lucide-react";
import { getMonParcours } from "../../../api";
import type { MonParcoursNiveau } from "../../../api";
import { PageWrapper } from "../../../components/ui";

const niveauColors: Record<string, string> = {
  decouverte: "bg-blue-500",
  standard: "bg-green-500",
  avance: "bg-orange-500",
};

const statusConfig: Record<string, { label: string; color: string; icon: typeof CheckCircle }> = {
  a_commencer: { label: "À commencer", color: "bg-gray-100 text-gray", icon: Clock },
  en_cours: { label: "En cours", color: "bg-blue-100 text-blue", icon: BookOpen },
  termine: { label: "Terminé", color: "bg-green-100 text-green", icon: CheckCircle },
  annule: { label: "Annulé", color: "bg-red-100 text-red", icon: AlertCircle },
};

export default function MonParcoursPage() {
  const { t } = useTranslation();
  const [parcours, setParcours] = useState<MonParcoursNiveau[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedMatieres, setExpandedMatieres] = useState<Set<number>>(new Set());

  const toggle = (id: number) => {
    setExpandedMatieres(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getMonParcours();
      if (data.niveaux) setParcours(data.niveaux);
    } catch { /* ignore */ }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) {
    return <PageWrapper title={<>Mon <span className="italic text-orange">Parcours</span></>} icon={<GraduationCap className="w-8 h-8" />}><div className="text-center py-12 text-gray">{t('monParcours.loading')}</div></PageWrapper>;
  }

  if (parcours.length === 0) {
    return (
      <PageWrapper title={<>Mon <span className="italic text-orange">Parcours</span></>} icon={<GraduationCap className="w-8 h-8" />}>
        <div className="bg-white rounded-2xl shadow-sm border border-black/5 p-12 text-center">
          <GraduationCap className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray mb-2">{t('monParcours.noActivePath')}</p>
          <p className="text-sm text-gray">{t('monParcours.buyPackPrompt')}</p>
        </div>
      </PageWrapper>
    );
  }

  return (
    <PageWrapper
      title={<>Mon <span className="italic text-orange">Parcours</span></>}
      subtitle={t('monParcours.subtitle')}
      icon={<GraduationCap className="w-8 h-8" />}
    >

      {parcours.map(niveau => {
        // Stats
        let totalChapitres = 0;
        let chapitresEnCours = 0;
        let chapitresTermines = 0;
        let totalNotions = 0;
        niveau.matieres.forEach(m => {
          totalChapitres += m.chapters.length;
          m.chapters.forEach(ch => {
            totalNotions += ch.notions_count;
            if (ch.status === "en_cours") chapitresEnCours++;
            if (ch.status === "termine") chapitresTermines++;
          });
        });

        return (
          <div key={niveau.niveau.id} className="bg-white rounded-2xl shadow-sm border border-black/5 overflow-hidden">
            {/* Header */}
            <div className="px-6 py-4 bg-gradient-to-r from-orange/5 to-blue/5 border-b border-black/5">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-semibold text-navy">{niveau.niveau.nom}</h2>
                  <p className="text-sm text-gray mt-0.5">
                    {totalChapitres} {t('monParcours.chapters', { count: totalChapitres })} • {" "}
                    {totalNotions} {t('monParcours.notions', { count: totalNotions })}
                  </p>
                </div>
                <div className="flex gap-3 text-center">
                  <div>
                    <p className="text-lg font-bold text-blue">{chapitresEnCours}</p>
                    <p className="text-xs text-gray">{t('monParcours.inProgress')}</p>
                  </div>
                  <div className="w-px bg-gray-200"></div>
                  <div>
                    <p className="text-lg font-bold text-green">{chapitresTermines}</p>
                    <p className="text-xs text-gray">{t('monParcours.completed')}</p>
                  </div>
                </div>
              </div>
              {/* Progress bar */}
              <div className="mt-3 h-2 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-orange to-orange-l rounded-full transition-all duration-500"
                  style={{ width: totalChapitres > 0 ? `${(chapitresTermines / totalChapitres) * 100}%` : "0%" }}
                />
              </div>
            </div>

            {/* Matieres */}
            <div className="divide-y divide-gray-100">
              {niveau.matieres.map(matiere => (
                <div key={matiere.id}>
                  <button
                    onClick={() => toggle(matiere.id)}
                    className="w-full flex items-center gap-3 px-6 py-4 hover:bg-gray-50 transition-colors text-start"
                  >
                    {expandedMatieres.has(matiere.id) ? (
                      <ChevronDown className="w-5 h-5 text-gray-400 flex-shrink-0" />
                    ) : (
                      <ChevronRight className="w-5 h-5 text-gray-400 flex-shrink-0" />
                    )}
                    <BookOpen className="w-5 h-5 text-blue flex-shrink-0" />
                    <div className="flex-1">
                      <p className="font-medium text-navy">{matiere.nom}</p>
                      <p className="text-xs text-gray">{matiere.chapters_count} {t('monParcours.chapters', { count: matiere.chapters_count })}</p>
                    </div>
                    {/* Mini status badges */}
                    <div className="flex gap-1">
                      {(() => {
                        const counts = { a_commencer: 0, en_cours: 0, termine: 0 };
                        matiere.chapters.forEach(ch => {
                          if (ch.status in counts) counts[ch.status as keyof typeof counts]++;
                        });
                        return (
                          <>
                            {counts.en_cours > 0 && (
                              <span className="px-2 py-0.5 bg-blue-100 text-blue rounded-full text-xs">{counts.en_cours}</span>
                            )}
                            {counts.termine > 0 && (
                              <span className="px-2 py-0.5 bg-green-100 text-green rounded-full text-xs">{counts.termine}</span>
                            )}
                          </>
                        );
                      })()}
                    </div>
                  </button>

                  {/* Chapters list */}
                  {expandedMatieres.has(matiere.id) && (
                    <div className="px-6 pb-4 space-y-2">
                      {matiere.chapters.map(ch => {
                        const cfg = statusConfig[ch.status] || statusConfig.a_commencer;
                        const Icon = cfg.icon;
                        return (
                          <div key={ch.id} className="flex items-center gap-3 px-4 py-3 bg-gray-50 rounded-xl">
                            <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${niveauColors[ch.niveau_assimilation || "standard"]}`}>
                              {ch.score_moyen !== null ? (
                                <span className="text-white text-xs font-bold">{Math.round(ch.score_moyen)}%</span>
                              ) : (
                                <Star className="w-4 h-4 text-white" />
                              )}
                            </div>
                            <div className="flex-1">
                              <p className="text-sm font-medium text-navy">{ch.nom}</p>
                              <div className="flex items-center gap-2 mt-0.5">
                                <span className={`px-2 py-0.5 rounded-full text-xs ${cfg.color}`}>
                                  <Icon className="w-3 h-3 inline me-1" />{cfg.label}
                                </span>
                                {ch.niveau_assimilation && (
                                  <span className="text-xs text-gray capitalize">{ch.niveau_assimilation}</span>
                                )}
                              </div>
                            </div>
                            <div className="text-end text-xs text-gray">
                              <p>{ch.notions_count} {t('monParcours.notion', { count: ch.notions_count })}</p>
                              {ch.scores_count > 0 && (
                                <p className="flex items-center gap-1 justify-end mt-0.5">
                                  <TrendingUp className="w-3 h-3" />
                                  {ch.scores_count} quiz
                                </p>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </PageWrapper>
  );
}
