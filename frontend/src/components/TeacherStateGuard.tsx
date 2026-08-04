import { useAuthStore } from "../store/authStore";
import { Navigate } from "react-router-dom";
import { AlertTriangle, Clock, Ban, Loader2 } from "lucide-react";

/**
 * TeacherStateGuard — P1 Audit
 *
 * États teacher :
 *   A = validé (is_approved=true, subscription_plan != "trial" ou school_affiliated)
 *   B = en attente (is_approved=false)
 *   C = suspendu (is_approved=true, subscription_plan="trial" avec restrictions)
 *
 * Règles :
 *   - State A : accès complet
 *   - State B : accès lecture seule + dashboard (pas de création/édition)
 *   - State C : accès lecture seule + wallet/abonnements uniquement
 */
export type TeacherState = "A" | "B" | "C";

export function getTeacherState(user: any): TeacherState {
  if (!user || user.role?.toUpperCase() !== "TEACHER") return "A";
  if (user.is_approved === false) return "B";
  if (user.subscription_plan === "trial") return "C";
  return "A";
}

function TeacherBlockedBanner({ state, reason }: { state: TeacherState; reason: string }) {
  const colors = {
    B: "bg-amber-50 border-amber-200 text-amber-800",
    C: "bg-red-50 border-red-200 text-red-800",
  };
  const icons = {
    B: <Clock size={20} className="text-amber-500" />,
    C: <Ban size={20} className="text-red-500" />,
  };
  const labels = {
    B: "Compte en attente de validation",
    C: "Compte restreint",
  };

  return (
    <div className={`border rounded-xl p-4 mb-6 flex items-start gap-3 ${colors[state]}`}>
      {icons[state]}
      <div>
        <p className="font-semibold text-sm">{labels[state]}</p>
        <p className="text-xs mt-1 opacity-80">{reason}</p>
      </div>
    </div>
  );
}

/**
 * Composant wrapper pour les routes teacher qui bloquent l'accès en écriture
 * selon l'état du teacher.
 *
 * children = contenu de la page (affiché en lecture seule si état B/C)
 */
export function TeacherWriteGuard({ children }: { children: React.ReactNode }) {
  const user = useAuthStore((s) => s.user);
  const state = getTeacherState(user);

  if (state === "B") {
    return (
      <div className="p-6">
        <TeacherBlockedBanner state="B" reason="Vous ne pouvez pas créer ou modifier de contenu en attendant la validation pédagogique par un responsable." />
        <div className="opacity-60 pointer-events-none">{children}</div>
      </div>
    );
  }

  if (state === "C") {
    return (
      <div className="p-6">
        <TeacherBlockedBanner state="C" reason="Votre compte est en période d'essai. Souscrivez à un pack pour accéder à toutes les fonctionnalités." />
        <div className="opacity-60 pointer-events-none">{children}</div>
      </div>
    );
  }

  return <>{children}</>;
}

/**
 * Composant guard qui redirige les teachers non-approuvés vers le dashboard
 * avec un message. Utilisé pour les routes qui nécessitent l'état A.
 */
export function RequireTeacherApproved({ children }: { children: React.ReactNode }) {
  const user = useAuthStore((s) => s.user);
  const state = getTeacherState(user);

  if (state === "B") {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="text-center max-w-md p-8">
          <Clock size={48} className="mx-auto text-amber-400 mb-4" />
          <h2 className="text-xl font-semibold text-navy mb-2">Validation en cours</h2>
          <p className="text-gray text-sm mb-4">
            Votre compte enseignant est en attente de validation pédagogique.
            Vous recevrez une notification une fois approuvé.
          </p>
          <Navigate to="/dashboard" replace />
        </div>
      </div>
    );
  }

  if (state === "C") {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="text-center max-w-md p-8">
          <Ban size={48} className="mx-auto text-red-400 mb-4" />
          <h2 className="text-xl font-semibold text-navy mb-2">Accès restreint</h2>
          <p className="text-gray text-sm mb-4">
            Votre compte est en période d'essai. Souscrivez à un pack pour accéder à cette fonctionnalité.
          </p>
          <a href="/dashboard/teacher/abonnements" className="inline-block bg-orange text-white px-4 py-2 rounded-xl text-sm hover:bg-orange/90">
            Voir les packs
          </a>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

/**
 * Badge état teacher — affiché dans le dashboard
 */
export function TeacherStateBadge() {
  const user = useAuthStore((s) => s.user);
  const state = getTeacherState(user);

  const config = {
    A: { label: "Validé", color: "bg-green-100 text-green-700" },
    B: { label: "En attente", color: "bg-amber-100 text-amber-700" },
    C: { label: "Essai", color: "bg-red-100 text-red-600" },
  };

  if (user?.role?.toUpperCase() !== "TEACHER") return null;

  return (
    <span className={`text-xs px-2 py-0.5 rounded-full ${config[state].color}`}>
      {config[state].label}
    </span>
  );
}
