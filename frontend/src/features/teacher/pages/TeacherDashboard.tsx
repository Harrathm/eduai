import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../../../store/authStore";
import { BookOpen, Users, Wallet, ArrowRight } from "lucide-react";
import { TeacherStateBadge } from "../../../components/TeacherStateGuard";

const API_URL = "";

interface DashboardStats {
  coursesCount: number;
  classesCount: number;
  totalStudents: number;
  walletBalance: number;
}

interface RecentClass {
  id: number;
  name: string;
  students_count: number;
  courses_count: number;
}

export default function TeacherDashboard() {
  const { user, token } = useAuthStore();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [stats, setStats] = useState<DashboardStats>({
    coursesCount: 0,
    classesCount: 0,
    totalStudents: 0,
    walletBalance: 0,
  });
  const [recentClasses, setRecentClasses] = useState<RecentClass[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) fetchDashboard();
  }, [token]);

  const fetchDashboard = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const [coursesRes, classesRes, walletRes] = await Promise.all([
        fetch(`${API_URL}/api/courses/my-courses`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        fetch(`${API_URL}/api/teacher/classes`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        fetch(`${API_URL}/api/wallet/balance`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
      ]);

      if (coursesRes.ok) {
        const data = await coursesRes.json();
        setStats((s) => ({ ...s, coursesCount: data.total || 0 }));
      }

      if (classesRes.ok) {
        const classes = await classesRes.json();
        setRecentClasses(classes.slice(0, 3));
        setStats((s) => ({
          ...s,
          classesCount: classes.length,
          totalStudents: classes.reduce(
            (sum: number, c: RecentClass) => sum + (c.students_count || 0),
            0
          ),
        }));
      }

      if (walletRes.ok) {
        const data = await walletRes.json();
        setStats((s) => ({ ...s, walletBalance: data.total || 0 }));
      }
    } catch (err) {
      console.error("Dashboard fetch error:", err);
    }
    setLoading(false);
  };

  const quickActions = [
    {
      to: "/dashboard/teacher/classroom",
      label: t('teacher.dashboard.myClasses'),
      icon: "👥",
      gradient: "from-orange-p to-cream",
    },
    {
      to: "/dashboard/teacher/ai-studio",
      label: t('teacher.dashboard.aiStudio'),
      icon: "🎨",
      gradient: "from-purple-50 to-cream",
    },
    {
      to: "/dashboard/teacher/sales",
      label: t('teacher.dashboard.revenue'),
      icon: "💰",
      gradient: "from-green-50 to-cream",
    },
    {
      to: "/dashboard/teacher/wallet",
      label: t('teacher.dashboard.wallet'),
      icon: "💳",
      gradient: "from-blue-50 to-cream",
    },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="bg-navy rounded-3xl p-8">
        <h1 className="text-4xl font-[300] text-white">
          {t('teacher.dashboard.title')} <span className="italic text-orange-l">{t('teacher.dashboard.titleSuffix')}</span>
        </h1>
        <p className="text-white/50 mt-2 flex items-center gap-2">
          {t('teacher.dashboard.welcome')}{user?.full_name}
          <TeacherStateBadge />
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-orange/10 rounded-xl flex items-center justify-center">
              <BookOpen className="w-5 h-5 text-orange" />
            </div>
          </div>
          <div className="text-3xl font-[300] text-navy">
            {loading ? "..." : stats.coursesCount}
          </div>
          <div className="text-sm text-gray mt-1">{t('teacher.dashboard.myCourses')}</div>
        </div>

        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center">
              <Users className="w-5 h-5 text-blue-600" />
            </div>
          </div>
          <div className="text-3xl font-[300] text-navy">
            {loading ? "..." : stats.classesCount}
          </div>
          <div className="text-sm text-gray mt-1">{t('teacher.dashboard.myClasses')}</div>
        </div>

        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-green-100 rounded-xl flex items-center justify-center">
              <Users className="w-5 h-5 text-green-600" />
            </div>
          </div>
          <div className="text-3xl font-[300] text-navy">
            {loading ? "..." : stats.totalStudents}
          </div>
          <div className="text-sm text-gray mt-1">{t('teacher.dashboard.students')}</div>
        </div>

        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-yellow-100 rounded-xl flex items-center justify-center">
              <Wallet className="w-5 h-5 text-yellow-600" />
            </div>
          </div>
          <div className="text-3xl font-[300] text-navy">
            {loading ? "..." : stats.walletBalance}
          </div>
          <div className="text-sm text-gray mt-1">{t('teacher.dashboard.aiCredits')}</div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-3xl p-8 shadow-sm border border-black/5">
        <h2 className="text-2xl font-[300] text-navy mb-6">{t('teacher.dashboard.quickAccess')}</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {quickActions.map((action) => (
            <button
              key={action.to}
              onClick={() => navigate(action.to)}
              className={`block p-6 bg-gradient-to-br ${action.gradient} rounded-2xl text-center hover:shadow-md transition-shadow cursor-pointer`}
            >
              <div className="text-3xl mb-2">{action.icon}</div>
              <div className="font-medium text-navy">{action.label}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Recent Classes */}
      {recentClasses.length > 0 && (
        <div className="bg-white rounded-3xl p-8 shadow-sm border border-black/5">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-[300] text-navy">{t('teacher.dashboard.myClasses')}</h2>
            <button
              onClick={() => navigate("/dashboard/teacher/classroom")}
              className="flex items-center gap-1 text-sm text-orange font-medium hover:underline"
            >
              {t('teacher.dashboard.viewAll')} <ArrowRight className="w-4 h-4" />
            </button>
          </div>
          <div className="grid gap-4 md:grid-cols-3">
            {recentClasses.map((cls) => (
              <div
                key={cls.id}
                onClick={() => navigate("/dashboard/teacher/classroom")}
                className="p-4 bg-cream-m rounded-xl hover:bg-cream transition-colors cursor-pointer"
              >
                <div className="font-medium text-navy">{cls.name}</div>
                <div className="text-sm text-gray mt-1">
                  {cls.students_count} {t('teacher.dashboard.eleves')} · {cls.courses_count} {t('teacher.dashboard.cours')}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
