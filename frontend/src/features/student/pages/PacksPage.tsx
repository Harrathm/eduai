import { useState, useEffect } from "react";
import { useAuthStore } from "../../../store/authStore";
import { api } from "../../../utils/apiClient";

interface Pack {
  id: number;
  name: string;
  description: string | null;
  niveau_scolaire: string;
  matieres: string[] | null;
  price: number;
  currency: string;
  validity_duration_days: number;
  owner_type: string;
  already_included_by_school: boolean;
}

function PackSkeleton() {
  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5 animate-pulse">
      <div className="h-5 w-48 bg-gray-200 rounded mb-3" />
      <div className="h-4 w-32 bg-gray-100 rounded mb-4" />
      <div className="h-16 bg-gray-50 rounded mb-4" />
      <div className="flex justify-between items-center">
        <div className="h-8 w-20 bg-gray-200 rounded" />
        <div className="h-8 w-24 bg-gray-100 rounded" />
      </div>
    </div>
  );
}

function PackCard({ pack, userNiveau }: { pack: Pack; userNiveau?: string }) {
  const isMatchingLevel = !userNiveau || pack.niveau_scolaire === userNiveau;

  return (
    <div
      className={`bg-white rounded-2xl p-6 shadow-sm border transition-all ${
        pack.already_included_by_school
          ? "border-green-200 bg-green-50/30"
          : isMatchingLevel
          ? "border-orange/30 hover:shadow-md"
          : "border-black/5 opacity-60"
      }`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="font-semibold text-navy">{pack.name}</h3>
          <p className="text-xs text-gray-400 mt-1">{pack.niveau_scolaire}</p>
        </div>
        {pack.already_included_by_school && (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">
            Inclus via école
          </span>
        )}
      </div>

      {/* Description */}
      {pack.description && (
        <p className="text-sm text-gray-600 mb-4 line-clamp-2">{pack.description}</p>
      )}

      {/* Matieres */}
      {pack.matieres && pack.matieres.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-4">
          {pack.matieres.map((m) => (
            <span key={m} className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full">
              {m}
            </span>
          ))}
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between pt-3 border-t border-gray-100">
        <div>
          <span className="text-2xl font-[300] text-navy">{pack.price}</span>
          <span className="text-sm text-gray-400 ml-1">{pack.currency}</span>
          <p className="text-xs text-gray-400">
            {pack.validity_duration_days} jours de validité
          </p>
        </div>

        {pack.already_included_by_school ? (
          <div className="px-4 py-2 bg-green-100 text-green-700 text-sm font-medium rounded-xl">
            Déjà actif
          </div>
        ) : (
          <button
            className={`px-4 py-2 text-sm font-medium rounded-xl transition-colors ${
              isMatchingLevel
                ? "bg-navy text-white hover:bg-navy/90"
                : "bg-gray-100 text-gray-400 cursor-not-allowed"
            }`}
            disabled={!isMatchingLevel}
          >
            {isMatchingLevel ? "Acheter" : "Niveau incompatible"}
          </button>
        )}
      </div>
    </div>
  );
}

export default function PacksPage() {
  const { user } = useAuthStore();
  const [packs, setPacks] = useState<Pack[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>("");

  const userNiveau = user?.niveau_scolaire || undefined;

  useEffect(() => {
    async function fetchPacks() {
      try {
        const params = new URLSearchParams();
        if (filter) params.set("niveau_scolaire", filter);
        const url = `/api/packs${params.toString() ? `?${params}` : ""}`;
        const data = await api.get(url);
        setPacks(data.items || []);
      } catch (err: any) {
        setError(err.message || "Erreur de chargement");
      } finally {
        setLoading(false);
      }
    }
    fetchPacks();
  }, [filter]);

  const niveaux = [
    "1ère année", "2ème année", "3ème année", "4ème année", "5ème année", "6ème année",
    "7ème de base", "8ème de base", "9ème de base",
    "1ère année secondaire",
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-navy rounded-3xl p-8">
        <h1 className="text-3xl font-[300] text-white">
          Packs d'<span className="italic text-orange-l">Étude</span>
        </h1>
        <p className="text-white/50 mt-2">
          Accédez à tous les cours de votre niveau avec un pack
        </p>
      </div>

      {/* Filter */}
      <div className="bg-white rounded-2xl p-4 shadow-sm border border-black/5">
        <div className="flex items-center gap-3 flex-wrap">
          <span className="text-sm text-gray-500 font-medium">Niveau :</span>
          <button
            onClick={() => setFilter("")}
            className={`px-3 py-1.5 text-xs rounded-full transition-colors ${
              !filter ? "bg-navy text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}
          >
            Tous
          </button>
          {niveaux.map((n) => (
            <button
              key={n}
              onClick={() => setFilter(n)}
              className={`px-3 py-1.5 text-xs rounded-full transition-colors ${
                filter === n ? "bg-navy text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              {n}
            </button>
          ))}
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-2xl p-4 text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Packs Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <PackSkeleton key={i} />
          ))}
        </div>
      ) : packs.length === 0 ? (
        <div className="bg-white rounded-2xl p-12 shadow-sm border border-black/5 text-center">
          <div className="text-4xl mb-4">📦</div>
          <h3 className="text-lg font-medium text-navy mb-2">Aucun pack disponible</h3>
          <p className="text-sm text-gray-500">
            {filter
              ? `Aucun pack pour le niveau "${filter}"`
              : "Aucun pack n'a été publié pour le moment"}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {packs.map((pack) => (
            <PackCard key={pack.id} pack={pack} userNiveau={userNiveau} />
          ))}
        </div>
      )}
    </div>
  );
}
