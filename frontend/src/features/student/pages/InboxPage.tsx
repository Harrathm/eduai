import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { inboxApi } from "../../../api";
import { Button, Modal, EmptyState, PageWrapper } from "../../../components/ui";
import { Inbox } from "lucide-react";

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
  const { t } = useTranslation();
  const [messages, setMessages] = useState<InboxMessage[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<InboxMessage | null>(null);
  const [filter, setFilter] = useState<"all" | "unread">("all");

  const fetchMessages = async () => {
    setLoading(true);
    try {
      const data = await inboxApi.list({ unread_only: filter === "unread" });
      setMessages((data as any).items || data || []);
      setTotal((data as any).total || 0);
      setUnreadCount((data as any).unread || 0);
    } catch (err) {
      console.error("Failed to load inbox", err);
    }
    setLoading(false);
  };

  useEffect(() => { fetchMessages(); }, [filter]);

  const markRead = async (id: number) => {
    try {
      await inboxApi.markRead(id);
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
    <PageWrapper
      title={t('inbox.title')}
      subtitle={t('inbox.messageCount', { total, unread: unreadCount })}
      icon={<Inbox className="w-8 h-8" />}
      actions={
        <div className="flex gap-2">
          <Button
            variant={filter === "all" ? "ghost" : "secondary"}
            size="sm"
            onClick={() => setFilter("all")}
          >
            {t('inbox.all')}
          </Button>
          <Button
            variant={filter === "unread" ? "ghost" : "secondary"}
            size="sm"
            onClick={() => setFilter("unread")}
          >
            {t('inbox.unread')} {unreadCount > 0 && `(${unreadCount})`}
          </Button>
        </div>
      }
    >

      <div className="bg-white rounded-2xl border border-black/5 overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-gray">{t('inbox.loading')}</div>
        ) : messages.length === 0 ? (
          <EmptyState
            icon={<Inbox className="w-12 h-12" />}
            title={t('inbox.noMessages')}
          />
        ) : (
          <div className="divide-y divide-black/5">
            {messages.map((msg) => (
              <Button
                key={msg.id}
                onClick={() => openMessage(msg)}
                variant="ghost"
                className={`w-full text-start px-6 py-4 hover:bg-cream-m/50 transition-colors ${
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
                      {t('inbox.from')} {msg.sender_name}
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
              </Button>
            ))}
          </div>
        )}
      </div>

      {/* Message detail modal */}
      <Modal
        open={!!selected}
        onClose={() => setSelected(null)}
        title={selected?.subject}
        maxWidth="max-w-lg"
      >
        <div className="flex items-center gap-3 mb-4 pb-4 border-b border-black/5">
          <div className="w-8 h-8 rounded-full bg-navy/10 flex items-center justify-center text-navy text-xs font-bold">
            {selected?.sender_name?.charAt(0) || "A"}
          </div>
          <div>
            <p className="text-sm font-medium text-navy">{selected?.sender_name}</p>
            <p className="text-xs text-gray">{selected && formatDate(selected.created_at)}</p>
          </div>
        </div>
        <p className="text-sm text-navy/80 leading-relaxed whitespace-pre-wrap">{selected?.body}</p>
      </Modal>
    </PageWrapper>
  );
}
