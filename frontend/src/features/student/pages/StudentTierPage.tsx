import React, { useEffect, useState } from "react";
import { useAuthStore } from "../../../store/authStore";
import { tierAPI, type DashboardData, type RecommendedPath as RecommendedPathType } from "../../../api/tier";
import TierBadge from "../../../components/TierBadge";
import DailyObjective from "../../../components/DailyObjective";
import RecommendedPath from "../../../components/RecommendedPath";

const TIER_DETAILS: Record<string, { title: string; description: string; color: string; features: string[] }> = {
  decouverte: {
    title: "Découverte",
    description: "Parcours guidé pour commencer votre apprentissage",
    color: "from-blue-500 to-blue-600",
    features: [
      "Accès IA : questions simples (ask / explain)",
      "Parcours guidé avec objectifs quotidiens",
      "Accès aux cours gratuits et achetés",
    ],
  },
  excellence: {
    title: "Excellence",
    description: "Recommandations adaptatives pour maximiser vos résultats",
    color: "from-purple-500 to-purple-600",
    features: [
      "Tout le palier Découverte +",
      "Exercices ciblés générés par IA",
      "Test de positionnement adaptatif",
      "Recommandations personnalisées",
      "Analytics détaillés par matière",
    ],
  },
  etablissement: {
    title: "Établissement",
    description: "Parcours complet aligné au programme national de votre école",
    color: "from-amber-500 to-amber-600",
    features: [
      "Tout le palier Excellence +",
      "Contenu personnalisé (génération IA complète)",
      "Contenu exclusif de votre établissement",
      "Parcours programme national",
      "Suivi analytics complet",
    ],
  },
};

export default function StudentTierPage() {
  const { user } = useAuthStore();
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [path, setPath] = useState<RecommendedPathType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [dash, recPath] = await Promise.all([
          tierAPI.dashboard(),
          tierAPI.recommendedPath(),
        ]);
        setDashboard(dash);
        setPath(recPath);
      } catch (e: any) {
        setError(e.message || "Erreur de chargement");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="space-y-8 animate-pulse">
        <div className="bg-navy rounded-3xl p-8 h-32" />
        <div className="grid grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-white rounded-2xl h-24" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-2xl p-6 text-red-700">
        Erreur : {error}
      </div>
    );
  }

  if (!dashboard) return null;

  const tier = dashboard.tier;
  const tierInfo = TIER_DETAILS[tier] || TIER_DETAILS.decouverte;

  return (
    <div className="space-y-8">
      {/* Header with tier */}
      <div className={`bg-gradient-to-r ${tierInfo.color} rounded-3xl p-8 text-white`}>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-[300]">
              Palier <span className="italic">{tierInfo.title}</span>
            </h1>
            <p className="text-white/70 mt-2">{tierInfo.description}</p>
          </div>
          <TierBadge tier={tier} size="lg" />
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <div className="text-4xl font-[300] text-orange">{dashboard.total_enrolled_courses}</div>
          <div className="text-sm text-gray mt-1">Cours inscrits</div>
        </div>
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <div className="text-4xl font-[300] text-green-600">{dashboard.overall_progress_pct}%</div>
          <div className="text-sm text-gray mt-1">Progression globale</div>
        </div>
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <div className="text-4xl font-[300] text-blue-600">
            {dashboard.lessons_completed}/{dashboard.total_lessons}
          </div>
          <div className="text-sm text-gray mt-1">Leçons complétées</div>
        </div>
      </div>

      {/* Tier features */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
        <h2 className="font-medium text-navy mb-3">Vos fonctionnalités</h2>
        <ul className="space-y-2">
          {tierInfo.features.map((f, i) => (
            <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
              <span className="text-green-500 mt-0.5">✓</span>
              <span>{f}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Daily objective + Recommended path */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <DailyObjective objective={dashboard.daily_objective} />
        {path && <RecommendedPath path={path} />}
      </div>

      {/* Matiere stats (excellence/etablissement) */}
      {dashboard.matiere_stats && Object.keys(dashboard.matiere_stats).length > 0 && (
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <h2 className="font-medium text-navy mb-4">Progression par matière</h2>
          <div className="space-y-3">
            {Object.entries(dashboard.matiere_stats).map(([matiere, stat]) => (
              <div key={matiere}>
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="text-gray-700">{matiere}</span>
                  <span className="text-gray-400">{stat.progress_pct}%</span>
                </div>
                <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-navy rounded-full transition-all"
                    style={{ width: `${stat.progress_pct}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Suggested school courses (etablissement) */}
      {dashboard.suggested_school_courses && dashboard.suggested_school_courses.length > 0 && (
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <h2 className="font-medium text-navy mb-4">Cours disponibles dans votre établissement</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {dashboard.suggested_school_courses.map((c) => (
              <a
                key={c.id}
                href={`/dashboard/courses/${c.id}`}
                className="block p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors"
              >
                <div className="font-medium text-navy text-sm">{c.title}</div>
                <div className="text-xs text-gray-400 mt-1">{c.niveau_scolaire}</div>
              </a>
            ))}
          </div>
        </div>
      )}

      {/* Upgrade prompt */}
      {tier !== "etablissement" && (
        <div className="bg-gradient-to-r from-orange-p/20 to-cream rounded-2xl p-6 border border-orange/20">
          <h3 className="font-medium text-navy mb-2">Passer au palier supérieur</h3>
          <p className="text-sm text-gray-600 mb-4">
            {tier === "decouverte"
              ? "Achetez un pack Excellence pour débloquer les exercices ciblés et le test de positionnement."
              : "Contactez votre admin d'école pour activer le palier Établissement et accéder au contenu exclusif."}
          </p>
          {tier === "decouverte" && (
            <a
              href="/dashboard/packs"
              className="inline-block px-5 py-2 bg-navy text-white rounded-xl text-sm font-medium hover:bg-navy/90 transition-colors"
            >
              Voir les packs
            </a>
          )}
        </div>
      )}
    </div>
  );
}
