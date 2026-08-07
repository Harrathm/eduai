import { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { Search, Building2, Plus, RefreshCw, Trash2, Pencil, Download, Globe, Users as UsersIcon, Calendar } from "lucide-react";
import { AdminTable, KPICard, StatusBadge, Modal, ConfirmModal } from "../components";
import { Button } from "../../../components/ui";
import { adminSchools } from "../../../api";
import type { AdminSchool, PaginatedResponse } from "../../../api";

const tierColors: Record<string, string> = {
  FREE: "bg-blue-50 text-blue-600",
  TEACHER_PRO: "bg-orange-50 text-orange-600",
  SCHOOL: "bg-purple-50 text-purple-600",
  INSTITUTION: "bg-green-50 text-green-600",
};

export default function AdminSchoolsPage() {
  const { t } = useTranslation();
  const [result, setResult] = useState<PaginatedResponse<AdminSchool> | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [tierFilter, setTierFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [page, setPage] = useState(1);
  const [refreshing, setRefreshing] = useState(false);
  const [editModal, setEditModal] = useState<AdminSchool | null>(null);
  const [createModal, setCreateModal] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<AdminSchool | null>(null);
  const [processing, setProcessing] = useState(false);
  const [toast, setToast] = useState({ show: false, message: "", type: "success" as "success" | "error" });

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(search), 400);
    return () => clearTimeout(timer);
  }, [search]);

  const showToast = (message: string, type: "success" | "error" = "success") => {
    setToast({ show: true, message, type });
    setTimeout(() => setToast({ show: false, message: "", type: "success" }), 3500);
  };

  const fetchSchools = useCallback(async (isRefresh = false) => {
    isRefresh ? setRefreshing(true) : setLoading(true);
    try {
      const data = await adminSchools.list({
        search: debouncedSearch || undefined,
        tier: tierFilter || undefined,
        is_active: statusFilter === "active" ? true : statusFilter === "inactive" ? false : undefined,
        page,
        per_page: 25,
      });
      setResult(data);
    } catch (err) {
      console.error(err);
      showToast(t("admin.schools.toast.loadFailed"), "error");
    }
    setLoading(false);
    setRefreshing(false);
  }, [debouncedSearch, tierFilter, statusFilter, page]);

  useEffect(() => { fetchSchools(); }, [fetchSchools]);

  const handleEdit = async (data: Partial<AdminSchool>) => {
    if (!editModal) return;
    setProcessing(true);
    try {
      await adminSchools.update(editModal.id, data);
      showToast(t("admin.schools.toast.updated"));
      setEditModal(null);
      fetchSchools();
    } catch (err: any) { showToast(err.message || "Failed", "error"); }
    setProcessing(false);
  };

  const handleCreate = async (data: Partial<AdminSchool>) => {
    setProcessing(true);
    try {
      await adminSchools.create(data);
      showToast(t("admin.schools.toast.created"));
      setCreateModal(false);
      fetchSchools();
    } catch (err: any) { showToast(err.message || "Failed", "error"); }
    setProcessing(false);
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setProcessing(true);
    try {
      await adminSchools.delete(deleteTarget.id);
      showToast(t("admin.schools.toast.deleted"));
      setDeleteTarget(null);
      fetchSchools();
    } catch (err: any) { showToast(err.message || "Failed", "error"); }
    setProcessing(false);
  };

  const exportCSV = () => {
    if (!result?.items.length) return;
    const headers = ["ID", "Name", "Domain", "Slug", "Tier", "Active", "Max Users", "Created"];
    const rows = result.items.map(s => [s.id, s.name, s.domain || "", s.slug, s.subscription_tier, s.is_active, s.max_users || "", s.created_at]);
    const csv = [headers, ...rows].map(r => r.map(c => `"${c}"`).join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url; a.download = `schools_${new Date().toISOString().slice(0,10)}.csv`; a.click();
    URL.revokeObjectURL(url);
  };

  const schools = result?.items || [];

  const columns = [
    { key: "name", header: t("admin.schools.table.colSchool"), render: (s: AdminSchool) => (
      <div>
        <div className="font-medium text-navy">{s.name}</div>
        <div className="flex items-center gap-1 text-xs text-gray">
          <Globe className="w-3 h-3" /> {s.domain || s.slug}
        </div>
      </div>
    )},
    { key: "tier", header: t("admin.schools.table.colPlan"), render: (s: AdminSchool) => (
      <span className={`px-2.5 py-1 text-xs rounded-full font-medium ${tierColors[s.subscription_tier] || "bg-gray-100 text-gray-600"}`}>
        {s.subscription_tier?.replace("_", " ")}
      </span>
    )},
    { key: "max_users", header: t("admin.schools.table.colMaxUsers"), render: (s: AdminSchool) => (
      <div className="flex items-center gap-1 text-sm">
        <UsersIcon className="w-3.5 h-3.5 text-gray" />
        {s.max_users || t("admin.schools.unlimited")}
      </div>
    )},
    { key: "is_active", header: t("admin.schools.table.colStatus"), render: (s: AdminSchool) => (
      <span className={`px-2.5 py-1 text-xs rounded-full font-medium ${s.is_active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-400"}`}>
        {s.is_active ? t("admin.schools.status.active") : t("admin.schools.status.inactive")}
      </span>
    )},
    { key: "created_at", header: t("admin.schools.table.colCreated"), render: (s: AdminSchool) => (
      <div className="flex items-center gap-1 text-xs text-gray">
        <Calendar className="w-3 h-3" />
        {new Date(s.created_at).toLocaleDateString("fr-TN")}
      </div>
    )},
    { key: "actions", header: t("admin.schools.table.colActions"), render: (s: AdminSchool) => (
      <div className="flex items-center gap-1">
        <Button variant="ghost" size="sm" onClick={() => setEditModal(s)} title={t("admin.schools.btn.edit")}>
          <Pencil className="w-4 h-4" />
        </Button>
        <Button variant="danger" size="sm" onClick={() => setDeleteTarget(s)} title={t("admin.schools.btn.delete")}>
          <Trash2 className="w-4 h-4" />
        </Button>
      </div>
    )},
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-display font-light text-navy">{t("admin.schools.title")} <span className="italic text-orange">& {t("admin.schools.titleSuffix")}</span></h1>
          <p className="text-gray text-sm mt-1">{result ? t("admin.schools.subtitle", { count: result.total }) : t("admin.schools.loading")}</p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="md" onClick={() => fetchSchools(true)}>
            <RefreshCw className={`w-5 h-5 text-gray ${refreshing ? "animate-spin" : ""}`} />
          </Button>
          <Button variant="secondary" size="md" onClick={exportCSV} disabled={!schools.length} className="flex items-center gap-2">
            <Download className="w-4 h-4" /> {t("admin.schools.btnExport")}
          </Button>
          <Button variant="primary" size="md" onClick={() => setCreateModal(true)} className="flex items-center gap-2">
            <Plus className="w-4 h-4" /> {t("admin.schools.btnNew")}
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard label={t("admin.schools.kpi.total")} value={result?.total || "—"} icon={<Building2 className="w-5 h-5" />} color="purple" loading={loading} />
        <KPICard label={t("admin.schools.kpi.active")} value={schools.filter(s => s.is_active).length} icon={<Building2 className="w-5 h-5" />} color="green" loading={loading} />
        <KPICard label={t("admin.schools.kpi.freeTier")} value={schools.filter(s => s.subscription_tier === "FREE").length} icon={<Building2 className="w-5 h-5" />} color="blue" loading={loading} />
        <KPICard label={t("admin.schools.kpi.institution")} value={schools.filter(s => s.subscription_tier === "INSTITUTION").length} icon={<Building2 className="w-5 h-5" />} color="orange" loading={loading} />
      </div>

      <div className="bg-white rounded-2xl p-4 shadow-sm border border-black/5 flex flex-wrap items-center gap-4">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray" />
          <input type="text" value={search} onChange={e => { setSearch(e.target.value); setPage(1); }}
            placeholder={t("admin.schools.filter.searchPlaceholder")} className="w-full ps-12 pe-4 py-3 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none focus:ring-2 focus:ring-orange/20" />
        </div>
        <select value={tierFilter} onChange={e => { setTierFilter(e.target.value); setPage(1); }}
          className="px-4 py-3 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none">
          <option value="">{t("admin.schools.filter.allPlans")}</option>
          <option value="FREE">FREE</option>
          <option value="TEACHER_PRO">TEACHER_PRO</option>
          <option value="SCHOOL">SCHOOL</option>
          <option value="INSTITUTION">INSTITUTION</option>
        </select>
        <select value={statusFilter} onChange={e => { setStatusFilter(e.target.value); setPage(1); }}
          className="px-4 py-3 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none">
          <option value="">{t("admin.schools.filter.allStatus")}</option>
          <option value="active">{t("admin.schools.status.active")}</option>
          <option value="inactive">{t("admin.schools.status.inactive")}</option>
        </select>
        {debouncedSearch && <span className="text-sm text-orange font-medium">{t("admin.schools.filter.resultsFor", { query: debouncedSearch })}</span>}
      </div>

      <AdminTable columns={columns} data={schools} loading={loading} emptyMessage={debouncedSearch ? t("admin.schools.empty.noMatch", { query: debouncedSearch }) : t("admin.schools.empty.noSchools")} rowKey="id"
        pagination={result ? { page, per_page: 25, total: result.total, onPageChange: setPage } : undefined} />

      {createModal && <SchoolFormModal open onClose={() => setCreateModal(false)} onSubmit={handleCreate} loading={processing} />}
      {editModal && <SchoolFormModal open school={editModal} onClose={() => setEditModal(null)} onSubmit={handleEdit} loading={processing} />}
      <ConfirmModal open={!!deleteTarget} onClose={() => setDeleteTarget(null)} onConfirm={handleDelete}
        title={t("admin.schools.deleteModal.title")} message={t("admin.schools.deleteModal.message", { name: deleteTarget?.name })} confirmLabel={t("admin.schools.deleteModal.confirm")} danger loading={processing} />

      {toast.show && (
        <div className={`fixed top-6 right-6 z-50 flex items-center gap-3 px-6 py-4 rounded-xl shadow-lg ${toast.type === "success" ? "bg-green-500" : "bg-red-500"} text-white`}>
          <span className="font-medium">{toast.message}</span>
        </div>
      )}
    </div>
  );
}

function SchoolFormModal({ open, school, onClose, onSubmit, loading }: {
  open: boolean; school?: AdminSchool; onClose: () => void; onSubmit: (d: Partial<AdminSchool>) => void; loading: boolean;
}) {
  const { t } = useTranslation();
  const [name, setName] = useState(school?.name || "");
  const [domain, setDomain] = useState(school?.domain || "");
  const [tier, setTier] = useState(school?.subscription_tier || "FREE");
  const [maxUsers, setMaxUsers] = useState(school?.max_users?.toString() || "");
  const [active, setActive] = useState(school?.is_active ?? true);

  if (!open) return null;

  const handleSubmit = () => onSubmit({ name, domain: domain || undefined, subscription_tier: tier, max_users: maxUsers ? Number(maxUsers) : undefined, is_active: active });

  return (
    <Modal open onClose={onClose} title={school ? t("admin.schools.modal.editTitle") : t("admin.schools.modal.createTitle")}
      footer={
        <>
          <Button variant="ghost" size="md" onClick={onClose} className="flex-1">{t("admin.schools.modal.btnCancel")}</Button>
          <Button variant="primary" size="md" onClick={handleSubmit} disabled={loading || !name} loading={loading} className="flex-1">
            {school ? t("admin.schools.modal.btnSave") : t("admin.schools.modal.btnCreate")}
          </Button>
        </>
      }>
      <div className="space-y-4">
        <div><label className="block text-sm font-medium text-gray mb-1.5">{t("admin.schools.modal.nameLabel")}</label>
          <input value={name} onChange={e => setName(e.target.value)} className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 focus:outline-none focus:ring-2 focus:ring-orange/20" /></div>
        <div><label className="block text-sm font-medium text-gray mb-1.5">{t("admin.schools.modal.domainLabel")}</label>
          <input value={domain} onChange={e => setDomain(e.target.value)} className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 focus:outline-none" /></div>
        <div><label className="block text-sm font-medium text-gray mb-1.5">{t("admin.schools.modal.planLabel")}</label>
          <select value={tier} onChange={e => setTier(e.target.value)} className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 focus:outline-none">
            <option value="FREE">FREE</option><option value="TEACHER_PRO">TEACHER_PRO</option>
            <option value="SCHOOL">SCHOOL</option><option value="INSTITUTION">INSTITUTION</option>
          </select></div>
        <div><label className="block text-sm font-medium text-gray mb-1.5">{t("admin.schools.modal.maxUsersLabel")}</label>
          <input type="number" value={maxUsers} onChange={e => setMaxUsers(e.target.value)} className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 focus:outline-none" /></div>
        {school && (
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" checked={active} onChange={e => setActive(e.target.checked)} className="w-4 h-4 rounded" />
            <span className="text-sm">{t("admin.schools.modal.activeLabel")}</span>
          </label>
        )}
      </div>
    </Modal>
  );
}
