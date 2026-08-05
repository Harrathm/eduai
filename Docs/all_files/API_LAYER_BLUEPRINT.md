# API LAYER BLUEPRINT — EDUAI Learning

**Date :** 05/08/2026
**Objectif :** Unifier la couche API — 0 `fetch()` inline dans les composants

---

## 1. STRUCTURE DES FICHIERS API

### Arborescence cible

```
src/api/
├── client.ts              ← Client HTTP centralisé (singleton, intercepteurs, refresh)
├── types.ts               ← Types partagés (PaginatedResponse, ApiError, etc.)
│
├── authApi.ts             ← Login, register, forgot/reset password, me
├── userApi.ts             ← CRUD users (admin), roles, balance
├── schoolApi.ts           ← CRUD schools, invite codes
├── courseApi.ts           ← CRUD courses (admin + learner), chapters, lessons
├── catalogApi.ts          ← Catalogue public, enrollment
├── quizApi.ts             ← Quiz CRUD (admin) + attempts (learner)
├── walletApi.ts           ← Balance, history, purchase
├── tierApi.ts             ← Dashboard, daily objective, recommended path, placement tests
├── abonnementApi.ts       ← Packs, abonnements, tier changes
├── conversationApi.ts     ← Conversations IA, messages, export
├── aiApi.ts               ← AI tutor (ask, explain, correct, generate), streaming SSE
├── gamificationApi.ts     ← Badges, streak, rankings
├── pathwayApi.ts          ← Parcours, matières, spécialités, éléments
├── inboxApi.ts            ← Messages inbox
├── adminApi.ts            ← Admin-specific (analytics, settings, logs, broadcast, teacher registrations, teacher classes)
│
└── index.ts               ← Ré-export barrel
```

### Règles de regroupement

| Règle | Application |
|-------|-------------|
| **1 entité = 1 fichier** | `walletApi.ts` pour `/api/wallet/*` |
| **Entités liées = 1 fichier** | `courseApi.ts` contient courses + chapters + lessons (un seul endpoint `/api/admin/courses/:id/chapters`) |
| **Endpoints publics séparés** | `catalogApi.ts` (pas d'auth) ≠ `courseApi.ts` (auth requis) |
| **Admin vs Learner dans le même fichier** | `courseApi.ts` exporte `courseAdmin` ET `courseLearner` |
| **Pas de doublon** | Seul `adminApi.ts` contient les endpoints `/api/admin/*` spécifiques (analytics, settings, etc.) |

### Migration : de l'ancien vers le nouveau

| Ancien fichier | Nouveau fichier | Action |
|----------------|-----------------|--------|
| `api/lms.ts` | `api/courseApi.ts` | **Supprimer** — tout est dans courseApi |
| `api/courses.ts` | `api/courseApi.ts` | **Supprimer** — doublon de lms.ts |
| `api/tier.ts` | `api/tierApi.ts` | **Renommer** + migrer vers apiClient |
| `api/catalog.ts` | `api/catalogApi.ts` | **Renommer** + migrer vers apiClient |
| `api/wallet.ts` | `api/walletApi.ts` | **Enrichir** (déjà partiellement sur apiClient) |
| `api/conversations.ts` | `api/conversationApi.ts` | **Renommer** (déjà sur apiClient) |
| `features/admin/api/index.ts` | `api/adminApi.ts` + `api/userApi.ts` + `api/schoolApi.ts` | **Décomposer** le fichier de 776 lignes |
| `features/teacher/api/index.ts` | `api/courseApi.ts` (classes teacher) | **Fusionner** |
| `features/teacher/api/moduleApi.ts` | `api/pathwayApi.ts` | **Fusionner** |
| `features/parent/api/index.ts` | `api/userApi.ts` (children) | **Fusionner** |
| `features/pathway/api/index.ts` | `api/pathwayApi.ts` | **Fusionner** |

---

## 2. CODE DE RÉFÉRENCE — `src/api/client.ts`

```typescript
// src/api/client.ts
// Client HTTP centralisé — singleton avec intercepteurs, refresh token, erreurs

import { tokenStorage } from "../utils/tokenStorage";

const API_URL = import.meta.env.VITE_API_URL || "";

// ─── Types ─────────────────────────────────────────────────────────────────

export interface RequestConfig extends RequestInit {
  /** Ne pas attacher le token (pour les routes publiques) */
  skipAuth?: boolean;
  /** Ne pas attacher school_id automatiquement */
  skipTenant?: boolean;
}

export interface ApiClientError extends Error {
  status: number;
  detail?: string;
  raw?: unknown;
}

// ─── Interceptor types ─────────────────────────────────────────────────────

type RequestInterceptor = (config: RequestConfig) => RequestConfig | Promise<RequestConfig>;
type ResponseInterceptor = (response: Response) => Response | Promise<Response>;
type ErrorInterceptor = (error: ApiClientError) => ApiClientError | Promise<ApiClientError>;

// ─── ApiClient class ───────────────────────────────────────────────────────

class ApiClient {
  private baseURL: string;
  private requestInterceptors: RequestInterceptor[] = [];
  private responseInterceptors: ResponseInterceptor[] = [];
  private errorInterceptors: ErrorInterceptor[] = [];
  private isRefreshing = false;
  private failedQueue: Array<{
    resolve: (token: string) => void;
    reject: (err: unknown) => void;
  }> = [];

  constructor(baseURL: string = API_URL) {
    this.baseURL = baseURL;
  }

  // ── Interceptor management ─────────────────────────────────────────────

  addRequestInterceptor(fn: RequestInterceptor): void {
    this.requestInterceptors.push(fn);
  }

  addResponseInterceptor(fn: ResponseInterceptor): void {
    this.responseInterceptors.push(fn);
  }

  addErrorInterceptor(fn: ErrorInterceptor): void {
    this.errorInterceptors.push(fn);
  }

  // ── Token & Tenant ────────────────────────────────────────────────────

  private getToken(): string | null {
    return tokenStorage.getToken();
  }

  private getSchoolId(): number | null {
    const user = tokenStorage.getUser();
    return user?.school_id ?? null;
  }

  private isAdminSchool(): boolean {
    const user = tokenStorage.getUser();
    const role = user?.role?.toUpperCase();
    return role === "ADMIN_SCHOOL" || role === "PEDAGOGICAL_LEAD";
  }

  // ── Refresh token queue ───────────────────────────────────────────────

  private processQueue(error: unknown, token: string | null): void {
    this.failedQueue.forEach((prom) => {
      if (error || !token) {
        prom.reject(error);
      } else {
        prom.resolve(token);
      }
    });
    this.failedQueue = [];
  }

  private async handleRefreshToken(): Promise<string> {
    const refreshToken = tokenStorage.getRefreshToken();
    if (!refreshToken) throw new Error("No refresh token");

    const res = await fetch(`${this.baseURL}/auth/refresh-token`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!res.ok) throw new Error("Refresh failed");

    const data = await res.json();
    tokenStorage.setToken(data.access_token);
    if (data.refresh_token) tokenStorage.setRefreshToken(data.refresh_token);
    return data.access_token;
  }

  // ── Core fetch ────────────────────────────────────────────────────────

  async fetch<T = unknown>(endpoint: string, config: RequestConfig = {}): Promise<T> {
    const url = endpoint.startsWith("http") ? endpoint : `${this.baseURL}${endpoint}`;
    const { skipAuth = false, skipTenant = false, ...fetchOptions } = config;

    // Build headers
    let headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(fetchOptions.headers as Record<string, string>),
    };

    // Attach token
    if (!skipAuth) {
      const token = this.getToken();
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }
    }

    // Attach school_id for admin_school users
    if (!skipTenant && this.isAdminSchool()) {
      const schoolId = this.getSchoolId();
      if (schoolId) {
        headers["X-School-Id"] = String(schoolId);
      }
    }

    // Build final config
    let requestConfig: RequestConfig = {
      ...fetchOptions,
      headers,
      skipAuth,
      skipTenant,
    };

    // Run request interceptors
    for (const interceptor of this.requestInterceptors) {
      requestConfig = await interceptor(requestConfig);
    }

    try {
      let response = await fetch(url, requestConfig);

      // ── 401: Refresh token ──────────────────────────────────────────
      if (response.status === 401 && !url.includes("/auth/refresh-token")) {
        if (this.isRefreshing) {
          // Queue while refresh is in progress
          return new Promise<T>((resolve, reject) => {
            this.failedQueue.push({
              resolve: (newToken: string) => {
                requestConfig.headers = {
                  ...requestConfig.headers,
                  Authorization: `Bearer ${newToken}`,
                };
                resolve(this.fetch<T>(endpoint, requestConfig));
              },
              reject,
            });
          });
        }

        this.isRefreshing = true;

        try {
          const newToken = await this.handleRefreshToken();
          this.processQueue(null, newToken);

          // Retry with new token
          requestConfig.headers = {
            ...requestConfig.headers,
            Authorization: `Bearer ${newToken}`,
          };
          response = await fetch(url, requestConfig);
        } catch (refreshError) {
          this.processQueue(refreshError, null);
          tokenStorage.clearAll();
          window.location.href = "/login";
          throw this.createError(401, "Session expirée. Veuillez vous reconnecter.");
        } finally {
          this.isRefreshing = false;
        }
      }

      // Run response interceptors
      for (const interceptor of this.responseInterceptors) {
        response = await interceptor(response);
      }

      // ── Error handling ──────────────────────────────────────────────
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const detail = typeof errorData.detail === "object"
          ? JSON.stringify(errorData.detail)
          : errorData.detail;

        throw this.createError(response.status, detail || `HTTP ${response.status}`);
      }

      // ── Empty response (204) ────────────────────────────────────────
      if (response.status === 204) return null as T;

      const text = await response.text();
      return text ? (JSON.parse(text) as T) : (null as T);
    } catch (error) {
      let apiError: ApiClientError;

      if ((error as ApiClientError).status) {
        apiError = error as ApiClientError;
      } else if (error instanceof TypeError) {
        apiError = this.createError(0, "Erreur réseau. Vérifiez votre connexion.");
      } else {
        apiError = this.createError(0, (error as Error).message || "Erreur inconnue");
      }

      // Run error interceptors
      for (const interceptor of this.errorInterceptors) {
        apiError = await interceptor(apiError);
      }

      throw apiError;
    }
  }

  private createError(status: number, message: string): ApiClientError {
    const error = new Error(message) as ApiClientError;
    error.status = status;
    return error;
  }

  // ── Convenience methods ─────────────────────────────────────────────

  get<T = unknown>(endpoint: string, config?: RequestConfig): Promise<T> {
    return this.fetch<T>(endpoint, { ...config, method: "GET" });
  }

  post<T = unknown>(endpoint: string, data?: unknown, config?: RequestConfig): Promise<T> {
    return this.fetch<T>(endpoint, {
      ...config,
      method: "POST",
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  put<T = unknown>(endpoint: string, data?: unknown, config?: RequestConfig): Promise<T> {
    return this.fetch<T>(endpoint, {
      ...config,
      method: "PUT",
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  patch<T = unknown>(endpoint: string, data?: unknown, config?: RequestConfig): Promise<T> {
    return this.fetch<T>(endpoint, {
      ...config,
      method: "PATCH",
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  delete<T = unknown>(endpoint: string, config?: RequestConfig): Promise<T> {
    return this.fetch<T>(endpoint, { ...config, method: "DELETE" });
  }

  /**
   * Upload avec FormData (pas de Content-Type manuel — le navigateur le gère)
   */
  upload<T = unknown>(endpoint: string, formData: FormData, config?: RequestConfig): Promise<T> {
    return this.fetch<T>(endpoint, {
      ...config,
      method: "POST",
      body: formData,
      // Important: pas de Content-Type pour FormData (boundary auto)
      headers: {
        ...(config?.headers as Record<string, string>),
        // Ne PAS définir Content-Type — le navigateur ajoute le boundary
      },
    });
  }

  /**
   * Téléchargement de fichier (retourne un Blob)
   */
  async download(endpoint: string, config?: RequestConfig): Promise<Blob> {
    const url = endpoint.startsWith("http") ? endpoint : `${this.baseURL}${endpoint}`;
    const token = this.getToken();

    const res = await fetch(url, {
      ...config,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(config?.headers as Record<string, string>),
      },
    });

    if (!res.ok) throw this.createError(res.status, "Erreur lors du téléchargement");
    return res.blob();
  }

  /**
   * Streaming SSE (pour les réponses IA)
   */
  stream(endpoint: string, data?: unknown): ReadableStream<Uint8Array> | null {
    const url = `${this.baseURL}${endpoint}`;
    const token = this.getToken();

    // Utilise un AbortController pour pouvoir annuler
    const controller = new AbortController();

    fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: data ? JSON.stringify(data) : undefined,
      signal: controller.signal,
    }).then((res) => {
      if (!res.body) return;
      // Le consumer doit lire le stream
    });

    // Retourne le controller pour annulation
    return null; // Implémentation côté consumer
  }
}

// ─── Singleton ──────────────────────────────────────────────────────────────

export const api = new ApiClient();

// ─── Intercepteurs globaux ─────────────────────────────────────────────────

// Logging en développement
if (import.meta.env.DEV) {
  api.addResponseInterceptor(async (response) => {
    console.log(`[API] ${response.status} ${response.url}`);
    return response;
  });

  api.addErrorInterceptor(async (error) => {
    console.error(`[API] ${error.status}: ${error.message}`);
    return error;
  });
}

export default api;
```

---

## 3. SERVICES REFACTORISÉS

### `src/api/courseApi.ts` — cours, chapitres, leçons (admin + learner)

```typescript
// src/api/courseApi.ts
// Service unifié pour les cours (admin CRUD + learner catalog/player)

import { api } from "./client";

// ─── Types ─────────────────────────────────────────────────────────────────

export interface Course {
  id: number;
  uuid: string | null;
  title: string;
  description: string | null;
  short_description: string | null;
  cover_url: string | null;
  thumbnail_url: string | null;
  category: string | null;
  level: string | null;
  language: string | null;
  status: string;
  price_tokens: number;
  price_dt: number;
  is_free: boolean;
  is_published: boolean;
  published_at: string | null;
  teacher_id: number;
  teacher_name: string;
  author_name: string;
  max_students: number | null;
  students_enrolled: number;
  total_chapters: number;
  total_modules: number;
  total_lessons: number;
  total_duration_minutes: number;
  created_at: string | null;
  updated_at: string | null;
  prerequisites: string | null;
  learning_objectives: string | null;
  visibility: string | null;
  enrollment_type: string | null;
  tags: string[] | null;
  slug: string;
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
  content_html: string | null;
  video_url: string | null;
  video_duration_seconds: number | null;
  video_thumbnail_url: string | null;
  pdf_url: string | null;
  document_url: string | null;
  document_type: string | null;
  image_urls: string[];
  link_url: string | null;
  link_title: string | null;
  order: number;
  duration_minutes: number;
  is_free: boolean;
  is_preview: boolean;
  has_quiz: boolean;
}

export interface SyllabusChapter {
  id: number;
  title: string;
  order_index: number;
  lessons: SyllabusLesson[];
}

export interface SyllabusLesson {
  id: number;
  title: string;
  lesson_type: string;
  duration_minutes: number;
  is_free: boolean;
  status: string;
  has_quiz: boolean;
}

export interface LessonContent extends Lesson {
  quiz?: {
    id: number;
    title: string;
    description?: string;
    time_limit_seconds?: number;
    passing_score_percent: number;
  };
  notes?: Note[];
  bookmarks?: Bookmark[];
}

export interface Note {
  id: number;
  content: string;
  position: number | null;
  created_at: string;
}

export interface Bookmark {
  id: number;
  position_seconds: number;
  note: string | null;
  created_at: string;
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

// ─── Admin Course API ───────────────────────────────────────────────────────

export const courseAdmin = {
  list: (params?: {
    status_filter?: string;
    search?: string;
    category?: string;
    level?: string;
    skip?: number;
    limit?: number;
  }) => {
    const sp = new URLSearchParams();
    if (params?.status_filter) sp.set("status_filter", params.status_filter);
    if (params?.search) sp.set("search", params.search);
    if (params?.category) sp.set("category", params.category);
    if (params?.level) sp.set("level", params.level);
    if (params?.skip) sp.set("skip", String(params.skip));
    if (params?.limit) sp.set("limit", String(params.limit));
    const qs = sp.toString();
    return api.get<{ total: number; items: Course[] }>(`/api/admin/courses${qs ? `?${qs}` : ""}`);
  },

  get: (id: number) => api.get<Course>(`/api/admin/courses/${id}`),

  create: (data: Partial<Course>) =>
    api.post<Course>("/api/admin/courses", data),

  update: (id: number, data: Partial<Course>) =>
    api.patch<Course>(`/api/admin/courses/${id}`, data),

  delete: (id: number) =>
    api.delete<void>(`/api/admin/courses/${id}`),

  publish: (id: number, priceTokens = 0, priceDt = 0) =>
    api.post<Course>(
      `/api/admin/courses/${id}/publish?price_tokens=${priceTokens}&price_dt=${priceDt}`
    ),

  unpublish: (id: number) =>
    api.post<Course>(`/api/admin/courses/${id}/unpublish`),

  archive: (id: number) =>
    api.post<Course>(`/api/admin/courses/${id}/archive`),

  duplicate: (id: number) =>
    api.post<Course>(`/api/admin/courses/${id}/duplicate`),

  submitForReview: (id: number) =>
    api.post<{ id: number; pedagogical_status: string }>(
      `/api/admin/courses/${id}/submit-for-review`
    ),

  analytics: (id: number) =>
    api.get<CourseAnalytics>(`/api/admin/courses/${id}/analytics`),

  preview: (id: number) =>
    api.get<any>(`/api/admin/courses/${id}/preview`),
};

// ─── Admin Chapter API ──────────────────────────────────────────────────────

export const chapterAdmin = {
  list: (courseId: number) =>
    api.get<Chapter[]>(`/api/admin/courses/${courseId}/chapters`),

  get: (courseId: number, chapterId: number) =>
    api.get<Chapter>(`/api/admin/courses/${courseId}/chapters/${chapterId}`),

  create: (courseId: number, data: Partial<Chapter>) =>
    api.post<Chapter>(`/api/admin/courses/${courseId}/chapters`, data),

  update: (courseId: number, chapterId: number, data: Partial<Chapter>) =>
    api.patch<Chapter>(`/api/admin/courses/${courseId}/chapters/${chapterId}`, data),

  delete: (courseId: number, chapterId: number) =>
    api.delete<void>(`/api/admin/courses/${courseId}/chapters/${chapterId}`),
};

// ─── Admin Lesson API ───────────────────────────────────────────────────────

export const lessonAdmin = {
  list: (moduleId: number) =>
    api.get<Lesson[]>(`/api/admin/lessons?module_id=${moduleId}`),

  get: (id: number) =>
    api.get<Lesson>(`/api/admin/lessons/${id}`),

  create: (moduleId: number, data: Partial<Lesson>) =>
    api.post<Lesson>(`/api/admin/lessons?module_id=${moduleId}`, data),

  update: (id: number, data: Partial<Lesson>) =>
    api.patch<Lesson>(`/api/admin/lessons/${id}`, data),

  delete: (id: number) =>
    api.delete<void>(`/api/admin/lessons/${id}`),

  reorder: (order: number[]) =>
    api.post<void>("/api/admin/lessons/reorder", { order }),
};

// ─── Learner Course API ─────────────────────────────────────────────────────

export const courseLearner = {
  catalog: (params?: {
    search?: string;
    category?: string;
    level?: string;
    language?: string;
    skip?: number;
    limit?: number;
  }) => {
    const sp = new URLSearchParams();
    if (params?.search) sp.set("search", params.search);
    if (params?.category) sp.set("category", params.category);
    if (params?.level) sp.set("level", params.level);
    if (params?.language) sp.set("language", params.language);
    if (params?.skip) sp.set("skip", String(params.skip));
    if (params?.limit) sp.set("limit", String(params.limit));
    const qs = sp.toString();
    return api.get<Course[]>(`/api/learner/courses${qs ? `?${qs}` : ""}`);
  },

  get: (id: number) => api.get<Course>(`/api/learner/courses/${id}`),

  syllabus: (id: number) =>
    api.get<SyllabusChapter[]>(`/api/learner/courses/${id}/syllabus`),

  enroll: (courseId: number) =>
    api.post<void>(`/api/learner/courses/${courseId}/enroll`),

  myCourses: () => api.get<Course[]>("/api/learner/my-courses"),

  certificate: (courseId: number) =>
    api.get<any>(`/api/learner/courses/${courseId}/certificate`),
};

// ─── Learner Lesson API ─────────────────────────────────────────────────────

export const lessonLearner = {
  get: (id: number) => api.get<LessonContent>(`/api/learner/lessons/${id}`),

  progress: (lessonId: number, data: {
    video_position_seconds?: number;
    video_completed?: boolean;
    content_completed?: boolean;
    quiz_completed?: boolean;
    quiz_passed?: boolean;
    quiz_score?: number;
  }) => api.post<void>(`/api/learner/lessons/${lessonId}/progress`, data),

  notes: {
    list: (lessonId: number) =>
      api.get<Note[]>(`/api/learner/lessons/${lessonId}/notes`),
    create: (lessonId: number, content: string, position?: number) =>
      api.post<Note>(`/api/learner/lessons/${lessonId}/notes`, { content, position }),
  },

  bookmarks: {
    list: (lessonId: number) =>
      api.get<Bookmark[]>(`/api/learner/lessons/${lessonId}/bookmarks`),
    create: (lessonId: number, positionSeconds: number, note?: string) =>
      api.post<Bookmark>(`/api/learner/lessons/${lessonId}/bookmarks`, {
        position_seconds: positionSeconds,
        note,
      }),
  },
};
```

### `src/api/walletApi.ts` — portefeuille de crédits

```typescript
// src/api/walletApi.ts
// Service wallet — balance, historique, achat

import { api } from "./client";

// ─── Types ─────────────────────────────────────────────────────────────────

export interface WalletPool {
  type: string;
  balance: number;
  currency: string;
  expires_at: string | null;
  source: string;
}

export interface WalletBalance {
  total_dt: number;
  total_tokens: number;
  pools: WalletPool[];
}

export interface WalletTransaction {
  id: number;
  type: string;
  amount: number;
  currency: string;
  description: string | null;
  pool: string | null;
  created_at: string;
}

export interface WalletHistoryResponse {
  total: number;
  page: number;
  page_size: number;
  items: WalletTransaction[];
}

export interface PurchaseResult {
  checkout_url: string;
  session_id: string;
}

// ─── Student/Parent Wallet API ──────────────────────────────────────────────

export const walletApi = {
  balance: () => api.get<WalletBalance>("/api/wallet/balance"),

  history: (page = 1, pageSize = 20) =>
    api.get<WalletHistoryResponse>(
      `/api/wallet/history?page=${page}&page_size=${pageSize}`
    ),

  purchase: (months: 1 | 3 | 12) =>
    api.post<PurchaseResult>("/api/wallet/purchase", { months }),
};

// ─── Admin Wallet API ───────────────────────────────────────────────────────

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

export const walletAdmin = {
  list: (params?: {
    school_id?: number;
    role?: string;
    skip?: number;
    limit?: number;
  }) => {
    const sp = new URLSearchParams();
    if (params?.school_id) sp.set("school_id", String(params.school_id));
    if (params?.role) sp.set("role", params.role);
    if (params?.skip) sp.set("skip", String(params.skip));
    if (params?.limit) sp.set("limit", String(params.limit));
    return api.get<WalletListResponse>(`/api/admin/wallets?${sp}`);
  },

  add: (userId: number, amountTokens: number, amountDt: number, reason: string) =>
    api.post<WalletAdjustResult>(`/api/admin/wallets/${userId}/add`, {
      amount_dt: amountDt,
      amount_tokens: amountTokens,
      reason,
    }),

  deduct: (userId: number, amountTokens: number, amountDt: number, reason: string) =>
    api.post<WalletAdjustResult>(`/api/admin/wallets/${userId}/deduct`, {
      amount_dt: amountDt,
      amount_tokens: amountTokens,
      reason,
    }),
};
```

---

## 4. STRATÉGIE DE MIGRATION

### 4.1 — Script de détection des `fetch()` inline

**Commande PowerShell (Windows) :**
```powershell
cd D:\RAG_APP_new\frontend\src
Get-ChildItem -Recurse -Include "*.tsx","*.ts" |
  Where-Object { $_.FullName -notlike "*api\*" -and $_.FullName -notlike "*__tests__*" -and $_.FullName -notlike "*utils\*" } |
  Select-String -Pattern "await fetch\(|fetch\(`" |
  ForEach-Object { "$($_.Filename):$($_.LineNumber)" } |
  Sort-Object
```

**Commande bash (Linux/Mac) :**
```bash
cd frontend/src
grep -rn "await fetch\|fetch(\`" --include="*.tsx" --include="*.ts" \
  --exclude-dir=api --exclude-dir=__tests__ --exclude-dir=utils | \
  awk -F: '{print $1 ":" $2}' | sort
```

### 4.2 — Priorisation de migration

| Priorité | Fichier | Fetch inline | Impact |
|----------|---------|-------------|--------|
| **P0** | `UserManagementView.tsx` | 6 | Le plus gros — migrate en `userApi.ts` |
| **P0** | `AdminDashboard.tsx` | 5 | Dashboard critique — migrate en `adminApi.ts` |
| **P0** | `ClassroomManager.tsx` | 5 | Teacher core — migrate en `courseApi.ts` |
| **P1** | `ContentModerationView.tsx` | 6 | Admin — migrate en `courseApi.ts` |
| **P1** | `AdminInboxView.tsx` | 4 | Admin — migrate en `inboxApi.ts` |
| **P1** | `PlatformOverview.tsx` | 4 | Admin — migrate en `adminApi.ts` |
| **P1** | `TeacherAbonnementsPage.tsx` | 5 | Teacher — migrate en `abonnementApi.ts` |
| **P1** | `TeacherDashboard.tsx` | 3 | Teacher — migrate en `courseApi.ts` |
| **P2** | `GamificationPage.tsx` | 3 | Student — migrate en `gamificationApi.ts` |
| **P2** | `CourseCatalog.tsx` | 5 | Student — migrate en `catalogApi.ts` |
| **P2** | `AdminSettingsPage.tsx` | 1 | Admin — migrate en `adminApi.ts` |
| **P2** | `TeacherAIStudio.tsx` | 3 | Teacher — migrate en `aiApi.ts` |
| **P2** | `AdminTokenPackagesPage.tsx` | 4 | Admin — migrate en `adminApi.ts` |
| **P3** | 18 autres fichiers | 1-3 chacun | Bottom-up |

### 4.3 — Processus de migration par fichier

```
1. Identifier le fichier avec le script ci-dessus
2. Lire les appels fetch() et lister les endpoints appelés
3. Créer ou enrichir le service API correspondant dans src/api/
4. Remplacer les fetch() inline par des appels au service
5. Supprimer les imports inutiles (tokenStorage, API_URL)
6. Vérifier que le build passe (npx vite build)
7. Tester le composant manuellement ou avec un test
```

### 4.4 — Règles de migration

| Règle | Description |
|-------|-------------|
| **Jamais de `fetch()` dans un `.tsx`** | Tout passe par `src/api/*.ts` |
| **Un seul `import { api } from "./client"`** | Pas de `tokenStorage` dans les composants |
| **Types dans le fichier API** | Les interfaces vont dans le fichier service correspondant, pas dans les composants |
| **Pas de `const API_URL`** | Seul `client.ts` connaît l'URL de base |
| **FormData = `api.upload()`** | Jamais de `fetch()` avec `FormData` dans les composants |
| **Blob/Download = `api.download()`** | Pour les exports PDF/DOCX |
| **SSE Streaming = `api.stream()`** | Pour les réponses IA |

### 4.5 — Checklist de validation par fichier

- [ ] Plus de `fetch()` dans le fichier
- [ ] Plus de `localStorage.getItem("token")`
- [ ] Plus de `const API_URL = ...`
- [ ] Import du service API depuis `src/api/`
- [ ] Types importés depuis le service API
- [ ] `npx vite build` passe sans erreur
- [ ] Le composant fonctionne manuellement

---

## 5. FICHIERS À SUPPRIMER APRÈS MIGRATION

| Fichier | Remplacé par | Raison |
|---------|-------------|--------|
| `api/lms.ts` | `api/courseApi.ts` | Doublon de courses.ts |
| `api/courses.ts` | `api/courseApi.ts` | Doublon de lms.ts |
| `api/tier.ts` | `api/tierApi.ts` | Renommage + migration |
| `api/catalog.ts` | `api/catalogApi.ts` | Renommage + migration |
| `features/admin/api/index.ts` | `api/adminApi.ts` + `api/userApi.ts` + `api/schoolApi.ts` | Décomposition |
| `features/teacher/api/index.ts` | `api/courseApi.ts` | Fusion |
| `features/teacher/api/moduleApi.ts` | `api/pathwayApi.ts` | Fusion |
| `features/parent/api/index.ts` | `api/userApi.ts` | Fusion |
| `features/pathway/api/index.ts` | `api/pathwayApi.ts` | Fusion |

**Après migration complète :** `src/api/` contiendra 15 fichiers propres + `client.ts` + `types.ts` + `index.ts` = **18 fichiers**, zéro doublon.

---

**Blueprint généré le 05/08/2026 — Phase 1 de la refonte frontend EDUAI Learning**
