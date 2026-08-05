import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../../../store/authStore";
import { Card, CardHeader, CardTitle, Button, PageSpinner } from "../../../components/ui";
import { useStudentDashboard } from "../hooks/useStudentDashboard";
import { TrimesterBadge } from "../components/trimester/TrimesterBadge";
import { TrimesterReconfigBanner } from "../components/trimester/TrimesterReconfigBanner";
import { QuotaGauge } from "../components/quota/QuotaGauge";
import { QuotaExhaustedModal } from "../components/quota/QuotaExhaustedModal";
import { useState, useEffect } from "react";

function WidgetError({ message }: { message: string }) {
  return (
    <div className="flex items-center gap-2 px-4 py-2 text-xs text-red-500 bg-red-50 rounded-xl">
      <svg className="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      {message}
    </div>
  );
}

function ProgressRing({ percent, size = 40 }: { percent: number; size?: number }) {
  const r = (size - 6) / 2;
  const circ = 2 * Math.PI * r;
  const offset = circ - (Math.min(percent, 100) / 100) * circ;
  return (
    <svg width={size} height={size} className="shrink-0 -rotate-90">
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#f1f5f9" strokeWidth="4" />
      <circle
        cx={size / 2} cy={size / 2} r={r} fill="none"
        stroke={percent >= 70 ? "#22c55e" : percent >= 40 ? "#f59e0b" : "#f97316"}
        strokeWidth="4" strokeLinecap="round" strokeDasharray={circ} strokeDashoffset={offset}
      />
    </svg>
  );
}

export default function StudentDashboard() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const {
    dashboard, packTier, wallet, unreadCount, lastMessage,
    softSkillsCourses, availablePacks,
    loading, error,
    quota, trimester,
    isFreePack, isBasicOrSilver, isGolden,
    matieresCount, globalProgress,
    lastLesson, learningTimeMinutes, averageScore,
  } = useStudentDashboard();

  const [showQuotaModal, setShowQuotaModal] = useState(false);
  const [aiLang, setAiLang] = useState<"fr" | "ar">("fr");

  useEffect(() => {
    if (quota.exhausted && !quota.isNotFree && !loading) {
      setShowQuotaModal(true);
    }
  }, [quota.exhausted, quota.isNotFree, loading]);

  if (loading) return <PageSpinner message={t("student.dashboard.loading")} />;

  const firstName = (user?.full_name || user?.email || "").split(" ")[0] || "Élève";
  const niveauScolaire = (user as any)?.niveau_scolaire || null;
  const courses = dashboard?.courses ?? [];

  return (
    <div className="space-y-6">
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-2xl p-4 text-red-700 text-sm">{error}</div>
      )}

      {/* ═══ [ZÉRO] HEADER PROFIL & STATUT ═══ */}
      <div className="bg-navy rounded-3xl p-6 lg:p-8">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-white/10 rounded-2xl flex items-center justify-center">
              <span className="text-xl font-semibold text-white">
                {firstName.charAt(0).toUpperCase()}
              </span>
            </div>
            <div>
              <h1 className="text-2xl lg:text-3xl font-[300] text-white">
                {t("student.dashboard.title")} — {firstName} !
              </h1>
              <div className="flex items-center gap-2 mt-1 flex-wrap">
                {niveauScolaire && (
                  <span className="text-xs text-white/40 bg-white/5 px-2 py-0.5 rounded-full">
                    {niveauScolaire}
                  </span>
                )}
                {packTier && (
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase ${
                    isGolden ? "bg-amber-400/20 text-amber-300"
                    : packTier === "silver" ? "bg-gray-300/20 text-gray-300"
                    : packTier === "basique" ? "bg-blue-400/20 text-blue-300"
                    : "bg-white/10 text-white/50"
                  }`}>
                    {packTier}
                  </span>
                )}
                {trimester.currentTrimester && (
                  <TrimesterBadge
                    label={trimester.currentTrimester.label}
                    number={trimester.currentTrimester.number}
                    startDate={trimester.currentTrimester.startDate}
                    endDate={trimester.currentTrimester.endDate}
                  />
                )}
              </div>
            </div>
          </div>
          <Button variant="primary" size="sm" onClick={() => navigate("/dashboard/packs")}>
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
            {t("student.dashboard.ouvrirAssistant").includes("assistant") ? "Améliorer mon pack" : t("student.dashboard.offresDisponibles")}
          </Button>
        </div>
      </div>

      {/* ═══ [UN] BANNIÈRE DYNAMIQUE DE STATUT & QUOTA ═══ */}
      {isFreePack && !quota.error && (
        <QuotaGauge used={quota.used} limit={quota.limit} percent={quota.percent} />
      )}
      {isBasicOrSilver && trimester.currentTrimester && (
        <TrimesterReconfigBanner
          canReconfigure={trimester.canReconfigure}
          daysRemaining={trimester.daysRemainingInWindow}
          trimesterLabel={trimester.currentTrimester.label}
          onReconfigure={() => navigate("/dashboard/settings/subscription")}
        />
      )}
      {isGolden && (
        <div className="flex items-center gap-3 bg-amber-50 border border-amber-200 rounded-2xl p-4">
          <div className="w-10 h-10 bg-amber-100 rounded-xl flex items-center justify-center">
            <svg className="w-5 h-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
            </svg>
          </div>
          <div>
            <p className="text-sm font-medium text-amber-800">Accès Illimité Actif</p>
            <p className="text-xs text-amber-600">Toutes les matières et formations sont accessibles</p>
          </div>
        </div>
      )}

      {/* ═══ GRILLE PRINCIPALE 3 COLONNES ═══ */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* ═══ [DEUX] COLONNE PRINCIPALE — lg:col-span-2 ═══ */}
        <div className="lg:col-span-2 space-y-6">

          {/* BLOC 1 — ASSISTANT IA (Copilote) */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <div className="w-8 h-8 bg-purple-100 rounded-xl flex items-center justify-center">
                    <svg className="w-4 h-4 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                  </div>
                  {t("student.dashboard.assistantIA")}
                </CardTitle>
                <div className="flex bg-cream rounded-lg p-0.5">
                  <button
                    onClick={() => setAiLang("fr")}
                    className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
                      aiLang === "fr" ? "bg-white text-navy shadow-sm" : "text-gray-400 hover:text-gray-600"
                    }`}
                  >FR</button>
                  <button
                    onClick={() => setAiLang("ar")}
                    className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
                      aiLang === "ar" ? "bg-white text-navy shadow-sm" : "text-gray-400 hover:text-gray-600"
                    }`}
                  >AR</button>
                </div>
              </div>
            </CardHeader>
            <p className="text-sm text-gray-500 mb-4">{t("student.dashboard.assistantIADescription")}</p>
            <div className="grid grid-cols-3 gap-3">
              {[
                { icon: "M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253", label: "Quiz" },
                { icon: "M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z", label: "Expliquer erreur" },
                { icon: "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2", label: "Aide Devoir" },
              ].map((action) => (
                <button
                  key={action.label}
                  onClick={() => navigate("/dashboard/ai-tutor")}
                  className="flex flex-col items-center gap-2 p-3 bg-cream hover:bg-cream-m rounded-xl transition-colors"
                >
                  <svg className="w-5 h-5 text-navy" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d={action.icon} />
                  </svg>
                  <span className="text-xs font-medium text-navy">{action.label}</span>
                </button>
              ))}
            </div>
          </Card>

          {/* BLOC 2 — REPRENDRE L'APPRENTISSAGE */}
          <Card>
            <CardHeader>
              <CardTitle>Reprendre l&apos;Apprentissage</CardTitle>
            </CardHeader>
            {lastLesson ? (
              <div className="flex items-center gap-4">
                <ProgressRing percent={lastLesson.progressPct} size={56} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-navy truncate">{lastLesson.title}</p>
                  <p className="text-xs text-gray-400 truncate">{lastLesson.courseTitle}</p>
                  <div className="flex items-center gap-2 mt-2">
                    <div className="flex-1 bg-gray-100 rounded-full h-1.5">
                      <div
                        className="bg-orange h-1.5 rounded-full transition-all"
                        style={{ width: `${Math.min(lastLesson.progressPct, 100)}%` }}
                      />
                    </div>
                    <span className="text-[10px] text-gray-400">{lastLesson.progressPct}%</span>
                  </div>
                </div>
                <Button variant="primary" size="sm" onClick={() => navigate("/dashboard/courses")}>
                  Continuer
                </Button>
              </div>
            ) : (
              <div className="text-center py-4">
                <p className="text-sm text-gray-400 mb-3">{t("student.dashboard.aucunParcours")}</p>
                <Button variant="primary" size="sm" onClick={() => navigate("/dashboard/packs")}>
                  {t("student.dashboard.voirLesPacks")}
                </Button>
              </div>
            )}
          </Card>

          {/* BLOC 3 — MES MATIÈRES ACCESSIBLES */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Mes Matières Accessibles</CardTitle>
                <span className="text-xs text-gray-400">{matieresCount} matière{matieresCount !== 1 ? "s" : ""}</span>
              </div>
            </CardHeader>
            {courses.length > 0 ? (
              <div className="grid grid-cols-2 gap-3">
                {courses.slice(0, 6).map((course) => (
                  <button
                    key={course.id}
                    onClick={() => navigate(`/dashboard/courses/${course.id}`)}
                    className="flex items-center gap-3 p-3 bg-cream hover:bg-cream-m rounded-xl transition-colors text-left"
                  >
                    <ProgressRing percent={course.progress_pct ?? 0} size={36} />
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-navy truncate">{course.title}</p>
                      <p className="text-[10px] text-gray-400">
                        {course.lessons_completed}/{course.total_lessons} leçons
                      </p>
                    </div>
                  </button>
                ))}
              </div>
            ) : (
              <div className="text-center py-4">
                <p className="text-sm text-gray-400">{t("student.dashboard.choisirMatieres")}</p>
              </div>
            )}
            {courses.length > 6 && (
              <div className="mt-3 text-center">
                <Button variant="ghost" size="sm" onClick={() => navigate("/dashboard/courses")}>
                  Voir toutes les matières ({courses.length})
                </Button>
              </div>
            )}
          </Card>
        </div>

        {/* ═══ [TROIS] COLONNE SECONDAIRE — lg:col-span-1 ═══ */}
        <div className="space-y-6">

          {/* BLOC 1 — VUE SYNTHÉTIQUE STATS */}
          <Card>
            <CardHeader>
              <CardTitle>Statistiques</CardTitle>
            </CardHeader>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                    <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <span className="text-sm text-gray-500">Temps d&apos;apprentissage</span>
                </div>
                <span className="text-sm font-semibold text-navy">{learningTimeMinutes} min</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                    <svg className="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <span className="text-sm text-gray-500">Leçons terminées</span>
                </div>
                <span className="text-sm font-semibold text-navy">{dashboard?.lessons_completed ?? 0}</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 bg-orange-100 rounded-lg flex items-center justify-center">
                    <svg className="w-4 h-4 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                    </svg>
                  </div>
                  <span className="text-sm text-gray-500">Progression globale</span>
                </div>
                <span className="text-sm font-semibold text-navy">{globalProgress}%</span>
              </div>
            </div>
          </Card>

          {/* BLOC 2 — MES FORMATIONS SOFT SKILLS */}
          <Card>
            <CardHeader>
              <CardTitle>{t("student.dashboard.formationsSoftSkills")}</CardTitle>
            </CardHeader>
            {softSkillsCourses.length > 0 ? (
              <div className="space-y-3 mb-3">
                {softSkillsCourses.map((course) => (
                  <div key={course.id} className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-orange/10 rounded-lg flex items-center justify-center shrink-0">
                      <svg className="w-4 h-4 text-orange" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-navy truncate">{course.title}</p>
                      <p className="text-[10px] text-gray-400">{course.category}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-400 mb-3">{t("student.dashboard.aucuneFormation")}</p>
            )}
            <Button variant="ghost" size="sm" onClick={() => navigate("/dashboard/soft-skills")} className="w-full">
              {t("student.dashboard.catalogue")}
            </Button>
          </Card>

          {/* BLOC 3 — ANNONCES & RAPPELS */}
          <Card>
            <CardHeader>
              <CardTitle>Annonces & Rappels</CardTitle>
            </CardHeader>
            <div className="space-y-3">
              {unreadCount > 0 && (
                <button
                  onClick={() => navigate("/dashboard/inbox")}
                  className="w-full flex items-center gap-3 p-3 bg-blue-50 hover:bg-blue-100 rounded-xl transition-colors text-left"
                >
                  <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center shrink-0">
                    <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-navy">{unreadCount} message{unreadCount !== 1 ? "s" : ""} non lu{unreadCount !== 1 ? "s" : ""}</p>
                    {lastMessage && (
                      <p className="text-[10px] text-gray-400 truncate">{lastMessage.subject}</p>
                    )}
                  </div>
                </button>
              )}
              <div className="flex items-center gap-3 p-3 bg-cream rounded-xl">
                <div className="w-8 h-8 bg-gray-200 rounded-lg flex items-center justify-center shrink-0">
                  <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-medium text-navy">Aucun devoir à venir</p>
                  <p className="text-[10px] text-gray-400">Prochains rappels</p>
                </div>
              </div>
            </div>
          </Card>

          {/* PORTFEUILLE — compact */}
          <Card>
            <CardHeader>
              <CardTitle>{t("student.dashboard.portefeuille")}</CardTitle>
            </CardHeader>
            {wallet ? (
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-baseline gap-1">
                    <span className="text-2xl font-[300] text-navy">{wallet.total_dt}</span>
                    <span className="text-xs text-gray-400">DT</span>
                  </div>
                  <p className="text-[10px] text-gray-400">{t("student.dashboard.tokensEquivalents", { count: wallet.total_tokens })}</p>
                </div>
                <Button variant="ghost" size="sm" onClick={() => navigate("/dashboard/wallet")}>
                  {t("student.dashboard.voirDetails")}
                </Button>
              </div>
            ) : (
              <WidgetError message={t("student.dashboard.erreurChargement")} />
            )}
          </Card>
        </div>
      </div>

      {/* ═══ BOUTON FLOTTANT IA ═══ */}
      <button
        onClick={() => navigate("/dashboard/ai-tutor")}
        className="fixed bottom-6 right-6 z-50 w-14 h-14 bg-orange hover:bg-orange/90 text-white rounded-full shadow-lg shadow-orange/30 flex items-center justify-center transition-all hover:scale-105"
        title={t("student.dashboard.assistantIA")}
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
        </svg>
      </button>

      {/* ═══ QUOTA EXHAUSTED MODAL ═══ */}
      <QuotaExhaustedModal open={showQuotaModal} onClose={() => setShowQuotaModal(false)} />
    </div>
  );
}
