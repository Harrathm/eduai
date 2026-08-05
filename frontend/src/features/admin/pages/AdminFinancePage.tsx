import { useState, useEffect, useCallback } from "react";
import { DollarSign, Coins, TrendingUp, ArrowUpRight, ArrowDownRight, RefreshCw, Search, Download, Calendar, Download as DownIcon } from "lucide-react";
import { KPICard, AdminTable, StatusBadge } from "../components";
import { adminTransactions, adminAnalytics } from "../../../api";
import type { Transaction, DashboardStats, PaginatedResponse } from "../../../api";

const typeColors: Record<string, string> = {
  token_recharge: "bg-blue-50 text-blue-600",
  token_purchase: "bg-green-50 text-green-600",
  token_spend: "bg-red-50 text-red-400",
  token_consumption: "bg-red-50 text-red-400",
  course_purchase: "bg-purple-50 text-purple-600",
  payout: "bg-orange-50 text-orange-600",
};

const CURRENCY_SYMBOLS: Record<string, string> = {
  DT: "DT", TOKEN: "TKN", USD: "$", EUR: "€",
};

export default function AdminFinancePage() {
  const [result, setResult] = useState<PaginatedResponse<Transaction> | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [skip, setSkip] = useState(0);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const limit = 50;

  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(search), 400);
    return () => clearTimeout(t);
  }, [search]);

  const fetchData = useCallback(async (isRefresh = false) => {
    isRefresh ? setRefreshing(true) : setLoading(true);
    try {
      const [txs, st] = await Promise.all([
        adminTransactions.list({
          skip, limit,
          search: debouncedSearch || undefined,
          type: typeFilter || undefined,
          status: statusFilter || undefined,
          date_from: dateFrom || undefined,
          date_to: dateTo || undefined,
        }),
        adminAnalytics.dashboard(),
      ]);
      setResult(txs);
      setStats(st);
    } catch (err) { console.error(err); }
    setLoading(false);
    setRefreshing(false);
  }, [debouncedSearch, typeFilter, statusFilter, dateFrom, dateTo, skip]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handlePageChange = (newSkip: number) => setSkip(newSkip);

  const exportCSV = () => {
    if (!result?.items.length) return;
    const headers = ["ID", "User", "Email", "Type", "Amount", "Currency", "Status", "Description", "Date"];
    const rows = result.items.map(t => [
      t.id, t.user_name || "", t.user_email || "", t.type, t.amount, t.currency, t.status, t.description || "", t.created_at
    ]);
    const csv = [headers, ...rows].map(r => r.map(c => `"${c}"`).join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url; a.download = `transactions_${new Date().toISOString().slice(0,10)}.csv`; a.click();
    URL.revokeObjectURL(url);
  };

  const transactions = result?.items || [];
  const totalIn = transactions.filter(t => !["token_spend", "token_consumption", "payout"].includes(t.type)).reduce((s, t) => s + t.amount, 0);
  const totalOut = transactions.filter(t => ["token_spend", "token_consumption", "payout"].includes(t.type)).reduce((s, t) => s + t.amount, 0);

  const columns = [
    { key: "type", header: "Type", render: (t: Transaction) => (
      <span className={`px-2.5 py-1 text-xs rounded-full font-medium ${typeColors[t.type] || "bg-gray-100 text-gray-600"}`}>
        {t.type.replace(/_/g, " ")}
      </span>
    )},
    { key: "user", header: "User", render: (t: Transaction) => (
      <div>
        <div className="font-medium text-navy text-sm">{t.user_name || "—"}</div>
        <div className="text-xs text-gray">{t.user_email || "—"}</div>
      </div>
    )},
    { key: "amount", header: "Amount", render: (t: Transaction) => {
      const isDebit = ["token_spend", "token_consumption", "payout"].includes(t.type);
      return (
        <div className={`flex items-center gap-1 font-bold ${isDebit ? "text-red-500" : "text-green-600"}`}>
          {isDebit ? <ArrowDownRight className="w-4 h-4" /> : <ArrowUpRight className="w-4 h-4" />}
          {t.currency === "DT" ? `${t.amount.toLocaleString("fr-TN")} DT` : `${t.amount.toLocaleString("fr-TN")} ${t.currency}`}
        </div>
      );
    }},
    { key: "status", header: "Status", render: (t: Transaction) => (
      <StatusBadge label={t.status} variant={t.status === "completed" ? "success" : t.status === "pending" ? "yellow" : "red"} dot />
    )},
    { key: "description", header: "Description", render: (t: Transaction) => (
      <span className="text-xs text-gray max-w-[180px] truncate block">{t.description || "—"}</span>
    )},
    { key: "created_at", header: "Date", render: (t: Transaction) => (
      <span className="text-xs text-gray whitespace-nowrap">{new Date(t.created_at).toLocaleString("fr-TN")}</span>
    )},
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-display font-light text-navy">Finance <span className="italic text-orange">& Transactions</span></h1>
          <p className="text-gray text-sm mt-1">{result ? `${result.total.toLocaleString("fr-TN")} transactions total` : "Loading..."}</p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={() => fetchData(true)} className="p-2.5 bg-white rounded-xl shadow-sm border border-black/5 hover:bg-cream">
            <RefreshCw className={`w-5 h-5 text-gray ${refreshing ? "animate-spin" : ""}`} />
          </button>
          <button onClick={exportCSV} disabled={!transactions.length}
            className="flex items-center gap-2 px-4 py-2.5 bg-navy text-white rounded-xl font-medium text-sm hover:bg-navy-m disabled:opacity-50 shadow-sm">
            <Download className="w-4 h-4" /> Export CSV
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard label="Total Revenue" value={stats ? `${stats.total_dt_revenue.toLocaleString("fr-TN")} DT` : "—"} icon={<DollarSign className="w-5 h-5" />} color="green" loading={loading} />
        <KPICard label="Tokens Sold" value={stats ? stats.total_tokens_sold.toLocaleString("fr-TN") : "—"} icon={<Coins className="w-5 h-5" />} color="orange" loading={loading} />
        <KPICard label="In Flow" value={`${totalIn.toLocaleString("fr-TN")} DT`} icon={<ArrowUpRight className="w-5 h-5" />} color="green" loading={loading} subValue={`${transactions.filter(t => !["token_spend", "token_consumption", "payout"].includes(t.type)).length} transactions`} />
        <KPICard label="Out Flow" value={`${totalOut.toLocaleString("fr-TN")} DT`} icon={<ArrowDownRight className="w-5 h-5" />} color="red" loading={loading} subValue={`${transactions.filter(t => ["token_spend", "token_consumption", "payout"].includes(t.type)).length} transactions`} />
      </div>

      {/* Filters */}
      <div className="bg-white rounded-2xl p-4 shadow-sm border border-black/5 flex flex-wrap items-center gap-4">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray" />
          <input type="text" value={search} onChange={e => { setSearch(e.target.value); setSkip(0); }}
            placeholder="Search user, email, description..." className="w-full ps-12 pe-4 py-3 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none focus:ring-2 focus:ring-orange/20" />
        </div>
        <select value={typeFilter} onChange={e => { setTypeFilter(e.target.value); setSkip(0); }}
          className="px-4 py-3 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none">
          <option value="">All Types</option>
          <option value="TOKEN_RECHARGE">Token Recharge</option>
          <option value="TOKEN_PURCHASE">Token Purchase</option>
          <option value="TOKEN_SPEND">Token Spend</option>
          <option value="TOKEN_CONSUMPTION">Token Consumption</option>
          <option value="COURSE_PURCHASE">Course Purchase</option>
          <option value="PAYOUT">Payout</option>
        </select>
        <select value={statusFilter} onChange={e => { setStatusFilter(e.target.value); setSkip(0); }}
          className="px-4 py-3 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none">
          <option value="">All Status</option>
          <option value="completed">Completed</option>
          <option value="pending">Pending</option>
          <option value="failed">Failed</option>
        </select>
        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4 text-gray" />
          <input type="date" value={dateFrom} onChange={e => { setDateFrom(e.target.value); setSkip(0); }}
            className="px-3 py-3 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none" placeholder="From" />
          <span className="text-gray text-sm">to</span>
          <input type="date" value={dateTo} onChange={e => { setDateTo(e.target.value); setSkip(0); }}
            className="px-3 py-3 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none" placeholder="To" />
        </div>
        {(debouncedSearch || typeFilter || statusFilter || dateFrom || dateTo) && (
          <button onClick={() => { setSearch(""); setDebouncedSearch(""); setTypeFilter(""); setStatusFilter(""); setDateFrom(""); setDateTo(""); setSkip(0); }}
            className="px-3 py-2 text-sm text-orange hover:bg-orange/5 rounded-lg">Clear filters</button>
        )}
      </div>

      <AdminTable columns={columns} data={transactions} loading={loading}
        emptyMessage={debouncedSearch ? `No transactions matching "${debouncedSearch}"` : "No transactions found"} rowKey="id"
        pagination={result ? { page: Math.floor(skip / limit) + 1, per_page: limit, total: result.total, onPageChange: p => setSkip((p - 1) * limit) } : undefined} />

      {toast.show && (
        <div className={`fixed top-6 right-6 z-50 px-6 py-4 rounded-xl shadow-lg text-white bg-green-500`}>
          {toast.message}
        </div>
      )}
    </div>
  );
}