import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { courseAdmin, chapterAdmin, lessonAdmin } from "../../../api";

export interface Lesson {
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

export interface Chapter {
  id: number;
  title: string;
  order: number;
  lessons: Lesson[];
}

export interface LessonForm {
  title: string;
  description: string;
  lesson_type: string;
  content_text: string;
  video_url: string;
  pdf_url: string;
  image_urls: string;
  link_url: string;
  link_title: string;
  duration_minutes: number;
  is_free: boolean;
}

const EMPTY_FORM: LessonForm = {
  title: "", description: "", lesson_type: "text", content_text: "",
  video_url: "", pdf_url: "", image_urls: "", link_url: "", link_title: "",
  duration_minutes: 0, is_free: false,
};

interface Toast {
  show: boolean;
  message: string;
  type: "success" | "error";
}

export function useCourseEditor(courseId: string | undefined) {
  const navigate = useNavigate();
  const [course, setCourse] = useState<any>(null);
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [activeChapter, setActiveChapter] = useState<number | null>(null);
  const [showLessonEditor, setShowLessonEditor] = useState(false);
  const [activeLesson, setActiveLesson] = useState<Lesson | null>(null);
  const [toast, setToast] = useState<Toast>({ show: false, message: "", type: "success" });
  const [publishErrors, setPublishErrors] = useState<string[]>([]);
  const [previewCourse, setPreviewCourse] = useState<any>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [editLessonForm, setEditLessonForm] = useState<LessonForm>(EMPTY_FORM);

  const showToast = useCallback((message: string, type: "success" | "error" = "success") => {
    setToast({ show: true, message, type });
    setTimeout(() => setToast({ show: false, message: "", type: "success" }), 3500);
  }, []);

  const loadCourse = useCallback(async () => {
    if (!courseId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await courseAdmin.get(Number(courseId));
      setCourse(data);
      const chs = data.chapters || [];
      setChapters(chs);
      if (chs.length > 0) setActiveChapter(chs[0].id);
    } catch (e: any) {
      console.error(e);
      setError(e.message || "Failed to load course.");
    } finally {
      setLoading(false);
    }
  }, [courseId]);

  useEffect(() => { loadCourse(); }, [loadCourse]);

  const handleSaveCourse = useCallback(async () => {
    if (!courseId || !course) return;
    setSaving(true);
    try {
      const tagsArray = course.tags
        ? (typeof course.tags === "string" ? JSON.parse(course.tags) : course.tags)
        : [];
      await courseAdmin.update(Number(courseId), {
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
        category_cible: course.category_cible || "Scolaire",
        niveau_scolaire: course.niveau_scolaire || null,
        tag_pack_requis: course.tag_pack_requis || "Basic",
      });
      showToast("Cours enregistré avec succès");
    } catch (e: any) {
      showToast("Erreur: " + e.message, "error");
    } finally {
      setSaving(false);
    }
  }, [courseId, course, showToast]);

  const handlePublish = useCallback(async () => {
    if (!courseId) return;
    setSaving(true);
    setPublishErrors([]);
    try {
      await courseAdmin.publish(Number(courseId));
      showToast("Cours publié avec succès!");
      loadCourse();
    } catch (e: any) {
      const msg = e.message || "";
      try {
        const errData = JSON.parse(msg);
        if (errData.errors?.length) setPublishErrors(errData.errors);
        else if (errData.message) setPublishErrors([errData.message]);
        else setPublishErrors([msg]);
      } catch {
        setPublishErrors([msg || "Erreur inconnue"]);
      }
    } finally {
      setSaving(false);
    }
  }, [courseId, loadCourse, showToast]);

  const handleUnpublish = useCallback(async () => {
    if (!courseId) return;
    setSaving(true);
    try {
      await courseAdmin.unpublish(Number(courseId));
      showToast("Cours dépublié");
      loadCourse();
    } catch (e: any) {
      showToast("Erreur: " + e.message, "error");
    } finally {
      setSaving(false);
    }
  }, [courseId, loadCourse, showToast]);

  const handleArchive = useCallback(async () => {
    if (!courseId) return;
    if (!confirm("Archiver ce cours ? Il ne sera plus visible par les apprenants.")) return;
    setSaving(true);
    try {
      await courseAdmin.archive(Number(courseId));
      showToast("Cours archivé");
      loadCourse();
    } catch (e: any) {
      showToast("Erreur: " + e.message, "error");
    } finally {
      setSaving(false);
    }
  }, [courseId, loadCourse, showToast]);

  const handlePreview = useCallback(async () => {
    if (!courseId) return;
    setPreviewLoading(true);
    try {
      const data = await courseAdmin.preview(Number(courseId));
      setPreviewCourse(data);
    } catch (e: any) {
      showToast("Erreur aperçu: " + e.message, "error");
    }
    setPreviewLoading(false);
  }, [courseId, showToast]);

  const handleDuplicate = useCallback(async () => {
    if (!courseId) return;
    if (!confirm("Dupliquer ce cours ? Une copie sera créée en brouillon.")) return;
    setSaving(true);
    try {
      await courseAdmin.duplicate(Number(courseId));
      showToast("Cours dupliqué!");
      navigate("/dashboard/admin/courses");
    } catch (e: any) {
      showToast("Erreur: " + e.message, "error");
    } finally {
      setSaving(false);
    }
  }, [courseId, navigate, showToast]);

  const handleAddChapter = useCallback(async () => {
    if (!courseId) return;
    try {
      const created = await chapterAdmin.create(Number(courseId), { title: `Chapitre ${chapters.length + 1}` });
      setChapters([...chapters, { ...created, lessons: [] }]);
      setActiveChapter(created.id);
      showToast("Chapitre ajouté");
    } catch (e) {
      console.error(e);
      showToast("Erreur ajout chapitre", "error");
    }
  }, [courseId, chapters, showToast]);

  const handleUpdateChapterTitle = useCallback(async (id: number, title: string) => {
    if (!courseId) return;
    try {
      await chapterAdmin.update(Number(courseId), id, { title });
      setChapters(chapters.map(c => c.id === id ? { ...c, title } : c));
    } catch (e) {
      console.error(e);
    }
  }, [courseId, chapters]);

  const handleDeleteChapter = useCallback(async (id: number) => {
    if (!courseId) return;
    if (!confirm("Supprimer ce chapitre et toutes ses leçons ?")) return;
    try {
      await chapterAdmin.delete(Number(courseId), id);
      setChapters(chapters.filter(c => c.id !== id));
      if (activeChapter === id) setActiveChapter(null);
      showToast("Chapitre supprimé");
    } catch (e) {
      console.error(e);
      showToast("Erreur suppression", "error");
    }
  }, [courseId, chapters, activeChapter, showToast]);

  const handleAddLesson = useCallback(async (chapterId: number) => {
    try {
      const created = await lessonAdmin.create(chapterId, { title: "Nouvelle leçon", lesson_type: "text", order: 0 });
      setChapters(chapters.map(c =>
        c.id === chapterId ? { ...c, lessons: [...(c.lessons || []), created] } : c
      ));
      setActiveLesson(created);
      setEditLessonForm({ ...EMPTY_FORM, title: created.title });
      setShowLessonEditor(true);
    } catch (e) {
      console.error(e);
      showToast("Erreur ajout leçon", "error");
    }
  }, [chapters, showToast]);

  const openLessonEditor = useCallback((lesson: Lesson) => {
    setActiveLesson(lesson);
    setEditLessonForm({
      title: lesson.title,
      description: lesson.description || "",
      lesson_type: lesson.lesson_type || "text",
      content_text: lesson.content_text || "",
      video_url: lesson.video_url || "",
      pdf_url: lesson.pdf_url || "",
      image_urls: lesson.image_urls
        ? (typeof lesson.image_urls === "string" ? lesson.image_urls : JSON.stringify(lesson.image_urls))
        : "[]",
      link_url: lesson.link_url || "",
      link_title: lesson.link_title || "",
      duration_minutes: lesson.duration_minutes || 0,
      is_free: lesson.is_free || false,
    });
    setShowLessonEditor(true);
  }, []);

  const handleSaveLesson = useCallback(async () => {
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
      await lessonAdmin.update(activeLesson.id, data);
      setChapters(chapters.map(c => ({
        ...c,
        lessons: c.lessons?.map((l: Lesson) => l.id === activeLesson.id ? { ...l, ...editLessonForm } : l),
      })));
      setShowLessonEditor(false);
      showToast("Leçon enregistrée");
    } catch (e) {
      console.error(e);
      showToast("Erreur enregistrement leçon", "error");
    }
  }, [activeLesson, editLessonForm, chapters, showToast]);

  const handleDeleteLesson = useCallback(async (chapterId: number, lessonId: number) => {
    if (!confirm("Supprimer cette leçon ?")) return;
    try {
      await lessonAdmin.delete(lessonId);
      setChapters(chapters.map(c =>
        c.id === chapterId ? { ...c, lessons: c.lessons.filter((l: Lesson) => l.id !== lessonId) } : c
      ));
      showToast("Leçon supprimée");
    } catch (e) {
      console.error(e);
      showToast("Erreur suppression", "error");
    }
  }, [chapters, showToast]);

  const updateCourseField = useCallback((field: string, value: any) => {
    setCourse((prev: any) => ({ ...prev, [field]: value }));
  }, []);

  return {
    course, chapters, loading, error, saving,
    activeChapter, setActiveChapter,
    showLessonEditor, setShowLessonEditor,
    activeLesson, editLessonForm, setEditLessonForm,
    toast, publishErrors, previewCourse, previewLoading,
    loadCourse, handleSaveCourse, handlePublish, handleUnpublish,
    handleArchive, handlePreview, handleDuplicate,
    handleAddChapter, handleUpdateChapterTitle, handleDeleteChapter,
    handleAddLesson, openLessonEditor, handleSaveLesson, handleDeleteLesson,
    updateCourseField,
  };
}
