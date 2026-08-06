import { Fragment, useState, useCallback, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Modal, Button } from "../../../../components/ui";
import { CheckCircle, ArrowLeft, Loader2 } from "lucide-react";
import { api } from "../../../../utils/apiClient";

interface Pack {
  id: number;
  tier: string;
  name: string;
  prix_tnd: number;
  niveau_scolaire: string;
}

interface MatiereOption {
  id: number;
  nom: string;
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
  const [langues, setLangues] = useState<MatiereOption[]>([]);
  const [specialites, setSpecialites] = useState<MatiereOption[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isGolden = pack.tier === "golden";
  const isSilver = pack.tier === "silver";
  const maxLangues = isSilver ? 2 : 1;
  const maxSpecialites = isSilver ? 2 : 1;

  const [selLangue1, setSelLangue1] = useState<number>(0);
  const [selLangue2, setSelLangue2] = useState<number>(0);
  const [selSpec1, setSelSpec1] = useState<number>(0);
  const [selSpec2, setSelSpec2] = useState<number>(0);

  const resetState = () => {
    setStep("matieres");
    setSelLangue1(0);
    setSelLangue2(0);
    setSelSpec1(0);
    setSelSpec2(0);
    setError(null);
    setLangues([]);
    setSpecialites([]);
  };

  const handleClose = () => { resetState(); onClose(); };

  useEffect(() => {
    if (!isOpen) return;
    resetState();
    if (isGolden) {
      setStep("confirm");
      return;
    }
    loadMatieres();
  }, [isOpen]);

  const loadMatieres = useCallback(async () => {
    try {
      setLoading(true);
      const resp = await api.get<{ langues: MatiereOption[]; specialites: MatiereOption[] }>(
        `/api/pathway/matieres-by-niveau?niveau_scolaire=${encodeURIComponent(pack.niveau_scolaire)}`
      );
      setLangues(resp.langues || []);
      setSpecialites(resp.specialites || []);
    } catch { setError("Erreur lors du chargement des matieres."); } finally { setLoading(false); }
  }, [pack.niveau_scolaire]);

  const getSelectedIds = (): number[] => {
    const ids: number[] = [];
    if (selLangue1) ids.push(selLangue1);
    if (maxLangues >= 2 && selLangue2) ids.push(selLangue2);
    if (selSpec1) ids.push(selSpec1);
    if (maxSpecialites >= 2 && selSpec2) ids.push(selSpec2);
    return ids;
  };

  const allSelected = (): boolean => {
    if (isGolden) return true;
    if (!selLangue1 || !selSpec1) return false;
    if (maxLangues >= 2 && !selLangue2) return false;
    if (maxSpecialites >= 2 && !selSpec2) return false;
    const ids = getSelectedIds();
    return ids.length === new Set(ids).size;
  };

  const handleConfirm = async () => {
    setLoading(true);
    setError(null);
    try {
      const matieres = isGolden ? undefined : getSelectedIds();
      await api.post(`/api/abonnements/packs/${pack.id}/purchase`, { matieres });
      setStep("success");
    } catch (err: any) {
      setError(err.message || t("packConfig.purchaseError"));
    } finally { setLoading(false); }
  };

  const renderSelect = (
    label: string,
    value: number,
    onChange: (v: number) => void,
    options: MatiereOption[],
    disabledIds: number[]
  ) => (
    <div>
      <label className="block text-xs font-medium text-gray-600 mb-1">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full px-3 py-2.5 rounded-xl border border-gray-200 text-sm text-navy bg-white focus:outline-none focus:ring-2 focus:ring-navy/30 focus:border-navy transition-colors"
      >
        <option value={0}>-- Choisir --</option>
        {options.map((m) => (
          <option key={m.id} value={m.id} disabled={disabledIds.includes(m.id)}>
            {m.nom}
          </option>
        ))}
      </select>
    </div>
  );

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
                      {i < idx ? "\u2713" : i + 1}
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

        {/* Step: matieres — dropdowns */}
        {step === "matieres" && !isGolden && (
          <div className="space-y-5">
            {loading ? (
              <div className="text-center py-8 text-gray text-sm">Chargement des matieres...</div>
            ) : (
              <>
                {/* Langues */}
                <div>
                  <h4 className="text-sm font-semibold text-navy mb-3">Langues</h4>
                  <div className="space-y-3">
                    {renderSelect(
                      "Choisissez 1 Langue",
                      selLangue1,
                      setSelLangue1,
                      langues,
                      selLangue2 ? [selLangue2] : []
                    )}
                    {isSilver && renderSelect(
                      "Choisissez Langue 2",
                      selLangue2,
                      setSelLangue2,
                      langues,
                      selLangue1 ? [selLangue1] : []
                    )}
                  </div>
                </div>

                {/* Specialites */}
                <div>
                  <h4 className="text-sm font-semibold text-navy mb-3">Specialites</h4>
                  <div className="space-y-3">
                    {renderSelect(
                      "Choisissez 1 Specialite",
                      selSpec1,
                      setSelSpec1,
                      specialites,
                      selSpec2 ? [selSpec2] : []
                    )}
                    {isSilver && renderSelect(
                      "Choisissez Specialite 2",
                      selSpec2,
                      setSelSpec2,
                      specialites,
                      selSpec1 ? [selSpec1] : []
                    )}
                  </div>
                </div>
              </>
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
                {!isGolden && <p><span className="font-medium">{t("packConfig.matieres")}:</span> {getSelectedIds().length} selectionnees</p>}
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
            {step === "confirm" && !isGolden ? (
              <Button onClick={() => setStep("matieres")} variant="secondary" className="flex items-center gap-2"><ArrowLeft className="w-4 h-4" />{t("common.back")}</Button>
            ) : <div />}
            <Button
              onClick={step === "confirm" ? handleConfirm : () => setStep("confirm")}
              disabled={(step === "matieres" && !allSelected()) || loading}
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
