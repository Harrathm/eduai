// Course Player Page - Learner View
import { useState, useEffect, useRef, useCallback } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import {
  ArrowLeft, ArrowRight, Menu, X, CheckCircle, Circle,
  FileText, Video, HelpCircle, File, BookmarkPlus, StickyNote,
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

const BASE_URL = import.meta.env.VITE_API_URL || "";

function getToken() { return tokenStorage.getToken(); }

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
    throw new Error(err.detail || `Erreur ${res.status}`);
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
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => { if (courseId) { loadCourse(); loadSyllabus(); } }, [courseId]);
  useEffect(() => { if (lessonId && !loading) { loadLessonContent(); } }, [lessonId, loading]);

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
      const data = await apiFetch(`/api/learner/lessons/${lessonId}`);
      setCurrentLesson(data);
      loadNotes(Number(lessonId));
      setShowQuiz(false);
      setQuizResult(null);
      setQuizAnswers({});
    } catch (e) { console.error(e); }
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

  const startQuiz = async () => {
    if (!currentLesson?.quiz) return;
    try {
      const res = await apiFetch(`/api/learner/quizzes/${currentLesson.quiz.id}/start`, { method: "POST" });
      setAttemptId(res.attempt_id);
      const quiz = await apiFetch(`/api/learner/quizzes/${currentLesson.quiz.id}`);
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
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className={`${sidebarOpen ? "w-80" : "w-0"} bg-white border-r transition-all overflow-hidden flex flex-col`}>
        <div className="p-4 border-b">
          <div className="flex items-center justify-between mb-2">
            <h2 className="font-semibold text-sm truncate">{courseInfo?.title || "Programme"}</h2>
            <button onClick={() => setSidebarOpen(false)} className="p-1 hover:bg-gray-100 rounded"><X className="w-4 h-4" /></button>
          </div>
          {progressPercent > 0 && (
            <div className="w-full bg-gray-200 rounded-full h-1.5">
              <div className="bg-green-500 h-1.5 rounded-full transition-all" style={{ width: `${progressPercent}%` }} />
            </div>
          )}
          <p className="text-xs text-gray-500 mt-1">{progressPercent}% complété</p>
          {certLoading ? (
            <div className="mt-3 p-2 bg-navy-50 rounded text-xs text-navy-600 text-center">Contrôle du certificat...</div>
          ) : certificate ? (
            <div className="mt-3 p-3 bg-green-50 rounded border border-green-200">
              <div className="flex items-center gap-2 mb-1.5">
                <Award className="w-4 h-4 text-green-600" />
                <span className="text-sm font-semibold text-green-800">Certificat obtenu!</span>
              </div>
              <p className="text-xs text-green-700 mb-2">N° {certificate.certificate_number}</p>
              <button
                onClick={downloadCertificate}
                className="w-full flex items-center justify-center gap-1 px-3 py-1.5 bg-green-600 text-white text-xs rounded hover:bg-green-700"
              >
                <Download className="w-3 h-3" />
                Télécharger PDF
              </button>
            </div>
          ) : null}
        </div>
        <div className="flex-1 overflow-y-auto">
          {syllabus.map((ch: any, ci: number) => (
            <div key={ch.id} className="border-b">
              <div className="px-4 py-3 bg-gray-50 font-medium text-sm flex items-center gap-2">
                <span className="text-navy-600 font-bold">{ci + 1}.</span>
                <span className="flex-1">{ch.title || "Module"}</span>
                <span className="text-xs text-gray-400">{ch.lessons?.length || 0}</span>
              </div>
              <div>
                {(ch.lessons || []).map((l: any) => (
                  <button key={l.id} onClick={() => navigate(`/learn/courses/${courseId}/lessons/${l.id}`)}
                    className={`w-full flex items-center gap-3 p-3 text-start border-b border-gray-50 hover:bg-gray-50 ${
                      currentLesson?.id === l.id ? "bg-navy-50 border-s-3 border-s-navy-600" : ""
                    }`}>
                    {completedLessons.has(l.id)
                      ? <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />
                      : <Circle className="w-4 h-4 text-gray-300 flex-shrink-0" />
                    }
                    <div className="flex-1 min-w-0">
                      <p className="text-sm truncate">{l.title || "Leçon"}</p>
                      <div className="flex items-center gap-2 text-xs text-gray-500">
                        {getIcon(l.lesson_type)}
                        <span><Clock className="w-3 h-3 inline" /> {l.duration_minutes || 0} min</span>
                      </div>
                    </div>
                    {l.has_quiz && <HelpCircle className="w-4 h-4 text-orange-500 flex-shrink-0" />}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        <header className="p-3 border-b bg-white flex items-center gap-3 shadow-sm">
          <button onClick={() => navigate("/dashboard")} title="Retour au dashboard"
            className="p-2 hover:bg-gray-100 rounded text-gray-600 hover:text-navy-600">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <button onClick={() => setSidebarOpen(true)} className="p-2 hover:bg-gray-100 rounded"><Menu className="w-5 h-5" /></button>
          <div className="flex-1">
            <h1 className="font-semibold text-sm">{currentLesson?.title || "Sélectionnez une leçon"}</h1>
            {currentLesson?.module_title && <p className="text-xs text-gray-500">{currentLesson.module_title}</p>}
          </div>
          <div className="flex gap-1">
            <button onClick={() => setShowNotes(!showNotes)} className={`p-2 rounded ${showNotes ? "bg-navy-100 text-navy-600" : "hover:bg-gray-100"}`}>
              <StickyNote className="w-4 h-4" />
            </button>
            <button onClick={prevLesson} className="p-2 hover:bg-gray-100 rounded"><ArrowLeft className="w-5 h-5" /></button>
            <button onClick={nextLesson} className="p-2 hover:bg-gray-100 rounded"><ArrowRight className="w-5 h-5" /></button>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto p-6 max-w-4xl mx-auto w-full">
          {!currentLesson && <div className="text-center py-20 text-gray-500">Sélectionnez une leçon pour commencer.</div>}

          {currentLesson && (
            <article>
              {/* Video */}
              {currentLesson.lesson_type === "video" && currentLesson.video_url && (
                <div className="mb-6">
                  {isYouTubeUrl(currentLesson.video_url) ? (
                    <iframe
                      src={getYouTubeEmbedUrl(currentLesson.video_url)}
                      className="w-full rounded-lg border"
                      style={{ height: "60vh" }}
                      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                      allowFullScreen
                      title={currentLesson.title}
                    />
                  ) : (
                    <video
                      ref={videoRef}
                      src={currentLesson.video_url}
                      controls
                      className="w-full rounded-lg bg-black"
                      style={{ maxHeight: "60vh" }}
                      onEnded={() => {
                        const t = getToken();
                        if (t) apiFetch(`/api/learner/lessons/${currentLesson.id}/progress`, {
                          method: "POST", body: JSON.stringify({ video_completed: true }),
                        });
                      }}
                    />
                  )}
                  {currentLesson.video_duration_seconds && (
                    <p className="text-xs text-gray-500 mt-1 text-center">
                      Duree: {Math.floor(currentLesson.video_duration_seconds / 60)}:{String(currentLesson.video_duration_seconds % 60).padStart(2, '0')}
                    </p>
                  )}
                </div>
              )}

              {/* PDF Viewer */}
              {currentLesson.lesson_type === "pdf" && currentLesson.pdf_url && (
                <div className="mb-6">
                  <embed src={currentLesson.pdf_url} type="application/pdf" className="w-full h-[70vh] rounded-lg border" />
                </div>
              )}

              {/* Images */}
              {currentLesson.lesson_type === "image" && currentLesson.image_urls && (
                <div className="mb-6 space-y-4">
                  {(Array.isArray(currentLesson.image_urls) ? currentLesson.image_urls : JSON.parse(currentLesson.image_urls || "[]")).map((url: string, i: number) => (
                    <img key={i} src={url} alt="" className="w-full rounded-lg" />
                  ))}
                </div>
              )}

              {/* Text Content */}
              {currentLesson.content_html && (
                <div className="prose max-w-none mb-6" dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(currentLesson.content_html) }} />
              )}
              {currentLesson.content_text && (
                <div className="whitespace-pre-wrap text-gray-700 leading-relaxed mb-6">{currentLesson.content_text}</div>
              )}

              {/* External Link */}
              {currentLesson.lesson_type === "link" && currentLesson.link_url && (
                <div className="mb-6 p-6 bg-blue-50 rounded-lg border border-blue-100">
                  <p className="text-sm text-gray-600 mb-2">Ressource externe:</p>
                  <a href={currentLesson.link_url} target="_blank" rel="noopener noreferrer"
                    className="text-blue-600 hover:underline font-medium flex items-center gap-2">
                    {currentLesson.link_title || currentLesson.link_url} →
                  </a>
                </div>
              )}

              {/* Document */}
              {currentLesson.document_url && (
                <div className="mb-6 p-4 bg-gray-50 rounded-lg border">
                  <a href={currentLesson.document_url} target="_blank" rel="noopener noreferrer"
                    className="flex items-center gap-3 text-navy-600 hover:text-navy-800">
                    <File className="w-5 h-5" />
                    <span className="font-medium">{currentLesson.document_type || "Document"}</span>
                    <span className="text-sm text-gray-500">(Ouvrir)</span>
                  </a>
                </div>
              )}

              {/* Quiz Section */}
              {currentLesson.quiz && !showQuiz && (
                <div className="mt-8 p-6 bg-orange-50 rounded-xl border border-orange-100">
                  <div className="flex items-center gap-3 mb-3">
                    <HelpCircle className="w-6 h-6 text-orange-600" />
                    <div>
                      <h3 className="font-semibold">{currentLesson.quiz.title}</h3>
                      {currentLesson.quiz.description && <p className="text-sm text-gray-600">{currentLesson.quiz.description}</p>}
                    </div>
                  </div>
                  {currentLesson.quiz.time_limit_minutes && (
                    <p className="text-xs text-gray-500 mb-3 flex items-center gap-1">
                      <Clock className="w-3 h-3" /> {currentLesson.quiz.time_limit_minutes} min
                    </p>
                  )}
                  <button onClick={startQuiz}
                    className="flex items-center gap-2 px-6 py-3 bg-orange-500 text-white rounded-lg hover:bg-orange-600 font-medium">
                    <Play className="w-5 h-5" /> Commencer le quiz
                  </button>
                </div>
              )}
            </article>
          )}

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
                <button onClick={startQuiz} className="w-full py-2 bg-gray-200 rounded-lg hover:bg-gray-300">
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
          <div className="p-4 border-t bg-white flex items-center justify-center gap-4">
            <button onClick={prevLesson}
              className="flex items-center gap-1 px-4 py-3 rounded-lg font-medium bg-gray-200 text-gray-700 hover:bg-gray-300">
              <ArrowLeft className="w-4 h-4" />
            </button>
            <button onClick={markComplete} disabled={completedLessons.has(currentLesson.id)}
              className={`flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-colors ${
                completedLessons.has(currentLesson.id)
                  ? "bg-green-500 text-white cursor-default"
                  : "bg-navy-600 text-white hover:bg-navy-700"
              }`}>
              <CheckCircle className="w-5 h-5" />
              {completedLessons.has(currentLesson.id) ? "Termine" : "Marquer comme termine"}
            </button>
            <button onClick={nextLesson}
              className="flex items-center gap-1 px-4 py-3 rounded-lg font-medium bg-navy-500 text-white hover:bg-navy-600">
              Lecon suivante <ArrowRight className="w-4 h-4" />
            </button>
            <button onClick={startQuiz}
              className={`flex items-center gap-2 px-5 py-3 rounded-lg font-medium bg-orange-500 text-white hover:bg-orange-600 ${
                syllabus.some((ch) => ch.lessons?.some((l: any) => l.id === currentLesson.id && l.has_quiz)) ? "" : "hidden"
              }`}>
              <HelpCircle className="w-5 h-5" /> Quiz
            </button>
          </div>
        )}
      </main>
    </div>
  );
}