import { useState, useEffect, useCallback } from "react";
import { Users, BookOpen, DollarSign, Coins, TrendingUp, GraduationCap, Building2, Activity } from "lucide-react";
import { KPICard } from "../components/KPICard";
import { adminAnalytics } from "../../../api";
import type { DashboardStats, RevenueData, EnrollmentTrend, ApiCostTrend } from "../../../api";
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from "recharts";

const API_URL = "";

export default function AdminDashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [revenue, setRevenue] = useState<RevenueData | null>(null);
  const [enrollments, setEnrollments] = useState<EnrollmentTrend[]>([]);
  const [apiCosts, setApiCosts] = useState<ApiCostTrend[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [period, setPeriod] = useState<"7d" | "30d" | "90d" | "12m">("30d");

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [statsData, revenueData, enrollData, costData] = await Promise.all([
        adminAnalytics.dashboard(),
        adminAnalytics.revenue(period),
        adminAnalytics.enrollments(period),
        adminAnalytics.apiCosts(period),
      ]);
      setStats(statsData);
      setRevenue(revenueData);
      setEnrollments(enrollData.data);
      setApiCosts(costData.data);
    } catch (err) {
      console.error("Failed to fetch dashboard data:", err);
      setError("Failed to load dashboard data. Please try again.");
    }
    setLoading(false);
  }, [period]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const formatDT = (n: number) => n.toLocaleString("fr-TN", { minimumFractionDigits: 0, maximumFractionDigits: 2 });
  const formatNum = (n: number) => n.toLocaleString("fr-TN");

  const userDist = stats ? {
    students: stats.total_students || 0,
    teachers: stats.total_teachers || 0,
    total: stats.total_users || 0,
  } : null;

  const chartPeriodLabels: Record<string, string> = { "7d": "7 Days", "30d": "30 Days", "90d": "90 Days", "12m": "12 Months" };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-navy to-navy-m rounded-3xl p-8 text-white">
        <div className="flex justify-between items-start flex-wrap gap-4">
          <div>
            <h1 className="text-3xl font-display font-light">
              Platform <span className="text-orange-l italic">Overview</span>
            </h1>
            <p className="text-white/60 mt-2">Real-time platform metrics and performance</p>
          </div>
          <div className="flex items-center gap-2">
            {(["7d", "30d", "90d", "12m"] as const).map((p) => (
              <button
                key={p}
                onClick={() => setPeriod(p)}
                className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                  period === p ? "bg-orange text-white" : "bg-white/10 text-white/70 hover:bg-white/20"
                }`}
              >
                {chartPeriodLabels[p]}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-2xl p-6 flex flex-col items-center justify-center text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <button onClick={fetchData} className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium">
            Retry
          </button>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          label="Total Revenue"
          value={revenue ? `${formatDT(revenue.total_revenue)} DT` : "—"}
          subValue={revenue ? `MRR: ${formatDT(revenue.monthly_recurring_revenue)} DT` : ""}
          icon={<DollarSign className="w-5 h-5" />}
          color="green"
          loading={loading}
        />
        <KPICard
          label="Total Users"
          value={stats ? formatNum(stats.total_users) : "—"}
          subValue={stats ? `${formatNum(stats.total_students)} students, ${formatNum(stats.total_teachers)} teachers` : ""}
          icon={<Users className="w-5 h-5" />}
          color="blue"
          loading={loading}
        />
        <KPICard
          label="Tokens Sold"
          value={stats ? formatNum(stats.total_tokens_sold) : "—"}
          subValue={revenue ? `AI cost: ${formatDT(revenue.ai_cost_estimate)} DT` : ""}
          icon={<Coins className="w-5 h-5" />}
          color="orange"
          loading={loading}
        />
        <KPICard
          label="Total Courses"
          value={stats ? formatNum(stats.total_courses) : "—"}
          subValue={stats ? `${formatNum(stats.published_courses)} published` : ""}
          icon={<BookOpen className="w-5 h-5" />}
          color="purple"
          loading={loading}
        />
      </div>

      {/* Secondary KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          label="ARR"
          value={revenue ? `${formatDT(revenue.annual_run_rate)} DT` : "—"}
          subValue="Annual Run Rate"
          icon={<TrendingUp className="w-5 h-5" />}
          color="green"
          loading={loading}
        />
        <KPICard
          label="Active Users"
          value={revenue ? formatNum(revenue.active_users_in_period) : "—"}
          subValue={revenue ? `of ${formatNum(revenue.total_users)} total` : ""}
          icon={<Activity className="w-5 h-5" />}
          color="blue"
          loading={loading}
        />
        <KPICard
          label="Conversion"
          value={revenue ? `${revenue.conversion_rate}%` : "—"}
          subValue="Free to paid"
          icon={<GraduationCap className="w-5 h-5" />}
          color="orange"
          loading={loading}
        />
        <KPICard
          label="Est. Profit"
          value={revenue ? `${formatDT(revenue.estimated_profit)} DT` : "—"}
          subValue="After AI costs"
          icon={<DollarSign className="w-5 h-5" />}
          color={revenue && revenue.estimated_profit >= 0 ? "green" : "red"}
          loading={loading}
        />
      </div>

      {/* Recharts: Enrollment + API Costs */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Enrollment Trend Chart */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <h3 className="text-lg font-semibold text-navy font-display mb-1">New Registrations</h3>
          <p className="text-xs text-gray mb-5">Daily user sign-ups ({chartPeriodLabels[period]})</p>
          {loading ? (
            <div className="h-64 bg-gray-100 rounded-xl animate-pulse" />
          ) : enrollments.length === 0 ? (
            <div className="h-64 flex items-center justify-center text-gray text-sm">No enrollment data</div>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <AreaChart data={enrollments} margin={{ top: 5, right: 5, left: -10, bottom: 0 }}>
                <defs>
                  <linearGradient id="regGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#FF6B35" stopOpacity={0.25} />
                    <stop offset="100%" stopColor="#FF6B35" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#999" }} tickFormatter={(v: string) => v.slice(5)} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: "#999" }} />
                <Tooltip
                  contentStyle={{ borderRadius: 12, border: "1px solid #eee", boxShadow: "0 4px 12px rgba(0,0,0,0.08)" }}
                  labelFormatter={(v: string) => new Date(v).toLocaleDateString("fr-TN")}
                />
                <Area type="monotone" dataKey="registrations" stroke="#FF6B35" strokeWidth={2} fill="url(#regGrad)" name="Registrations" />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* AI Cost Trend Chart */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <h3 className="text-lg font-semibold text-navy font-display mb-1">AI API Costs</h3>
          <p className="text-xs text-gray mb-5">Daily token consumption cost ({chartPeriodLabels[period]})</p>
          {loading ? (
            <div className="h-64 bg-gray-100 rounded-xl animate-pulse" />
          ) : apiCosts.length === 0 ? (
            <div className="h-64 flex items-center justify-center text-gray text-sm">No API cost data</div>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={apiCosts} margin={{ top: 5, right: 5, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#999" }} tickFormatter={(v: string) => v.slice(5)} />
                <YAxis tick={{ fontSize: 11, fill: "#999" }} tickFormatter={(v: number) => `${v.toFixed(2)}`} />
                <Tooltip
                  contentStyle={{ borderRadius: 12, border: "1px solid #eee", boxShadow: "0 4px 12px rgba(0,0,0,0.08)" }}
                  labelFormatter={(v: string) => new Date(v).toLocaleDateString("fr-TN")}
                  formatter={(value: number) => [`${value.toFixed(2)} DT`, "Cost"]}
                />
                <Bar dataKey="estimated_cost_dt" fill="#FF6B35" radius={[4, 4, 0, 0]} name="Cost (DT)" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Bottom Row: Existing Cards */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* User Distribution */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <h3 className="text-lg font-semibold text-navy font-display mb-5">User Distribution</h3>
          {loading ? (
            <div className="space-y-4">
              {[1, 2].map(i => <div key={i} className="h-12 bg-gray-100 rounded-xl animate-pulse" />)}
            </div>
          ) : userDist ? (
            <div className="space-y-5">
              {[
                { label: "Students", value: userDist.students, color: "bg-blue-500", icon: <GraduationCap className="w-4 h-4" /> },
                { label: "Teachers", value: userDist.teachers, color: "bg-green-500", icon: <Users className="w-4 h-4" /> },
              ].map(({ label, value, color, icon }) => {
                const pct = userDist.total > 0 ? Math.round((value / userDist.total) * 100) : 0;
                return (
                  <div key={label}>
                    <div className="flex items-center justify-between text-sm mb-2">
                      <span className="flex items-center gap-2 text-gray-600">
                        <span className={`w-2 h-2 rounded-full ${color}`} />
                        {icon}
                        {label}
                      </span>
                      <span className="font-semibold text-navy">{formatNum(value)} ({pct}%)</span>
                    </div>
                    <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div className={`h-full ${color} rounded-full transition-all duration-500`} style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-gray text-center py-8">No data available</p>
          )}
        </div>

        {/* Plan Distribution */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <h3 className="text-lg font-semibold text-navy font-display mb-5">Plan Distribution</h3>
          {loading ? (
            <div className="space-y-4">
              {[1,2,3].map(i => <div key={i} className="h-10 bg-gray-100 rounded-xl animate-pulse" />)}
            </div>
          ) : revenue && Object.keys(revenue.plan_distribution).length > 0 ? (
            <div className="space-y-3">
              {Object.entries(revenue.plan_distribution).map(([tier, count]) => (
                <div key={tier} className="flex items-center justify-between p-3 bg-cream-m rounded-xl">
                  <div className="flex items-center gap-2">
                    <Building2 className="w-4 h-4 text-gray" />
                    <span className="text-sm font-medium text-navy capitalize">{tier.toLowerCase().replace("_", " ")}</span>
                  </div>
                  <span className="text-lg font-bold text-orange">{count}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray text-center py-8">No plan data</p>
          )}
        </div>

        {/* Quick Stats */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <h3 className="text-lg font-semibold text-navy font-display mb-5">Quick Stats</h3>
          {loading ? (
            <div className="space-y-4">
              {[1,2,3,4].map(i => <div key={i} className="h-10 bg-gray-100 rounded-xl animate-pulse" />)}
            </div>
          ) : stats ? (
            <div className="space-y-3">
              {[
                { label: "Pending Courses", value: stats.pending_courses || 0, color: "text-yellow-600", bg: "bg-yellow-50" },
                { label: "Published Courses", value: stats.published_courses || 0, color: "text-green-600", bg: "bg-green-50" },
                { label: "Total Transactions", value: stats.total_transactions || 0, color: "text-blue-600", bg: "bg-blue-50" },
                { label: "Teacher Registrations", value: stats.pending_teacher_registrations || 0, color: "text-orange-600", bg: "bg-orange-50" },
              ].map(({ label, value, color, bg }) => (
                <div key={label} className={`flex items-center justify-between p-3 ${bg} rounded-xl`}>
                  <span className="text-sm text-gray-600">{label}</span>
                  <span className={`text-lg font-bold ${color}`}>{value}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray text-center py-8">No data available</p>
          )}
        </div>
      </div>

      {/* Top Schools */}
      {revenue && revenue.top_schools.length > 0 && (
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <h3 className="text-lg font-semibold text-navy font-display mb-5">Top Schools by Revenue</h3>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-cream-m">
                <tr>
                  <th className="text-start px-6 py-3 text-xs font-semibold text-gray uppercase">School</th>
                  <th className="text-end px-6 py-3 text-xs font-semibold text-gray uppercase">Revenue (DT)</th>
                  <th className="text-end px-6 py-3 text-xs font-semibold text-gray uppercase">Share</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-black/5">
                {revenue.top_schools.map((school, i) => (
                  <tr key={school.school_id} className="hover:bg-cream/30">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <span className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${
                          i === 0 ? "bg-orange text-white" : i === 1 ? "bg-orange-w text-white" : i === 2 ? "bg-orange-l text-navy" : "bg-cream-m text-gray"
                        }`}>
                          {i + 1}
                        </span>
                        <span className="font-medium text-navy">{school.school_name}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-end font-bold text-green-600">{formatDT(school.revenue)} DT</td>
                    <td className="px-6 py-4 text-end text-gray text-sm">
                      {revenue.total_revenue > 0 ? ((school.revenue / revenue.total_revenue) * 100).toFixed(1) : 0}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
