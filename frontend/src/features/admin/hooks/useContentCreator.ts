import { useState, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { adminAIFactory } from "../../../api";
import type { AIFactoryPlan, AIFactoryBundle, AIPreviewInfo } from "../../../api";

const LEVELS = ["beginner", "intermediate", "advanced"];
const LEVEL_LABELS: Record<string, string> = { beginner: "Beginner", intermediate: "Intermediate", advanced: "Advanced" };

export type PreviewLesson = { module_title: string; lesson_title: string } | null;

export function useContentCreator() {
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
  const [previewLesson, setPreviewLesson] = useState<PreviewLesson>(null);
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

  const handleGeneratePlan = useCallback(async () => {
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
  }, [topic, useRag]);

  const handlePlanEdit = useCallback((modIdx: number, lesIdx: number | null, field: string, value: string | number) => {
    if (!editedPlan) return;
    const copy = JSON.parse(JSON.stringify(editedPlan));
    if (lesIdx === null) {
      copy.modules[modIdx][field] = value;
    } else {
      copy.modules[modIdx].lessons[lesIdx][field] = value;
    }
    setEditedPlan(copy);
  }, [editedPlan]);

  const setEditedPlanDirectly = useCallback((p: AIFactoryPlan | null) => setEditedPlan(p), []);

  const generateNextLesson = useCallback(async (
    queue: { module_title: string; lesson_title: string; description: string }[],
    idx: number,
    acc: AIFactoryBundle,
    planRef: AIFactoryPlan
  ) => {
    if (idx >= queue.length) {
      const fullBundle: AIFactoryBundle = { plan: planRef, lessons: acc.lessons || {}, quizzes: acc.quizzes || {}, media_prompts: acc.media_prompts || {} };
      setBundle(fullBundle);
      setGenerating(false);
      setGenProgress(p => ({ ...p, status: "Complete!", streamingText: "" }));
      return;
    }
    const item = queue[idx];
    setGenProgress(p => ({ ...p, current: idx + 1, lesson: `${item.module_title} › ${item.lesson_title}`, status: "Generating content...", streamingText: "" }));

    try {
      const streamRes = await adminAIFactory.generateContentStream({
        topic: planRef.title,
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

      const quizRes = await adminAIFactory.generateQuiz({ topic: planRef.title, lesson_title: item.lesson_title, lesson_content: fullContent });
      acc.quizzes = { ...(acc.quizzes || {}), [lessonKey]: quizRes.quiz };

      setGenProgress(p => ({ ...p, status: "Generating media prompts...", streamingText: "" }));
      const mediaRes = await adminAIFactory.generateMediaPrompts({ topic: planRef.title, lesson_title: item.lesson_title, lesson_description: item.description });
      acc.media_prompts = { ...(acc.media_prompts || {}), [lessonKey]: { image_prompt: mediaRes.image_prompt, video_prompt: mediaRes.video_prompt } };

      const updatedBundle: AIFactoryBundle = { plan: planRef, lessons: acc.lessons!, quizzes: acc.quizzes!, media_prompts: acc.media_prompts! };
      setBundle(updatedBundle);
    } catch (err: any) {
      setGenProgress(p => ({ ...p, status: `Error: ${err.message}`, streamingText: "" }));
    }
    generateNextLesson(queue, idx + 1, acc, planRef);
  }, [useRag]);

  const handleStartGeneration = useCallback(() => {
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
  }, [editedPlan, generateNextLesson]);

  const handlePreview = useCallback(async () => {
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
  }, [bundle]);

  const handlePublish = useCallback(async () => {
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
  }, [bundle]);

  const handleGenerateImage = useCallback(async (lessonKey: string, prompt: string) => {
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
  }, [bundle]);

  const handleUploadPDF = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
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
  }, []);

  const handleRemoveFile = useCallback((idx: number) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== idx));
  }, []);

  const resetAll = useCallback(() => {
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
  }, [navigate]);

  const dismissError = useCallback(() => setError(null), []);

  const countLessons = useCallback((p: AIFactoryPlan) => (p.modules || []).reduce((sum, m) => sum + m.lessons.length, 0), []);

  return {
    step, setStep,
    topic, setTopic,
    useRag, setUseRag,
    loading, generating, error, publishing,
    plan, editedPlan, bundle, previewInfo, publishResult,
    previewLesson, setPreviewLesson,
    generatedImages, generatingImage,
    uploadedFiles, uploadingFile,
    fileInputRef,
    genProgress,
    handleGeneratePlan, handlePlanEdit, setEditedPlanDirectly,
    handleStartGeneration, handlePreview, handlePublish,
    handleGenerateImage, handleUploadPDF, handleRemoveFile,
    resetAll, dismissError, countLessons,
    LEVELS, LEVEL_LABELS,
  };
}
