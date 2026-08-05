import { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { lessonLearner, quizLearner, courseLearner } from "../../../api";
const learnerAPI = {
  syllabus: courseLearner.syllabus,
  lesson: lessonLearner.get,
  updateProgress: lessonLearner.progress,
  startQuiz: quizLearner.start,
  submitQuiz: quizLearner.submit,
  certificates: quizLearner.certificates,
  certificate: quizLearner.certificate,
  getCourseCertificate: courseLearner.certificate,
};
import { Play, Pause, CheckCircle, ChevronLeft, ChevronRight, BookOpen, Award, FileText, Video as VideoIcon, HelpCircle, Download } from "lucide-react";
import { jsPDF } from "jspdf";
import DOMPurify from "dompurify";

function isYouTubeUrl(url: string): boolean {
  return /youtube\.com\/embed\/|youtu\.be\/|youtube\.com\/watch/.test(url);
}

function getYouTubeEmbedUrl(url: string): string {
  const match = url.match(/(?:youtube\.com\/embed\/|youtu\.be\/|youtube\.com\/watch\?v=)([\w-]+)/);
  return match ? `https://www.youtube.com/embed/${match[1]}` : url;
}

interface Chapter {
  id: number;
  title: string;
  lessons: Lesson[];
}

interface Lesson {
  id: number;
  title: string;
  lesson_type: string;
  duration_minutes: number;
  is_free: boolean;
}

interface LessonContent {
  id: number;
  title: string;
  description: string;
  lesson_type: string;
  content_text: string;
  content_html: string;
  video_url: string;
  video_duration_seconds: number;
  video_thumbnail_url: string;
  pdf_url: string;
  has_quiz: boolean;
}

export default function LearnerPlayerPage() {
  const { courseId } = useParams();
  const navigate = useNavigate();
  const videoRef = useRef<HTMLVideoElement>(null);
  const [course, setCourse] = useState<any>(null);
  const [syllabus, setSyllabus] = useState<Chapter[]>([]);
  const [currentLesson, setCurrentLesson] = useState<LessonContent | null>(null);
  const [loading, setLoading] = useState(true);
  const [enrolled, setEnrolled] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [currentTime, setCurrentTime] = useState(0);
  const [certificate, setCertificate] = useState<any>(null);
  const [certLoading, setCertLoading] = useState(false);

  useEffect(() => {
    loadCourse();
  }, [courseId]);

  const loadCourse = async () => {
    try {
      const detail = await learnerAPI.courseDetail(Number(courseId));
      setCourse(detail);
      const sylla = await learnerAPI.syllabus(Number(courseId));
      setSyllabus(sylla);
      await checkCertificate();
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleEnroll = async () => {
    try {
      await learnerAPI.enroll(Number(courseId));
      setEnrolled(true);
      if (syllabus.length > 0 && syllabus[0].lessons.length > 0) {
        loadLesson(syllabus[0].lessons[0].id);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const loadLesson = async (lessonId: number) => {
    try {
      const content = await learnerAPI.lesson(lessonId);
      setCurrentLesson(content);
      updateProgress(lessonId, { status: "in_progress" });
    } catch (err) {
      console.error(err);
    }
  };

  const checkCertificate = async () => {
    try {
      setCertLoading(true);
      const cert = await learnerAPI.getCourseCertificate(Number(courseId));
      setCertificate(cert);
    } catch {
      setCertificate(null);
    } finally {
      setCertLoading(false);
    }
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
    doc.text(certificate.course_name || course?.title || "Course", pageW / 2, 110, { align: "center" });

    doc.setFontSize(11);
    doc.setTextColor(120, 120, 120);
    doc.text(`Certificate No: ${certificate.certificate_number}`, pageW / 2, 130, { align: "center" });
    doc.text(`Verification: ${certificate.verification_code}`, pageW / 2, 138, { align: "center" });
    doc.text(`Issued: ${new Date(certificate.issue_date).toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" })}`, pageW / 2, 146, { align: "center" });

    doc.setFontSize(9);
    doc.text("EduAI Learning Platform", pageW / 2, pageH - 25, { align: "center" });

    doc.save(`certificate-${certificate.certificate_number}.pdf`);
  };

  const updateProgress = async (lessonId: number, data: any) => {
    try {
      await learnerAPI.updateProgress(lessonId, data);
    } catch (err) {
      console.error(err);
    }
  };

  const handleVideoTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);
    }
  };

  const handleVideoEnded = () => {
    if (currentLesson) {
      updateProgress(currentLesson.id, {
        status: "completed",
        video_completed: true,
        video_progress_seconds: currentTime,
      });
    }
  };

  const markContentComplete = () => {
    if (currentLesson) {
      updateProgress(currentLesson.id, {
        status: "completed",
        content_completed: true,
      });
    }
  };

  const getLessonIcon = (type: string) => {
    switch (type) {
      case "video":
        return <VideoIcon className="w-5 h-5 text-blue-600" />;
      case "quiz":
        return <HelpCircle className="w-5 h-5 text-purple-600" />;
      case "pdf":
        return <FileText className="w-5 h-5 text-red-600" />;
      default:
        return <FileText className="w-5 h-5 text-gray-600" />;
    }
  };

  const getCurrentLessonIndex = () => {
    for (let i = 0; i < syllabus.length; i++) {
      const idx = syllabus[i].lessons.findIndex((l) => l.id === currentLesson?.id);
      if (idx >= 0) return { chapter: i, lesson: idx };
    }
    return null;
  };

  const navigateLesson = (direction: "prev" | "next") => {
    const idx = getCurrentLessonIndex();
    if (!idx) return;

    if (direction === "next") {
      if (idx.lesson < syllabus[idx.chapter].lessons.length - 1) {
        loadLesson(syllabus[idx.chapter].lessons[idx.lesson + 1].id);
      } else if (idx.chapter < syllabus.length - 1) {
        loadLesson(syllabus[idx.chapter + 1].lessons[0].id);
      }
    } else {
      if (idx.lesson > 0) {
        loadLesson(syllabus[idx.chapter].lessons[idx.lesson - 1].id);
      } else if (idx.chapter > 0) {
        const prevChapter = syllabus[idx.chapter - 1];
        loadLesson(prevChapter.lessons[prevChapter.lessons.length - 1].id);
      }
    }
  };

  if (loading) {
    return <div className="p-6">Loading...</div>;
  }

  if (!course) {
    return (
      <div className="p-6">
        <p>Course not found</p>
        <button onClick={() => navigate("/dashboard")} className="text-navy-600">
          Back
        </button>
      </div>
    );
  }

  if (!enrolled && !currentLesson) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="max-w-md p-8 bg-white rounded-lg shadow text-center">
          <BookOpen className="w-16 h-16 mx-auto mb-4 text-navy-600" />
          <h1 className="text-2xl font-bold mb-2">{course.title}</h1>
          <p className="text-gray-600 mb-4">{course.description}</p>
          <div className="mb-4">
            <span className="text-sm text-gray-500">
              {course.total_chapters} chapters • {course.total_lessons} lessons •{" "}
              {course.total_duration_minutes} min
            </span>
          </div>
          {(course.price_tokens > 0 || course.price_dt > 0) && (
            <div className="mb-4 p-3 bg-gray-50 rounded">
              <p className="font-semibold">Price:</p>
              <p>
                {course.price_tokens > 0 && `${course.price_tokens} tokens`}
                {course.price_tokens > 0 && course.price_dt > 0 && " + "}
                {course.price_dt > 0 && `${course.price_dt} DT`}
              </p>
            </div>
          )}
          <button
            onClick={handleEnroll}
            className="w-full px-4 py-3 bg-navy-600 text-white rounded-lg hover:bg-navy-700"
          >
            {course.price_tokens > 0 || course.price_dt > 0 ? "Enroll Now" : "Start Learning"}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <div
        className={`${
          sidebarOpen ? "w-80" : "w-0"
        } bg-white border-r transition-all overflow-hidden flex flex-col`}
      >
        <div className="p-4 border-b">
          <button
            onClick={() => navigate("/dashboard")}
            className="flex items-center gap-1 text-sm text-gray-600 mb-2"
          >
            <ChevronLeft className="w-4 h-4" />
            Exit
          </button>
          <h2 className="font-semibold text-sm">{course.title}</h2>
          {certLoading ? (
            <div className="mt-2 p-2 bg-navy-50 rounded text-xs text-navy-600">Checking certificate...</div>
          ) : certificate ? (
            <div className="mt-2 p-3 bg-green-50 rounded border border-green-200">
              <div className="flex items-center gap-2 mb-2">
                <Award className="w-4 h-4 text-green-600" />
                <span className="text-sm font-semibold text-green-800">Certificate Earned!</span>
              </div>
              <p className="text-xs text-green-700 mb-2">No: {certificate.certificate_number}</p>
              <button
                onClick={downloadCertificate}
                className="w-full flex items-center justify-center gap-1 px-3 py-1.5 bg-green-600 text-white text-xs rounded hover:bg-green-700"
              >
                <Download className="w-3 h-3" />
                Download PDF
              </button>
            </div>
          ) : null}
        </div>

        <div className="flex-1 overflow-y-auto">
          {syllabus.map((chapter, idx) => (
            <div key={chapter.id} className="border-b">
              <div className="p-3 bg-gray-50 font-medium text-sm">{chapter.title}</div>
              <div>
                {chapter.lessons.map((lesson) => (
                  <button
                    key={lesson.id}
                    onClick={() => loadLesson(lesson.id)}
                    className={`w-full flex items-center gap-3 p-3 text-start hover:bg-gray-50 ${
                      currentLesson?.id === lesson.id ? "bg-navy-50" : ""
                    }`}
                  >
                    {getLessonIcon(lesson.lesson_type)}
                    <div className="flex-1">
                      <p className="text-sm">{lesson.title}</p>
                      <p className="text-xs text-gray-500">{lesson.duration_minutes} min</p>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="p-4 border-t">
          <button className="flex items-center gap-2 text-sm text-gray-600">
            <Award className="w-4 h-4" />
            My Certificates
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="p-3 border-b bg-white flex items-center gap-3">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 hover:bg-gray-100 rounded"
          >
            {sidebarOpen ? <ChevronLeft className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
          </button>
          <div className="flex-1">
            <h3 className="font-medium">{currentLesson?.title}</h3>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => navigateLesson("prev")}
              className="p-2 hover:bg-gray-100 rounded"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
            <button
              onClick={() => navigateLesson("next")}
              className="p-2 hover:bg-gray-100 rounded"
            >
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto p-6">
          {currentLesson?.lesson_type === "video" && currentLesson.video_url && (
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
                  onTimeUpdate={handleVideoTimeUpdate}
                  onEnded={handleVideoEnded}
                  className="w-full rounded-lg bg-black"
                />
              )}
            </div>
          )}

          {currentLesson?.lesson_type === "video" && !currentLesson.video_url && (
            <div className="mb-6 p-12 bg-gray-100 rounded-lg text-center">
              <VideoIcon className="w-16 h-16 mx-auto mb-4 text-gray-400" />
              <p className="text-gray-500">Video coming soon</p>
            </div>
          )}

          {currentLesson?.content_text && (
            <div className="prose max-w-none mb-6">
              <div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(currentLesson.content_html || currentLesson.content_text) }} />
            </div>
          )}

          {currentLesson?.content_html && (
            <div
              className="prose max-w-none mb-6"
              dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(currentLesson.content_html) }}
            />
          )}

          {!currentLesson?.content_text && !currentLesson?.content_html && currentLesson?.lesson_type !== "video" && (
            <div className="text-center py-12 text-gray-500">
              <FileText className="w-16 h-16 mx-auto mb-4 text-gray-400" />
              <p>Content coming soon</p>
            </div>
          )}

          <div className="mt-6 flex justify-center">
            <button
              onClick={markContentComplete}
              className="flex items-center gap-2 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700"
            >
              <CheckCircle className="w-5 h-5" />
              Mark as Complete
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}