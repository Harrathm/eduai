import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useAuthStore } from "../../../store/authStore";
import { tierAPI, type DashboardData, type DailyObjective } from "../../../api/tier";
import { tokenStorage } from "../../../utils/tokenStorage";

function StatSkeleton() {
  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5 animate-pulse">
      <div className="h-10 w-16 bg-gray-200 rounded mb-2" />
      <div className="h-4 w-24 bg-gray-100 rounded" />
    </div>
  );
}

function ObjectiveSkeleton() {
  return (
    <div className="bg-white rounded-3xl p-6 shadow-sm border border-black/5 animate-pulse">
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 bg-gray-200 rounded-xl" />
        <div className="flex-1">
          <div className="h-5 w-48 bg-gray-200 rounded mb-2" />
          <div className="h-4 w-72 bg-gray-100 rounded" />
        </div>
      </div>
    </div>
  );
}

function PalierBadge({ tier }: { tier: string }) {
  const { t } = useTranslation();
  const labels: Record<string, { label: string; color: string }> = {
    decouverte: { label: "Découverte", color: "bg-blue-100 text-blue-700" },
    excellence: { label: "Excellence", color: "bg-orange-100 text-orange-700" },
    etablissement: { label: "Établissement", color: "bg-purple-100 text-purple-700" },
  };
  const info = labels[tier] || labels.decouverte;
  return (
    <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${info.color}`}>
      {t('student.dashboard.palier')} : {info.label}
    </span>
  );
}

function PackBadge({ tier }: { tier: string }) {
  const { t } = useTranslation();
  const labels: Record<string, { label: string; color: string }> = {
    gratuit: { label: "Gratuit", color: "bg-gray-100 text-gray-700" },
    basique: { label: "Basique", color: "bg-blue-100 text-blue-700" },
    silver: { label: "Silver", color: "bg-gray-200 text-gray-700" },
    golden: { label: "Golden", color: "bg-amber-100 text-amber-700" },
  };
  const info = labels[tier] || labels.gratuit;
  return (
    <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${info.color}`}>
      {t('student.dashboard.pack')} : {info.label}
    </span>
  );
}

function DailyObjectiveCard({ objective }: { objective: DailyObjective | null }) {
  const { t } = useTranslation();
  if (!objective) return null;

  const icons: Record<string, string> = {
    no_enrollment: "📚",
    continue_lesson: "📖",
    start_course: "🚀",
    no_lessons: "📭",
    adaptive_practice: "🎯",
    review: "🔄",
    curriculum_lesson: "📋",
    no_pending: "🎉",
  };

  return (
    <div className="bg-gradient-to-r from-orange/10 to-cream rounded-3xl p-6 border border-orange/20">
      <div className="flex items-start gap-4">
        <div className="w-12 h-12 bg-gradient-to-br from-orange to-orange-l rounded-xl flex items-center justify-center flex-shrink-0 shadow-sm">
          <span className="text-2xl">{icons[objective.type] || "🎯"}</span>
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-semibold text-navy text-sm">{t('student.dashboard.dailyObjective')}</h3>
            <PalierBadge tier={objective.tier} />
          </div>
          <p className="text-gray-700 text-sm leading-relaxed">{objective.message}</p>
          {objective.estimated_minutes > 0 && (
            <p className="text-gray-400 text-xs mt-1">
              ~{objective.estimated_minutes} {t('student.dashboard.minEstimees')}
            </p>
          )}
        </div>
        {objective.lesson_id && (
          <a
            href={`/dashboard/courses/${objective.lesson_id}`}
            className="px-4 py-2 bg-navy text-white text-xs font-medium rounded-xl hover:bg-navy/90 transition-colors flex-shrink-0"
          >
            {t('student.dashboard.commencer')}
          </a>
        )}
      </div>
    </div>
  );
}

export default function StudentDashboard() {
  const { t } = useTranslation();
  const { user } = useAuthStore();
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [packTier, setPackTier] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const [dashData, aboData] = await Promise.all([
          tierAPI.dashboard(),
          fetch("/api/abonnements/mes-abonnements", {
            headers: { Authorization: `Bearer ${tokenStorage.getToken()}` },
          }).then((r) => r.ok ? r.json() : { items: [] }).catch(() => ({ items: [] })),
        ]);
        setDashboard(dashData);
        const activeAbo = (aboData.items || []).find((a: any) => a.statut === "actif" || a.statut === "grace");
        if (activeAbo?.pack?.tier) setPackTier(activeAbo.pack.tier);
      } catch (err: any) {
        setError(err.message || t('student.dashboard.erreurChargement'));
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="bg-navy rounded-3xl p-8">
        <h1 className="text-4xl font-[300] text-white">
          {t('student.dashboard.title')}
        </h1>
        <p className="text-white/50 mt-2">{t('student.dashboard.welcome', { name: user?.full_name })}</p>
        {dashboard?.tier && (
          <div className="mt-3 flex items-center gap-2">
            <PalierBadge tier={dashboard.tier} />
            {packTier && <PackBadge tier={packTier} />}
          </div>
        )}
      </div>

      {/* Daily Objective — first section */}
      {loading ? (
        <ObjectiveSkeleton />
      ) : dashboard?.daily_objective ? (
        <DailyObjectiveCard objective={dashboard.daily_objective} />
      ) : null}

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {loading ? (
          <>
            <StatSkeleton />
            <StatSkeleton />
            <StatSkeleton />
          </>
        ) : (
          <>
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
              <div className="text-4xl font-[300] text-orange">
                {dashboard?.total_enrolled_courses ?? 0}
              </div>
              <div className="text-sm text-gray mt-1">{t('student.dashboard.mesCours')}</div>
              {dashboard && dashboard.total_enrolled_courses > 0 && (
                <div className="text-xs text-gray-400 mt-1">
                  {dashboard.lessons_completed}/{dashboard.total_lessons} {t('student.dashboard.leconsCompletees')}
                </div>
              )}
            </div>
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
              <div className="text-4xl font-[300] text-green-600">
                {dashboard?.overall_progress_pct ?? 0}%
              </div>
              <div className="text-sm text-gray mt-1">{t('student.dashboard.progression')}</div>
              {dashboard && dashboard.total_enrolled_courses > 0 && (
                <div className="w-full bg-gray-100 rounded-full h-1.5 mt-2">
                  <div
                    className="bg-green-500 h-1.5 rounded-full transition-all"
                    style={{ width: `${Math.min(dashboard.overall_progress_pct, 100)}%` }}
                  />
                </div>
              )}
            </div>
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
              <div className="text-4xl font-[300] text-purple-600">
                {dashboard?.lessons_completed ?? 0}
              </div>
              <div className="text-sm text-gray mt-1">{t('student.dashboard.leconsCompleteesTitle')}</div>
              {dashboard && dashboard.total_lessons > 0 && (
                <div className="text-xs text-gray-400 mt-1">
                  {t('student.dashboard.surTotal', { total: dashboard.total_lessons })}
                </div>
              )}
            </div>
          </>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-2xl p-4 text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Quick Actions */}
      <div className="bg-white rounded-3xl p-8 shadow-sm border border-black/5">
        <h2 className="text-2xl font-[300] text-navy mb-6">{t('student.dashboard.accesRapide')}</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <a href="/dashboard/courses" className="block p-6 bg-gradient-to-br from-orange-p to-cream rounded-2xl text-center hover:shadow-md transition-shadow cursor-pointer">
            <div className="text-3xl mb-2">📚</div>
            <div className="font-medium text-navy">{t('student.dashboard.catalogue')}</div>
          </a>
          <a href="/dashboard/assignments" className="block p-6 bg-gradient-to-br from-blue-50 to-cream rounded-2xl text-center hover:shadow-md transition-shadow cursor-pointer">
            <div className="text-3xl mb-2">📝</div>
            <div className="font-medium text-navy">{t('student.dashboard.devoirs')}</div>
          </a>
          <a href="/dashboard/ai-tutor" className="block p-6 bg-gradient-to-br from-purple-50 to-cream rounded-2xl text-center hover:shadow-md transition-shadow cursor-pointer">
            <div className="text-3xl mb-2">🤖</div>
            <div className="font-medium text-navy">{t('student.dashboard.tuteurIA')}</div>
          </a>
          <a href="/dashboard/wallet" className="block p-6 bg-gradient-to-br from-green-50 to-cream rounded-2xl text-center hover:shadow-md transition-shadow cursor-pointer">
            <div className="text-3xl mb-2">💳</div>
            <div className="font-medium text-navy">{t('student.dashboard.portefeuille')}</div>
          </a>
          <a href="/dashboard/tier" className="block p-6 bg-gradient-to-br from-purple-50 to-cream rounded-2xl text-center hover:shadow-md transition-shadow cursor-pointer">
            <div className="text-3xl mb-2">🎯</div>
            <div className="font-medium text-navy">{t('student.dashboard.monPalier')}</div>
          </a>
        </div>
      </div>

      {/* Enrolled Courses */}
      {dashboard && dashboard.courses.length > 0 && (
        <div className="bg-white rounded-3xl p-8 shadow-sm border border-black/5">
          <h2 className="text-2xl font-[300] text-navy mb-6">{t('student.dashboard.mesCours')}</h2>
          <div className="space-y-3">
            {dashboard.courses.map((course) => (
              <a
                key={course.id}
                href={`/dashboard/courses/${course.id}`}
                className="flex items-center justify-between p-4 rounded-xl border border-black/5 hover:bg-gray-50 transition-colors"
              >
                <div className="flex-1 min-w-0">
                  <h3 className="font-medium text-navy text-sm truncate">{course.title}</h3>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {course.niveau_scolaire} · {course.lessons_completed}/{course.total_lessons} {t('student.dashboard.lecons')}
                  </p>
                </div>
                <div className="flex items-center gap-3 flex-shrink-0">
                  <div className="w-20 bg-gray-100 rounded-full h-1.5">
                    <div
                      className="bg-orange h-1.5 rounded-full"
                      style={{ width: `${Math.min(course.progress_pct, 100)}%` }}
                    />
                  </div>
                  <span className="text-xs text-gray-500 w-10 text-end">{course.progress_pct}%</span>
                </div>
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
