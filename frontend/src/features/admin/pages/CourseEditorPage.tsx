import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Plus, Trash2, Save, ArrowLeft, GripVertical, Video, FileText,
  Image, Link, HelpCircle, File, ChevronDown, X, Eye, EyeOff, Copy,
  Archive, AlertCircle, CheckCircle
} from "lucide-react";

import { adminCoursesAPI, adminChaptersAPI, adminLessonsAPI } from "../../../api/lms";
import { adminCourses } from "../../admin/api";
import { tokenStorage } from "../../../utils/tokenStorage";

const LESSON_TYPES = [
  { value: "text", label: "Texte", icon: FileText },
  { value: "video", label: "Vidéo", icon: Video },
  { value: "pdf", label: "Document PDF", icon: File },
  { value: "image", label: "Image", icon: Image },
  { value: "link", label: "Lien externe", icon: Link },
  { value: "quiz", label: "Quiz/Examen", icon: HelpCircle },
];

function getToken() { return tokenStorage.getToken(); }

async function apiFetch(path: string, options: RequestInit = {}) {
  const token = getToken();
  const res = await fetch(`${""}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Erreur ${res.status}`);
  }
  return res.json();
}

interface Lesson {
  id: number;
  title: string;
  lesson_type: string;
  order: number;
  duration_minutes: number;
  content_text?: string;
  video_url?: string;
  pdf_url?: string;
  image_urls?: string[];
  link_url?: string;
  link_title?: string;
  is_free?: boolean;
  description?: string;
}

interface Chapter {
  id: number;
  title: string;
  order: number;
  lessons: Lesson[];
}

export default function CourseEditorPage() {
  const { courseId } = useParams();
  const navigate = useNavigate();
  const [course, setCourse] = useState<any>(null);
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [activeChapter, setActiveChapter] = useState<number | null>(null);
  const [showLessonEditor, setShowLessonEditor] = useState(false);
  const [activeLesson, setActiveLesson] = useState<Lesson | null>(null);
  const [toast, setToast] = useState({ show: false, message: "", type: "success" as "success" | "error" });
  const [publishErrors, setPublishErrors] = useState<string[]>([]);
  const [previewCourse, setPreviewCourse] = useState<any>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [editLessonForm, setEditLessonForm] = useState({
    title: "", description: "", lesson_type: "text", content_text: "",
    video_url: "", pdf_url: "", image_urls: "", link_url: "", link_title: "",
    duration_minutes: 0, is_free: false,
  });

  const showToast = (message: string, type: "success" | "error" = "success") => {
    setToast({ show: true, message, type });
    setTimeout(() => setToast({ show: false, message: "", type: "success" }), 3500);
  };

  useEffect(() => { if (courseId) loadCourse(); }, [courseId]);

  const loadCourse = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiFetch(`/api/admin/courses/${courseId}`);
      setCourse(data);
      const chs = data.chapters || [];
      setChapters(chs);
      if (chs.length > 0) setActiveChapter(chs[0].id);
    } catch (e: any) {
      console.error(e);
      setError(e.message || "Failed to load course. Please try again.");
    }
    finally { setLoading(false); }
  };

  const handleSaveCourse = async () => {
    setSaving(true);
    try {
      const tagsArray = course.tags
        ? (typeof course.tags === "string" ? JSON.parse(course.tags) : course.tags)
        : [];
      await adminCoursesAPI.update(Number(courseId), {
        title: course.title,
        short_description: course.short_description,
        description: course.description,
        category: course.category,
        level: course.level,
        prerequisites: course.prerequisites,
        learning_objectives: course.learning_objectives,
        price_tokens: course.price_tokens,
        price_dt: course.price_dt,
        cover_url: course.cover_url,
        thumbnail_url: course.thumbnail_url,
        visibility: course.visibility,
        enrollment_type: course.enrollment_type,
        tags: tagsArray,
        language: course.language,
        max_students: course.max_students,
      });
      showToast("Cours enregistré avec succès");
    } catch (e: any) { showToast("Erreur: " + e.message, "error"); }
    finally { setSaving(false); }
  };

  const handlePublish = async () => {
    setSaving(true);
    setPublishErrors([]);
    try {
      await adminCourses.publish(Number(courseId));
      showToast("Cours publié avec succès!");
      loadCourse();
    } catch (e: any) {
      const msg = e.message || "";
      try {
        const errData = JSON.parse(msg);
        if (errData.errors && errData.errors.length) {
          setPublishErrors(errData.errors);
        } else if (errData.message) {
          setPublishErrors([errData.message]);
        } else {
          setPublishErrors([msg]);
        }
      } catch {
        setPublishErrors([msg || "Erreur inconnue"]);
      }
    }
    finally { setSaving(false); }
  };

  const handleUnpublish = async () => {
    setSaving(true);
    try {
      await adminCourses.unpublish(Number(courseId));
      showToast("Cours dépublié");
      loadCourse();
    } catch (e: any) { showToast("Erreur: " + e.message, "error"); }
    finally { setSaving(false); }
  };

  const handleArchive = async () => {
    if (!confirm("Archiver ce cours ? Il ne sera plus visible par les apprenants.")) return;
    setSaving(true);
    try {
      await adminCourses.archive(Number(courseId));
      showToast("Cours archivé");
      loadCourse();
    } catch (e: any) { showToast("Erreur: " + e.message, "error"); }
    finally { setSaving(false); }
  };

  const handlePreview = async () => {
    setPreviewLoading(true);
    try {
      const data = await adminCourses.preview(Number(courseId));
      setPreviewCourse(data);
    } catch (e: any) { showToast("Erreur aperçu: " + e.message, "error"); }
    setPreviewLoading(false);
  };

  const handleAddChapter = async () => {
    try {
      const created = await adminChaptersAPI.create(Number(courseId), { title: `Chapitre ${chapters.length + 1}` });
      setChapters([...chapters, { ...created, lessons: [] }]);
      setActiveChapter(created.id);
      showToast("Chapitre ajouté");
    } catch (e) { console.error(e); showToast("Erreur ajout chapitre", "error"); }
  };

  const handleUpdateChapterTitle = async (id: number, title: string) => {
    try {
      await adminChaptersAPI.update(Number(courseId), id, { title });
      setChapters(chapters.map(c => c.id === id ? { ...c, title } : c));
    } catch (e) { console.error(e); }
  };

  const handleDeleteChapter = async (id: number) => {
    if (!confirm("Supprimer ce chapitre et toutes ses leçons ?")) return;
    try {
      await adminChaptersAPI.delete(Number(courseId), id);
      setChapters(chapters.filter(c => c.id !== id));
      if (activeChapter === id) setActiveChapter(null);
      showToast("Chapitre supprimé");
    } catch (e) { console.error(e); showToast("Erreur suppression", "error"); }
  };

  const handleAddLesson = async (chapterId: number) => {
    try {
      const created = await adminLessonsAPI.create(chapterId, { title: "Nouvelle leçon", lesson_type: "text", order: 0 });
      setChapters(chapters.map(c =>
        c.id === chapterId ? { ...c, lessons: [...(c.lessons || []), created] } : c
      ));
      setActiveLesson(created);
      setEditLessonForm({
        title: created.title, description: "", lesson_type: "text", content_text: "",
        video_url: "", pdf_url: "", image_urls: "", link_url: "", link_title: "",
        duration_minutes: 0, is_free: false,
      });
      setShowLessonEditor(true);
    } catch (e) { console.error(e); showToast("Erreur ajout leçon", "error"); }
  };

  const handleSaveLesson = async () => {
    if (!activeLesson) return;
    try {
      const data = {
        title: editLessonForm.title,
        lesson_type: editLessonForm.lesson_type,
        content_text: editLessonForm.content_text,
        video_url: editLessonForm.video_url,
        pdf_url: editLessonForm.pdf_url,
        image_urls: (() => {
          const v = editLessonForm.image_urls;
          if (!v) return [];
          try { const parsed = JSON.parse(v); return Array.isArray(parsed) ? parsed : [parsed]; }
          catch { return v.split("\n").map((s: string) => s.trim()).filter(Boolean); }
        })(),
        link_url: editLessonForm.link_url,
        link_title: editLessonForm.link_title,
        duration_minutes: editLessonForm.duration_minutes,
        is_free: editLessonForm.is_free,
      };
      await adminLessonsAPI.update(activeLesson.id, data);
      setChapters(chapters.map(c => ({
        ...c,
        lessons: c.lessons?.map((l: Lesson) => l.id === activeLesson.id ? { ...l, ...editLessonForm } : l),
      })));
      setShowLessonEditor(false);
      showToast("Leçon enregistrée");
    } catch (e) { console.error(e); showToast("Erreur enregistrement leçon", "error"); }
  };

  const handleDeleteLesson = async (chapterId: number, lessonId: number) => {
    if (!confirm("Supprimer cette leçon ?")) return;
    try {
      await adminLessonsAPI.delete(lessonId);
      setChapters(chapters.map(c =>
        c.id === chapterId ? { ...c, lessons: c.lessons.filter((l: Lesson) => l.id !== lessonId) } : c
      ));
      showToast("Leçon supprimée");
    } catch (e) { console.error(e); showToast("Erreur suppression", "error"); }
  };

  const openLessonEditor = (lesson: Lesson) => {
    setActiveLesson(lesson);
    setEditLessonForm({
      title: lesson.title,
      description: lesson.description || "",
      lesson_type: lesson.lesson_type || "text",
      content_text: lesson.content_text || "",
      video_url: lesson.video_url || "",
      pdf_url: lesson.pdf_url || "",
      image_urls: lesson.image_urls ? (typeof lesson.image_urls === "string" ? lesson.image_urls : JSON.stringify(lesson.image_urls)) : "[]",
      link_url: lesson.link_url || "",
      link_title: lesson.link_title || "",
      duration_minutes: lesson.duration_minutes || 0,
      is_free: lesson.is_free || false,
    });
    setShowLessonEditor(true);
  };

  const handleDuplicate = async () => {
    if (!confirm("Dupliquer ce cours ? Une copie sera créée en brouillon.")) return;
    setSaving(true);
    try {
      await adminCourses.duplicate(Number(courseId));
      showToast("Cours dupliqué!");
      navigate("/dashboard/admin/courses");
    } catch (e: any) { showToast("Erreur: " + e.message, "error"); }
    setSaving(false);
  };

  const getLessonIcon = (type: string) => {
    const t = LESSON_TYPES.find(x => x.value === type);
    return t ? <t.icon className="w-4 h-4" /> : <FileText className="w-4 h-4" />;
  };

  const getLessonBg = (type: string) => {
    switch (type) {
      case "video": return "bg-blue-50 text-blue-600";
      case "pdf": return "bg-red-50 text-red-600";
      case "image": return "bg-green-50 text-green-600";
      case "link": return "bg-purple-50 text-purple-600";
      case "quiz": return "bg-orange-50 text-orange-600";
      default: return "bg-gray-50 text-gray-600";
    }
  };

  if (loading) {
    return (
      <div className="flex h-screen bg-gray-50">
        <div className="w-72 bg-white border-r p-4">
          <div className="h-8 bg-gray-200 rounded w-24 mb-4 animate-pulse"></div>
          <div className="h-12 bg-gray-200 rounded mb-4 animate-pulse"></div>
          <div className="space-y-2">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-10 bg-gray-200 rounded animate-pulse"></div>
            ))}
          </div>
        </div>
        <div className="flex-1 p-6">
          <div className="h-64 bg-gray-200 rounded-xl animate-pulse"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-50">
        <div className="bg-white rounded-2xl p-8 shadow-sm border text-center max-w-md">
          <p className="text-red-600 mb-4">{error}</p>
          <div className="flex gap-3 justify-center">
            <button onClick={() => navigate("/dashboard/admin/courses")} className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 font-medium">
              Retour aux cours
            </button>
            <button onClick={loadCourse} className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium">
              Réessayer
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!course) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-50">
        <div className="bg-white rounded-2xl p-8 shadow-sm border text-center">
          <p className="text-gray-600 mb-4">Cours introuvable</p>
          <button onClick={() => navigate("/dashboard/admin/courses")} className="px-4 py-2 bg-navy text-white rounded-lg hover:bg-navy-m font-medium">
            Retour aux cours
          </button>
        </div>
      </div>
    );
  }

  const activeChapterData = chapters.find(c => c.id === activeChapter);
  const tagsDisplay = course.tags ? (typeof course.tags === "string" ? JSON.parse(course.tags) : course.tags) : [];

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Left Sidebar */}
      <div className="w-80 bg-white border-r flex flex-col">
        <div className="p-4 border-b space-y-2">
          <button onClick={() => navigate("/dashboard/admin/courses")} className="flex items-center gap-1 text-sm text-gray-600 hover:text-gray-900">
            <ArrowLeft className="w-4 h-4" /> Retour
          </button>
          <h2 className="font-semibold text-lg line-clamp-1">{course.title}</h2>
          <div className="flex gap-2 flex-wrap">
            <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${
              course.status === "published" ? "bg-green-100 text-green-800" :
              course.status === "archived" ? "bg-orange-100 text-orange-700" : "bg-yellow-100 text-yellow-800"
            }`}>
              {course.status === "published" ? "Publié" : course.status === "archived" ? "Archivé" : "Brouillon"}
            </span>
            <span className="text-xs text-gray-500">{chapters.length} chapitres</span>
          </div>
          <div className="flex gap-2">
            <button onClick={handlePreview} disabled={previewLoading}
              className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 text-xs bg-purple-100 text-purple-800 rounded hover:bg-purple-200 disabled:opacity-50">
              <Eye className="w-3 h-3" /> Aperçu
            </button>
            <button onClick={handleDuplicate} disabled={saving}
              className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 text-xs bg-navy-100 text-navy-800 rounded hover:bg-navy-200 disabled:opacity-50">
              <Copy className="w-3 h-3" /> Dupliquer
            </button>
          </div>
          <div className="flex gap-2">
            {course.status === "published" ? (
              <button onClick={handleUnpublish} disabled={saving}
                className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 text-xs bg-orange-100 text-orange-800 rounded hover:bg-orange-200 disabled:opacity-50">
                <EyeOff className="w-3 h-3" /> Dépublier
              </button>
            ) : (
              <button onClick={handlePublish} disabled={saving}
                className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 text-xs bg-green-100 text-green-800 rounded hover:bg-green-200 disabled:opacity-50">
                <Eye className="w-3 h-3" /> Publier
              </button>
            )}
            {course.status !== "archived" && (
              <button onClick={handleArchive} disabled={saving}
                className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 text-xs bg-gray-100 text-gray-600 rounded hover:bg-gray-200 disabled:opacity-50">
                <Archive className="w-3 h-3" /> Archiver
              </button>
            )}
          </div>
          {publishErrors.length > 0 && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-2 space-y-1">
              {publishErrors.map((e, i) => (
                <div key={i} className="flex items-start gap-1 text-xs text-red-600">
                  <AlertCircle className="w-3 h-3 mt-0.5 shrink-0" /> {e}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Course Settings */}
        <div className="p-3 border-b bg-gray-50 space-y-3 max-h-[50vh] overflow-y-auto">
          <h4 className="text-xs font-medium text-gray-500 uppercase">Paramètres du cours</h4>
          <div>
            <label className="block text-xs font-medium mb-1">Titre *</label>
            <input type="text" value={course.title || ""} onChange={e => setCourse({ ...course, title: e.target.value })}
              className="w-full px-2 py-1 text-sm border rounded" />
          </div>
          <div>
            <label className="block text-xs font-medium mb-1">Description courte</label>
            <textarea value={course.short_description || ""} onChange={e => setCourse({ ...course, short_description: e.target.value })}
              className="w-full px-2 py-1 text-sm border rounded" rows={2} />
          </div>
          <div>
            <label className="block text-xs font-medium mb-1">Description</label>
            <textarea value={course.description || ""} onChange={e => setCourse({ ...course, description: e.target.value })}
              className="w-full px-2 py-1 text-sm border rounded" rows={3} />
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="block text-xs font-medium mb-1">Catégorie</label>
              <input type="text" value={course.category || ""} onChange={e => setCourse({ ...course, category: e.target.value })}
                className="w-full px-2 py-1 text-sm border rounded" />
            </div>
            <div>
              <label className="block text-xs font-medium mb-1">Niveau</label>
              <select value={course.level || "beginner"} onChange={e => setCourse({ ...course, level: e.target.value })}
                className="w-full px-2 py-1 text-sm border rounded">
                <option value="beginner">Débutant</option>
                <option value="intermediate">Intermédiaire</option>
                <option value="advanced">Avancé</option>
              </select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="block text-xs font-medium mb-1">Visibilité</label>
              <select value={course.visibility || "public"} onChange={e => setCourse({ ...course, visibility: e.target.value })}
                className="w-full px-2 py-1 text-sm border rounded">
                <option value="public">Public</option>
                <option value="private">Privé</option>
                <option value="school">Par école</option>
                <option value="role">Par rôle</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium mb-1">Inscription</label>
              <select value={course.enrollment_type || "open"} onChange={e => setCourse({ ...course, enrollment_type: e.target.value })}
                className="w-full px-2 py-1 text-sm border rounded">
                <option value="open">Libre</option>
                <option value="manual">Manuelle</option>
              </select>
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium mb-1">Prérequis</label>
            <textarea value={course.prerequisites || ""} onChange={e => setCourse({ ...course, prerequisites: e.target.value })}
              className="w-full px-2 py-1 text-sm border rounded" rows={2}
              placeholder="Prérequis pour suivre ce cours" />
          </div>
          <div>
            <label className="block text-xs font-medium mb-1">Objectifs pédagogiques</label>
            <textarea value={course.learning_objectives || ""} onChange={e => setCourse({ ...course, learning_objectives: e.target.value })}
              className="w-full px-2 py-1 text-sm border rounded" rows={2}
              placeholder="Ce que les apprenants sauront faire" />
          </div>
          <div>
            <label className="block text-xs font-medium mb-1">Tags (virgules)</label>
            <input type="text" value={tagsDisplay.join(", ")} onChange={e => setCourse({ ...course, tags: e.target.value.split(",").map((t: string) => t.trim()).filter(Boolean) })}
              className="w-full px-2 py-1 text-sm border rounded" placeholder="python, débutant" />
          </div>
          <div>
            <label className="block text-xs font-medium mb-1">Langue</label>
            <select value={course.language || "fr"} onChange={e => setCourse({ ...course, language: e.target.value })}
              className="w-full px-2 py-1 text-sm border rounded">
              <option value="fr">Français</option>
              <option value="en">English</option>
              <option value="ar">العربية</option>
            </select>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="block text-xs font-medium mb-1">Prix (Tokens)</label>
              <input type="number" value={course.price_tokens || 0} onChange={e => setCourse({ ...course, price_tokens: Number(e.target.value) })}
                className="w-full px-2 py-1 text-sm border rounded" />
            </div>
            <div>
              <label className="block text-xs font-medium mb-1">Prix (DT)</label>
              <input type="number" step="0.01" value={course.price_dt || 0} onChange={e => setCourse({ ...course, price_dt: Number(e.target.value) })}
                className="w-full px-2 py-1 text-sm border rounded" />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="block text-xs font-medium mb-1">Max étudiants</label>
              <input type="number" value={course.max_students || ""} onChange={e => setCourse({ ...course, max_students: e.target.value ? Number(e.target.value) : null })}
                className="w-full px-2 py-1 text-sm border rounded" placeholder="Illimité" />
            </div>
            <div>
              <label className="block text-xs font-medium mb-1">Durée estimée (min)</label>
              <input type="number" value={course.total_duration_minutes || 0} readOnly
                className="w-full px-2 py-1 text-sm border rounded bg-gray-100" />
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium mb-1">URL Couverture</label>
            <input type="text" value={course.cover_url || course.thumbnail_url || ""} onChange={e => setCourse({ ...course, cover_url: e.target.value, thumbnail_url: e.target.value })}
              className="w-full px-2 py-1 text-sm border rounded" placeholder="https://..." />
          </div>
          {(course.cover_url || course.thumbnail_url) && (
            <img src={course.cover_url || course.thumbnail_url} alt="Couverture" className="w-full h-24 object-cover rounded border" />
          )}
          <div className="text-xs text-gray-400 space-y-0.5">
            <div>Créé: {course.created_at ? new Date(course.created_at).toLocaleDateString() : "—"}</div>
            <div>Modifié: {course.updated_at ? new Date(course.updated_at).toLocaleDateString() : "—"}</div>
            {course.published_at && <div>Publié: {new Date(course.published_at).toLocaleDateString()}</div>}
            {course.modifier_name && <div>Modifié par: {course.modifier_name}</div>}
          </div>
          <button onClick={handleSaveCourse} disabled={saving}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 text-sm bg-navy-600 text-white rounded-lg hover:bg-navy-700 disabled:opacity-50">
            <Save className="w-4 h-4" /> {saving ? "Sauvegarde..." : "Enregistrer"}
          </button>
        </div>

        {/* Chapters */}
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {chapters.map(ch => (
            <div key={ch.id}
              className={`rounded cursor-pointer ${activeChapter === ch.id ? "bg-navy-50" : "hover:bg-gray-50"}`}>
              <div onClick={() => setActiveChapter(ch.id)} className="flex items-center gap-2 p-2">
                <GripVertical className="w-4 h-4 text-gray-400" />
                <div className="flex-1">
                  <input type="text" value={ch.title} onChange={e => handleUpdateChapterTitle(ch.id, e.target.value)}
                    onClick={e => e.stopPropagation()}
                    className="w-full text-sm font-medium bg-transparent border-none focus:outline-none" />
                  <span className="text-xs text-gray-400">{ch.lessons?.length || 0} leçons</span>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="p-3 border-t">
          <button onClick={handleAddChapter}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm border border-dashed rounded-lg hover:bg-gray-50">
            <Plus className="w-4 h-4" /> Nouveau chapitre
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {activeChapterData ? (
          <>
            <div className="p-4 border-b bg-white flex justify-between items-center">
              <div>
                <h3 className="font-semibold text-lg">{activeChapterData.title}</h3>
                <p className="text-sm text-gray-500">{activeChapterData.lessons?.length || 0} leçons</p>
              </div>
              <div className="flex gap-2">
                <button onClick={() => handleAddLesson(activeChapterData.id)}
                  className="flex items-center gap-1 px-3 py-2 text-sm bg-navy-600 text-white rounded-lg hover:bg-navy-700">
                  <Plus className="w-4 h-4" /> Ajouter leçon
                </button>
                <button onClick={() => handleDeleteChapter(activeChapterData.id)}
                  className="p-2 text-red-600 hover:bg-red-50 rounded-lg">
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-4">
              {!activeChapterData.lessons?.length ? (
                <div className="text-center py-20 text-gray-500">
                  <FileText className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                  <p>Aucune leçon. Cliquez sur "Ajouter leçon" !</p>
                </div>
              ) : (
                <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
                  {activeChapterData.lessons.map((lesson: Lesson) => (
                    <div key={lesson.id}
                      onClick={() => openLessonEditor(lesson)}
                      className={`p-4 rounded-lg border-2 cursor-pointer hover:border-navy-300 transition-colors ${getLessonBg(lesson.lesson_type)}`}>
                      <div className="flex items-center gap-2 mb-2">
                        {getLessonIcon(lesson.lesson_type)}
                        <span className="text-xs font-medium">
                          {LESSON_TYPES.find(t => t.value === lesson.lesson_type)?.label || lesson.lesson_type}
                        </span>
                      </div>
                      <h4 className="font-medium text-sm line-clamp-1">{lesson.title}</h4>
                      <div className="flex justify-between items-center mt-2">
                        <span className="text-xs opacity-70">{lesson.duration_minutes} min</span>
                        <button onClick={e => { e.stopPropagation(); handleDeleteLesson(activeChapterData.id, lesson.id); }}
                          className="p-1 rounded hover:bg-white/50">
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-500">
            <div className="text-center">
              <ChevronDown className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p>Sélectionnez un chapitre</p>
              {chapters.length === 0 && (
                <button onClick={handleAddChapter} className="mt-4 px-4 py-2 bg-navy-600 text-white rounded-lg hover:bg-navy-700">
                  Créer le premier chapitre
                </button>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Lesson Editor Modal */}
      {showLessonEditor && activeLesson && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="p-4 border-b sticky top-0 bg-white flex justify-between items-center">
              <h3 className="font-semibold text-lg">Éditer la leçon</h3>
              <button onClick={() => setShowLessonEditor(false)} className="p-1 hover:bg-gray-100 rounded">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-4 space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Type de contenu</label>
                <div className="grid grid-cols-3 gap-2">
                  {LESSON_TYPES.map(t => {
                    const Icon = t.icon;
                    return (
                      <button key={t.value}
                        onClick={() => setEditLessonForm({ ...editLessonForm, lesson_type: t.value })}
                        className={`p-3 rounded-lg border-2 flex flex-col items-center gap-2 ${
                          editLessonForm.lesson_type === t.value ? "border-navy-600 bg-navy-50" : "border-gray-200 hover:border-gray-300"
                        }`}>
                        <Icon className="w-5 h-5" />
                        <span className="text-sm">{t.label}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Titre</label>
                <input type="text" value={editLessonForm.title}
                  onChange={e => setEditLessonForm({ ...editLessonForm, title: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg" />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Durée (minutes)</label>
                <input type="number" value={editLessonForm.duration_minutes}
                  onChange={e => setEditLessonForm({ ...editLessonForm, duration_minutes: Number(e.target.value) })}
                  className="w-full px-3 py-2 border rounded-lg" />
              </div>

              <div className="flex items-center gap-2">
                <input type="checkbox" checked={editLessonForm.is_free}
                  onChange={e => setEditLessonForm({ ...editLessonForm, is_free: e.target.checked })}
                  className="w-4 h-4" />
                <label className="text-sm">Leçon gratuite (visible sans inscription)</label>
              </div>

              {editLessonForm.lesson_type === "text" && (
                <div>
                  <label className="block text-sm font-medium mb-1">Contenu texte</label>
                  <textarea value={editLessonForm.content_text}
                    onChange={e => setEditLessonForm({ ...editLessonForm, content_text: e.target.value })}
                    className="w-full px-3 py-2 border rounded-lg font-mono text-sm" rows={10}
                    placeholder="Entrez le contenu de la leçon..." />
                </div>
              )}

              {editLessonForm.lesson_type === "video" && (
                <div>
                  <label className="block text-sm font-medium mb-1">URL Vidéo</label>
                  <input type="url" value={editLessonForm.video_url}
                    onChange={e => setEditLessonForm({ ...editLessonForm, video_url: e.target.value })}
                    className="w-full px-3 py-2 border rounded-lg" placeholder="https://..." />
                  <p className="text-xs text-gray-500 mt-1">MP4, YouTube, Vimeo...</p>
                </div>
              )}

              {editLessonForm.lesson_type === "pdf" && (
                <div>
                  <label className="block text-sm font-medium mb-1">URL PDF</label>
                  <input type="url" value={editLessonForm.pdf_url}
                    onChange={e => setEditLessonForm({ ...editLessonForm, pdf_url: e.target.value })}
                    className="w-full px-3 py-2 border rounded-lg" placeholder="https://.../file.pdf" />
                </div>
              )}

              {editLessonForm.lesson_type === "image" && (
                <div>
                  <label className="block text-sm font-medium mb-1">URLs Images (une par ligne ou JSON)</label>
                  <textarea value={editLessonForm.image_urls}
                    onChange={e => setEditLessonForm({ ...editLessonForm, image_urls: e.target.value })}
                    className="w-full px-3 py-2 border rounded-lg font-mono text-sm" rows={3}
                    placeholder="https://image1.jpg&#10;https://image2.jpg" />
                </div>
              )}

              {editLessonForm.lesson_type === "link" && (
                <>
                  <div>
                    <label className="block text-sm font-medium mb-1">Titre du lien</label>
                    <input type="text" value={editLessonForm.link_title}
                      onChange={e => setEditLessonForm({ ...editLessonForm, link_title: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">URL</label>
                    <input type="url" value={editLessonForm.link_url}
                      onChange={e => setEditLessonForm({ ...editLessonForm, link_url: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg" placeholder="https://..." />
                  </div>
                </>
              )}

              {editLessonForm.lesson_type === "quiz" && (
                <div className="p-4 bg-orange-50 rounded-lg">
                  <p className="text-sm">Quiz/Examen — Configurez le quiz dans l'éditeur de quiz.</p>
                </div>
              )}
            </div>

            <div className="p-4 border-t sticky bottom-0 bg-white flex justify-end gap-2">
              <button onClick={() => setShowLessonEditor(false)} className="px-4 py-2 border rounded-lg hover:bg-gray-50">
                Annuler
              </button>
              <button onClick={handleSaveLesson}
                className="flex items-center gap-2 px-4 py-2 bg-navy-600 text-white rounded-lg hover:bg-navy-700">
                <Save className="w-4 h-4" /> Enregistrer
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Course Preview Modal */}
      {previewCourse && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={() => setPreviewCourse(null)}>
          <div className="bg-white rounded-2xl w-full max-w-3xl max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <div className="p-4 border-b sticky top-0 bg-white flex justify-between items-center z-10">
              <h3 className="font-semibold text-lg">Aperçu du cours</h3>
              <button onClick={() => setPreviewCourse(null)} className="p-1 hover:bg-gray-100 rounded">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6">
              {previewCourse.cover_url && (
                <img src={previewCourse.cover_url} alt="" className="w-full h-48 object-cover rounded-xl mb-4" />
              )}
              <div className="flex items-center gap-2 mb-2">
                <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${
                  previewCourse.status === "published" ? "bg-green-100 text-green-800" :
                  previewCourse.status === "archived" ? "bg-orange-100 text-orange-700" : "bg-yellow-100 text-yellow-800"
                }`}>
                  {previewCourse.status === "published" ? "Publié" : previewCourse.status === "archived" ? "Archivé" : "Brouillon"}
                </span>
                <span className="text-xs text-gray-500">{previewCourse.level}</span>
                {previewCourse.category && <span className="text-xs text-gray-500">/ {previewCourse.category}</span>}
              </div>
              <h2 className="text-2xl font-bold text-navy mb-2">{previewCourse.title}</h2>
              {previewCourse.short_description && <p className="text-gray-600 mb-4">{previewCourse.short_description}</p>}
              {previewCourse.description && <p className="text-gray-600 mb-4">{previewCourse.description}</p>}
              <div className="grid grid-cols-3 gap-4 mb-6 text-sm">
                <div className="bg-gray-50 rounded-lg p-3 text-center">
                  <div className="font-bold text-navy">{previewCourse.total_modules}</div>
                  <div className="text-gray-500">Chapitres</div>
                </div>
                <div className="bg-gray-50 rounded-lg p-3 text-center">
                  <div className="font-bold text-navy">{previewCourse.total_lessons}</div>
                  <div className="text-gray-500">Leçons</div>
                </div>
                <div className="bg-gray-50 rounded-lg p-3 text-center">
                  <div className="font-bold text-navy">{previewCourse.total_duration_minutes || 0} min</div>
                  <div className="text-gray-500">Durée</div>
                </div>
              </div>
              {previewCourse.prerequisites && (
                <div className="mb-4">
                  <h4 className="font-medium text-sm mb-1">Prérequis</h4>
                  <p className="text-sm text-gray-600">{previewCourse.prerequisites}</p>
                </div>
              )}
              {previewCourse.learning_objectives && (
                <div className="mb-4">
                  <h4 className="font-medium text-sm mb-1">Objectifs pédagogiques</h4>
                  <p className="text-sm text-gray-600">{previewCourse.learning_objectives}</p>
                </div>
              )}
              {previewCourse.modules?.length > 0 && (
                <div>
                  <h4 className="font-medium text-sm mb-2">Programme du cours</h4>
                  <div className="space-y-3">
                    {previewCourse.modules.map((mod: any, idx: number) => (
                      <div key={mod.id} className="border rounded-lg p-3">
                        <div className="font-medium text-sm flex items-center gap-2">
                          <span className="bg-navy text-white text-xs w-6 h-6 rounded-full flex items-center justify-center">{idx + 1}</span>
                          {mod.title}
                        </div>
                        {mod.lessons?.length > 0 && (
                          <div className="ml-8 mt-2 space-y-1">
                            {mod.lessons.map((les: any) => (
                              <div key={les.id} className="flex items-center gap-2 text-xs text-gray-600">
                                <FileText className="w-3 h-3" />
                                {les.title}
                                {les.is_free && <span className="text-green-600">(Gratuit)</span>}
                                <span className="text-gray-400">{les.duration_minutes} min</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Toast */}
      {toast.show && (
        <div className={`fixed top-6 right-6 z-50 px-6 py-4 rounded-xl shadow-lg text-white flex items-center gap-2 ${toast.type === "success" ? "bg-green-500" : "bg-red-500"}`}>
          {toast.type === "success" ? <CheckCircle className="w-5 h-5" /> : <AlertCircle className="w-5 h-5" />}
          {toast.message}
        </div>
      )}
    </div>
  );
}
