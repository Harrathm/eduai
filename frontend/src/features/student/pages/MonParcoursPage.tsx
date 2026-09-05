import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { GraduationCap, ChevronDown, ChevronRight, BookOpen, Clock, CheckCircle, PlayCircle } from "lucide-react";
import { getMonParcours } from "../../../api";
import type { MonParcoursNiveau } from "../../../api";
import { PageWrapper, Button } from "../../../components/ui";

const STATUS_COLORS: Record<string, string> = {
  course: "bg-blue-100 text-blue",
  free: "bg-green-100 text-green",
};

export default function MonParcoursPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
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

  // Aucun niveau actif (aucun pack)
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

  const totalCourses = parcours.reduce(
    (acc, n) => acc + n.matieres.filter(m => (m.courses || []).length > 0).length,
    0
  );

  // Niveau actif mais aucune matière avec cours publié : message + redirection catalogue
  if (totalCourses === 0) {
    return (
      <PageWrapper title={<>Mon <span className="italic text-orange">Parcours</span></>} icon={<GraduationCap className="w-8 h-8" />}>
        <div className="bg-white rounded-2xl shadow-sm border border-black/5 p-12 text-center">
          <BookOpen className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="text-navy font-medium mb-2">Aucun contenu disponible pour votre niveau actuellement. Explorez le catalogue global.</p>
          <p className="text-sm text-gray mb-6">Consultez le catalogue pour découvrir les cours disponibles.</p>
          <Button variant="primary" size="md" onClick={() => navigate("/catalog")}>
            Consulter le catalogue
          </Button>
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
        const matieresAvecCours = niveau.matieres.filter(m => (m.courses || []).length > 0);
        if (matieresAvecCours.length === 0) return null;

        return (
          <div key={niveau.niveau.id} className="bg-white rounded-2xl shadow-sm border border-black/5 overflow-hidden">
            {/* Header */}
            <div className="px-6 py-4 bg-gradient-to-r from-orange/5 to-blue/5 border-b border-black/5">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-semibold text-navy">{niveau.niveau.nom}</h2>
                  <p className="text-sm text-gray mt-0.5">
                    {matieresAvecCours.length} {t('monParcours.matieres', { count: matieresAvecCours.length })}
                  </p>
                </div>
              </div>
            </div>

            {/* Matieres */}
            <div className="divide-y divide-gray-100">
              {matieresAvecCours.map(matiere => (
                <div key={matiere.id}>
                  <Button
                    variant="ghost"
                    size="md"
                    onClick={() => toggle(matiere.id)}
                    className="w-full justify-start"
                  >
                    {expandedMatieres.has(matiere.id) ? (
                      <ChevronDown className="w-5 h-5 text-gray-400 flex-shrink-0" />
                    ) : (
                      <ChevronRight className="w-5 h-5 text-gray-400 flex-shrink-0" />
                    )}
                    <BookOpen className="w-5 h-5 text-blue flex-shrink-0" />
                    <div className="flex-1">
                      <p className="font-medium text-navy">{matiere.nom}</p>
                      <p className="text-xs text-gray">{matiere.courses.length} {t('monParcours.courses', { count: matiere.courses.length })}</p>
                    </div>
                    <span className="px-2 py-0.5 bg-blue-100 text-blue rounded-full text-xs">
                      {matiere.courses.length}
                    </span>
                  </Button>

                  {/* Cours réels */}
                  {expandedMatieres.has(matiere.id) && (
                    <div className="px-6 pb-4 space-y-2">
                      {matiere.courses.map(course => (
                        <button
                          key={course.id}
                          onClick={() => navigate(`/dashboard/courses/${course.id}`)}
                          className="w-full flex items-center gap-3 px-4 py-3 bg-gray-50 rounded-xl hover:bg-blue-50 hover:border-blue-200 border border-transparent transition-all text-start"
                        >
                          {course.thumbnail_url || course.cover_url ? (
                            <img
                              src={course.thumbnail_url || course.cover_url}
                              alt={course.title}
                              className="w-14 h-14 rounded-lg object-cover flex-shrink-0"
                            />
                          ) : (
                            <div className="w-14 h-14 rounded-lg bg-gradient-to-br from-blue to-blue-l flex items-center justify-center flex-shrink-0">
                              <PlayCircle className="w-7 h-7 text-white" />
                            </div>
                          )}
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-navy truncate">{course.title}</p>
                            {course.description && (
                              <p className="text-xs text-gray truncate mt-0.5">{course.description}</p>
                            )}
                            <div className="flex items-center gap-2 mt-1">
                              <span className={`px-2 py-0.5 rounded-full text-xs ${course.is_free ? STATUS_COLORS.free : STATUS_COLORS.course}`}>
                                {course.is_free ? "Gratuit" : "Premium"}
                              </span>
                              {course.total_lessons > 0 && (
                                <span className="flex items-center gap-1 text-xs text-gray">
                                  <Clock className="w-3 h-3" />
                                  {course.total_lessons} {t('monParcours.lessons', { count: course.total_lessons })}
                                </span>
                              )}
                            </div>
                          </div>
                          <CheckCircle className="w-5 h-5 text-gray-300 flex-shrink-0" />
                        </button>
                      ))}
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
