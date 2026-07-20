const API_URL = "";

function getToken(): string | null {
  return localStorage.getItem("token");
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers as Record<string, string> || {}),
  };

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    const detail = typeof err.detail === "object" ? JSON.stringify(err.detail) : (err.detail || `HTTP ${res.status}`);
    throw new Error(detail);
  }

  if (res.status === 204) return {} as T;
  return res.json();
}

// ─── Types ──────────────────────────────────────────────────────────────────

export interface AdminUser {
  id: number;
  email: string;
  full_name: string | null;
  role: string;
  school_id: number;
  school_name: string | null;
  is_active: boolean;
  is_approved: boolean;
  token_balance: number;
  dt_balance: number;
  total_dt_earned: number;
  created_at: string;
  last_login: string | null;
}

export interface AdminSchool {
  id: number;
  name: string;
  domain: string | null;
  slug: string;
  is_active: boolean;
  subscription_tier: string;
  max_users: number | null;
  created_at: string;
}

export interface AdminCourse {
  id: number;
  uuid: string | null;
  title: string;
  description: string | null;
  short_description: string | null;
  cover_url: string | null;
  thumbnail_url: string | null;
  category: string | null;
  level: string | null;
  status: string;
  price_tokens: number;
  price_dt: number;
  is_free: boolean;
  teacher_id: number;
  teacher_name: string;
  author_name: string;
  max_students: number | null;
  students_enrolled: number;
  total_chapters: number;
  total_modules: number;
  total_lessons: number;
  is_published: boolean;
  published_at: string | null;
  created_at: string | null;
  updated_at: string | null;
  language: string | null;
  prerequisites: string | null;
  learning_objectives: string | null;
  visibility: string | null;
  enrollment_type: string | null;
  tags: string[] | null;
  chapters?: Chapter[];
}

export interface Chapter {
  id: number;
  title: string;
  description: string | null;
  order: number;
  order_index: number;
  lessons: Lesson[];
}

export interface Lesson {
  id: number;
  chapter_id: number;
  title: string;
  description: string | null;
  lesson_type: string;
  content_text: string | null;
  video_url: string | null;
  pdf_url: string | null;
  image_urls: string[];
  link_url: string | null;
  link_title: string | null;
  order: number;
  duration_minutes: number;
  is_free: boolean;
}

export interface Transaction {
  id: number;
  user_id: number;
  user_email: string | null;
  user_name: string | null;
  type: string;
  amount: number;
  currency: string;
  status: string;
  description: string | null;
  created_at: string;
}

export interface RevenueData {
  period: string;
  total_revenue: number;
  revenue_by_currency: Record<string, number>;
  monthly_recurring_revenue: number;
  annual_run_rate: number;
  ai_cost_estimate: number;
  estimated_profit: number;
  active_users_in_period: number;
  total_users: number;
  conversion_rate: number;
  top_schools: { school_id: number; school_name: string; revenue: number }[];
  plan_distribution: Record<string, number>;
  total_transactions: number;
  total_courses: number;
  published_courses: number;
}

export interface DashboardStats {
  total_users: number;
  total_teachers: number;
  total_students: number;
  total_courses: number;
  pending_courses: number;
  published_courses: number;
  total_transactions: number;
  total_tokens_sold: number;
  total_dt_revenue: number;
  total_tokens_consumed: number;
  pending_teacher_registrations: number;
}

export interface GlobalStats {
  users: { total: number; active: number; teachers: number; students: number; admins: number };
  schools: { total: number; active: number; by_tier: Record<string, number> };
  finances: { total_dt_in_system: number; total_tokens_in_system: number; total_transactions: number; total_dt_volume: number };
  ai: { total_tokens_consumed: number; estimated_cost_dt: number };
  courses: { total: number; published: number };
}

export interface TeacherRegistration {
  id: number;
  email: string;
  full_name: string;
  qualifications: string | null;
  experience_years: number | null;
  status: string;
  school_id: number;
  rejection_reason: string | null;
  created_at: string;
  reviewed_at: string | null;
}

export interface WalletEntry {
  id: number;
  email: string;
  full_name: string | null;
  role: string;
  school_id: number;
  school_name: string;
  balance_dt: number;
  balance_tokens: number;
  total_dt_spent: number;
  total_tokens_spent: number;
  is_active: boolean;
}

export interface WalletListResponse {
  total: number;
  skip: number;
  limit: number;
  items: WalletEntry[];
}

export interface WalletAdjustResult {
  id: number;
  email: string;
  balance_dt: number;
  balance_tokens: number;
  action: string;
  amount_dt: number;
  amount_tokens: number;
  reason: string;
  admin_id: number;
  timestamp: string;
}

export interface EnrollmentTrend {
  date: string;
  registrations: number;
}

export interface ApiCostTrend {
  date: string;
  tokens_consumed: number;
  estimated_cost_dt: number;
}

export interface TrendResponse<T> {
  period: string;
  data: T[];
}

export interface CourseAnalytics {
  course_id: number;
  course_title: string;
  total_modules: number;
  total_lessons: number;
  total_enrolled: number;
  completion_rate: number;
  total_revenue: number;
}

export interface PaginatedResponse<T> {
  total: number;
  page: number;
  per_page: number;
  items: T[];
}

export const adminUsers = {
  list: (params?: {
    role?: string; is_active?: boolean; search?: string;
    page?: number; per_page?: number; sort_by?: string; sort_order?: string;
  }) => {
    const sp = new URLSearchParams();
    if (params?.role) sp.set("role", params.role);
    if (params?.is_active !== undefined) sp.set("is_active", String(params.is_active));
    if (params?.search) sp.set("search", params.search);
    if (params?.page) sp.set("page", String(params.page));
    if (params?.per_page) sp.set("per_page", String(params.per_page));
    if (params?.sort_by) sp.set("sort_by", params.sort_by);
    if (params?.sort_order) sp.set("sort_order", params.sort_order);
    return request<PaginatedResponse<AdminUser>>(`/api/admin/users?${sp}`);
  },

  listAll: () => request<AdminUser[]>("/api/admin/users-all"),

  get: (id: number) => request<AdminUser>(`/api/admin/users/${id}`),

  create: (data: { email: string; password: string; full_name?: string; role: string; school_id?: number }) => {
    const sp = new URLSearchParams();
    sp.set("email", data.email);
    sp.set("password", data.password);
    if (data.full_name) sp.set("full_name", data.full_name);
    sp.set("role", data.role);
    if (data.school_id) sp.set("school_id", String(data.school_id));
    return request<AdminUser>(`/api/admin/users?${sp.toString()}`, { method: "POST" });
  },

  delete: (id: number) => request<{ ok: boolean; deleted: number }>(`/api/admin/users/${id}`, { method: "DELETE" }),

  toggleActive: (id: number) =>
    request<{ id: number; is_active: boolean }>(`/api/admin/users/${id}/toggle-active`, { method: "PUT" }),

  updateBalance: (id: number, data: { tokens?: number; dt_balance?: number }) =>
    request<AdminUser>(`/api/admin/users/${id}/balance`, { method: "PUT", body: JSON.stringify(data) }),

  changeRole: (id: number, role: string) =>
    request<{ id: number; new_role: string }>(`/api/admin/users/${id}/change-role?new_role=${role}`, { method: "PUT" }),

  approve: (id: number, approved: boolean) =>
    request<AdminUser>(`/api/admin/users/${id}/approve`, { method: "PUT", body: JSON.stringify({ approved }) }),

  resetPassword: (id: number, newPassword: string) =>
    request<{ ok: boolean }>(`/api/admin/users/${id}/reset-password?new_password=${newPassword}`, { method: "POST" }),

  addWallet: (id: number, amountTokens?: number, amountDt?: number, reason?: string) =>
    request<WalletAdjustResult>(`/api/admin/wallets/${id}/add`, {
      method: "POST",
      body: JSON.stringify({
        amount_dt: amountDt || 0,
        amount_tokens: amountTokens || 0,
        reason: reason || "Admin credit",
      }),
    }),

  deductWallet: (id: number, amountTokens?: number, amountDt?: number, reason?: string) =>
    request<WalletAdjustResult>(`/api/admin/wallets/${id}/deduct`, {
      method: "POST",
      body: JSON.stringify({
        amount_dt: amountDt || 0,
        amount_tokens: amountTokens || 0,
        reason: reason || "Admin deduction",
      }),
    }),

  listWallets: (params?: { school_id?: number; role?: string; skip?: number; limit?: number }) => {
    const sp = new URLSearchParams();
    if (params?.school_id) sp.set("school_id", String(params.school_id));
    if (params?.role) sp.set("role", params.role);
    if (params?.skip) sp.set("skip", String(params.skip));
    if (params?.limit) sp.set("limit", String(params.limit));
    return request<WalletListResponse>(`/api/admin/wallets?${sp}`);
  },

  update: (id: number, data: { full_name?: string; email?: string; role?: string; school_id?: number; is_active?: boolean; is_approved?: boolean }) =>
    request<AdminUser>(`/api/admin/users/${id}`, { method: "PUT", body: JSON.stringify(data) }),
};

// ─── Broadcast / Messages ──────────────────────────────────────────────

export interface BroadcastMessage {
  id: number;
  type: string;
  subject: string;
  body: string;
  sender_id: number;
  sender_name: string | null;
  recipient_id: number | null;
  recipient_name: string | null;
  recipient_role: string | null;
  target_audience: string | null;
  is_read: boolean;
  created_at: string;
}

export interface BroadcastResult {
  ok: boolean;
  target: string;
  audience_count: number;
  messages_created: number;
  subject: string;
}

export const adminBroadcast = {
  send: (data: { target: string; subject: string; body: string }) =>
    request<BroadcastResult>("/api/admin/broadcast", { method: "POST", body: JSON.stringify(data) }),

  listMessages: (params?: { skip?: number; limit?: number }) => {
    const sp = new URLSearchParams();
    if (params?.skip) sp.set("skip", String(params.skip));
    if (params?.limit) sp.set("limit", String(params.limit));
    return request<{ total: number; items: BroadcastMessage[] }>(`/api/admin/messages?${sp}`);
  },

  deleteMessage: (id: number) =>
    request<{ status: string }>(`/api/admin/messages/${id}`, { method: "DELETE" }),
};

// ─── Schools ─────────────────────────────────────────────────────────────────

export const adminSchools = {
  list: (params?: { search?: string; tier?: string; is_active?: boolean; page?: number; per_page?: number }) => {
    const sp = new URLSearchParams();
    if (params?.search) sp.set("search", params.search);
    if (params?.tier) sp.set("tier", params.tier);
    if (params?.is_active !== undefined) sp.set("is_active", String(params.is_active));
    if (params?.page) sp.set("page", String(params.page));
    if (params?.per_page) sp.set("per_page", String(params.per_page));
    return request<PaginatedResponse<AdminSchool>>(`/api/admin/schools?${sp}`);
  },

  get: (id: number) => request<AdminSchool>(`/api/admin/schools/${id}`),

  create: (data: Partial<AdminSchool>) =>
    request<AdminSchool>("/api/admin/schools", { method: "POST", body: JSON.stringify(data) }),

  update: (id: number, data: Partial<AdminSchool>) =>
    request<AdminSchool>(`/api/admin/schools/${id}`, { method: "PUT", body: JSON.stringify(data) }),

  delete: (id: number) =>
    request<{ ok: boolean; deleted: number }>(`/api/admin/schools/${id}`, { method: "DELETE" }),
};

// ─── Courses ─────────────────────────────────────────────────────────────────

export const adminCourses = {
  list: (params?: { status_filter?: string; search?: string; category?: string; level?: string; skip?: number; limit?: number }) => {
    const sp = new URLSearchParams();
    if (params?.status_filter) sp.set("status_filter", params.status_filter);
    if (params?.search) sp.set("search", params.search);
    if (params?.category) sp.set("category", params.category);
    if (params?.level) sp.set("level", params.level);
    if (params?.skip) sp.set("skip", String(params.skip));
    if (params?.limit) sp.set("limit", String(params.limit));
    return request<{ total: number; items: AdminCourse[] }>(`/api/admin/courses?${sp}`);
  },

  get: (id: number) => request<AdminCourse>(`/api/admin/courses/${id}`),

  create: (data: Partial<AdminCourse>) =>
    request<AdminCourse>("/api/admin/courses", { method: "POST", body: JSON.stringify(data) }),

  update: (id: number, data: Partial<AdminCourse>) =>
    request<AdminCourse>(`/api/admin/courses/${id}`, { method: "PATCH", body: JSON.stringify(data) }),

  delete: (id: number) => request<void>(`/api/admin/courses/${id}`, { method: "DELETE" }),

  publish: (id: number, priceTokens?: number, priceDt?: number) =>
    request<AdminCourse>(
      `/api/admin/courses/${id}/publish?price_tokens=${priceTokens || 0}&price_dt=${priceDt || 0}`,
      { method: "POST" }
    ),

  submitForReview: (id: number) =>
    request<{ id: number; pedagogical_status: string }>(`/api/admin/courses/${id}/submit-for-review`, { method: "POST" }),

  unpublish: (id: number) =>
    request<AdminCourse>(`/api/admin/courses/${id}/unpublish`, { method: "POST" }),

  archive: (id: number) =>
    request<AdminCourse>(`/api/admin/courses/${id}/archive`, { method: "POST" }),

  duplicate: (id: number) =>
    request<AdminCourse>(`/api/admin/courses/${id}/duplicate`, { method: "POST" }),

  preview: (id: number) => request<any>(`/api/admin/courses/${id}/preview`),

  analytics: (id: number) => request<CourseAnalytics>(`/api/admin/courses/${id}/analytics`),
};

// ─── Transactions ───────────────────────────────────────────────────────────

export const adminTransactions = {
  list: (params?: { skip?: number; limit?: number; user_id?: number; type?: string; status?: string }) => {
    const sp = new URLSearchParams();
    if (params?.skip) sp.set("skip", String(params.skip));
    if (params?.limit) sp.set("limit", String(params.limit));
    if (params?.user_id) sp.set("user_id", String(params.user_id));
    if (params?.type) sp.set("type", params.type);
    if (params?.status) sp.set("status", params.status);
    return request<PaginatedResponse<Transaction>>(`/api/admin/transactions?${sp}`);
  },
  listAll: () => request<PaginatedResponse<Transaction>>(`/api/admin/transactions?limit=200`),
};

// ─── Analytics ───────────────────────────────────────────────────────────────

export const adminAnalytics = {
  dashboard: () => request<DashboardStats>("/api/admin/dashboard"),
  global: () => request<GlobalStats>("/api/admin/stats/global"),
  overview: () => request<DashboardStats>("/api/admin/analytics/overview"),
  users: () => request<DashboardStats[]>("/api/admin/analytics/users"),
  revenue: (period = "30d") => request<RevenueData>(`/api/admin/analytics/revenue?period=${period}`),
  wallets: () => request<AdminUser[]>("/api/admin/wallets"),
  enrollments: (period = "30d") => request<TrendResponse<EnrollmentTrend>>(`/api/admin/analytics/enrollments?period=${period}`),
  apiCosts: (period = "30d") => request<TrendResponse<ApiCostTrend>>(`/api/admin/analytics/api-costs?period=${period}`),
};

// ─── Teacher Registrations ───────────────────────────────────────────────────

export const adminTeacherRegistrations = {
  list: (statusFilter?: string) => {
    const sp = statusFilter ? `?status_filter=${statusFilter}` : "";
    return request<TeacherRegistration[]>(`/api/admin/teacher-registrations${sp}`);
  },
  review: (id: number, status: "approved" | "rejected", rejectionReason?: string) =>
    request<{ ok: boolean; status: string; reg_id: number }>(
      `/api/admin/teacher-registrations/${id}/review?status=${status}${rejectionReason ? `&rejection_reason=${encodeURIComponent(rejectionReason)}` : ""}`,
      { method: "POST" }
    ),
};

// ─── Auth ────────────────────────────────────────────────────────────────────

// ─── AI Factory ───────────────────────────────────────────────────────────

export interface AIFactoryPlan {
  title: string;
  subtitle: string;
  description: string;
  level: string;
  category: string;
  modules: {
    title: string;
    description: string;
    lessons: { title: string; description: string; duration_minutes: number }[];
  }[];
}

export interface AIFactoryBundle {
  plan: AIFactoryPlan;
  lessons: Record<string, string>;
  quizzes: Record<string, any>;
  media_prompts: Record<string, { image_prompt: string; video_prompt: string }>;
}

export interface AIPreviewInfo {
  title: string;
  subtitle: string;
  description: string;
  level: string;
  category: string;
  total_modules: number;
  total_lessons: number;
  lessons: {
    module_title: string;
    lesson_title: string;
    description: string;
    has_content: boolean;
    has_quiz: boolean;
    has_media_prompts: boolean;
  }[];
}

export interface AIPublishResult {
  course_id: number;
  title: string;
  slug: string;
  status: string;
}

export const adminAIFactory = {
  generatePlan: (data: { topic: string; use_rag?: boolean }) =>
    request<{ plan: AIFactoryPlan }>("/api/admin/ai-factory/generate-plan", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  generateContentStream: (data: {
    topic: string; lesson_title: string; lesson_description: string;
    module_title?: string; use_rag?: boolean;
  }) => {
    const token = getToken();
    return fetch(`${API_URL}/api/admin/ai-factory/generate-content-stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(data),
    });
  },

  generateQuiz: (data: { topic: string; lesson_title: string; lesson_content?: string }) =>
    request<{ quiz: any }>("/api/admin/ai-factory/generate-quiz", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  generateMediaPrompts: (data: { topic: string; lesson_title: string; lesson_description?: string }) =>
    request<{ image_prompt: string; video_prompt: string }>("/api/admin/ai-factory/generate-media-prompts", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  generateImage: (data: { prompt: string; size?: string; quality?: string }) =>
    request<{ url: string; revised_prompt: string }>("/api/admin/ai-factory/generate-image", {
      method: "POST",
      body: JSON.stringify({ size: "1024x1024", quality: "standard", ...data }),
    }),

  saveImageToBundle: (data: { bundle: AIFactoryBundle; lesson_key: string; image_url: string; image_prompt?: string }) =>
    request<{ bundle: AIFactoryBundle }>("/api/admin/ai-factory/save-image-to-bundle", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  generateBundle: (data: { topic: string; use_rag?: boolean }) =>
    request<AIFactoryBundle>("/api/admin/ai-factory/generate-bundle", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  preview: (data: { bundle: AIFactoryBundle }) =>
    request<{ preview: AIPreviewInfo }>("/api/admin/ai-factory/preview", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  publish: (data: { bundle: AIFactoryBundle }) =>
    request<AIPublishResult>("/api/admin/ai-factory/publish", {
      method: "POST",
      body: JSON.stringify(data),
    }),
};

// ─── Settings & Logs ────────────────────────────────────────────────────

export interface PlatformSettingItem {
  id?: number;
  key: string;
  value: string;
  description?: string;
}

export interface TokenLimits {
  student_free: { monthly: number; daily: number; per_request: number };
  student_premium: { monthly: number; daily: number; per_request: number };
  teacher: { monthly: number; daily: number; per_request: number };
  admin: { monthly: number; daily: number; per_request: number };
  super_admin: { monthly: number; daily: number; per_request: number };
}

export interface ErrorLogResponse {
  total_lines: number;
  lines: string[];
  file: string;
  truncated: boolean;
  error?: string;
}

export const adminSettings = {
  list: () => request<PlatformSettingItem[]>("/api/admin/settings"),

  update: (key: string, value: string, description?: string) =>
    request<PlatformSettingItem>("/api/admin/settings", {
      method: "PUT",
      body: JSON.stringify({ key, value, description }),
    }),

  apply: (settings: { key: string; value: string; description?: string }[]) =>
    request<{ ok: boolean; applied: number; settings: any[] }>("/api/admin/settings/apply", {
      method: "POST",
      body: JSON.stringify(settings),
    }),

  getTokenLimits: () =>
    request<{ limits: TokenLimits }>("/api/admin/settings/token-limits"),

  updateTokenLimits: (limits: TokenLimits) =>
    request<{ ok: boolean; limits: TokenLimits }>("/api/admin/settings/token-limits", {
      method: "PUT",
      body: JSON.stringify(limits),
    }),

  refreshCache: () =>
    request<{ ok: boolean; message: string }>("/api/admin/settings/refresh-cache", {
      method: "POST",
    }),
};

export const adminLogs = {
  errors: (params?: { lines?: number; search?: string; level?: string }) => {
    const sp = new URLSearchParams();
    if (params?.lines) sp.set("lines", String(params.lines));
    if (params?.search) sp.set("search", params.search);
    if (params?.level) sp.set("level", params.level);
    return request<ErrorLogResponse>(`/api/admin/logs/errors?${sp}`);
  },
};

export const adminAuth = {
  me: () => request<AdminUser>("/auth/me"),
};

// ─── Teacher Classes (v2) ──────────────────────────────────────────

export interface TeacherClassInfo {
  id: number;
  teacher_id: number;
  school_id: number | null;
  teacher_name: string | null;
  school_name: string | null;
  name: string;
  description: string | null;
  code: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  courses_count: number;
  students_count: number;
}

export interface ClassCourseAccessInfo {
  id: number;
  class_id: number;
  course_id: number;
  course_title: string | null;
  assigned_at: string | null;
  is_active: boolean;
}

export interface StudentEnrollmentInfo {
  id: number;
  student_id: number;
  class_id: number;
  student_name: string | null;
  student_email: string | null;
  enrolled_at: string | null;
  is_active: boolean;
}

export interface TeacherCourseCatalogEntry {
  class_id: number;
  class_name: string;
  class_code: string | null;
  teacher_id: number;
  teacher_name: string | null;
  teacher_email: string | null;
  school_id: number | null;
  school_name: string | null;
  courses: { course_id: number; title: string; category: string | null; level: string | null; status: string; is_published: boolean }[];
  students_count: number;
  created_at: string | null;
}

export interface TeacherCourseCatalogResponse {
  total_classes: number;
  classes: TeacherCourseCatalogEntry[];
}

export const adminTeacherClasses = {
  // Super admin: list all teacher classes
  listAll: (params?: { school_id?: number; search?: string }) => {
    const sp = new URLSearchParams();
    if (params?.school_id) sp.set("school_id", String(params.school_id));
    if (params?.search) sp.set("search", params.search);
    return request<TeacherClassInfo[]>(`/api/admin/teacher-classes?${sp}`);
  },

  // Super admin: get class details
  get: (id: number) => request<TeacherClassInfo>(`/api/admin/teacher-classes/${id}`),

  // Super admin: list courses in a teacher class
  listCourses: (classId: number) =>
    request<ClassCourseAccessInfo[]>(`/api/admin/teacher-classes/${classId}/courses`),

  // Super admin: list students in a teacher class
  listStudents: (classId: number) =>
    request<StudentEnrollmentInfo[]>(`/api/admin/teacher-classes/${classId}/students`),

  // Super admin: teacher courses catalog
  catalog: (params?: { school_id?: number; teacher_id?: number; search?: string }) => {
    const sp = new URLSearchParams();
    if (params?.school_id) sp.set("school_id", String(params.school_id));
    if (params?.teacher_id) sp.set("teacher_id", String(params.teacher_id));
    if (params?.search) sp.set("search", params.search);
    return request<TeacherCourseCatalogResponse>(`/api/admin/teacher-courses/catalog?${sp}`);
  },
};