import { useNavigate } from "react-router-dom";
import { Check, Loader2, Save, BookOpen, FileText, Puzzle, Image, Sparkles } from "lucide-react";
import type { AIFactoryBundle, AIPreviewInfo } from "../../../../api";

type Props = {
  bundle: AIFactoryBundle;
  previewInfo: AIPreviewInfo;
  publishing: boolean;
  publishResult: { course_id: number; slug: string } | null;
  onPublish: () => void;
  onBack: () => void;
  onReset: () => void;
  onPreviewLesson: (lesson: { module_title: string; lesson_title: string }) => void;
};

export function PreviewPublish({ bundle, previewInfo, publishing, publishResult, onPublish, onBack, onReset, onPreviewLesson }: Props) {
  const navigate = useNavigate();

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-2xl shadow-sm border border-black/5 p-6">
        <div className="flex items-start justify-between mb-6">
          <div>
            <h2 className="text-2xl font-display font-light text-navy">{previewInfo.title}</h2>
            {previewInfo.subtitle && <p className="text-gray text-sm mt-1">{previewInfo.subtitle}</p>}
            <div className="flex items-center gap-3 mt-2">
              <span className="px-2.5 py-1 bg-orange/10 text-orange text-xs font-medium rounded-full capitalize">{previewInfo.level}</span>
              <span className="px-2.5 py-1 bg-blue/10 text-blue text-xs font-medium rounded-full">{previewInfo.category}</span>
              <span className="text-xs text-gray">{previewInfo.total_modules} modules · {previewInfo.total_lessons} lessons</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {publishResult ? (
              <div className="flex items-center gap-2 px-4 py-2 bg-green-100 text-green-700 rounded-xl text-sm font-medium">
                <Check className="w-4 h-4" /> Published as Draft
              </div>
            ) : (
              <button
                onClick={onPublish}
                disabled={publishing}
                className="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-orange to-orange-l text-white rounded-xl font-semibold shadow-lg shadow-orange/20 disabled:opacity-50"
              >
                {publishing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                {publishing ? "Publishing..." : "Save as Draft"}
              </button>
            )}
          </div>
        </div>

        {publishResult && (
          <div className="bg-green-50 border border-green-200 rounded-xl p-4 mb-6 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Check className="w-5 h-5 text-green-600" />
              <span className="text-sm text-green-800">Course saved as draft</span>
            </div>
            <button
              onClick={() => navigate(`/dashboard/admin/courses/${publishResult.course_id}`)}
              className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700"
            >
              Open Course Editor
            </button>
          </div>
        )}

        {previewInfo.description && (
          <div className="mb-6">
            <h3 className="text-sm font-semibold text-navy mb-2">Description</h3>
            <p className="text-sm text-gray leading-relaxed">{previewInfo.description}</p>
          </div>
        )}

        <h3 className="text-sm font-semibold text-navy mb-3">Course Structure</h3>
        <div className="space-y-3">
          {previewInfo.lessons.map((l, i) => {
            const isFirstInModule = i === 0 || previewInfo.lessons[i - 1].module_title !== l.module_title;
            return (
              <div key={i}>
                {isFirstInModule && (
                  <h4 className="text-xs font-bold text-orange uppercase tracking-wider mt-4 mb-2">{l.module_title}</h4>
                )}
                <div
                  className="flex items-center gap-3 px-4 py-2.5 bg-cream-m rounded-xl hover:bg-cream cursor-pointer transition-colors"
                  onClick={() => onPreviewLesson({ module_title: l.module_title, lesson_title: l.lesson_title })}
                >
                  <BookOpen className="w-4 h-4 text-navy-m flex-shrink-0" />
                  <span className="flex-1 text-sm font-medium text-navy">{l.lesson_title}</span>
                  {l.has_content && <FileText className="w-3.5 h-3.5 text-green-500" title="Has content" />}
                  {l.has_quiz && <Puzzle className="w-3.5 h-3.5 text-purple-400" title="Has quiz" />}
                  {l.has_media_prompts && <Image className="w-3.5 h-3.5 text-blue-400" title="Has media prompts" />}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="flex justify-end gap-3">
        <button onClick={onBack} className="px-6 py-3 bg-cream-m rounded-xl font-medium text-navy">Back</button>
        {publishResult && (
          <button onClick={onReset} className="px-6 py-3 bg-navy text-white rounded-xl font-medium flex items-center gap-2">
            <Sparkles className="w-4 h-4" /> Create Another Course
          </button>
        )}
      </div>
    </div>
  );
}
