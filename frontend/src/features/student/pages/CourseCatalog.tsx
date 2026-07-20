import { useState, useEffect } from "react";
import { useAuthStore } from "../../../store/authStore";
import { Search, BookOpen, Clock, User, ShoppingCart, AlertCircle, CheckCircle, X } from "lucide-react";

const API_URL = "";

interface Course {
  id: number;
  title: string;
  description: string;
  teacher_name: string;
  duration_hours: number;
  price_tokens: number;
  price_dt: number;
  enrolled_count: number;
  price?: number;
  currency?: string;
  visibility?: string;
  pedagogical_status?: string;
  owner_type?: string;
}

interface Purchase {
  purchase_id: number;
  amount_paid: number;
  currency: string;
  platform_fee: number;
  teacher_revenue: number;
}

export default function StudentCourseCatalog() {
  const { token, user } = useAuthStore();
  const [courses, setCourses] = useState<Course[]>([]);
  const [myEnrollments, setMyEnrollments] = useState<number[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [purchasing, setPurchasing] = useState<number | null>(null);
  const [refundModal, setRefundModal] = useState<{ courseId: number; courseTitle: string } | null>(null);
  const [refundReason, setRefundReason] = useState("");
  const [refundLoading, setRefundLoading] = useState(false);
  const [toast, setToast] = useState<{ show: boolean; message: string; type: "success" | "error" }>({
    show: false, message: "", type: "success"
  });

  useEffect(() => {
    fetchCourses();
    fetchEnrollments();
  }, [token]);

  const fetchCourses = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/academy/courses`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setCourses(Array.isArray(data) ? data : data.items || []);
      }
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const fetchEnrollments = async () => {
    if (!token) return;
    try {
      const res = await fetch(`${API_URL}/api/learner/courses`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        const list = Array.isArray(data) ? data : data.items || [];
        setMyEnrollments(list.map((c: Course) => c.id));
      }
    } catch (err) {
      console.error(err);
    }
  };

  const purchaseCourse = async (courseId: number) => {
    if (!token) return;
    setPurchasing(courseId);
    try {
      const res = await fetch(`${API_URL}/api/courses/${courseId}/purchase`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data: Purchase = await res.json();
        setToast({
          show: true,
          message: `Achat réussi! Montant: ${data.amount_paid} ${data.currency}`,
          type: "success"
        });
        fetchEnrollments();
        fetchCourses();
      } else {
        const err = await res.json();
        setToast({
          show: true,
          message: err.detail || "Échec de l'achat",
          type: "error"
        });
      }
    } catch (err) {
      setToast({
        show: true,
        message: "Erreur lors de l'achat",
        type: "error"
      });
    }
    setPurchasing(null);
  };

  const requestRefund = async () => {
    if (!token || !refundModal || !refundReason.trim()) return;
    setRefundLoading(true);
    try {
      const res = await fetch(
        `${API_URL}/api/courses/${refundModal.courseId}/refund-request?reason=${encodeURIComponent(refundReason)}`,
        { method: "POST", headers: { Authorization: `Bearer ${token}` } }
      );
      if (res.ok) {
        const data = await res.json();
        setToast({
          show: true,
          message: data.message || "Demande de remboursement envoyée",
          type: "success"
        });
        setRefundModal(null);
        setRefundReason("");
        fetchEnrollments();
      } else {
        const err = await res.json();
        setToast({
          show: true,
          message: err.detail || "Échec de la demande",
          type: "error"
        });
      }
    } catch (err) {
      setToast({
        show: true,
        message: "Erreur lors de la demande",
        type: "error"
      });
    }
    setRefundLoading(false);
  };

  const filtered = courses.filter((c) =>
    c.title.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-3xl p-8 shadow-sm border border-black/5">
        <h1 className="text-3xl font-[300] text-navy">
          Course <span className="italic text-orange">Catalog</span>
        </h1>
        <p className="text-gray mt-2">Parcourez et inscrivez-vous aux cours</p>
      </div>

      {/* Search */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
        <div className="relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-12 pr-4 py-3 bg-cream-m rounded-xl border border-black/5 focus:border-orange focus:outline-none"
            placeholder="Rechercher un cours..."
          />
        </div>
      </div>

      {/* Course Grid */}
      <div className="grid gap-4">
        {loading ? (
          <div className="bg-white rounded-3xl p-12 text-center text-gray">
            Chargement...
          </div>
        ) : filtered.length === 0 ? (
          <div className="bg-white rounded-3xl p-12 text-center text-gray">
            Aucun cours trouvé
          </div>
        ) : (
          filtered.map((course) => {
            const isEnrolled = myEnrollments.includes(course.id);
            const isFree = !course.price || course.price === 0;
            const canPurchase = !isEnrolled && !isFree;

            return (
              <div
                key={course.id}
                className="bg-white rounded-2xl p-6 shadow-sm border border-black/5 hover:shadow-md transition-shadow"
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="text-lg font-semibold text-navy">{course.title}</h3>
                      {course.owner_type === "independent_teacher" && (
                        <span className="px-2 py-0.5 bg-purple-100 text-purple-700 text-xs rounded-full">
                          Indépendant
                        </span>
                      )}
                      {course.owner_type === "eduai_catalog" && (
                        <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full">
                          Catalogue EDUAI
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray mt-1">{course.description}</p>
                    <div className="flex items-center gap-6 text-sm text-gray mt-2">
                      <span className="flex items-center gap-1">
                        <User className="w-4 h-4" />
                        {course.teacher_name}
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        {course.duration_hours}h
                      </span>
                    </div>
                  </div>
                  <div className="text-right">
                    {isFree ? (
                      <div className="text-lg font-semibold text-green-600">Gratuit</div>
                    ) : (
                      <div className="text-lg font-semibold text-navy">{course.price} TND</div>
                    )}
                    
                    {isEnrolled ? (
                      <div className="mt-2 flex flex-col gap-2">
                        <span className="inline-flex items-center gap-1 px-3 py-1 bg-green-100 text-green-700 rounded-xl text-sm font-medium">
                          <CheckCircle className="w-4 h-4" />
                          Inscrit
                        </span>
                        {isEnrolled && !isFree && (
                          <button
                            onClick={() => setRefundModal({ courseId: course.id, courseTitle: course.title })}
                            className="text-xs text-red-500 hover:text-red-700 underline"
                          >
                            Demander un remboursement
                          </button>
                        )}
                      </div>
                    ) : canPurchase ? (
                      <button
                        onClick={() => purchaseCourse(course.id)}
                        disabled={purchasing === course.id}
                        className="mt-2 flex items-center gap-2 px-4 py-2 bg-orange text-white rounded-xl text-sm font-medium disabled:opacity-50"
                      >
                        <ShoppingCart className="w-4 h-4" />
                        {purchasing === course.id ? "Achat en cours..." : "Acheter"}
                      </button>
                    ) : (
                      <button
                        onClick={() => {
                          // Free enrollment
                          fetch(`${API_URL}/api/learner/courses/${course.id}/enroll`, {
                            method: "POST",
                            headers: { Authorization: `Bearer ${token}` },
                          }).then(() => {
                            fetchEnrollments();
                            fetchCourses();
                          });
                        }}
                        className="mt-2 px-4 py-2 bg-orange text-white rounded-xl text-sm font-medium"
                      >
                        S'inscrire
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Modal de remboursement */}
      {refundModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl w-full max-w-md">
            <div className="p-6 border-b flex justify-between items-center">
              <h3 className="text-lg font-semibold">Demander un remboursement</h3>
              <button onClick={() => setRefundModal(null)} className="p-1 hover:bg-gray-100 rounded">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6 space-y-4">
              <p className="text-sm text-gray">
                Vous demandez un remboursement pour le cours: <strong>{refundModal.courseTitle}</strong>
              </p>
              <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4">
                <div className="flex items-start gap-2">
                  <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />
                  <div className="text-sm text-yellow-800">
                    <p className="font-medium">Conditions de remboursement:</p>
                    <ul className="mt-1 list-disc list-inside text-yellow-700">
                      <li>Progression inférieure à 20%</li>
                      <li>Cours acheté (pas gratuit)</li>
                    </ul>
                  </div>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray mb-2">Raison du remboursement *</label>
                <textarea
                  value={refundReason}
                  onChange={(e) => setRefundReason(e.target.value)}
                  className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 focus:outline-none"
                  rows={3}
                  placeholder="Expliquez la raison de votre demande..."
                />
              </div>
            </div>
            <div className="p-6 border-t flex gap-3">
              <button
                onClick={() => setRefundModal(null)}
                className="flex-1 py-3 bg-cream-m rounded-xl font-medium"
              >
                Annuler
              </button>
              <button
                onClick={requestRefund}
                disabled={!refundReason.trim() || refundLoading}
                className="flex-1 py-3 bg-red-500 text-white rounded-xl font-medium disabled:opacity-50"
              >
                {refundLoading ? "Envoi..." : "Envoyer la demande"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Toast */}
      {toast.show && (
        <div className={`fixed top-6 right-6 z-50 px-6 py-4 rounded-xl shadow-lg text-white ${toast.type === "success" ? "bg-green-500" : "bg-red-500"}`}>
          {toast.message}
        </div>
      )}
    </div>
  );
}