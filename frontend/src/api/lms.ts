const API_URL = "";

const getToken = () => localStorage.getItem("token");

async function fetchAPI(endpoint: string, options: RequestInit = {}) {
  const token = getToken();
  const res = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `API error ${res.status}`);
  }
  return res.json();
}

export const adminCoursesAPI = {
  list: (params?: { status_filter?: string; search?: string; skip?: number; limit?: number }) => {
    const sp = new URLSearchParams();
    if (params?.status_filter) sp.set("status_filter", params.status_filter);
    if (params?.search) sp.set("search", params.search);
    if (params?.skip) sp.set("skip", String(params.skip));
    if (params?.limit) sp.set("limit", String(params.limit));
    const qs = sp.toString();
    return fetchAPI(`/api/admin/courses${qs ? `?${qs}` : ""}`);
  },
  get: (id: number) => fetchAPI(`/api/admin/courses/${id}`),
  create: (data: any) => fetchAPI("/api/admin/courses", { method: "POST", body: JSON.stringify(data) }),
  update: (id: number, data: any) =>
    fetchAPI(`/api/admin/courses/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  delete: (id: number) =>
    fetchAPI(`/api/admin/courses/${id}`, { method: "DELETE" }),
  publish: (id: number, price_tokens?: number, price_dt?: number) =>
    fetchAPI(`/api/admin/courses/${id}/publish?price_tokens=${price_tokens || 0}&price_dt=${price_dt || 0}`, { method: "POST" }),
  unpublish: (id: number) =>
    fetchAPI(`/api/admin/courses/${id}/unpublish`, { method: "POST" }),
  duplicate: (id: number) =>
    fetchAPI(`/api/admin/courses/${id}/duplicate`, { method: "POST" }),
  reorder: (id: number, order: number[]) =>
    fetchAPI(`/api/admin/courses/${id}/reorder`, { method: "POST", body: JSON.stringify({ order }) }),
  analytics: (id: number) => fetchAPI(`/api/admin/courses/${id}/analytics`),
};

export const adminChaptersAPI = {
  list: (courseId: number) => fetchAPI(`/api/admin/courses/${courseId}/chapters`),
  get: (courseId: number, chapterId: number) => fetchAPI(`/api/admin/courses/${courseId}/chapters/${chapterId}`),
  create: (courseId: number, data: any) =>
    fetchAPI(`/api/admin/courses/${courseId}/chapters`, { method: "POST", body: JSON.stringify(data) }),
  update: (courseId: number, chapterId: number, data: any) =>
    fetchAPI(`/api/admin/courses/${courseId}/chapters/${chapterId}`, { method: "PATCH", body: JSON.stringify(data) }),
  delete: (courseId: number, chapterId: number) =>
    fetchAPI(`/api/admin/courses/${courseId}/chapters/${chapterId}`, { method: "DELETE" }),
};

export const adminLessonsAPI = {
  list: (moduleId: number) => fetchAPI(`/api/admin/lessons?module_id=${moduleId}`),
  get: (id: number) => fetchAPI(`/api/admin/lessons/${id}`),
  create: (moduleId: number, data: any) =>
    fetchAPI(`/api/admin/lessons?module_id=${moduleId}`, { method: "POST", body: JSON.stringify(data) }),
  update: (id: number, data: any) =>
    fetchAPI(`/api/admin/lessons/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  delete: (id: number) => fetchAPI(`/api/admin/lessons/${id}`, { method: "DELETE" }),
  reorder: (order: number[]) => fetchAPI(`/api/admin/lessons/reorder`, { method: "POST", body: JSON.stringify({ order }) }),
};

export const adminQuizzesAPI = {
  getByLesson: (lessonId: number) => fetchAPI(`/api/admin/quizzes/lesson/${lessonId}`),
  get: (id: number) => fetchAPI(`/api/admin/quizzes/${id}`),
  create: (data: any) =>
    fetchAPI("/api/admin/quizzes", { method: "POST", body: JSON.stringify(data) }),
  update: (id: number, data: any) =>
    fetchAPI(`/api/admin/quizzes/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  delete: (id: number) =>
    fetchAPI(`/api/admin/quizzes/${id}`, { method: "DELETE" }),
  addQuestion: (quizId: number, data: any) =>
    fetchAPI(`/api/admin/quizzes/${quizId}/questions`, { method: "POST", body: JSON.stringify(data) }),
  updateQuestion: (quizId: number, questionId: number, data: any) =>
    fetchAPI(`/api/admin/quizzes/${quizId}/questions/${questionId}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteQuestion: (quizId: number, questionId: number) =>
    fetchAPI(`/api/admin/quizzes/${quizId}/questions/${questionId}`, { method: "DELETE" }),
  addOption: (quizId: number, questionId: number, data: any) =>
    fetchAPI(`/api/admin/quizzes/${quizId}/questions/${questionId}/options`, { method: "POST", body: JSON.stringify(data) }),
  deleteOption: (quizId: number, questionId: number, optionId: number) =>
    fetchAPI(`/api/admin/quizzes/${quizId}/questions/${questionId}/options/${optionId}`, { method: "DELETE" }),
};

export const learnerAPI = {
  catalog: (category?: string) =>
    fetchAPI(`/api/learner/courses${category ? `?category=${category}` : ""}`),
  courseDetail: (id: number) => fetchAPI(`/api/learner/courses/${id}`),
  syllabus: (id: number) => fetchAPI(`/api/learner/courses/${id}/syllabus`),
  enroll: (courseId: number) =>
    fetchAPI(`/api/learner/courses/${courseId}/enroll`, { method: "POST" }),
  myCourses: () => fetchAPI("/api/learner/my-courses"),
  lesson: (id: number) => fetchAPI(`/api/learner/lessons/${id}`),
  updateProgress: (lessonId: number, data: any) =>
    fetchAPI(`/api/learner/lessons/${lessonId}/progress`, { method: "POST", body: JSON.stringify(data) }),
  startQuiz: (quizId: number) => fetchAPI(`/api/learner/quizzes/${quizId}/start`, { method: "POST" }),
  submitQuiz: (quizId: number, data: any) =>
    fetchAPI(`/api/learner/quizzes/${quizId}/submit`, { method: "POST", body: JSON.stringify(data) }),
  certificates: () => fetchAPI("/api/learner/certificates"),
  certificate: (id: number) => fetchAPI(`/api/learner/certificates/${id}`),
  getCourseCertificate: (courseId: number) => fetchAPI(`/api/learner/courses/${courseId}/certificate`),
};