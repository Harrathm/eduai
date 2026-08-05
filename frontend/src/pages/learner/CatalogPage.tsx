// Learner Course Catalog Page
import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { catalogApi, type CatalogCourse, enrollmentApi } from "../../api";
const catalogAPI = catalogApi;
const enrollmentAPI = enrollmentApi;
import { Search, BookOpen, Clock, Users, Award, ChevronRight } from "lucide-react";

const LEVELS = { beginner: "Débutant", intermediate: "Intermédiaire", advanced: "Avancé" };

export default function CatalogPage() {
  const navigate = useNavigate();
  const [courses, setCourses] = useState<CatalogCourse[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [myCourses, setMyCourses] = useState<Set<number>>(new Set());
  const [filters, setFilters] = useState({ search: "", category: "", level: "" });

  useEffect(() => {
    loadCourses();
    loadCategories();
    loadMyCourses();
  }, []);

  const loadCourses = async () => {
    setLoading(true);
    try {
      const data = await catalogAPI.list(filters);
      setCourses(Array.isArray(data) ? data : (data.items || []));
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  const loadCategories = async () => {
    try {
      const data = await catalogAPI.categories();
      setCategories(Array.isArray(data) ? data : []);
    } catch (err) { console.error(err); }
  };

  const loadMyCourses = async () => {
    try {
      const data = await enrollmentAPI.myCourses();
      setMyCourses(new Set((data || []).map((c: any) => c.course_id)));
    } catch (err) { /* Not logged in */ }
  };

  const handleEnroll = async (e: React.MouseEvent, courseId: number) => {
    e.preventDefault();
    e.stopPropagation();
    try {
      await enrollmentAPI.enroll(courseId);
      setMyCourses(prev => new Set([...prev, courseId]));
    } catch (err: any) {
      alert(err.message || "Erreur d'inscription");
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero */}
      <div className="bg-gradient-to-r from-navy-600 to-purple-700 text-white py-12">
        <div className="container mx-auto px-4">
          <h1 className="text-3xl font-bold mb-2">Catalogue des formations</h1>
          <p className="text-navy-100 mb-6">Découvrez nos cours et commencez à apprendre</p>
          <form onSubmit={(e) => { e.preventDefault(); loadCourses(); }} className="flex gap-2 max-w-xl">
            <input type="text" placeholder="Rechercher un cours..." value={filters.search}
              onChange={e => setFilters({ ...filters, search: e.target.value })}
              className="flex-1 px-4 py-3 rounded-lg text-gray-900" />
            <button type="submit" className="px-6 py-3 bg-orange-500 rounded-lg font-medium hover:bg-orange-600">
              <Search className="w-5 h-5" />
            </button>
          </form>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white border-b shadow-sm">
        <div className="container mx-auto px-4 py-3">
          <div className="flex flex-wrap gap-3">
            <select value={filters.category} onChange={e => { setFilters({ ...filters, category: e.target.value }); loadCourses(); }}
              className="px-4 py-2 border rounded-lg">
              <option value="">Toutes catégories</option>
              {categories.map(cat => <option key={cat} value={cat}>{cat}</option>)}
            </select>
            <select value={filters.level} onChange={e => { setFilters({ ...filters, level: e.target.value }); loadCourses(); }}
              className="px-4 py-2 border rounded-lg">
              <option value="">Tous niveaux</option>
              {Object.entries(LEVELS).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
            </select>
            <button onClick={() => { setFilters({ search: "", category: "", level: "" }); loadCourses(); }}
              className="px-3 py-2 text-sm text-gray-500 hover:text-gray-700">Réinitialiser</button>
          </div>
        </div>
      </div>

      {/* Course Grid */}
      <div className="container mx-auto px-4 py-8">
        {loading ? (
          <div className="text-center py-16">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-navy-600 mx-auto"></div>
            <p className="mt-4 text-gray-500">Chargement...</p>
          </div>
        ) : courses.length === 0 ? (
          <div className="text-center py-16">
            <BookOpen className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <p className="text-gray-500 mb-4">Aucun cours trouvé</p>
            <button onClick={() => { setFilters({ search: "", category: "", level: "" }); loadCourses(); }}
              className="px-4 py-2 bg-navy-600 text-white rounded-lg">Voir tous les cours</button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {courses.map(course => {
              const isEnrolled = myCourses.has(course.id);
              return (
                <div key={course.id} className="bg-white rounded-xl border overflow-hidden hover:shadow-lg transition-all group">
                  <div className="aspect-video bg-gray-100 relative">
                    {course.cover_url
                      ? <img src={course.cover_url} alt={course.title} className="w-full h-full object-cover" />
                      : <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-navy-100 to-purple-100">
                          <BookOpen className="w-12 h-12 text-navy-300" />
                        </div>
                    }
                    {course.is_free && (
                      <span className="absolute top-2 left-2 px-2 py-0.5 bg-green-500 text-white text-xs font-medium rounded">Gratuit</span>
                    )}
                    {isEnrolled && (
                      <span className="absolute top-2 right-2 px-2 py-0.5 bg-navy-500 text-white text-xs font-medium rounded flex items-center gap-1">
                        <Award className="w-3 h-3" /> Inscrit
                      </span>
                    )}
                  </div>
                  <div className="p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="px-2 py-0.5 bg-navy-50 text-navy-700 text-xs rounded capitalize">
                        {LEVELS[course.level as keyof typeof LEVELS] || course.level}
                      </span>
                      {course.category && (
                        <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded">{course.category}</span>
                      )}
                    </div>
                    <h3 className="font-semibold mb-1 line-clamp-2">{course.title}</h3>
                    {course.description && (
                      <p className="text-sm text-gray-500 mb-3 line-clamp-2">{course.description}</p>
                    )}
                    <div className="flex items-center gap-4 text-xs text-gray-400 mb-3">
                      <span className="flex items-center gap-1"><BookOpen className="w-3 h-3" /> {course.total_lessons} leçons</span>
                      <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> {course.total_duration_minutes} min</span>
                      {course.total_modules > 0 && <span className="flex items-center gap-1">📚 {course.total_modules} modules</span>}
                    </div>
                    <div className="flex gap-2">
                      {isEnrolled ? (
                        <button onClick={() => navigate(`/learn/courses/${course.id}`)}
                          className="flex-1 flex items-center justify-center gap-2 py-2 bg-navy-600 text-white text-sm rounded-lg hover:bg-navy-700 font-medium">
                          Continuer <ChevronRight className="w-4 h-4" />
                        </button>
                      ) : (
                        <>
                          <button onClick={(e) => handleEnroll(e, course.id)}
                            className="flex-1 py-2 bg-navy-600 text-white text-sm rounded-lg hover:bg-navy-700 font-medium">
                            S'inscrire
                          </button>
                          <button onClick={() => navigate(`/learn/courses/${course.id}`)}
                            className="py-2 px-3 border text-sm text-gray-600 rounded-lg hover:bg-gray-50">
                            Aperçu
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}