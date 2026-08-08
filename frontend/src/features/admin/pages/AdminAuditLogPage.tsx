import { useState, useEffect, useCallback } from "react";
import { Shield, UserX, Pencil, Trash2, Check, Coins, BookOpen, Building2 } from "lucide-react";
import { AdminTable, KPICard, StatusBadge } from "../components";
import { adminLogs } from "../../../api";
import { Button } from "@/components/ui";

interface AuditLog {
  id: number;
  admin_id: number;
  admin_email: string;
  action: string;
  target_type: string | null;
  target_id: number | null;
  details: string | null;
  ip_address: string | null;
  created_at: string;
}

const actionIcons: Record<string, React.ReactNode> = {
  "user.create": <Shield className="w-4 h-4" />,
  "user.update": <Pencil className="w-4 h-4" />,
  "user.delete": <UserX className="w-4 h-4" />,
  "user.role_change": <Shield className="w-4 h-4" />,
  "user.balance_adjust": <Coins className="w-4 h-4" />,
  "school.create": <Building2 className="w-4 h-4" />,
  "school.update": <Pencil className="w-4 h-4" />,
  "course.publish": <BookOpen className="w-4 h-4" />,
  "course.unpublish": <BookOpen className="w-4 h-4" />,
};

const actionColors: Record<string, string> = {
  "user.create": "bg-green-50 text-green-600",
  "user.update": "bg-blue-50 text-blue-600",
  "user.delete": "bg-red-50 text-red-500",
  "user.role_change": "bg-purple-50 text-purple-600",
  "user.balance_adjust": "bg-orange-50 text-orange-600",
  "school.create": "bg-green-50 text-green-600",
  "school.update": "bg-blue-50 text-blue-600",
  "course.publish": "bg-green-50 text-green-600",
  "course.unpublish": "bg-yellow-50 text-yellow-600",
  "registration.approve": "bg-green-50 text-green-600",
  "registration.reject": "bg-red-50 text-red-500",
};

export default function AdminAuditLogPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [actionFilter, setActionFilter] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [page, setPage] = useState(1);
  const perPage = 50;

  const fetchLogs = useCallback(async (isRefresh = false) => {
    isRefresh ? setRefreshing(true) : setLoading(true);
    try {
      const data = await adminLogs.list({ skip: (page - 1) * perPage, limit: perPage });
      setLogs((data as any).items || data);
      setTotal((data as any).total || 0);
    } catch (err) { console.error(err); }
    setLoading(false);
    setRefreshing(false);
  }, [page]);

  useEffect(() => { fetchLogs(); }, [fetchLogs]);

  const formatAction = (action: string) => action.replace(/\./g, " ").replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase());

  const columns = [
    { key: "action", header: "Action", render: (log: AuditLog) => (
      <div className="flex items-center gap-2">
        <span className={`w-8 h-8 rounded-lg flex items-center justify-center ${actionColors[log.action] || "bg-gray-50 text-gray-500"}`}>
          {actionIcons[log.action] || <Shield className="w-4 h-4" />}
        </span>
        <span className="text-sm font-medium text-navy">{formatAction(log.action)}</span>
      </div>
    )},
    { key: "admin_email", header: "Admin", render: (log: AuditLog) => (
      <div>
        <div className="font-medium text-navy text-sm">{log.admin_email}</div>
        {log.ip_address && <div className="text-xs text-gray">IP: {log.ip_address}</div>}
      </div>
    )},
    { key: "target", header: "Target", render: (log: AuditLog) => (
      <div>
        {log.target_type && <span className="px-2 py-0.5 text-xs bg-cream-m rounded text-navy">{log.target_type}</span>}
        {log.target_id && <span className="ml-1 text-xs text-gray">#{log.target_id}</span>}
      </div>
    )},
    { key: "details", header: "Details", render: (log: AuditLog) => (
      <span className="text-xs text-gray max-w-xs truncate block">{log.details || "—"}</span>
    )},
    { key: "created_at", header: "Timestamp", render: (log: AuditLog) => (
      <div className="text-xs text-gray whitespace-nowrap">
        <div>{new Date(log.created_at).toLocaleDateString("fr-TN")}</div>
        <div className="text-gray-l">{new Date(log.created_at).toLocaleTimeString("fr-TN", { hour: "2-digit", minute: "2-digit" })}</div>
      </div>
    )},
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-display font-light text-navy">Audit <span className="italic text-orange">Log</span></h1>
          <p className="text-gray text-sm mt-1">{total.toLocaleString("fr-TN")} actions recorded</p>
        </div>
        <Button variant="ghost" size="sm" onClick={() => fetchLogs(true)}>
          <Shield className={`w-5 h-5 text-gray ${refreshing ? "animate-spin" : ""}`} />
        </Button>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <KPICard label="Total Actions" value={total} icon={<Shield className="w-5 h-5" />} color="blue" loading={loading} />
        <KPICard label="Today" value={logs.filter(l => new Date(l.created_at).toDateString() === new Date().toDateString()).length || "—"} icon={<Shield className="w-5 h-5" />} color="orange" loading={loading} />
        <KPICard label="This Week" value={logs.filter(l => { const d = new Date(l.created_at); const now = new Date(); return now.getTime() - d.getTime() < 7 * 86400000; }).length || "—"} icon={<Shield className="w-5 h-5" />} color="purple" loading={loading} />
      </div>

      <div className="bg-white rounded-2xl p-4 shadow-sm border border-black/5 flex flex-wrap items-center gap-4">
        <select value={actionFilter} onChange={e => { setActionFilter(e.target.value); setPage(1); }}
          className="px-4 py-3 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none">
          <option value="">All Actions</option>
          <option value="user.create">User Created</option>
          <option value="user.update">User Updated</option>
          <option value="user.delete">User Deleted</option>
          <option value="user.role_change">Role Changed</option>
          <option value="user.balance_adjust">Balance Adjusted</option>
          <option value="school.create">School Created</option>
          <option value="course.publish">Course Published</option>
          <option value="registration.approve">Registration Approved</option>
          <option value="registration.reject">Registration Rejected</option>
        </select>
        <div className="flex items-center gap-2 text-sm text-gray">
          <span>From</span>
          <input type="date" value={dateFrom} onChange={e => { setDateFrom(e.target.value); setPage(1); }}
            className="px-3 py-3 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none" />
          <span>To</span>
          <input type="date" value={dateTo} onChange={e => { setDateTo(e.target.value); setPage(1); }}
            className="px-3 py-3 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none" />
        </div>
        {(actionFilter || dateFrom || dateTo) && (
          <Button variant="ghost" size="sm" onClick={() => { setActionFilter(""); setDateFrom(""); setDateTo(""); setPage(1); }}>
            Clear
          </Button>
        )}
      </div>

      <AdminTable columns={columns} data={logs} loading={loading} emptyMessage="No audit logs found" rowKey="id"
        pagination={{ page, per_page: perPage, total, onPageChange: setPage }} />
    </div>
  );
}