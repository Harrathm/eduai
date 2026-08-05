import { useTranslation } from "react-i18next";
import { Button } from "../../../../components/ui";
import { RefreshCw, Clock } from "lucide-react";

interface TrimesterReconfigBannerProps {
  canReconfigure: boolean;
  daysRemaining: number;
  trimesterLabel: string;
  onReconfigure: () => void;
}

export function TrimesterReconfigBanner({ canReconfigure, daysRemaining, trimesterLabel, onReconfigure }: TrimesterReconfigBannerProps) {
  const { t } = useTranslation();
  if (!canReconfigure) return null;
  return (
    <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-2xl p-5">
      <div className="flex items-start gap-4">
        <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center flex-shrink-0">
          <RefreshCw className="w-5 h-5 text-blue-600" />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-blue-900 text-sm">{t("student.trimester.newTrimester", { trimester: trimesterLabel })}</h3>
          <p className="text-sm text-blue-700 mt-1">{t("student.trimester.reconfigDescription")}</p>
          <div className="flex items-center gap-1.5 mt-2">
            <Clock className="w-3.5 h-3.5 text-blue-500" />
            <span className="text-xs text-blue-600">{t("student.trimester.daysRemaining", { count: daysRemaining })}</span>
          </div>
        </div>
        <Button variant="secondary" size="sm" onClick={onReconfigure} className="flex-shrink-0">
          <RefreshCw className="w-3.5 h-3.5" />
          {t("student.trimester.reconfigure")}
        </Button>
      </div>
    </div>
  );
}
