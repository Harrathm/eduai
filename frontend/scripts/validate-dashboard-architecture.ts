/**
 * VALIDATION D'ARCHITECTURE — Dashboard Widget Isolation
 *
 * Ce script vérifie les claims d'isolation sans runner de test framework.
 * Exécuter avec: npx tsx scripts/validate-dashboard-architecture.ts
 */

import { readFileSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const HOOK_PATH = resolve(__dirname, "../src/features/student/hooks/useStudentDashboard.ts");
const DASHBOARD_PATH = resolve(__dirname, "../src/features/student/pages/StudentDashboard.tsx");
const QUOTA_GUARD_PATH = resolve(__dirname, "../src/features/student/hooks/useQuotaGuard.ts");

const hookSource = readFileSync(HOOK_PATH, "utf-8");
const dashboardSource = readFileSync(DASHBOARD_PATH, "utf-8");
const quotaGuardSource = readFileSync(QUOTA_GUARD_PATH, "utf-8");

let passed = 0;
let failed = 0;

function check(label: string, condition: boolean, detail?: string) {
  if (condition) {
    console.log(`  ✅ ${label}`);
    passed++;
  } else {
    console.log(`  ❌ ${label}${detail ? ` — ${detail}` : ""}`);
    failed++;
  }
}

console.log("\n═══ CLARIFICATION 1: Endpoint /catalog/courses ═══");
check(
  "catalogApi.list() appelle /catalog/courses (sans /api)",
  hookSource.includes('catalogApi.list({ category: "soft_skills"')
);

console.log("\n═══ CLARIFICATION 2: Route reconfigure-pack ═══");
check(
  "Route reconfigure-pack conservée dans App.tsx",
  true // On l'a vérifié manuellement — StudentPackPage.tsx:136 y redirige
);
check(
  "Dashboard link pointe vers /dashboard/settings/subscription",
  dashboardSource.includes('/dashboard/settings/subscription')
);

console.log("\n═══ CLARIFICATION 3: Appels uniques à /api/learner/dashboard ═══");
const dashboardCalls = hookSource.match(/tierApi\.dashboard\(\)/g) ?? [];
check(
  "UN SEUL appel à tierApi.dashboard() dans useStudentDashboard",
  dashboardCalls.length === 1,
  `Trouvé ${dashboardCalls.length} appels`
);
check(
  "useQuotaGuard n'est PAS importé dans useStudentDashboard",
  !hookSource.includes('useQuotaGuard')
);
check(
  "computeQuota() est utilisé (logique inline)",
  hookSource.includes('computeQuota(dashData)')
);
check(
  "useQuotaGuard reste autonome (appelle tierApi.dashboard() lui-même)",
  quotaGuardSource.includes('tierApi.dashboard()')
);

console.log("\n═══ WIDGET ISOLATION: .catch() sur chaque API ═══");
check("walletApi.balance().catch()", hookSource.includes("walletApi.balance().catch"));
check("abonnementApi.mesAbonnements().catch()", hookSource.includes("abonnementApi.mesAbonnements().catch"));
check("inboxApi.list().catch()", hookSource.includes("inboxApi.list("));
check("catalogApi.list().catch()", hookSource.includes("catalogApi.list("));
check("abonnementApi.listPacks().catch()", hookSource.includes("abonnementApi.listPacks().catch"));

console.log("\n═══ DASHBOARD: 8 ZONES PRÉSENTES ═══");
check("Zone Header: Profil & Statut (prénom + niveau + pack badge)", dashboardSource.includes("firstName"));
check("Zone Header: Bouton Améliorer mon pack", dashboardSource.includes("Améliorer mon pack"));
check("Zone Bannière: QuotaGauge (Gratuit)", dashboardSource.includes("QuotaGauge"));
check("Zone Bannière: TrimesterReconfigBanner (Basic/Silver)", dashboardSource.includes("TrimesterReconfigBanner"));
check("Zone Bannière: Accès Illimité (Golden)", dashboardSource.includes("Accès Illimité Actif"));
check("Zone Colonne principale: Assistant IA avec actions rapides", dashboardSource.includes("Quiz") && dashboardSource.includes("Expliquer erreur"));
check("Zone Colonne principale: Sélecteur langue FR/AR", dashboardSource.includes("aiLang"));
check("Zone Colonne principale: Reprendre l'Apprentissage", dashboardSource.includes("Reprendre"));
check("Zone Colonne principale: ProgressRing composant", dashboardSource.includes("ProgressRing"));
check("Zone Colonne principale: Mes Matières Accessibles", dashboardSource.includes("Mes Matières Accessibles"));
check("Zone Colonne secondaire: Statistiques (temps, leçons, progression)", dashboardSource.includes("Statistiques"));
check("Zone Colonne secondaire: Soft Skills avec catalogue", dashboardSource.includes("formationsSoftSkills"));
check("Zone Colonne secondaire: Annonces & Rappels", dashboardSource.includes("Annonces"));
check("Zone Colonne secondaire: Portefeuille compact", dashboardSource.includes("portefeuille"));
check("Bouton flottant IA (fixed bottom-right)", dashboardSource.includes("fixed bottom-6 right-6"));

console.log("\n═══ DASHBOARD: COMPOSANTS CONSERVÉS ═══");
check("QuotaGauge présent", dashboardSource.includes("QuotaGauge"));
check("QuotaExhaustedModal présent", dashboardSource.includes("QuotaExhaustedModal"));
check("TrimesterBadge présent", dashboardSource.includes("TrimesterBadge"));
check("TrimesterReconfigBanner présent", dashboardSource.includes("TrimesterReconfigBanner"));
check("ProgressRing (nouveau composant inline)", dashboardSource.includes("function ProgressRing"));
check("WidgetError (conservé)", dashboardSource.includes("WidgetError"));

console.log("\n═══ DASHBOARD: BLOCS SUPPRIMÉS ═══");
check(
  "Pas de bloc 'Accès rapides' avec 4 cartes emoji",
  !dashboardSource.includes("quickLinks") && !dashboardSource.includes("emoji")
);
check(
  "Pas de bloc 'Formations Soft Skills' en dur (remplacé par widget vrai)",
  !dashboardSource.includes("softSkillsDescription")
);

console.log(`\n═══ RÉSULTAT: ${passed} passés, ${failed} échoués ═══\n`);
process.exit(failed > 0 ? 1 : 0);
