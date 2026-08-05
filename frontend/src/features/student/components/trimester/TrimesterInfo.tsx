import { useTranslation } from "react-i18next";
import { Calendar, CheckCircle, Lock } from "lucide-react";

interface TrimesterInfoProps {
  trimesterLabel: string;
  startDate: Date;
  endDate: Date;
  isInWindow: boolean;
  alreadyReconfigured: boolean;
  packTier: string;
}

export function TrimesterInfo({ trimesterLabel, startDate, endDate, isInWindow, alreadyReconfigured, packTier }: TrimesterInfoProps) {
  const { t } = useTranslation();
  const fmt = (d: Date) => d.toLocaleDateString("fr-TN", { day: "numeric", month: "long", year: "numeric" });
  const isGolden = packTier === "golden";
  const isFree = packTier === "gratuit";

  return (
    <div className="bg-white rounded-2xl p-5 shadow-sm border border-black/5">
      <div className="flex items-center gap-3 mb-4">
        <Calendar className="w-5 h-5 text-navy" />
        <h3 className="font-semibold text-navy">{t("student.trimester.currentTrimester", { label: trimesterLabel })}</h3>
      </div>
      <div className="space-y-3">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray">{t("student.trimester.period")}</span>
          <span className="font-medium text-navy">{fmt(startDate)} — {fmt(endDate)}</span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray">{t("student.trimester.reconfigStatus")}</span>
          {isGolden ? (
            <span className="flex items-center gap-1.5 text-amber-600"><CheckCircle className="w-4 h-4" />{t("student.trimester.goldenNoNeed")}</span>
          ) : isFree ? (
            <span className="flex items-center gap-1.5 text-gray"><Lock className="w-4 h-4" />{t("student.trimester.freeNotEligible")}</span>
          ) : alreadyReconfigured ? (
            <span className="flex items-center gap-1.5 text-green-600"><CheckCircle className="w-4 h-4" />{t("student.trimester.alreadyReconfigured")}</span>
          ) : isInWindow ? (
            <span className="text-blue-600 font-medium">{t("student.trimester.windowOpen")}</span>
          ) : (
            <span className="text-gray">{t("student.trimester.windowClosed")}</span>
          )}
        </div>
      </div>
    </div>
  );
}
