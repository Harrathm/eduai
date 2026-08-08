import { Plus, Trash2, FileText, Video, HelpCircle, File, Image, Link, ChevronDown } from "lucide-react";
import { Button, EmptyState } from "../../../../components/ui";
import type { Chapter, Lesson } from "../../hooks/useCourseEditor";

const LESSON_TYPES = [
  { value: "text", label: "Texte", icon: FileText },
  { value: "video", label: "Vidéo", icon: Video },
  { value: "pdf", label: "Document PDF", icon: File },
  { value: "image", label: "Image", icon: Image },
  { value: "link", label: "Lien externe", icon: Link },
  { value: "quiz", label: "Quiz/Examen", icon: HelpCircle },
];

function getLessonIcon(type: string) {
  const t = LESSON_TYPES.find(x => x.value === type);
  return t ? <t.icon className="w-4 h-4" /> : <FileText className="w-4 h-4" />;
}

function getLessonBg(type: string) {
  switch (type) {
    case "video": return "bg-blue-50 text-blue-600";
    case "pdf": return "bg-red-50 text-red-600";
    case "image": return "bg-green-50 text-green-600";
    case "link": return "bg-purple-50 text-purple-600";
    case "quiz": return "bg-orange-50 text-orange-600";
    default: return "bg-gray-50 text-gray-600";
  }
}

interface ChapterContentProps {
  activeChapter: Chapter | null;
  chapters: Chapter[];
  onAddLesson: (chapterId: number) => void;
  onDeleteChapter: (id: number) => void;
  onOpenLesson: (lesson: Lesson) => void;
  onDeleteLesson: (chapterId: number, lessonId: number) => void;
  onAddFirstChapter: () => void;
}

export function ChapterContent({
  activeChapter, chapters, onAddLesson, onDeleteChapter,
  onOpenLesson, onDeleteLesson, onAddFirstChapter,
}: ChapterContentProps) {
  if (!activeChapter) {
    return (
      <div className="flex-1 flex items-center justify-center text-gray-500">
        <div className="text-center">
          <ChevronDown className="w-12 h-12 mx-auto mb-4 text-gray-300" />
          <p>Sélectionnez un chapitre</p>
          {chapters.length === 0 && (
            <Button onClick={onAddFirstChapter}>
              Créer le premier chapitre
            </Button>
          )}
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="p-4 border-b bg-white flex justify-between items-center">
        <div>
          <h3 className="font-semibold text-lg">{activeChapter.title}</h3>
          <p className="text-sm text-gray-500">{activeChapter.lessons?.length || 0} leçons</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => onAddLesson(activeChapter.id)}>
            <Plus className="w-4 h-4" /> Ajouter leçon
          </Button>
          <Button variant="danger" size="sm" onClick={() => onDeleteChapter(activeChapter.id)}>
            <Trash2 className="w-4 h-4" />
          </Button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {!activeChapter.lessons?.length ? (
          <EmptyState
            icon={<FileText className="w-12 h-12" />}
            title="Aucune leçon"
            description="Cliquez sur 'Ajouter leçon' pour commencer."
          />
        ) : (
          <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
            {activeChapter.lessons.map((lesson: Lesson) => (
              <div key={lesson.id}
                onClick={() => onOpenLesson(lesson)}
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
                  <Button variant="ghost" size="sm" onClick={e => { e.stopPropagation(); onDeleteLesson(activeChapter.id, lesson.id); }}>
                    <Trash2 className="w-3 h-3" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
