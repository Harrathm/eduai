import { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { ShoppingCart, CheckCircle, BookOpen, ChevronRight, Clock, GraduationCap, Lock, Unlock } from "lucide-react";
import { getPathwayCatalog, enrollPathway } from "../../../api";
import type { PathwayCatalogItem } from "../../../api";
import { Button } from "@/components/ui";

export default function PathwayCatalogPage() {
  const { t } = useTranslation();
  const [catalog, setCatalog] = useState<PathwayCatalogItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [purchasing, setPurchasing] = useState<number | null>(null);
  const [toast, setToast] = useState({ show: false, message: "", type: "success" as "success" | "error" });

  const showToast = (message: string, type: "success" | "error" = "success") => {
    setToast({ show: true, message, type });
    setTimeout(() => setToast({ show: false, message: "", type: "success" }), 4000);
  };

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getPathwayCatalog();
      setCatalog(data);
    } catch { /* ignore */ }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const handlePurchase = async (item: PathwayCatalogItem) => {
    if (!item.pack) {
      showToast(t("student.pathway.noPackForLevel"), "error");
      return;
    }
    if (!confirm(`${t("student.pathway.buyButton", { price: item.pack.price, currency: item.pack.currency })} ?`)) return;

    setPurchasing(item.niveau.id);
    try {
      // Use existing pack purchase endpoint via centralized api client
      const { api } = await import("../../../api");
      const data = await api.post<any>(`/api/abonnements/packs/${item.pack.id}/purchase`);
      showToast(data.message || t("student.pathway.purchaseSuccess"));

      // Auto-enroll in pathway
      try {
        const enrollRes = await enrollPathway(item.niveau.id);
        showToast(t("student.pathway.pathwayEnrolled", { count: enrollRes.chapters_initialized }));
      } catch { /* enrollment is best-effort */ }

      load();
    } catch (err: any) {
      showToast(err.message || t("student.pathway.purchaseError"), "error");
    }
    setPurchasing(null);
  };

  return (
    <div className="space-y-6">
      {toast.show && (
        <div className={`fixed top-4 right-4 z-50 px-4 py-3 rounded-xl shadow-lg text-sm font-medium ${
          toast.type === "success" ? "bg-green-500 text-white" : "bg-red-500 text-white"
        }`}>{toast.message}</div>
      )}

      <div>
        <h1 className="text-3xl font-display font-light text-navy">{t("student.pathway.title").split(" ").slice(0, 1).join(" ")} <span className="italic text-orange">{t("student.pathway.title").split(" ").slice(1).join(" ")}</span></h1>
        <p className="text-gray text-sm mt-1">{t("student.pathway.subtitle")}</p>
      </div>

      {loading ? (
        <div className="text-center py-12 text-gray">{t("student.pathway.loading")}</div>
      ) : catalog.length === 0 ? (
        <div className="bg-white rounded-2xl shadow-sm border border-black/5 p-12 text-center">
          <GraduationCap className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray">{t("student.pathway.noPathways")}</p>
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2">
          {catalog.map(item => (
            <div key={item.niveau.id} className={`bg-white rounded-2xl shadow-sm border overflow-hidden transition-all ${
              item.has_access ? "border-green-200 ring-2 ring-green-100" : "border-black/5 hover:shadow-md"
            }`}>
              {/* Header */}
              <div className={`px-6 py-4 ${item.has_access ? "bg-green-50" : "bg-gradient-to-r from-orange/5 to-orange/10"}`}>
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-lg font-semibold text-navy">{item.niveau.nom}</h2>
                    <p className="text-xs text-gray mt-0.5">
                      {item.matieres.length} {t("student.pathway.subjectsCount")} • {" "}
                      {item.matieres.reduce((acc, m) => acc + m.chapters_count, 0)} {t("student.pathway.chaptersCount")}
                    </p>
                  </div>
                  {item.has_access ? (
                    <span className="flex items-center gap-1 px-3 py-1.5 bg-green-100 text-green-700 rounded-full text-xs font-medium">
                      <CheckCircle className="w-3.5 h-3.5" /> {t("student.pathway.activeAccess")}
                    </span>
                  ) : item.pack ? (
                    <div className="text-end">
                      <p className="text-xl font-bold text-orange">{item.pack.price} {item.pack.currency}</p>
                      <p className="text-xs text-gray">{item.pack.name}</p>
                    </div>
                  ) : (
                    <span className="flex items-center gap-1 px-3 py-1.5 bg-gray-100 text-gray rounded-full text-xs font-medium">
                      <Lock className="w-3.5 h-3.5" /> {t("student.pathway.noPackAvailable")}
                    </span>
                  )}
                </div>
              </div>

              {/* Matieres */}
              <div className="px-6 py-4 space-y-3">
                {item.matieres.map(m => (
                  <div key={m.id} className="flex items-center gap-3">
                    <BookOpen className="w-4 h-4 text-blue-500 flex-shrink-0" />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-navy">{m.nom}</p>
                      <p className="text-xs text-gray">{m.chapters_count} {t("student.pathway.chaptersCount")}</p>
                    </div>
                    <ChevronRight className="w-4 h-4 text-gray-300" />
                  </div>
                ))}
              </div>

              {/* Access info or purchase button */}
              <div className="px-6 py-4 border-t bg-gray-50">
                {item.has_access ? (
                  <div className="flex items-center gap-2 text-sm text-green-700">
                    <Unlock className="w-4 h-4" />
                    <span>
                      {t("student.pathway.activeAccess")}
                      {item.purchase && (
                        <span className="text-gray ms-1">
                          — {t("student.pathway.untilDate", { date: new Date(item.purchase.valid_until).toLocaleDateString("fr-FR") })}
                        </span>
                      )}
                    </span>
                  </div>
                ) : item.pack ? (
                  <Button
                    variant="primary"
                    size="lg"
                    loading={purchasing === item.niveau.id}
                    disabled={purchasing === item.niveau.id}
                    onClick={() => handlePurchase(item)}
                  >
                    {purchasing !== item.niveau.id && (
                      <>
                        <ShoppingCart className="w-4 h-4" />
                        {t("student.pathway.buyButton", { price: item.pack.price, currency: item.pack.currency })}
                      </>
                    )}
                  </Button>
                ) : (
                  <p className="text-sm text-gray text-center">{t("student.pathway.noPackAvailable")}</p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
