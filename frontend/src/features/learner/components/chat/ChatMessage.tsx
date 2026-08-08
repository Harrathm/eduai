import { Loader2, Bot, User, FileText, File } from "lucide-react";
import type { Message } from "../../hooks/useAIChat";
import { Button } from "@/components/ui";

type Props = {
  msg: Message;
  exportingId: string | null;
  onExport: (msgId: string, content: string, role: string, format: "pdf" | "docx") => void;
};

export function ChatMessage({ msg, exportingId, onExport }: Props) {
  const isRtl = msg.detected_language === "ar";
  const textDir = isRtl ? "rtl" : "ltr";
  const textAlign = isRtl ? "right" : "left";

  return (
    <div className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
      {msg.role === "assistant" && (
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-navy to-navy-m flex items-center justify-center flex-shrink-0 shadow-sm">
          <Bot className="w-4 h-4 text-white" />
        </div>
      )}
      <div className="max-w-[75%] group">
        <div
          className={`px-4 py-3 ${
            msg.role === "user"
              ? "bg-gradient-to-br from-orange to-orange-l text-white rounded-2xl rounded-tr-sm shadow-sm"
              : "bg-white border border-gray-100 text-gray-800 rounded-2xl rounded-tl-sm shadow-sm"
          }`}
          dir={textDir}
          style={{ textAlign }}
        >
          <p className="whitespace-pre-wrap text-sm leading-relaxed">
            {msg.content}
          </p>
          {msg.sources && msg.sources.length > 0 && (
            <div className="mt-2 pt-2 border-t border-gray-100">
              <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-1">
                Sources
              </p>
              {msg.sources.slice(0, 3).map((s: any, i: number) => (
                <div
                  key={i}
                  className="text-xs text-gray-500 truncate flex items-center gap-1"
                >
                  <span className="w-1 h-1 rounded-full bg-orange/40 flex-shrink-0" />
                  {s.title || s.text?.substring(0, 60)}
                </div>
              ))}
            </div>
          )}
        </div>
        {msg.role === "assistant" && !msg.id.startsWith("welcome") && (
          <div className="flex gap-1.5 mt-1.5 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onExport(msg.id, msg.content, msg.role, "pdf")}
              disabled={exportingId === `${msg.id}-pdf`}
            >
              {exportingId === `${msg.id}-pdf` ? (
                <Loader2 className="w-3 h-3 animate-spin" />
              ) : (
                <FileText className="w-3 h-3" />
              )}
              PDF
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onExport(msg.id, msg.content, msg.role, "docx")}
              disabled={exportingId === `${msg.id}-docx`}
            >
              {exportingId === `${msg.id}-docx` ? (
                <Loader2 className="w-3 h-3 animate-spin" />
              ) : (
                <File className="w-3 h-3" />
              )}
              DOCX
            </Button>
          </div>
        )}
      </div>
      {msg.role === "user" && (
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-orange to-orange-l flex items-center justify-center flex-shrink-0 shadow-sm">
          <User className="w-4 h-4 text-white" />
        </div>
      )}
    </div>
  );
}

export function TypingIndicator() {
  return (
    <div className="flex gap-3 justify-start">
      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-navy to-navy-m flex items-center justify-center flex-shrink-0 shadow-sm">
        <Bot className="w-4 h-4 text-white" />
      </div>
      <div className="bg-white border border-gray-100 px-5 py-3.5 rounded-2xl rounded-tl-sm shadow-sm">
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 bg-orange/60 rounded-full animate-bounce [animation-delay:0ms]" />
          <span className="w-2 h-2 bg-orange/60 rounded-full animate-bounce [animation-delay:150ms]" />
          <span className="w-2 h-2 bg-orange/60 rounded-full animate-bounce [animation-delay:300ms]" />
        </div>
      </div>
    </div>
  );
}
