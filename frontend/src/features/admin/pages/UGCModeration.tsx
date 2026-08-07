import { useState, useEffect } from "react";
import { useAuthStore } from "../../../store/authStore";
import { Check, X, Eye, User, Clock, Trash2 } from "lucide-react";
import { adminCourseModeration } from "../../../api";
import { Button, Modal, EmptyState } from "../../../components/ui";

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
}

export default function UGCModeration() {
  const { token } = useAuthStore();
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"all" | "pending" | "published" | "rejected">("all");
  const [selectedCourse, setSelectedCourse] = useState<Course | null>(null);

  useEffect(() => {
    fetchCourses();
  }, [token, filter]);

  const fetchCourses = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const data = await adminCourseModeration.list(filter === "all" ? undefined : filter);
      setCourses(Array.isArray(data) ? data : (data as any).items || []);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const approveCourse = async (id: number) => {
    if (!token) return;
    try {
      await adminCourseModeration.setStatus(id, "published");
      fetchCourses();
    } catch (err) {
      console.error(err);
    }
  };

  const rejectCourse = async (id: number) => {
    if (!token) return;
    try {
      await adminCourseModeration.setStatus(id, "rejected");
      fetchCourses();
    } catch (err) {
      console.error(err);
    }
  };

  const deleteCourse = async (id: number) => {
    if (!token || !confirm("Êtes-vous sûr de vouloir supprimer ce cours?")) return;
    try {
      await adminCourseModeration.delete(id);
      fetchCourses();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-3xl p-8 shadow-sm border border-black/5">
        <h1 className="text-3xl font-[300] text-navy">
          UGC <span className="italic text-orange">Moderation</span>
        </h1>
        <p className="text-gray mt-2">
          Modérez les cours générés par les enseignants
        </p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-3xl p-6 shadow-sm border border-black/5">
        <div className="flex gap-2 flex-wrap">
          {(["all", "pending", "published", "rejected"] as const).map((f) => (
            <Button
              key={f}
              variant={filter === f ? "primary" : "ghost"}
              size="sm"
              onClick={() => setFilter(f)}
              className="capitalize"
            >
              {f}
              {f === "pending" && courses.filter((c) => c.status === "pending").length > 0 && (
                <span className="ml-2 bg-white text-orange text-xs px-2 py-0.5 rounded-full">
                  {courses.filter((c) => c.status === "pending").length}
                </span>
              )}
            </Button>
          ))}
        </div>
      </div>

      {/* Course List */}
      <div className="grid gap-4">
        {loading ? (
          <div className="bg-white rounded-3xl p-12 text-center text-gray">
            Chargement...
          </div>
        ) : courses.length === 0 ? (
          <div className="bg-white rounded-3xl">
            <EmptyState title="Aucun cours trouvé" />
          </div>
        ) : (
          courses.map((course) => (
            <div
              key={course.id}
              className="bg-white rounded-2xl p-6 shadow-sm border border-black/5 hover:shadow-md transition-shadow"
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-semibold text-navy">{course.title}</h3>
                    <span
                      className={`px-2 py-0.5 text-xs rounded-full ${
                        course.status === "published"
                          ? "bg-green-100 text-green-700"
                          : course.status === "pending"
                          ? "bg-yellow-100 text-yellow-700"
                          : "bg-red-100 text-red-700"
                      }`}
                    >
                      {course.status}
                    </span>
                  </div>
                  <p className="text-sm text-gray mb-3">{course.description}</p>
                  <div className="flex items-center gap-6 text-sm text-gray">
                    <span className="flex items-center gap-1">
                      <User className="w-4 h-4" />
                      {course.teacher_name}
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-4 h-4" />
                      {new Date(course.created_at).toLocaleDateString("fr-FR")}
                    </span>
                    <span>{course.modules_count} modules</span>
                    <span>{course.lessons_count} leçons</span>
                    <span>{course.students_enrolled} étudiants</span>
                  </div>
                </div>
                <div className="text-end">
                  <div className="text-lg font-semibold text-navy mb-1">
                    {course.price_tokens} tokens
                  </div>
                  <div className="text-sm text-gray mb-3">
                    {course.price_dt} DT
                  </div>
                  <div className="flex gap-2">
                    <Button variant="ghost" size="sm" onClick={() => setSelectedCourse(course)} title="Voir">
                      <Eye className="w-4 h-4 text-gray" />
                    </Button>
                    {course.status === "pending" && (
                      <>
                        <Button variant="ghost" size="sm" onClick={() => approveCourse(course.id)} title="Approuver">
                          <Check className="w-4 h-4 text-green-700" />
                        </Button>
                        <Button variant="ghost" size="sm" onClick={() => rejectCourse(course.id)} title="Rejeter">
                          <X className="w-4 h-4 text-red-700" />
                        </Button>
                      </>
                    )}
                    {(course.status === "published" || course.status === "rejected") && (
                      <Button variant="ghost" size="sm" onClick={() => deleteCourse(course.id)} title="Supprimer">
                        <Trash2 className="w-4 h-4 text-red-700" />
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Course Detail Modal */}
      <Modal open={!!selectedCourse} onClose={() => setSelectedCourse(null)}
        title={selectedCourse?.title} maxWidth="max-w-2xl">
        {selectedCourse && (
          <div className="max-h-[80vh] overflow-y-auto">
            <div className="prose max-w-none mb-6">
              <p className="text-gray">{selectedCourse.description}</p>
            </div>
            <div className="grid grid-cols-4 gap-4 mb-6">
              <div className="bg-cream-m rounded-xl p-4 text-center">
                <div className="text-2xl font-semibold text-navy">
                  {selectedCourse.modules_count}
                </div>
                <div className="text-xs text-gray">Modules</div>
              </div>
              <div className="bg-cream-m rounded-xl p-4 text-center">
                <div className="text-2xl font-semibold text-navy">
                  {selectedCourse.lessons_count}
                </div>
                <div className="text-xs text-gray">Leçons</div>
              </div>
              <div className="bg-cream-m rounded-xl p-4 text-center">
                <div className="text-2xl font-semibold text-navy">
                  {selectedCourse.students_enrolled}
                </div>
                <div className="text-xs text-gray">Étudiants</div>
              </div>
              <div className="bg-cream-m rounded-xl p-4 text-center">
                <div className="text-2xl font-semibold text-orange">
                  {selectedCourse.price_tokens}
                </div>
                <div className="text-xs text-gray">Tokens</div>
              </div>
            </div>
            {selectedCourse.status === "pending" && (
              <div className="flex gap-4">
                <Button variant="success" className="flex-1" onClick={() => {
                  approveCourse(selectedCourse.id);
                  setSelectedCourse(null);
                }}>
                  Approuver
                </Button>
                <Button variant="danger" className="flex-1" onClick={() => {
                  rejectCourse(selectedCourse.id);
                  setSelectedCourse(null);
                }}>
                  Rejeter
                </Button>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
}