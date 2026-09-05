/**
 * Teacher API — classes, students, courses, wallet.
 * Merged from features/teacher/api/index.ts.
 */

import { api } from "./client";

// ─── Types ─────────────────────────────────────────────────────────────────

export interface TeacherClass {
  id: number;
  teacher_id: number;
  school_id: number;
  name: string;
  description: string;
  code: string;
  is_active: boolean;
  courses_count: number;
  students_count: number;
}

export interface ClassStudent {
  id: number;
  student_id: number;
  class_id: number;
  student_name: string;
  student_email: string;
  enrolled_at: string;
  is_active: boolean;
}

export interface TeacherCourseCatalogEntry {
  class_id: number;
  class_name: string;
  teacher_id: number;
  teacher_name: string;
  school_id: number;
  school_name: string;
  courses_count: number;
  students_count: number;
  courses: ClassCourseAccessInfo[];
}

export interface TeacherClassInfo {
  id: number;
  name: string;
  teacher_id: number;
  teacher_name: string;
  school_id: number;
  school_name: string;
  students_count: number;
}

export interface ClassCourseAccessInfo {
  id: number;
  course_id: number;
  course_title: string;
  class_id: number;
  is_active: boolean;
  granted_at: string;
}

export interface StudentEnrollmentInfo {
  id: number;
  student_id: number;
  student_name: string;
  student_email: string;
  enrolled_at: string;
  is_active: boolean;
}

// ─── Teacher Classes API ────────────────────────────────────────────────────

export const teacherClassesApi = {
  list: () => api.get<TeacherClass[]>("/api/teacher/classes"),

  create: (data: { name: string; description?: string }) =>
    api.post<TeacherClass>("/api/teacher/classes", data),

  delete: (classId: number) =>
    api.delete<void>(`/api/teacher/classes/${classId}`),

  listStudents: (classId: number) =>
    api.get<ClassStudent[]>(`/api/teacher/classes/${classId}/students`),

  removeStudent: (classId: number, studentId: number) =>
    api.delete<void>(`/api/teacher/classes/${classId}/students/${studentId}`),

  // Admin-specific endpoints
  catalog: (params?: { search?: string; school_id?: number; teacher_id?: number }) => {
    const sp = new URLSearchParams();
    if (params?.search) sp.set("search", params.search);
    if (params?.school_id) sp.set("school_id", String(params.school_id));
    if (params?.teacher_id) sp.set("teacher_id", String(params.teacher_id));
    const qs = sp.toString();
    return api.get<any>(`/api/admin/teacher-courses/catalog${qs ? `?${qs}` : ""}`);
  },

  listCourses: (classId: number) =>
    api.get<any[]>(`/api/admin/teacher-classes/${classId}/courses`),

  adminListStudents: (classId: number) =>
    api.get<any[]>(`/api/admin/teacher-classes/${classId}/students`),
};

// ─── Teacher Courses API ────────────────────────────────────────────────────

export const teacherCoursesApi = {
  listMyCourses: () => api.get<any[]>("/api/teacher/courses"),

  listClassCourses: (classId: number) =>
    api.get<any[]>(`/api/teacher/classes/${classId}/courses`),

  assignCourse: (classId: number, courseId: number) =>
    api.post<any>(`/api/teacher/classes/${classId}/courses`, { course_id: courseId }),

  removeCourse: (classId: number, courseId: number) =>
    api.delete<void>(`/api/teacher/classes/${classId}/courses/${courseId}`),
};

// ─── Teacher Class → Parcours API ─────────────────────────────────────────

export const teacherParcoursClassApi = {
  listClassParcours: (classId: number) =>
    api.get<any[]>(`/api/teacher/classes/${classId}/parcours`),

  assignParcours: (classId: number, parcoursId: number) =>
    api.post<any>(`/api/teacher/classes/${classId}/parcours`, { parcours_id: parcoursId }),

  removeParcours: (classId: number, parcoursId: number) =>
    api.delete<void>(`/api/teacher/classes/${classId}/parcours/${parcoursId}`),
};

// ─── Teacher Sales API ─────────────────────────────────────────────────────

export const teacherSalesApi = {
  mySales: () => api.get<any>("/api/courses/my-sales"),
};

// ─── Teacher My Courses API ────────────────────────────────────────────────

export const teacherMyCoursesApi = {
  listMyCourses: () => api.get<any[]>("/api/courses/my-courses"),
  listCatalog: () => api.get<any[]>("/api/courses"),
  createCourse: (data: {
    title: string;
    description?: string;
    category_cible?: string;
    niveau_scolaire?: string;
    category?: string;
  }) => api.post<any>("/api/courses", data),
};

// ─── Student Search API ────────────────────────────────────────────────────

export const studentSearchApi = {
  search: (query: string) =>
    api.get<any[]>(`/api/teacher/students/search?q=${encodeURIComponent(query)}`),
  addToClass: (classId: number, studentId: number) =>
    api.post<void>(`/api/teacher/classes/${classId}/students`, { student_id: studentId }),
};

// ─── Teacher Student Progress API ──────────────────────────────────────────

export interface StudentProgress {
  student_id: number;
  student_name: string | null;
  student_email: string | null;
  progress_percent: number;
  courses_enrolled: number;
  total_class_courses: number;
  last_quiz_score: number | null;
  last_quiz_passed: boolean | null;
  last_quiz_at: string | null;
  pack_tier: string | null;
  pack_label: string;
  pack_status: "ok" | "expired" | "quota_exceeded" | "none";
  pack_expiry: string | null;
}

export const teacherProgressApi = {
  getClassProgress: (classId: number) =>
    api.get<StudentProgress[]>(`/api/teacher/classes/${classId}/students/progress`),
};

// ─── Teacher Wallet API ─────────────────────────────────────────────────────

export const teacherWalletApi = {
  balance: () => api.get<any>("/api/wallet/balance"),
  history: (page = 1, pageSize = 20) =>
    api.get<any>(`/api/wallet/history?page=${page}&page_size=${pageSize}`),
};

// ─── Backward compat aliases ───────────────────────────────────────────────

export const adminTeacherClasses = teacherClassesApi;
