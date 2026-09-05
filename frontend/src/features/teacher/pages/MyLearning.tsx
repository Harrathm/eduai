import { useState, useEffect, useCallback } from "react";
import { useTranslation } from 'react-i18next';
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../../../store/authStore";
import { Search, BookOpen, Clock, Plus, Pencil, GripVertical, AlertCircle } from "lucide-react";
import { teacherMyCoursesApi } from "../../../api";
import { Button } from "../../../components/ui";
import { ALL_NIVEAUX } from "../../admin/constants/cycles";

interface Course {
  id: number;
  title: string;
  short_description: string;
  description: string;
  category: string;
  category_cible: string;
  niveau_scolaire: string;
  cover_url: string;
  thumbnail_url: string;
  status: string;
  is_published: boolean;
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
  const [myCourses, setMyCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [createForm, setCreateForm] = useState({
    title: "",
    description: "",
    niveau_scolaire: "",
    category: "",
  });

  useEffect(() => {
    fetchMyCourses();
  }, [token]);

  const fetchMyCourses = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const data = await teacherMyCoursesApi.listMyCourses();
      setMyCourses(Array.isArray(data) ? data : (data as any).items || data || []);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const handleCreateCourse = useCallback(async () => {
    if (!createForm.title.trim()) return;
    if (!createForm.niveau_scolaire.trim() || !createForm.category.trim()) {
      setCreateError("Le niveau scolaire et la matière sont obligatoires pour un cours scolaire.");
      return;
    }
    setCreating(true);
    setCreateError(null);
    try {
      const result = await teacherMyCoursesApi.createCourse({
        title: createForm.title,
        description: createForm.description || undefined,
        category_cible: "Scolaire",
        niveau_scolaire: createForm.niveau_scolaire,
        category: createForm.category,
      } as any);
      setShowCreateModal(false);
      setCreateForm({ title: "", description: "", niveau_scolaire: "", category: "" });
      fetchMyCourses();
      const courseId = (result as any)?.id;
      if (courseId) {
        navigate(`/dashboard/teacher/courses/${courseId}/editor`);
      }
    } catch (err: any) {
      setCreateError(err?.message || "Erreur lors de la création");
    } finally {
      setCreating(false);
    }
  }, [createForm, navigate]);

  const filtered = myCourses.filter((c) => {
    if (!search) return true;
    return c.title.toLowerCase().includes(search.toLowerCase());
  });

  const statusBadge = (status: string, isPublished: boolean) => {
    if (isPublished) return <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full font-medium">Publié</span>;
    if (status === "pending_review") return <span className="px-2 py-0.5 bg-yellow-100 text-yellow-700 text-xs rounded-full font-medium">En review</span>;
    return <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full font-medium">Brouillon</span>;
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-3xl p-8 shadow-sm border border-black/5">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-[300] text-navy">
              {t('teacher.learning.title')} <span className="italic text-orange">{t('teacher.learning.titleSuffix')}</span>
            </h1>
            <p className="text-gray mt-2">
              {t('teacher.learning.description')}
            </p>
          </div>
          <Button variant="primary" size="md" onClick={() => setShowCreateModal(true)}>
            <Plus className="w-4 h-4 mr-2" />
            Créer un cours
          </Button>
        </div>
      </div>

      {/* Search */}
      <div className="bg-white rounded-3xl p-6 shadow-sm border border-black/5">
        <div className="relative max-w-md">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full ps-12 pe-4 py-3 bg-cream-m rounded-xl border border-black/5 focus:border-orange focus:outline-none"
            placeholder="Rechercher un cours..."
          />
        </div>
      </div>

      {/* My Courses */}
      {loading ? (
        <div className="bg-white rounded-3xl p-12 text-center text-gray">
          {t('teacher.learning.loading')}
        </div>
      ) : filtered.length === 0 ? (
        <div className="bg-white rounded-3xl p-12 text-center">
          <BookOpen className="w-12 h-12 mx-auto mb-3 text-gray-300" />
          <p className="text-gray mb-4">
            {search ? "Aucun cours ne correspond à votre recherche" : "Vous n'avez pas encore créé de cours"}
          </p>
          {!search && (
            <Button variant="primary" size="md" onClick={() => setShowCreateModal(true)}>
              <Plus className="w-4 h-4 mr-2" />
              Créer votre premier cours
            </Button>
          )}
        </div>
      ) : (
        <div className="grid gap-4">
          {filtered.map((course) => (
            <div
              key={course.id}
              className="bg-white rounded-2xl p-6 shadow-sm border border-black/5 hover:shadow-md transition-shadow"
            >
              <div className="flex justify-between items-start gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-semibold text-navy truncate">{course.title}</h3>
                    {statusBadge(course.status, course.is_published)}
                  </div>
                  <p className="text-sm text-gray mb-3 line-clamp-2">
                    {course.short_description || course.description || "Aucune description"}
                  </p>
                  <div className="flex items-center gap-6 text-sm text-gray">
                    <span className="flex items-center gap-1">
                      <BookOpen className="w-4 h-4" />
                      {course.total_modules || 0} chapitres
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-4 h-4" />
                      {course.total_lessons || 0} leçons
                    </span>
                    {course.niveau_scolaire && (
                      <span className="px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded-full">
                        {course.niveau_scolaire}
                      </span>
                    )}
                    {course.category && (
                      <span className="px-2 py-0.5 bg-orange-50 text-orange-700 text-xs rounded-full">
                        {course.category}
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex gap-2 shrink-0">
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => navigate(`/dashboard/teacher/courses/${course.id}/editor`)}
                    title="Modifier les informations du cours"
                  >
                    <Pencil className="w-4 h-4 mr-1" />
                    Éditer
                  </Button>
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => navigate(`/dashboard/teacher/courses/${course.id}/builder`)}
                    title="Construire la structure du cours"
                  >
                    <GripVertical className="w-4 h-4 mr-1" />
                    Builder
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Course Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-2xl p-8 w-full max-w-lg shadow-xl">
            <h2 className="text-xl font-semibold text-navy mb-4">Créer un cours</h2>

            {createError && (
              <div className="flex items-center gap-2 p-3 mb-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
                <AlertCircle className="w-4 h-4 shrink-0" />
                {createError}
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Titre *</label>
                <input
                  type="text"
                  value={createForm.title}
                  onChange={(e) => setCreateForm({ ...createForm, title: e.target.value })}
                  className="w-full px-4 py-2.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-orange/30 focus:border-orange"
                  placeholder="Ex: Mathématiques - ème année"
                  autoFocus
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea
                  value={createForm.description}
                  onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
                  className="w-full px-4 py-2.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-orange/30 focus:border-orange"
                  placeholder="Description courte du cours"
                  rows={3}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Niveau scolaire *</label>
                  <select
                    value={createForm.niveau_scolaire}
                    onChange={(e) => setCreateForm({ ...createForm, niveau_scolaire: e.target.value })}
                    className="w-full px-4 py-2.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-orange/30 focus:border-orange"
                  >
                    <option value="">-- Choisir un niveau --</option>
                    {ALL_NIVEAUX.map((g) => (
                      <optgroup key={g.group} label={g.group}>
                        {g.items.map((n) => (
                          <option key={n} value={n}>{n}</option>
                        ))}
                      </optgroup>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Matière *</label>
                  <input
                    type="text"
                    value={createForm.category}
                    onChange={(e) => setCreateForm({ ...createForm, category: e.target.value })}
                    className="w-full px-4 py-2.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-orange/30 focus:border-orange"
                    placeholder="Ex: Mathématiques"
                  />
                </div>
              </div>
            </div>

            <div className="flex gap-3 mt-6 justify-end">
              <Button
                variant="ghost"
                size="md"
                onClick={() => {
                  setShowCreateModal(false);
                  setCreateError(null);
                  setCreateForm({ title: "", description: "", niveau_scolaire: "", category: "" });
                }}
              >
                Annuler
              </Button>
              <Button
                variant="primary"
                size="md"
                onClick={handleCreateCourse}
                disabled={!createForm.title.trim() || !createForm.niveau_scolaire.trim() || !createForm.category.trim() || creating}
              >
                {creating ? "Création..." : "Créer le cours"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
