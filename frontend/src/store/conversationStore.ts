/**
 * Store Zustand pour les conversations IA
 */
import { create } from "zustand";
import {
  listConversations,
  getConversation,
  createConversation,
  addMessage,
  deleteConversation,
  deleteAllConversations,
  type ConversationSummary,
  type ConversationDetail,
  type ChatMessage,
} from "../api/conversations";

interface ConversationState {
  conversations: ConversationSummary[];
  activeConversation: ConversationDetail | null;
  loading: boolean;
  error: string | null;

  fetchConversations: () => Promise<void>;
  openConversation: (id: number) => Promise<void>;
  startNewConversation: (title?: string, subject?: string) => Promise<ConversationDetail>;
  sendMessage: (conversationId: number, role: "user" | "assistant", content: string) => Promise<void>;
  removeConversation: (id: number) => Promise<void>;
  clearAll: () => Promise<void>;
  resetActive: () => void;
}

export const useConversationStore = create<ConversationState>((set, get) => ({
  conversations: [],
  activeConversation: null,
  loading: false,
  error: null,

  fetchConversations: async () => {
    set({ loading: true, error: null });
    try {
      const convs = await listConversations();
      set({ conversations: convs, loading: false });
    } catch (e: any) {
      set({ error: e.message, loading: false });
    }
  },

  openConversation: async (id: number) => {
    set({ loading: true, error: null });
    try {
      const conv = await getConversation(id);
      set({ activeConversation: conv, loading: false });
    } catch (e: any) {
      set({ error: e.message, loading: false });
    }
  },

  startNewConversation: async (title?: string, subject?: string) => {
    const conv = await createConversation(title, subject);
    const detail: ConversationDetail = {
      id: conv.id,
      title: conv.title,
      subject: conv.subject,
      created_at: conv.created_at,
      updated_at: conv.updated_at,
      messages: [],
    };
    set((s) => ({
      activeConversation: detail,
      conversations: [conv, ...s.conversations],
    }));
    return detail;
  },

  sendMessage: async (conversationId: number, role: "user" | "assistant", content: string) => {
    await addMessage(conversationId, role, content);
    const msg: ChatMessage = { role, content, created_at: new Date().toISOString() };
    set((s) => {
      if (s.activeConversation && s.activeConversation.id === conversationId) {
        return {
          activeConversation: {
            ...s.activeConversation,
            messages: [...s.activeConversation.messages, msg],
          },
        };
      }
      return {};
    });
  },

  removeConversation: async (id: number) => {
    await deleteConversation(id);
    set((s) => ({
      conversations: s.conversations.filter((c) => c.id !== id),
      activeConversation: s.activeConversation?.id === id ? null : s.activeConversation,
    }));
  },

  clearAll: async () => {
    await deleteAllConversations();
    set({ conversations: [], activeConversation: null });
  },

  resetActive: () => set({ activeConversation: null }),
}));
