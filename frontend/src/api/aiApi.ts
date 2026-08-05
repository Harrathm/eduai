/**
 * AI API — AI tutor (ask, explain, correct, generate), streaming SSE.
 * Extracted from inline fetch calls in LearnerAIChatPage, TeacherAIStudio, etc.
 */

import { api } from "./client";
import { tokenStorage } from "../utils/tokenStorage";

// ─── Types ─────────────────────────────────────────────────────────────────

export interface AIRequest {
  question: string;
  subject?: string;
  level?: string;
  language?: string;
  conversation_id?: number;
}

export interface AIResponse {
  answer: string;
  sources?: { title: string; url: string }[];
  detected_language?: string;
}

// ─── Endpoints ──────────────────────────────────────────────────────────────

export const aiApi = {
  ask: (data: AIRequest) => api.post<AIResponse>("/api/ai/ask", data),

  explain: (data: { content: string; level?: string }) =>
    api.post<AIResponse>("/api/ai/explain", data),

  correct: (data: { content: string; subject?: string }) =>
    api.post<AIResponse>("/api/ai/correct", data),

  generate: (data: { prompt: string; type?: string }) =>
    api.post<AIResponse>("/api/ai/generate", data),

  history: () => api.get<any[]>("/api/ai/history"),

  wallet: () => api.get<any>("/api/wallet/balance"),

  /**
   * Streaming SSE — returns a ReadableStream for AI responses.
   * Uses raw fetch with Authorization header (not api.fetch).
   */
  streamAsk: async (data: AIRequest): Promise<ReadableStream<Uint8Array>> => {
    const API_URL = import.meta.env.VITE_API_URL || "";
    const token = tokenStorage.getToken();
    const response = await fetch(`${API_URL}/api/ai/stream-ask`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || `AI streaming error ${response.status}`);
    }
    if (!response.body) throw new Error("No response body");
    return response.body;
  },
};
