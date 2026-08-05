import { useState, useEffect } from "react";
import { useAuthStore } from "../../../store/authStore";
import { 
  Building2,
  Users,
  BookOpen,
  GraduationCap,
  CheckCircle,
  Clock,
  TrendingUp,
  Wallet,
  Loader2
} from "lucide-react";
import { adminSchoolDashboard } from "../../../api";

interface SchoolStats {
  total_users: number;
  total_teachers: number;
  total_students: number;
  total_courses: number;
  pending_courses: number;
  published_courses: number;
  pending_teacher_registrations: number;
}

export default function SchoolOverview() {
  const { token, user } = useAuthStore();
  const [stats, setStats] = useState<SchoolStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      fetchStats();
    }
  }, [token]);

  const fetchStats = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const data = await adminSchoolDashboard.get();
      setStats(data);
    } catch (err) {
      console.error("fetchStats error:", err);
    }
    setLoading(false);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 animate-spin text-orange" />
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-navy">
          {user?.school_name || "Mon Ecole"}
        </h1>
        <p className="text-gray">Vue d'ensemble de votre établissement</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          icon={<Users className="w-6 h-6" />}
          label="Total Utilisateurs"
          value={stats?.total_users || 0}
          color="blue"
        />
        <StatCard
          icon={<GraduationCap className="w-6 h-6" />}
          label="Elèves"
          value={stats?.total_students || 0}
          color="yellow"
        />
        <StatCard
          icon={<BookOpen className="w-6 h-6" />}
          label="Enseignants"
          value={stats?.total_teachers || 0}
          color="green"
        />
        <StatCard
          icon={<TrendingUp className="w-6 h-6" />}
          label="Cours"
          value={stats?.total_courses || 0}
          color="purple"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-2xl p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-navy mb-4">Cours</h2>
          <div className="space-y-3">
            <div className="flex justify-between items-center p-3 bg-cream-m rounded-xl">
              <span className="text-gray">Publiés</span>
              <span className="font-semibold text-green-600">{stats?.published_courses || 0}</span>
            </div>
            <div className="flex justify-between items-center p-3 bg-cream-m rounded-xl">
              <span className="text-gray">En attente</span>
              <span className="font-semibold text-yellow-600">{stats?.pending_courses || 0}</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-navy mb-4">Demandes</h2>
          <div className="space-y-3">
            <div className="flex justify-between items-center p-3 bg-cream-m rounded-xl">
              <span className="text-gray">Enseignants en attente</span>
              <span className="font-semibold text-orange-600">{stats?.pending_teacher_registrations || 0}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-6 bg-white rounded-2xl p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-navy mb-4">Informations de l'école</h2>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-gray">Nom</p>
            <p className="font-medium">{user?.school_name || "Non défini"}</p>
          </div>
          <div>
            <p className="text-sm text-gray">ID</p>
            <p className="font-medium">{user?.school_id || "N/A"}</p>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ icon, label, value, color }: { icon: React.ReactNode; label: string; value: number; color: string }) {
  const colors: Record<string, string> = {
    blue: "bg-blue-50 text-blue-600",
    yellow: "bg-yellow-50 text-yellow-600",
    green: "bg-green-50 text-green-600",
    purple: "bg-purple-50 text-purple-600",
  };
  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm">
      <div className={`w-12 h-12 rounded-xl ${colors[color]} flex items-center justify-center mb-4`}>
        {icon}
      </div>
      <p className="text-2xl font-bold text-navy">{value}</p>
      <p className="text-sm text-gray">{label}</p>
    </div>
  );
}