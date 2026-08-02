import { useState, useEffect, useRef } from "react";
import { parentAPI } from "../api";

interface Message {
  id: number;
  sender_id: number;
  sender_name: string;
  subject: string;
  body: string;
  created_at: string;
  is_read: boolean;
}

interface Props {
  token: string;
}

export default function ParentMessaging({ token }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [composing, setComposing] = useState(false);
  const [recipientType, setRecipientType] = useState<"teacher" | "admin">("teacher");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [sending, setSending] = useState(false);
  const [sendMsg, setSendMsg] = useState("");

  useEffect(() => {
    fetchMessages();
  }, [token]);

  const fetchMessages = async () => {
    setLoading(true);
    try {
      const data = await parentAPI.getMessages();
      setMessages(data.messages || []);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!subject.trim() || !body.trim()) return;
    setSending(true);
    setSendMsg("");
    try {
      await parentAPI.sendMessage({
        recipient_type: recipientType,
        subject: subject.trim(),
        body: body.trim(),
      });
      setSendMsg("Message envoye !");
      setSubject("");
      setBody("");
      setComposing(false);
      fetchMessages();
    } catch (e: any) {
      setSendMsg(e.message || "Erreur lors de l'envoi");
    } finally {
      setSending(false);
    }
  };

  const markRead = async (id: number) => {
    try {
      await parentAPI.markMessageRead(id);
      setMessages((prev) =>
        prev.map((m) => (m.id === id ? { ...m, is_read: true } : m))
      );
    } catch {}
  };

  if (loading) return <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange mx-auto" />;

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-black/5 p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-medium text-navy">Messagerie</h2>
        <button
          onClick={() => setComposing(!composing)}
          className="px-4 py-2 bg-orange text-white rounded-xl text-sm font-medium hover:bg-orange-l transition-colors"
        >
          {composing ? "Annuler" : "Nouveau message"}
        </button>
      </div>

      {error && <p className="text-red-500 text-sm mb-4">{error}</p>}

      {composing && (
        <form onSubmit={handleSend} className="mb-6 p-4 bg-cream-m rounded-xl space-y-3">
          <div className="flex gap-3">
            <label className="text-sm text-gray-600">Destinataire :</label>
            <select
              value={recipientType}
              onChange={(e) => setRecipientType(e.target.value as "teacher" | "admin")}
              className="px-3 py-1 border border-gray-200 rounded-lg text-sm focus:outline-none focus:border-orange"
            >
              <option value="teacher">Professeur</option>
              <option value="admin">Administration</option>
            </select>
          </div>
          <input
            type="text"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            placeholder="Sujet"
            className="w-full px-4 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:border-orange"
            required
          />
          <textarea
            value={body}
            onChange={(e) => setBody(e.target.value)}
            placeholder="Votre message..."
            rows={4}
            className="w-full px-4 py-2 border border-gray-200 rounded-xl text-sm resize-none focus:outline-none focus:border-orange"
            required
          />
          <button
            type="submit"
            disabled={sending || !subject.trim() || !body.trim()}
            className="px-6 py-2 bg-orange text-white rounded-xl text-sm font-medium hover:bg-orange-l transition-colors disabled:opacity-50"
          >
            {sending ? "Envoi..." : "Envoyer"}
          </button>
          {sendMsg && <p className="text-sm text-gray-600">{sendMsg}</p>}
        </form>
      )}

      {messages.length === 0 ? (
        <p className="text-gray-400 text-center py-8">Aucun message.</p>
      ) : (
        <div className="space-y-2">
          {messages.map((msg) => (
            <div
              key={msg.id}
              onClick={() => !msg.is_read && markRead(msg.id)}
              className={`p-4 rounded-xl border cursor-pointer transition-colors ${
                msg.is_read
                  ? "border-black/5 bg-white hover:bg-gray-50"
                  : "border-orange/20 bg-orange/5 hover:bg-orange/10"
              }`}
            >
              <div className="flex justify-between items-start">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    {!msg.is_read && <span className="w-2 h-2 rounded-full bg-orange shrink-0" />}
                    <span className="text-sm font-medium text-navy truncate">{msg.subject}</span>
                  </div>
                  <p className="text-sm text-gray-500 mt-1 line-clamp-2">{msg.body}</p>
                  <p className="text-xs text-gray-400 mt-1">
                    De: {msg.sender_name} — {new Date(msg.created_at).toLocaleDateString("fr-TN")}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
