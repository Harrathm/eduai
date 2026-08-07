import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useAuthStore } from "../../../store/authStore";
import { courseAcademy, courseLearner } from "../../../api";
import { Search, BookOpen, Clock, User, ShoppingCart, AlertCircle, CheckCircle } from "lucide-react";
import { Button, Modal, EmptyState, PageWrapper } from "../../../components/ui";

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
  const { t } = useTranslation();
  const { user } = useAuthStore();
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
  }, []);

  const fetchCourses = async () => {
    setLoading(true);
    try {
      const data = await courseAcademy.list();
      setCourses(Array.isArray(data) ? data : (data as any).items || []);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const fetchEnrollments = async () => {
    try {
      const data = await courseLearner.myCourses();
      const list = Array.isArray(data) ? data : (data as any).items || [];
      setMyEnrollments(list.map((c: Course) => c.id));
    } catch (err) {
      console.error(err);
    }
  };

  const purchaseCourse = async (courseId: number) => {
    setPurchasing(courseId);
    try {
      const data: Purchase = await courseLearner.purchase(courseId);
      setToast({
        show: true,
        message: t('courseCatalog.purchaseSuccess', { amount: data.amount_paid, currency: data.currency }),
        type: "success"
      });
      fetchEnrollments();
      fetchCourses();
    } catch (err: any) {
      setToast({
        show: true,
        message: err.message || t('courseCatalog.purchaseFailed'),
        type: "error"
      });
    }
    setPurchasing(null);
  };

  const requestRefund = async () => {
    if (!refundModal || !refundReason.trim()) return;
    setRefundLoading(true);
    try {
      const data = await courseLearner.refundRequest(refundModal.courseId, refundReason);
      setToast({
        show: true,
        message: data.message || t('courseCatalog.refundSent'),
        type: "success"
      });
      setRefundModal(null);
      setRefundReason("");
      fetchEnrollments();
    } catch (err: any) {
      setToast({
        show: true,
        message: err.message || t('courseCatalog.refundFailed'),
        type: "error"
      });
    }
    setRefundLoading(false);
  };

  const filtered = courses.filter((c) =>
    c.title.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <PageWrapper
      title={<>{t('courseCatalog.title', 'Soft Skills')} <span className="italic text-orange">{t('courseCatalog.titleHighlight', 'Catalogue')}</span></>}
      subtitle={t('courseCatalog.subtitle')}
      icon={<BookOpen className="w-8 h-8" />}
    >

      {/* Search */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
        <div className="relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full ps-12 pe-4 py-3 bg-cream-m rounded-xl border border-black/5 focus:border-orange focus:outline-none"
            placeholder={t('courseCatalog.searchPlaceholder')}
          />
        </div>
      </div>

      {/* Course Grid */}
      <div className="grid gap-4">
        {loading ? (
          <div className="bg-white rounded-3xl p-12 text-center text-gray">
            {t('courseCatalog.loading')}
          </div>
        ) : filtered.length === 0 ? (
          <EmptyState
            icon={<BookOpen className="w-12 h-12" />}
            title={t('courseCatalog.noResults')}
          />
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
                          {t('courseCatalog.independent')}
                        </span>
                      )}
                      {course.owner_type === "eduai_catalog" && (
                        <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full">
                          {t('courseCatalog.catalogueEduai')}
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
                  <div className="text-end">
                    {isFree ? (
                      <div className="text-lg font-semibold text-green-600">{t('courseCatalog.free')}</div>
                    ) : (
                      <div className="text-lg font-semibold text-navy">{course.price} TND</div>
                    )}
                    
                    {isEnrolled ? (
                      <div className="mt-2 flex flex-col gap-2">
                        <span className="inline-flex items-center gap-1 px-3 py-1 bg-green-100 text-green-700 rounded-xl text-sm font-medium">
                          <CheckCircle className="w-4 h-4" />
                          {t('courseCatalog.enrolled')}
                        </span>
                        {isEnrolled && !isFree && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setRefundModal({ courseId: course.id, courseTitle: course.title })}
                            className="text-xs text-red-500 hover:text-red-700 underline"
                          >
                            {t('courseCatalog.requestRefund')}
                          </Button>
                        )}
                      </div>
                    ) : canPurchase ? (
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => purchaseCourse(course.id)}
                        disabled={purchasing === course.id}
                        loading={purchasing === course.id}
                      >
                        <ShoppingCart className="w-4 h-4" />
                        {purchasing === course.id ? t('courseCatalog.purchasing') : t('courseCatalog.buy')}
                      </Button>
                    ) : (
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => {
                          courseLearner.enroll(course.id).then(() => {
                            fetchEnrollments();
                            fetchCourses();
                          });
                        }}
                      >
                        {t('courseCatalog.enrollFree')}
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Modal de remboursement */}
      <Modal
        open={!!refundModal}
        onClose={() => setRefundModal(null)}
        title={t('courseCatalog.refundTitle')}
        maxWidth="max-w-md"
      >
        <p className="text-sm text-gray">
          {t('courseCatalog.refundDescription', { title: refundModal?.courseTitle })}
        </p>
        <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4 mt-4">
          <div className="flex items-start gap-2">
            <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />
            <div className="text-sm text-yellow-800">
              <p className="font-medium">{t('courseCatalog.refundConditions')}</p>
              <ul className="mt-1 list-disc list-inside text-yellow-700">
                <li>{t('courseCatalog.refundConditionProgress')}</li>
                <li>{t('courseCatalog.refundConditionPaid')}</li>
              </ul>
            </div>
          </div>
        </div>
        <div className="mt-4">
          <label className="block text-sm font-medium text-gray mb-2">{t('courseCatalog.refundReasonLabel')}</label>
          <textarea
            value={refundReason}
            onChange={(e) => setRefundReason(e.target.value)}
            className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 focus:outline-none"
            rows={3}
            placeholder={t('courseCatalog.refundReasonPlaceholder')}
          />
        </div>
        <div className="mt-6 flex gap-3">
          <Button
            variant="ghost"
            onClick={() => setRefundModal(null)}
            className="flex-1"
          >
            {t('courseCatalog.cancel')}
          </Button>
          <Button
            variant="danger"
            onClick={requestRefund}
            disabled={!refundReason.trim() || refundLoading}
            loading={refundLoading}
            className="flex-1"
          >
            {refundLoading ? t('courseCatalog.sending') : t('courseCatalog.sendRequest')}
          </Button>
        </div>
      </Modal>

      {/* Toast */}
      {toast.show && (
        <div className={`fixed top-6 right-6 z-50 px-6 py-4 rounded-xl shadow-lg text-white ${toast.type === "success" ? "bg-green-500" : "bg-red-500"}`}>
          {toast.message}
        </div>
      )}
    </PageWrapper>
  );
}