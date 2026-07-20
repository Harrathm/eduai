import { useState, useEffect } from "react";
import { Outlet, NavLink, useNavigate } from "react-router-dom";
import { useAuthStore } from "../../../store/authStore";
import { 
  Building2,
  Users,
  TrendingUp,
  Settings,
  LogOut
} from "lucide-react";

function SchoolAdminDashboard() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="min-h-screen flex bg-cream">
      <aside className={`fixed inset-y-0 left-0 w-72 bg-navy transform transition-transform duration-300 z-50 ${sidebarOpen ? "translate-x-0" : "-translate-x-full"} lg:relative lg:translate-x-0`}>
        <div className="p-6 border-b border-white/10">
          <h1 className="text-xl font-[300] text-white">
            {user?.school_name || "EDUAI"}
          </h1>
          <p className="text-white/40 text-xs mt-1">Admin École</p>
        </div>
        <nav className="p-4 space-y-1">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                  isActive
                    ? "bg-orange text-white"
                    : "text-white/60 hover:text-white hover:bg-white/5"
                }`
              }
            >
              <item.icon className="w-5 h-5" />
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="absolute bottom-0 w-72 p-4 border-t border-white/10">
          <button onClick={handleLogout} className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-white/60 hover:text-white hover:bg-white/5 w-full">
            <LogOut className="w-5 h-5" />
            Déconnexion
          </button>
        </div>
      </aside>
      <main className="flex-1 p-8 lg:ml-0">
        <button onClick={() => setSidebarOpen(!sidebarOpen)} className="lg:hidden fixed top-4 left-4 z-50 p-2 bg-white rounded-lg shadow-lg">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        <Outlet />
      </main>
    </div>
  );
}

const NAV_ITEMS = [
  { to: "/dashboard/school", label: "Mon Ecole", icon: Building2, end: true },
  { to: "/dashboard/school/users", label: "Utilisateurs", icon: Users },
  { to: "/dashboard/school/finance", label: "Finance", icon: TrendingUp },
  { to: "/dashboard/school/settings", label: "Paramètres", icon: Settings },
];

export default SchoolAdminDashboard;