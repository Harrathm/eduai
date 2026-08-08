import { useState, useEffect } from "react";
import { useAuthStore } from "../../../store/authStore";
import { BookOpen, CheckCircle, XCircle, Clock, AlertTriangle, Eye, RefreshCw, Filter } from "lucide-react";
import { Button, Spinner } from "@/components/ui";
import { pedagogicalAdmin } from "../../../api";

interface Course {
  id: number;
  title: string;
  description: string;
  pedagogical_status: string;
  owner_type: string;
  validated_by?: number;
  validated_at?: string;
  school_id?: number;
}

export default function PedagogicalAdminPage() {
  const { token, user } = useAuthStore();
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("pending_review");
  const [processing, setProcessing] = useState<number | null>(null);
  const [toast, setToast] = useState<{ show: boolean; message: string; type: "success" | "error" }>({
    show: false, message: "", type: "success"
  });

  useEffect(() => {
    fetchCourses();
  }, [token, filter]);

  const fetchCourses = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const data = await pedagogicalAdmin.listPending();
      setCourses(Array.isArray(data) ? data : (data as any).courses || (data as any).items || []);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const reviewCourse = async (courseId: number, action: "approved_for_b2b" | "needs_revision") => {
    if (!token) return;
    setProcessing(courseId);
    try {
      await pedagogicalAdmin.review(courseId, action);
      const messages: Record<string, string> = {
        approved_for_b2b: "Cours approuvé pour la distribution B2B",
        needs_revision: "Révision demandée",
      };
      setToast({ show: true, message: messages[action], type: "success" });
      fetchCourses();
    } catch (err) {
      setToast({ show: true, message: "Erreur de connexion", type: "error" });
    }
    setProcessing(null);
  };

  const filteredCourses = courses.filter(c => filter === "all" || c.pedagogical_status === filter);

  const statusBadge = (status: string) => {
    const colors: Record<string, string> = {
      draft: "bg-gray-100 text-gray-600",
      pending_review: "bg-yellow-100 text-yellow-700",
      rejected: "bg-red-100 text-red-700",
      approved_for_platform: "bg-blue-100 text-blue-700",
      approved_for_b2b: "bg-green-100 text-green-700",
      revision_requested: "bg-orange-100 text-orange-700",
    };
    const labels: Record<string, string> = {
      draft: "Brouillon",
      pending_review: "En revue",
      rejected: "Rejeté",
      approved_for_platform: "Approuvé",
      approved_for_b2b: "Approuvé B2B",
      revision_requested: "Révision",
    };
    return (
      <span className={`px-2 py-1 text-xs rounded-full font-medium ${colors[status] || "bg-gray-100 text-gray-600"}`}>
        {labels[status] || status}
      </span>
    );
  };

  if (user?.role !== "pedagogical_admin") {
    return (
      <div className="space-y-6">
        <div className="bg-white rounded-3xl p-8 shadow-sm border border-black/5">
          <h1 className="text-3xl font-[300] text-navy">
            Review <span className="italic text-orange">Pédagogique</span>
          </h1>
        </div>
        <div className="bg-white rounded-2xl p-12 shadow-sm border border-black/5 text-center">
          <AlertTriangle className="w-16 h-16 text-yellow-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-700 mb-2">Accès restreint</h3>
          <p className="text-gray-500">Cette page est réservée aux responsables pédagogiques plateforme.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-3xl p-8 shadow-sm border border-black/5">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-[300] text-navy">
              Review <span className="italic text-orange">Pédagogique</span>
            </h1>
            <p className="text-gray mt-2">Validez ou rejetez les cours soumis</p>
          </div>
          <Button variant="ghost" size="sm" onClick={fetchCourses} disabled={loading} loading={loading}>
            <RefreshCw className="w-5 h-5 text-gray" />
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-2xl p-4 shadow-sm border border-black/5 flex items-center gap-4">
        <Filter className="w-5 h-5 text-gray" />
        <select value={filter} onChange={e => setFilter(e.target.value)}
          className="px-4 py-3 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none">
          <option value="pending_review">En attente de review</option>
          <option value="all">Tous les statuts</option>
          <option value="approved_for_platform">Approuvés (Plateforme)</option>
          <option value="approved_for_b2b">Approuvés (B2B)</option>
          <option value="rejected">Rejetés</option>
          <option value="revision_requested">Révision demandée</option>
        </select>
      </div>

      {/* Course List */}
      <div className="space-y-4">
        {loading ? (
          <div className="bg-white rounded-3xl p-12 text-center"><Spinner size="lg" /></div>
        ) : filteredCourses.length === 0 ? (
          <div className="bg-white rounded-3xl p-12 text-center text-gray">
            <BookOpen className="w-16 h-16 mx-auto mb-4 opacity-30" />
            <p>Aucun cours à reviewer</p>
          </div>
        ) : (
          filteredCourses.map(course => (
            <div key={course.id} className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <h3 className="text-lg font-semibold text-navy">{course.title}</h3>
                    {statusBadge(course.pedagogical_status)}
                    <span className={`px-2 py-1 text-xs rounded-full font-medium ${
                      course.owner_type === "independent_teacher" ? "bg-purple-100 text-purple-700" :
                      course.owner_type === "eduai_catalog" ? "bg-blue-100 text-blue-700" :
                      "bg-gray-100 text-gray-600"
                    }`}>
                      {course.owner_type === "independent_teacher" ? "Indépendant" :
                       course.owner_type === "eduai_catalog" ? "Catalogue EDUAI" : "École"}
                    </span>
                  </div>
                  <p className="text-sm text-gray mt-1">{course.description}</p>
                  {course.validated_at && (
                    <p className="text-xs text-gray mt-2">
                      Validé le {new Date(course.validated_at).toLocaleDateString("fr-FR")}
                    </p>
                  )}
                </div>
                
                {course.pedagogical_status === "pending_review" && (
                  <div className="flex items-center gap-2">
                    <Button
                      variant="success"
                      size="sm"
                      onClick={() => reviewCourse(course.id, "approved_for_b2b")}
                      disabled={processing === course.id}
                    >
                      <CheckCircle className="w-4 h-4" />
                      Approuver B2B
                    </Button>
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => reviewCourse(course.id, "needs_revision")}
                      disabled={processing === course.id}
                    >
                      <Clock className="w-4 h-4" />
                      Demander révision
                    </Button>
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {toast.show && (
        <div className={`fixed top-6 right-6 z-50 px-6 py-4 rounded-xl shadow-lg text-white ${toast.type === "success" ? "bg-green-500" : "bg-red-500"}`}>
          {toast.message}
        </div>
      )}
    </div>
  );
}
