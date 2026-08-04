import { useState } from "react";
import { Outlet, NavLink, useNavigate } from "react-router-dom";
import { useAuthStore } from "../../../store/authStore";

const NAV_ITEMS = [
  { to: "/dashboard/admin", label: "Overview", icon: "M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1h3a1 1 0 001-1V10", end: true },
  { to: "/dashboard/admin/courses", label: "Course Builder", icon: "M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253M13 18.747l2-2m0 0c1.666-1.669 3.716-1.668 5.396 0l2.214 2.214c1.665 1.668 1.665 4.22 0 5.876l-2.214 2.214c-.56.56-1.292.84-2.088.84H9.708c-.796 0-1.528-.28-2.088-.84l-2.214-2.214c-1.666-1.656-1.666-4.208 0-5.876l2.214-2.214z" },
  { to: "/dashboard/admin/finance", label: "Finance Center", icon: "M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.1 0 2 .9 2 2s-.9 2-2 2-2 .9-2 2 .9 2 2 2m0-5.5c1.381 0 2.5 1.043 2.5 2.333v3.334c0 1.29-1.119 2.333-2.5 2.333s-2.5-1.043-2.5-2.333v-3.334C6.5 6.543 7.619 5.5 9 5.5" },
  { to: "/dashboard/admin/users", label: "Users & Economy", icon: "M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" },
  { to: "/dashboard/admin/content", label: "Content", icon: "M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253M13 18.747l2-2m0 0c1.666-1.669 3.716-1.668 5.396 0l2.214 2.214c1.665 1.668 1.665 4.22 0 5.876l-2.214 2.214c-.56.56-1.292.84-2.088.84H9.708c-.796 0-1.528-.28-2.088-.84l-2.214-2.214c-1.666-1.656-1.666-4.208 0-5.876l2.214-2.214z" },
  { to: "/dashboard/admin/communication", label: "Communication", icon: "M8 9l3 3-3 3m5 0h3M9 19V5m0 14l4-4 4 4-4-4z" },
  { to: "/dashboard/admin/settings", label: "Settings", icon: "M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" },
];

export default function AdminDashboardContainer() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="min-h-screen flex bg-cream">
      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 w-72 bg-navy transform transition-transform duration-300 z-50 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        } lg:relative lg:translate-x-0`}
      >
        {/* Logo */}
        <div className="p-6 border-b border-white/10">
          <h1 className="text-xl font-[300] text-white">
            EDU<span className="italic text-orange-l">AI</span>
          </h1>
          <p className="text-white/40 text-xs mt-1">Admin Panel</p>
        </div>

        {/* Navigation */}
        <nav className="p-4 space-y-1">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                  isActive
                    ? "bg-gradient-to-r from-orange to-orange-l text-white"
                    : "text-white/50 hover:bg-white/5 hover:text-white"
                }`
              }
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d={item.icon} />
              </svg>
              {item.label}
            </NavLink>
          ))}
        </nav>

        {/* Logout */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-white/10">
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-white/50 hover:bg-red-600/20 hover:text-red-400 transition-all"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            Déconnexion
          </button>
        </div>
      </aside>

      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main content */}
      <div className="flex-1 flex flex-col min-h-screen">
        {/* Header */}
        <header className="bg-white/80 backdrop-blur-sm border-b border-black/5 p-4 flex items-center justify-between sticky top-0 z-30">
          <button
            className="lg:hidden p-2 text-navy"
            onClick={() => setSidebarOpen(true)}
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          
          <div className="flex items-center gap-4 ms-auto">
            <div className="text-end">
              <div className="text-sm font-medium text-navy">{user?.full_name}</div>
              <div className="text-xs text-orange font-medium">Administrator</div>
            </div>
            <div className="w-10 h-10 rounded-full bg-gradient-to-r from-orange to-orange-l flex items-center justify-center text-white font-semibold">
              {user?.full_name?.charAt(0) || "A"}
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 p-6 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}