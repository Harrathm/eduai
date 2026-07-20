import { useState, useEffect } from "react";
import { useAuthStore } from "../../../store/authStore";

const API_URL = "";

interface InboxMessage {
  id: number;
  type: string;
  subject: string;
  body: string;
  sender_id: number;
  sender_name: string;
  is_read: boolean;
  created_at: string;
  target_audience?: string;
}

export default function InboxPage() {
  const { token } = useAuthStore();
  const [messages, setMessages] = useState<InboxMessage[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<InboxMessage | null>(null);
  const [filter, setFilter] = useState<"all" | "unread">("all");

  const fetchMessages = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ skip: "0", limit: "50" });
      if (filter === "unread") params.set("unread_only", "true");
      const res = await fetch(`${API_URL}/api/inbox/messages?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setMessages(data.items || []);
        setTotal(data.total || 0);
        setUnreadCount(data.unread || 0);
      }
    } catch (err) {
      console.error("Failed to load inbox", err);
    }
    setLoading(false);
  };

  useEffect(() => { fetchMessages(); }, [filter]);

  const markRead = async (id: number) => {
    try {
      await fetch(`${API_URL}/api/inbox/messages/${id}/read`, {
        method: "PUT",
        headers: { Authorization: `Bearer ${token}` },
      });
      setMessages((prev) =>
        prev.map((m) => (m.id === id ? { ...m, is_read: true } : m))
      );
      setUnreadCount((prev) => Math.max(0, prev - 1));
    } catch (err) {
      console.error("Failed to mark as read", err);
    }
  };

  const openMessage = (msg: InboxMessage) => {
    setSelected(msg);
    if (!msg.is_read) markRead(msg.id);
  };

  const formatDate = (d: string) => {
    const date = new Date(d);
    return date.toLocaleDateString("fr-FR", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-[300] text-navy">Boîte de réception</h1>
          <p className="text-gray text-sm mt-1">{total} message(s), {unreadCount} non lu(s)</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setFilter("all")}
            className={`px-4 py-2 rounded-xl text-sm font-semibold transition-all ${
              filter === "all" ? "bg-navy text-white" : "bg-cream-m text-gray hover:text-navy"
            }`}
          >
            Tous
          </button>
          <button
            onClick={() => setFilter("unread")}
            className={`px-4 py-2 rounded-xl text-sm font-semibold transition-all ${
              filter === "unread" ? "bg-navy text-white" : "bg-cream-m text-gray hover:text-navy"
            }`}
          >
            Non lus {unreadCount > 0 && `(${unreadCount})`}
          </button>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-black/5 overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-gray">Chargement...</div>
        ) : messages.length === 0 ? (
          <div className="p-12 text-center text-gray">
            <svg className="w-12 h-12 mx-auto mb-4 text-gray/30" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75" />
            </svg>
            Aucun message
          </div>
        ) : (
          <div className="divide-y divide-black/5">
            {messages.map((msg) => (
              <button
                key={msg.id}
                onClick={() => openMessage(msg)}
                className={`w-full text-left px-6 py-4 hover:bg-cream-m/50 transition-colors ${
                  !msg.is_read ? "bg-orange/5" : ""
                }`}
              >
                <div className="flex items-start gap-4">
                  <div className={`w-2 h-2 rounded-full mt-2 flex-shrink-0 ${
                    msg.is_read ? "bg-transparent" : "bg-orange"
                  }`} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-4">
                      <p className={`text-sm truncate ${!msg.is_read ? "font-semibold text-navy" : "text-gray"}`}>
                        {msg.subject}
                      </p>
                      <span className="text-xs text-gray flex-shrink-0">{formatDate(msg.created_at)}</span>
                    </div>
                    <p className="text-xs text-gray mt-1">
                      De : {msg.sender_name}
                      {msg.target_audience && msg.target_audience !== "specific" && (
                        <span className="ml-2 px-2 py-0.5 bg-cream-m rounded-full text-[10px]">
                          {msg.target_audience}
                        </span>
                      )}
                    </p>
                    <p className="text-xs text-gray/60 mt-1 truncate">
                      {msg.body.substring(0, 100)}...
                    </p>
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Message detail modal */}
      {selected && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4" onClick={() => setSelected(null)}>
          <div className="bg-white rounded-2xl max-w-lg w-full max-h-[80vh] overflow-y-auto p-8" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-navy">{selected.subject}</h3>
              <button onClick={() => setSelected(null)} className="text-gray hover:text-navy">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="flex items-center gap-3 mb-4 pb-4 border-b border-black/5">
              <div className="w-8 h-8 rounded-full bg-navy/10 flex items-center justify-center text-navy text-xs font-bold">
                {selected.sender_name?.charAt(0) || "A"}
              </div>
              <div>
                <p className="text-sm font-medium text-navy">{selected.sender_name}</p>
                <p className="text-xs text-gray">{formatDate(selected.created_at)}</p>
              </div>
            </div>
            <p className="text-sm text-navy/80 leading-relaxed whitespace-pre-wrap">{selected.body}</p>
          </div>
        </div>
      )}
    </div>
  );
}
