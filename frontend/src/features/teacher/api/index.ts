const API_URL = import.meta.env.VITE_API_URL || "";

function authHeaders(token: string) {
  return { Authorization: `Bearer ${token}` };
}

export interface TeacherClass {
  id: number;
  teacher_id: number;
  school_id: number;
  teacher_name: string;
  school_name: string;
  name: string;
  description: string;
  code: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  courses_count: number;
  students_count: number;
}

export interface ClassCourse {
  id: number;
  class_id: number;
  course_id: number;
  course_title: string;
  assigned_at: string;
  is_active: boolean;
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

export interface Course {
  id: number;
  title: string;
  category: string;
  level: string;
  status: string;
  is_published: boolean;
  author_id: number;
}

export interface WalletBalance {
  user_id: number;
  total: number;
  pools: { pool: string; balance: number; expires_at: string | null }[];
}

export interface WalletTransaction {
  id: number;
  pool: string;
  amount: number;
  feature: string;
  expires_at: string | null;
  created_at: string;
}

// ─── Classes ──────────────────────────────────────────────────────
export async function listMyClasses(token: string): Promise<TeacherClass[]> {
  const res = await fetch(`${API_URL}/api/teacher/classes`, { headers: authHeaders(token) });
  if (!res.ok) throw new Error("Failed to list classes");
  return res.json();
}

export async function createClass(token: string, name: string, description?: string): Promise<TeacherClass> {
  const res = await fetch(`${API_URL}/api/teacher/classes`, {
    method: "POST",
    headers: { ...authHeaders(token), "Content-Type": "application/json" },
    body: JSON.stringify({ name, description }),
  });
  if (!res.ok) throw new Error("Failed to create class");
  return res.json();
}

export async function deleteClass(token: string, classId: number): Promise<void> {
  const res = await fetch(`${API_URL}/api/teacher/classes/${classId}`, {
    method: "DELETE",
    headers: authHeaders(token),
  });
  if (!res.ok) throw new Error("Failed to delete class");
}

export async function listClassCourses(token: string, classId: number): Promise<ClassCourse[]> {
  const res = await fetch(`${API_URL}/api/teacher/classes/${classId}/courses`, { headers: authHeaders(token) });
  if (!res.ok) throw new Error("Failed to list class courses");
  return res.json();
}

export async function assignCourse(token: string, classId: number, courseId: number): Promise<ClassCourse> {
  const res = await fetch(`${API_URL}/api/teacher/classes/${classId}/courses`, {
    method: "POST",
    headers: { ...authHeaders(token), "Content-Type": "application/json" },
    body: JSON.stringify({ course_id: courseId }),
  });
  if (!res.ok) throw new Error("Failed to assign course");
  return res.json();
}

export async function removeCourseFromClass(token: string, classId: number, courseId: number): Promise<void> {
  const res = await fetch(`${API_URL}/api/teacher/classes/${classId}/courses/${courseId}`, {
    method: "DELETE",
    headers: authHeaders(token),
  });
  if (!res.ok) throw new Error("Failed to remove course");
}

export async function listClassStudents(token: string, classId: number): Promise<ClassStudent[]> {
  const res = await fetch(`${API_URL}/api/teacher/classes/${classId}/students`, { headers: authHeaders(token) });
  if (!res.ok) throw new Error("Failed to list class students");
  return res.json();
}

export async function enrollStudent(token: string, classId: number, studentId: number): Promise<ClassStudent> {
  const res = await fetch(`${API_URL}/api/teacher/classes/${classId}/students`, {
    method: "POST",
    headers: { ...authHeaders(token), "Content-Type": "application/json" },
    body: JSON.stringify({ student_id: studentId }),
  });
  if (!res.ok) throw new Error("Failed to enroll student");
  return res.json();
}

export async function removeStudentFromClass(token: string, classId: number, studentId: number): Promise<void> {
  const res = await fetch(`${API_URL}/api/teacher/classes/${classId}/students/${studentId}`, {
    method: "DELETE",
    headers: authHeaders(token),
  });
  if (!res.ok) throw new Error("Failed to remove student");
}

// ─── Courses ──────────────────────────────────────────────────────
export async function listMyCourses(token: string): Promise<{ total: number; items: Course[] }> {
  const res = await fetch(`${API_URL}/api/courses/my-courses`, { headers: authHeaders(token) });
  if (!res.ok) throw new Error("Failed to list courses");
  return res.json();
}

// ─── Wallet ───────────────────────────────────────────────────────
export async function getWalletBalance(token: string): Promise<WalletBalance> {
  const res = await fetch(`${API_URL}/api/wallet/balance`, { headers: authHeaders(token) });
  if (!res.ok) throw new Error("Failed to get balance");
  return res.json();
}

export async function getWalletHistory(token: string, page = 1, pageSize = 20): Promise<{ total: number; transactions: WalletTransaction[] }> {
  const res = await fetch(`${API_URL}/api/wallet/history?page=${page}&page_size=${pageSize}`, { headers: authHeaders(token) });
  if (!res.ok) throw new Error("Failed to get history");
  return res.json();
}
