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

// ─── Teacher Classes API ────────────────────────────────────────────────────

export const teacherClassesApi = {
  list: () => api.get<{ items: TeacherClass[] }>("/api/teacher/classes"),

  create: (data: { name: string; description?: string }) =>
    api.post<TeacherClass>("/api/teacher/classes", data),

  delete: (classId: number) =>
    api.delete<void>(`/api/teacher/classes/${classId}`),

  listStudents: (classId: number) =>
    api.get<{ items: ClassStudent[] }>(`/api/teacher/classes/${classId}/students`),

  addStudent: (classId: number, studentId: number) =>
    api.post<void>(`/api/teacher/classes/${classId}/students/${studentId}`),

  removeStudent: (classId: number, studentId: number) =>
    api.delete<void>(`/api/teacher/classes/${classId}/students/${studentId}`),
};

// ─── Teacher Courses API ────────────────────────────────────────────────────

export const teacherCoursesApi = {
  listMyCourses: () => api.get<any[]>("/api/teacher/courses"),

  listClassCourses: (classId: number) =>
    api.get<any[]>(`/api/teacher/classes/${classId}/courses`),

  assignCourse: (classId: number, courseId: number) =>
    api.post<void>(`/api/teacher/classes/${classId}/courses/${courseId}`),

  removeCourse: (classId: number, courseId: number) =>
    api.delete<void>(`/api/teacher/classes/${classId}/courses/${courseId}`),
};

// ─── Teacher Sales API ─────────────────────────────────────────────────────

export const teacherSalesApi = {
  mySales: () => api.get<any>("/api/courses/my-sales"),
};

// ─── Teacher My Courses API ────────────────────────────────────────────────

export const teacherMyCoursesApi = {
  listMyCourses: () => api.get<any[]>("/api/courses/my-courses"),
  listCatalog: () => api.get<any[]>("/api/courses"),
};

// ─── Student Search API ────────────────────────────────────────────────────

export const studentSearchApi = {
  search: (query: string) =>
    api.get<any[]>(`/api/teacher/students/search?q=${encodeURIComponent(query)}`),
  addToClass: (classId: number, studentId: number) =>
    api.post<void>(`/api/teacher/classes/${classId}/students`, { student_id: studentId }),
};

// ─── Teacher Wallet API ─────────────────────────────────────────────────────

export const teacherWalletApi = {
  balance: () => api.get<any>("/api/wallet/balance"),
  history: (page = 1, pageSize = 20) =>
    api.get<any>(`/api/wallet/history?page=${page}&page_size=${pageSize}`),
};
