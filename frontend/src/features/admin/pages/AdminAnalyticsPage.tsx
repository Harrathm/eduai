import { useState, useEffect } from "react";
import { DollarSign, TrendingUp, Users, BookOpen, Activity } from "lucide-react";
import { KPICard } from "../components";
import { adminAnalytics } from "../../../api";
import type { RevenueData, DashboardStats } from "../../../api";

export default function AdminAnalyticsPage() {
  const [revenue, setRevenue] = useState<RevenueData | null>(null);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState<"7d" | "30d" | "90d" | "12m">("30d");

  useEffect(() => {
    setLoading(true);
    Promise.all([
      adminAnalytics.revenue(period),
      adminAnalytics.dashboard(),
    ]).then(([rev, st]) => {
      setRevenue(rev);
      setStats(st);
    }).catch(console.error).finally(() => setLoading(false));
  }, [period]);

  const formatDT = (n: number) => n.toLocaleString("fr-TN", { minimumFractionDigits: 0 });
  const formatNum = (n: number) => n.toLocaleString("fr-TN");

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-display font-light text-navy">Analytics <span className="italic text-orange">& Revenue</span></h1>
          <p className="text-gray text-sm mt-1">Financial performance and platform metrics</p>
        </div>
        <div className="flex gap-2">
          {(["7d", "30d", "90d", "12m"] as const).map(p => (
            <button key={p} onClick={() => setPeriod(p)}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${period === p ? "bg-orange text-white" : "bg-white border border-black/5 text-gray hover:bg-cream"}`}>
              {p === "7d" ? "7D" : p === "30d" ? "30D" : p === "90d" ? "90D" : "12M"}
            </button>
          ))}
        </div>
      </div>

      {/* Revenue KPI Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard label="Total Revenue" value={revenue ? `${formatDT(revenue.total_revenue)} DT` : "—"} icon={<DollarSign className="w-5 h-5" />} color="green" loading={loading} />
        <KPICard label="MRR" value={revenue ? `${formatDT(revenue.monthly_recurring_revenue)} DT` : "—"} icon={<TrendingUp className="w-5 h-5" />} color="orange" loading={loading} />
        <KPICard label="ARR" value={revenue ? `${formatDT(revenue.annual_run_rate)} DT` : "—"} subValue="Annual Run Rate" icon={<DollarSign className="w-5 h-5" />} color="purple" loading={loading} />
        <KPICard label="Transactions" value={revenue ? formatNum(revenue.total_transactions) : "—"} icon={<Activity className="w-5 h-5" />} color="blue" loading={loading} />
      </div>

      {/* Cost & Profit Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard label="AI Cost Est." value={revenue ? `${formatDT(revenue.ai_cost_estimate)} DT` : "—"} subValue="~1% of token revenue" icon={<TrendingUp className="w-5 h-5" />} color="red" loading={loading} />
        <KPICard label="Est. Profit" value={revenue ? `${formatDT(revenue.estimated_profit)} DT` : "—"} subValue="Revenue - AI cost" icon={<DollarSign className="w-5 h-5" />} color={revenue && revenue.estimated_profit >= 0 ? "green" : "red"} loading={loading} />
        <KPICard label="Active Users" value={revenue ? formatNum(revenue.active_users_in_period) : "—"} subValue={`of ${revenue ? formatNum(revenue.total_users) : 0} total`} icon={<Users className="w-5 h-5" />} color="blue" loading={loading} />
        <KPICard label="Conversion" value={revenue ? `${revenue.conversion_rate}%` : "—"} subValue="Free to paid" icon={<Activity className="w-5 h-5" />} color="orange" loading={loading} />
      </div>

      {/* Revenue by Currency */}
      {revenue && Object.keys(revenue.revenue_by_currency).length > 0 && (
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <h3 className="text-lg font-semibold text-navy font-display mb-5">Revenue by Currency</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(revenue.revenue_by_currency).map(([curr, amount]) => (
              <div key={curr} className="p-4 bg-cream-m rounded-xl text-center">
                <p className="text-2xl font-bold text-green-600">{formatDT(amount)}</p>
                <p className="text-sm text-gray mt-1">{curr}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Platform Summary */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
        <h3 className="text-lg font-semibold text-navy font-display mb-5">Platform Summary</h3>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { label: "Total Users", value: stats?.total_users || 0, icon: <Users className="w-5 h-5" />, color: "blue" },
            { label: "Total Courses", value: stats?.total_courses || 0, icon: <BookOpen className="w-5 h-5" />, color: "purple" },
            { label: "Published Courses", value: stats?.published_courses || 0, icon: <BookOpen className="w-5 h-5" />, color: "green" },
            { label: "Pending Courses", value: stats?.pending_courses || 0, icon: <BookOpen className="w-5 h-5" />, color: "yellow" },
          ].map(({ label, value, icon, color }) => (
            <div key={label} className="p-4 bg-cream-m rounded-xl">
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center mb-3 bg-${color}-100 text-${color}-600`}>
                {icon}
              </div>
              <p className="text-2xl font-bold text-navy">{formatNum(value)}</p>
              <p className="text-sm text-gray mt-1">{label}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Plan Distribution */}
      {revenue && Object.keys(revenue.plan_distribution).length > 0 && (
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <h3 className="text-lg font-semibold text-navy font-display mb-5">Plan Distribution</h3>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {Object.entries(revenue.plan_distribution).map(([tier, count]) => {
              const colors: Record<string, string> = { FREE: "bg-blue-50 text-blue-600", TEACHER_PRO: "bg-orange-50 text-orange-600", SCHOOL: "bg-purple-50 text-purple-600", INSTITUTION: "bg-green-50 text-green-600" };
              return (
                <div key={tier} className={`p-5 rounded-xl ${colors[tier] || "bg-gray-50 text-gray-600"}`}>
                  <p className="text-3xl font-bold">{count}</p>
                  <p className="text-sm font-medium mt-1">{tier.replace("_", " ")}</p>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}