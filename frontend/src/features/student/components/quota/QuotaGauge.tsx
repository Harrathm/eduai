import { useTranslation } from "react-i18next";

interface QuotaGaugeProps {
  used: number;
  limit: number;
  percent: number;
}

export function QuotaGauge({ used, limit, percent }: QuotaGaugeProps) {
  const { t } = useTranslation();

  const barColor =
    percent >= 100 ? "bg-red-500" :
    percent >= 66 ? "bg-orange" :
    percent >= 33 ? "bg-amber-400" :
    "bg-green-500";

  const textColor =
    percent >= 100 ? "text-red-600" :
    percent >= 66 ? "text-orange" :
    "text-navy";

  return (
    <div className="bg-white rounded-2xl p-5 shadow-sm border border-black/5">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-navy">{t("student.quota.title")}</h3>
        <span className={`text-lg font-bold ${textColor}`}>{used}/{limit}</span>
      </div>
      <div className="w-full bg-gray-100 rounded-full h-3 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ease-out ${barColor}`}
          style={{ width: `${percent}%` }}
        />
      </div>
      <p className="text-xs text-gray mt-2">{t("student.quota.subtitle", { used, limit })}</p>
    </div>
  );
}
