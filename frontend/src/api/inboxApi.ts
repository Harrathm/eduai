/**
 * Inbox API — messages.
 * Extracted from inline fetch calls in InboxPage, AdminInboxView.
 */

import { api } from "./client";

// ─── Types ─────────────────────────────────────────────────────────────────

export interface InboxMessage {
  id: number;
  sender_id: number;
  sender_name: string;
  recipient_id: number;
  subject: string;
  content: string;
  is_read: boolean;
  created_at: string;
}

// ─── Endpoints ──────────────────────────────────────────────────────────────

export const inboxApi = {
  list: (params?: { unread_only?: boolean }) => {
    const sp = new URLSearchParams();
    if (params?.unreadOnly) sp.set("unread_only", "true");
    const qs = sp.toString();
    return api.get<InboxMessage[]>(`/api/inbox/messages${qs ? `?${qs}` : ""}`);
  },

  markRead: (messageId: number) =>
    api.post<void>(`/api/inbox/messages/${messageId}/read`),

  send: (data: { recipient_id: number; subject: string; content: string }) =>
    api.post<InboxMessage>("/api/inbox/messages", data),

  delete: (messageId: number) =>
    api.delete<void>(`/api/inbox/messages/${messageId}`),
};
