import { useState, useRef, useEffect, useCallback } from "react";
import { conversationApi, type ConversationSummary } from "../../../api";
import { tokenStorage } from "../../../utils/tokenStorage";

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: any[];
  detected_language?: string | null;
}

const BASE_URL = import.meta.env.VITE_API_URL || "";

export function detectInputDirection(text: string): "ltr" | "rtl" {
  if (!text) return "ltr";
  const arabic = text.replace(/[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]/g, "").length;
  const total = text.replace(/\s/g, "").length;
  if (total === 0) return "ltr";
  return arabic / total > 0.3 ? "rtl" : "ltr";
}

export function formatTime(iso: string | null): string {
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

export const CONTEXT_HINTS = [
  "Explique-moi le concept de...",
  "Résume cette leçon en 3 points",
  "Donne-moi un exemple concret",
  "Comment appliquer cela en pratique?",
  "Quiz moi sur ce chapitre",
  "Quelle est la différence entre...",
];

export function useAIChat() {
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

  const loadConversations = useCallback(async () => {
    try {
      const convs = await conversationApi.list();
      setConversations(convs);
    } catch {}
  }, []);

  const handleInputChange = useCallback((value: string) => {
    setInput(value);
    if (directionTimerRef.current) clearTimeout(directionTimerRef.current);
    directionTimerRef.current = setTimeout(() => {
      setInputDirection(detectInputDirection(value));
    }, 300);
  }, []);

  const startNew = useCallback(() => {
    setMessages([]);
    setActiveConvId(null);
    inputRef.current?.focus();
  }, []);

  const openConversation = useCallback(async (convId: number) => {
    try {
      const detail = await conversationApi.get(convId);
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
  }, []);

  const handleDeleteConversation = useCallback(async (convId: number) => {
    try {
      await conversationApi.delete(convId);
      setConversations((prev) => prev.filter((c) => c.id !== convId));
      if (activeConvId === convId) startNew();
      setDeleteConfirmId(null);
    } catch {}
  }, [activeConvId, startNew]);

  const sendMessage = useCallback(async (text?: string) => {
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
      const token = tokenStorage.getToken();

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
  }, [input, loading, activeConvId, loadConversations]);

  const handleExportMessage = useCallback(async (
    msgId: string,
    content: string,
    role: string,
    format: "pdf" | "docx"
  ) => {
    setExportingId(`${msgId}-${format}`);
    try {
      if (format === "pdf") {
        await conversationApi.exportMessagePdf(content, role);
      } else {
        await conversationApi.exportMessageDocx(content, role);
      }
    } catch {
    } finally {
      setExportingId(null);
    }
  }, []);

  const handleExportAll = useCallback(() => {
    if (!activeConvId) return;
    const conv = conversations.find((c) => c.id === activeConvId);
    if (!conv) return;
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
  }, [activeConvId, conversations, messages]);

  const filteredConversations = conversations.filter(
    (c) =>
      c.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.summary?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const showWelcome = messages.length === 0;

  return {
    messages, input, loading, activeConvId,
    conversations, filteredConversations,
    exportingId, deleteConfirmId, searchQuery, inputDirection,
    messagesEndRef, inputRef,
    setSearchQuery, setDeleteConfirmId,
    handleInputChange, startNew, openConversation,
    handleDeleteConversation, sendMessage,
    handleExportMessage, handleExportAll,
    showWelcome,
  };
}
