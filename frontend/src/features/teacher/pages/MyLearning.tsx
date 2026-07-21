import { useState, useEffect } from "react";
import { useAuthStore } from "../../../store/authStore";
import { Search, BookOpen, Clock, User } from "lucide-react";

const API_URL = "";

interface Training {
  id: number;
  title: string;
  short_description: string;
  description: string;
  category: string;
  level: string;
  niveau_scolaire: string;
  cover_url: string;
  thumbnail_url: string;
  price_tokens: number;
  price_dt: number;
  is_free: boolean;
  total_modules: number;
  total_lessons: number;
  total_duration_minutes: number;
  author_id: number;
}

interface Enrollment {
  enrollment_id: number;
  course_id: number;
  title: string;
  thumbnail_url: string;
  cover_url: string;
  progress_percent: number;
  status: string;
}

export default function MyLearning() {
  const { token } = useAuthStore();
  const [trainings, setTrainings] = useState<Training[]>([]);
  const [myEnrollments, setMyEnrollments] = useState<Enrollment[]>([]);
  const [enrolledIds, setEnrolledIds] = useState<number[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("all");

  useEffect(() => {
    fetchTrainings();
    fetchMyEnrollments();
  }, [token]);

  const fetchTrainings = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/learner/catalog`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setTrainings(data.items || []);
      }
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const fetchMyEnrollments = async () => {
    if (!token) return;
    try {
      const res = await fetch(`${API_URL}/api/learner/my-courses`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        const items = data.items || [];
        setMyEnrollments(items);
        setEnrolledIds(items.map((e: Enrollment) => e.course_id));
      }
    } catch (err) {
      console.error(err);
    }
  };

  const enroll = async (courseId: number) => {
    if (!token) return;
    try {
      const res = await fetch(`${API_URL}/api/learner/courses/${courseId}/enroll`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        fetchMyEnrollments();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const filtered = trainings.filter((t) => {
    const matches = search
      ? t.title.toLowerCase().includes(search.toLowerCase())
      : true;
    return matches && (category === "all" || t.category === category);
  });

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-3xl p-8 shadow-sm border border-black/5">
        <h1 className="text-3xl font-[300] text-navy">
          Mon <span className="italic text-orange">Apprentissage</span>
        </h1>
        <p className="text-gray mt-2">
          Inscrivez-vous aux formations disponibles
        </p>
      </div>

      {/* My Enrollments */}
      <div className="bg-gradient-to-r from-navy to-navy-m rounded-3xl p-8">
        <h2 className="text-xl font-semibold text-white mb-4">
          Mes formations inscrites
        </h2>
        {myEnrollments.length === 0 ? (
          <p className="text-white/50">Aucune inscription</p>
        ) : (
          <div className="flex gap-3 flex-wrap">
            {myEnrollments.map((e) => (
              <div
                key={e.course_id}
                className="bg-white/10 text-white px-4 py-2 rounded-xl text-sm"
              >
                {e.title}
                {e.progress_percent > 0 && (
                  <span className="ml-2 text-white/60">({e.progress_percent}%)</span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Filters */}
      <div className="bg-white rounded-3xl p-6 shadow-sm border border-black/5">
        <div className="flex flex-wrap gap-4">
          <div className="flex-1 min-w-[200px]">
            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-12 pr-4 py-3 bg-cream-m rounded-xl border border-black/5 focus:border-orange focus:outline-none"
                placeholder="Rechercher une formation..."
              />
            </div>
          </div>
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="px-4 py-3 bg-cream-m rounded-xl border border-black/5"
          >
            <option value="all">Toutes catégories</option>
            <option value="pedagogy">Pédagogie</option>
            <option value="technology">Technologie</option>
            <option value="management">Gestion</option>
          </select>
        </div>
      </div>

      {/* Training Grid */}
      <div className="grid gap-4">
        {loading ? (
          <div className="bg-white rounded-3xl p-12 text-center text-gray">
            Chargement...
          </div>
        ) : filtered.length === 0 ? (
          <div className="bg-white rounded-3xl p-12 text-center text-gray">
            Aucune formation trouvée
          </div>
        ) : (
          filtered.map((training) => (
            <div
              key={training.id}
              className="bg-white rounded-2xl p-6 shadow-sm border border-black/5 hover:shadow-md transition-shadow"
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-semibold text-navy">
                      {training.title}
                    </h3>
                    {enrolledIds.includes(training.id) && (
                      <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full">
                        Inscrit
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray mb-3">{training.short_description || training.description}</p>
                  <div className="flex items-center gap-6 text-sm text-gray">
                    <span className="flex items-center gap-1">
                      <BookOpen className="w-4 h-4" />
                      {training.total_modules} modules
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-4 h-4" />
                      {training.total_duration_minutes} min
                    </span>
                    {training.niveau_scolaire && (
                      <span className="px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded-full">
                        {training.niveau_scolaire}
                      </span>
                    )}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-lg font-semibold text-navy mb-1">
                    {training.is_free ? "Gratuit" : `${training.price_tokens} tokens`}
                  </div>
                  {!training.is_free && (
                    <div className="text-sm text-gray mb-3">
                      {training.price_dt} DT
                    </div>
                  )}
                  {enrolledIds.includes(training.id) ? (
                    <button className="px-4 py-2 bg-green-100 text-green-700 rounded-xl text-sm font-medium">
                      Commencer
                    </button>
                  ) : (
                    <button
                      onClick={() => enroll(training.id)}
                      className="px-4 py-2 bg-orange text-white rounded-xl text-sm font-medium"
                    >
                      S'inscrire
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}