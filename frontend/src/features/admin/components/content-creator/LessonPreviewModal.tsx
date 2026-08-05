import { Loader2, FileText, Puzzle, Image as ImageIcon } from "lucide-react";
import { Modal } from "../../components";
import type { AIFactoryBundle } from "../../../../api";

type Props = {
  lesson: { module_title: string; lesson_title: string } | null;
  bundle: AIFactoryBundle;
  generatedImages: Record<string, string>;
  generatingImage: string | null;
  onClose: () => void;
  onGenerateImage: (lessonKey: string, prompt: string) => void;
};

export function LessonPreviewModal({ lesson, bundle, generatedImages, generatingImage, onClose, onGenerateImage }: Props) {
  if (!lesson) return null;
  const key = `${lesson.module_title}::${lesson.lesson_title}`;
  const content = bundle.lessons?.[key];
  const quiz = bundle.quizzes?.[key];
  const media = bundle.media_prompts?.[key];

  return (
    <Modal open onClose={onClose} title={`${lesson.module_title} › ${lesson.lesson_title}`} size="lg"
      footer={<button onClick={onClose} className="px-6 py-2.5 bg-cream-m rounded-xl font-medium">Close</button>}
    >
      <div className="space-y-6 max-h-[70vh] overflow-y-auto">
        {content && (
          <div>
            <h3 className="text-sm font-semibold text-navy mb-2 flex items-center gap-2">
              <FileText className="w-4 h-4 text-orange" /> Lesson Content
            </h3>
            <div className="prose prose-sm max-w-none bg-cream-m rounded-xl p-4 text-sm text-navy leading-relaxed whitespace-pre-wrap">
              {content}
            </div>
          </div>
        )}
        {quiz && quiz.questions && quiz.questions.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-navy mb-2 flex items-center gap-2">
              <Puzzle className="w-4 h-4 text-purple-500" /> Quiz
            </h3>
            <div className="space-y-3">
              {quiz.questions.map((q: any, qi: number) => (
                <div key={qi} className="bg-cream-m rounded-xl p-4">
                  <p className="text-sm font-medium text-navy mb-2">{qi + 1}. {q.question_text}</p>
                  <div className="space-y-1 ps-4">
                    {q.options?.map((o: any, oi: number) => (
                      <div key={oi} className={`text-xs px-3 py-1.5 rounded-lg ${o.is_correct ? "bg-green-100 text-green-700 font-medium" : "bg-white/50 text-gray"}`}>
                        {o.option_text} {o.is_correct && "\u2713"}
                      </div>
                    ))}
                  </div>
                  {q.explanation && <p className="text-xs text-gray mt-2 italic">{q.explanation}</p>}
                </div>
              ))}
            </div>
          </div>
        )}
        {media && (
          <div>
            <h3 className="text-sm font-semibold text-navy mb-2 flex items-center gap-2">
              <ImageIcon className="w-4 h-4 text-blue-500" /> Media
            </h3>
            <div className="space-y-3">
              {media.image_prompt && (
                <div className="bg-blue-50 rounded-xl p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-semibold text-blue-600">DALL-E Prompt</span>
                    <button
                      onClick={() => onGenerateImage(key, media.image_prompt)}
                      disabled={generatingImage === key}
                      className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-500 text-white rounded-lg text-xs font-medium hover:bg-blue-600 disabled:opacity-50"
                    >
                      {generatingImage === key ? (
                        <Loader2 className="w-3 h-3 animate-spin" />
                      ) : (
                        <ImageIcon className="w-3 h-3" />
                      )}
                      {generatingImage === key ? "Generating..." : "Generate Image"}
                    </button>
                  </div>
                  <p className="text-xs text-blue-800 mb-3">{media.image_prompt}</p>
                  {generatedImages[key] && (
                    <img
                      src={generatedImages[key]}
                      alt="Generated for lesson"
                      className="w-full max-w-md rounded-xl border border-blue-200 shadow-sm"
                    />
                  )}
                </div>
              )}
              {media.video_prompt && (
                <div className="bg-pink-50 rounded-xl p-4">
                  <span className="text-xs font-semibold text-pink-600 block mb-1">Video Prompt</span>
                  <p className="text-xs text-pink-800">{media.video_prompt}</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </Modal>
  );
}
