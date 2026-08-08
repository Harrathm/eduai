import { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { Users, BookOpen, DollarSign, Coins, TrendingUp, GraduationCap, Building2, Activity } from "lucide-react";
import { KPICard } from "../components/KPICard";
import { Button } from "@/components/ui";
import { adminDashboard, adminAnalytics } from "../../../api";
import type { AdminDashboardStats, EnrollmentTrend, ApiCostTrend } from "../../../api";
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from "recharts";

export default function AdminDashboardPage() {
  const { t } = useTranslation();
  const [stats, setStats] = useState<AdminDashboardStats | null>(null);
  const [revenue, setRevenue] = useState<any | null>(null);
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
        adminDashboard.stats(),
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
      setError(t("admin.dashboard.errors.loadFailed"));
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

  return (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-navy to-navy-m rounded-3xl p-8 text-white">
        <div className="flex justify-between items-start flex-wrap gap-4">
          <div>
            <h1 className="text-3xl font-display font-light">
              {t("admin.dashboard.title")} <span className="text-orange-l italic">{t("admin.dashboard.titleSuffix")}</span>
            </h1>
            <p className="text-white/60 mt-2">{t("admin.dashboard.subtitle")}</p>
          </div>
          <div className="flex items-center gap-2">
            {(["7d", "30d", "90d", "12m"] as const).map((p) => (
              <Button
                key={p}
                variant={period === p ? "primary" : "ghost"}
                size="sm"
                onClick={() => setPeriod(p)}
              >
                {t(`admin.dashboard.period.${p}`)}
              </Button>
            ))}
          </div>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-2xl p-6 flex flex-col items-center justify-center text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <Button variant="danger" size="sm" onClick={fetchData}>
            {t("admin.dashboard.btn.retry")}
          </Button>
        </div>
      )}

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          label={t("admin.dashboard.kpi.totalRevenue")}
          value={revenue ? `${formatDT(revenue.total_revenue)} DT` : "—"}
          subValue={revenue ? `MRR: ${formatDT(revenue.monthly_recurring_revenue)} DT` : ""}
          icon={<DollarSign className="w-5 h-5" />}
          color="green"
          loading={loading}
        />
        <KPICard
          label={t("admin.dashboard.kpi.totalUsers")}
          value={stats ? formatNum(stats.total_users) : "—"}
          subValue={stats ? `${formatNum(stats.total_students)} ${t("admin.dashboard.kpi.students")}, ${formatNum(stats.total_teachers)} ${t("admin.dashboard.kpi.teachers")}` : ""}
          icon={<Users className="w-5 h-5" />}
          color="blue"
          loading={loading}
        />
        <KPICard
          label={t("admin.dashboard.kpi.tokensSold")}
          value={stats ? formatNum(stats.total_tokens_sold) : "—"}
          subValue={revenue ? `${t("admin.dashboard.kpi.aiCost")}: ${formatDT(revenue.ai_cost_estimate)} DT` : ""}
          icon={<Coins className="w-5 h-5" />}
          color="orange"
          loading={loading}
        />
        <KPICard
          label={t("admin.dashboard.kpi.totalCourses")}
          value={stats ? formatNum(stats.total_courses) : "—"}
          subValue={stats ? `${formatNum(stats.published_courses)} ${t("admin.dashboard.kpi.published")}` : ""}
          icon={<BookOpen className="w-5 h-5" />}
          color="purple"
          loading={loading}
        />
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          label="ARR"
          value={revenue ? `${formatDT(revenue.annual_run_rate)} DT` : "—"}
          subValue={t("admin.dashboard.kpi.annualRunRate")}
          icon={<TrendingUp className="w-5 h-5" />}
          color="green"
          loading={loading}
        />
        <KPICard
          label={t("admin.dashboard.kpi.activeUsers")}
          value={revenue ? formatNum(revenue.active_users_in_period) : "—"}
          subValue={revenue ? `${t("admin.dashboard.kpi.ofTotal", { total: formatNum(revenue.total_users) })}` : ""}
          icon={<Activity className="w-5 h-5" />}
          color="blue"
          loading={loading}
        />
        <KPICard
          label={t("admin.dashboard.kpi.conversion")}
          value={revenue ? `${revenue.conversion_rate}%` : "—"}
          subValue={t("admin.dashboard.kpi.freeToPaid")}
          icon={<GraduationCap className="w-5 h-5" />}
          color="orange"
          loading={loading}
        />
        <KPICard
          label={t("admin.dashboard.kpi.estProfit")}
          value={revenue ? `${formatDT(revenue.estimated_profit)} DT` : "—"}
          subValue={t("admin.dashboard.kpi.afterAiCosts")}
          icon={<DollarSign className="w-5 h-5" />}
          color={revenue && revenue.estimated_profit >= 0 ? "green" : "red"}
          loading={loading}
        />
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <h3 className="text-lg font-semibold text-navy font-display mb-1">{t("admin.dashboard.chart.enrollmentTitle")}</h3>
          <p className="text-xs text-gray mb-5">{t("admin.dashboard.chart.enrollmentSubtitle", { period: t(`admin.dashboard.period.${period}`) })}</p>
          {loading ? (
            <div className="h-64 bg-gray-100 rounded-xl animate-pulse" />
          ) : enrollments.length === 0 ? (
            <div className="h-64 flex items-center justify-center text-gray text-sm">{t("admin.dashboard.chart.noEnrollmentData")}</div>
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
                <Area type="monotone" dataKey="registrations" stroke="#FF6B35" strokeWidth={2} fill="url(#regGrad)" name={t("admin.dashboard.chart.registrations")} />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <h3 className="text-lg font-semibold text-navy font-display mb-1">{t("admin.dashboard.chart.apiCostTitle")}</h3>
          <p className="text-xs text-gray mb-5">{t("admin.dashboard.chart.apiCostSubtitle", { period: t(`admin.dashboard.period.${period}`) })}</p>
          {loading ? (
            <div className="h-64 bg-gray-100 rounded-xl animate-pulse" />
          ) : apiCosts.length === 0 ? (
            <div className="h-64 flex items-center justify-center text-gray text-sm">{t("admin.dashboard.chart.noApiCostData")}</div>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={apiCosts} margin={{ top: 5, right: 5, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#999" }} tickFormatter={(v: string) => v.slice(5)} />
                <YAxis tick={{ fontSize: 11, fill: "#999" }} tickFormatter={(v: number) => `${v.toFixed(2)}`} />
                <Tooltip
                  contentStyle={{ borderRadius: 12, border: "1px solid #eee", boxShadow: "0 4px 12px rgba(0,0,0,0.08)" }}
                  labelFormatter={(v: string) => new Date(v).toLocaleDateString("fr-TN")}
                  formatter={(value: number) => [`${value.toFixed(2)} DT`, t("admin.dashboard.chart.cost")]}
                />
                <Bar dataKey="estimated_cost_dt" fill="#FF6B35" radius={[4, 4, 0, 0]} name={t("admin.dashboard.chart.costDT")} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <h3 className="text-lg font-semibold text-navy font-display mb-5">{t("admin.dashboard.section.userDistribution")}</h3>
          {loading ? (
            <div className="space-y-4">
              {[1, 2].map(i => <div key={i} className="h-12 bg-gray-100 rounded-xl animate-pulse" />)}
            </div>
          ) : userDist ? (
            <div className="space-y-5">
              {[
                { label: t("admin.dashboard.kpi.students"), value: userDist.students, color: "bg-blue-500", icon: <GraduationCap className="w-4 h-4" /> },
                { label: t("admin.dashboard.kpi.teachers"), value: userDist.teachers, color: "bg-green-500", icon: <Users className="w-4 h-4" /> },
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
            <p className="text-gray text-center py-8">{t("admin.dashboard.empty.noData")}</p>
          )}
        </div>

        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <h3 className="text-lg font-semibold text-navy font-display mb-5">{t("admin.dashboard.section.planDistribution")}</h3>
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
            <p className="text-gray text-center py-8">{t("admin.dashboard.empty.noPlanData")}</p>
          )}
        </div>

        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <h3 className="text-lg font-semibold text-navy font-display mb-5">{t("admin.dashboard.section.quickStats")}</h3>
          {loading ? (
            <div className="space-y-4">
              {[1,2,3,4].map(i => <div key={i} className="h-10 bg-gray-100 rounded-xl animate-pulse" />)}
            </div>
          ) : stats ? (
            <div className="space-y-3">
              {[
                { label: t("admin.dashboard.stats.pendingCourses"), value: stats.pending_courses || 0, color: "text-yellow-600", bg: "bg-yellow-50" },
                { label: t("admin.dashboard.stats.publishedCourses"), value: stats.published_courses || 0, color: "text-green-600", bg: "bg-green-50" },
                { label: t("admin.dashboard.stats.totalTransactions"), value: stats.total_transactions || 0, color: "text-blue-600", bg: "bg-blue-50" },
                { label: t("admin.dashboard.stats.teacherRegistrations"), value: stats.pending_teacher_registrations || 0, color: "text-orange-600", bg: "bg-orange-50" },
              ].map(({ label, value, color, bg }) => (
                <div key={label} className={`flex items-center justify-between p-3 ${bg} rounded-xl`}>
                  <span className="text-sm text-gray-600">{label}</span>
                  <span className={`text-lg font-bold ${color}`}>{value}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray text-center py-8">{t("admin.dashboard.empty.noData")}</p>
          )}
        </div>
      </div>

      {revenue && revenue.top_schools.length > 0 && (
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <h3 className="text-lg font-semibold text-navy font-display mb-5">{t("admin.dashboard.section.topSchools")}</h3>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-cream-m">
                <tr>
                  <th className="text-start px-6 py-3 text-xs font-semibold text-gray uppercase">{t("admin.dashboard.table.colSchool")}</th>
                  <th className="text-end px-6 py-3 text-xs font-semibold text-gray uppercase">{t("admin.dashboard.table.colRevenue")}</th>
                  <th className="text-end px-6 py-3 text-xs font-semibold text-gray uppercase">{t("admin.dashboard.table.colShare")}</th>
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
