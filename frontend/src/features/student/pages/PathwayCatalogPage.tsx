import { useState, useEffect, useCallback } from "react";
import { ShoppingCart, CheckCircle, BookOpen, ChevronRight, Clock, GraduationCap, Lock, Unlock } from "lucide-react";
import { useAuthStore } from "../../../store/authStore";
import { getPathwayCatalog, enrollPathway } from "../../pathway/api";
import type { PathwayCatalogItem } from "../../pathway/api";

export default function PathwayCatalogPage() {
  const { user, token } = useAuthStore();
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
      showToast("Aucun pack disponible pour ce niveau", "error");
      return;
    }
    if (!confirm(`Acheter "${item.pack.name}" pour ${item.pack.price} ${item.pack.currency} ?`)) return;

    setPurchasing(item.niveau.id);
    try {
      // Use existing pack purchase endpoint
      const res = await fetch(`/api/packs/${item.pack.id}/purchase`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Erreur d'achat");

      showToast(data.message || "Pack acheté avec succès !");

      // Auto-enroll in pathway
      try {
        const enrollRes = await enrollPathway(item.niveau.id);
        showToast(`Parcours inscrit — ${enrollRes.chapters_initialized} chapitre(s) initialisé(s)`);
      } catch { /* enrollment is best-effort */ }

      load();
    } catch (err: any) {
      showToast(err.message || "Erreur d'achat", "error");
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
        <h1 className="text-3xl font-display font-light text-navy">Parcours <span className="italic text-orange">Éducatifs</span></h1>
        <p className="text-gray text-sm mt-1">Choisissez votre niveau et accédez à un parcours adaptatif complet</p>
      </div>

      {loading ? (
        <div className="text-center py-12 text-gray">Chargement des parcours...</div>
      ) : catalog.length === 0 ? (
        <div className="bg-white rounded-2xl shadow-sm border border-black/5 p-12 text-center">
          <GraduationCap className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray">Aucun parcours disponible</p>
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
                      {item.matieres.length} matière{item.matieres.length > 1 ? "s" : ""} • {" "}
                      {item.matieres.reduce((acc, m) => acc + m.chapters_count, 0)} chapitres
                    </p>
                  </div>
                  {item.has_access ? (
                    <span className="flex items-center gap-1 px-3 py-1.5 bg-green-100 text-green-700 rounded-full text-xs font-medium">
                      <CheckCircle className="w-3.5 h-3.5" /> Accès actif
                    </span>
                  ) : item.pack ? (
                    <div className="text-end">
                      <p className="text-xl font-bold text-orange">{item.pack.price} {item.pack.currency}</p>
                      <p className="text-xs text-gray">{item.pack.name}</p>
                    </div>
                  ) : (
                    <span className="flex items-center gap-1 px-3 py-1.5 bg-gray-100 text-gray rounded-full text-xs font-medium">
                      <Lock className="w-3.5 h-3.5" /> Non disponible
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
                      <p className="text-xs text-gray">{m.chapters_count} chapitre{m.chapters_count > 1 ? "s" : ""}</p>
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
                      Accès actif
                      {item.purchase && (
                        <span className="text-gray ms-1">
                          — jusqu'au {new Date(item.purchase.valid_until).toLocaleDateString("fr-FR")}
                        </span>
                      )}
                    </span>
                  </div>
                ) : item.pack ? (
                  <button
                    onClick={() => handlePurchase(item)}
                    disabled={purchasing === item.niveau.id}
                    className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-orange to-orange-l text-white rounded-xl font-medium hover:shadow-lg transition-all disabled:opacity-50"
                  >
                    {purchasing === item.niveau.id ? (
                      <span className="animate-pulse">Achat en cours...</span>
                    ) : (
                      <>
                        <ShoppingCart className="w-4 h-4" />
                        Acheter — {item.pack.price} {item.pack.currency}
                      </>
                    )}
                  </button>
                ) : (
                  <p className="text-sm text-gray text-center">Pack non disponible pour ce niveau</p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
