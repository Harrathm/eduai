import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useEffect } from "react";
import LoginPage from "./features/auth/pages/LoginPage";
import RegisterPage from "./features/auth/pages/RegisterPage";
import AdminDashboardContainer from "./features/admin/pages/AdminDashboardContainer";
import AdminLayout from "./features/admin/pages/AdminLayout";
import AdminDashboardPage from "./features/admin/pages/AdminDashboardPage";
import AdminUsersPage from "./features/admin/pages/AdminUsersPage";
import AdminSchoolsPage from "./features/admin/pages/AdminSchoolsPage";
import AdminAnalyticsPage from "./features/admin/pages/AdminAnalyticsPage";
import AdminTeacherQueuePage from "./features/admin/pages/AdminTeacherQueuePage";
import AdminCoursesPage from "./features/admin/pages/AdminCoursesPage";
import AdminSettingsPage from "./features/admin/pages/AdminSettingsPage";
import AdminFinancePage from "./features/admin/pages/AdminFinancePage";
import BroadcastCenter from "./features/admin/pages/BroadcastCenter";
import ContentCreatorAI from "./features/admin/pages/ContentCreatorAI";
import AdminTokenPackagesPage from "./features/admin/pages/AdminTokenPackagesPage";
import AdminAuditLogPage from "./features/admin/pages/AdminAuditLogPage";
import SchoolAdminLayout from "./features/admin/pages/SchoolAdminLayout";
import SchoolAdminDashboard from "./features/admin/pages/SchoolAdminDashboard";
import UserManagementView from "./features/admin/pages/UserManagementView";
import ContentModerationView from "./features/admin/pages/ContentModerationView";
import PlatformOverview from "./features/admin/pages/PlatformOverview";
import SchoolOverview from "./features/admin/pages/SchoolOverview";
import FinanceCenter from "./features/admin/pages/FinanceCenter";
import AdminInboxView from "./features/admin/pages/AdminInboxView";
import PlatformSettings from "./features/admin/pages/PlatformSettings";
import PedagogicalAdminPage from "./features/admin/pages/PedagogicalAdminPage";
import PedagogicalLeadPage from "./features/admin/pages/PedagogicalLeadPage";
import SchoolCourseDistribution from "./features/admin/pages/SchoolCourseDistribution";
import SuperAdminCourseFactory from "./features/admin/pages/SuperAdminCourseFactory";
import TeacherDashboard from "./features/teacher/pages/TeacherDashboard";
import StudentDashboard from "./features/student/pages/StudentDashboard";
import DashboardLayout from "./components/layout/DashboardLayout";
import MyLearning from "./features/teacher/pages/MyLearning";
import ClassroomManager from "./features/teacher/pages/ClassroomManager";
import TeacherAIStudio from "./features/teacher/pages/TeacherAIStudio";
import TeacherWallet from "./features/teacher/pages/TeacherWallet";
import TeacherSalesPage from "./features/teacher/pages/TeacherSalesPage";
import StudentCourseCatalog from "./features/student/pages/CourseCatalog";
import StudentWallet from "./features/student/pages/StudentWallet";
import CourseBuilderPage from "./features/admin/pages/CourseBuilderPage";
import CourseEditorPage from "./features/admin/pages/CourseEditorPage";
import LearnerPlayerPage from "./features/learner/pages/PlayerPage";
import CatalogPage from "./pages/learner/CatalogPage";
import CoursePlayerPage from "./pages/learner/CoursePlayerPage";
import LearnerAIChatPage from "./pages/learner/LearnerAIChatPage";

import AdminMediaLibraryPage from "./pages/admin/AdminMediaLibraryPage";
import { useAuthStore } from "./store/authStore";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { useOnlineStatus } from "./hooks";

function RequireAuth({ children }) {
  const token = useAuthStore((s) => s.token);
  if (!token) return <Navigate to="/login" replace />;
  return children;
}

function RequireRole({ roles, children, redirectTo = "/dashboard" }: { 
  roles: string[]; 
  children: React.ReactNode;
  redirectTo?: string;
}) {
  const user = useAuthStore((s) => s.user);
  const userRole = user?.role?.toUpperCase();
  
  if (!user) return <Navigate to="/login" replace />;
  if (!roles.some(r => r.toUpperCase() === userRole)) {
    return <Navigate to={redirectTo} replace />;
  }
  return <>{children}</>;
}

function OnlineStatusBanner() {
  const isOnline = useOnlineStatus();
  
  if (isOnline) return null;
  
  return (
    <div className="fixed top-0 left-0 right-0 bg-yellow-500 text-yellow-900 px-4 py-2 text-center text-sm font-medium z-50">
      You are offline. Some features may not be available.
    </div>
  );
}

function AppContent() {
  const restore = useAuthStore((s) => s.restore);
  const user = useAuthStore((s) => s.user);
  
  useEffect(() => {
    restore();
  }, []);

  const getDefaultRoute = () => {
    const role = user?.role?.toUpperCase();
    if (role === "SUPER_ADMIN" || role === "PEDAGOGICAL_ADMIN") return "/dashboard/admin";
    if (role === "ADMIN_SCHOOL" || role === "PEDAGOGICAL_LEAD") return "/dashboard/school";
    return "/dashboard";
  };

  return (
    <ErrorBoundary>
      <OnlineStatusBanner />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        
        {/* SUPER_ADMIN - Uses AdminLayout with new professional dashboard */}
        <Route
          path="/dashboard/admin"
          element={
            <RequireRole roles={["SUPER_ADMIN", "PEDAGOGICAL_ADMIN"]}>
              <AdminLayout />
            </RequireRole>
          }
        >
          <Route index element={<AdminDashboardPage />} />
          <Route path="users" element={<AdminUsersPage />} />
          <Route path="schools" element={<AdminSchoolsPage />} />
          <Route path="courses" element={<AdminCoursesPage />} />
          <Route path="courses/:courseId" element={<CourseEditorPage />} />
          <Route path="analytics" element={<AdminAnalyticsPage />} />
          <Route path="teachers" element={<AdminTeacherQueuePage />} />
          <Route path="finance" element={<FinanceCenter />} />
          <Route path="media" element={<AdminMediaLibraryPage />} />
          <Route path="inbox" element={<AdminInboxView />} />
          <Route path="ai-factory" element={<ContentCreatorAI />} />
          <Route path="course-distribution" element={<SchoolCourseDistribution />} />
          <Route path="teacher-catalog" element={<SuperAdminCourseFactory />} />
          <Route path="broadcast" element={<BroadcastCenter />} />
          <Route path="settings" element={<AdminSettingsPage />} />
          <Route path="packages" element={<AdminTokenPackagesPage />} />
          <Route path="audit" element={<AdminAuditLogPage />} />
          <Route path="pedagogical-review" element={<PedagogicalAdminPage />} />
        </Route>

        {/* ADMIN_SCHOOL - Uses SchoolAdminLayout */}
        <Route
          path="/dashboard/school"
          element={
            <RequireRole roles={["ADMIN_SCHOOL", "PEDAGOGICAL_LEAD"]}>
              <SchoolAdminLayout />
            </RequireRole>
          }
        >
          <Route index element={<SchoolOverview />} />
          <Route path="users" element={<UserManagementView />} />
          <Route path="finance" element={<FinanceCenter />} />
          <Route path="courses" element={<AdminCoursesPage />} />
          <Route path="teachers" element={<AdminTeacherQueuePage />} />
          <Route path="settings" element={<AdminSettingsPage />} />
          <Route path="pedagogical" element={<PedagogicalLeadPage />} />
        </Route>

        {/* TEACHER & STUDENT - Uses DashboardLayout */}
        <Route
          path="/dashboard"
          element={
            <RequireAuth>
              {["SUPER_ADMIN", "PEDAGOGICAL_ADMIN"].includes(user?.role?.toUpperCase()) ? <Navigate to="/dashboard/admin" replace /> :
               ["ADMIN_SCHOOL", "PEDAGOGICAL_LEAD"].includes(user?.role?.toUpperCase()) ? <Navigate to="/dashboard/school" replace /> :
               <DashboardLayout />}
            </RequireAuth>
          }
        >
          <Route index element={
            user?.role === "teacher" ? <TeacherDashboard /> : 
            user?.role === "student" ? <StudentDashboard /> :
            <Navigate to="/login" replace />
          } />
          
          {/* Teacher Routes */}
          <Route path="teacher/learning" element={<MyLearning />} />
          <Route path="teacher/classroom" element={<ClassroomManager />} />
          <Route path="teacher/ai-studio" element={<TeacherAIStudio />} />
          <Route path="teacher/wallet" element={<TeacherWallet />} />
          <Route path="teacher/sales" element={<TeacherSalesPage />} />
          
          {/* Student Routes */}
          <Route path="courses" element={<CatalogPage />} />
          <Route path="courses/:courseId" element={<CoursePlayerPage />} />
          <Route path="courses/:courseId/lessons/:lessonId" element={<CoursePlayerPage />} />
          <Route path="assignments" element={<StudentCourseCatalog />} />
          <Route path="ai-tutor" element={<LearnerAIChatPage />} />
          <Route path="wallet" element={<StudentWallet />} />
        </Route>

        {/* Public learner routes - auth handled internally */}
        <Route path="learn/courses" element={<CatalogPage />} />
        <Route path="learn/courses/:courseId" element={<CoursePlayerPage />} />
        <Route path="learn/courses/:courseId/lessons/:lessonId" element={<CoursePlayerPage />} />
        
        {/* Redirect root to login or dashboard */}
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </ErrorBoundary>
  );
}

export default function App() {
  return (
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <AppContent />
    </BrowserRouter>
  );
}
