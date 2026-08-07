import { useState, useEffect, useCallback } from "react";
import { School, BookOpen, Users, CheckCircle, XCircle, Plus, Loader2, AlertCircle, RefreshCw, Search, Ban } from "lucide-react";
import { Button } from "../../../components/ui";
import { tokenStorage } from "../../../utils/tokenStorage";

const API_URL = "";

function getToken(): string | null {
  return tokenStorage.getToken();
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...((options.headers as Record<string, string>) || {}),
  };
  const res = await fetch(`${API_URL}${path}`, { ...options, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

interface GrantedCourse {
  course_id: number;
  course_title: string;
  course_slug: string;
  course_category: string | null;
  course_level: string | null;
  purchased_at: string | null;
  is_active: boolean;
  price_paid_dt: number;
  granted_by_admin_id: number | null;
  enrolled_users_count: number;
}

interface SchoolAccess {
  school_id: number;
  school_name: string;
  school_slug: string;
  total_users: number;
  student_count: number;
  teacher_count: number;
  granted_courses: GrantedCourse[];
}

interface CourseAccessResponse {
  total_schools: number;
  academy_courses_count: number;
  schools: SchoolAccess[];
}

interface AvailableCourse {
  id: number;
  title: string;
  slug: string;
  category: string | null;
  level: string | null;
  price_dt: number;
  price_tokens: number;
  total_modules: number;
  total_lessons: number;
}

export default function SchoolCourseDistribution() {
  const [data, setData] = useState<CourseAccessResponse | null>(null);
  const [availableCourses, setAvailableCourses] = useState<AvailableCourse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [granting, setGranting] = useState(false);
  const [selectedSchoolId, setSelectedSchoolId] = useState<number | "">("");
  const [selectedCourseId, setSelectedCourseId] = useState<number | "">("");
  const [toast, setToast] = useState<{ show: boolean; message: string; type: "success" | "error" }>({
    show: false, message: "", type: "success",
  });

  const showToast = (message: string, type: "success" | "error" = "success") => {
    setToast({ show: true, message, type });
    setTimeout(() => setToast({ show: false, message: "", type: "success" }), 3500);
  };

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [accessData, coursesData] = await Promise.all([
        request<CourseAccessResponse>("/api/admin/courses/schools/course-access"),
        request<{ courses: AvailableCourse[] }>("/api/admin/courses/schools/course-access/available-courses"),
      ]);
      setData(accessData);
      setAvailableCourses(coursesData.courses);
    } catch (err: any) {
      setError(err.message || "Failed to load data");
    }
    setLoading(false);
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleGrant = async () => {
    if (!selectedSchoolId || !selectedCourseId) return;
    setGranting(true);
    try {
      const res = await request<{ ok: boolean; action: string; access_id: number }>(
        `/api/admin/courses/schools/${selectedSchoolId}/grant-course`,
        { method: "POST", body: JSON.stringify({ course_id: selectedCourseId }) }
      );
      showToast(`Course ${res.action} successfully`);
      setSelectedSchoolId("");
      setSelectedCourseId("");
      fetchData();
    } catch (err: any) {
      showToast(err.message || "Failed to grant", "error");
    }
    setGranting(false);
  };

  const handleRevoke = async (schoolId: number, courseId: number, courseTitle: string) => {
    if (!window.confirm(`Revoke "${courseTitle}" from this school?`)) return;
    try {
      await request(`/api/admin/courses/schools/${schoolId}/revoke-course/${courseId}`, { method: "DELETE" });
      showToast(`Access revoked for "${courseTitle}"`);
      fetchData();
    } catch (err: any) {
      showToast(err.message || "Failed to revoke", "error");
    }
  };

  const filteredSchools = data?.schools.filter(
    s => s.school_name.toLowerCase().includes(search.toLowerCase()) || s.school_slug.toLowerCase().includes(search.toLowerCase())
  ) || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-display font-light text-navy">
            B2B Course <span className="italic text-orange">Distribution</span>
          </h1>
          <p className="text-gray text-sm mt-1">
            {data
              ? `${data.total_schools} schools · ${data.academy_courses_count} academy courses`
              : "Manage which schools can access which academy courses"}
          </p>
        </div>
        <Button variant="ghost" size="md" onClick={fetchData}>
          <RefreshCw className={`w-5 h-5 text-gray ${loading ? "animate-spin" : ""}`} />
        </Button>
      </div>

      {error && (
        <div className="flex items-center gap-3 px-4 py-3 bg-red-50 text-red-600 rounded-xl text-sm">
          <AlertCircle className="w-5 h-5" />
          {error}
          <Button variant="ghost" size="sm" onClick={() => setError(null)} className="ml-auto text-red-400 hover:text-red-600">&times;</Button>
        </div>
      )}

      {/* Quick Grant Form */}
      <div className="bg-white rounded-2xl shadow-sm border border-black/5 p-5">
        <div className="flex items-center gap-2 mb-4">
          <Plus className="w-5 h-5 text-orange" />
          <h3 className="font-semibold text-navy">Quick Grant — Assign Academy Course to School</h3>
        </div>
        <div className="flex flex-wrap items-end gap-3">
          <div className="flex-1 min-w-[200px]">
            <label className="block text-xs font-medium text-gray mb-1">School</label>
            <select
              value={selectedSchoolId}
              onChange={e => setSelectedSchoolId(e.target.value ? Number(e.target.value) : "")}
              className="w-full px-4 py-2.5 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none focus:ring-2 focus:ring-orange/20"
            >
              <option value="">Select school...</option>
              {data?.schools.map(s => (
                <option key={s.school_id} value={s.school_id}>
                  {s.school_name} ({s.student_count} students)
                </option>
              ))}
            </select>
          </div>
          <div className="flex-1 min-w-[200px]">
            <label className="block text-xs font-medium text-gray mb-1">Academy Course</label>
            <select
              value={selectedCourseId}
              onChange={e => setSelectedCourseId(e.target.value ? Number(e.target.value) : "")}
              className="w-full px-4 py-2.5 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none focus:ring-2 focus:ring-orange/20"
            >
              <option value="">Select course...</option>
              {availableCourses.map(c => (
                <option key={c.id} value={c.id}>
                  {c.title} ({c.price_dt} DT)
                </option>
              ))}
            </select>
          </div>
          <Button
            variant="primary"
            size="md"
            onClick={handleGrant}
            disabled={granting || !selectedSchoolId || !selectedCourseId}
            loading={granting}
            className="px-6 py-2.5 flex items-center gap-2 shadow-sm whitespace-nowrap"
          >
            <Plus className="w-4 h-4" />
            {granting ? "Granting..." : "Grant to School"}
          </Button>
        </div>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray" />
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Filter schools by name..."
          className="w-full ps-11 pe-4 py-3 bg-white rounded-2xl shadow-sm border border-black/5 text-sm focus:outline-none focus:ring-2 focus:ring-orange/20"
        />
      </div>

      {/* Schools Grid */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 text-orange animate-spin" />
        </div>
      ) : (
        <div className="space-y-6">
          {filteredSchools.map(school => (
            <div key={school.school_id} className="bg-white rounded-2xl shadow-sm border border-black/5 overflow-hidden">
              {/* School Header */}
              <div className="px-6 py-4 border-b border-black/5 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-navy/5 flex items-center justify-center">
                    <School className="w-5 h-5 text-navy" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-navy">{school.school_name}</h3>
                    <p className="text-xs text-gray">
                      <Users className="w-3 h-3 inline me-1" />
                      {school.total_users} users ({school.student_count} students, {school.teacher_count} teachers)
                    </p>
                  </div>
                </div>
                <span className="text-xs text-gray font-mono">#{school.school_id}</span>
              </div>

              {/* Granted Courses */}
              <div className="px-6 py-4">
                {school.granted_courses.length === 0 ? (
                  <div className="text-sm text-gray py-6 text-center">
                    <Ban className="w-8 h-8 mx-auto mb-2 text-gray/40" />
                    No academy courses granted yet. Use the form above to assign courses.
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {school.granted_courses.map(course => (
                      <div
                        key={course.course_id}
                        className={`relative rounded-xl border-2 p-4 transition-all ${
                          course.is_active
                            ? "border-green-200 bg-green-50/30"
                            : "border-red-200 bg-red-50/30 opacity-70"
                        }`}
                      >
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <BookOpen className="w-4 h-4 text-navy-m" />
                            <span className="font-medium text-sm text-navy">{course.course_title}</span>
                          </div>
                          {course.is_active ? (
                            <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />
                          ) : (
                            <XCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
                          )}
                        </div>
                        <div className="flex items-center gap-2 flex-wrap text-xs text-gray mb-2">
                          {course.course_category && (
                            <span className="px-2 py-0.5 bg-orange/10 text-orange rounded-full">{course.course_category}</span>
                          )}
                          {course.course_level && (
                            <span className="px-2 py-0.5 bg-blue/10 text-blue rounded-full capitalize">{course.course_level}</span>
                          )}
                          {course.price_paid_dt > 0 && (
                            <span className="px-2 py-0.5 bg-green/10 text-green-700 rounded-full">{course.price_paid_dt} DT</span>
                          )}
                        </div>
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-gray">
                            <Users className="w-3 h-3 inline me-1" />
                            {course.enrolled_users_count} enrolled
                          </span>
                          <span className="text-gray/50">
                            {course.purchased_at ? new Date(course.purchased_at).toLocaleDateString("fr-TN") : "—"}
                          </span>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleRevoke(school.school_id, course.course_id, course.course_title)}
                          className="absolute top-2 right-2 p-1 text-gray/30 hover:text-red-500 transition-colors"
                          title="Revoke access"
                        >
                          <XCircle className="w-3.5 h-3.5" />
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}

          {filteredSchools.length === 0 && !loading && (
            <div className="text-center py-12 text-gray text-sm">
              {search ? `No schools matching "${search}"` : "No schools found"}
            </div>
          )}
        </div>
      )}

      {/* Toast */}
      {toast.show && (
        <div
          className={`fixed top-6 right-6 z-50 flex items-center gap-3 px-6 py-4 rounded-xl shadow-lg ${
            toast.type === "success" ? "bg-green-500" : "bg-red-500"
          } text-white`}
        >
          <span className="font-medium">{toast.message}</span>
        </div>
      )}
    </div>
  );
}
