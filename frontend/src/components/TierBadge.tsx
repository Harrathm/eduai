import React from "react";

interface TierBadgeProps {
  tier: string;
  size?: "sm" | "md" | "lg";
}

const TIER_CONFIG: Record<string, { label: string; color: string; bg: string; icon: string }> = {
  decouverte: {
    label: "Découverte",
    color: "text-blue-700",
    bg: "bg-blue-100 border-blue-200",
    icon: "🌱",
  },
  excellence: {
    label: "Excellence",
    color: "text-purple-700",
    bg: "bg-purple-100 border-purple-200",
    icon: "⭐",
  },
  etablissement: {
    label: "Établissement",
    color: "text-amber-700",
    bg: "bg-amber-100 border-amber-200",
    icon: "🏛️",
  },
};

export default function TierBadge({ tier, size = "md" }: TierBadgeProps) {
  const config = TIER_CONFIG[tier] || TIER_CONFIG.decouverte;

  const sizeClasses = {
    sm: "text-xs px-2 py-0.5",
    md: "text-sm px-3 py-1",
    lg: "text-base px-4 py-1.5",
  };

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border font-medium ${config.color} ${config.bg} ${sizeClasses[size]}`}
    >
      <span>{config.icon}</span>
      <span>{config.label}</span>
    </span>
  );
}
