import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Modal, Button } from "../../../../components/ui";
import { AlertTriangle } from "lucide-react";

interface QuotaExhaustedModalProps {
  open: boolean;
  onClose: () => void;
}

export function QuotaExhaustedModal({ open, onClose }: QuotaExhaustedModalProps) {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const handleGoToPacks = () => {
    onClose();
    navigate("/dashboard/packs");
  };

  return (
    <Modal open={open} onClose={onClose} title={t("student.quota.exhaustedTitle")}>
      <div className="space-y-6">
        <div className="flex justify-center">
          <div className="w-16 h-16 bg-orange/10 rounded-full flex items-center justify-center">
            <AlertTriangle className="w-8 h-8 text-orange" />
          </div>
        </div>
        <div className="text-center space-y-2">
          <p className="text-navy font-medium">{t("student.quota.exhaustedMessage")}</p>
          <p className="text-sm text-gray">{t("student.quota.exhaustedDescription")}</p>
        </div>
        <div className="bg-cream rounded-2xl p-4 space-y-2">
          <p className="text-xs font-semibold text-navy uppercase tracking-wide">{t("student.quota.unlockBenefits")}</p>
          <ul className="space-y-1.5">
            {[t("student.quota.benefit1"), t("student.quota.benefit2"), t("student.quota.benefit3")].map((b) => (
              <li key={b} className="flex items-center gap-2 text-sm text-gray-700">
                <span className="w-1.5 h-1.5 bg-orange rounded-full flex-shrink-0" />
                {b}
              </li>
            ))}
          </ul>
        </div>
        <div className="flex gap-3">
          <Button variant="ghost" size="md" onClick={onClose} className="flex-1">{t("student.quota.later")}</Button>
          <Button variant="primary" size="md" onClick={handleGoToPacks} className="flex-1">{t("student.quota.discoverPacks")}</Button>
        </div>
      </div>
    </Modal>
  );
}
