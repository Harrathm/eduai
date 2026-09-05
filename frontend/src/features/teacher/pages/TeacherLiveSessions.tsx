import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import {
  Video,
  Plus,
  Clock,
  Users,
  Calendar,
  Play,
  Trash2,
  AlertCircle,
  Radio,
  CheckCircle2,
  XCircle,
} from "lucide-react";
import { Button, Modal, Input, PageSpinner, EmptyState } from "../../../components/ui";
import {
  teacherLiveSessionsApi,
  teacherClassesApi,
} from "../../../api";
import type { LiveSession, LiveSessionStatus } from "../../../api/liveSessionApi";

const statusConfig: Record<LiveSessionStatus, { color: string; bg: string; label: string; icon: typeof Play }> = {
  upcoming: { color: "text-blue-700", bg: "bg-blue-50", label: "upcoming", icon: Clock },
  live: { color: "text-red-700", bg: "bg-red-50", label: "live", icon: Radio },
  ended: { color: "text-gray-600", bg: "bg-gray-100", label: "ended", icon: CheckCircle2 },
  cancelled: { color: "text-red-500", bg: "bg-red-50", label: "cancelled", icon: XCircle },
};

function StatusBadge({ status }: { status: LiveSessionStatus }) {
  const cfg = statusConfig[status];
  const Icon = cfg.icon;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-full ${cfg.color} ${cfg.bg}`}>
      <Icon className="w-3.5 h-3.5" />
      {statusConfig[status].label}
    </span>
  );
}

interface ClassOption {
  id: number;
  name: string;
}

interface CreateModalProps {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

function CreateLiveSessionModal({ open, onClose, onCreated }: CreateModalProps) {
  const { t } = useTranslation();
  const [classes, setClasses] = useState<ClassOption[]>([]);
  const [classId, setClassId] = useState<number | "">("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [scheduledAt, setScheduledAt] = useState("");
  const [duration, setDuration] = useState(60);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!open) return;
    teacherClassesApi
      .list()
      .then((res) => {
        const list = Array.isArray(res) ? res : (res.items || res || []);
        setClasses(list.map((c: any) => ({ id: c.id, name: c.name })));
      })
      .catch((err) => {
        console.error(err);
      });
    setClassId("");
    setTitle("");
    setDescription("");
    setScheduledAt("");
    setDuration(60);
    setError("");
  }, [open]);

  const handleSubmit = async () => {
    if (!classId || !title.trim() || !scheduledAt) {
      setError(t("teacher.liveSessions.createModal.required"));
      return;
    }
    setLoading(true);
    setError("");
    try {
      await teacherLiveSessionsApi.create({
        class_id: Number(classId),
        title: title.trim(),
        description: description.trim() || undefined,
        scheduled_at: new Date(scheduledAt).toISOString(),
        duration_minutes: duration,
      });
      onCreated();
    } catch (err: any) {
      setError(err?.message || t("teacher.liveSessions.createModal.error"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal open={open} onClose={onClose} title={t("teacher.liveSessions.createModal.title")} maxWidth="max-w-lg">
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray mb-2">{t("teacher.liveSessions.createModal.class")} *</label>
          <select
            value={classId}
            onChange={(e) => setClassId(e.target.value ? Number(e.target.value) : "")}
            className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5"
          >
            <option value="">{t("teacher.liveSessions.createModal.selectClass")}</option>
            {classes.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </div>

        <Input
          label={t("teacher.liveSessions.createModal.titleField") + " *"}
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder={t("teacher.liveSessions.createModal.titlePlaceholder")}
        />

        <div>
          <label className="block text-sm font-medium text-gray mb-2">{t("teacher.liveSessions.createModal.description")}</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={2}
            className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 resize-none"
          />
        </div>

        <Input
          label={t("teacher.liveSessions.createModal.scheduledAt") + " *"}
          type="datetime-local"
          value={scheduledAt}
          onChange={(e) => setScheduledAt(e.target.value)}
        />

        <div>
          <label className="block text-sm font-medium text-gray mb-2">{t("teacher.liveSessions.createModal.duration")}</label>
          <select
            value={duration}
            onChange={(e) => setDuration(Number(e.target.value))}
            className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5"
          >
            <option value={30}>30 min</option>
            <option value={45}>45 min</option>
            <option value={60}>60 min</option>
            <option value={90}>90 min</option>
            <option value={120}>120 min</option>
          </select>
        </div>

        {error && (
          <div className="flex items-center gap-2 text-xs text-red-500 bg-red-50 rounded-xl px-3 py-2">
            <AlertCircle className="w-3.5 h-3.5 shrink-0" />
            {error}
          </div>
        )}

        <div className="flex gap-3 pt-2">
          <Button variant="ghost" className="flex-1" onClick={onClose}>
            {t("teacher.liveSessions.createModal.cancel")}
          </Button>
          <Button className="flex-1" onClick={handleSubmit} loading={loading}>
            {t("teacher.liveSessions.createModal.create")}
          </Button>
        </div>
      </div>
    </Modal>
  );
}

export default function TeacherLiveSessions() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<LiveSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadSessions = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await teacherLiveSessionsApi.list();
      setSessions(Array.isArray(res) ? res : (res.data || []));
    } catch {
      setError(t("teacher.liveSessions.loadError", "Erreur de chargement des séances"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSessions();
  }, []);

  const handleDelete = async (id: number) => {
    if (!window.confirm(t("teacher.liveSessions.confirmDelete"))) return;
    try {
      await teacherLiveSessionsApi.delete(id);
      setSessions((prev) => prev.filter((s) => s.id !== id));
    } catch {
      setError(t("teacher.liveSessions.deleteError", "Erreur lors de la suppression"));
    }
  };

  const handleJoin = (session: LiveSession) => {
    navigate(`/dashboard/live-sessions/${session.id}/join`);
  };

  const formatDate = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleDateString(undefined, {
      day: "numeric",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  if (loading) return <PageSpinner />;

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-orange/10 rounded-xl flex items-center justify-center">
            <Video className="w-5 h-5 text-orange" />
          </div>
          <div>
            <h1 className="text-2xl font-semibold text-navy">{t("teacher.liveSessions.title")}</h1>
            <p className="text-sm text-gray-400">{t("teacher.liveSessions.subtitle")}</p>
          </div>
        </div>
        <Button onClick={() => setShowCreate(true)}>
          <Plus className="w-4 h-4" />
          {t("teacher.liveSessions.newSession")}
        </Button>
      </div>

      {error && (
        <div className="flex items-center gap-2 px-4 py-3 text-sm text-red-600 bg-red-50 rounded-xl">
          <AlertCircle className="w-4 h-4 shrink-0" />
          {error}
        </div>
      )}

      {/* Sessions list */}
      {sessions.length === 0 ? (
        <EmptyState message={t("teacher.liveSessions.noSessions")} />
      ) : (
        <div className="grid gap-4">
          {sessions.map((session) => (
            <div
              key={session.id}
              className="flex items-center justify-between p-5 bg-white rounded-2xl border border-black/5 hover:shadow-sm transition-shadow"
            >
              <div className="flex items-center gap-4 min-w-0">
                <div className="w-11 h-11 bg-orange/10 rounded-xl flex items-center justify-center shrink-0">
                  <Video className="w-5 h-5 text-orange" />
                </div>
                <div className="min-w-0">
                  <h3 className="text-sm font-semibold text-navy truncate">{session.title}</h3>
                  <div className="flex items-center gap-3 mt-1 text-xs text-gray-400">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      {formatDate(session.scheduled_at)}
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {session.duration_minutes} min
                    </span>
                    {session.class_name && (
                      <span className="flex items-center gap-1">
                        <Users className="w-3 h-3" />
                        {session.class_name}
                      </span>
                    )}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3 shrink-0">
                <StatusBadge status={session.status} />
                {(session.status === "upcoming" || session.status === "live") && (
                  <Button size="sm" onClick={() => handleJoin(session)}>
                    <Play className="w-3.5 h-3.5" />
                    {t("teacher.liveSessions.join")}
                  </Button>
                )}
                {session.status === "upcoming" && (
                  <Button size="sm" variant="danger" onClick={() => handleDelete(session.id)}>
                    <Trash2 className="w-3.5 h-3.5" />
                  </Button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      <CreateLiveSessionModal
        open={showCreate}
        onClose={() => setShowCreate(false)}
        onCreated={() => {
          setShowCreate(false);
          loadSessions();
        }}
      />
    </div>
  );
}
