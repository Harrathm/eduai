/**
 * Module API pour les conversations IA
 * Utilise le client API centralisé pour la gestion de l'authentification
 */

import { api } from "../utils/apiClient";

// ── Types ──────────────────────────────────────────────

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

// ── Endpoints ──────────────────────────────────────────

export async function listConversations(): Promise<ConversationSummary[]> {
  return api.get("/api/conversations");
}

export async function getConversation(id: number): Promise<ConversationDetail> {
  return api.get(`/api/conversations/${id}`);
}

export async function createConversation(
  title?: string,
  subject?: string
): Promise<ConversationSummary> {
  return api.post("/api/conversations", { title: title || "Nouvelle conversation", subject });
}

export async function addMessage(
  conversationId: number,
  role: "user" | "assistant",
  content: string
): Promise<{ ok: boolean; message_id: number }> {
  return api.post(`/api/conversations/${conversationId}/messages`, { role, content });
}

export async function deleteConversation(id: number): Promise<{ ok: boolean }> {
  return api.delete(`/api/conversations/${id}`);
}

export async function deleteAllConversations(): Promise<{ ok: boolean; deleted: number }> {
  return api.delete("/api/conversations");
}

export function getExportUrl(conversationId: number, format: "pdf" | "docx"): string {
  const token = localStorage.getItem("token");
  return `/api/conversations/${conversationId}/export/${format}?token=${token}`;
}

// ── Export de message unique ────────────────────────────

export async function exportMessagePdf(
  content: string,
  role: string = "assistant",
  title?: string
): Promise<void> {
  const response = await fetch("/api/conversations/export/message/pdf", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${localStorage.getItem("token")}`,
    },
    body: JSON.stringify({ content, role, title }),
  });
  
  if (!response.ok) {
    throw new Error("Erreur lors de l'export PDF");
  }
  
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `message_ia.pdf`;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}

export async function exportMessageDocx(
  content: string,
  role: string = "assistant",
  title?: string
): Promise<void> {
  const response = await fetch("/api/conversations/export/message/docx", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${localStorage.getItem("token")}`,
    },
    body: JSON.stringify({ content, role, title }),
  });
  
  if (!response.ok) {
    throw new Error("Erreur lors de l'export DOCX");
  }
  
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `message_ia.docx`;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}
