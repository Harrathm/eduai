import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../../../store/authStore";
import { Card, CardHeader, CardTitle, Button, PageSpinner, EmptyState } from "../../../components/ui";
import { useStudentDashboard } from "../hooks/useStudentDashboard";
import { TrimesterBadge } from "../components/trimester/TrimesterBadge";
import { TrimesterReconfigBanner } from "../components/trimester/TrimesterReconfigBanner";
import { QuotaGauge } from "../components/quota/QuotaGauge";
import { QuotaExhaustedModal } from "../components/quota/QuotaExhaustedModal";
import { useState, useEffect } from "react";

function WidgetError({ message }: { message: string }) {
  return (
    <div className="flex items-center gap-2 px-4 py-2 text-xs text-red-500 bg-red-50 rounded-xl">
      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      {message}
    </div>
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
  } = useStudentDashboard();

  const [showQuotaModal, setShowQuotaModal] = useState(false);

  useEffect(() => {
    if (quota.exhausted && !quota.isNotFree && !loading) {
      setShowQuotaModal(true);
    }
  }, [quota.exhausted, quota.isNotFree, loading]);

  if (loading) return <PageSpinner message={t("student.dashboard.loading")} />;

  return (
    <div className="space-y-6">
      {/* ═══ HEADER ═══ */}
      <div className="bg-navy rounded-3xl p-8">
        <div className="flex items-center gap-3 mb-2">
          <h1 className="text-3xl font-[300] text-white">{t("student.dashboard.title")}</h1>
          {trimester.currentTrimester && (
            <TrimesterBadge
              label={trimester.currentTrimester.label}
              number={trimester.currentTrimester.number}
              startDate={trimester.currentTrimester.startDate}
              endDate={trimester.currentTrimester.endDate}
            />
          )}
        </div>
        <p className="text-white/50">
          {t("student.dashboard.welcome", { name: user?.full_name || user?.email })}
        </p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-2xl p-4 text-red-700 text-sm">{error}</div>
      )}

      {/* ═══ WIDGET #2 — PACK ACTIF ═══ */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>{t("student.dashboard.monPack")}</CardTitle>
          </CardHeader>
          <div className="flex items-center gap-3 mb-3">
            <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
              isGolden ? "bg-amber-100 text-amber-700"
              : packTier === "silver" ? "bg-gray-200 text-gray-700"
              : packTier === "basique" ? "bg-blue-100 text-blue-700"
              : "bg-gray-100 text-gray-500"
            }`}>
              {packTier ? packTier.charAt(0).toUpperCase() + packTier.slice(1) : "Gratuit"}
            </span>
            {isGolden && <span className="text-xs text-gray-400">{t("student.dashboard.accesIllimite")}</span>}
          </div>
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
          <div className="mt-3">
            <Button variant="ghost" size="sm" onClick={() => navigate("/dashboard/settings/subscription")}>
              {t("student.dashboard.voirMonAbonnement")}
            </Button>
          </div>
        </Card>

        {/* ═══ WIDGET #1 — OFFRES DISPONIBLES ═══ */}
        <Card>
          <CardHeader>
            <CardTitle>{t("student.dashboard.offresDisponibles")}</CardTitle>
          </CardHeader>
          {availablePacks.length > 0 ? (
            <div className="space-y-2">
              {availablePacks.map((pack) => (
                <div key={pack.id} className="flex items-center justify-between p-3 bg-cream rounded-xl">
                  <div>
                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold uppercase ${
                      pack.tier === "golden" ? "bg-amber-100 text-amber-700"
                      : pack.tier === "silver" ? "bg-gray-200 text-gray-700"
                      : "bg-blue-100 text-blue-700"
                    }`}>
                      {pack.tier}
                    </span>
                    <span className="ml-2 text-sm text-navy font-medium">{pack.name}</span>
                  </div>
                  <span className="text-sm font-semibold text-orange">{pack.price} TND</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-400">{t("student.dashboard.aucuneOffre")}</p>
          )}
          <div className="mt-3">
            <Button variant="ghost" size="sm" onClick={() => navigate("/dashboard/packs")}>
              {t("student.dashboard.voirToutesLesOffres")}
            </Button>
          </div>
        </Card>
      </div>

      {/* ═══ WIDGET #3 — PARCOURS ═══ + WIDGET #4 — ASSISTANT IA ═══ */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>{t("student.dashboard.monParcours")}</CardTitle>
          </CardHeader>
          {matieresCount > 0 ? (
            <>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-500">
                  {matieresCount} {t("student.dashboard.matieresSuivies")}
                </span>
                <span className="text-sm font-semibold text-navy">{globalProgress}%</span>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-2 mb-3">
                <div
                  className="bg-orange h-2 rounded-full transition-all"
                  style={{ width: `${Math.min(globalProgress, 100)}%` }}
                />
              </div>
              <Button variant="ghost" size="sm" onClick={() => navigate("/dashboard/courses")}>
                {t("student.dashboard.voirMesCours")}
              </Button>
            </>
          ) : (
            <EmptyState
              title={t("student.dashboard.aucunParcours")}
              description={t("student.dashboard.choisirMatieres")}
              action={
                <Button variant="primary" size="sm" onClick={() => navigate("/dashboard/packs")}>
                  {t("student.dashboard.voirLesPacks")}
                </Button>
              }
            />
          )}
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t("student.dashboard.assistantIA")}</CardTitle>
          </CardHeader>
          <p className="text-sm text-gray-500 mb-4">{t("student.dashboard.assistantIADescription")}</p>
          <Button variant="primary" size="sm" onClick={() => navigate("/dashboard/ai-tutor")}>
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 9l3 3-3 3m5 0h3M9 19V5m0 14l4-4 4 4-4-4z" />
            </svg>
            {t("student.dashboard.ouvrirAssistant")}
          </Button>
        </Card>
      </div>

      {/* ═══ WIDGET #5 — PORTEFEUILLE ═══ + WIDGET #8 — MESSAGES ═══ */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>{t("student.dashboard.portefeuille")}</CardTitle>
          </CardHeader>
          {wallet ? (
            <>
              <div className="flex items-baseline gap-2 mb-1">
                <span className="text-3xl font-[300] text-navy">{wallet.total_dt}</span>
                <span className="text-sm text-gray-400">DT</span>
              </div>
              <p className="text-xs text-gray-400 mb-3">
                {t("student.dashboard.tokensEquivalents", { count: wallet.total_tokens })}
              </p>
              <Button variant="ghost" size="sm" onClick={() => navigate("/dashboard/wallet")}>
                {t("student.dashboard.voirDetails")}
              </Button>
            </>
          ) : (
            <WidgetError message={t("student.dashboard.erreurChargement")} />
          )}
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t("student.dashboard.messages")}</CardTitle>
          </CardHeader>
          {unreadCount > 0 ? (
            <>
              <div className="flex items-center gap-2 mb-2">
                <span className="inline-flex items-center justify-center w-6 h-6 bg-red-500 text-white text-xs font-bold rounded-full">
                  {unreadCount}
                </span>
                <span className="text-sm text-gray-600">
                  {t("student.dashboard.nonLus", { count: unreadCount })}
                </span>
              </div>
              {lastMessage && (
                <p className="text-xs text-gray-400 truncate mb-3">
                  {lastMessage.sender_name} — {lastMessage.subject}
                </p>
              )}
            </>
          ) : (
            <p className="text-sm text-gray-400 mb-3">{t("student.dashboard.aucunMessageNonLu")}</p>
          )}
          <Button variant="ghost" size="sm" onClick={() => navigate("/dashboard/inbox")}>
            {t("student.dashboard.ouvrirMessagerie")}
          </Button>
        </Card>
      </div>

      {/* ═══ WIDGET #6 — SOFT SKILLS ═══ + WIDGET #7 — PROFIL ═══ */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>{t("student.dashboard.formationsSoftSkills")}</CardTitle>
          </CardHeader>
          {softSkillsCourses.length > 0 ? (
            <div className="space-y-2 mb-3">
              {softSkillsCourses.map((course) => (
                <div key={course.id} className="flex items-center gap-3 p-2 bg-cream rounded-lg">
                  <div className="w-8 h-8 bg-orange/10 rounded-lg flex items-center justify-center flex-shrink-0">
                    <svg className="w-4 h-4 text-orange" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-navy truncate">{course.title}</p>
                    <p className="text-[10px] text-gray-400">{course.category}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-400 mb-3">{t("student.dashboard.aucuneFormation")}</p>
          )}
          <div className="flex gap-2">
            <Button variant="ghost" size="sm" onClick={() => navigate("/dashboard/soft-skills")}>
              {t("student.dashboard.catalogue")}
            </Button>
            <Button variant="ghost" size="sm" onClick={() => navigate("/dashboard/my-skills")}>
              {t("student.dashboard.mesFormations")}
            </Button>
          </div>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t("student.dashboard.profil")}</CardTitle>
          </CardHeader>
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 bg-navy/10 rounded-full flex items-center justify-center">
              <span className="text-sm font-semibold text-navy">
                {user?.full_name?.charAt(0) || user?.email?.charAt(0) || "?"}
              </span>
            </div>
            <div>
              <p className="text-sm font-medium text-navy">{user?.full_name || user?.email}</p>
              <p className="text-xs text-gray-400">{(user as any)?.niveau_scolaire || t("student.dashboard.nonDefini")}</p>
            </div>
          </div>
          <Button variant="ghost" size="sm" onClick={() => navigate("/dashboard/profile")}>
            {t("student.dashboard.modifierProfil")}
          </Button>
        </Card>
      </div>

      {/* ═══ QUOTA EXHAUSTED MODAL ═══ */}
      <QuotaExhaustedModal open={showQuotaModal} onClose={() => setShowQuotaModal(false)} />
    </div>
  );
}
