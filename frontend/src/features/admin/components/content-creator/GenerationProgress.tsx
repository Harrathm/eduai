import { Loader2, Check, Eye, ChevronLeft, FileText, Puzzle, Image, Video } from "lucide-react";
import type { AIFactoryBundle } from "../../../../api";

type Progress = {
  current: number; total: number; lesson: string; status: string; streamingText: string;
};

type Props = {
  generating: boolean;
  genProgress: Progress;
  bundle: AIFactoryBundle | null;
  onBack: () => void;
  onPreview: () => void;
  loading: boolean;
};

export function GenerationProgress({ generating, genProgress, bundle, onBack, onPreview, loading }: Props) {
  return (
    <div className="space-y-6">
      <div className="bg-white rounded-2xl shadow-sm border border-black/5 p-6">
        <div className="text-center mb-6">
          <div className="w-16 h-16 bg-orange/10 rounded-2xl flex items-center justify-center mx-auto mb-4">
            {generating ? <Loader2 className="w-8 h-8 text-orange animate-spin" /> : <Check className="w-8 h-8 text-green-500" />}
          </div>
          <h2 className="text-2xl font-display font-light text-navy">
            {generating ? "Generating Course Content" : "Generation Complete!"}
          </h2>
          <p className="text-gray text-sm mt-2">
            {generating
              ? `Lesson ${genProgress.current} of ${genProgress.total}`
              : `All ${genProgress.total} lessons generated successfully`}
          </p>
        </div>

        <div className="w-full bg-cream-m rounded-full h-3 mb-6 overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-orange to-orange-l rounded-full transition-all duration-500"
            style={{ width: `${genProgress.total ? (genProgress.current / genProgress.total) * 100 : 0}%` }}
          />
        </div>

        {generating && (
          <div className="bg-cream-m rounded-xl p-4 mb-4">
            <div className="flex items-center gap-2 text-sm font-medium text-navy mb-1">
              <FileText className="w-4 h-4 text-orange" />
              {genProgress.lesson}
            </div>
            <div className="text-xs text-gray">{genProgress.status}</div>
          </div>
        )}

        {genProgress.streamingText && (
          <div className="bg-navy text-green-300 rounded-xl p-4 max-h-48 overflow-y-auto text-xs font-mono leading-relaxed">
            {genProgress.streamingText.slice(0, 2000)}
            {genProgress.streamingText.length > 2000 && "..."}
          </div>
        )}

        {bundle && (
          <div className="space-y-2 mt-4">
            <h3 className="text-sm font-semibold text-navy">Generated Content</h3>
            {Object.entries(bundle.lessons).map(([key]) => {
              const hasQuiz = key in (bundle.quizzes || {});
              const hasMedia = key in (bundle.media_prompts || {});
              return (
                <div key={key} className="flex items-center gap-3 px-4 py-2 bg-green-50 rounded-xl text-sm">
                  <Check className="w-4 h-4 text-green-500" />
                  <span className="flex-1 text-navy">{key.replace("::", " › ")}</span>
                  {hasQuiz && <Puzzle className="w-3.5 h-3.5 text-purple-400" title="Quiz" />}
                  {hasMedia && <><Image className="w-3.5 h-3.5 text-blue-400" title="Image prompt" /><Video className="w-3.5 h-3.5 text-pink-400" title="Video prompt" /></>}
                </div>
              );
            })}
          </div>
        )}
      </div>

      <div className="flex justify-end gap-3">
        {bundle && !generating && (
          <>
            <button onClick={onBack} className="px-6 py-3 bg-cream-m rounded-xl font-medium text-navy">Back to Plan</button>
            <button onClick={onPreview} disabled={loading} className="px-6 py-3 bg-gradient-to-r from-orange to-orange-l text-white rounded-xl font-semibold flex items-center gap-2 shadow-lg shadow-orange/20 disabled:opacity-50">
              <Eye className="w-5 h-5" /> Preview & Publish
            </button>
          </>
        )}
      </div>
    </div>
  );
}
