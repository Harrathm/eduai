import { ReactNode } from "react";

interface KPICardProps {
  label: string;
  value: string | number;
  subValue?: string;
  icon?: ReactNode;
  trend?: number;
  color?: "blue" | "green" | "orange" | "purple" | "red" | "yellow";
  loading?: boolean;
}

const colorMap = {
  blue: { bg: "bg-blue-50", icon: "bg-blue-100 text-blue-600", trendUp: "text-blue-600", trendDown: "text-red-500" },
  green: { bg: "bg-green-50", icon: "bg-green-100 text-green-600", trendUp: "text-green-600", trendDown: "text-red-500" },
  orange: { bg: "bg-orange-50", icon: "bg-orange-100 text-orange-600", trendUp: "text-orange-600", trendDown: "text-red-500" },
  purple: { bg: "bg-purple-50", icon: "bg-purple-100 text-purple-600", trendUp: "text-purple-600", trendDown: "text-red-500" },
  red: { bg: "bg-red-50", icon: "bg-red-100 text-red-600", trendUp: "text-green-600", trendDown: "text-red-500" },
  yellow: { bg: "bg-yellow-50", icon: "bg-yellow-100 text-yellow-600", trendUp: "text-yellow-600", trendDown: "text-red-500" },
};

export function KPICard({ label, value, subValue, icon, trend, color = "blue", loading }: KPICardProps) {
  if (loading) {
    return (
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5 animate-pulse">
        <div className="h-4 w-24 bg-gray-200 rounded mb-4" />
        <div className="h-8 w-32 bg-gray-200 rounded mb-2" />
        <div className="h-3 w-20 bg-gray-100 rounded" />
      </div>
    );
  }

  const c = colorMap[color];

  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
      <div className="flex items-start justify-between mb-4">
        {icon && (
          <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${c.icon}`}>
            {icon}
          </div>
        )}
        {trend !== undefined && (
          <span className={`text-xs font-medium ${trend >= 0 ? c.trendUp : c.trendDown}`}>
            {trend >= 0 ? "+" : ""}{trend}%
          </span>
        )}
      </div>
      <p className="text-2xl font-bold text-navy font-display">{value}</p>
      <p className="text-sm text-gray mt-1">{label}</p>
      {subValue && <p className="text-xs text-gray-l mt-1">{subValue}</p>}
    </div>
  );
}