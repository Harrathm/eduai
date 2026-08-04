import { useState, useEffect } from "react";
import { Coins, Plus, RefreshCw, Pencil, Trash2, Save } from "lucide-react";
import { KPICard, AdminTable, Modal, ConfirmModal } from "../components";
import { tokenStorage } from "../../../utils/tokenStorage";

const API_URL = "";

interface TokenPackage {
  id: number;
  name: string;
  tokens: number;
  price_dt: number;
  bonus_tokens: number;
  is_active: boolean;
}

export default function AdminTokenPackagesPage() {
  const [packages, setPackages] = useState<TokenPackage[]>([]);
  const [loading, setLoading] = useState(true);
  const [editModal, setEditModal] = useState<TokenPackage | null>(null);
  const [createModal, setCreateModal] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<TokenPackage | null>(null);
  const [processing, setProcessing] = useState(false);
  const [toast, setToast] = useState({ show: false, message: "", type: "success" as "success" | "error" });

  const showToast = (message: string, type: "success" | "error" = "success") => {
    setToast({ show: true, message, type });
    setTimeout(() => setToast({ show: false, message: "", type: "success" }), 3000);
  };

  const token = tokenStorage.getToken();

  const fetchPackages = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/admin/token-packages`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setPackages(Array.isArray(data) ? data : data.items || []);
      }
    } catch (err) { console.error(err); showToast("Failed to load packages", "error"); }
    setLoading(false);
  };

  useEffect(() => { fetchPackages(); }, []);

  const handleCreate = async (data: Partial<TokenPackage>) => {
    setProcessing(true);
    try {
      const res = await fetch(`${API_URL}/api/admin/token-packages`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (!res.ok) throw new Error(await res.text());
      showToast("Package created");
      setCreateModal(false);
      fetchPackages();
    } catch (err: any) { showToast(err.message || "Failed", "error"); }
    setProcessing(false);
  };

  const handleUpdate = async (data: Partial<TokenPackage>) => {
    if (!editModal) return;
    setProcessing(true);
    try {
      const res = await fetch(`${API_URL}/api/admin/token-packages/${editModal.id}`, {
        method: "PUT",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (!res.ok) throw new Error(await res.text());
      showToast("Package updated");
      setEditModal(null);
      fetchPackages();
    } catch (err: any) { showToast(err.message || "Failed", "error"); }
    setProcessing(false);
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setProcessing(true);
    try {
      const res = await fetch(`${API_URL}/api/admin/token-packages/${deleteTarget.id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error(await res.text());
      showToast("Package deleted");
      setDeleteTarget(null);
      fetchPackages();
    } catch (err: any) { showToast(err.message || "Failed", "error"); }
    setProcessing(false);
  };

  const activePackages = packages.filter(p => p.is_active);

  const columns = [
    { key: "name", header: "Package Name", render: (p: TokenPackage) => (
      <div className="flex items-center gap-2">
        <div className="w-8 h-8 rounded-lg bg-orange-100 flex items-center justify-center">
          <Coins className="w-4 h-4 text-orange-500" />
        </div>
        <span className="font-medium text-navy">{p.name}</span>
      </div>
    )},
    { key: "tokens", header: "Tokens", render: (p: TokenPackage) => (
      <span className="font-semibold text-navy">{p.tokens.toLocaleString("fr-TN")}</span>
    )},
    { key: "bonus", header: "Bonus", render: (p: TokenPackage) => (
      <span className="text-green-600 text-sm">{p.bonus_tokens > 0 ? `+${p.bonus_tokens}` : "—"}</span>
    )},
    { key: "price", header: "Price (DT)", render: (p: TokenPackage) => (
      <span className="font-bold text-green-600">{p.price_dt.toLocaleString("fr-TN")} DT</span>
    )},
    { key: "status", header: "Status", render: (p: TokenPackage) => (
      <span className={`px-2 py-1 text-xs rounded-full ${p.is_active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"}`}>
        {p.is_active ? "Active" : "Inactive"}
      </span>
    )},
    { key: "actions", header: "Actions", render: (p: TokenPackage) => (
      <div className="flex items-center gap-1">
        <button onClick={() => setEditModal(p)} className="p-1.5 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100">
          <Pencil className="w-4 h-4" />
        </button>
        <button onClick={() => setDeleteTarget(p)} className="p-1.5 bg-red-50 text-red-400 rounded-lg hover:bg-red-100">
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    )},
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-display font-light text-navy">Token <span className="italic text-orange">Packages</span></h1>
          <p className="text-gray text-sm mt-1">Configure token pricing and bundles</p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={fetchPackages} className="p-2 hover:bg-white rounded-xl shadow-sm border border-black/5">
            <RefreshCw className={`w-5 h-5 text-gray ${loading ? "animate-spin" : ""}`} />
          </button>
          <button onClick={() => setCreateModal(true)} className="flex items-center gap-2 px-4 py-2 bg-orange text-white rounded-xl font-medium text-sm hover:bg-orange-w">
            <Plus className="w-4 h-4" /> New Package
          </button>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <KPICard label="Total Packages" value={packages.length} icon={<Coins className="w-5 h-5" />} color="blue" loading={loading} />
        <KPICard label="Active" value={activePackages.length} icon={<Coins className="w-5 h-5" />} color="green" loading={loading} />
        <KPICard label="Avg Price" value={activePackages.length > 0 ? `${Math.round(activePackages.reduce((s, p) => s + p.price_dt, 0) / activePackages.length)} DT` : "—"} icon={<Coins className="w-5 h-5" />} color="orange" loading={loading} />
      </div>

      <AdminTable columns={columns} data={packages} loading={loading} emptyMessage="No packages configured" rowKey="id" />

      {createModal && <PackageFormModal open onClose={() => setCreateModal(false)} onSubmit={handleCreate} loading={processing} />}
      {editModal && <PackageFormModal open package={editModal} onClose={() => setEditModal(null)} onSubmit={handleUpdate} loading={processing} />}

      <ConfirmModal open={!!deleteTarget} onClose={() => setDeleteTarget(null)} onConfirm={handleDelete}
        title="Delete Package" message={`Delete "${deleteTarget?.name}"?`} confirmLabel="Delete" danger loading={processing} />

      {toast.show && (
        <div className={`fixed top-6 right-6 z-50 px-6 py-4 rounded-xl shadow-lg text-white ${toast.type === "success" ? "bg-green-500" : "bg-red-500"}`}>
          {toast.message}
        </div>
      )}
    </div>
  );
}

function PackageFormModal({ open, package: pkg, onClose, onSubmit, loading }: {
  open: boolean; package?: TokenPackage; onClose: () => void; onSubmit: (d: Partial<TokenPackage>) => void; loading: boolean;
}) {
  const [name, setName] = useState(pkg?.name || "");
  const [tokens, setTokens] = useState(pkg?.tokens?.toString() || "");
  const [bonus, setBonus] = useState(pkg?.bonus_tokens?.toString() || "0");
  const [price, setPrice] = useState(pkg?.price_dt?.toString() || "");
  const [active, setActive] = useState(pkg?.is_active ?? true);

  if (!open) return null;

  return (
    <Modal open onClose={onClose} title={pkg ? "Edit Package" : "New Package"}
      footer={
        <>
          <button onClick={onClose} className="flex-1 py-3 bg-cream-m rounded-xl font-medium">Cancel</button>
          <button onClick={() => onSubmit({ name, tokens: Number(tokens), bonus_tokens: Number(bonus), price_dt: Number(price), is_active: active })}
            disabled={loading || !name || !tokens || !price} className="flex-1 py-3 bg-orange text-white rounded-xl font-medium disabled:opacity-50">
            {loading ? "..." : pkg ? "Save" : "Create"}
          </button>
        </>
      }>
      <div className="space-y-4">
        <div><label className="block text-sm font-medium text-gray mb-1.5">Name *</label>
          <input value={name} onChange={e => setName(e.target.value)} className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 focus:outline-none focus:ring-2 focus:ring-orange/20" /></div>
        <div className="grid grid-cols-2 gap-4">
          <div><label className="block text-sm font-medium text-gray mb-1.5">Tokens *</label>
            <input type="number" value={tokens} onChange={e => setTokens(e.target.value)} className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 focus:outline-none" /></div>
          <div><label className="block text-sm font-medium text-gray mb-1.5">Bonus Tokens</label>
            <input type="number" value={bonus} onChange={e => setBonus(e.target.value)} className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 focus:outline-none" /></div>
        </div>
        <div><label className="block text-sm font-medium text-gray mb-1.5">Price (DT) *</label>
          <input type="number" step="0.01" value={price} onChange={e => setPrice(e.target.value)} className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 focus:outline-none" /></div>
        {pkg && (
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" checked={active} onChange={e => setActive(e.target.checked)} className="w-4 h-4 rounded" />
            <span className="text-sm">Active</span>
          </label>
        )}
      </div>
    </Modal>
  );
}