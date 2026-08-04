import { useState, useEffect } from "react";
import { useAuthStore } from "../../../store/authStore";
import { 
  TrendingUp, 
  Users, 
  BookOpen,
  Clock,
  DollarSign,
  CheckCircle,
  AlertTriangle,
  ShoppingCart,
  GraduationCap,
  Video,
  Coins,
  CreditCard
} from "lucide-react";

const API_URL = "";

interface PlatformStats {
  total_users: number;
  total_teachers: number;
  total_students: number;
  total_courses: number;
  total_transactions: number;
  total_tokens_sold: number;
  total_dt_revenue: number;
  total_tokens_consumed: number;
  pending_courses: number;
  pending_teachers: number;
}

interface UserActivity {
  id: number;
  type: string;
  user: string;
  action: string;
  target: string;
  time: string;
}

interface RevenueDay {
  day: string;
  amount: number;
}

interface TokenDay {
  day: string;
  tokens: number;
}

export default function PlatformOverview() {
  const { token, user } = useAuthStore();
  const [stats, setStats] = useState<PlatformStats | null>(null);
  const [activity, setActivity] = useState<UserActivity[]>([]);
  const [revenueData, setRevenueData] = useState<RevenueDay[]>([]);
  const [tokenData, setTokenData] = useState<TokenDay[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      fetchDashboardData();
    }
  }, [token]);

  const fetchDashboardData = async () => {
    if (!token) return;
    setLoading(true);
    
    try {
      // Fetch stats
      const statsRes = await fetch(`${API_URL}/api/admin/dashboard`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      if (statsRes.ok) {
        const data = await statsRes.json();
        setStats(data);
      } else {
        // Fetch individual data if dashboard endpoint not available
        await fetchAllData();
      }
    } catch (err) {
      console.error(err);
      await fetchAllData();
    }
    
    setLoading(false);
  };

  const fetchAllData = async () => {
    if (!token) return;
    
    try {
      // Users
      const usersRes = await fetch(`${API_URL}/api/admin/users`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const users = usersRes.ok ? await usersRes.json() : [];
      
      // Courses  
      const coursesRes = await fetch(`${API_URL}/api/admin/courses`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const courses = coursesRes.ok ? await coursesRes.json() : [];
      
      // Transactions
      const transRes = await fetch(`${API_URL}/api/admin/transactions`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const transactions = transRes.ok ? await transRes.json() : [];
      
      // Calculate stats
      const teachers = users.filter((u: any) => u.role === "teacher");
      const students = users.filter((u: any) => u.role === "student");
      const pendingCourses = courses.filter((c: any) => c.status === "pending");
      
      const totalRevenue = transactions
        .filter((t: any) => t.status === "completed")
        .reduce((sum: number, t: any) => sum + (t.currency === "DT" ? t.amount : 0), 0);
      
      setStats({
        total_users: users.length,
        total_teachers: teachers.length,
        total_students: students.length,
        total_courses: courses.length,
        total_transactions: transactions.length,
        total_tokens_sold: 0,
        total_dt_revenue: totalRevenue,
        total_tokens_consumed: 0,
        pending_courses: pendingCourses.length,
        pending_teachers: 0,
      });
      
    } catch (err) {
      console.error(err);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('fr-TN', { 
      style: 'currency', 
      currency: 'TND',
      minimumFractionDigits: 0 
    }).format(amount);
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('fr-TN').format(num);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-navy to-navy/90 rounded-3xl p-8 text-white">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-[300]">
              Welcome back, <span className="text-orange">{user?.full_name?.split(" ")[0] || "Admin"}</span>
            </h1>
            <p className="text-white/60 mt-2">Here's what's happening on your platform today.</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-end">
              <div className="text-sm text-white/60">Today's Date</div>
              <div className="font-medium">
                {new Date().toLocaleDateString("fr-FR", { weekday: "long", day: "numeric", month: "long" })}
              </div>
            </div>
            <div className="w-12 h-12 rounded-2xl bg-white/10 flex items-center justify-center">
              <DollarSign className="w-6 h-6 text-orange" />
            </div>
          </div>
        </div>
      </div>

      {/* Top Stats Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-green-100 rounded-xl">
              <DollarSign className="w-6 h-6 text-green-600" />
            </div>
          </div>
          <div className="text-3xl font-[300] text-navy">
            {stats ? formatCurrency(stats.total_dt_revenue || 0) : "0 DT"}
          </div>
          <div className="text-sm text-gray mt-1">Total Revenue (DT)</div>
        </div>

        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-purple-100 rounded-xl">
              <Coins className="w-6 h-6 text-purple-600" />
            </div>
          </div>
          <div className="text-3xl font-[300] text-navy">
            {stats ? formatNumber(stats.total_tokens_sold || 0) : "0"}
          </div>
          <div className="text-sm text-gray mt-1">Tokens Sold</div>
        </div>

        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-blue-100 rounded-xl">
              <Users className="w-6 h-6 text-blue-600" />
            </div>
          </div>
          <div className="text-3xl font-[300] text-navy">
            {stats ? formatNumber(stats.total_users || 0) : "0"}
          </div>
          <div className="text-sm text-gray mt-1">Active Users</div>
        </div>

        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-yellow-100 rounded-xl">
              <Clock className="w-6 h-6 text-yellow-600" />
            </div>
          </div>
          <div className="text-3xl font-[300] text-navy">
            {stats ? stats.pending_courses || 0 : "0"}
          </div>
          <div className="text-sm text-gray mt-1">Pending Content</div>
        </div>
      </div>

      {/* User Distribution */}
      <div className="grid lg:grid-cols-3 gap-6">
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <h3 className="font-semibold text-navy mb-4">User Distribution</h3>
          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between text-sm mb-2">
                <span className="flex items-center gap-2">
                  <GraduationCap className="w-4 h-4 text-blue-500" />
                  Students
                </span>
                <span className="font-medium">
                  {stats ? stats.total_students || 0 : 0}
                </span>
              </div>
              <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-blue-500 rounded-full" 
                  style={{ width: stats ? `${(stats.total_students / (stats.total_users || 1)) * 100}%` : "0%" }} 
                />
              </div>
            </div>
            <div>
              <div className="flex items-center justify-between text-sm mb-2">
                <span className="flex items-center gap-2">
                  <Users className="w-4 h-4 text-green-500" />
                  Teachers
                </span>
                <span className="font-medium">
                  {stats ? stats.total_teachers || 0 : 0}
                </span>
              </div>
              <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-green-500 rounded-full" 
                  style={{ width: stats ? `${(stats.total_teachers / (stats.total_users || 1)) * 100}%` : "0%" }} 
                />
              </div>
            </div>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <h3 className="font-semibold text-navy mb-4">Quick Stats</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-cream-m rounded-xl">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <BookOpen className="w-4 h-4 text-blue-600" />
                </div>
                <span className="text-sm">Total Courses</span>
              </div>
              <span className="font-semibold text-navy">
                {stats ? stats.total_courses || 0 : 0}
              </span>
            </div>
            <div className="flex items-center justify-between p-3 bg-cream-m rounded-xl">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-orange-100 rounded-lg">
                  <ShoppingCart className="w-4 h-4 text-orange" />
                </div>
                <span className="text-sm">Transactions</span>
              </div>
              <span className="font-semibold text-navy">
                {stats ? stats.total_transactions || 0 : 0}
              </span>
            </div>
            <div className="flex items-center justify-between p-3 bg-cream-m rounded-xl">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <Coins className="w-4 h-4 text-purple-600" />
                </div>
                <span className="text-sm">Tokens Consumed</span>
              </div>
              <span className="font-semibold text-navy">
                {stats ? formatNumber(stats.total_tokens_consumed || 0) : 0}
              </span>
            </div>
          </div>
        </div>

        {/* Activity */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <h3 className="font-semibold text-navy mb-4">Platform Activity</h3>
          <div className="text-center py-8 text-gray">
            <Activity className="w-12 h-12 mx-auto mb-2 opacity-30" />
            <p className="text-sm">Activity feed will appear here</p>
          </div>
        </div>
      </div>
    </div>
  );
}

function Activity(props: any) {
  return (
    <svg {...props} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
    </svg>
  );
}