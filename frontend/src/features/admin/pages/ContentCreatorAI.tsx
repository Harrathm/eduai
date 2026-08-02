import { useState, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Sparkles, Loader2, Check, ChevronRight, BookOpen, FileText, Image, Video, Eye, Save, ArrowLeft, AlertCircle, Puzzle, RotateCcw, Upload, X, File } from "lucide-react";
import { Modal } from "../components";
import { adminAIFactory } from "../api";
import type { AIFactoryPlan, AIFactoryBundle, AIPreviewInfo } from "../api";

const STEPS = ["Topic", "Plan", "Generate", "Preview"];

const LEVELS = ["beginner", "intermediate", "advanced"];
const LEVEL_LABELS: Record<string, string> = { beginner: "Beginner", intermediate: "Intermediate", advanced: "Advanced" };

export default function ContentCreatorAI() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [topic, setTopic] = useState("");
  const [useRag, setUseRag] = useState(false);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [plan, setPlan] = useState<AIFactoryPlan | null>(null);
  const [editedPlan, setEditedPlan] = useState<AIFactoryPlan | null>(null);
  const [bundle, setBundle] = useState<AIFactoryBundle | null>(null);
  const [previewInfo, setPreviewInfo] = useState<AIPreviewInfo | null>(null);
  const [publishing, setPublishing] = useState(false);
  const [publishResult, setPublishResult] = useState<{ course_id: number; slug: string } | null>(null);
  const [previewLesson, setPreviewLesson] = useState<{ module_title: string; lesson_title: string } | null>(null);
  const [generatedImages, setGeneratedImages] = useState<Record<string, string>>({});
  const [generatingImage, setGeneratingImage] = useState<string | null>(null);
  const [uploadedFiles, setUploadedFiles] = useState<{ name: string; chunks: number }[]>([]);
  const [uploadingFile, setUploadingFile] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [genProgress, setGenProgress] = useState<{
    current: number; total: number; lesson: string; status: string; streamingText: string;
  }>({ current: 0, total: 0, lesson: "", status: "", streamingText: "" });

  const streamRef = useRef<AbortController | null>(null);
  const genQueueRef = useRef<{ module_title: string; lesson_title: string; description: string }[]>([]);

  const handleGeneratePlan = async () => {
    if (!topic.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await adminAIFactory.generatePlan({ topic: topic.trim(), use_rag: useRag });
      const planData = { ...res.plan, modules: res.plan.modules || [] };
      setPlan(planData);
      setEditedPlan(JSON.parse(JSON.stringify(planData)));
      setStep(1);
    } catch (err: any) {
      setError(err.message || "Failed to generate plan");
    }
    setLoading(false);
  };

  const handlePlanEdit = (modIdx: number, lesIdx: number | null, field: string, value: string | number) => {
    if (!editedPlan) return;
    const copy = JSON.parse(JSON.stringify(editedPlan));
    if (lesIdx === null) {
      copy.modules[modIdx][field] = value;
    } else {
      copy.modules[modIdx].lessons[lesIdx][field] = value;
    }
    setEditedPlan(copy);
  };

  const handleStartGeneration = () => {
    if (!editedPlan) return;
    setBundle(null);
    setPreviewInfo(null);
    setPublishResult(null);
    const queue: { module_title: string; lesson_title: string; description: string }[] = [];
    for (const mod of editedPlan.modules || []) {
      for (const les of mod.lessons) {
        queue.push({ module_title: mod.title, lesson_title: les.title, description: les.description });
      }
    }
    genQueueRef.current = queue;
    setGenProgress({ current: 0, total: queue.length, lesson: "", status: "starting...", streamingText: "" });
    setStep(2);
    setGenerating(true);
    generateNextLesson(queue, 0, {} as AIFactoryBundle, editedPlan);
  };

  const generateNextLesson = async (
    queue: { module_title: string; lesson_title: string; description: string }[],
    idx: number,
    acc: AIFactoryBundle,
    plan: AIFactoryPlan
  ) => {
    if (idx >= queue.length) {
      const fullBundle: AIFactoryBundle = { plan, lessons: acc.lessons || {}, quizzes: acc.quizzes || {}, media_prompts: acc.media_prompts || {} };
      setBundle(fullBundle);
      setGenerating(false);
      setGenProgress(p => ({ ...p, status: "Complete!", streamingText: "" }));
      return;
    }
    const item = queue[idx];
    setGenProgress(p => ({ ...p, current: idx + 1, lesson: `${item.module_title} › ${item.lesson_title}`, status: "Generating content...", streamingText: "" }));

    try {
      const streamRes = await adminAIFactory.generateContentStream({
        topic: plan.title,
        lesson_title: item.lesson_title,
        lesson_description: item.description,
        module_title: item.module_title,
        use_rag: useRag,
      });
      if (!streamRes.ok) throw new Error("Stream request failed");
      const reader = streamRes.body!.getReader();
      const decoder = new TextDecoder();
      let fullContent = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const text = decoder.decode(value, { stream: true });
        const lines = text.split("\n");
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6).trim();
            if (data === "[DONE]") break;
            try {
              const parsed = JSON.parse(data);
              if (parsed.chunk) {
                fullContent += parsed.chunk;
                setGenProgress(p => ({ ...p, streamingText: fullContent }));
              }
              if (parsed.error) throw new Error(parsed.error);
            } catch { /* skip parse errors */ }
          }
        }
      }
      const lessonKey = `${item.module_title}::${item.lesson_title}`;
      acc.lessons = { ...(acc.lessons || {}), [lessonKey]: fullContent };
      setGenProgress(p => ({ ...p, status: "Generating quiz...", streamingText: "" }));

      const quizRes = await adminAIFactory.generateQuiz({ topic: plan.title, lesson_title: item.lesson_title, lesson_content: fullContent });
      acc.quizzes = { ...(acc.quizzes || {}), [lessonKey]: quizRes.quiz };

      setGenProgress(p => ({ ...p, status: "Generating media prompts...", streamingText: "" }));
      const mediaRes = await adminAIFactory.generateMediaPrompts({ topic: plan.title, lesson_title: item.lesson_title, lesson_description: item.description });
      acc.media_prompts = { ...(acc.media_prompts || {}), [lessonKey]: { image_prompt: mediaRes.image_prompt, video_prompt: mediaRes.video_prompt } };

      const updatedBundle: AIFactoryBundle = { plan, lessons: acc.lessons!, quizzes: acc.quizzes!, media_prompts: acc.media_prompts! };
      setBundle(updatedBundle);
    } catch (err: any) {
      setGenProgress(p => ({ ...p, status: `Error: ${err.message}`, streamingText: "" }));
    }
    generateNextLesson(queue, idx + 1, acc, plan);
  };

  const handlePreview = async () => {
    if (!bundle) return;
    setLoading(true);
    try {
      const res = await adminAIFactory.preview({ bundle });
      setPreviewInfo(res.preview);
      setStep(3);
    } catch (err: any) {
      setError(err.message || "Preview failed");
    }
    setLoading(false);
  };

  const handlePublish = async () => {
    if (!bundle) return;
    setPublishing(true);
    setError(null);
    try {
      const res = await adminAIFactory.publish({ bundle });
      setPublishResult({ course_id: res.course_id, slug: res.slug });
    } catch (err: any) {
      setError(err.message || "Publish failed");
    }
    setPublishing(false);
  };

  const handleGenerateImage = async (lessonKey: string, prompt: string) => {
    setGeneratingImage(lessonKey);
    setError(null);
    try {
      const res = await adminAIFactory.generateImage({ prompt });
      setGeneratedImages(prev => ({ ...prev, [lessonKey]: res.url }));
      if (bundle) {
        const saveRes = await adminAIFactory.saveImageToBundle({
          bundle,
          lesson_key: lessonKey,
          image_url: res.url,
          image_prompt: prompt,
        });
        setBundle(saveRes.bundle);
      }
    } catch (err: any) {
      setError(err.message || "Image generation failed");
    }
    setGeneratingImage(null);
  };

  const handleUploadPDF = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.name.endsWith(".pdf")) {
      setError("Only PDF files are supported");
      return;
    }
    setUploadingFile(true);
    setError(null);
    try {
      const res = await adminAIFactory.ingestPDF(file);
      setUploadedFiles(prev => [...prev, { name: file.name, chunks: res.chunks_added }]);
    } catch (err: any) {
      setError(err.message || "Upload failed");
    }
    setUploadingFile(false);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleRemoveFile = (idx: number) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== idx));
  };

  const resetAll = () => {
    setStep(0);
    setTopic("");
    setPlan(null);
    setEditedPlan(null);
    setBundle(null);
    setPreviewInfo(null);
    setPublishResult(null);
    setGeneratedImages({});
    setUploadedFiles([]);
    setError(null);
    setGenProgress({ current: 0, total: 0, lesson: "", status: "", streamingText: "" });
    if (streamRef.current) streamRef.current.abort();
  };

  const countLessons = (p: AIFactoryPlan) => (p.modules || []).reduce((sum, m) => sum + m.lessons.length, 0);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-display font-light text-navy">
            Content Creator <span className="italic text-orange">AI</span>
          </h1>
          <p className="text-gray text-sm mt-1">Generate full courses with AI in 4 steps</p>
        </div>
        {step > 0 && (
          <button onClick={resetAll} className="flex items-center gap-2 px-4 py-2 bg-cream-m rounded-xl text-sm font-medium text-navy hover:bg-cream">
            <RotateCcw className="w-4 h-4" /> Start Over
          </button>
        )}
      </div>

      {/* Steps indicator */}
      <div className="flex items-center gap-2 bg-white p-4 rounded-2xl shadow-sm border border-black/5">
        {STEPS.map((label, i) => (
          <div key={label} className="flex items-center gap-2 flex-1">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold transition-all ${i < step ? "bg-green-500 text-white" : i === step ? "bg-orange text-white" : "bg-cream-m text-navy-m"}`}>
              {i < step ? <Check className="w-4 h-4" /> : i + 1}
            </div>
            <span className={`text-sm font-medium hidden sm:inline ${i === step ? "text-navy" : "text-gray"}`}>{label}</span>
            {i < STEPS.length - 1 && <ChevronRight className="w-4 h-4 text-gray flex-shrink-0" />}
          </div>
        ))}
      </div>

      {error && (
        <div className="flex items-center gap-3 px-4 py-3 bg-red-50 text-red-600 rounded-xl text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          {error}
          <button onClick={() => setError(null)} className="ml-auto text-red-400 hover:text-red-600">&times;</button>
        </div>
      )}

      {/* ─── Step 0: Topic ─────────────────────────────────────────── */}
      {step === 0 && (
        <div className="bg-white rounded-2xl shadow-sm border border-black/5 p-8">
          <div className="max-w-2xl mx-auto space-y-6">
            <div className="text-center">
              <div className="w-16 h-16 bg-orange/10 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <Sparkles className="w-8 h-8 text-orange" />
              </div>
              <h2 className="text-2xl font-display font-light text-navy">What course do you want to create?</h2>
              <p className="text-gray text-sm mt-2">Enter a topic and the AI will generate a complete course with lessons, quizzes, and media prompts.</p>
            </div>

            <textarea
              value={topic}
              onChange={e => setTopic(e.target.value)}
              placeholder="e.g., Introduction to Machine Learning, Advanced French Grammar, Web Development with React..."
              className="w-full h-28 px-5 py-4 bg-cream-m rounded-2xl border border-black/5 text-sm focus:outline-none focus:ring-2 focus:ring-orange/20 resize-none"
            />

            <label className="flex items-center gap-3 px-4 py-3 bg-cream-m rounded-xl cursor-pointer">
              <input type="checkbox" checked={useRag} onChange={e => setUseRag(e.target.checked)} className="rounded border-gray-300 text-orange focus:ring-orange" />
              <div>
                <span className="text-sm font-medium text-navy">Use uploaded documents as context</span>
                <p className="text-xs text-gray mt-0.5">The AI will reference your uploaded PDFs and documents for more relevant content</p>
              </div>
            </label>

            {useRag && (
              <div className="space-y-3">
                <div
                  onClick={() => fileInputRef.current?.click()}
                  className="flex flex-col items-center justify-center gap-2 px-6 py-8 border-2 border-dashed border-orange/30 rounded-2xl bg-orange/5 cursor-pointer hover:border-orange/50 hover:bg-orange/10 transition-colors"
                >
                  {uploadingFile ? (
                    <Loader2 className="w-8 h-8 text-orange animate-spin" />
                  ) : (
                    <Upload className="w-8 h-8 text-orange" />
                  )}
                  <span className="text-sm font-medium text-navy">
                    {uploadingFile ? "Uploading..." : "Click to upload a PDF"}
                  </span>
                  <span className="text-xs text-gray">PDF files only — content will be indexed for RAG</span>
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf"
                  onChange={handleUploadPDF}
                  className="hidden"
                />

                {uploadedFiles.length > 0 && (
                  <div className="space-y-2">
                    <span className="text-xs font-medium text-gray uppercase tracking-wider">Uploaded documents</span>
                    {uploadedFiles.map((f, i) => (
                      <div key={i} className="flex items-center gap-3 px-4 py-2.5 bg-green-50 rounded-xl">
                        <File className="w-4 h-4 text-green-600 flex-shrink-0" />
                        <span className="flex-1 text-sm text-navy truncate">{f.name}</span>
                        <span className="text-xs text-green-600 font-medium">{f.chunks} chunks</span>
                        <button onClick={() => handleRemoveFile(i)} className="text-gray hover:text-red-500 transition-colors">
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            <button
              onClick={handleGeneratePlan}
              disabled={loading || !topic.trim()}
              className="w-full py-4 bg-gradient-to-r from-orange to-orange-l text-white rounded-2xl font-semibold text-lg disabled:opacity-50 flex items-center justify-center gap-3 shadow-lg shadow-orange/20"
            >
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Sparkles className="w-5 h-5" />}
              {loading ? "Generating Course Plan..." : "Generate Course Plan"}
            </button>
          </div>
        </div>
      )}

      {/* ─── Step 1: Plan Review ────────────────────────────────────── */}
      {step === 1 && editedPlan && (
        <div className="space-y-6">
          <div className="bg-white rounded-2xl shadow-sm border border-black/5 p-6 space-y-4">
            <h2 className="font-display font-semibold text-navy text-lg">Course Details</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label className="block text-xs font-medium text-gray mb-1">Title</label>
                <input value={editedPlan.title} onChange={e => setEditedPlan({ ...editedPlan, title: e.target.value })}
                  className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none focus:ring-2 focus:ring-orange/20" />
              </div>
              <div className="md:col-span-2">
                <label className="block text-xs font-medium text-gray mb-1">Subtitle</label>
                <input value={editedPlan.subtitle} onChange={e => setEditedPlan({ ...editedPlan, subtitle: e.target.value })}
                  className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none focus:ring-2 focus:ring-orange/20" />
              </div>
              <div className="md:col-span-2">
                <label className="block text-xs font-medium text-gray mb-1">Description</label>
                <textarea value={editedPlan.description} onChange={e => setEditedPlan({ ...editedPlan, description: e.target.value })}
                  className="w-full h-24 px-4 py-3 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none focus:ring-2 focus:ring-orange/20 resize-none" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray mb-1">Level</label>
                <select value={editedPlan.level} onChange={e => setEditedPlan({ ...editedPlan, level: e.target.value })}
                  className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none">
                  {LEVELS.map(l => <option key={l} value={l}>{LEVEL_LABELS[l]}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray mb-1">Category</label>
                <input value={editedPlan.category} onChange={e => setEditedPlan({ ...editedPlan, category: e.target.value })}
                  className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none focus:ring-2 focus:ring-orange/20" />
              </div>
            </div>
          </div>

          {editedPlan.modules.map((mod, mi) => (
            <div key={mi} className="bg-white rounded-2xl shadow-sm border border-black/5 p-6 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex-1 space-y-2">
                  <label className="block text-xs font-medium text-gray">Module {mi + 1} Title</label>
                  <input value={mod.title} onChange={e => handlePlanEdit(mi, null, "title", e.target.value)}
                    className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-orange/20" />
                  <textarea value={mod.description} onChange={e => handlePlanEdit(mi, null, "description", e.target.value)}
                    className="w-full px-4 py-2 bg-cream-m rounded-xl border border-black/5 text-xs focus:outline-none focus:ring-2 focus:ring-orange/20 resize-none h-16" />
                </div>
                <span className="ml-4 text-xs text-gray font-medium">{mod.lessons.length} lessons</span>
              </div>
              <div className="space-y-2 pl-4 border-l-2 border-orange/20">
                {mod.lessons.map((les, li) => (
                  <div key={li} className="space-y-1">
                    <input value={les.title} onChange={e => handlePlanEdit(mi, li, "title", e.target.value)}
                      className="w-full px-3 py-2 bg-cream-m rounded-lg border border-black/5 text-sm focus:outline-none focus:ring-2 focus:ring-orange/20" />
                    <div className="flex gap-2">
                      <input value={les.description} onChange={e => handlePlanEdit(mi, li, "description", e.target.value)}
                        className="flex-1 px-3 py-2 bg-cream-m rounded-lg border border-black/5 text-xs focus:outline-none focus:ring-2 focus:ring-orange/20" />
                      <input type="number" value={les.duration_minutes} onChange={e => handlePlanEdit(mi, li, "duration_minutes", Number(e.target.value))}
                        className="w-20 px-3 py-2 bg-cream-m rounded-lg border border-black/5 text-xs focus:outline-none focus:ring-2 focus:ring-orange/20" title="Minutes" />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}

          <div className="flex justify-end gap-3">
            <button onClick={() => setStep(0)} className="px-6 py-3 bg-cream-m rounded-xl font-medium text-navy">Back</button>
            <button onClick={handleStartGeneration} className="px-6 py-3 bg-gradient-to-r from-orange to-orange-l text-white rounded-xl font-semibold flex items-center gap-2 shadow-lg shadow-orange/20">
              <Sparkles className="w-5 h-5" /> Generate All Content ({countLessons(editedPlan)} lessons)
            </button>
          </div>
        </div>
      )}

      {/* ─── Step 2: Generation Progress ─────────────────────────────── */}
      {step === 2 && (
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

            {/* Progress bar */}
            <div className="w-full bg-cream-m rounded-full h-3 mb-6 overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-orange to-orange-l rounded-full transition-all duration-500"
                style={{ width: `${genProgress.total ? (genProgress.current / genProgress.total) * 100 : 0}%` }}
              />
            </div>

            {/* Current lesson info */}
            {generating && (
              <div className="bg-cream-m rounded-xl p-4 mb-4">
                <div className="flex items-center gap-2 text-sm font-medium text-navy mb-1">
                  <FileText className="w-4 h-4 text-orange" />
                  {genProgress.lesson}
                </div>
                <div className="text-xs text-gray">{genProgress.status}</div>
              </div>
            )}

            {/* Streaming text preview */}
            {genProgress.streamingText && (
              <div className="bg-navy text-green-300 rounded-xl p-4 max-h-48 overflow-y-auto text-xs font-mono leading-relaxed">
                {genProgress.streamingText.slice(0, 2000)}
                {genProgress.streamingText.length > 2000 && "..."}
              </div>
            )}

            {/* Generated lessons list */}
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
                <button onClick={() => setStep(1)} className="px-6 py-3 bg-cream-m rounded-xl font-medium text-navy">Back to Plan</button>
                <button onClick={handlePreview} className="px-6 py-3 bg-gradient-to-r from-orange to-orange-l text-white rounded-xl font-semibold flex items-center gap-2 shadow-lg shadow-orange/20">
                  <Eye className="w-5 h-5" /> Preview & Publish
                </button>
              </>
            )}
          </div>
        </div>
      )}

      {/* ─── Step 3: Preview & Publish ─────────────────────────────── */}
      {step === 3 && bundle && previewInfo && (
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
                    onClick={handlePublish}
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
                      onClick={() => setPreviewLesson({ module_title: l.module_title, lesson_title: l.lesson_title })}
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
            <button onClick={() => setStep(2)} className="px-6 py-3 bg-cream-m rounded-xl font-medium text-navy">Back</button>
            {publishResult && (
              <button onClick={resetAll} className="px-6 py-3 bg-navy text-white rounded-xl font-medium flex items-center gap-2">
                <Sparkles className="w-4 h-4" /> Create Another Course
              </button>
            )}
          </div>
        </div>
      )}

      {/* Lesson Preview Modal */}
      {previewLesson && bundle && (
        <Modal open onClose={() => setPreviewLesson(null)} title={`${previewLesson.module_title} › ${previewLesson.lesson_title}`} size="lg"
          footer={<button onClick={() => setPreviewLesson(null)} className="px-6 py-2.5 bg-cream-m rounded-xl font-medium">Close</button>}
        >
          <div className="space-y-6 max-h-[70vh] overflow-y-auto">
            {(() => {
              const key = `${previewLesson.module_title}::${previewLesson.lesson_title}`;
              const content = bundle.lessons?.[key];
              const quiz = bundle.quizzes?.[key];
              const media = bundle.media_prompts?.[key];
              return (
                <>
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
                            <div className="space-y-1 pl-4">
                              {q.options?.map((o: any, oi: number) => (
                                <div key={oi} className={`text-xs px-3 py-1.5 rounded-lg ${o.is_correct ? "bg-green-100 text-green-700 font-medium" : "bg-white/50 text-gray"}`}>
                                  {o.option_text} {o.is_correct && "✓"}
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
                        <Image className="w-4 h-4 text-blue-500" /> Media
                      </h3>
                      <div className="space-y-3">
                        {media.image_prompt && (
                          <div className="bg-blue-50 rounded-xl p-4">
                            <div className="flex items-center justify-between mb-2">
                              <span className="text-xs font-semibold text-blue-600">DALL-E Prompt</span>
                              <button
                                onClick={() => handleGenerateImage(key, media.image_prompt)}
                                disabled={generatingImage === key}
                                className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-500 text-white rounded-lg text-xs font-medium hover:bg-blue-600 disabled:opacity-50"
                              >
                                {generatingImage === key ? (
                                  <Loader2 className="w-3 h-3 animate-spin" />
                                ) : (
                                  <Image className="w-3 h-3" />
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
                </>
              );
            })()}
          </div>
        </Modal>
      )}
    </div>
  );
}
