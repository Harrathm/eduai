import { useState, useRef, useEffect, useCallback } from "react";
import {
  Send, Bot, User, Loader2, Plus, History, MessageSquare,
  FileText, File, Trash2, Search, Sparkles, Clock,
} from "lucide-react";
import {
  listConversations,
  getConversation,
  deleteConversation,
  exportMessagePdf,
  exportMessageDocx,
  type ConversationSummary,
} from "../../api/conversations";

const BASE_URL = "";
function getToken() {
  return localStorage.getItem("token");
}

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: any[];
  detected_language?: string | null;
}

const CONTEXT_HINTS = [
  "Explique-moi le concept de...",
  "Résume cette leçon en 3 points",
  "Donne-moi un exemple concret",
  "Comment appliquer cela en pratique?",
  "Quiz moi sur ce chapitre",
  "Quelle est la différence entre...",
];

function formatTime(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  if (diffMins < 1) return "à l'instant";
  if (diffMins < 60) return `il y a ${diffMins}min`;
  const diffH = Math.floor(diffMins / 60);
  if (diffH < 24) return `il y a ${diffH}h`;
  return d.toLocaleDateString("fr-FR", { day: "numeric", month: "short" });
}

function detectInputDirection(text: string): "ltr" | "rtl" {
  if (!text) return "ltr";
  const arabic = text.replace(/[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]/g, "").length;
  const total = text.replace(/\s/g, "").length;
  if (total === 0) return "ltr";
  return arabic / total > 0.3 ? "rtl" : "ltr";
}

function TypingIndicator() {
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

function WelcomeMessage({ onHintClick }: { onHintClick: (hint: string) => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4">
      <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-orange to-orange-l flex items-center justify-center mb-6 shadow-or">
        <Sparkles className="w-8 h-8 text-white" />
      </div>
      <h2 className="text-2xl font-semibold text-navy mb-2 font-body">
        Bonjour ! Je suis votre tuteur IA
      </h2>
      <p className="text-gray-500 text-center max-w-md mb-8 leading-relaxed">
        Posez-moi des questions sur vos cours, demandez des explications,
        des résumés ou des exercices.
      </p>
      <div className="grid grid-cols-2 gap-3 max-w-lg">
        {CONTEXT_HINTS.map((hint, i) => (
          <button
            key={i}
            onClick={() => onHintClick(hint)}
            className="text-left px-4 py-3 text-sm bg-white border border-gray-100 rounded-xl hover:border-orange/30 hover:bg-orange-p text-gray-600 hover:text-navy transition-all duration-200 shadow-sm"
          >
            {hint}
          </button>
        ))}
      </div>
    </div>
  );
}

export default function LearnerAIChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [activeConvId, setActiveConvId] = useState<number | null>(null);
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [exportingId, setExportingId] = useState<string | null>(null);
  const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [inputDirection, setInputDirection] = useState<"ltr" | "rtl">("ltr");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const directionTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    loadConversations();
  }, []);

  const loadConversations = async () => {
    try {
      const convs = await listConversations();
      setConversations(convs);
    } catch {}
  };

  const handleInputChange = useCallback((value: string) => {
    setInput(value);
    if (directionTimerRef.current) clearTimeout(directionTimerRef.current);
    directionTimerRef.current = setTimeout(() => {
      setInputDirection(detectInputDirection(value));
    }, 300);
  }, []);

  const startNew = () => {
    setMessages([]);
    setActiveConvId(null);
    inputRef.current?.focus();
  };

  const openConversation = async (convId: number) => {
    try {
      const detail = await getConversation(convId);
      const loaded: Message[] = detail.messages.map((m: any, i: number) => ({
        id: `loaded-${i}`,
        role: m.role,
        content: m.content,
        detected_language: m.detected_language,
      }));
      setMessages(loaded);
      setActiveConvId(convId);
    } catch {
      setMessages([]);
    }
  };

  const handleDeleteConversation = async (convId: number) => {
    try {
      await deleteConversation(convId);
      setConversations((prev) => prev.filter((c) => c.id !== convId));
      if (activeConvId === convId) startNew();
      setDeleteConfirmId(null);
    } catch {}
  };

  const sendMessage = async (text?: string) => {
    const textToSend = text || input.trim();
    if (!textToSend || loading) return;
    setLoading(true);

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: textToSend,
    };
    setMessages((prev) => [...prev, userMsg]);
    const streamId = "stream-" + Date.now();
    setMessages((prev) => [
      ...prev,
      { id: streamId, role: "assistant" as const, content: "" },
    ]);
    setInput("");

    try {
      const token = getToken();

      const res = await fetch(`${BASE_URL}/api/ai/ask`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          question: textToSend,
          conversation_id: activeConvId,
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `HTTP ${res.status}`);
      }

      const reader = res.body?.getReader();
      const decoder = new TextDecoder();
      let answer = "";
      let returnedConvId: string | null = null;

      if (reader) {
        let buffer = "";
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";
          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            try {
              const event = JSON.parse(line.slice(6));
              if (event.error) {
                answer = event.error;
                break;
              }
              if (event.chunk) {
                answer += event.chunk;
                setMessages((prev) => {
                  const updated = [...prev];
                  const last = updated[updated.length - 1];
                  if (last && last.role === "assistant" && last.id.startsWith("stream-")) {
                    updated[updated.length - 1] = { ...last, content: answer };
                  }
                  return updated;
                });
              }
              if (event.conversation_id) {
                returnedConvId = event.conversation_id;
              }
            } catch {
              // skip malformed lines
            }
          }
        }
      }

      const streamMsgId = "stream-" + Date.now();
      setMessages((prev) => {
        const withoutPlaceholder = prev.filter(
          (m) => !m.id.startsWith("stream-")
        );
        return [
          ...withoutPlaceholder,
          {
            id: streamMsgId,
            role: "assistant",
            content: answer || "Je n'ai pas pu générer de réponse.",
          },
        ];
      });

      if (returnedConvId && !activeConvId) {
        setActiveConvId(returnedConvId);
        setConversations((prev) => [
          {
            id: returnedConvId,
            title: textToSend.slice(0, 80),
            subject: null,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            message_count: 0,
            summary: textToSend.slice(0, 120),
          },
          ...prev,
        ]);
      }

      loadConversations();
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content:
            "Désolé, je n'ai pas pu répondre. Vérifiez votre connexion et réessayez.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleExportMessage = async (
    msgId: string,
    content: string,
    role: string,
    format: "pdf" | "docx"
  ) => {
    setExportingId(`${msgId}-${format}`);
    try {
      if (format === "pdf") {
        await exportMessagePdf(content, role);
      } else {
        await exportMessageDocx(content, role);
      }
    } catch {
    } finally {
      setExportingId(null);
    }
  };

  const filteredConversations = conversations.filter(
    (c) =>
      c.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.summary?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const showWelcome = messages.length === 0;

  return (
    <div className="flex h-[calc(100vh-64px)] bg-cream-m">
      {/* ── Sidebar ── */}
      <aside className="w-80 bg-white border-r border-gray-100 flex flex-col flex-shrink-0">
        {/* Header sidebar */}
        <div className="p-5 border-b border-gray-100">
          <div className="flex items-center gap-2.5 mb-4">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-orange to-orange-l flex items-center justify-center shadow-sm">
              <MessageSquare className="w-4.5 h-4.5 text-white" />
            </div>
            <div>
              <h2 className="font-semibold text-navy text-sm">Assistant IA</h2>
              <p className="text-xs text-gray-400">Tuteur personnel</p>
            </div>
          </div>

          <button
            onClick={startNew}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-gradient-to-r from-orange to-orange-l text-white rounded-xl text-sm font-medium hover:shadow-or transition-all duration-200"
          >
            <Plus className="w-4 h-4" />
            Nouvelle conversation
          </button>
        </div>

        {/* Recherche */}
        <div className="px-4 py-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Rechercher..."
              className="w-full pl-9 pr-3 py-2 text-sm bg-gray-50 border border-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange/20 focus:border-orange/40 transition-all"
            />
          </div>
        </div>

        {/* Liste conversations */}
        <div className="flex-1 overflow-y-auto px-3 pb-4">
          <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider px-2 mb-2">
            Récent
          </p>
          <div className="space-y-0.5">
            {filteredConversations.length === 0 && (
              <p className="text-xs text-gray-400 text-center py-6">
                {searchQuery ? "Aucun résultat" : "Aucune conversation"}
              </p>
            )}
            {filteredConversations.slice(0, 20).map((conv) => (
              <div key={conv.id} className="group relative">
                <button
                  onClick={() => openConversation(conv.id)}
                  className={`w-full text-left px-3 py-2.5 rounded-lg transition-all duration-150 pr-9 ${
                    activeConvId === conv.id
                      ? "bg-orange-p border border-orange/10"
                      : "hover:bg-gray-50 border border-transparent"
                  }`}
                >
                  <p
                    className={`text-sm truncate ${
                      activeConvId === conv.id
                        ? "text-orange font-medium"
                        : "text-gray-700"
                    }`}
                  >
                    {conv.title}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <Clock className="w-3 h-3 text-gray-400" />
                    <span className="text-[10px] text-gray-400">
                      {formatTime(conv.updated_at)}
                    </span>
                    {conv.message_count > 0 && (
                      <>
                        <span className="text-[10px] text-gray-300">·</span>
                        <span className="text-[10px] text-gray-400">
                          {conv.message_count} msg
                        </span>
                      </>
                    )}
                  </div>
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setDeleteConfirmId(
                      deleteConfirmId === conv.id ? null : conv.id
                    );
                  }}
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded-md opacity-0 group-hover:opacity-100 hover:bg-red-50 text-gray-400 hover:text-red-500 transition-all"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
                {deleteConfirmId === conv.id && (
                  <div className="absolute right-0 top-full mt-1 bg-white border border-gray-200 rounded-xl shadow-dp p-2 z-10 flex gap-1.5">
                    <button
                      onClick={() => handleDeleteConversation(conv.id)}
                      className="px-3 py-1.5 text-xs bg-red-500 text-white rounded-lg hover:bg-red-600 font-medium"
                    >
                      Supprimer
                    </button>
                    <button
                      onClick={() => setDeleteConfirmId(null)}
                      className="px-3 py-1.5 text-xs bg-gray-100 rounded-lg hover:bg-gray-200 text-gray-600"
                    >
                      Annuler
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </aside>

      {/* ── Zone de chat ── */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header chat */}
        {activeConvId && (
          <div className="px-6 py-3 bg-white border-b border-gray-100 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-green-400" />
              <span className="text-sm font-medium text-navy">
                {conversations.find((c) => c.id === activeConvId)?.title ||
                  "Conversation"}
              </span>
            </div>
            <div className="flex items-center gap-1">
              <button
                onClick={() => {
                  if (activeConvId) {
                    const conv = conversations.find((c) => c.id === activeConvId);
                    if (conv) {
                      const allContent = messages
                        .filter((m) => !m.id.startsWith("welcome"))
                        .map((m) => `[${m.role === "user" ? "Vous" : "IA"}] ${m.content}`)
                        .join("\n\n");
                      const blob = new Blob([allContent], { type: "text/plain" });
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement("a");
                      a.href = url;
                      a.download = `${conv.title.slice(0, 50)}.txt`;
                      a.click();
                      URL.revokeObjectURL(url);
                    }
                  }
                }}
                className="px-3 py-1.5 text-xs text-gray-500 hover:text-navy hover:bg-gray-100 rounded-lg transition-colors"
              >
                Tout exporter
              </button>
            </div>
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto">
          {showWelcome ? (
            <WelcomeMessage onHintClick={sendMessage} />
          ) : (
            <div className="max-w-3xl mx-auto px-6 py-6 space-y-6">
              {messages.map((msg) => {
                const isRtl = msg.detected_language === "ar";
                const textDir = isRtl ? "rtl" : "ltr";
                const textAlign = isRtl ? "right" : "left";
                return (
                <div
                  key={msg.id}
                  className={`flex gap-3 ${
                    msg.role === "user" ? "justify-end" : "justify-start"
                  }`}
                >
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
                    {/* Export buttons — visible on hover */}
                    {msg.role === "assistant" && !msg.id.startsWith("welcome") && (
                      <div className="flex gap-1.5 mt-1.5 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                        <button
                          onClick={() =>
                            handleExportMessage(msg.id, msg.content, msg.role, "pdf")
                          }
                          disabled={exportingId === `${msg.id}-pdf`}
                          className="flex items-center gap-1 px-2 py-1 text-[11px] bg-white border border-gray-200 rounded-md hover:border-orange/30 hover:bg-orange-p text-gray-400 hover:text-orange transition-all disabled:opacity-50"
                        >
                          {exportingId === `${msg.id}-pdf` ? (
                            <Loader2 className="w-3 h-3 animate-spin" />
                          ) : (
                            <FileText className="w-3 h-3" />
                          )}
                          PDF
                        </button>
                        <button
                          onClick={() =>
                            handleExportMessage(msg.id, msg.content, msg.role, "docx")
                          }
                          disabled={exportingId === `${msg.id}-docx`}
                          className="flex items-center gap-1 px-2 py-1 text-[11px] bg-white border border-gray-200 rounded-md hover:border-orange/30 hover:bg-orange-p text-gray-400 hover:text-orange transition-all disabled:opacity-50"
                        >
                          {exportingId === `${msg.id}-docx` ? (
                            <Loader2 className="w-3 h-3 animate-spin" />
                          ) : (
                            <File className="w-3 h-3" />
                          )}
                          DOCX
                        </button>
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
              })}

              {loading && !messages.some((m) => m.id.startsWith("stream-")) && <TypingIndicator />}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Zone de saisie */}
        <div className="p-4 bg-white border-t border-gray-100">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              sendMessage();
            }}
            className="max-w-3xl mx-auto"
          >
            <div className="flex items-center gap-2 bg-gray-50 border border-gray-200 rounded-2xl px-4 py-2 focus-within:border-orange/40 focus-within:ring-2 focus-within:ring-orange/10 transition-all">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => handleInputChange(e.target.value)}
                placeholder={inputDirection === "rtl" ? "اكتب سؤالك هنا..." : "Posez une question à votre tuteur IA..."}
                dir={inputDirection}
                disabled={loading}
                className="flex-1 bg-transparent text-sm text-gray-800 placeholder-gray-400 focus:outline-none disabled:opacity-50 py-1"
              />
              <button
                type="submit"
                disabled={!input.trim() || loading}
                className="w-9 h-9 flex items-center justify-center bg-gradient-to-r from-orange to-orange-l text-white rounded-xl hover:shadow-or disabled:opacity-30 disabled:cursor-not-allowed transition-all duration-200 flex-shrink-0"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
            <p className="text-[10px] text-gray-400 text-center mt-2">
              L'IA peut faire des erreurs. Vérifiez les informations importantes.
            </p>
          </form>
        </div>
      </div>
    </div>
  );
}
