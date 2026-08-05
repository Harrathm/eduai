import { Fragment, useState, useCallback, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { Modal, Button } from "../../../../components/ui";
import { MatiereSelector } from "./MatiereSelector";
import { CheckCircle, ArrowLeft, Loader2 } from "lucide-react";
import { api } from "../../../../utils/apiClient";

interface Pack {
  id: number;
  tier: string;
  name: string;
  prix_tnd: number;
  niveau_scolaire: string;
}

interface Matiere {
  id: number;
  name: string;
  category: "langue" | "specialite";
  niveau_scolaire: string;
}

interface PackConfiguratorModalProps {
  isOpen: boolean;
  onClose: () => void;
  pack: Pack;
  userNiveau: string | null;
}

const TIER_LABELS: Record<string, string> = { basique: "Basique", silver: "Silver", golden: "Golden" };
const TIER_DESC: Record<string, string> = {
  basique: "1 Matiere de Langue + 1 Matiere de Specialite",
  silver: "2 Matieres de Langues + 2 Matieres de Specialites",
  golden: "Acces illimite a toutes les matieres + Soft Skills",
};

export function PackConfiguratorModal({ isOpen, onClose, pack, userNiveau }: PackConfiguratorModalProps) {
  const { t } = useTranslation();
  const [step, setStep] = useState<"matieres" | "confirm" | "success">("matieres");
  const [selectedMatieres, setSelectedMatieres] = useState<number[]>([]);
  const [availableMatieres, setAvailableMatieres] = useState<Matiere[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isGolden = pack.tier === "golden";
  const maxLangues = pack.tier === "silver" ? 2 : 1;
  const maxSpecialites = pack.tier === "silver" ? 2 : 1;

  const langues = useMemo(() => availableMatieres.filter((m) => m.category === "langue"), [availableMatieres]);
  const specialites = useMemo(() => availableMatieres.filter((m) => m.category === "specialite"), [availableMatieres]);
  const selLangues = selectedMatieres.filter((id) => langues.some((l) => l.id === id)).length;
  const selSpec = selectedMatieres.filter((id) => specialites.some((s) => s.id === id)).length;

  const canConfirm = isGolden || (selLangues === maxLangues && selSpec === maxSpecialites);

  const loadMatieres = useCallback(async () => {
    try {
      setLoading(true);
      const data = await api.get<Matiere[]>(`/api/pathway/matieres?niveau_scolaire=${encodeURIComponent(pack.niveau_scolaire)}`);
      setAvailableMatieres(Array.isArray(data) ? data : []);
    } catch { /* ignore */ } finally { setLoading(false); }
  }, [pack.niveau_scolaire]);

  const handleOpen = useCallback(async () => {
    if (isGolden) { setStep("confirm"); return; }
    await loadMatieres();
    setStep("matieres");
  }, [isGolden, loadMatieres]);

  const handleConfirm = async () => {
    setLoading(true);
    setError(null);
    try {
      await api.post(`/api/abonnements/packs/${pack.id}/purchase`, { matieres: isGolden ? undefined : selectedMatieres });
      setStep("success");
    } catch (err: any) {
      setError(err.message || t("packConfig.purchaseError"));
    } finally { setLoading(false); }
  };

  const handleClose = () => { setStep("matieres"); setSelectedMatieres([]); setError(null); onClose(); };

  if (!isOpen) return null;

  return (
    <Modal open={isOpen} onClose={handleClose} title={t("packConfig.title")}>
      <div className="space-y-6">
        {/* Step indicator */}
        {!isGolden && (
          <div className="flex items-center gap-2">
            {["Matieres", "Confirmation"].map((label, i) => {
              const idx = step === "matieres" ? 0 : 1;
              return (
                <Fragment key={label}>
                  <div className="flex items-center gap-2">
                    <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${i < idx ? "bg-green-500 text-white" : i === idx ? "bg-navy text-white" : "bg-gray-200 text-gray-500"}`}>
                      {i < idx ? "✓" : i + 1}
                    </div>
                    <span className={`text-xs font-medium ${i === idx ? "text-navy" : "text-gray-400"}`}>{label}</span>
                  </div>
                  {i < 1 && <div className={`flex-1 h-0.5 ${i < idx ? "bg-green-500" : "bg-gray-200"}`} />}
                </Fragment>
              );
            })}
          </div>
        )}

        {error && <div className="bg-red-50 border border-red-200 rounded-xl p-3 text-sm text-red-700">{error}</div>}

        {/* Pack info */}
        <div className="bg-navy/5 rounded-2xl p-6">
          <h3 className="font-semibold text-navy text-lg">{TIER_LABELS[pack.tier]} — {pack.name}</h3>
          <p className="text-sm text-gray-600 mt-1">{TIER_DESC[pack.tier]}</p>
          <p className="text-2xl font-[300] text-navy mt-3">{pack.prix_tnd} <span className="text-sm text-gray-400">TND</span></p>
        </div>

        {/* Step: matieres */}
        {step === "matieres" && !isGolden && (
          <div className="space-y-4">
            <div className="flex gap-3 text-xs">
              <span className="px-2 py-1 bg-blue-50 text-blue-700 rounded-full">Langues: {selLangues}/{maxLangues}</span>
              <span className="px-2 py-1 bg-purple-50 text-purple-700 rounded-full">Specialites: {selSpec}/{maxSpecialites}</span>
            </div>
            {loading ? (
              <div className="text-center py-8 text-gray text-sm">Chargement des matieres...</div>
            ) : (
              <MatiereSelector matieres={availableMatieres} selectedIds={selectedMatieres} onToggle={(id) => setSelectedMatieres((p) => p.includes(id) ? p.filter((x) => x !== id) : (p.length < maxLangues + maxSpecialites ? [...p, id] : p))} maxLangues={maxLangues} maxSpecialites={maxSpecialites} />
            )}
          </div>
        )}

        {/* Step: confirm */}
        {step === "confirm" && (
          <div className="space-y-4">
            <div className="bg-green-50 border border-green-200 rounded-2xl p-6">
              <div className="flex items-center gap-3 mb-3">
                <CheckCircle className="w-6 h-6 text-green-600" />
                <h3 className="font-semibold text-green-800">{t("packConfig.confirmTitle")}</h3>
              </div>
              <div className="space-y-2 text-sm text-green-700">
                <p><span className="font-medium">{t("packConfig.pack")}:</span> {TIER_LABELS[pack.tier]}</p>
                {!isGolden && <p><span className="font-medium">{t("packConfig.matieres")}:</span> {selectedMatieres.length} selectionnees</p>}
                <p><span className="font-medium">{t("packConfig.price")}:</span> {pack.prix_tnd} TND</p>
              </div>
            </div>
            <p className="text-xs text-gray-500">{t("packConfig.confirmDisclaimer")}</p>
          </div>
        )}

        {/* Step: success */}
        {step === "success" && (
          <div className="text-center py-8 space-y-4">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto"><CheckCircle className="w-8 h-8 text-green-600" /></div>
            <h3 className="text-lg font-semibold text-navy">{t("packConfig.successTitle")}</h3>
            <p className="text-sm text-gray-600">{t("packConfig.successDesc")}</p>
            <Button onClick={handleClose} variant="primary">{t("packConfig.goToDashboard")}</Button>
          </div>
        )}

        {/* Actions */}
        {step !== "success" && (
          <div className="flex items-center justify-between pt-4 border-t border-gray-100">
            {step !== "matieres" && isGolden ? <div /> : step === "confirm" ? (
              <Button onClick={() => setStep("matieres")} variant="secondary" className="flex items-center gap-2"><ArrowLeft className="w-4 h-4" />{t("common.back")}</Button>
            ) : <div />}
            <Button
              onClick={step === "confirm" ? handleConfirm : () => { if (isGolden) setStep("confirm"); else setStep("confirm"); }}
              disabled={step === "matieres" && !canConfirm || loading}
              variant="primary"
              className="flex items-center gap-2"
            >
              {loading && <Loader2 className="w-4 h-4 animate-spin" />}
              {step === "confirm" ? t("packConfig.confirmPurchase") : t("common.next")}
            </Button>
          </div>
        )}
      </div>
    </Modal>
  );
}
