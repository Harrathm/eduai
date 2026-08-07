import { useState, useEffect } from "react";
import { api, userApi } from "../../../api";
import { Button, Modal, EmptyState, PageSpinner } from "../../../components/ui";
import { 
  Send, 
  Inbox, 
  Users, 
  Search,
  X,
  Trash2,
  CheckCircle,
  AlertTriangle,
  User,
  Megaphone,
  Send as SendIcon,
  Reply,
  AlertOctagon,
  Loader2
} from "lucide-react";

interface Message {
  id: number;
  type: "broadcast" | "direct" | "observation";
  title: string;
  content: string;
  sender_id?: number;
  sender_name?: string;
  recipient_id?: number;
  recipient_name?: string;
  recipient_role?: string;
  created_at: string;
  is_read: boolean;
}

interface UserList {
  id: number;
  full_name: string;
  email: string;
  role: string;
}

export default function AdminInboxView() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [users, setUsers] = useState<UserList[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"inbox" | "sent" | "compose">("inbox");
  const [showComposeModal, setShowComposeModal] = useState(false);
  const [composeType, setComposeType] = useState<"broadcast" | "direct">("broadcast");
  const [selectedUser, setSelectedUser] = useState<UserList | null>(null);
  const [composeForm, setComposeForm] = useState({
    title: "",
    content: "",
    targetRole: "all",
  });
  const [sending, setSending] = useState(false);
  const [searchUser, setSearchUser] = useState("");
  const [sendResult, setSendResult] = useState<{success: boolean; message: string} | null>(null);

  useEffect(() => {
    fetchMessages();
    fetchUsers();
  }, []);

  const fetchMessages = async () => {
    setLoading(true);
    try {
      const data = await api.get<Message[] | { items: Message[] }>("/api/admin/messages");
      setMessages(Array.isArray(data) ? data : data.items || []);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const fetchUsers = async () => {
    try {
      const data = await userApi.list();
      setUsers(Array.isArray(data) ? data : data.items || []);
    } catch (err) {
      console.error(err);
    }
  };

  const sendMessage = async () => {
    if (!composeForm.title || !composeForm.content) return;
    setSending(true);
    setSendResult(null);
    try {
      const payload = {
        type: composeType,
        title: composeForm.title,
        content: composeForm.content,
        ...(composeType === "direct" && selectedUser ? { recipient_id: selectedUser.id } : {}),
        ...(composeType === "broadcast" && composeForm.targetRole !== "all" ? { recipient_role: composeForm.targetRole } : {}),
      };
      await api.post("/api/admin/messages", payload);
      setSendResult({ success: true, message: "Message envoyé avec succès!" });
      setTimeout(() => {
        setShowComposeModal(false);
        setComposeForm({ title: "", content: "", targetRole: "all" });
        setSelectedUser(null);
        setSendResult(null);
        fetchMessages();
      }, 1500);
    } catch (err) {
      setSendResult({ success: false, message: "Erreur de connexion" });
    }
    setSending(false);
  };

  const deleteMessage = async (messageId: number) => {
    if (!confirm("Supprimer ce message?")) return;
    try {
      await api.delete(`/api/admin/messages/${messageId}`);
      fetchMessages();
    } catch (err) {
      console.error(err);
    }
  };

  const filteredUsers = users.filter(u => 
    searchUser === "" ||
    u.full_name?.toLowerCase().includes(searchUser.toLowerCase()) ||
    u.email.toLowerCase().includes(searchUser.toLowerCase())
  );

  const stats = {
    total: messages.length,
    unread: messages.filter(m => !m.is_read).length,
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-3xl p-8 shadow-sm border border-black/5">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-[300] text-navy">
              Communication <span className="italic text-orange">Center</span>
            </h1>
            <p className="text-gray mt-2">Envoyez des messages et notifications</p>
          </div>
          <Button
            onClick={() => setShowComposeModal(true)}
            variant="primary"
            size="lg"
            className="flex items-center gap-2"
          >
            <SendIcon className="w-5 h-5" />
            Nouveau Message
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-gradient-to-br from-blue-50 to-cream rounded-2xl p-6">
          <div className="text-3xl font-[300] text-navy">{stats.total}</div>
          <div className="text-sm text-gray">Total Messages</div>
        </div>
        <div className="bg-gradient-to-br from-orange-50 to-cream rounded-2xl p-6">
          <div className="text-3xl font-[300] text-orange">{stats.unread}</div>
          <div className="text-sm text-gray">Non lus</div>
        </div>
        <div className="bg-gradient-to-br from-green-50 to-cream rounded-2xl p-6">
          <div className="text-3xl font-[300] text-green-700">
            {messages.filter(m => m.type === "broadcast").length}
          </div>
          <div className="text-sm text-gray">Broadcasts</div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-2xl shadow-sm border border-black/5 overflow-hidden">
        <div className="flex border-b">
          <Button
            onClick={() => setActiveTab("inbox")}
            variant="ghost"
            className={`flex-1 px-6 py-4 text-sm font-medium transition-colors rounded-none ${
              activeTab === "inbox" ? "text-orange border-b-2 border-orange" : "text-gray hover:text-navy"
            }`}
          >
            Inbox
          </Button>
          <Button
            onClick={() => setActiveTab("sent")}
            variant="ghost"
            className={`flex-1 px-6 py-4 text-sm font-medium transition-colors rounded-none ${
              activeTab === "sent" ? "text-orange border-b-2 border-orange" : "text-gray hover:text-navy"
            }`}
          >
            Envoyés
          </Button>
        </div>

        <div className="p-6">
          {loading ? (
            <PageSpinner />
          ) : messages.length === 0 ? (
            <EmptyState icon={Inbox} message="Aucun message" />
          ) : (
            <div className="space-y-4">
              {messages.map((msg) => (
                <div key={msg.id} className="p-4 rounded-xl border border-black/5">
                  <div className="flex justify-between items-start">
                    <div className="flex items-start gap-3">
                      <div className={`p-2 rounded-lg ${
                        msg.type === "observation" ? "bg-red-100" :
                        msg.type === "broadcast" ? "bg-purple-100" : "bg-blue-100"
                      }`}>
                        {msg.type === "observation" && <AlertOctagon className="w-4 h-4 text-red-600" />}
                        {msg.type === "broadcast" && <Megaphone className="w-4 h-4 text-purple-600" />}
                        {msg.type === "direct" && <User className="w-4 h-4 text-blue-600" />}
                      </div>
                      <div>
                        <h3 className="font-semibold text-navy">{msg.title}</h3>
                        <p className="text-sm text-gray">{msg.content}</p>
                        <div className="text-xs text-gray mt-2">
                          {msg.sender_name && <span>De: {msg.sender_name}</span>}
                          {msg.recipient_name && <span> • À: {msg.recipient_name}</span>}
                          {msg.recipient_role && <span> • Rôle: {msg.recipient_role}</span>}
                          <span className="ml-2">
                            {new Date(msg.created_at).toLocaleDateString("fr-FR")}
                          </span>
                        </div>
                      </div>
                    </div>
                    <Button
                      onClick={() => deleteMessage(msg.id)}
                      variant="danger"
                      size="sm"
                      className="p-2"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Compose Modal */}
      <Modal
        open={showComposeModal}
        onClose={() => setShowComposeModal(false)}
        title="Nouveau Message"
        maxWidth="max-w-2xl"
      >
        <div className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray mb-3">Type</label>
            <div className="grid grid-cols-2 gap-4">
              <Button
                onClick={() => setComposeType("broadcast")}
                variant="ghost"
                className={`p-4 rounded-xl text-center ${
                  composeType === "broadcast" ? "bg-purple-100 border-2 border-purple-500" : "bg-cream-m"
                }`}
              >
                <Megaphone className="w-6 h-6 mx-auto text-purple-600 mb-2" />
                <div className="text-sm font-medium">Broadcast</div>
              </Button>
              <Button
                onClick={() => setComposeType("direct")}
                variant="ghost"
                className={`p-4 rounded-xl text-center ${
                  composeType === "direct" ? "bg-blue-100 border-2 border-blue-500" : "bg-cream-m"
                }`}
              >
                <User className="w-6 h-6 mx-auto text-blue-600 mb-2" />
                <div className="text-sm font-medium">Direct</div>
              </Button>
            </div>
          </div>

          {composeType === "broadcast" && (
            <div>
              <label className="block text-sm font-medium text-gray mb-2">Destinataires</label>
              <select
                value={composeForm.targetRole}
                onChange={(e) => setComposeForm({ ...composeForm, targetRole: e.target.value })}
                className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5"
              >
                <option value="all">Tous les utilisateurs</option>
                <option value="teacher">Tous les teachers</option>
                <option value="student">Tous les students</option>
              </select>
            </div>
          )}

          {composeType === "direct" && (
            <div>
              <label className="block text-sm font-medium text-gray mb-2">Destinataire</label>
              <div className="relative">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray" />
                <input
                  type="text"
                  value={searchUser}
                  onChange={(e) => setSearchUser(e.target.value)}
                  className="w-full ps-12 pe-4 py-3 bg-cream-m rounded-xl border border-black/5"
                  placeholder="Rechercher..."
                />
              </div>
              {searchUser && (
                <div className="mt-2 max-h-40 overflow-y-auto bg-white border rounded-xl">
                  {filteredUsers.slice(0, 5).map((u) => (
                    <Button
                      key={u.id}
                      onClick={() => { setSelectedUser(u); setSearchUser(""); }}
                      variant="ghost"
                      className="w-full px-4 py-2 text-start rounded-none first:rounded-t-xl last:rounded-b-xl"
                    >
                      <div className="font-medium">{u.full_name}</div>
                      <div className="text-xs text-gray">{u.role}</div>
                    </Button>
                  ))}
                </div>
              )}
              {selectedUser && (
                <div className="mt-2 flex items-center gap-2 p-2 bg-green-50 rounded-xl">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  <span className="text-sm">{selectedUser.full_name}</span>
                  <Button onClick={() => setSelectedUser(null)} variant="ghost" size="sm" className="ml-auto p-1">
                    <X className="w-4 h-4" />
                  </Button>
                </div>
              )}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray mb-2">Sujet</label>
            <input
              type="text"
              value={composeForm.title}
              onChange={(e) => setComposeForm({ ...composeForm, title: e.target.value })}
              className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5"
              placeholder="Sujet..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray mb-2">Message</label>
            <textarea
              value={composeForm.content}
              onChange={(e) => setComposeForm({ ...composeForm, content: e.target.value })}
              className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 min-h-[150px]"
              placeholder="Message..."
            />
          </div>

          <Button
            onClick={sendMessage}
            disabled={sending || !composeForm.title || !composeForm.content || (composeType === "direct" && !selectedUser)}
            variant="primary"
            loading={sending}
            className="w-full py-4"
          >
            {sending ? "Envoi..." : "Envoyer"}
          </Button>
          {sendResult && (
            <div className={`p-4 rounded-xl text-center ${
              sendResult.success ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
            }`}>
              {sendResult.message}
            </div>
          )}
        </div>
      </Modal>
    </div>
  );
}
