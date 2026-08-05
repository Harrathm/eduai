import { useTranslation } from "react-i18next";

interface TrimesterBadgeProps {
  label: string;
  number: number;
  startDate: Date;
  endDate: Date;
}

export function TrimesterBadge({ label, startDate, endDate }: TrimesterBadgeProps) {
  const { t } = useTranslation();
  const fmt = (d: Date) => d.toLocaleDateString("fr-TN", { day: "numeric", month: "short" });
  return (
    <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-navy/10 rounded-full">
      <span className="w-2 h-2 bg-navy rounded-full" />
      <span className="text-xs font-semibold text-navy">{t("student.trimester.badge", { label })}</span>
      <span className="text-xs text-gray">{fmt(startDate)} — {fmt(endDate)}</span>
    </div>
  );
}
