import { BrowserRouter, Routes, Route, Navigate, Outlet } from "react-router-dom";
import { Suspense, lazy, useEffect } from "react";
import { useAuthStore } from "./store/authStore";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { useOnlineStatus } from "./hooks";
import DashboardLayout from "./components/layout/DashboardLayout";
import FloatingAITutor from "./components/FloatingAITutor";
import { TeacherWriteGuard, TeacherStateBadge } from "./components/TeacherStateGuard";

// ─── Lazy-loaded pages ──────────────────────────────────────────────
const LoginPage = lazy(() => import("./features/auth/pages/LoginPage"));
const RegisterPage = lazy(() => import("./features/auth/pages/RegisterPage"));
const ForgotPasswordPage = lazy(() => import("./features/auth/pages/ForgotPassword"));
const ResetPasswordPage = lazy(() => import("./features/auth/pages/ResetPassword"));
const OnboardingPage = lazy(() => import("./features/student/pages/OnboardingPage"));

// Admin
const AdminLayout = lazy(() => import("./features/admin/pages/AdminLayout"));
const AdminDashboardPage = lazy(() => import("./features/admin/pages/AdminDashboardPage"));
const AdminUsersPage = lazy(() => import("./features/admin/pages/AdminUsersPage"));
const AdminSchoolsPage = lazy(() => import("./features/admin/pages/AdminSchoolsPage"));
const AdminCoursesPage = lazy(() => import("./features/admin/pages/AdminCoursesPage"));
const AdminAnalyticsPage = lazy(() => import("./features/admin/pages/AdminAnalyticsPage"));
const AdminTeacherQueuePage = lazy(() => import("./features/admin/pages/AdminTeacherQueuePage"));
const AdminSettingsPage = lazy(() => import("./features/admin/pages/AdminSettingsPage"));
const AdminTokenPackagesPage = lazy(() => import("./features/admin/pages/AdminTokenPackagesPage"));
const AdminInviteCodesPage = lazy(() => import("./features/admin/pages/AdminInviteCodesPage"));
const AdminAuditLogPage = lazy(() => import("./features/admin/pages/AdminAuditLogPage"));
const AdminArborescencePage = lazy(() => import("./features/admin/pages/AdminArborescencePage"));
const AdminPublicationStatusPage = lazy(() => import("./features/admin/pages/AdminPublicationStatusPage"));
const AdminSeuilsConfigPage = lazy(() => import("./features/admin/pages/AdminSeuilsConfigPage"));
const AdminSpecialitesPedagogiquesPage = lazy(() => import("./features/admin/pages/AdminSpecialitesPedagogiquesPage"));
const AdminMediaLibraryPage = lazy(() => import("./pages/admin/AdminMediaLibraryPage"));
const BroadcastCenter = lazy(() => import("./features/admin/pages/BroadcastCenter"));
const ContentCreatorAI = lazy(() => import("./features/admin/pages/ContentCreatorAI"));
const PedagogicalAdminPage = lazy(() => import("./features/admin/pages/PedagogicalAdminPage"));
const SchoolAdminLayout = lazy(() => import("./features/admin/pages/SchoolAdminLayout"));
const SchoolOverview = lazy(() => import("./features/admin/pages/SchoolOverview"));
const UserManagementView = lazy(() => import("./features/admin/pages/UserManagementView"));
const FinanceCenter = lazy(() => import("./features/admin/pages/FinanceCenter"));
const PedagogicalLeadPage = lazy(() => import("./features/admin/pages/PedagogicalLeadPage"));
const AdminInboxView = lazy(() => import("./features/admin/pages/AdminInboxView"));
const SchoolCourseDistribution = lazy(() => import("./features/admin/pages/SchoolCourseDistribution"));
const SuperAdminCourseFactory = lazy(() => import("./features/admin/pages/SuperAdminCourseFactory"));
const CourseEditorPage = lazy(() => import("./features/admin/pages/CourseEditorPage"));
const CourseBuilderPage = lazy(() => import("./features/admin/pages/CourseBuilderPage"));

// Teacher
const TeacherDashboard = lazy(() => import("./features/teacher/pages/TeacherDashboard"));
const MyLearning = lazy(() => import("./features/teacher/pages/MyLearning"));
const ClassroomManager = lazy(() => import("./features/teacher/pages/ClassroomManager"));
const TeacherAIStudio = lazy(() => import("./features/teacher/pages/TeacherAIStudio"));
const TeacherWallet = lazy(() => import("./features/teacher/pages/TeacherWallet"));
const TeacherSalesPage = lazy(() => import("./features/teacher/pages/TeacherSalesPage"));
const TeacherReorientationPage = lazy(() => import("./features/teacher/pages/TeacherReorientationPage"));
const TeacherValidationContenuPage = lazy(() => import("./features/teacher/pages/TeacherValidationContenuPage"));
const TeacherParcoursPage = lazy(() => import("./features/teacher/pages/TeacherParcoursPage"));
const TeacherElementsPage = lazy(() => import("./features/teacher/pages/TeacherElementsPage"));
const TeacherBibliothequePage = lazy(() => import("./features/teacher/pages/TeacherBibliothequePage"));
const TeacherAbonnementsPage = lazy(() => import("./features/teacher/pages/TeacherAbonnementsPage"));

// Student
const StudentDashboard = lazy(() => import("./features/student/pages/StudentDashboard"));
const ProfilePage = lazy(() => import("./features/student/pages/ProfilePage"));
const StudentCourseCatalog = lazy(() => import("./features/student/pages/CourseCatalog"));
const StudentWallet = lazy(() => import("./features/student/pages/StudentWallet"));
const StudentTierPage = lazy(() => import("./features/student/pages/StudentTierPage"));
const PacksPage = lazy(() => import("./features/student/pages/PacksPage"));
const StudentPackPage = lazy(() => import("./features/student/pages/StudentPackPage"));
const PlacementTestPage = lazy(() => import("./features/student/pages/PlacementTestPage"));
const InboxPage = lazy(() => import("./features/student/pages/InboxPage"));
const PathwayCatalogPage = lazy(() => import("./features/student/pages/PathwayCatalogPage"));
const MonParcoursPage = lazy(() => import("./features/student/pages/MonParcoursPage"));
const GamificationPage = lazy(() => import("./features/student/pages/GamificationPage"));
const StudentAssimilationProfilePage = lazy(() => import("./features/student/pages/StudentAssimilationProfilePage"));
const MySkillsPage = lazy(() => import("./features/student/pages/MySkillsPage"));

// Learner
const LearnerPlayerPage = lazy(() => import("./features/learner/pages/PlayerPage"));
const CatalogPage = lazy(() => import("./pages/learner/CatalogPage"));
const CoursePlayerPage = lazy(() => import("./pages/learner/CoursePlayerPage"));
const LearnerAIChatPage = lazy(() => import("./pages/learner/LearnerAIChatPage"));
const SoftSkillsCatalogPage = lazy(() => import("./pages/learner/SoftSkillsCatalogPage"));

// Parent
const ParentDashboardPage = lazy(() => import("./features/parent/pages/ParentDashboardPage"));
const ChildDetailPage = lazy(() => import("./features/parent/pages/ChildDetailPage"));
const ParentWalletPage = lazy(() => import("./features/parent/pages/ParentWalletPage"));
const ParentPackPage = lazy(() => import("./features/parent/pages/ParentPackPage"));
const ParentFamillePage = lazy(() => import("./features/parent/pages/ParentFamillePage"));

// ─── Loading fallback ───────────────────────────────────────────────
function PageLoader() {
  return (
    <div className="flex items-center justify-center h-screen">
      <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-orange" />
    </div>
  );
}

// ─── Auth guards ────────────────────────────────────────────────────
function isTokenExpired(token: string): boolean {
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return Date.now() >= (payload.exp || 0) * 1000;
  } catch {
    return true;
  }
}

function RequireAuth({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.token);
  const logout = useAuthStore((s) => s.logout);

  if (!token) return <Navigate to="/login" replace />;
  if (isTokenExpired(token)) {
    logout();
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
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

export default function App() {
  const user = useAuthStore((s) => s.user);
  const restore = useAuthStore((s) => s.restore);

  useEffect(() => {
    restore();
  }, []);

  return (
    <ErrorBoundary>
      <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <OnlineStatusBanner />
        <Suspense fallback={<PageLoader />}>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            <Route path="/reset-password" element={<ResetPasswordPage />} />
            <Route path="/onboarding" element={
              <RequireAuth><OnboardingPage /></RequireAuth>
            } />

            {/* SUPER_ADMIN */}
            <Route path="/dashboard/admin" element={
              <RequireRole roles={["SUPER_ADMIN", "PEDAGOGICAL_ADMIN"]}>
                <AdminLayout />
              </RequireRole>
            }>
              <Route index element={<AdminDashboardPage />} />
              <Route path="users" element={<AdminUsersPage />} />
              <Route path="schools" element={<AdminSchoolsPage />} />
              <Route path="courses" element={<AdminCoursesPage />} />
              <Route path="courses/:courseId" element={<CourseEditorPage />} />
              <Route path="courses/:courseId/builder" element={<CourseBuilderPage />} />
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
              <Route path="invite-codes" element={<AdminInviteCodesPage />} />
              <Route path="audit" element={<AdminAuditLogPage />} />
              <Route path="pedagogical-review" element={<PedagogicalAdminPage />} />
              <Route path="arborescence" element={<AdminArborescencePage />} />
              <Route path="publication-status" element={<AdminPublicationStatusPage />} />
              <Route path="seuils-config" element={<AdminSeuilsConfigPage />} />
              <Route path="specialites-pedagogiques" element={<AdminSpecialitesPedagogiquesPage />} />
            </Route>

            {/* ADMIN_SCHOOL */}
            <Route path="/dashboard/school" element={
              <RequireRole roles={["ADMIN_SCHOOL", "PEDAGOGICAL_LEAD"]}>
                <SchoolAdminLayout />
              </RequireRole>
            }>
              <Route index element={<SchoolOverview />} />
              <Route path="users" element={<UserManagementView />} />
              <Route path="finance" element={<FinanceCenter />} />
              <Route path="courses" element={<AdminCoursesPage />} />
              <Route path="courses/:courseId" element={<CourseEditorPage />} />
              <Route path="courses/:courseId/builder" element={<CourseBuilderPage />} />
              <Route path="teachers" element={<AdminTeacherQueuePage />} />
              <Route path="settings" element={<AdminSettingsPage />} />
              <Route path="pedagogical" element={<PedagogicalLeadPage />} />
            </Route>

            {/* TEACHER / STUDENT / PARENT */}
            <Route path="/dashboard" element={
              <RequireAuth>
                {["SUPER_ADMIN", "PEDAGOGICAL_ADMIN"].includes(user?.role?.toUpperCase()) ? <Navigate to="/dashboard/admin" replace /> :
                 ["ADMIN_SCHOOL", "PEDAGOGICAL_LEAD"].includes(user?.role?.toUpperCase()) ? <Navigate to="/dashboard/school" replace /> :
                 <DashboardLayout />}
              </RequireAuth>
            }>
              <Route index element={
                user?.role?.toUpperCase() === "TEACHER" ? <TeacherDashboard /> :
                user?.role?.toUpperCase() === "STUDENT" ? <StudentDashboard /> :
                user?.role?.toUpperCase() === "PARENT" ? <ParentDashboardPage /> :
                <Navigate to="/login" replace />
              } />

              {/* Teacher */}
              <Route path="teacher" element={
                <RequireRole roles={["teacher", "admin_school"]}><Outlet /></RequireRole>
              }>
                <Route path="learning" element={<MyLearning />} />
                <Route path="classroom" element={<ClassroomManager />} />
                <Route path="ai-studio" element={<TeacherWriteGuard><TeacherAIStudio /></TeacherWriteGuard>} />
                <Route path="wallet" element={<TeacherWallet />} />
                <Route path="sales" element={<TeacherSalesPage />} />
                <Route path="abonnements" element={<TeacherAbonnementsPage />} />
                <Route path="reorientations" element={<TeacherWriteGuard><TeacherReorientationPage /></TeacherWriteGuard>} />
                <Route path="validation-contenu" element={<TeacherWriteGuard><TeacherValidationContenuPage /></TeacherWriteGuard>} />
                <Route path="parcours" element={<TeacherWriteGuard><TeacherParcoursPage /></TeacherWriteGuard>} />
                <Route path="elements" element={<TeacherWriteGuard><TeacherElementsPage /></TeacherWriteGuard>} />
                <Route path="bibliotheque" element={<TeacherBibliothequePage />} />
              </Route>

              <Route path="inbox" element={<InboxPage />} />

              {/* Student */}
              <Route path="courses" element={<RequireRole roles={["student", "admin_school"]}><CatalogPage /></RequireRole>} />
              <Route path="courses/:courseId" element={<RequireRole roles={["student", "admin_school", "teacher"]}><CoursePlayerPage /></RequireRole>} />
              <Route path="courses/:courseId/lessons/:lessonId" element={<RequireRole roles={["student", "admin_school", "teacher"]}><CoursePlayerPage /></RequireRole>} />
              <Route path="ai-tutor" element={<RequireRole roles={["student", "admin_school", "teacher"]}><LearnerAIChatPage /></RequireRole>} />
              <Route path="wallet" element={<RequireRole roles={["student", "admin_school"]}><StudentWallet /></RequireRole>} />
              <Route path="packs" element={<RequireRole roles={["student", "admin_school"]}><PacksPage /></RequireRole>} />
              <Route path="settings/subscription" element={<RequireRole roles={["student", "admin_school"]}><StudentPackPage /></RequireRole>} />
              <Route path="tier" element={<RequireRole roles={["student", "admin_school"]}><StudentTierPage /></RequireRole>} />
              <Route path="soft-skills" element={<RequireAuth><SoftSkillsCatalogPage /></RequireAuth>} />
              <Route path="my-skills" element={<RequireAuth><MySkillsPage /></RequireAuth>} />
              <Route path="placement/:testId" element={<RequireRole roles={["student", "admin_school"]}><PlacementTestPage /></RequireRole>} />
              <Route path="profile" element={<RequireRole roles={["student", "teacher", "admin_school"]}><ProfilePage /></RequireRole>} />
              <Route path="assimilation" element={<RequireRole roles={["student", "admin_school"]}><StudentAssimilationProfilePage /></RequireRole>} />
              <Route path="parcours-catalog" element={<RequireRole roles={["student", "teacher"]}><PathwayCatalogPage /></RequireRole>} />
              <Route path="mon-parcours" element={<RequireRole roles={["student"]}><MonParcoursPage /></RequireRole>} />
              <Route path="gamification" element={<RequireRole roles={["student", "teacher"]}><GamificationPage /></RequireRole>} />

              {/* Parent */}
              <Route path="parent" element={<RequireRole roles={["parent"]}><Outlet /></RequireRole>}>
                <Route index element={<ParentDashboardPage />} />
                <Route path="enfant/:eleveId" element={<ChildDetailPage />} />
                <Route path="enfant/:eleveId/wallet" element={<ParentWalletPage />} />
                <Route path="enfant/:eleveId/pack" element={<ParentPackPage />} />
                <Route path="famille" element={<ParentFamillePage />} />
              </Route>
            </Route>

            {/* Public learner routes */}
            <Route path="learn/courses" element={<CatalogPage />} />
            <Route path="learn/courses/:courseId" element={<CoursePlayerPage />} />
            <Route path="learn/courses/:courseId/lessons/:lessonId" element={<CoursePlayerPage />} />

            <Route path="/" element={<Navigate to="/login" replace />} />
            <Route path="*" element={<Navigate to="/login" replace />} />
          </Routes>

          {/* Global floating AI tutor — visible on all authenticated pages */}
          {user && <FloatingAITutor />}
        </Suspense>
      </BrowserRouter>
    </ErrorBoundary>
  );
}
