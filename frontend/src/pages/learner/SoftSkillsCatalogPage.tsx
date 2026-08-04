import { useState, useEffect } from "react";
import { useAuthStore } from "../../store/authStore";
import { Link } from "react-router-dom";
import { Sparkles, Search, Filter, BookOpen } from "lucide-react";

interface Formation {
  id: number;
  name: string;
  description: string | null;
  category: string;
  niveau_scolaire: string;
  price: number;
  currency: string;
  is_free: boolean;
}

export default function SoftSkillsCatalogPage() {
  const { token, user } = useAuthStore();
  const [formations, setFormations] = useState<Formation[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<string>("");

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await fetch("/catalog/courses?category=soft_skills", {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (res.ok) {
        const data = await res.json();
        setFormations(data.items || data.courses || []);
      }
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const filtered = formations.filter((f) => {
    if (search && !f.name.toLowerCase().includes(search.toLowerCase())) return false;
    if (filter && f.category !== filter) return false;
    return true;
  });

  const categories = [...new Set(formations.map((f) => f.category).filter(Boolean))];

  return (
    <div className="space-y-6">
      <div className="bg-gradient-to-br from-purple-600 to-navy-700 rounded-3xl p-8">
        <div className="flex items-center gap-3 mb-2">
          <Sparkles className="w-8 h-8 text-white/80" />
          <h1 className="text-3xl font-[300] text-white">
            Formations <span className="italic text-purple-200">Soft Skills</span>
          </h1>
        </div>
        <p className="text-white/60 mt-2">
          Developpez vos competences transversales — accessible a tous les profils
        </p>
      </div>

      {/* Access info */}
      <div className="bg-white rounded-2xl p-5 shadow-sm border border-black/5">
        <div className="flex items-start gap-3">
          <BookOpen className="w-5 h-5 text-purple-500 mt-0.5" />
          <div className="text-sm text-gray-600">
            <p className="font-medium text-navy">Conditions d'acces</p>
            <ul className="mt-1 space-y-1 list-disc list-inside text-xs text-gray-500">
              <li><span className="font-medium">Gratuites</span> : inscription directe, acces immediat</li>
              <li><span className="font-medium">Incluses (Pack Golden)</span> : acces automatique avec votre abonnement</li>
              <li><span className="font-medium">Payantes a l'unite</span> : achat individuel pour acceder a la formation</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Search */}
      <div className="bg-white rounded-2xl p-4 shadow-sm border border-black/5">
        <div className="flex items-center gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Rechercher une formation..."
              className="w-full ps-10 pe-4 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-purple/30"
            />
          </div>
          {categories.length > 0 && (
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-gray-400" />
              <button
                onClick={() => setFilter("")}
                className={`px-3 py-1.5 text-xs rounded-full ${!filter ? "bg-purple-600 text-white" : "bg-gray-100 text-gray-600"}`}
              >
                Tous
              </button>
              {categories.map((cat) => (
                <button
                  key={cat}
                  onClick={() => setFilter(cat)}
                  className={`px-3 py-1.5 text-xs rounded-full capitalize ${filter === cat ? "bg-purple-600 text-white" : "bg-gray-100 text-gray-600"}`}
                >
                  {cat.replace(/_/g, " ")}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Formations */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-white rounded-2xl p-6 shadow-sm border border-black/5 animate-pulse">
              <div className="h-5 w-48 bg-gray-200 rounded mb-3" />
              <div className="h-4 w-32 bg-gray-100 rounded mb-4" />
              <div className="h-16 bg-gray-50 rounded" />
            </div>
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="bg-white rounded-2xl p-12 shadow-sm border border-black/5 text-center">
          <Sparkles className="w-12 h-12 text-purple-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-navy mb-2">Aucune formation disponible</h3>
          <p className="text-sm text-gray-500">
            Les formations Soft Skills seront bientot disponibles.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((f) => (
            <div key={f.id} className="bg-white rounded-2xl p-6 shadow-sm border border-black/5 hover:shadow-md transition-all">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="font-semibold text-navy">{f.name}</h3>
                  <p className="text-xs text-purple-500 capitalize mt-1">{f.category?.replace(/_/g, " ")}</p>
                </div>
                {f.is_free || f.price === 0 ? (
                  <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs font-medium rounded-full">Gratuit</span>
                ) : (
                  <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs font-medium rounded-full">{f.price} {f.currency}</span>
                )}
              </div>
              {f.description && (
                <p className="text-sm text-gray-600 mb-4 line-clamp-3">{f.description}</p>
              )}
              <div className="pt-3 border-t border-gray-100 flex items-center justify-between">
                <span className="text-xs text-gray-400">{f.niveau_scolaire || "Tous niveaux"}</span>
                <Link
                  to={`/dashboard/courses/${f.id}`}
                  className="px-3 py-1.5 bg-purple-600 text-white text-xs font-medium rounded-xl hover:bg-purple-700"
                >
                  {f.is_free || f.price === 0 ? "Commencer" : "Voir"}
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
