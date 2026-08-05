import { useState, useEffect } from "react";
import { useAuthStore } from "../../../store/authStore";
import { adminDashboard, userApi, courseAdmin } from "../../../api";

interface Stats {
  total_users: number;
  total_teachers: number;
  total_students: number;
  total_courses: number;
  pending_courses: number;
  published_courses: number;
  total_tokens_sold: number;
  total_dt_revenue: number;
  pending_teacher_registrations: number;
}

interface User {
  id: number;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  is_approved: boolean;
}

interface Course {
  id: number;
  title: string;
  description: string;
  status: string;
  price_tokens: number;
  price_dt: number;
  teacher_name: string;
}

type Tab = "overview" | "users" | "courses" | "transactions";

export default function AdminDashboard() {
  const { user, token } = useAuthStore();
  const [activeTab, setActiveTab] = useState<Tab>("overview");
  const [stats, setStats] = useState<Stats | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchStats = async () => {
    setLoading(true);
    try {
      setStats(await adminDashboard.stats());
    } catch (err) { console.error(err); }
    setLoading(false);
  };

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const data = await userApi.list();
      setUsers(data.items || []);
    } catch (err) { console.error(err); }
    setLoading(false);
  };

  const fetchCourses = async () => {
    setLoading(true);
    try {
      const data = await courseAdmin.list();
      setCourses(data.items || []);
    } catch (err) { console.error(err); }
    setLoading(false);
  };

  useEffect(() => {
    if (!token) return;
    if (activeTab === "overview") fetchStats();
    if (activeTab === "users") fetchUsers();
    if (activeTab === "courses") fetchCourses();
  }, [activeTab, token]);

  const approveUser = async (userId: number) => {
    try {
      await userApi.approve(userId);
      fetchUsers();
    } catch (err) { console.error(err); }
  };

  const updateCourseStatus = async (courseId: number, status: string) => {
    try {
      if (status === "published") {
        await courseAdmin.publish(courseId);
      } else if (status === "rejected") {
        await courseAdmin.update(courseId, { status: "rejected" });
      }
      fetchCourses();
    } catch (err) { console.error(err); }
  };

  const tabs = [
    { id: "overview", label: "Overview" },
    { id: "users", label: "Utilisateurs" },
    { id: "courses", label: "Cours" },
    { id: "transactions", label: "Transactions" },
  ];

  const statCards = [
    { label: "Utilisateurs", value: stats?.total_users || 0, color: "blue" },
    { label: "Enseignants", value: stats?.total_teachers || 0, color: "green" },
    { label: "Étudiants", value: stats?.total_students || 0, color: "yellow" },
    { label: "Cours", value: stats?.total_courses || 0, color: "purple" },
    { label: "En attente", value: stats?.pending_courses || 0, color: "orange" },
    { label: "Publiés", value: stats?.published_courses || 0, color: "emerald" },
    { label: "Tokens Vendus", value: stats?.total_tokens_sold || 0, color: "cyan" },
    { label: "Revenus DT", value: stats?.total_dt_revenue || 0, color: "pink" },
  ];

  const colorMap: Record<string, string> = {
    blue: "bg-blue-100 text-blue-700",
    green: "bg-green-100 text-green-700",
    yellow: "bg-yellow-100 text-yellow-700",
    purple: "bg-purple-100 text-purple-700",
    orange: "bg-orange-100 text-orange-700",
    emerald: "bg-emerald-100 text-emerald-700",
    cyan: "bg-cyan-100 text-cyan-700",
    pink: "bg-pink-100 text-pink-700",
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="bg-white rounded-3xl p-8 shadow-sm border border-black/5">
        <h1 className="text-4xl font-[300] text-navy">
          Dashboard <span className="italic text-orange">Admin</span>
        </h1>
        <p className="text-gray mt-2">Bienvenue, {user?.full_name}</p>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-3xl shadow-sm border border-black/5 overflow-hidden">
        <div className="flex overflow-x-auto border-b border-black/5">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as Tab)}
              className={`px-8 py-5 text-sm font-semibold whitespace-nowrap transition-colors ${
                activeTab === tab.id
                  ? "text-orange border-b-2 border-orange"
                  : "text-gray hover:text-navy"
              }`}
            >
              {tab.label}
              {tab.id === "overview" && stats?.pending_courses ? (
                <span className="ml-2 bg-orange text-white text-xs px-2 py-0.5 rounded-full">
                  {stats.pending_courses}
                </span>
              ) : null}
            </button>
          ))}
        </div>

        <div className="p-8">
          {/* OVERVIEW */}
          {activeTab === "overview" && (
            <div className="space-y-6">
              {loading ? (
                <div className="text-center py-12 text-gray">Chargement...</div>
              ) : (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {statCards.map((stat, i) => (
                    <div key={i} className={`${colorMap[stat.color]} rounded-2xl p-6`}>
                      <div className="text-4xl font-[300]">{stat.value}</div>
                      <div className="text-sm mt-1 opacity-80">{stat.label}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* USERS */}
          {activeTab === "users" && (
            <div className="space-y-4">
              <h3 className="text-xl font-[300] text-navy mb-6">Tous les utilisateurs</h3>
              {loading ? (
                <div className="text-center py-12 text-gray">Chargement...</div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-cream-m">
                      <tr>
                        <th className="text-start px-5 py-3 text-xs font-semibold text-gray uppercase">Nom</th>
                        <th className="text-start px-5 py-3 text-xs font-semibold text-gray uppercase">Email</th>
                        <th className="text-start px-5 py-3 text-xs font-semibold text-gray uppercase">Rôle</th>
                        <th className="text-start px-5 py-3 text-xs font-semibold text-gray uppercase">Status</th>
                        <th className="text-start px-5 py-3 text-xs font-semibold text-gray uppercase">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-black/5">
                      {users.map((u) => (
                        <tr key={u.id} className="hover:bg-cream/50">
                          <td className="px-5 py-4 font-medium">{u.full_name}</td>
                          <td className="px-5 py-4 text-gray">{u.email}</td>
                          <td className="px-5 py-4">
                            <span className={`px-3 py-1 text-xs rounded-full ${
                              u.role === "admin_school" ? "bg-purple-100 text-purple-700" :
                              u.role === "pedagogical_admin" ? "bg-blue-100 text-blue-700" :
                              u.role === "pedagogical_lead" ? "bg-teal-100 text-teal-700" :
                              u.role === "teacher" ? "bg-green-100 text-green-700" :
                              "bg-blue-100 text-blue-700"
                            }`}>
                              {u.role}
                            </span>
                          </td>
                          <td className="px-5 py-4">
                            <span className={`px-3 py-1 text-xs rounded-full ${
                              u.is_active ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
                            }`}>
                              {u.is_active ? "Actif" : "Inactif"}
                            </span>
                          </td>
                          <td className="px-5 py-4">
                            {u.role === "teacher" && !u.is_approved && (
                              <button
                                onClick={() => approveUser(u.id)}
                                className="text-orange hover:underline text-sm font-medium"
                              >
                                Approuver
                              </button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* COURSES */}
          {activeTab === "courses" && (
            <div className="space-y-4">
              <h3 className="text-xl font-[300] text-navy mb-6">Tous les cours</h3>
              {loading ? (
                <div className="text-center py-12 text-gray">Chargement...</div>
              ) : (
                <div className="grid gap-4">
                  {courses.map((c) => (
                    <div key={c.id} className="border border-black/5 rounded-2xl p-6 hover:shadow-md transition-shadow">
                      <div className="flex justify-between items-start">
                        <div>
                          <h4 className="text-lg font-semibold text-navy">{c.title}</h4>
                          <p className="text-sm text-gray mt-1">{c.description}</p>
                          <p className="text-xs text-gray mt-2">Enseignant: {c.teacher_name}</p>
                        </div>
                        <div className="text-end">
                          <span className={`px-3 py-1 text-xs rounded-full ${
                            c.status === "published" ? "bg-green-100 text-green-700" :
                            c.status === "pending" ? "bg-yellow-100 text-yellow-700" :
                            "bg-red-100 text-red-700"
                          }`}>
                            {c.status}
                          </span>
                          <p className="text-sm mt-2">{c.price_tokens} tokens / {c.price_dt} DT</p>
                        </div>
                      </div>
                      {c.status === "pending" && (
                        <div className="mt-4 flex gap-3">
                          <button
                            onClick={() => updateCourseStatus(c.id, "published")}
                            className="px-5 py-2 bg-gradient-to-r from-green-500 to-green-600 text-white rounded-xl text-sm font-medium hover:opacity-90"
                          >
                            Approuver
                          </button>
                          <button
                            onClick={() => updateCourseStatus(c.id, "rejected")}
                            className="px-5 py-2 bg-gradient-to-r from-red-500 to-red-600 text-white rounded-xl text-sm font-medium hover:opacity-90"
                          >
                            Rejeter
                          </button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TRANSACTIONS */}
          {activeTab === "transactions" && (
            <div className="space-y-6">
              <h3 className="text-xl font-[300] text-navy mb-6">Aperçu financier</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-gradient-to-br from-green-100 to-green-50 rounded-2xl p-6">
                  <div className="text-3xl font-[300] text-green-700">
                    {stats?.total_tokens_sold || 0}
                  </div>
                  <div className="text-sm text-green-600 mt-1">Tokens Vendus</div>
                </div>
                <div className="bg-gradient-to-br from-yellow-100 to-yellow-50 rounded-2xl p-6">
                  <div className="text-3xl font-[300] text-yellow-700">
                    {stats?.total_dt_revenue || 0}
                  </div>
                  <div className="text-sm text-yellow-600 mt-1">Revenus DT</div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}