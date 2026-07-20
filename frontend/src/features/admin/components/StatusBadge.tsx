import { ReactNode } from "react";

type BadgeVariant = "success" | "warning" | "danger" | "info" | "neutral" | "purple" | "orange";

const variantMap: Record<BadgeVariant, string> = {
  success: "bg-green-100 text-green-700",
  warning: "bg-yellow-100 text-yellow-700",
  danger: "bg-red-100 text-red-700",
  info: "bg-blue-100 text-blue-700",
  neutral: "bg-gray-100 text-gray-600",
  purple: "bg-purple-100 text-purple-700",
  orange: "bg-orange-100 text-orange-700",
};

interface StatusBadgeProps {
  label: string;
  variant?: BadgeVariant;
  dot?: boolean;
  icon?: ReactNode;
}

export function StatusBadge({ label, variant = "neutral", dot, icon }: StatusBadgeProps) {
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${variantMap[variant]}`}>
      {dot && (
        <span className="w-1.5 h-1.5 rounded-full bg-current" />
      )}
      {icon}
      {label}
    </span>
  );
}

interface RoleBadgeProps {
  role: string;
}

const roleVariants: Record<string, BadgeVariant> = {
  SUPER_ADMIN: "purple",
  super_admin: "purple",
  admin_school: "purple",
  PEDAGOGICAL_ADMIN: "info",
  pedagogical_admin: "info",
  PEDAGOGICAL_LEAD: "success",
  pedagogical_lead: "success",
  TEACHER: "green",
  teacher: "green",
  STUDENT: "info",
  student: "info",
};

export function RoleBadge({ role }: RoleBadgeProps) {
  const roleLabels: Record<string, string> = {
    pedagogical_admin: "Resp. Pédago. (Plateforme)",
    pedagogical_lead: "Resp. Pédago. (École)",
    admin_school: "Admin École",
  };
  const display = roleLabels[role] || role;
  const variant = roleVariants[role.toUpperCase()] || "neutral";
  return <StatusBadge label={display} variant={variant} />;
}

interface ActiveBadgeProps {
  isActive: boolean;
}

export function ActiveBadge({ isActive }: ActiveBadgeProps) {
  return (
    <StatusBadge
      label={isActive ? "Actif" : "Inactif"}
      variant={isActive ? "success" : "danger"}
      dot
    />
  );
}