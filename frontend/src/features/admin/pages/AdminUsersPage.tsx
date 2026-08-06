import { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { Search, Coins, Wallet, Ban, CheckCircle, Shield, ShieldCheck, GraduationCap, Users, RefreshCw, Trash2, Pencil, Download, ArrowUp, ArrowDown, Save, X, Plus, BookOpen, Loader2 } from "lucide-react";
import { AdminTable, KPICard, StatusBadge, ConfirmModal, Modal } from "../components";
import { adminUsers, adminSchools } from "../../../api";
import type { AdminUser, AdminSchool, PaginatedResponse } from "../../../api";

type RoleFilter = "all" | "student" | "teacher" | "admin_school" | "pedagogical_admin" | "pedagogical_lead" | "super_admin";
type StatusFilter = "all" | "active" | "inactive";
type SortField = "created_at" | "full_name" | "email" | "role";

const ROLE_ICONS: Record<string, React.ReactNode> = {
  super_admin: <ShieldCheck className="w-4 h-4 text-orange" />,
  admin: <Shield className="w-4 h-4 text-purple" />,
  admin_school: <Shield className="w-4 h-4 text-purple" />,
  admin_pedagogique: <BookOpen className="w-4 h-4 text-teal-500" />,
  teacher: <GraduationCap className="w-4 h-4 text-blue" />,
  student: <GraduationCap className="w-4 h-4 text-green" />,
  member: <Users className="w-4 h-4 text-gray" />,
};

const NIVEAUX = [
  "1ere annee", "2eme annee", "3eme annee", "4eme annee", "5eme annee", "6eme annee",
  "7eme de base", "8eme de base", "9eme de base",
  "1ere annee secondaire", "2eme annee secondaire", "3eme annee secondaire", "4eme annee secondaire",
  "1ere annee sciences", "2eme annee sciences", "3eme annee mathematiques", "4eme annee mathematiques",
];

export default function AdminUsersPage() {
  const { t } = useTranslation();
  const [result, setResult] = useState<PaginatedResponse<AdminUser> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState<RoleFilter>("all");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [page, setPage] = useState(1);
  const [sortBy, setSortBy] = useState<SortField>("created_at");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const perPage = 25;

  const [balanceModal, setBalanceModal] = useState<{ user: AdminUser | null; type: "tokens" | "dt"; mode: "add" | "deduct"; amount: number } | null>(null);
  const [roleModal, setRoleModal] = useState<AdminUser | null>(null);
  const [newRole, setNewRole] = useState("student");
  const [editModal, setEditModal] = useState<AdminUser | null>(null);
  const [editData, setEditData] = useState({ full_name: "", email: "", role: "", school_id: 0, is_active: true, is_approved: true, niveau_scolaire: "" });
  const [deleteTarget, setDeleteTarget] = useState<AdminUser | null>(null);
  const [processing, setProcessing] = useState(false);
  const [toast, setToast] = useState<{ show: boolean; message: string; type: "success" | "error" }>({ show: false, message: "", type: "success" });

  const [createModal, setCreateModal] = useState(false);
  const [schools, setSchools] = useState<AdminSchool[]>([]);
  const [newUserData, setNewUserData] = useState({ email: "", password: "", full_name: "", role: "student", school_id: 0 });
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(search), 400);
    return () => clearTimeout(timer);
  }, [search]);

  const showToast = (message: string, type: "success" | "error" = "success") => {
    setToast({ show: true, message, type });
    setTimeout(() => setToast({ show: false, message: "", type: "success" }), 3500);
  };

  const fetchUsers = useCallback(async (isRefresh = false) => {
    isRefresh ? setRefreshing(true) : setLoading(true);
    setError(null);
    try {
      const data = await adminUsers.list({
        role: roleFilter !== "all" ? roleFilter : undefined,
        is_active: statusFilter === "active" ? true : statusFilter === "inactive" ? false : undefined,
        search: debouncedSearch || undefined,
        page,
        per_page: perPage,
        sort_by: sortBy,
        sort_order: sortOrder,
      });
      setResult(data);
    } catch (err) {
      console.error(err);
      setError(t("admin.users.errors.loadFailed"));
    }
    setLoading(false);
    setRefreshing(false);
  }, [roleFilter, statusFilter, debouncedSearch, page, sortBy, sortOrder]);

  useEffect(() => { fetchUsers(); fetchSchools(); }, [fetchUsers]);

  const fetchSchools = async () => {
    try {
      const data = await adminSchools.list({ per_page: 100 });
      setSchools(data.items || []);
    } catch (err) {
      console.error("fetchSchools error:", err);
    }
  };

  const handleSort = (field: SortField) => {
    if (sortBy === field) setSortOrder(o => o === "asc" ? "desc" : "asc");
    else { setSortBy(field); setSortOrder("desc"); }
    setPage(1);
  };

  const SortIcon = ({ field }: { field: SortField }) => (
    sortBy === field
      ? sortOrder === "asc" ? <ArrowUp className="w-3 h-3 inline ms-1" /> : <ArrowDown className="w-3 h-3 inline ms-1" />
      : <span className="w-3 h-3 inline ms-1 opacity-30">↕</span>
  );

  const toggleActive = async (user: AdminUser) => {
    try {
      await adminUsers.toggleActive(user.id);
      showToast(t(`admin.users.toast.${user.is_active ? "deactivated" : "activated"}`, { name: user.full_name || user.email }));
      fetchUsers();
    } catch (err: any) { showToast(err.message || "Failed", "error"); }
  };

  const handleBalance = async () => {
    if (!balanceModal || !balanceModal.amount) return;
    setProcessing(true);
    try {
      const { user, type, mode, amount } = balanceModal;
      if (mode === "add") {
        await adminUsers.addWallet(user!.id, type === "tokens" ? amount : undefined, type === "dt" ? amount : undefined);
      } else {
        await adminUsers.deductWallet(user!.id, type === "tokens" ? amount : undefined, type === "dt" ? amount : undefined);
      }
      showToast(t(`admin.users.toast.${mode === "add" ? "added" : "deducted"}`, { amount, type }));
      setBalanceModal(null);
      fetchUsers();
    } catch (err: any) { showToast(err.message || "Failed", "error"); }
    setProcessing(false);
  };

  const handleRoleChange = async () => {
    if (!roleModal) return;
    setProcessing(true);
    try {
      await adminUsers.changeRole(roleModal.id, newRole);
      showToast(t("admin.users.toast.roleChanged", { role: t(`admin.users.roles.${newRole}`) }));
      setRoleModal(null);
      fetchUsers();
    } catch (err: any) { showToast(err.message || "Failed", "error"); }
    setProcessing(false);
  };

  const openEditModal = (user: AdminUser) => {
    setEditData({
      full_name: user.full_name || "",
      email: user.email,
      role: user.role,
      school_id: user.school_id,
      is_active: user.is_active,
      is_approved: user.is_approved ?? true,
      niveau_scolaire: (user as any).niveau_scolaire || "",
    });
    setEditModal(user);
  };

  const handleEditSave = async () => {
    if (!editModal) return;
    setProcessing(true);
    try {
      await adminUsers.update(editModal.id, editData);
      showToast(t("admin.users.toast.updated"));
      setEditModal(null);
      fetchUsers();
    } catch (err: any) { showToast(err.message || "Failed", "error"); }
    setProcessing(false);
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setProcessing(true);
    try {
      await adminUsers.delete(deleteTarget.id);
      showToast(t("admin.users.toast.deleted"));
      setDeleteTarget(null);
      fetchUsers();
    } catch (err: any) { showToast(err.message || "Failed", "error"); }
    setProcessing(false);
  };

  const handleCreateUser = async () => {
    if (!newUserData.email || !newUserData.password) return;
    setCreating(true);
    try {
      await adminUsers.create({
        email: newUserData.email,
        password: newUserData.password,
        full_name: newUserData.full_name || undefined,
        role: newUserData.role,
        school_id: newUserData.school_id || undefined,
      });
      showToast(t("admin.users.toast.created"));
      setCreateModal(false);
      setNewUserData({ email: "", password: "", full_name: "", role: "student", school_id: 0 });
      fetchUsers();
    } catch (err: any) { showToast(err.message || t("admin.users.errors.createFailed"), "error"); }
    setCreating(false);
  };

  const exportCSV = () => {
    if (!result?.items.length) return;
    const headers = ["ID", "Name", "Email", "Role", "School", "Active", "Tokens", "DT", "Created"];
    const rows = result.items.map(u => [
      u.id, u.full_name || "", u.email, u.role, u.school_name || "", u.is_active, u.token_balance, u.dt_balance, u.created_at
    ]);
    const csv = [headers, ...rows].map(r => r.map(c => `"${c}"`).join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url; a.download = `users_${new Date().toISOString().slice(0,10)}.csv`; a.click();
    URL.revokeObjectURL(url);
  };

  const users = result?.items || [];

  const columns = [
    { key: "full_name", header: <button onClick={() => handleSort("full_name")} className="flex items-center gap-1">{t("admin.users.table.colUser")} <SortIcon field="full_name" /></button>, render: (u: AdminUser) => (
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-full bg-gradient-to-r from-orange to-orange-l text-white flex items-center justify-center font-semibold text-xs">
          {u.full_name?.charAt(0) || u.email.charAt(0).toUpperCase()}
        </div>
        <div>
          <div className="font-medium text-navy">{u.full_name || "—"}</div>
          <div className="text-xs text-gray">{u.email}</div>
        </div>
      </div>
    )},
    { key: "role", header: <button onClick={() => handleSort("role")} className="flex items-center gap-1">{t("admin.users.table.colRole")} <SortIcon field="role" /></button>, render: (u: AdminUser) => (
      <div className="flex items-center gap-1.5 text-xs font-medium capitalize">
        {ROLE_ICONS[u.role] || ROLE_ICONS.member}
        <span className={u.role === "super_admin" ? "text-orange" : u.role === "pedagogical_admin" ? "text-blue" : u.role === "pedagogical_lead" ? "text-teal" : "text-navy"}>{t(`admin.users.roles.${u.role}`) || u.role}</span>
      </div>
    )},
    { key: "school", header: t("admin.users.table.colSchool"), render: (u: AdminUser) => <span className="text-sm text-gray">{u.school_name || "—"}</span> },
    { key: "is_active", header: t("admin.users.table.colStatus"), render: (u: AdminUser) => (
      <button onClick={() => toggleActive(u)} className={`px-2 py-1 text-xs rounded-full font-medium transition-all ${u.is_active ? "bg-green-100 text-green-700 hover:bg-green-200" : "bg-gray-100 text-gray-400 hover:bg-gray-200"}`}>
        {u.is_active ? t("admin.users.status.active") : t("admin.users.status.inactive")}
      </button>
    )},
    { key: "token_balance", header: t("admin.users.table.colTokens"), render: (u: AdminUser) => <span className="font-semibold text-blue-600">{u.token_balance?.toLocaleString("fr-TN")}</span> },
    { key: "dt_balance", header: t("admin.users.table.colBalance"), render: (u: AdminUser) => <span className="font-semibold text-green-600">{u.dt_balance?.toLocaleString("fr-TN")} DT</span> },
    { key: "created_at", header: <button onClick={() => handleSort("created_at")} className="flex items-center gap-1">{t("admin.users.table.colJoined")} <SortIcon field="created_at" /></button>, render: (u: AdminUser) => (
      <span className="text-xs text-gray">{new Date(u.created_at).toLocaleDateString("fr-TN")}</span>
    )},
    { key: "actions", header: t("admin.users.table.colActions"), render: (u: AdminUser) => (
      <div className="flex items-center gap-1">
        <button onClick={() => openEditModal(u)} className="p-1.5 bg-cream-m text-navy rounded-lg hover:bg-cream" title={t("admin.users.btn.edit")}>
          <Pencil className="w-4 h-4" />
        </button>
        <button onClick={() => setBalanceModal({ user: u, type: "tokens", mode: "add", amount: 0 })} className="p-1.5 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100" title={t("admin.users.btn.addTokens")}>
          <Coins className="w-4 h-4" />
        </button>
        <button onClick={() => setRoleModal(u)} className="p-1.5 bg-purple-50 text-purple-500 rounded-lg hover:bg-purple-100" title={t("admin.users.btn.changeRole")}>
          <Shield className="w-4 h-4" />
        </button>
        <button onClick={() => setDeleteTarget(u)} className="p-1.5 bg-red-50 text-red-400 rounded-lg hover:bg-red-100" title={t("admin.users.btn.delete")}>
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    )},
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-display font-light text-navy">{t("admin.users.title")} <span className="italic text-orange">& {t("admin.users.titleSuffix")}</span></h1>
          <p className="text-gray text-sm mt-1">{result ? t("admin.users.subtitle", { count: result.total }) : t("admin.users.loading")}</p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={() => setCreateModal(true)} className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-orange to-orange-l text-white rounded-xl font-medium text-sm hover:shadow-lg transition-shadow">
            <Plus className="w-4 h-4" /> {t("admin.users.btnNew")}
          </button>
          <button onClick={() => fetchUsers(true)} className="p-2.5 bg-white rounded-xl shadow-sm border border-black/5 hover:bg-cream">
            <RefreshCw className={`w-5 h-5 text-gray ${refreshing ? "animate-spin" : ""}`} />
          </button>
          <button onClick={exportCSV} disabled={!users.length} className="flex items-center gap-2 px-4 py-2.5 bg-navy text-white rounded-xl font-medium text-sm hover:bg-navy-m disabled:opacity-50 shadow-sm">
            <Download className="w-4 h-4" /> {t("admin.users.btnExport")}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard label={t("admin.users.kpi.total")} value={result?.total || "—"} icon={<Users className="w-5 h-5" />} color="blue" loading={loading} />
        <KPICard label={t("admin.users.kpi.active")} value={users.filter(u => u.is_active).length || "—"} subValue={t("admin.users.kpi.ofTotal", { total: result?.total || 0 })} icon={<CheckCircle className="w-5 h-5" />} color="green" loading={loading} />
        <KPICard label={t("admin.users.kpi.tokens")} value={users.reduce((s, u) => s + (u.token_balance || 0), 0).toLocaleString("fr-TN")} icon={<Coins className="w-5 h-5" />} color="orange" loading={loading} />
        <KPICard label={t("admin.users.kpi.dt")} value={`${users.reduce((s, u) => s + (u.dt_balance || 0), 0).toLocaleString("fr-TN")} DT`} icon={<Wallet className="w-5 h-5" />} color="purple" loading={loading} />
      </div>

      <div className="bg-white rounded-2xl p-4 shadow-sm border border-black/5 flex flex-wrap items-center gap-4">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray" />
          <input type="text" value={search} onChange={e => { setSearch(e.target.value); setPage(1); }}
            placeholder={t("admin.users.filter.searchPlaceholder")} className="w-full ps-12 pe-4 py-3 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none focus:ring-2 focus:ring-orange/20" />
        </div>
        <select value={roleFilter} onChange={e => { setRoleFilter(e.target.value as RoleFilter); setPage(1); }}
          className="px-4 py-3 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none">
          <option value="all">{t("admin.users.filter.allRoles")}</option>
          <option value="student">{t("admin.users.filter.students")}</option>
          <option value="teacher">{t("admin.users.filter.teachers")}</option>
          <option value="admin_school">{t("admin.users.roles.admin_school")}</option>
          <option value="pedagogical_admin">{t("admin.users.roles.pedagogical_admin")}</option>
          <option value="pedagogical_lead">{t("admin.users.roles.pedagogical_lead")}</option>
          <option value="super_admin">{t("admin.users.roles.super_admin")}</option>
        </select>
        <select value={statusFilter} onChange={e => { setStatusFilter(e.target.value as StatusFilter); setPage(1); }}
          className="px-4 py-3 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none">
          <option value="all">{t("admin.users.filter.allStatus")}</option>
          <option value="active">{t("admin.users.status.active")}</option>
          <option value="inactive">{t("admin.users.status.inactive")}</option>
        </select>
        {debouncedSearch && (
          <span className="text-sm text-orange font-medium">
            {t("admin.users.filter.resultsFor", { query: debouncedSearch })}
          </span>
        )}
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-2xl p-6 flex flex-col items-center justify-center text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <button onClick={() => fetchUsers()} className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium">
            {t("admin.users.btn.retry")}
          </button>
        </div>
      )}

      <AdminTable
        columns={columns}
        data={users}
        loading={loading}
        emptyMessage={debouncedSearch ? t("admin.users.empty.noMatch", { query: debouncedSearch }) : t("admin.users.empty.noUsers")}
        rowKey="id"
        pagination={result ? { page, per_page: perPage, total: result.total, onPageChange: setPage } : undefined}
      />

      {balanceModal && (
        <Modal open onClose={() => setBalanceModal(null)}
          title={t(`admin.users.balanceModal.${balanceModal.mode === "add" ? "addTitle" : "deductTitle"}.${balanceModal.type}`)}
          footer={
            <>
              <button onClick={() => setBalanceModal(null)} className="flex-1 py-3 bg-cream-m rounded-xl font-medium">{t("admin.users.balanceModal.btnCancel")}</button>
              <button onClick={handleBalance} disabled={processing || !balanceModal.amount} className="flex-1 py-3 bg-orange text-white rounded-xl font-medium disabled:opacity-50">
                {processing ? "..." : t("admin.users.balanceModal.btnConfirm")}
              </button>
            </>
          }>
          <div className="space-y-4">
            <div className="bg-cream-m rounded-xl p-4">
              <p className="text-sm text-gray">{t("admin.users.balanceModal.user")}</p>
              <p className="font-medium">{balanceModal.user?.full_name}</p>
              <p className="text-xs text-gray">{balanceModal.user?.email}</p>
              <p className="text-xs text-gray mt-1">{t("admin.users.balanceModal.current", { balance: balanceModal.type === "tokens" ? `${balanceModal.user?.token_balance} tokens` : `${balanceModal.user?.dt_balance} DT` })}</p>
            </div>
            <div className="flex gap-2 mb-2">
              {(["tokens", "dt"] as const).map(tp => (
                <button key={tp} onClick={() => setBalanceModal({ ...balanceModal, type: tp })}
                  className={`flex-1 py-2.5 rounded-xl text-sm font-medium transition-all ${balanceModal.type === tp ? "bg-orange text-white" : "bg-cream-m text-navy"}`}>
                  {tp === "tokens" ? t("admin.users.balanceModal.tokens") : "DT"}
                </button>
              ))}
            </div>
            <div className="flex gap-2 mb-2">
              {(["add", "deduct"] as const).map(m => (
                <button key={m} onClick={() => setBalanceModal({ ...balanceModal, mode: m })}
                  className={`flex-1 py-2.5 rounded-xl text-sm font-medium transition-all ${balanceModal.mode === m ? "bg-navy text-white" : "bg-cream-m text-navy"}`}>
                  {t(`admin.users.balanceModal.mode.${m}`)}
                </button>
              ))}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray mb-2">{t("admin.users.balanceModal.amount")}</label>
              <input type="number" value={balanceModal.amount} onChange={e => setBalanceModal({ ...balanceModal, amount: Number(e.target.value) })}
                className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 focus:outline-none focus:ring-2 focus:ring-orange/20" min={1} />
            </div>
          </div>
        </Modal>
      )}

      {roleModal && (
        <Modal open onClose={() => setRoleModal(null)} title={t("admin.users.roleModal.title")}
          footer={
            <>
              <button onClick={() => setRoleModal(null)} className="flex-1 py-3 bg-cream-m rounded-xl font-medium">{t("admin.users.roleModal.btnCancel")}</button>
              <button onClick={handleRoleChange} disabled={processing || newRole === roleModal.role} className="flex-1 py-3 bg-orange text-white rounded-xl font-medium disabled:opacity-50">
                {processing ? "..." : t("admin.users.roleModal.btnSave")}
              </button>
            </>
          }>
          <div className="space-y-2">
            {(["student", "teacher", "admin_school", "pedagogical_admin", "pedagogical_lead"] as const).map(r => (
              <button key={r} onClick={() => setNewRole(r)}
                className={`w-full p-4 rounded-xl text-start font-medium capitalize transition-all ${newRole === r ? "bg-orange text-white" : "bg-cream-m hover:bg-cream text-navy"}`}>
                {t(`admin.users.roles.${r}`)}
              </button>
            ))}
          </div>
        </Modal>
      )}

      {editModal && (
        <Modal open onClose={() => setEditModal(null)} title={t("admin.users.editModal.title")} size="lg"
          footer={
            <>
              <button onClick={() => setEditModal(null)} className="flex-1 py-3 bg-cream-m rounded-xl font-medium">{t("admin.users.editModal.btnCancel")}</button>
              <button onClick={handleEditSave} disabled={processing} className="flex-1 py-3 bg-orange text-white rounded-xl font-medium disabled:opacity-50">
                {processing ? t("admin.users.editModal.saving") : t("admin.users.editModal.btnSave")}
              </button>
            </>
          }>
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-gray mb-1.5">{t("admin.users.editModal.fullName")}</label>
              <input type="text" value={editData.full_name} onChange={e => setEditData({ ...editData, full_name: e.target.value })}
                className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none focus:ring-2 focus:ring-orange/20" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray mb-1.5">{t("admin.users.editModal.email")}</label>
              <input type="email" value={editData.email} onChange={e => setEditData({ ...editData, email: e.target.value })}
                className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none focus:ring-2 focus:ring-orange/20" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray mb-1.5">{t("admin.users.editModal.role")}</label>
              <select value={editData.role} onChange={e => setEditData({ ...editData, role: e.target.value })}
                className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none">
                <option value="student">{t("admin.users.roles.student")}</option>
                <option value="teacher">{t("admin.users.roles.teacher")}</option>
                <option value="admin_school">{t("admin.users.roles.admin_school")}</option>
                <option value="pedagogical_admin">{t("admin.users.roles.pedagogical_admin")}</option>
                <option value="pedagogical_lead">{t("admin.users.roles.pedagogical_lead")}</option>
                <option value="super_admin">{t("admin.users.roles.super_admin")}</option>
              </select>
            </div>
            {editData.role === "student" && (
              <div>
                <label className="block text-xs font-medium text-gray mb-1.5">Niveau scolaire</label>
                <select value={editData.niveau_scolaire} onChange={e => setEditData({ ...editData, niveau_scolaire: e.target.value })}
                  className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none">
                  <option value="">— Non défini —</option>
                  {NIVEAUX.map(n => <option key={n} value={n}>{n}</option>)}
                </select>
              </div>
            )}
            <div className="flex items-center gap-6">
              <label className="flex items-center gap-2 text-sm text-navy">
                <input type="checkbox" checked={editData.is_active} onChange={e => setEditData({ ...editData, is_active: e.target.checked })}
                  className="rounded border-gray-300 text-orange focus:ring-orange" />
                {t("admin.users.editModal.active")}
              </label>
              <label className="flex items-center gap-2 text-sm text-navy">
                <input type="checkbox" checked={editData.is_approved} onChange={e => setEditData({ ...editData, is_approved: e.target.checked })}
                  className="rounded border-gray-300 text-orange focus:ring-orange" />
                {t("admin.users.editModal.approved")}
              </label>
            </div>
          </div>
        </Modal>
      )}

      <ConfirmModal open={!!deleteTarget} onClose={() => setDeleteTarget(null)} onConfirm={handleDelete}
        title={t("admin.users.deleteModal.title")} message={t("admin.users.deleteModal.message", { name: deleteTarget?.full_name })}
        confirmLabel={t("admin.users.deleteModal.confirm")} danger loading={processing} />

      {createModal && (
        <Modal open onClose={() => setCreateModal(false)} title={t("admin.users.createModal.title")} size="lg"
          footer={
            <>
              <button onClick={() => setCreateModal(false)} className="flex-1 py-3 bg-cream-m rounded-xl font-medium">{t("admin.users.createModal.btnCancel")}</button>
              <button onClick={handleCreateUser} disabled={creating || !newUserData.email || !newUserData.password}
                className="flex-1 py-3 bg-orange text-white rounded-xl font-medium disabled:opacity-50">
                {creating ? t("admin.users.createModal.creating") : t("admin.users.createModal.btnCreate")}
              </button>
            </>
          }>
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-gray mb-1.5">{t("admin.users.createModal.emailLabel")}</label>
              <input type="email" value={newUserData.email} onChange={e => setNewUserData({ ...newUserData, email: e.target.value })}
                className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none focus:ring-2 focus:ring-orange/20"
                placeholder={t("admin.users.createModal.emailPlaceholder")} />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray mb-1.5">{t("admin.users.createModal.passwordLabel")}</label>
              <input type="password" value={newUserData.password} onChange={e => setNewUserData({ ...newUserData, password: e.target.value })}
                className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none focus:ring-2 focus:ring-orange/20"
                placeholder={t("admin.users.createModal.passwordPlaceholder")} />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray mb-1.5">{t("admin.users.createModal.fullNameLabel")}</label>
              <input type="text" value={newUserData.full_name} onChange={e => setNewUserData({ ...newUserData, full_name: e.target.value })}
                className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none focus:ring-2 focus:ring-orange/20"
                placeholder={t("admin.users.createModal.fullNamePlaceholder")} />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-gray mb-1.5">{t("admin.users.createModal.roleLabel")}</label>
                <select value={newUserData.role} onChange={e => setNewUserData({ ...newUserData, role: e.target.value })}
                  className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 text-sm">
                  <option value="student">{t("admin.users.roles.student")}</option>
                  <option value="teacher">{t("admin.users.roles.teacher")}</option>
                  <option value="admin_school">{t("admin.users.roles.admin_school")}</option>
                  <option value="pedagogical_admin">{t("admin.users.roles.pedagogical_admin")}</option>
                  <option value="pedagogical_lead">{t("admin.users.roles.pedagogical_lead")}</option>
                  <option value="super_admin">{t("admin.users.roles.super_admin")}</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray mb-1.5">{t("admin.users.createModal.schoolLabel")}</label>
                <select value={newUserData.school_id} onChange={e => setNewUserData({ ...newUserData, school_id: Number(e.target.value) })}
                  className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 text-sm">
                  <option value={0}>{t("admin.users.createModal.noSchool")}</option>
                  {schools.map(s => (
                    <option key={s.id} value={s.id}>{s.name} ({s.subscription_tier})</option>
                  ))}
                </select>
              </div>
            </div>
            {newUserData.school_id > 0 && (
              <div className="bg-blue-50 rounded-xl p-3 text-sm text-blue-700">
                {t("admin.users.createModal.schoolInfo")}
              </div>
            )}
          </div>
        </Modal>
      )}

      {toast.show && (
        <div className={`fixed top-6 right-6 z-50 flex items-center gap-3 px-6 py-4 rounded-xl shadow-lg ${toast.type === "success" ? "bg-green-500" : "bg-red-500"} text-white`}>
          <span className="font-medium">{toast.message}</span>
        </div>
      )}
    </div>
  );
}
