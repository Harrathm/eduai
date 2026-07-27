import { useState } from "react";
import { Outlet, useNavigate, NavLink } from "react-router-dom";
import { useAuthStore } from "../../store/authStore";
import WalletWidget from "../WalletWidget";
import LanguageSelector from "../LanguageSelector";

const ADMIN_NAV = [
  { to: "/dashboard/admin", label: "Dashboard", icon: "M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1h3a1 1 0 001-1V10", end: true },
];

const TEACHER_NAV = [
  { to: "/dashboard", label: "Dashboard", icon: "M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1h3a1 1 0 001-1V10", end: true },
  { to: "/dashboard/teacher/learning", label: "My Learning", icon: "M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253M13 18.747l2-2m0 0c1.666-1.669 3.716-1.668 5.396 0l2.214 2.214c1.665 1.668 1.665 4.22 0 5.876l-2.214 2.214c-.56.56-1.292.84-2.088.84H9.708c-.796 0-1.528-.28-2.088-.84l-2.214-2.214c-1.666-1.656-1.666-4.208 0-5.876l2.214-2.214z" },
  { to: "/dashboard/teacher/classroom", label: "Classroom", icon: "M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" },
  { to: "/dashboard/ai-tutor", label: "Tuteur IA", icon: "M8 9l3 3-3 3m5 0h3M9 19V5m0 14l4-4 4 4-4-4z" },
  { to: "/dashboard/teacher/ai-studio", label: "AI Studio", icon: "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" },
  { to: "/dashboard/teacher/wallet", label: "Wallet", icon: "M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" },
  { to: "/dashboard/teacher/sales", label: "Revenus", icon: "M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" },
];

const STUDENT_NAV = [
  { to: "/dashboard", label: "Mon Apprentissage", icon: "M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253M13 18.747l2-2m0 0c1.666-1.669 3.716-1.668 5.396 0l2.214 2.214c1.665 1.668 1.665 4.22 0 5.876l-2.214 2.214c-.56.56-1.292.84-2.088.84H9.708c-.796 0-1.528-.28-2.088-.84l-2.214-2.214c-1.666-1.656-1.666-4.208 0-5.876l2.214-2.214z", end: true },
  { to: "/dashboard/courses", label: "Catalogue", icon: "M3 15a4 4 0 004 4h9a5 5 0 10-.207-1.99 4.993 4.993 0 00-2.525 1.92l-.321.965a1.5 1.5 0 01-1.424 0l-.715-.955A4.973 4.973 0 0010 18V6a3 3 0 00-3-3H6a3 3 0 00-3 3v12z" },
  { to: "/dashboard/assignments", label: "Devoirs", icon: "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" },
  { to: "/dashboard/ai-tutor", label: "Tuteur IA", icon: "M8 9l3 3-3 3m5 0h3M9 19V5m0 14l4-4 4 4-4-4z" },
  { to: "/dashboard/wallet", label: "Portefeuille", icon: "M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" },
];

const getNavItems = (role?: string) => {
  if (!role) return STUDENT_NAV;
  const r = role.toUpperCase();
  if (r === "SUPER_ADMIN" || r === "ADMIN_SCHOOL" || r === "PEDAGOGICAL_ADMIN" || r === "PEDAGOGICAL_LEAD") return ADMIN_NAV;
  if (r === "TEACHER") return TEACHER_NAV;
  return STUDENT_NAV;
};

export default function DashboardLayout() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const navItems = getNavItems(user?.role);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="min-h-screen flex bg-cream">
      <aside
        className={`fixed inset-y-0 left-0 w-72 bg-navy transform transition-transform duration-300 z-50 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        } lg:relative lg:translate-x-0`}
      >
        <div className="p-8 border-b border-white/10">
          <h1 className="text-2xl font-[300] text-white">
            EDU<span className="italic text-orange-l">AI</span>
          </h1>
          <p className="text-white/40 text-xs mt-1 capitalize">{user?.role}</p>
        </div>

        <nav className="p-4 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-4 px-5 py-3 rounded-xl text-sm font-medium transition-all ${
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

        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-white/10">
          <div className="mb-3">
            <WalletWidget compact />
          </div>
          <div className="mb-3">
            <LanguageSelector />
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-4 w-full px-5 py-3 rounded-xl text-sm font-medium text-white/50 hover:bg-white/5 hover:text-white transition-all"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            Déconnexion
          </button>
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-h-screen">
        <header className="bg-white border-b border-black/5 px-8 py-4 flex items-center justify-between lg:hidden">
          <button onClick={() => setSidebarOpen(true)} className="p-2">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          <h1 className="text-lg font-[300] text-navy">
            EDU<span className="italic text-orange-l">AI</span>
          </h1>
        </header>
        <main className="flex-1 p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}