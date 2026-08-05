import { useState, useEffect, useCallback } from "react";
import { Send, Users, Megaphone, MessageSquare, History, Trash2, RefreshCw } from "lucide-react";
import { adminBroadcast } from "../../../api";
import type { BroadcastMessage } from "../../../api";

const TARGET_OPTIONS = [
  { value: "all", label: "All Users", icon: "🌍", desc: "Every active user on the platform" },
  { value: "teachers_only", label: "Teachers Only", icon: "👨‍🏫", desc: "All users with teacher role" },
  { value: "students_only", label: "Students Only", icon: "🎓", desc: "All users with student role" },
  { value: "admins_only", label: "Admins Only", icon: "⚙️", desc: "School admins and super admins" },
];

export default function BroadcastCenter() {
  const [target, setTarget] = useState("all");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [sending, setSending] = useState(false);
  const [history, setHistory] = useState<BroadcastMessage[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [result, setResult] = useState<{ ok: boolean; audience_count: number } | null>(null);
  const [toast, setToast] = useState<{ show: boolean; message: string; error?: boolean }>({ show: false, message: "" });

  const showToast = (message: string, error = false) => {
    setToast({ show: true, message, error });
    setTimeout(() => setToast({ show: false, message: "" }), 3000);
  };

  const fetchHistory = useCallback(async () => {
    setLoadingHistory(true);
    try {
      const res = await adminBroadcast.listMessages({ limit: 20 });
      setHistory(res.items);
    } catch (err) {
      console.error(err);
    }
    setLoadingHistory(false);
  }, []);

  useEffect(() => { fetchHistory(); }, [fetchHistory]);

  const handleSend = async () => {
    if (!subject.trim() || !body.trim()) {
      showToast("Subject and message body are required", true);
      return;
    }
    setSending(true);
    setResult(null);
    try {
      const res = await adminBroadcast.send({ target, subject, body });
      setResult(res);
      showToast(`Broadcast sent to ${res.audience_count} users`);
      setSubject("");
      setBody("");
      fetchHistory();
    } catch (err: any) {
      showToast(err.message || "Failed to send broadcast", true);
    }
    setSending(false);
  };

  const handleDelete = async (id: number) => {
    try {
      await adminBroadcast.deleteMessage(id);
      showToast("Message deleted");
      fetchHistory();
    } catch (err: any) {
      showToast(err.message || "Delete failed", true);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-display font-light text-navy">Broadcast <span className="italic text-orange">Center</span></h1>
          <p className="text-gray text-sm mt-1">Send messages to user segments</p>
        </div>
        <button onClick={fetchHistory} className="p-2.5 bg-white rounded-xl shadow-sm border border-black/5 hover:bg-cream">
          <RefreshCw className={`w-5 h-5 text-gray ${loadingHistory ? "animate-spin" : ""}`} />
        </button>
      </div>

      {/* Compose */}
      <div className="grid lg:grid-cols-5 gap-6">
        {/* Target Selection */}
        <div className="lg:col-span-2 space-y-3">
          <h3 className="text-sm font-semibold text-navy uppercase tracking-wider flex items-center gap-2">
            <Users className="w-4 h-4 text-orange" /> Target Audience
          </h3>
          {TARGET_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setTarget(opt.value)}
              className={`w-full text-start p-4 rounded-2xl border-2 transition-all ${
                target === opt.value
                  ? "border-orange bg-orange/5 shadow-sm"
                  : "border-transparent bg-white hover:border-black/10 shadow-sm"
              }`}
            >
              <div className="flex items-center gap-3">
                <span className="text-2xl">{opt.icon}</span>
                <div>
                  <div className="font-semibold text-navy text-sm">{opt.label}</div>
                  <div className="text-xs text-gray">{opt.desc}</div>
                </div>
              </div>
            </button>
          ))}
        </div>

        {/* Compose Form */}
        <div className="lg:col-span-3 bg-white rounded-2xl p-6 shadow-sm border border-black/5 space-y-5">
          <h3 className="text-sm font-semibold text-navy uppercase tracking-wider flex items-center gap-2">
            <MessageSquare className="w-4 h-4 text-orange" /> Compose Message
          </h3>

          <div>
            <label className="block text-xs font-medium text-gray mb-1.5">Subject</label>
            <input
              type="text"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              placeholder="e.g., Platform Maintenance Tomorrow"
              className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none focus:ring-2 focus:ring-orange/20"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray mb-1.5">Message Body</label>
            <textarea
              value={body}
              onChange={(e) => setBody(e.target.value)}
              placeholder="Write your broadcast message here..."
              rows={6}
              className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none focus:ring-2 focus:ring-orange/20 resize-none"
            />
          </div>

          {result && (
            <div className="bg-green-50 border border-green-200 rounded-xl px-4 py-3 text-sm text-green-700">
              ✅ Sent to <strong>{result.audience_count}</strong> users
            </div>
          )}

          <button
            onClick={handleSend}
            disabled={sending || !subject.trim() || !body.trim()}
            className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-orange to-orange-l text-white rounded-xl font-medium text-sm hover:opacity-90 disabled:opacity-50 shadow-sm"
          >
            {sending ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
            {sending ? "Sending..." : `Send to ${TARGET_OPTIONS.find((o) => o.value === target)?.label || "All"}`}
          </button>
        </div>
      </div>

      {/* History */}
      <div className="bg-white rounded-2xl shadow-sm border border-black/5 overflow-hidden">
        <div className="px-6 py-5 border-b border-black/5 flex items-center gap-2">
          <History className="w-5 h-5 text-orange" />
          <h3 className="font-semibold text-navy">Broadcast History</h3>
        </div>
        {loadingHistory ? (
          <div className="p-6 space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-16 bg-gray-100 rounded-xl animate-pulse" />
            ))}
          </div>
        ) : history.length === 0 ? (
          <div className="p-12 text-center text-gray text-sm">No broadcasts sent yet</div>
        ) : (
          <div className="divide-y divide-black/5">
            {history.map((msg) => (
              <div key={msg.id} className="px-6 py-4 flex items-start justify-between hover:bg-cream/30">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <Megaphone className="w-4 h-4 text-orange flex-shrink-0" />
                    <span className="font-medium text-navy text-sm truncate">{msg.subject}</span>
                    <span className="px-2 py-0.5 text-xs rounded-full bg-blue-50 text-blue-600 capitalize">
                      {msg.target_audience || "direct"}
                    </span>
                  </div>
                  <p className="text-xs text-gray truncate">{msg.body}</p>
                  <div className="flex items-center gap-3 mt-1.5 text-xs text-gray">
                    <span>by {msg.sender_name || "Admin"}</span>
                    <span>{new Date(msg.created_at).toLocaleString("fr-TN")}</span>
                  </div>
                </div>
                <button
                  onClick={() => handleDelete(msg.id)}
                  className="p-2 rounded-lg text-gray hover:bg-red-50 hover:text-red-500 transition-colors flex-shrink-0 ms-4"
                  title="Delete"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Toast */}
      {toast.show && (
        <div className={`fixed top-6 right-6 z-50 px-6 py-4 rounded-xl shadow-lg text-white ${toast.error ? "bg-red-500" : "bg-green-500"}`}>
          {toast.message}
        </div>
      )}
    </div>
  );
}
