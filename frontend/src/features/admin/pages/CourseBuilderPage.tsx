import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { adminCoursesAPI } from "../../../api/lms";
import { Plus, Trash2, Edit, Eye, EyeOff, BookOpen, Search, Copy, X, Check } from "lucide-react";

const CATEGORIES = ["Programmation", "Mathématiques", "Sciences", "Langues", "Business", "Design", "Marketing", "Autre"];
const LEVELS = [
  { value: "beginner", label: "Débutant" },
  { value: "intermediate", label: "Intermédiaire" },
  { value: "advanced", label: "Avancé" },
];

interface Course {
  id: number;
  title: string;
  description?: string;
  short_description?: string;
  cover_url?: string;
  thumbnail_url?: string;
  category?: string;
  level?: string;
  status: string;
  price_tokens: number;
  price_dt: number;
  total_chapters?: number;
  total_lessons?: number;
  visibility?: string;
  created_at?: string;
}

export default function CourseBuilderPage() {
  const navigate = useNavigate();
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [levelFilter, setLevelFilter] = useState("");
  const [creating, setCreating] = useState(false);

  const [form, setForm] = useState({
    title: "",
    short_description: "",
    description: "",
    category: "",
    level: "beginner",
    price_tokens: 0,
    price_dt: 0,
  });

  useEffect(() => { loadCourses(); }, [statusFilter]);

  const loadCourses = async () => {
    setLoading(true);
    try {
      const data = await adminCoursesAPI.list(statusFilter || undefined);
      setCourses(Array.isArray(data) ? data : (data.items || []));
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const handleCreate = async () => {
    if (!form.title.trim()) { alert("Le titre est requis"); return; }
    setCreating(true);
    try {
      const created = await adminCoursesAPI.create(form);
      setCourses([created, ...courses]);
      setShowCreate(false);
      setForm({ title: "", short_description: "", description: "", category: "", level: "beginner", price_tokens: 0, price_dt: 0 });
      navigate(`/dashboard/admin/courses/${created.id}`);
    } catch (e: any) { alert("Erreur: " + (e.message || "")); }
    finally { setCreating(false); }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Supprimer ce cours ?")) return;
    try {
      await adminCoursesAPI.delete(id);
      setCourses(courses.filter(c => c.id !== id));
    } catch (e) { alert("Erreur de suppression"); }
  };

  const handlePublish = async (id: number) => {
    try { await adminCoursesAPI.publish(id); loadCourses(); }
    catch (e) { alert("Erreur"); }
  };

  const handleUnpublish = async (id: number) => {
    try { await adminCoursesAPI.unpublish(id); loadCourses(); }
    catch (e) { alert("Erreur"); }
  };

  const handleDuplicate = async (id: number) => {
    try {
      const result = await adminCoursesAPI.duplicate(id);
      alert(`Cours copié: ${result.title}`);
      loadCourses();
    } catch (e) { alert("Erreur de duplication"); }
  };

  const filtered = courses.filter(c => {
    const s = search.toLowerCase();
    const match = !s || c.title?.toLowerCase().includes(s) || c.description?.toLowerCase().includes(s);
    const matchLevel = !levelFilter || c.level === levelFilter;
    return match && matchLevel;
  });

  const statusBadge = (s: string) => {
    switch (s) {
      case "published": return <span className="px-2 py-0.5 text-xs rounded bg-green-100 text-green-800">Publié</span>;
      case "archived": return <span className="px-2 py-0.5 text-xs rounded bg-gray-100 text-gray-600">Archivé</span>;
      default: return <span className="px-2 py-0.5 text-xs rounded bg-yellow-100 text-yellow-800">Brouillon</span>;
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Course Builder</h1>
          <p className="text-gray-500 text-sm">Créez et gérez vos cours</p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 px-4 py-2 bg-navy-600 text-white rounded-lg hover:bg-navy-700 font-medium"
        >
          <Plus className="w-5 h-5" />
          Nouveau cours
        </button>
      </div>

      {/* Create Modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl w-full max-w-lg">
            <div className="p-4 border-b flex justify-between items-center">
              <h2 className="font-semibold text-lg">Créer un nouveau cours</h2>
              <button onClick={() => setShowCreate(false)} className="p-1 hover:bg-gray-100 rounded"><X className="w-5 h-5" /></button>
            </div>
            <div className="p-4 space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Titre *</label>
                <input type="text" value={form.title} onChange={e => setForm({ ...form, title: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg" placeholder="Introduction à Python" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Description courte</label>
                <textarea value={form.short_description} onChange={e => setForm({ ...form, short_description: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg" rows={2} placeholder="Un résumé du cours..." />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Catégorie</label>
                  <select value={form.category} onChange={e => setForm({ ...form, category: e.target.value })}
                    className="w-full px-3 py-2 border rounded-lg">
                    <option value="">Sélectionner...</option>
                    {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Niveau</label>
                  <select value={form.level} onChange={e => setForm({ ...form, level: e.target.value })}
                    className="w-full px-3 py-2 border rounded-lg">
                    {LEVELS.map(l => <option key={l.value} value={l.value}>{l.label}</option>)}
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Prix (Tokens)</label>
                  <input type="number" value={form.price_tokens} onChange={e => setForm({ ...form, price_tokens: Number(e.target.value) })}
                    className="w-full px-3 py-2 border rounded-lg" min="0" />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Prix (DT)</label>
                  <input type="number" step="0.01" value={form.price_dt} onChange={e => setForm({ ...form, price_dt: Number(e.target.value) })}
                    className="w-full px-3 py-2 border rounded-lg" min="0" />
                </div>
              </div>
            </div>
            <div className="p-4 border-t flex justify-end gap-2">
              <button onClick={() => setShowCreate(false)} className="px-4 py-2 border rounded-lg hover:bg-gray-50">Annuler</button>
              <button onClick={handleCreate} disabled={creating}
                className="flex items-center gap-2 px-4 py-2 bg-navy-600 text-white rounded-lg hover:bg-navy-700 disabled:opacity-50">
                {creating ? "Création..." : <><Check className="w-4 h-4" /> Créer</>}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow mb-6">
        <div className="flex flex-wrap gap-3 items-center">
          <div className="flex-1 min-w-[200px] relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input type="text" placeholder="Rechercher un cours..." value={search}
              onChange={e => setSearch(e.target.value)} className="w-full ps-10 pe-4 py-2 border rounded-lg" />
          </div>
          <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="px-3 py-2 border rounded-lg">
            <option value="">Tous les statuts</option>
            <option value="draft">Brouillon</option>
            <option value="published">Publié</option>
            <option value="archived">Archivé</option>
          </select>
          <select value={levelFilter} onChange={e => setLevelFilter(e.target.value)} className="px-3 py-2 border rounded-lg">
            <option value="">Tous les niveaux</option>
            {LEVELS.map(l => <option key={l.value} value={l.value}>{l.label}</option>)}
          </select>
        </div>
      </div>

      {/* Course Grid */}
      {loading ? (
        <div className="text-center py-20 text-gray-500">Chargement...</div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-20">
          <BookOpen className="w-12 h-12 mx-auto mb-4 text-gray-300" />
          <p className="text-gray-500">Aucun cours trouvé</p>
          <button onClick={() => setShowCreate(true)} className="mt-4 px-4 py-2 bg-navy-600 text-white rounded-lg hover:bg-navy-700">
            Créer mon premier cours
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map(course => (
            <div key={course.id} className="bg-white rounded-lg shadow hover:shadow-md transition-shadow">
              {course.cover_url && (
                <img src={course.cover_url} alt="" className="w-full h-32 object-cover rounded-t-lg" />
              )}
              <div className="p-4">
                <div className="flex justify-between items-start mb-2">
                  <h3 className="font-semibold text-gray-900 line-clamp-1">{course.title}</h3>
                  {statusBadge(course.status)}
                </div>
                <p className="text-sm text-gray-500 line-clamp-2 mb-3">
                  {course.short_description || course.description || "Aucune description"}
                </p>
                <div className="flex items-center gap-2 text-xs text-gray-400 mb-3">
                  <span>{course.total_chapters || 0} chapitres</span>
                  <span>•</span>
                  <span>{course.total_lessons || 0} leçons</span>
                  {course.level && <><span>•</span><span className="capitalize">{course.level}</span></>}
                </div>
                <div className="flex gap-2 flex-wrap">
                  <button onClick={() => navigate(`/dashboard/admin/courses/${course.id}`)}
                    className="flex items-center gap-1 px-3 py-1.5 text-sm bg-navy-600 text-white rounded hover:bg-navy-700">
                    <Edit className="w-3 h-3" /> Éditer
                  </button>
                  {course.status === "published" ? (
                    <button onClick={() => handleUnpublish(course.id)}
                      className="flex items-center gap-1 px-3 py-1.5 text-sm border rounded hover:bg-gray-50">
                      <EyeOff className="w-3 h-3" /> Dépublier
                    </button>
                  ) : (
                    <button onClick={() => handlePublish(course.id)}
                      className="flex items-center gap-1 px-3 py-1.5 text-sm border rounded hover:bg-gray-50">
                      <Eye className="w-3 h-3" /> Publier
                    </button>
                  )}
                  <button onClick={() => handleDuplicate(course.id)}
                    className="p-1.5 border rounded hover:bg-gray-50" title="Dupliquer">
                    <Copy className="w-4 h-4" />
                  </button>
                  <button onClick={() => handleDelete(course.id)}
                    className="p-1.5 text-red-600 hover:bg-red-50 rounded">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
