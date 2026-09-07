// Course Player Page - Learner View
import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import {
  ArrowLeft, ArrowRight, Menu, X, CheckCircle, Circle,
  FileText, Video, HelpCircle, File, FileCode, BookmarkPlus, StickyNote,
  Clock, Award, ChevronDown, Play, MessageSquare, Download
} from "lucide-react";
import { lessonLearner, quizLearner } from "../../api";
const learnerAPI = {
  lesson: lessonLearner.get,
  updateProgress: lessonLearner.progress,
  startQuiz: quizLearner.start,
  submitQuiz: quizLearner.submit,
  certificates: quizLearner.certificates,
  certificate: quizLearner.certificate,
  getCourseCertificate: (id: number) => lessonLearner.get(id),
  syllabus: (id: number) => import("../../api").then(m => m.courseLearner.syllabus(id)),
};
import { jsPDF } from "jspdf";
import DOMPurify from "dompurify";
import { tokenStorage } from "../../utils/tokenStorage";
// Correction E2 : /learn/* est hors DashboardLayout → l'UpsellModal globale n'est pas
// montée. On monte une instance locale et on enregistre le handler global au montage,
// pour que tout 402 (ABAC ou quota Freemium) sur ces routes déclenche la modale d'upsell.
import UpsellModal, { setUpsellHandler, triggerUpsell } from "../../components/UpsellModal";

const BASE_URL = import.meta.env.VITE_API_URL || "";

function getToken() { return tokenStorage.getToken(); }

function extractUpsell(detail: any): { message?: string; requiredPack?: string } | null {
  if (!detail) return null;
  if (typeof detail === "object") {
    if (detail.message || detail.required_pack) {
      return { message: detail.message, requiredPack: detail.required_pack };
    }
    return null;
  }
  if (/pack|abonnement|premium/i.test(detail)) return { message: detail };
  return null;
}

async function apiFetch(path: string, options: RequestInit = {}) {
  const token = getToken();
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    const detail = err.detail;
    // 402 structuré (ABAC / Freemium) → déclenche l'UpsellModal enregistrée
    if (res.status === 402) {
      const upsell = extractUpsell(detail);
      triggerUpsell(
        upsell?.message ?? (typeof detail === "string" ? detail : "Contenu premium requis."),
        upsell?.requiredPack,
      );
    }
    const msg = typeof detail === "string"
      ? detail
      : detail?.message ?? `Erreur ${res.status}`;
    throw new Error(msg);
  }
  return res.json();
}

function isYouTubeUrl(url: string): boolean {
  return /youtube\.com\/embed\/|youtu\.be\/|youtube\.com\/watch/.test(url);
}

function getYouTubeEmbedUrl(url: string): string {
  const match = url.match(/(?:youtube\.com\/embed\/|youtu\.be\/|youtube\.com\/watch\?v=)([\w-]+)/);
  return match ? `https://www.youtube.com/embed/${match[1]}` : url;
}

export default function CoursePlayerPage() {
  const { courseId, lessonId } = useParams();
  const navigate = useNavigate();
  const [syllabus, setSyllabus] = useState<any[]>([]);
  const [courseInfo, setCourseInfo] = useState<any>(null);
  const [currentLesson, setCurrentLesson] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [completedLessons, setCompletedLessons] = useState<Set<number>>(new Set());
  const [progressPercent, setProgressPercent] = useState(0);
  const [showNotes, setShowNotes] = useState(false);
  const [notes, setNotes] = useState<any[]>([]);
  const [noteText, setNoteText] = useState("");
  const [showQuiz, setShowQuiz] = useState(false);
  const [quizData, setQuizData] = useState<any>(null);
  const [attemptId, setAttemptId] = useState<number | null>(null);
  const [quizAnswers, setQuizAnswers] = useState<Record<number, number[]>>({});
  const [quizResult, setQuizResult] = useState<any>(null);
  const [quizSubmitting, setQuizSubmitting] = useState(false);
  const [certificate, setCertificate] = useState<any>(null);
  const [certLoading, setCertLoading] = useState(false);
  // Correction E2 : instance locale de l'UpsellModal pour les routes /learn/*
  const [upsell, setUpsell] = useState<{ isOpen: boolean; message?: string; requiredPack?: string }>({ isOpen: false });
  const videoRef = useRef<HTMLVideoElement>(null);
  const lessonRefs = useRef<Record<number, HTMLDivElement | null>>({});
  const loadedModuleIdRef = useRef<number | null>(null);
  const [chapterLessons, setChapterLessons] = useState<any[]>([]);
  const [chapterLoading, setChapterLoading] = useState(false);

  // Chapitre (module) actif : celui qui contient la leçon sélectionnée.
  const activeModule = useMemo(
    () => syllabus.find((ch: any) => (ch.lessons || []).some((l: any) => l.id === Number(lessonId))) || null,
    [syllabus, lessonId]
  );

  useEffect(() => {
    if (courseId) { loadCourse(); loadSyllabus(); }
  }, [courseId]);
  useEffect(() => { if (lessonId && !loading) { loadLessonContent(); } }, [lessonId, loading]);

  // Correction E2 : enregistre le handler global au montage (apiFetch → triggerUpsell),
  // et déregistre au démontage (comme DashboardLayout.tsx).
  useEffect(() => {
    setUpsellHandler((message, requiredPack) =>
      setUpsell({ isOpen: true, message, requiredPack })
    );
    return () => setUpsellHandler(() => {});
  }, []);

  const closeUpsell = () => setUpsell((s) => ({ ...s, isOpen: false }));

  const loadCourse = async () => {
    try {
      const data = await apiFetch(`/api/learner/courses/${courseId}`);
      setCourseInfo(data);
      await checkCertificate();
    } catch (e) { console.error(e); }
  };

  const checkCertificate = async () => {
    try {
      setCertLoading(true);
      const data = await learnerAPI.getCourseCertificate(Number(courseId));
      setCertificate(data);
    } catch { setCertificate(null); }
    finally { setCertLoading(false); }
  };

  const downloadCertificate = () => {
    if (!certificate) return;
    const doc = new jsPDF({ orientation: "landscape", unit: "mm", format: "a4" });
    const pageW = doc.internal.pageSize.getWidth();
    const pageH = doc.internal.pageSize.getHeight();
    doc.setFillColor(250, 250, 255);
    doc.rect(0, 0, pageW, pageH, "F");
    doc.setDrawColor(37, 99, 235);
    doc.setLineWidth(2);
    doc.rect(10, 10, pageW - 20, pageH - 20);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(32);
    doc.setTextColor(37, 99, 235);
    doc.text("CERTIFICATE OF COMPLETION", pageW / 2, 45, { align: "center" });
    doc.setFont("helvetica", "normal");
    doc.setFontSize(14);
    doc.setTextColor(100, 100, 100);
    doc.text("This is to certify that", pageW / 2, 65, { align: "center" });
    doc.setFont("helvetica", "bold");
    doc.setFontSize(24);
    doc.setTextColor(30, 30, 30);
    doc.text(certificate.student_name || "Student", pageW / 2, 80, { align: "center" });
    doc.setFont("helvetica", "normal");
    doc.setFontSize(14);
    doc.setTextColor(100, 100, 100);
    doc.text("has successfully completed the course", pageW / 2, 95, { align: "center" });
    doc.setFont("helvetica", "bold");
    doc.setFontSize(20);
    doc.setTextColor(30, 30, 30);
    doc.text(certificate.course_name || courseInfo?.title || "Course", pageW / 2, 110, { align: "center" });
    doc.setFontSize(11);
    doc.setTextColor(120, 120, 120);
    doc.text(`Certificate No: ${certificate.certificate_number}`, pageW / 2, 130, { align: "center" });
    doc.text(`Verification: ${certificate.verification_code}`, pageW / 2, 138, { align: "center" });
    doc.text(`Issued: ${new Date(certificate.issue_date).toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" })}`, pageW / 2, 146, { align: "center" });
    doc.setFontSize(9);
    doc.text("EduAI Learning Platform", pageW / 2, pageH - 25, { align: "center" });
    doc.save(`certificate-${certificate.certificate_number}.pdf`);
  };

  const loadSyllabus = async () => {
    setLoading(true); setError(null);
    try {
      const data = await apiFetch(`/api/learner/courses/${courseId}/syllabus`);
      setSyllabus(Array.isArray(data) ? data : []);
      if (!lessonId && data.length > 0 && (data[0].lessons?.length || 0) > 0) {
        navigate(`/learn/courses/${courseId}/lessons/${data[0].lessons[0].id}`, { replace: true });
      }
    } catch (e: any) { setError(e.message || "Impossible de charger le syllabus"); }
    finally { setLoading(false); }
  };

  const loadLessonContent = async () => {
    if (!lessonId) return;
    try {
      setShowQuiz(false);
      setQuizResult(null);
      setQuizAnswers({});
      loadNotes(Number(lessonId));
      // Vue unifiée : on charge tout le chapitre (module) de la leçon sélectionnée.
      if (activeModule?.id) {
        if (loadedModuleIdRef.current !== activeModule.id) {
          loadedModuleIdRef.current = activeModule.id;
          setChapterLessons([]);
        }
        setChapterLoading(true);
        const results = await Promise.all(
          (activeModule.lessons || []).map((l: any) =>
            apiFetch(`/api/learner/lessons/${l.id}`).catch(() => null)
          )
        );
        const lessons = results.filter(Boolean);
        setChapterLessons(lessons);
        const selected = lessons.find((l: any) => l && l.id === Number(lessonId));
        if (selected) {
          setCurrentLesson(selected);
          setTimeout(() => {
            lessonRefs.current[Number(lessonId)]?.scrollIntoView({ behavior: "smooth", block: "start" });
          }, 50);
        } else if (results.some(Boolean)) {
          setError("Cette leçon n'est pas accessible pour le moment.");
        }
        setChapterLoading(false);
        return;
      }
      const data = await apiFetch(`/api/learner/lessons/${lessonId}`);
      setCurrentLesson(data);
    } catch (e: any) {
      setError(e.message || "Impossible de charger la leçon");
      setChapterLoading(false);
    }
  };

  const loadNotes = async (lid: number) => {
    try {
      const data = await apiFetch(`/api/learner/lessons/${lid}/notes`);
      setNotes(Array.isArray(data) ? data : []);
    } catch (e) { console.error(e); }
  };

  const saveNote = async () => {
    if (!noteText.trim() || !lessonId) return;
    try {
      await apiFetch(`/api/learner/lessons/${lessonId}/notes`, {
        method: "POST", body: JSON.stringify({ content: noteText }),
      });
      setNoteText("");
      loadNotes(Number(lessonId));
    } catch (e) { console.error(e); }
  };

  const markComplete = async () => {
    if (!currentLesson) return;
    try {
      const res = await apiFetch(`/api/learner/lessons/${currentLesson.id}/progress`, {
        method: "POST", body: JSON.stringify({ status: "completed" }),
      });
      setCompletedLessons(prev => new Set([...prev, currentLesson.id]));
      if (res.progress_percent !== undefined) setProgressPercent(res.progress_percent);
    } catch (e) { console.error(e); }
  };

  const completeLesson = async (lesson: any) => {
    if (!lesson) return;
    try {
      const res = await apiFetch(`/api/learner/lessons/${lesson.id}/progress`, {
        method: "POST", body: JSON.stringify({ status: "completed" }),
      });
      setCompletedLessons(prev => new Set([...prev, lesson.id]));
      if (res.progress_percent !== undefined) setProgressPercent(res.progress_percent);
    } catch (e) { console.error(e); }
  };

  const selectLessonSection = (lesson: any) => {
    setCurrentLesson(lesson);
    setTimeout(() => {
      lessonRefs.current[lesson.id]?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 50);
  };

  const startQuiz = async (lesson: any = currentLesson) => {
    const target = lesson || currentLesson;
    if (!target?.quiz) return;
    try {
      const res = await apiFetch(`/api/learner/quizzes/${target.quiz.id}/start`, { method: "POST" });
      setAttemptId(res.attempt_id);
      const quiz = await apiFetch(`/api/learner/quizzes/${target.quiz.id}`);
      setQuizData(quiz);
      setShowQuiz(true);
      setQuizAnswers({});
      setQuizResult(null);
    } catch (e) { console.error(e); }
  };

  const submitQuiz = async () => {
    if (!quizData || !attemptId) return;
    setQuizSubmitting(true);
    try {
      const answers = Object.entries(quizAnswers).map(([qid, optIds]) => ({
        question_id: Number(qid),
        selected_option_ids: optIds,
      }));
      const res = await apiFetch(`/api/learner/quizzes/${quizData.id}/submit`, {
        method: "POST",
        body: JSON.stringify({ attempt_id: attemptId, answers }),
      });
      setQuizResult(res);
      setCompletedLessons(prev => new Set([...prev, currentLesson.id]));
      if (res.progress_percent !== undefined) setProgressPercent(res.progress_percent);
    } catch (e) { console.error(e); }
    finally { setQuizSubmitting(false); }
  };

  const nextLesson = useCallback(() => {
    let found = false;
    for (const ch of syllabus) {
      for (const l of ch.lessons || []) {
        if (found) { navigate(`/learn/courses/${courseId}/lessons/${l.id}`); return; }
        if (l.id === currentLesson?.id) found = true;
      }
    }
  }, [syllabus, currentLesson, courseId, navigate]);

  const prevLesson = useCallback(() => {
    let prev = null;
    for (const ch of syllabus) {
      for (const l of ch.lessons || []) {
        if (l.id === currentLesson?.id) { if (prev) navigate(`/learn/courses/${courseId}/lessons/${prev.id}`); return; }
        prev = l;
      }
    }
  }, [syllabus, currentLesson, courseId, navigate]);

  const getIcon = (type: string) => {
    switch (type) {
      case "video": return <Video className="w-4 h-4" />;
      case "quiz": return <HelpCircle className="w-4 h-4" />;
      case "pdf": return <File className="w-4 h-4" />;
      case "html": return <FileCode className="w-4 h-4" />;
      case "link": return <FileText className="w-4 h-4" />;
      default: return <FileText className="w-4 h-4" />;
    }
  };

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-navy-600 mx-auto mb-4"></div>
        <p className="text-gray-500">Chargement du cours...</p>
      </div>
    </div>
  );

  if (error) return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center max-w-md p-8">
        <h2 className="text-xl font-semibold text-red-500 mb-2">Erreur</h2>
        <p className="text-gray-600 mb-6">{error}</p>
        <div className="space-x-4">
          <button onClick={loadSyllabus} className="px-4 py-2 bg-navy-600 text-white rounded-lg hover:bg-navy-700">Réessayer</button>
          <Link to="/login" className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300">Connexion</Link>
        </div>
      </div>
    </div>
  );

  return (
    <div className="flex h-screen bg-cream">
      {/* Sidebar — thème EDUAI (navy) : seuls les chapitres sont listés */}
      <aside className={`${sidebarOpen ? "w-80" : "w-0"} bg-navy transition-all overflow-hidden flex flex-col`}>
        <div className="p-6 border-b border-white/10">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-2xl font-[300] text-white">
              EDU<span className="italic text-orange-l">AI</span>
            </h1>
            <button onClick={() => setSidebarOpen(false)} className="p-1.5 hover:bg-white/10 rounded-lg text-white/70">
              <X className="w-4 h-4" />
            </button>
          </div>
          <h2 className="text-white font-semibold text-lg leading-snug">{courseInfo?.title || "Programme"}</h2>
          {progressPercent > 0 && (
            <div className="w-full bg-white/10 rounded-full h-1.5 mt-3">
              <div className="bg-gradient-to-r from-orange to-orange-l h-1.5 rounded-full transition-all" style={{ width: `${progressPercent}%` }} />
            </div>
          )}
          <p className="text-white/50 text-xs mt-1">{progressPercent}% complété</p>
          {certLoading ? (
            <div className="mt-3 p-2 bg-white/10 rounded-lg text-xs text-orange-l text-center">Contrôle du certificat...</div>
          ) : certificate ? (
            <div className="mt-3 p-3 bg-white/10 rounded-xl border border-white/10">
              <div className="flex items-center gap-2 mb-1.5">
                <Award className="w-4 h-4 text-orange-l" />
                <span className="text-sm font-semibold text-orange-l">Certificat obtenu!</span>
              </div>
              <p className="text-xs text-white/60 mb-2">N° {certificate.certificate_number}</p>
              <button
                onClick={downloadCertificate}
                className="w-full flex items-center justify-center gap-1 px-3 py-1.5 bg-gradient-to-r from-orange to-orange-l text-white text-xs rounded-lg hover:opacity-90"
              >
                <Download className="w-3 h-3" />
                Télécharger PDF
              </button>
            </div>
          ) : null}
        </div>
        <div className="flex-1 overflow-y-auto">
          <p className="px-6 pt-4 pb-2 text-[11px] uppercase tracking-widest text-white/40">Chapitres</p>
          {syllabus.map((ch: any, ci: number) => {
            const lessons = ch.lessons || [];
            const done = lessons.filter((l: any) => completedLessons.has(l.id)).length;
            const allDone = lessons.length > 0 && done === lessons.length;
            const isActive = activeModule?.id === ch.id;
            return (
              <button
                key={ch.id}
                onClick={() => { const first = lessons[0]; if (first) navigate(`/learn/courses/${courseId}/lessons/${first.id}`); }}
                className={`w-full flex items-center gap-4 px-5 py-4 text-start transition-all ${
                  isActive
                    ? "bg-gradient-to-r from-orange to-orange-l text-white"
                    : "text-white/60 hover:bg-white/5 hover:text-white"
                }`}
              >
                <span className={`w-9 h-9 rounded-xl flex items-center justify-center font-bold text-sm flex-shrink-0 ${
                  isActive ? "bg-white/20 text-white" : "bg-white/10 text-orange-l"
                }`}>
                  {ci + 1}
                </span>
                <span className="flex-1 min-w-0">
                  <span className="block text-sm font-medium truncate">{ch.title || "Chapitre"}</span>
                  <span className={`block text-xs mt-0.5 ${isActive ? "text-white/80" : "text-white/40"}`}>
                    {lessons.length} élément{lessons.length > 1 ? "s" : ""} · {done}/{lessons.length} terminés
                  </span>
                </span>
                {allDone
                  ? <CheckCircle className="w-5 h-5 text-green-300 flex-shrink-0" />
                  : <Circle className="w-5 h-5 text-white/30 flex-shrink-0" />
                }
              </button>
            );
          })}
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        <header className="px-4 py-3 border-b border-black/5 bg-white flex items-center gap-3">
          <button onClick={() => navigate("/dashboard")} title="Retour au dashboard"
            className="p-2 hover:bg-gray-100 rounded-lg text-navy/60 hover:text-navy">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <button onClick={() => setSidebarOpen(true)} className="p-2 hover:bg-gray-100 rounded-lg"><Menu className="w-5 h-5" /></button>
          <div className="flex-1 min-w-0">
            <h1 className="text-navy text-lg font-semibold truncate">{activeModule?.title || currentLesson?.module_title || "Chapitre"}</h1>
            {activeModule?.description && <p className="text-xs text-gray-500 truncate hidden sm:block">{activeModule.description}</p>}
          </div>
          <div className="flex items-center gap-1">
            <button onClick={() => setShowNotes(!showNotes)} className={`p-2 rounded-lg ${showNotes ? "bg-orange/10 text-orange" : "hover:bg-gray-100 text-navy/60"}`}>
              <StickyNote className="w-5 h-5" />
            </button>
            <button onClick={prevLesson} className="p-2 hover:bg-gray-100 rounded-lg text-navy/60"><ArrowLeft className="w-5 h-5" /></button>
            <button onClick={nextLesson} className="p-2 hover:bg-gray-100 rounded-lg text-navy/60"><ArrowRight className="w-5 h-5" /></button>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto p-6 max-w-4xl mx-auto w-full">
          {chapterLoading && <div className="text-center py-20 text-gray-500">Chargement du chapitre...</div>}

          {!chapterLoading && !currentLesson && <div className="text-center py-20 text-gray-500">Sélectionnez un chapitre pour commencer.</div>}

          {!chapterLoading && currentLesson && (
            <>
              {/* Bannière du chapitre : les éléments ci-dessous forment une seule leçon */}
              {activeModule && (
                <div className="mb-8 p-8 bg-navy rounded-2xl border border-white/10 relative overflow-hidden">
                  <div className="absolute w-96 h-96 rounded-full bg-gradient-to-br from-orange/30 to-transparent -top-40 -right-20" />
                  <div className="relative z-10">
                    <p className="text-[11px] uppercase tracking-widest text-orange-l font-bold mb-2">Chapitre en une seule leçon</p>
                    <h2 className="text-3xl text-white mb-1">{activeModule.title}</h2>
                    {activeModule.description && <p className="text-white/60 text-sm">{activeModule.description}</p>}
                    <p className="text-white/40 text-xs mt-3">
                      {activeModule.lessons?.length || 0} éléments dans ce chapitre
                    </p>
                  </div>
                </div>
              )}

              {/* Tous les éléments du chapitre affichés sur la même page */}
              {(chapterLessons.length > 0 ? chapterLessons : [currentLesson]).map((lesson, li) => (
                <article
                  key={lesson.id}
                  ref={el => { lessonRefs.current[lesson.id] = el; }}
                  className={`mb-8 p-6 rounded-2xl border transition-all ${
                    lesson.id === Number(lessonId)
                      ? "bg-white border-orange/40 shadow-md"
                      : "bg-white border-black/5 shadow-sm"
                  }`}
                >
                  <header className="flex items-center gap-3 mb-5 pb-4 border-b border-black/5">
                    <span className="w-9 h-9 rounded-xl bg-gradient-to-r from-orange to-orange-l text-white flex items-center justify-center font-bold text-sm shadow-or">
                      {(li + 1)}
                    </span>
                    <div className="flex-1 min-w-0">
                      <h3 className="text-navy font-semibold text-lg truncate">{lesson.title || "Leçon"}</h3>
                      <div className="flex items-center gap-3 text-xs text-gray-500">
                        <span className="flex items-center gap-1">{getIcon(lesson.lesson_type)} <span>{lesson.lesson_type}</span></span>
                        <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> {lesson.duration_minutes || 0} min</span>
                      </div>
                    </div>
                    {completedLessons.has(lesson.id)
                      ? <CheckCircle className="w-6 h-6 text-green-500 flex-shrink-0" />
                      : <Circle className="w-6 h-6 text-gray-200 flex-shrink-0" />}
                  </header>

                  {/* Video */}
                  {lesson.lesson_type === "video" && lesson.video_url && (
                    <div className="mb-6">
                      {isYouTubeUrl(lesson.video_url) ? (
                        <iframe
                          src={getYouTubeEmbedUrl(lesson.video_url)}
                          className="w-full rounded-lg border"
                          style={{ height: "60vh" }}
                          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                          allowFullScreen
                          title={lesson.title}
                        />
                      ) : (
                        <video
                          ref={lesson.id === Number(lessonId) ? videoRef : undefined}
                          src={lesson.video_url}
                          controls
                          preload={lesson.id === Number(lessonId) ? "auto" : "metadata"}
                          className="w-full rounded-lg bg-black"
                          style={{ maxHeight: "60vh" }}
                          onEnded={() => {
                            const t = getToken();
                            if (t) apiFetch(`/api/learner/lessons/${lesson.id}/progress`, {
                              method: "POST", body: JSON.stringify({ video_completed: true }),
                            });
                          }}
                        />
                      )}
                      {lesson.video_duration_seconds && (
                        <p className="text-xs text-gray-500 mt-1 text-center">
                          Duree: {Math.floor(lesson.video_duration_seconds / 60)}:{String(lesson.video_duration_seconds % 60).padStart(2, '0')}
                        </p>
                      )}
                    </div>
                  )}

                  {/* PDF Viewer */}
                  {lesson.lesson_type === "pdf" && lesson.pdf_url && (
                    <div className="mb-6">
                      <embed src={lesson.pdf_url} type="application/pdf" className="w-full h-[70vh] rounded-lg border" />
                    </div>
                  )}

                  {/* HTML Page (code HTML rendu) */}
                  {lesson.lesson_type === "html" && lesson.content_html && (
                    <div className="mb-6">
                      <iframe
                        srcDoc={lesson.content_html}
                        className="w-full h-[70vh] rounded-lg border border-black/5 bg-white"
                        sandbox="allow-scripts allow-forms allow-popups allow-modals"
                        title={lesson.title || "Page HTML"}
                      />
                    </div>
                  )}

                  {/* Images */}
                  {lesson.lesson_type === "image" && lesson.image_urls && (
                    <div className="mb-6 space-y-4">
                      {(Array.isArray(lesson.image_urls) ? lesson.image_urls : JSON.parse(lesson.image_urls || "[]")).map((url: string, i: number) => (
                        <img key={i} src={url} alt="" className="w-full rounded-lg" />
                      ))}
                    </div>
                  )}

                  {/* Text Content */}
                  {lesson.content_html && lesson.lesson_type !== "html" && (
                    <div className="prose prose-navy max-w-none mb-6" dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(lesson.content_html) }} />
                  )}
                  {lesson.content_text && (
                    <div className="whitespace-pre-wrap text-gray-700 leading-relaxed mb-6">{lesson.content_text}</div>
                  )}

                  {/* External Link */}
                  {lesson.lesson_type === "link" && lesson.link_url && (
                    <div className="mb-6 p-6 bg-blue-50 rounded-lg border border-blue-100">
                      <p className="text-sm text-gray-600 mb-2">Ressource externe:</p>
                      <a href={lesson.link_url} target="_blank" rel="noopener noreferrer"
                        className="text-blue-600 hover:underline font-medium flex items-center gap-2">
                        {lesson.link_title || lesson.link_url} →
                      </a>
                    </div>
                  )}

                  {/* Document */}
                  {lesson.document_url && (
                    <div className="mb-6 p-4 bg-gray-50 rounded-lg border">
                      <a href={lesson.document_url} target="_blank" rel="noopener noreferrer"
                        className="flex items-center gap-3 text-navy-600 hover:text-navy-800">
                        <File className="w-5 h-5" />
                        <span className="font-medium">{lesson.document_type || "Document"}</span>
                        <span className="text-sm text-gray-500">(Ouvrir)</span>
                      </a>
                    </div>
                  )}

                  {/* Quiz Section */}
                  {lesson.quiz && !showQuiz && (
                    <div className="mt-6 p-6 bg-orange-p rounded-2xl border border-orange/15">
                      <div className="flex items-center gap-3 mb-3">
                        <HelpCircle className="w-6 h-6 text-orange" />
                        <div>
                          <h4 className="text-navy font-semibold">{lesson.quiz.title}</h4>
                          {lesson.quiz.description && <p className="text-sm text-gray-600">{lesson.quiz.description}</p>}
                        </div>
                      </div>
                      {lesson.quiz.time_limit_minutes && (
                        <p className="text-xs text-gray-500 mb-3 flex items-center gap-1">
                          <Clock className="w-3 h-3" /> {lesson.quiz.time_limit_minutes} min
                        </p>
                      )}
                      <button onClick={() => { selectLessonSection(lesson); startQuiz(lesson); }}
                        className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-orange to-orange-l text-white rounded-full hover:opacity-90 font-medium shadow-or">
                        <Play className="w-5 h-5" /> Commencer le quiz
                      </button>
                    </div>
                  )}

                  {/* Terminer cet élément */}
                  <div className="mt-6 pt-4 border-t border-black/5 flex items-center justify-end gap-2">
                    {completedLessons.has(lesson.id) ? (
                      <span className="flex items-center gap-1 text-sm text-green-600 font-medium">
                        <CheckCircle className="w-4 h-4" /> Terminé
                      </span>
                    ) : (
                      <button onClick={() => completeLesson(lesson)}
                        className="flex items-center gap-2 px-5 py-2.5 rounded-full text-sm font-medium bg-gradient-to-r from-orange to-orange-l text-white hover:opacity-90 shadow-or transition-all">
                        <CheckCircle className="w-4 h-4" /> Marquer comme terminé
                      </button>
                    )}
                  </div>
                </article>
              ))}

              {/* Quiz Player */}
              {showQuiz && quizData && !quizResult && (
                <div className="mt-4 p-6 bg-white rounded-xl border">
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="font-bold text-xl">{quizData.title}</h2>
                    <button onClick={() => setShowQuiz(false)} className="text-gray-400 hover:text-gray-600">✕</button>
                  </div>
                  {quizData.questions?.map((q: any, qi: number) => (
                    <div key={q.id} className="mb-6 p-4 bg-gray-50 rounded-lg">
                      <p className="font-medium mb-3">{qi + 1}. {q.question_text}</p>
                      <div className="space-y-2">
                        {q.options?.map((opt: any) => (
                          <label key={opt.id} className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer border transition-colors ${
                            quizAnswers[q.id]?.includes(opt.id) ? "border-navy-500 bg-navy-50" : "border-gray-200 hover:border-gray-300"
                          }`}>
                            <input type="checkbox" className="w-4 h-4"
                              checked={quizAnswers[q.id]?.includes(opt.id) || false}
                              onChange={(e) => {
                                setQuizAnswers(prev => {
                                  const curr = prev[q.id] || [];
                                  if (e.target.checked) return { ...prev, [q.id]: [...curr, opt.id] };
                                  return { ...prev, [q.id]: curr.filter((id: number) => id !== opt.id) };
                                });
                              }} />
                            <span>{opt.text}</span>
                          </label>
                        ))}
                      </div>
                    </div>
                  ))}
                  <button onClick={submitQuiz} disabled={quizSubmitting}
                    className="w-full py-3 bg-navy-600 text-white rounded-lg hover:bg-navy-700 font-medium disabled:opacity-50">
                    {quizSubmitting ? "Soumission..." : "Soumettre le quiz"}
                  </button>
                </div>
              )}

              {/* Quiz Result */}
              {quizResult && (
                <div className={`mt-4 p-6 rounded-xl border ${quizResult.passed ? "bg-green-50 border-green-200" : "bg-red-50 border-red-200"}`}>
                  <div className="flex items-center gap-3 mb-4">
                    <Award className={`w-8 h-8 ${quizResult.passed ? "text-green-600" : "text-red-600"}`} />
                    <div>
                      <h3 className={`font-bold text-xl ${quizResult.passed ? "text-green-700" : "text-red-700"}`}>
                        {quizResult.passed ? "Félicitations ! Quiz réussi !" : "Quiz non réussi"}
                      </h3>
                      <p className="text-sm text-gray-500">{quizResult.correct_count}/{quizResult.total_count} bonnes réponses</p>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div className="text-center p-4 bg-white rounded-lg border">
                      <p className="text-3xl font-bold text-navy-600">{quizResult.score_percent}%</p>
                      <p className="text-xs text-gray-500">Score</p>
                    </div>
                    <div className="text-center p-4 bg-white rounded-lg border">
                      <p className="text-3xl font-bold text-green-600">{quizResult.correct_count}</p>
                      <p className="text-xs text-gray-500">Réussies</p>
                    </div>
                  </div>
                  {!quizResult.passed && (
                    <button onClick={() => startQuiz()} className="w-full py-2 bg-gray-200 rounded-lg hover:bg-gray-300">
                      Réessayer
                    </button>
                  )}
                  {quizResult.passed && (
                    <button onClick={() => setShowQuiz(false)} className="w-full py-2 bg-green-500 text-white rounded-lg hover:bg-green-600">
                      Continuer le cours
                    </button>
                  )}
                </div>
              )}
            </>
          )}
        </div>

        {/* Notes Panel */}
        {showNotes && (
          <div className="absolute right-0 top-0 h-full w-80 bg-white border-l shadow-xl p-4 overflow-y-auto z-10">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold flex items-center gap-2"><StickyNote className="w-4 h-4" /> Notes</h3>
              <button onClick={() => setShowNotes(false)} className="text-gray-400 hover:text-gray-600">✕</button>
            </div>
            <textarea value={noteText} onChange={e => setNoteText(e.target.value)} rows={3}
              className="w-full p-2 border rounded-lg text-sm mb-2" placeholder="Écrire une note..." />
            <button onClick={saveNote} disabled={!noteText.trim()}
              className="w-full py-2 bg-navy-600 text-white text-sm rounded-lg hover:bg-navy-700 disabled:opacity-50 mb-4">
              Sauvegarder
            </button>
            <div className="space-y-3">
              {notes.map((n: any) => (
                <div key={n.id} className="p-3 bg-gray-50 rounded-lg text-sm">
                  <p className="text-gray-700 whitespace-pre-wrap">{n.content}</p>
                  <p className="text-xs text-gray-400 mt-1">
                    {n.created_at ? new Date(n.created_at).toLocaleString("fr-FR") : ""}
                  </p>
                </div>
              ))}
              {notes.length === 0 && <p className="text-sm text-gray-400 text-center">Aucune note</p>}
            </div>
          </div>
        )}

        {/* Footer Actions */}
        {currentLesson && !showQuiz && (
          <div className="px-6 py-4 border-t border-black/5 bg-white flex items-center justify-between gap-4">
            <button onClick={prevLesson}
              className="flex items-center gap-2 px-5 py-3 rounded-full font-medium bg-cream-m text-navy hover:bg-orange-p transition-colors">
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div className="flex items-center gap-3">
              <button onClick={markComplete} disabled={completedLessons.has(currentLesson.id)}
                className={`flex items-center gap-2 px-6 py-3 rounded-full font-medium transition-all ${
                  completedLessons.has(currentLesson.id)
                    ? "bg-green-500 text-white cursor-default"
                    : "bg-gradient-to-r from-orange to-orange-l text-white hover:opacity-90 shadow-or"
                }`}>
                <CheckCircle className="w-5 h-5" />
                {completedLessons.has(currentLesson.id) ? "Terminé" : "Marquer comme terminé"}
              </button>
              <button onClick={startQuiz}
                className={`flex items-center gap-2 px-5 py-3 rounded-full font-medium bg-navy text-white hover:bg-navy-m ${
                  syllabus.some((ch) => ch.lessons?.some((l: any) => l.id === currentLesson.id && l.has_quiz)) ? "" : "hidden"
                }`}>
                <HelpCircle className="w-5 h-5" /> Quiz
              </button>
              <button onClick={nextLesson}
                className="flex items-center gap-2 px-5 py-3 rounded-full font-medium bg-navy text-white hover:bg-navy-m">
                Suivant <ArrowRight className="w-5 h-5" />
              </button>
            </div>
          </div>
        )}
      </main>

      {/* Correction E2 : UpsellModal montée sur /learn/* — déclenchée par les 402 d'apiFetch */}
      <UpsellModal
        isOpen={upsell.isOpen}
        onClose={closeUpsell}
        message={upsell.message}
        requiredPack={upsell.requiredPack}
      />
    </div>
  );
}