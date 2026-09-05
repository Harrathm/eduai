import { useState } from "react";
import { Outlet, NavLink, useLocation, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui";
import { useAuthStore } from "../../../store/authStore";

interface NavItem {
  to: string;
  label: string;
  icon: string;
  end?: boolean;
  badge?: number;
  roles?: string[];
}

const NAV_ITEMS: NavItem[] = [
  { to: "/dashboard/admin", label: "Overview", icon: "M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1h3a1 1 0 001-1V10", end: true },
  { to: "/dashboard/admin/users", label: "Users", icon: "M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" },
  { to: "/dashboard/admin/schools", label: "Schools", icon: "M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" },
  { to: "/dashboard/admin/course-distribution", label: "Course Dist.", icon: "M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" },
  { to: "/dashboard/admin/teacher-catalog", label: "Teacher Catalog", icon: "M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" },
  { to: "/dashboard/admin/courses", label: "Courses", icon: "M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253M13 18.747l2-2m0 0c1.666-1.669 3.716-1.668 5.396 0l2.214 2.214c1.665 1.668 1.665 4.22 0 5.876l-2.214 2.214c-.56.56-1.292.84-2.088.84H9.708c-.796 0-1.528-.28-2.088-.84l-2.214-2.214c-1.666-1.656-1.666-4.208 0-5.876l2.214-2.214z" },
  { to: "/dashboard/admin/pedagogical-review", label: "Review Pédago.", icon: "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z", roles: ["PEDAGOGICAL_ADMIN"] },
  { to: "/dashboard/admin/library-review", label: "Validation Bibliothèque", icon: "M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253M13 18.747l2-2m0 0c1.666-1.669 3.716-1.668 5.396 0l2.214 2.214c1.665 1.668 1.665 4.22 0 5.876l-2.214 2.214c-.56.56-1.292.84-2.088.84H9.708c-.796 0-1.528-.28-2.088-.84l-2.214-2.214c-1.666-1.656-1.666-4.208 0-5.876l2.214-2.214z", roles: ["PEDAGOGICAL_ADMIN"] },
  { to: "/dashboard/admin/arborescence", label: "Arborescence", icon: "M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" },
  { to: "/dashboard/admin/publication-status", label: "Statut Publication", icon: "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" },
  { to: "/dashboard/admin/finance", label: "Finance", icon: "M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.1 0 2 .9 2 2s-.9 2-2 2-2-.9-2-2 .9-2 2-2m0-5.5c1.381 0 2.5 1.043 2.5 2.333v3.334c0 1.29-1.119 2.333-2.5 2.333s-2.5-1.043-2.5-2.333v-3.334C6.5 6.543 7.619 5.5 9 5.5" },
  { to: "/dashboard/admin/analytics", label: "Analytics", icon: "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" },
  { to: "/dashboard/admin/teachers", label: "Teacher Queue", icon: "M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" },
  { to: "/dashboard/admin/packages", label: "Token Packages", icon: "M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.1 0 2 .9 2 2s-.9 2-2 2-2-.9-2-2 .9-2 2-2m0-5.5c1.381 0 2.5 1.043 2.5 2.333v3.334c0 1.29-1.119 2.333-2.5 2.333s-2.5-1.043-2.5-2.333v-3.334C6.5 6.543 7.619 5.5 9 5.5" },
  { to: "/dashboard/admin/invite-codes", label: "Invite Codes", icon: "M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" },
  { to: "/dashboard/admin/audit", label: "Audit Log", icon: "M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 12.02 0 8.874-3.88 8.99-8.99z" },
  { to: "/dashboard/admin/seuils-config", label: "Seuils Config", icon: "M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" },
  { to: "/dashboard/admin/specialites-pedagogiques", label: "Spécialités Pédago.", icon: "M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" },
  { to: "/dashboard/admin/ai-factory", label: "AI Factory", icon: "M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z" },
  { to: "/dashboard/admin/broadcast", label: "Broadcast", icon: "M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" },
  { to: "/dashboard/admin/inbox", label: "Inbox", icon: "M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" },
  { to: "/dashboard/admin/settings", label: "Settings", icon: "M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" },
];

export default function AdminLayout() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="min-h-screen flex bg-cream">
      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 w-72 bg-navy transform transition-transform duration-300 z-50 flex flex-col ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        } lg:relative lg:translate-x-0`}
      >
        {/* Logo */}
        <div className="p-6 border-b border-white/10">
          <h1 className="text-xl font-display text-white font-light">
            EDU<span className="italic text-orange-lighter">AI</span>
          </h1>
          <p className="text-white/40 text-xs mt-1 font-body">Admin Panel</p>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-0.5 overflow-y-auto">
          {NAV_ITEMS.filter(item => !item.roles || item.roles.includes(user?.role?.toUpperCase() || "")).map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                  isActive
                    ? "bg-gradient-to-r from-orange to-orange-l text-white shadow-sm"
                    : "text-white/50 hover:bg-white/5 hover:text-white/80"
                }`
              }
            >
              <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d={item.icon} />
              </svg>
              <span>{item.label}</span>
              {item.badge ? (
                <span className="ml-auto px-2 py-0.5 text-xs bg-red-500 text-white rounded-full">
                  {item.badge}
                </span>
              ) : null}
            </NavLink>
          ))}
        </nav>

        {/* Bottom section */}
        <div className="p-4 border-t border-white/10 space-y-1">
          <Button variant="ghost" onClick={handleLogout} className="w-full">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            Deconnexion
          </Button>
          <div className="mt-2 pt-2 border-t border-white/5 px-4">
            <div className="text-xs text-white/30">v1.0.0</div>
          </div>
        </div>
      </aside>

      {/* Mobile overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 bg-black/50 z-40 lg:hidden" onClick={() => setSidebarOpen(false)} />
      )}

      {/* Main content */}
      <div className="flex-1 flex flex-col min-h-screen">
        {/* Header */}
        <header className="bg-white/90 backdrop-blur-sm border-b border-black/5 px-6 py-4 flex items-center justify-between sticky top-0 z-30">
          <div className="flex items-center gap-4">
              <Button variant="ghost" size="sm" onClick={() => setSidebarOpen(true)} className="lg:hidden">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </Button>
            <div>
              <h2 className="text-sm font-semibold text-navy font-display">
                {NAV_ITEMS.find(item => location.pathname === item.to || (item.to !== "/dashboard/admin" && location.pathname.startsWith(item.to)))?.label || "Dashboard"}
              </h2>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* Notifications */}
              <Button variant="ghost" size="sm" onClick={() => setShowNotifications(!showNotifications)} className="relative">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M15 17h5l-1.405-1.405A2 2 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
                <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
              </Button>

            {/* User */}
            <div className="flex items-center gap-3">
              <div className="hidden sm:block text-end">
                <div className="text-sm font-medium text-navy">{user?.full_name}</div>
                <div className="text-xs text-orange font-medium capitalize">{user?.role?.toLowerCase().replace("_", " ")}</div>
              </div>
              <div className="w-10 h-10 rounded-full bg-gradient-to-r from-orange to-orange-l flex items-center justify-center text-white font-semibold text-sm">
                {user?.full_name?.charAt(0) || "A"}
              </div>
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