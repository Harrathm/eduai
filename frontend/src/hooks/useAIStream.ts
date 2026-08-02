import { useState, useCallback, useRef } from "react";

interface UseAIStreamOptions {
  /** Backend URL (default: /api/ai/ask via Vite proxy) */
  apiBase?: string;
  /** JWT token for Authorization header */
  token?: string | null;
}

interface UseAIStreamReturn {
  /** The streamed answer text (updates in real-time) */
  answer: string;
  /** True while streaming is in progress */
  isLoading: boolean;
  /** Error message if the stream failed */
  error: string | null;
  /** The conversation_id returned by the backend */
  conversationId: number | null;
  /** Number of tokens used */
  tokens: number | null;
  /** Send a question and start streaming */
  send: (question: string, conversationId?: number | null) => void;
  /** Reset state */
  reset: () => void;
}

/**
 * Custom hook to consume SSE streaming from `/api/ai/ask`.
 *
 * Usage:
 * ```tsx
 * const { answer, isLoading, error, send } = useAIStream({ token });
 * // In your component:
 * <button onClick={() => send("Qu'est-ce qu'une fraction ?")}>Ask</button>
 * <div>{answer}</div>
 * ```
 */
export function useAIStream(options: UseAIStreamOptions = {}): UseAIStreamReturn {
  const { apiBase = "/api/ai/ask", token } = options;

  const [answer, setAnswer] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [tokens, setTokens] = useState<number | null>(null);

  // Track the active AbortController so we can cancel on re-send
  const abortRef = useRef<AbortController | null>(null);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    setAnswer("");
    setIsLoading(false);
    setError(null);
    setConversationId(null);
    setTokens(null);
  }, []);

  const send = useCallback(
    (question: string, convId?: number | null) => {
      // Cancel any in-flight request
      abortRef.current?.abort();

      const controller = new AbortController();
      abortRef.current = controller;

      setAnswer("");
      setIsLoading(true);
      setError(null);
      setConversationId(null);
      setTokens(null);

      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      };
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      fetch(apiBase, {
        method: "POST",
        headers,
        body: JSON.stringify({
          question,
          conversation_id: convId ?? null,
        }),
        signal: controller.signal,
      })
        .then(async (response) => {
          if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(
              errData.detail || `Erreur HTTP ${response.status}`
            );
          }

          const reader = response.body?.getReader();
          if (!reader) throw new Error("Pas de stream disponible");

          const decoder = new TextDecoder();
          let buffer = "";

          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });

            // Process complete SSE lines
            const lines = buffer.split("\n");
            buffer = lines.pop() || ""; // Keep incomplete line in buffer

            for (const line of lines) {
              const trimmed = line.trim();
              if (!trimmed.startsWith("data: ")) continue;

              const payload = trimmed.slice(6);
              if (!payload || payload === "[DONE]") continue;

              try {
                const data = JSON.parse(payload);

                if (data.error) {
                  setError(data.error);
                  setIsLoading(false);
                  return;
                }

                if (data.chunk) {
                  setAnswer((prev) => prev + data.chunk);
                }

                if (data.done) {
                  if (data.conversation_id) {
                    setConversationId(data.conversation_id);
                  }
                  if (data.tokens) {
                    setTokens(data.tokens);
                  }
                  setIsLoading(false);
                  return;
                }
              } catch {
                // Ignore malformed JSON lines
              }
            }
          }

          // Stream ended without explicit done signal
          setIsLoading(false);
        })
        .catch((err) => {
          if (err.name === "AbortError") {
            // Request was cancelled — not an error
            return;
          }
          setError(err.message || "Erreur de connexion");
          setIsLoading(false);
        });
    },
    [apiBase, token]
  );

  return { answer, isLoading, error, conversationId, tokens, send, reset };
}
