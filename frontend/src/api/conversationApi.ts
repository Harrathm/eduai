/**
 * Conversation API — conversations CRUD, messages, exports.
 * Migrated from conversations.ts — now uses centralized apiClient.
 */

import { api } from "./client";

// ─── Types ─────────────────────────────────────────────────────────────────

export interface ConversationSummary {
  id: number;
  title: string;
  subject: string | null;
  created_at: string | null;
  updated_at: string | null;
  message_count: number;
  summary: string;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  created_at: string | null;
  detected_language?: string | null;
}

export interface ConversationDetail {
  id: number;
  title: string;
  subject: string | null;
  created_at: string | null;
  updated_at: string | null;
  messages: ChatMessage[];
}

// ─── Endpoints ──────────────────────────────────────────────────────────────

export const conversationApi = {
  list: () => api.get<ConversationSummary[]>("/api/conversations"),

  get: (id: number) => api.get<ConversationDetail>(`/api/conversations/${id}`),

  create: (title?: string, subject?: string) =>
    api.post<ConversationSummary>("/api/conversations", {
      title: title || "Nouvelle conversation",
      subject,
    }),

  addMessage: (conversationId: number, role: "user" | "assistant", content: string) =>
    api.post<{ ok: boolean; message_id: number }>(
      `/api/conversations/${conversationId}/messages`,
      { role, content }
    ),

  delete: (id: number) => api.delete<{ ok: boolean }>(`/api/conversations/${id}`),

  deleteAll: () => api.delete<{ ok: boolean; deleted: number }>("/api/conversations"),

  downloadExport: async (conversationId: number, format: "pdf" | "docx") => {
    const { tokenStorage } = await import("../utils/tokenStorage");
    const token = tokenStorage.getToken();
    const response = await fetch(`/api/conversations/${conversationId}/export/${format}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!response.ok) throw new Error("Erreur lors de l'export");
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `conversation_${conversationId}.${format}`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  },

  exportMessagePdf: async (content: string, role = "assistant", title?: string) => {
    const { tokenStorage } = await import("../utils/tokenStorage");
    const token = tokenStorage.getToken();
    const response = await fetch("/api/conversations/export/message/pdf", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ content, role, title }),
    });
    if (!response.ok) throw new Error("Erreur lors de l'export PDF");
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "message_ia.pdf";
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  },

  exportMessageDocx: async (content: string, role = "assistant", title?: string) => {
    const { tokenStorage } = await import("../utils/tokenStorage");
    const token = tokenStorage.getToken();
    const response = await fetch("/api/conversations/export/message/docx", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ content, role, title }),
    });
    if (!response.ok) throw new Error("Erreur lors de l'export DOCX");
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "message_ia.docx";
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  },
};
