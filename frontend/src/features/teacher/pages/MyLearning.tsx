import { useState, useEffect } from "react";
import { useTranslation } from 'react-i18next';
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../../../store/authStore";
import { Search, BookOpen, Clock, User } from "lucide-react";
import { teacherMyCoursesApi } from "../../../api";

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

export default function MyLearning() {
  const { t } = useTranslation();
  const { token } = useAuthStore();
  const navigate = useNavigate();
  const [myCourses, setMyCourses] = useState<Training[]>([]);
  const [catalog, setCatalog] = useState<Training[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("all");

  useEffect(() => {
    fetchMyCourses();
    fetchCatalog();
  }, [token]);

  const fetchMyCourses = async () => {
    if (!token) return;
    try {
      const data = await teacherMyCoursesApi.listMyCourses();
      setMyCourses(Array.isArray(data) ? data : (data as any).items || data || []);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchCatalog = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const data = await teacherMyCoursesApi.listCatalog();
      setCatalog(Array.isArray(data) ? data : (data as any).items || data || []);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const filtered = catalog.filter((t) => {
    const matches = search
      ? t.title.toLowerCase().includes(search.toLowerCase())
      : true;
    return matches && (category === "all" || t.category === category);
  });

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-3xl p-8 shadow-sm border border-black/5">
        <h1 className="text-3xl font-[300] text-navy">
          {t('teacher.learning.title')} <span className="italic text-orange">{t('teacher.learning.titleSuffix')}</span>
        </h1>
        <p className="text-gray mt-2">
          {t('teacher.learning.description')}
        </p>
      </div>

      {/* My Courses (Teacher's own) */}
      <div className="bg-gradient-to-r from-navy to-navy-m rounded-3xl p-8">
          <h2 className="text-xl font-semibold text-white mb-4">
            {t('teacher.learning.myCourses')}
          </h2>
        {myCourses.length === 0 ? (
          <p className="text-white/50">{t('teacher.learning.noCoursesYet')}</p>
        ) : (
          <div className="flex gap-3 flex-wrap">
            {myCourses.map((c) => (
              <div
                key={c.id}
                className="bg-white/10 text-white px-4 py-2 rounded-xl text-sm"
              >
                {c.title}
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
                className="w-full ps-12 pe-4 py-3 bg-cream-m rounded-xl border border-black/5 focus:border-orange focus:outline-none"
                placeholder={t('teacher.learning.searchPlaceholder')}
              />
            </div>
          </div>
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="px-4 py-3 bg-cream-m rounded-xl border border-black/5"
          >
            <option value="all">{t('teacher.learning.allCategories')}</option>
            <option value="pedagogy">{t('teacher.learning.pedagogy')}</option>
            <option value="technology">{t('teacher.learning.technology')}</option>
            <option value="management">{t('teacher.learning.management')}</option>
          </select>
        </div>
      </div>

      {/* Catalog Grid */}
      <div className="grid gap-4">
        {loading ? (
          <div className="bg-white rounded-3xl p-12 text-center text-gray">
            {t('teacher.learning.loading')}
          </div>
        ) : filtered.length === 0 ? (
          <div className="bg-white rounded-3xl p-12 text-center text-gray">
            {t('teacher.learning.noTrainingsFound')}
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
                  </div>
                  <p className="text-sm text-gray mb-3">{training.short_description || training.description}</p>
                  <div className="flex items-center gap-6 text-sm text-gray">
                    <span className="flex items-center gap-1">
                      <BookOpen className="w-4 h-4" />
                      {training.total_modules} {t('teacher.learning.modules')}
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-4 h-4" />
                      {training.total_duration_minutes} {t('teacher.learning.min')}
                    </span>
                    {training.niveau_scolaire && (
                      <span className="px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded-full">
                        {training.niveau_scolaire}
                      </span>
                    )}
                  </div>
                </div>
                <div className="text-end">
                  <div className="text-lg font-semibold text-navy mb-1">
                    {training.is_free ? t('teacher.learning.free') : `${training.price_tokens} ${t('teacher.learning.tokens')}`}
                  </div>
                  {!training.is_free && (
                    <div className="text-sm text-gray mb-3">
                      {training.price_dt} {t('teacher.learning.dt')}
                    </div>
                  )}
                  <button
                    onClick={() => navigate(`/dashboard/courses/${training.id}`)}
                    className="px-4 py-2 bg-orange text-white rounded-xl text-sm font-medium"
                  >
                    {t('teacher.learning.viewCourse')}
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
