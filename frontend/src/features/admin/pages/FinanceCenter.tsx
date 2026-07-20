import { useState, useEffect, useCallback } from "react";
import { Search, Plus, Minus, DollarSign, Coins, RefreshCw, ChevronLeft, ChevronRight } from "lucide-react";
import { adminUsers, adminAnalytics, adminTransactions } from "../api";
import type { WalletEntry, GlobalStats } from "../api";

export default function FinanceCenter() {
  const [wallets, setWallets] = useState<WalletEntry[]>([]);
  const [stats, setStats] = useState<GlobalStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [skip, setSkip] = useState(0);
  const [total, setTotal] = useState(0);
  const [selected, setSelected] = useState<WalletEntry | null>(null);
  const [modal, setModal] = useState<"add" | "deduct" | null>(null);
  const [amountDt, setAmountDt] = useState("");
  const [amountTokens, setAmountTokens] = useState("");
  const [reason, setReason] = useState("");
  const [actionLoading, setActionLoading] = useState(false);
  const [toast, setToast] = useState<{ show: boolean; message: string; error?: boolean }>({ show: false, message: "" });
  const limit = 20;

  const showToast = (message: string, error = false) => {
    setToast({ show: true, message, error });
    setTimeout(() => setToast({ show: false, message: "" }), 3000);
  };

  const fetchWallets = useCallback(async () => {
    setLoading(true);
    try {
      const [res, gs] = await Promise.all([
        adminUsers.listWallets({ skip, limit }),
        adminAnalytics.global(),
      ]);
      setWallets(res.items);
      setTotal(res.total);
      setStats(gs);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  }, [skip]);

  useEffect(() => { fetchWallets(); }, [fetchWallets]);

  const filtered = search
    ? wallets.filter(w => w.email.toLowerCase().includes(search.toLowerCase()) || w.full_name?.toLowerCase().includes(search.toLowerCase()))
    : wallets;

  const openModal = (wallet: WalletEntry, action: "add" | "deduct") => {
    setSelected(wallet);
    setModal(action);
    setAmountDt("");
    setAmountTokens("");
    setReason(action === "add" ? "Admin credit" : "Admin deduction");
  };

  const handleAdjust = async () => {
    if (!selected) return;
    const dt = parseFloat(amountDt) || 0;
    const tokens = parseInt(amountTokens) || 0;
    if (dt <= 0 && tokens <= 0) { showToast("Enter at least one amount", true); return; }

    setActionLoading(true);
    try {
      if (modal === "add") {
        await adminUsers.addWallet(selected.id, tokens || undefined, dt || undefined, reason);
        showToast(`Added ${dt} DT + ${tokens} TKN to ${selected.email}`);
      } else {
        await adminUsers.deductWallet(selected.id, tokens || undefined, dt || undefined, reason);
        showToast(`Deducted ${dt} DT + ${tokens} TKN from ${selected.email}`);
      }
      setModal(null);
      fetchWallets();
    } catch (err: any) {
      showToast(err.message || "Action failed", true);
    }
    setActionLoading(false);
  };

  const formatNum = (n: number) => n.toLocaleString("fr-TN");

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-display font-light text-navy">Finance <span className="italic text-orange">Center</span></h1>
          <p className="text-gray text-sm mt-1">{total} users</p>
        </div>
        <button onClick={fetchWallets} className="p-2.5 bg-white rounded-xl shadow-sm border border-black/5 hover:bg-cream">
          <RefreshCw className={`w-5 h-5 text-gray ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: "Total DT in System", value: stats ? `${formatNum(stats.finances.total_dt_in_system)} DT` : "—", icon: <DollarSign className="w-5 h-5" />, color: "green" },
          { label: "Total Tokens in System", value: stats ? formatNum(stats.finances.total_tokens_in_system) : "—", icon: <Coins className="w-5 h-5" />, color: "orange" },
          { label: "AI Tokens Consumed", value: stats ? formatNum(stats.ai.total_tokens_consumed) : "—", icon: <Coins className="w-5 h-5" />, color: "purple" },
          { label: "Est. AI Cost", value: stats ? `${formatNum(stats.ai.estimated_cost_dt)} DT` : "—", icon: <DollarSign className="w-5 h-5" />, color: "red" },
        ].map(({ label, value, icon, color }) => (
          <div key={label} className="bg-white rounded-2xl p-5 shadow-sm border border-black/5">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs text-gray font-medium uppercase tracking-wider">{label}</span>
              <span className={`w-9 h-9 rounded-xl bg-${color}-50 flex items-center justify-center text-${color}-600`}>{icon}</span>
            </div>
            <div className="text-2xl font-bold text-navy">{loading ? <div className="h-8 w-24 bg-gray-100 rounded animate-pulse" /> : value}</div>
          </div>
        ))}
      </div>

      {/* Search */}
      <div className="bg-white rounded-2xl p-4 shadow-sm border border-black/5">
        <div className="relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray" />
          <input type="text" value={search} onChange={e => setSearch(e.target.value)}
            placeholder="Search by email or name..." className="w-full pl-12 pr-4 py-3 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none focus:ring-2 focus:ring-orange/20" />
        </div>
      </div>

      {/* Wallet Table */}
      <div className="bg-white rounded-2xl shadow-sm border border-black/5 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-cream-m">
              <tr>
                <th className="text-left px-5 py-4 text-xs font-semibold text-gray uppercase">User</th>
                <th className="text-left px-5 py-4 text-xs font-semibold text-gray uppercase">Role</th>
                <th className="text-right px-5 py-4 text-xs font-semibold text-gray uppercase">DT Balance</th>
                <th className="text-right px-5 py-4 text-xs font-semibold text-gray uppercase">Token Balance</th>
                <th className="text-right px-5 py-4 text-xs font-semibold text-gray uppercase">Total DT Spent</th>
                <th className="text-right px-5 py-4 text-xs font-semibold text-gray uppercase">Total TKN Spent</th>
                <th className="text-right px-5 py-4 text-xs font-semibold text-gray uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-black/5">
              {loading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i}>
                    {Array.from({ length: 7 }).map((_, j) => (
                      <td key={j} className="px-5 py-4"><div className="h-5 bg-gray-100 rounded animate-pulse" /></td>
                    ))}
                  </tr>
                ))
              ) : filtered.length === 0 ? (
                <tr><td colSpan={7} className="text-center py-12 text-gray text-sm">No wallets found</td></tr>
              ) : filtered.map(w => (
                <tr key={w.id} className="hover:bg-cream/30 transition-colors">
                  <td className="px-5 py-4">
                    <div className="font-medium text-navy text-sm">{w.full_name || "—"}</div>
                    <div className="text-xs text-gray">{w.email}</div>
                  </td>
                  <td className="px-5 py-4">
                    <span className="px-2.5 py-1 text-xs rounded-full font-medium bg-blue-50 text-blue-600 capitalize">
                      {w.role.toLowerCase().replace("_", " ")}
                    </span>
                  </td>
                  <td className="px-5 py-4 text-right font-semibold text-green-600">{formatNum(w.balance_dt)} DT</td>
                  <td className="px-5 py-4 text-right font-semibold text-orange">{formatNum(w.balance_tokens)} TKN</td>
                  <td className="px-5 py-4 text-right text-gray text-sm">{formatNum(w.total_dt_spent)} DT</td>
                  <td className="px-5 py-4 text-right text-gray text-sm">{formatNum(w.total_tokens_spent)} TKN</td>
                  <td className="px-5 py-4 text-right">
                    <div className="flex items-center justify-end gap-1">
                      <button onClick={() => openModal(w, "add")}
                        className="p-2 rounded-lg text-green-600 hover:bg-green-50 transition-colors" title="Add funds">
                        <Plus className="w-4 h-4" />
                      </button>
                      <button onClick={() => openModal(w, "deduct")}
                        className="p-2 rounded-lg text-red-500 hover:bg-red-50 transition-colors" title="Deduct funds">
                        <Minus className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between px-5 py-4 border-t border-black/5">
          <span className="text-sm text-gray">{total} total</span>
          <div className="flex items-center gap-2">
            <button disabled={skip <= 0} onClick={() => setSkip(Math.max(0, skip - limit))}
              className="p-2 rounded-lg hover:bg-cream disabled:opacity-30"><ChevronLeft className="w-5 h-5" /></button>
            <span className="text-sm text-navy font-medium">{Math.floor(skip / limit) + 1} / {Math.max(1, Math.ceil(total / limit))}</span>
            <button disabled={skip + limit >= total} onClick={() => setSkip(skip + limit)}
              className="p-2 rounded-lg hover:bg-cream disabled:opacity-30"><ChevronRight className="w-5 h-5" /></button>
          </div>
        </div>
      </div>

      {/* Modal */}
      {modal && selected && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setModal(null)}>
          <div className="bg-white rounded-3xl p-8 w-full max-w-md shadow-2xl" onClick={e => e.stopPropagation()}>
            <h2 className="text-xl font-display font-semibold text-navy mb-1">
              {modal === "add" ? "Add Funds" : "Deduct Funds"}
            </h2>
            <p className="text-sm text-gray mb-6">{selected.email} ({selected.full_name || "—"})</p>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-gray mb-1.5">DT Amount</label>
                <input type="number" step="0.01" min="0" value={amountDt} onChange={e => setAmountDt(e.target.value)}
                  className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none focus:ring-2 focus:ring-orange/20" placeholder="0.00" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray mb-1.5">Token Amount</label>
                <input type="number" step="1" min="0" value={amountTokens} onChange={e => setAmountTokens(e.target.value)}
                  className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none focus:ring-2 focus:ring-orange/20" placeholder="0" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray mb-1.5">Reason</label>
                <input type="text" value={reason} onChange={e => setReason(e.target.value)}
                  className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none focus:ring-2 focus:ring-orange/20" />
              </div>
            </div>

            <div className="flex items-center gap-3 mt-8">
              <button onClick={() => setModal(null)} disabled={actionLoading}
                className="flex-1 px-5 py-3 bg-cream-m rounded-xl text-navy font-medium text-sm hover:bg-cream disabled:opacity-50">
                Cancel
              </button>
              <button onClick={handleAdjust} disabled={actionLoading}
                className={`flex-1 px-5 py-3 rounded-xl text-white font-medium text-sm disabled:opacity-50 ${
                  modal === "add" ? "bg-green-600 hover:bg-green-700" : "bg-red-500 hover:bg-red-600"
                }`}>
                {actionLoading ? "Processing..." : modal === "add" ? "Add Funds" : "Deduct Funds"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Toast */}
      {toast.show && (
        <div className={`fixed top-6 right-6 z-50 px-6 py-4 rounded-xl shadow-lg text-white ${toast.error ? "bg-red-500" : "bg-green-500"}`}>
          {toast.message}
        </div>
      )}
    </div>
  );
}
