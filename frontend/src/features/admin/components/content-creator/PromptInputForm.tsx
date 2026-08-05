import { useState, useRef } from "react";
import { Sparkles, Loader2, Upload, File, X } from "lucide-react";

type Props = {
  topic: string;
  onTopicChange: (v: string) => void;
  useRag: boolean;
  onUseRagChange: (v: boolean) => void;
  uploadedFiles: { name: string; chunks: number }[];
  uploadingFile: boolean;
  fileInputRef: React.RefObject<HTMLInputElement>;
  onUploadPDF: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onRemoveFile: (idx: number) => void;
  onGenerate: () => void;
  loading: boolean;
};

export function PromptInputForm({
  topic, onTopicChange,
  useRag, onUseRagChange,
  uploadedFiles, uploadingFile,
  fileInputRef, onUploadPDF, onRemoveFile,
  onGenerate, loading,
}: Props) {
  return (
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
          onChange={e => onTopicChange(e.target.value)}
          placeholder="e.g., Introduction to Machine Learning, Advanced French Grammar, Web Development with React..."
          className="w-full h-28 px-5 py-4 bg-cream-m rounded-2xl border border-black/5 text-sm focus:outline-none focus:ring-2 focus:ring-orange/20 resize-none"
        />

        <label className="flex items-center gap-3 px-4 py-3 bg-cream-m rounded-xl cursor-pointer">
          <input type="checkbox" checked={useRag} onChange={e => onUseRagChange(e.target.checked)} className="rounded border-gray-300 text-orange focus:ring-orange" />
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
              onChange={onUploadPDF}
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
                    <button onClick={() => onRemoveFile(i)} className="text-gray hover:text-red-500 transition-colors">
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        <button
          onClick={onGenerate}
          disabled={loading || !topic.trim()}
          className="w-full py-4 bg-gradient-to-r from-orange to-orange-l text-white rounded-2xl font-semibold text-lg disabled:opacity-50 flex items-center justify-center gap-3 shadow-lg shadow-orange/20"
        >
          {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Sparkles className="w-5 h-5" />}
          {loading ? "Generating Course Plan..." : "Generate Course Plan"}
        </button>
      </div>
    </div>
  );
}
