import { CheckCircle, AlertCircle, LayoutGrid } from "lucide-react";
import { useParams, useNavigate } from "react-router-dom";
import { PageSpinner } from "../../../components/ui";
import { useCourseEditor } from "../hooks/useCourseEditor";
import { CourseSidebar, ChapterContent, LessonEditor, CoursePreviewModal } from "../components/course-editor";

export default function CourseEditorPage() {
  const { courseId } = useParams();
  const navigate = useNavigate();
  const {
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
  } = useCourseEditor(courseId);

  if (loading) return <PageSpinner message="Chargement du cours..." />;

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

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Left Sidebar */}
      <CourseSidebar
        course={course}
        chapters={chapters}
        activeChapter={activeChapter}
        saving={saving}
        previewLoading={previewLoading}
        publishErrors={publishErrors}
        onBack={() => navigate("/dashboard/admin/courses")}
        onPreview={handlePreview}
        onDuplicate={handleDuplicate}
        onPublish={handlePublish}
        onUnpublish={handleUnpublish}
        onArchive={handleArchive}
        onSave={handleSaveCourse}
        onAddChapter={handleAddChapter}
        onSetActiveChapter={setActiveChapter}
        onUpdateChapterTitle={handleUpdateChapterTitle}
        onCourseFieldChange={updateCourseField}
        onOpenBuilder={() => navigate(`/dashboard/admin/courses/${courseId}/builder`)}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <ChapterContent
          activeChapter={activeChapterData || null}
          chapters={chapters}
          onAddLesson={handleAddLesson}
          onDeleteChapter={handleDeleteChapter}
          onOpenLesson={openLessonEditor}
          onDeleteLesson={handleDeleteLesson}
          onAddFirstChapter={handleAddChapter}
        />
      </div>

      {/* Lesson Editor Modal */}
      <LessonEditor
        open={showLessonEditor && !!activeLesson}
        form={editLessonForm}
        onFormChange={setEditLessonForm}
        onClose={() => setShowLessonEditor(false)}
        onSave={handleSaveLesson}
      />

      {/* Course Preview Modal */}
      <CoursePreviewModal previewCourse={previewCourse} onClose={() => setPreviewCourse(null)} />

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
