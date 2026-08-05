import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { Check } from "lucide-react";

interface Matiere {
  id: number;
  name: string;
  category: "langue" | "specialite";
  niveau_scolaire: string;
}

interface MatiereSelectorProps {
  matieres: Matiere[];
  selectedIds: number[];
  onToggle: (id: number) => void;
  maxLangues: number;
  maxSpecialites: number;
}

export function MatiereSelector({ matieres, selectedIds, onToggle, maxLangues, maxSpecialites }: MatiereSelectorProps) {
  const { t } = useTranslation();
  const langues = useMemo(() => matieres.filter((m) => m.category === "langue"), [matieres]);
  const specialites = useMemo(() => matieres.filter((m) => m.category === "specialite"), [matieres]);
  const selLangues = selectedIds.filter((id) => langues.some((l) => l.id === id)).length;
  const selSpec = selectedIds.filter((id) => specialites.some((s) => s.id === id)).length;

  const renderSection = (title: string, items: Matiere[], selCount: number, maxCount: number, cat: "langue" | "specialite") => (
    <div>
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-sm font-semibold text-navy">{title}</h4>
        <span className={`text-xs px-2 py-0.5 rounded-full ${selCount === maxCount ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-600"}`}>{selCount}/{maxCount}</span>
      </div>
      <div className="grid grid-cols-2 gap-2">
        {items.map((m) => {
          const isSel = selectedIds.includes(m.id);
          const isDis = !isSel && ((cat === "langue" && selLangues >= maxLangues) || (cat === "specialite" && selSpec >= maxSpecialites));
          return (
            <button key={m.id} onClick={() => onToggle(m.id)} disabled={isDis}
              className={`flex items-center gap-2 p-3 rounded-xl border-2 text-left text-sm transition-all ${isSel ? "border-navy bg-navy/5 text-navy font-medium" : isDis ? "border-gray-100 bg-gray-50 text-gray-400 cursor-not-allowed" : "border-gray-200 hover:border-navy/30 text-gray-700"}`}>
              <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0 ${isSel ? "border-navy bg-navy" : "border-gray-300"}`}>
                {isSel && <Check className="w-3 h-3 text-white" />}
              </div>
              <span className="truncate">{m.name}</span>
            </button>
          );
        })}
      </div>
    </div>
  );

  return (
    <div className="space-y-5">
      {maxLangues > 0 && renderSection(t("packConfig.langues"), langues, selLangues, maxLangues, "langue")}
      {maxSpecialites > 0 && renderSection(t("packConfig.specialites"), specialites, selSpec, maxSpecialites, "specialite")}
    </div>
  );
}
