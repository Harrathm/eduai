import { useState, useRef, useEffect, useMemo } from "react";
import { Outlet, useNavigate, NavLink } from "react-router-dom";
import { useTranslation } from "react-i18next";
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
  { to: "/dashboard/teacher/abonnements", label: "Abonnements", icon: "M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" },
  { to: "/dashboard/teacher/reorientations", label: "Réorientations", icon: "M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" },
  { to: "/dashboard/teacher/validation-contenu", label: "Validation Contenu", icon: "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" },
  { to: "/dashboard/teacher/parcours", label: "Mes Parcours", icon: "M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" },
  { to: "/dashboard/teacher/elements", label: "Éléments", icon: "M11 4a2 2 0 114 0v1a1 1 0 001 1h3a1 1 0 011 1v3a1 1 0 01-1 1h-1a2 2 0 100 4h1a1 1 0 011 1v3a1 1 0 01-1 1h-3a1 1 0 01-1-1v-1a2 2 0 10-4 0v1a1 1 0 01-1 1H7a1 1 0 01-1-1v-3a1 1 0 00-1-1H4a2 2 0 110-4h1a1 1 0 001-1V7a1 1 0 011-1h3a1 1 0 001-1V4z" },
  { to: "/dashboard/teacher/bibliotheque", label: "Bibliothèque", icon: "M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253M13 18.747l2-2m0 0c1.666-1.669 3.716-1.668 5.396 0l2.214 2.214c1.665 1.668 1.665 4.22 0 5.876l-2.214 2.214c-.56.56-1.292.84-2.088.84H9.708c-.796 0-1.528-.28-2.088-.84l-2.214-2.214c-1.666-1.656-1.666-4.208 0-5.876l2.214-2.214z" },
  { to: "/dashboard/profile", label: "Profil", icon: "M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" },
];

interface NavItem {
  to: string;
  label: string;
  icon: string;
  end?: boolean;
}

const getStudentNav = (t: (key: string) => string): NavItem[] => [
  { to: "/dashboard", label: t("student.sidebar.dashboard"), icon: "M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1h3a1 1 0 001-1V10", end: true },
  { to: "/dashboard/mon-parcours", label: t("student.sidebar.pathway"), icon: "M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" },
  { to: "/dashboard/ai-tutor", label: t("student.sidebar.aiAssistant"), icon: "M8 9l3 3-3 3m5 0h3M9 19V5m0 14l4-4 4 4-4-4z" },
  { to: "/dashboard/courses", label: t("student.sidebar.courseCatalog"), icon: "M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253M13 18.747l2-2m0 0c1.666-1.669 3.716-1.668 5.396 0l2.214 2.214c1.665 1.668 1.665 4.22 0 5.876l-2.214 2.214c-.56.56-1.292.84-2.088.84H9.708c-.796 0-1.528-.28-2.088-.84l-2.214-2.214c-1.666-1.656-1.666-4.208 0-5.876l2.214-2.214z" },
  { to: "/dashboard/soft-skills", label: t("student.sidebar.softSkills"), icon: "M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" },
  { to: "/dashboard/my-skills", label: t("student.sidebar.myTrainings"), icon: "M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" },
  { to: "/dashboard/packs", label: t("student.sidebar.packs"), icon: "M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" },
  { to: "/dashboard/settings/subscription", label: t("student.sidebar.subscription"), icon: "M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" },
  { to: "/dashboard/wallet", label: t("student.sidebar.wallet"), icon: "M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" },
  { to: "/dashboard/inbox", label: t("student.sidebar.messages"), icon: "M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" },
  { to: "/dashboard/profile", label: t("student.sidebar.profile"), icon: "M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" },
];

const PARENT_NAV = [
  { to: "/dashboard/parent", label: "Tableau de bord", icon: "M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1h3a1 1 0 001-1V10", end: true },
  { to: "/dashboard/parent/famille", label: "Ma Famille", icon: "M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" },
  { to: "/dashboard/soft-skills", label: "Soft Skills", icon: "M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" },
  { to: "/dashboard/profile", label: "Profil", icon: "M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" },
];

const getNavItems = (role?: string) => {
  const r = role?.toUpperCase();
  if (r === "SUPER_ADMIN" || r === "ADMIN_SCHOOL" || r === "PEDAGOGICAL_ADMIN" || r === "PEDAGOGICAL_LEAD") return ADMIN_NAV;
  if (r === "TEACHER") return TEACHER_NAV;
  if (r === "PARENT") return PARENT_NAV;
  return null;
};

const ROLE_LABELS: Record<string, string> = {
  super_admin: "Super Admin",
  admin_school: "Admin École",
  pedagogical_admin: "Admin Pédagogique",
  pedagogical_lead: "Responsable Pédagogique",
  teacher: "Enseignant",
  student: "Élève",
  parent: "Parent",
};

export default function DashboardLayout() {
  const { t } = useTranslation();
  const { user, logout, switchRole, stopImpersonation } = useAuthStore();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [roleDropdownOpen, setRoleDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  
  // Use activeRole for navigation, fallback to role
  const activeRole = user?.activeRole || user?.role;
  const navItems = getNavItems(activeRole);
  const isStudent = activeRole?.toUpperCase() === "STUDENT";
  const hasMultipleRoles = user?.roles && user.roles.length > 1;
  const isImpersonating = !!user?.impersonated_by;

  const studentNav = useMemo(() => getStudentNav(t), [t]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setRoleDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const handleSwitchRole = async (role: string) => {
    if (role === activeRole) {
      setRoleDropdownOpen(false);
      return;
    }
    await switchRole(role);
    setRoleDropdownOpen(false);
  };

  const handleStopImpersonation = async () => {
    await stopImpersonation();
  };

  return (
    <div className="min-h-screen flex bg-cream">
      {/* Impersonation Banner */}
      {isImpersonating && (
        <div className="fixed top-0 left-0 right-0 z-[60] bg-red-600 text-white px-4 py-2 flex items-center justify-between shadow-lg">
          <div className="flex items-center gap-3">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <span className="text-sm font-medium">
              ⚠️ Mode Impersonation actif. Vous êtes connecté en tant que <strong>{user?.full_name}</strong>.
            </span>
          </div>
          <button
            onClick={handleStopImpersonation}
            className="px-3 py-1 bg-white text-red-600 rounded text-sm font-medium hover:bg-red-50 transition-colors"
          >
            Arrêter l'impersonation
          </button>
        </div>
      )}

      <aside
        className={`fixed inset-y-0 left-0 w-72 bg-navy flex flex-col transform transition-transform duration-300 z-50 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        } lg:relative lg:translate-x-0 ${isImpersonating ? "top-10" : ""}`}
      >
        <div className="p-8 border-b border-white/10">
          <h1 className="text-2xl font-[300] text-white">
            EDU<span className="italic text-orange-l">AI</span>
          </h1>
          <p className="text-white/40 text-xs mt-1 capitalize">{ROLE_LABELS[activeRole] || activeRole}</p>
        </div>

        {/* Context Switcher */}
        {hasMultipleRoles && (
          <div className="px-4 py-3 border-b border-white/10" ref={dropdownRef}>
            <button
              onClick={() => setRoleDropdownOpen(!roleDropdownOpen)}
              className="w-full flex items-center justify-between px-3 py-2 bg-white/10 rounded-lg text-white text-sm hover:bg-white/15 transition-colors"
            >
              <span className="flex items-center gap-2">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                </svg>
                {ROLE_LABELS[activeRole] || activeRole}
              </span>
              <svg className={`w-4 h-4 transition-transform ${roleDropdownOpen ? "rotate-180" : ""}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            
            {roleDropdownOpen && (
              <div className="mt-2 bg-white rounded-lg shadow-lg overflow-hidden">
                {user?.roles?.map((role) => (
                  <button
                    key={role}
                    onClick={() => handleSwitchRole(role)}
                    className={`w-full px-4 py-2 text-left text-sm flex items-center gap-2 transition-colors ${
                      role === activeRole
                        ? "bg-orange/10 text-orange font-medium"
                        : "text-gray-700 hover:bg-gray-100"
                    }`}
                  >
                    {role === activeRole && (
                      <svg className="w-4 h-4 text-orange" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    )}
                    {ROLE_LABELS[role] || role}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        <nav className="p-4 space-y-1 overflow-y-auto flex-1">
          {isStudent ? (
            studentNav.map((item) => (
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
            ))
          ) : navItems ? (
            navItems.map((item) => (
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
            ))
          ) : null}
        </nav>

        <div className="p-4 border-t border-white/10 mt-auto">
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

      <div className={`flex-1 flex flex-col min-h-screen ${isImpersonating ? "pt-10" : ""}`}>
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