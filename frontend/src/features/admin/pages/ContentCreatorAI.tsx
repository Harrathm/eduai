import { RotateCcw, AlertCircle } from "lucide-react";
import { useContentCreator } from "../hooks/useContentCreator";
import { Button } from "../../../components/ui";
import { PromptInputForm, PlanEditor, GenerationProgress, PreviewPublish, LessonPreviewModal } from "../components/content-creator";

const STEPS = ["Topic", "Plan", "Generate", "Preview"];

export default function ContentCreatorAI() {
  const cc = useContentCreator();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-display font-light text-navy">
            Content Creator <span className="italic text-orange">AI</span>
          </h1>
          <p className="text-gray text-sm mt-1">Generate full courses with AI in 4 steps</p>
        </div>
        {cc.step > 0 && (
          <Button variant="ghost" size="md" onClick={cc.resetAll}>
            <RotateCcw className="w-4 h-4" /> Start Over
          </Button>
        )}
      </div>

      <div className="flex items-center gap-2 bg-white p-4 rounded-2xl shadow-sm border border-black/5">
        {STEPS.map((label, i) => (
          <div key={label} className="flex items-center gap-2 flex-1">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold transition-all ${i < cc.step ? "bg-green-500 text-white" : i === cc.step ? "bg-orange text-white" : "bg-cream-m text-navy-m"}`}>
              {i < cc.step ? "\u2713" : i + 1}
            </div>
            <span className={`text-sm font-medium hidden sm:inline ${i === cc.step ? "text-navy" : "text-gray"}`}>{label}</span>
          </div>
        ))}
      </div>

      {cc.error && (
        <div className="flex items-center gap-3 px-4 py-3 bg-red-50 text-red-600 rounded-xl text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          {cc.error}
          <Button variant="ghost" size="sm" onClick={cc.dismissError}>&times;</Button>
        </div>
      )}

      {cc.step === 0 && (
        <PromptInputForm
          topic={cc.topic}
          onTopicChange={cc.setTopic}
          useRag={cc.useRag}
          onUseRagChange={cc.setUseRag}
          uploadedFiles={cc.uploadedFiles}
          uploadingFile={cc.uploadingFile}
          fileInputRef={cc.fileInputRef}
          onUploadPDF={cc.handleUploadPDF}
          onRemoveFile={cc.handleRemoveFile}
          onGenerate={cc.handleGeneratePlan}
          loading={cc.loading}
        />
      )}

      {cc.step === 1 && cc.editedPlan && (
        <PlanEditor
          plan={cc.editedPlan}
          onPlanEdit={cc.handlePlanEdit}
          setPlan={cc.setEditedPlanDirectly}
          onBack={() => cc.setStep(0)}
          onStart={cc.handleStartGeneration}
          countLessons={cc.countLessons}
          LEVELS={cc.LEVELS}
          LEVEL_LABELS={cc.LEVEL_LABELS}
        />
      )}

      {cc.step === 2 && (
        <GenerationProgress
          generating={cc.generating}
          genProgress={cc.genProgress}
          bundle={cc.bundle}
          onBack={() => cc.setStep(1)}
          onPreview={cc.handlePreview}
          loading={cc.loading}
        />
      )}

      {cc.step === 3 && cc.bundle && cc.previewInfo && (
        <PreviewPublish
          bundle={cc.bundle}
          previewInfo={cc.previewInfo}
          publishing={cc.publishing}
          publishResult={cc.publishResult}
          onPublish={cc.handlePublish}
          onBack={() => cc.setStep(2)}
          onReset={cc.resetAll}
          onPreviewLesson={(l) => cc.setPreviewLesson(l)}
        />
      )}

      <LessonPreviewModal
        lesson={cc.previewLesson}
        bundle={cc.bundle!}
        generatedImages={cc.generatedImages}
        generatingImage={cc.generatingImage}
        onClose={() => cc.setPreviewLesson(null)}
        onGenerateImage={cc.handleGenerateImage}
      />
    </div>
  );
}
