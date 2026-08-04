import { useState, useEffect } from "react";
import { useAuthStore } from "../../../store/authStore";
import { 
  Search,
  BookOpen,
  Users,
  CheckCircle,
  XCircle,
  Trash2,
  Eye,
  Video,
  FileText,
  Clock,
  X,
  Loader2,
  GraduationCap
} from "lucide-react";

const API_URL = "";

interface Course {
  id: number;
  title: string;
  description: string;
  status: string;
  price_tokens: number;
  price_dt: number;
  teacher_id: number;
  teacher_name: string;
  modules_count: number;
  lessons_count: number;
  students_enrolled: number;
  created_at: string;
  is_published: boolean;
}

interface Enrollment {
  id: number;
  student_name: string;
  student_email: string;
  progress: number;
  enrolled_at: string;
}

export default function ContentModerationView() {
  const { token } = useAuthStore();
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<"all" | "pending" | "published" | "rejected">("all");
  const [processing, setProcessing] = useState(false);

  const [selectedCourse, setSelectedCourse] = useState<Course | null>(null);
  const [enrollments, setEnrollments] = useState<Enrollment[]>([]);
  const [showEnrollments, setShowEnrollments] = useState(false);

  useEffect(() => {
    if (token) {
      fetchCourses();
    }
  }, [token, statusFilter]);

  const fetchCourses = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const params = statusFilter !== "all" ? `?status=${statusFilter}` : "";
      const res = await fetch(`${API_URL}/api/admin/courses${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        // Transform data to match expected format
        setCourses(data.map((c: any) => ({
          id: c.id,
          title: c.title,
          description: c.description,
          status: c.status,
          price_tokens: c.price_tokens,
          price_dt: c.price_dt,
          teacher_id: c.teacher_id,
          teacher_name: c.author_name || c.teacher_name || "Unknown",
          modules_count: c.modules_count || 0,
          lessons_count: c.lessons_count || 0,
          students_enrolled: c.students_enrolled || 0,
          created_at: c.created_at,
          is_published: c.is_published,
        })));
      }
    } catch (err) {
      console.error(err);
      setCourses([]);
    }
    setLoading(false);
  };

  const approveCourse = async (courseId: number) => {
    if (!token) return;
    setProcessing(true);
    try {
      const res = await fetch(`${API_URL}/api/admin/courses/${courseId}`, {
        method: "PUT",
        headers: { 
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}` 
        },
        body: JSON.stringify({ status: "published", is_published: true }),
      });
      if (res.ok) fetchCourses();
    } catch (err) {
      console.error(err);
    }
    setProcessing(false);
  };

  const rejectCourse = async (courseId: number) => {
    if (!token || !confirm("Êtes-vous sûr de vouloir rejeter ce cours?")) return;
    setProcessing(true);
    try {
      const res = await fetch(`${API_URL}/api/admin/courses/${courseId}`, {
        method: "PUT",
        headers: { 
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}` 
        },
        body: JSON.stringify({ status: "rejected", is_published: false }),
      });
      if (res.ok) fetchCourses();
    } catch (err) {
      console.error(err);
    }
    setProcessing(false);
  };

  const deleteCourse = async (courseId: number) => {
    if (!confirm("ATTENTION: Cette action est irréversible. Voulez-vous vraiment supprimer?")) return;
    setProcessing(true);
    try {
      const res = await fetch(`${API_URL}/api/admin/courses/${courseId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) fetchCourses();
    } catch (err) {
      console.error(err);
    }
    setProcessing(false);
  };

  const toggleVisibility = async (courseId: number, currentStatus: boolean) => {
    if (!token) return;
    setProcessing(true);
    try {
      const res = await fetch(`${API_URL}/api/admin/courses/${courseId}`, {
        method: "PUT",
        headers: { 
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}` 
        },
        body: JSON.stringify({ is_published: !currentStatus }),
      });
      if (res.ok) fetchCourses();
    } catch (err) {
      console.error(err);
    }
    setProcessing(false);
  };

  const viewEnrollments = async (course: Course) => {
    setSelectedCourse(course);
    if (!token) return;
    try {
      const res = await fetch(`${API_URL}/api/admin/courses/${course.id}/enrollments`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setEnrollments(data);
      }
    } catch (err) {
      console.error(err);
    }
    setShowEnrollments(true);
  };

  const filteredCourses = courses.filter(c =>
    search === "" || 
    c.title?.toLowerCase().includes(search.toLowerCase()) ||
    c.teacher_name?.toLowerCase().includes(search.toLowerCase())
  );

  const stats = {
    total: courses.length,
    pending: courses.filter(c => c.status === "pending").length,
    published: courses.filter(c => c.status === "published").length,
    rejected: courses.filter(c => c.status === "rejected").length,
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-3xl p-8 shadow-sm border border-black/5">
        <h1 className="text-3xl font-[300] text-navy">
          Content & <span className="italic text-orange">Academy</span>
        </h1>
        <p className="text-gray mt-2">Gérez les cours et formations</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-blue-50 to-cream rounded-2xl p-6">
          <div className="text-3xl font-[300] text-navy">{stats.total}</div>
          <div className="text-sm text-gray">Total Cours</div>
        </div>
        <div className="bg-gradient-to-br from-yellow-50 to-cream rounded-2xl p-6">
          <div className="text-3xl font-[300] text-yellow-700">{stats.pending}</div>
          <div className="text-sm text-gray">En attente</div>
        </div>
        <div className="bg-gradient-to-br from-green-50 to-cream rounded-2xl p-6">
          <div className="text-3xl font-[300] text-green-700">{stats.published}</div>
          <div className="text-sm text-gray">Publiés</div>
        </div>
        <div className="bg-gradient-to-br from-red-50 to-cream rounded-2xl p-6">
          <div className="text-3xl font-[300] text-red-700">{stats.rejected}</div>
          <div className="text-sm text-gray">Rejetés</div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
        <div className="flex flex-wrap gap-4">
          <div className="flex-1 min-w-[200px]">
            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full ps-12 pe-4 py-3 bg-cream-m rounded-xl border border-black/5"
                placeholder="Rechercher un cours..."
              />
            </div>
          </div>
          <div className="flex gap-2">
            {(["all", "pending", "published", "rejected"] as const).map((f) => (
              <button
                key={f}
                onClick={() => setStatusFilter(f)}
                className={`px-4 py-2 rounded-xl text-sm font-medium capitalize ${
                  statusFilter === f
                    ? "bg-orange text-white"
                    : "bg-cream-m text-gray hover:bg-cream"
                }`}
              >
                {f}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Pending UGC */}
      {stats.pending > 0 && statusFilter !== "published" && statusFilter !== "rejected" && (
        <div className="bg-yellow-50 rounded-2xl p-6 border-2 border-yellow-200">
          <div className="flex items-center gap-2 mb-4">
            <Clock className="w-5 h-5 text-yellow-600" />
            <h2 className="text-lg font-semibold text-yellow-800">En attente de modération</h2>
            <span className="bg-yellow-200 text-yellow-800 text-sm px-3 py-1 rounded-full">
              {stats.pending}
            </span>
          </div>
          <div className="grid gap-4">
            {courses.filter(c => c.status === "pending").slice(0, 3).map((course) => (
              <div key={course.id} className="bg-white rounded-xl p-4 border border-yellow-200">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-semibold text-navy">{course.title}</h3>
                    <p className="text-sm text-gray line-clamp-1">{course.description}</p>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => approveCourse(course.id)}
                      className="flex items-center gap-1 px-4 py-2 bg-green-500 text-white rounded-lg text-sm"
                    >
                      <CheckCircle className="w-4 h-4" /> Approuver
                    </button>
                    <button
                      onClick={() => rejectCourse(course.id)}
                      className="flex items-center gap-1 px-4 py-2 bg-red-500 text-white rounded-lg text-sm"
                    >
                      <XCircle className="w-4 h-4" /> Rejeter
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Course List */}
      <div className="space-y-4">
        {loading ? (
          <div className="bg-white rounded-3xl p-12 text-center">
            <Loader2 className="w-8 h-8 mx-auto animate-spin text-orange" />
          </div>
        ) : filteredCourses.length === 0 ? (
          <div className="bg-white rounded-3xl p-12 text-center text-gray">
            <BookOpen className="w-16 h-16 mx-auto mb-4 opacity-20" />
            <p className="text-lg">Aucun cours trouvé</p>
          </div>
        ) : (
          filteredCourses.map((course) => (
            <div key={course.id} className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-semibold text-navy">{course.title}</h3>
                    <span className={`px-2 py-0.5 text-xs rounded-full ${
                      course.status === "published" ? "bg-green-100 text-green-700" :
                      course.status === "pending" ? "bg-yellow-100 text-yellow-700" :
                      "bg-red-100 text-red-700"
                    }`}>
                      {course.status === "pending" ? "En attente" : 
                       course.status === "published" ? "Publié" : "Rejeté"}
                    </span>
                    {!course.is_published && course.status === "published" && (
                      <span className="px-2 py-0.5 text-xs rounded-full bg-gray-100 text-gray-600">
                        Non visible
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray mb-3 line-clamp-2">{course.description}</p>
                  <div className="flex items-center gap-6 text-sm text-gray">
                    <span className="flex items-center gap-1">
                      <Users className="w-4 h-4" />
                      {course.teacher_name}
                    </span>
                    <span>{course.modules_count} modules</span>
                    <span>{course.lessons_count} leçons</span>
                    <span className="text-orange font-medium">{course.price_tokens} Tokens</span>
                  </div>
                </div>
                <div className="flex flex-col gap-2">
                  <div className="flex gap-2">
                    {course.status === "pending" && (
                      <>
                        <button onClick={() => approveCourse(course.id)} className="p-2 bg-green-500 text-white rounded-lg">
                          <CheckCircle className="w-4 h-4" />
                        </button>
                        <button onClick={() => rejectCourse(course.id)} className="p-2 bg-red-500 text-white rounded-lg">
                          <XCircle className="w-4 h-4" />
                        </button>
                      </>
                    )}
                    <button
                      onClick={() => toggleVisibility(course.id, course.is_published)}
                      className={`p-2 rounded-lg ${
                        course.is_published ? "bg-gray-100 text-gray-600" : "bg-green-100 text-green-600"
                      }`}
                      title={course.is_published ? "Masquer" : "Publier"}
                    >
                      {course.is_published ? <Eye className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                    {course.students_enrolled > 0 && (
                      <button
                        onClick={() => viewEnrollments(course)}
                        className="p-2 bg-blue-100 text-blue-600 rounded-lg"
                      >
                        <Users className="w-4 h-4" />
                      </button>
                    )}
                    <button
                      onClick={() => deleteCourse(course.id)}
                      className="p-2 bg-red-100 text-red-600 rounded-lg"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Enrollments Modal */}
      {showEnrollments && selectedCourse && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-3xl max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="p-8">
              <div className="flex justify-between items-center mb-6">
                <div>
                  <h2 className="text-2xl font-semibold text-navy">Étudiants inscrits</h2>
                  <p className="text-gray">{selectedCourse.title}</p>
                </div>
                <button onClick={() => setShowEnrollments(false)} className="p-2 hover:bg-cream rounded-lg">
                  <X className="w-5 h-5" />
                </button>
              </div>
              <div className="space-y-3">
                {enrollments.map((e) => (
                  <div key={e.id} className="flex items-center gap-4 p-4 bg-cream-m rounded-xl">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-r from-orange to-orange-l flex items-center justify-center text-white font-medium">
                      {e.student_name.charAt(0)}
                    </div>
                    <div className="flex-1">
                      <div className="font-medium">{e.student_name}</div>
                      <div className="text-sm text-gray">{e.student_email}</div>
                    </div>
                    <div className="text-end">
                      <div className="flex items-center gap-2 mb-1">
                        <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div className="h-full bg-orange rounded-full" style={{ width: `${e.progress}%` }} />
                        </div>
                        <span className="text-sm font-medium">{e.progress}%</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}