import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { BookOpen, Plus, RefreshCw, Eye, EyeOff, Pencil, Trash2, Search, Copy, Archive, X, FileText, Clock, Users, Tag, Send } from "lucide-react";
import { AdminTable, KPICard, StatusBadge, Modal, ConfirmModal } from "../components";
import { adminCourses } from "../../../api";
import type { AdminCourse } from "../../../api";
import DOMPurify from "dompurify";

const statusColors: Record<string, string> = {
  draft: "bg-gray-100 text-gray-600",
  published: "bg-green-100 text-green-700",
  archived: "bg-orange-100 text-orange-700",
  pending: "bg-yellow-100 text-yellow-700",
};

const pedagogicalStatusColors: Record<string, string> = {
  draft: "bg-gray-100 text-gray-600",
  pending_review: "bg-yellow-100 text-yellow-700",
  rejected: "bg-red-100 text-red-700",
  approved_for_platform: "bg-blue-100 text-blue-700",
  approved_for_b2b: "bg-green-100 text-green-700",
  revision_requested: "bg-orange-100 text-orange-700",
};

export default function AdminCoursesPage() {
  const { t } = useTranslation();
  const [courses, setCourses] = useState<AdminCourse[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [levelFilter, setLevelFilter] = useState("");
  const [pedagogicalFilter, setPedagogicalFilter] = useState("");
  const [createModal, setCreateModal] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<AdminCourse | null>(null);
  const [processing, setProcessing] = useState(false);
  const [toast, setToast] = useState({ show: false, message: "", type: "success" as "success" | "error" });
  const [previewCourse, setPreviewCourse] = useState<any>(null);
  const [previewLoading, setPreviewLoading] = useState(false);

  const showToast = (message: string, type: "success" | "error" = "success") => {
    setToast({ show: true, message, type });
    setTimeout(() => setToast({ show: false, message: "", type: "success" }), 3500);
  };

  const fetchCourses = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await adminCourses.list({
        status_filter: statusFilter || undefined,
        category: categoryFilter || undefined,
        level: levelFilter || undefined,
      });
      setCourses(data.items);
      setTotal(data.total);
    } catch (err) {
      console.error(err);
      setError(t("admin.courses.errors.loadFailed"));
    }
    setLoading(false);
  };

  useEffect(() => { fetchCourses(); }, [statusFilter, categoryFilter, levelFilter]);

  const handlePublish = async (id: number, publish: boolean) => {
    setProcessing(true);
    try {
      if (publish) {
        await adminCourses.publish(id);
        showToast(t("admin.courses.toast.published"));
      } else {
        await adminCourses.unpublish(id);
        showToast(t("admin.courses.toast.unpublished"));
      }
      fetchCourses();
    } catch (err: any) {
      const msg = err.message || "Failed";
      if (msg.includes("422")) {
        showToast(t("admin.courses.toast.publishBlocked"), "error");
      } else {
        showToast(msg, "error");
      }
    }
    setProcessing(false);
  };

  const handleSubmitForReview = async (id: number) => {
    setProcessing(true);
    try {
      await adminCourses.submitForReview(id);
      showToast(t("admin.courses.toast.submittedReview"));
      fetchCourses();
    } catch (err: any) {
      showToast(err.message || "Failed", "error");
    }
    setProcessing(false);
  };

  const handleArchive = async (id: number) => {
    setProcessing(true);
    try {
      await adminCourses.archive(id);
      showToast(t("admin.courses.toast.archived"));
      fetchCourses();
    } catch (err: any) {
      showToast(err.message || "Failed", "error");
    }
    setProcessing(false);
  };

  const handleDuplicate = async (id: number) => {
    setProcessing(true);
    try {
      await adminCourses.duplicate(id);
      showToast(t("admin.courses.toast.duplicated"));
      fetchCourses();
    } catch (err: any) {
      showToast(err.message || "Failed", "error");
    }
    setProcessing(false);
  };

  const handlePreview = async (id: number) => {
    setPreviewLoading(true);
    try {
      const data = await adminCourses.preview(id);
      setPreviewCourse(data);
    } catch (err: any) {
      showToast(err.message || t("admin.courses.errors.previewFailed"), "error");
    }
    setPreviewLoading(false);
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setProcessing(true);
    try {
      await adminCourses.delete(deleteTarget.id);
      showToast(t("admin.courses.toast.deleted"));
      setDeleteTarget(null);
      fetchCourses();
    } catch (err: any) {
      showToast(err.message || "Failed", "error");
    }
    setProcessing(false);
  };

  const categories = [...new Set(courses.map(c => c.category).filter(Boolean))];

  const filtered = courses.filter(c =>
    (search === "" || c.title?.toLowerCase().includes(search.toLowerCase()) || c.description?.toLowerCase().includes(search.toLowerCase())) &&
    (pedagogicalFilter === "" || (c as any).pedagogical_status === pedagogicalFilter)
  );

  const columns = [
    { key: "title", header: t("admin.courses.table.colTitle"), render: (c: AdminCourse) => (
      <div className="flex items-center gap-3">
        {c.cover_url || c.thumbnail_url ? (
          <img src={c.cover_url || c.thumbnail_url || ""} alt={c.title} className="w-10 h-10 rounded-lg object-cover" />
        ) : (
          <div className="w-10 h-10 rounded-lg bg-orange-100 flex items-center justify-center">
            <BookOpen className="w-5 h-5 text-orange-500" />
          </div>
        )}
        <div>
          <div className="font-medium text-navy line-clamp-1">{c.title}</div>
          <div className="text-xs text-gray flex items-center gap-1">
            <Tag className="w-3 h-3" />
            {c.category || "—"} / {t(`admin.courses.level.${c.level}`) || c.level || "—"}
          </div>
        </div>
      </div>
    )},
    { key: "status", header: t("admin.courses.table.colStatus"), render: (c: AdminCourse) => (
      <span className={`px-2 py-1 text-xs rounded-full font-medium ${statusColors[c.status?.toLowerCase()] || "bg-gray-100 text-gray-600"}`}>
        {t(`admin.courses.status.${c.status?.toLowerCase()}`) || c.status}
      </span>
    )},
    { key: "content", header: t("admin.courses.table.colContent"), render: (c: AdminCourse) => (
      <div className="text-sm text-gray">
        <div className="flex items-center gap-1"><FileText className="w-3 h-3" /> {c.total_modules || 0} {t("admin.courses.table.chapters")}</div>
        <div className="flex items-center gap-1"><BookOpen className="w-3 h-3" /> {c.total_lessons || 0} {t("admin.courses.table.lessons")}</div>
      </div>
    )},
    { key: "pedagogical_status", header: t("admin.courses.table.colPedagogical"), render: (c: any) => {
      const ps = c.pedagogical_status || "draft";
      return (
        <span className={`px-2 py-1 text-xs rounded-full font-medium ${pedagogicalStatusColors[ps] || "bg-gray-100 text-gray-600"}`}>
          {t(`admin.courses.pedagogicalStatus.${ps}`) || ps}
        </span>
      );
    }},
    { key: "owner_type", header: t("admin.courses.table.colOwner"), render: (c: any) => {
      const ot = c.owner_type || "school";
      return (
        <div className="text-sm">
          <span className={`px-2 py-1 text-xs rounded-full font-medium ${
            ot === "independent_teacher" ? "bg-purple-100 text-purple-700" :
            ot === "eduai_catalog" ? "bg-blue-100 text-blue-700" :
            "bg-gray-100 text-gray-600"
          }`}>
            {t(`admin.courses.owner.${ot}`) || ot}
          </span>
        </div>
      );
    }},
    { key: "price", header: t("admin.courses.table.colPrice"), render: (c: any) => (
      <div className="text-sm">
        {!c.price || c.price === 0 ? (
          <span className="text-green-600 font-medium">{t("admin.courses.free")}</span>
        ) : (
          <span className="font-semibold text-navy">{c.price} {t("admin.courses.currency")}</span>
        )}
      </div>
    )},
    { key: "actions", header: t("admin.courses.table.colActions"), render: (c: AdminCourse) => (
      <div className="flex items-center gap-1 flex-wrap">
        <button onClick={() => window.location.href = `/dashboard/admin/courses/${c.id}`}
          className="p-1.5 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100" title={t("admin.courses.btn.edit")}>
          <Pencil className="w-4 h-4" />
        </button>
        <button onClick={() => handlePreview(c.id)} disabled={previewLoading}
          className="p-1.5 bg-purple-50 text-purple-600 rounded-lg hover:bg-purple-100" title={t("admin.courses.btn.preview")}>
          <Eye className="w-4 h-4" />
        </button>
        <button onClick={() => handleDuplicate(c.id)} disabled={processing}
          className="p-1.5 bg-navy-50 text-navy-600 rounded-lg hover:bg-navy-100" title={t("admin.courses.btn.duplicate")}>
          <Copy className="w-4 h-4" />
        </button>
        {c.is_published ? (
          <button onClick={() => handlePublish(c.id, false)} disabled={processing}
            className="p-1.5 bg-orange-50 text-orange-500 rounded-lg hover:bg-orange-100" title={t("admin.courses.btn.unpublish")}>
            <EyeOff className="w-4 h-4" />
          </button>
        ) : (
          <button onClick={() => handlePublish(c.id, true)} disabled={processing}
            className="p-1.5 bg-green-50 text-green-600 rounded-lg hover:bg-green-100" title={t("admin.courses.btn.publish")}>
            <Eye className="w-4 h-4" />
          </button>
        )}
        {c.status?.toLowerCase() !== "archived" && (
          <button onClick={() => handleArchive(c.id)} disabled={processing}
            className="p-1.5 bg-gray-100 text-gray-500 rounded-lg hover:bg-gray-200" title={t("admin.courses.btn.archive")}>
            <Archive className="w-4 h-4" />
          </button>
        )}
        {c.status?.toLowerCase() === "draft" && (c as any).pedagogical_status !== "pending_review" && (c as any).pedagogical_status !== "approved_for_b2b" && (
          <button onClick={() => handleSubmitForReview(c.id)} disabled={processing}
            className="p-1.5 bg-teal-50 text-teal-600 rounded-lg hover:bg-teal-100" title={t("admin.courses.btn.submitReview")}>
            <Send className="w-4 h-4" />
          </button>
        )}
        <button onClick={() => setDeleteTarget(c)}
          className="p-1.5 bg-red-50 text-red-400 rounded-lg hover:bg-red-100" title={t("admin.courses.btn.delete")}>
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    )},
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-display font-light text-navy">{t("admin.courses.title")} <span className="italic text-orange">& {t("admin.courses.titleSuffix")}</span></h1>
          <p className="text-gray text-sm mt-1">{t("admin.courses.subtitle", { count: total })}</p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={fetchCourses} className="p-2 hover:bg-white rounded-xl shadow-sm border border-black/5">
            <RefreshCw className={`w-5 h-5 text-gray ${loading ? "animate-spin" : ""}`} />
          </button>
          <button onClick={() => setCreateModal(true)} className="flex items-center gap-2 px-4 py-2 bg-orange text-white rounded-xl font-medium text-sm hover:bg-orange-w">
            <Plus className="w-4 h-4" /> {t("admin.courses.btnNew")}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-5 gap-4">
        <KPICard label={t("admin.courses.kpi.total")} value={total} icon={<BookOpen className="w-5 h-5" />} color="blue" loading={loading} />
        <KPICard label={t("admin.courses.kpi.published")} value={courses.filter(c => c.is_published).length} icon={<Eye className="w-5 h-5" />} color="green" loading={loading} />
        <KPICard label={t("admin.courses.kpi.draft")} value={courses.filter(c => c.status?.toLowerCase() === "draft").length} icon={<BookOpen className="w-5 h-5" />} color="yellow" loading={loading} />
        <KPICard label={t("admin.courses.kpi.inReview")} value={courses.filter((c: any) => c.pedagogical_status === "pending_review").length} icon={<Clock className="w-5 h-5" />} color="orange" loading={loading} />
        <KPICard label={t("admin.courses.kpi.archived")} value={courses.filter(c => c.status?.toLowerCase() === "archived").length} icon={<Archive className="w-5 h-5" />} color="orange" loading={loading} />
      </div>

      <div className="bg-white rounded-2xl p-4 shadow-sm border border-black/5 flex items-center gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray" />
          <input type="text" value={search} onChange={e => setSearch(e.target.value)}
            placeholder={t("admin.courses.filter.searchPlaceholder")} className="w-full ps-12 pe-4 py-3 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none focus:ring-2 focus:ring-orange/20" />
        </div>
        <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)}
          className="px-4 py-3 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none">
          <option value="">{t("admin.courses.filter.allStatus")}</option>
          <option value="draft">{t("admin.courses.status.draft")}</option>
          <option value="published">{t("admin.courses.status.published")}</option>
          <option value="archived">{t("admin.courses.status.archived")}</option>
        </select>
        <select value={categoryFilter} onChange={e => setCategoryFilter(e.target.value)}
          className="px-4 py-3 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none">
          <option value="">{t("admin.courses.filter.allCategories")}</option>
          {categories.map(cat => <option key={cat} value={cat}>{cat}</option>)}
        </select>
        <select value={levelFilter} onChange={e => setLevelFilter(e.target.value)}
          className="px-4 py-3 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none">
          <option value="">{t("admin.courses.filter.allLevels")}</option>
          <option value="beginner">{t("admin.courses.level.beginner")}</option>
          <option value="intermediate">{t("admin.courses.level.intermediate")}</option>
          <option value="advanced">{t("admin.courses.level.advanced")}</option>
        </select>
        <select value={pedagogicalFilter} onChange={e => setPedagogicalFilter(e.target.value)}
          className="px-4 py-3 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none">
          <option value="">{t("admin.courses.filter.allPedagogicalStatus")}</option>
          <option value="draft">{t("admin.courses.pedagogicalStatus.draft")}</option>
          <option value="pending_review">{t("admin.courses.pedagogicalStatus.pending_review")}</option>
          <option value="rejected">{t("admin.courses.pedagogicalStatus.rejected")}</option>
          <option value="approved_for_platform">{t("admin.courses.pedagogicalStatus.approved_for_platform")}</option>
          <option value="approved_for_b2b">{t("admin.courses.pedagogicalStatus.approved_for_b2b")}</option>
          <option value="revision_requested">{t("admin.courses.pedagogicalStatus.revision_requested")}</option>
        </select>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-2xl p-6 flex flex-col items-center justify-center text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <button onClick={fetchCourses} className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium">
            {t("admin.courses.btn.retry")}
          </button>
        </div>
      )}

      {!loading && filtered.length === 0 && !error && (
        <div className="bg-white rounded-2xl p-12 shadow-sm border border-black/5 flex flex-col items-center justify-center text-center">
          <BookOpen className="w-16 h-16 text-gray-300 mb-4" />
          <h3 className="text-lg font-medium text-gray-700 mb-2">{t("admin.courses.empty.noResults")}</h3>
          <p className="text-gray-500 mb-6">
            {search || statusFilter || categoryFilter || levelFilter
              ? t("admin.courses.empty.noResultsDesc")
              : t("admin.courses.empty.startCreate")}
          </p>
          {!search && !statusFilter && !categoryFilter && !levelFilter && (
            <button onClick={() => setCreateModal(true)} className="flex items-center gap-2 px-4 py-2 bg-orange text-white rounded-xl font-medium text-sm hover:bg-orange-w">
              <Plus className="w-4 h-4" /> {t("admin.courses.btn.createNew")}
            </button>
          )}
        </div>
      )}

      <AdminTable columns={columns} data={filtered} loading={loading} emptyMessage="" rowKey="id" />

      {createModal && <CourseFormModal open onClose={() => setCreateModal(false)} onSubmit={async (data) => {
        setProcessing(true);
        try {
          await adminCourses.create(data);
          showToast(t("admin.courses.toast.created"));
          setCreateModal(false);
          fetchCourses();
        } catch (err: any) { showToast(err.message || "Failed", "error"); }
        setProcessing(false);
      }} loading={processing} />}

      <ConfirmModal open={!!deleteTarget} onClose={() => setDeleteTarget(null)} onConfirm={handleDelete}
        title={t("admin.courses.modal.confirmDelete.title")} message={t("admin.courses.modal.confirmDelete.message", { name: deleteTarget?.title })}
        confirmLabel={t("admin.courses.modal.confirmDelete.confirm")} danger loading={processing} />

      {/* Preview Modal */}
      {previewCourse && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={() => setPreviewCourse(null)}>
          <div className="bg-white rounded-2xl w-full max-w-3xl max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <div className="p-4 border-b sticky top-0 bg-white flex justify-between items-center z-10">
              <h3 className="font-semibold text-lg">{t("admin.courses.modal.preview.title")}</h3>
              <button onClick={() => setPreviewCourse(null)} className="p-1 hover:bg-gray-100 rounded">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6">
              {previewCourse.cover_url && (
                <img src={previewCourse.cover_url} alt="" className="w-full h-48 object-cover rounded-xl mb-4" />
              )}
              <div className="flex items-center gap-2 mb-2">
                <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${statusColors[previewCourse.status] || "bg-gray-100 text-gray-600"}`}>
                  {t(`admin.courses.status.${previewCourse.status}`) || previewCourse.status}
                </span>
                <span className="text-xs text-gray-500">{t(`admin.courses.level.${previewCourse.level}`) || previewCourse.level}</span>
                {previewCourse.category && <span className="text-xs text-gray-500">/ {previewCourse.category}</span>}
              </div>
              <h2 className="text-2xl font-bold text-navy mb-2">{previewCourse.title}</h2>
              {previewCourse.short_description && (
                <p className="text-gray-600 mb-4">{previewCourse.short_description}</p>
              )}
              {previewCourse.description && (
                <div className="prose prose-sm max-w-none mb-4" dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(previewCourse.description) }} />
              )}
              <div className="grid grid-cols-3 gap-4 mb-6 text-sm">
                <div className="bg-gray-50 rounded-lg p-3 text-center">
                  <div className="font-bold text-navy">{previewCourse.total_modules}</div>
                  <div className="text-gray-500">{t("admin.courses.modal.preview.chapters")}</div>
                </div>
                <div className="bg-gray-50 rounded-lg p-3 text-center">
                  <div className="font-bold text-navy">{previewCourse.total_lessons}</div>
                  <div className="text-gray-500">{t("admin.courses.modal.preview.lessons")}</div>
                </div>
                <div className="bg-gray-50 rounded-lg p-3 text-center">
                  <div className="font-bold text-navy">{previewCourse.total_duration_minutes || 0} min</div>
                  <div className="text-gray-500">{t("admin.courses.modal.preview.duration")}</div>
                </div>
              </div>
              {previewCourse.prerequisites && (
                <div className="mb-4">
                  <h4 className="font-medium text-sm mb-1">{t("admin.courses.modal.preview.prerequisites")}</h4>
                  <p className="text-sm text-gray-600">{previewCourse.prerequisites}</p>
                </div>
              )}
              {previewCourse.learning_objectives && (
                <div className="mb-4">
                  <h4 className="font-medium text-sm mb-1">{t("admin.courses.modal.preview.objectives")}</h4>
                  <p className="text-sm text-gray-600">{previewCourse.learning_objectives}</p>
                </div>
              )}
              {previewCourse.modules?.length > 0 && (
                <div>
                  <h4 className="font-medium text-sm mb-2">{t("admin.courses.modal.preview.program")}</h4>
                  <div className="space-y-3">
                    {previewCourse.modules.map((mod: any, idx: number) => (
                      <div key={mod.id} className="border rounded-lg p-3">
                        <div className="font-medium text-sm flex items-center gap-2">
                          <span className="bg-navy text-white text-xs w-6 h-6 rounded-full flex items-center justify-center">{idx + 1}</span>
                          {mod.title}
                        </div>
                        {mod.lessons?.length > 0 && (
                          <div className="ml-8 mt-2 space-y-1">
                            {mod.lessons.map((les: any) => (
                              <div key={les.id} className="flex items-center gap-2 text-xs text-gray-600">
                                <FileText className="w-3 h-3" />
                                {les.title}
                                {les.is_free && <span className="text-green-600">({t("admin.courses.free")})</span>}
                                <span className="text-gray-400">{les.duration_minutes} min</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {toast.show && (
        <div className={`fixed top-6 right-6 z-50 px-6 py-4 rounded-xl shadow-lg text-white ${toast.type === "success" ? "bg-green-500" : "bg-red-500"}`}>
          {toast.message}
        </div>
      )}
    </div>
  );
}

function CourseFormModal({ open, onClose, onSubmit, loading }: {
  open: boolean; onClose: () => void; onSubmit: (d: any) => void; loading: boolean;
}) {
  const { t } = useTranslation();
  const [title, setTitle] = useState("");
  const [shortDescription, setShortDescription] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("");
  const [level, setLevel] = useState("beginner");
  const [visibility, setVisibility] = useState("public");
  const [enrollmentType, setEnrollmentType] = useState("open");
  const [tags, setTags] = useState("");
  const [prerequisites, setPrerequisites] = useState("");
  const [learningObjectives, setLearningObjectives] = useState("");
  const [errors, setErrors] = useState<string[]>([]);

  if (!open) return null;

  const handleSubmit = () => {
    const errs: string[] = [];
    if (!title.trim()) errs.push(t("admin.courses.modal.create.validation.titleRequired"));
    if (errs.length > 0) { setErrors(errs); return; }
    setErrors([]);
    onSubmit({
      title, short_description: shortDescription || undefined, description: description || undefined,
      category: category || undefined, level, visibility, enrollment_type: enrollmentType,
      tags: tags ? tags.split(",").map(t => t.trim()).filter(Boolean) : undefined,
      prerequisites: prerequisites || undefined,
      learning_objectives: learningObjectives || undefined,
    });
  };

  return (
    <Modal open onClose={onClose} title={t("admin.courses.modal.create.title")}
      footer={
        <>
          <button onClick={onClose} className="flex-1 py-3 bg-cream-m rounded-xl font-medium">{t("admin.courses.modal.create.btnCancel")}</button>
          <button onClick={handleSubmit} disabled={loading || !title.trim()}
            className="flex-1 py-3 bg-orange text-white rounded-xl font-medium disabled:opacity-50">
            {loading ? "..." : t("admin.courses.modal.create.btnCreate")}
          </button>
        </>
      }>
      <div className="space-y-4">
        {errors.length > 0 && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3">
            {errors.map((e, i) => <p key={i} className="text-red-600 text-sm">{e}</p>)}
          </div>
        )}
        <div>
          <label className="block text-sm font-medium text-gray mb-1.5">{t("admin.courses.modal.create.titleLabel")}</label>
          <input value={title} onChange={e => setTitle(e.target.value)} className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 focus:outline-none focus:ring-2 focus:ring-orange/20"
            placeholder={t("admin.courses.modal.create.titlePlaceholder")} />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray mb-1.5">{t("admin.courses.modal.create.descLabel")}</label>
          <textarea value={shortDescription} onChange={e => setShortDescription(e.target.value)} rows={2}
            className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 focus:outline-none resize-none"
            placeholder={t("admin.courses.modal.create.descPlaceholder")} />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray mb-1.5">{t("admin.courses.modal.create.fullDescLabel")}</label>
          <textarea value={description} onChange={e => setDescription(e.target.value)} rows={3}
            className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 focus:outline-none resize-none" />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray mb-1.5">{t("admin.courses.modal.create.categoryLabel")}</label>
            <input value={category} onChange={e => setCategory(e.target.value)}
              className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 focus:outline-none" placeholder={t("admin.courses.modal.create.categoryPlaceholder")} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray mb-1.5">{t("admin.courses.modal.create.levelLabel")}</label>
            <select value={level} onChange={e => setLevel(e.target.value)}
              className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 focus:outline-none">
              <option value="beginner">{t("admin.courses.level.beginner")}</option>
              <option value="intermediate">{t("admin.courses.level.intermediate")}</option>
              <option value="advanced">{t("admin.courses.level.advanced")}</option>
            </select>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray mb-1.5">{t("admin.courses.modal.create.visibilityLabel")}</label>
            <select value={visibility} onChange={e => setVisibility(e.target.value)}
              className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 focus:outline-none">
              <option value="public">{t("admin.courses.visibility.public")}</option>
              <option value="private">{t("admin.courses.visibility.private")}</option>
              <option value="school">{t("admin.courses.visibility.school")}</option>
              <option value="role">{t("admin.courses.visibility.role")}</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray mb-1.5">{t("admin.courses.modal.create.enrollmentLabel")}</label>
            <select value={enrollmentType} onChange={e => setEnrollmentType(e.target.value)}
              className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 focus:outline-none">
              <option value="open">{t("admin.courses.enrollment.open")}</option>
              <option value="manual">{t("admin.courses.enrollment.manual")}</option>
            </select>
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray mb-1.5">{t("admin.courses.modal.create.tagsLabel")}</label>
          <input value={tags} onChange={e => setTags(e.target.value)}
            className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 focus:outline-none" placeholder={t("admin.courses.modal.create.tagsPlaceholder")} />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray mb-1.5">{t("admin.courses.modal.create.prereqLabel")}</label>
          <textarea value={prerequisites} onChange={e => setPrerequisites(e.target.value)} rows={2}
            className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 focus:outline-none resize-none"
            placeholder={t("admin.courses.modal.create.prereqPlaceholder")} />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray mb-1.5">{t("admin.courses.modal.create.objectivesLabel")}</label>
          <textarea value={learningObjectives} onChange={e => setLearningObjectives(e.target.value)} rows={2}
            className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 focus:outline-none resize-none"
            placeholder={t("admin.courses.modal.create.objectivesPlaceholder")} />
        </div>
      </div>
    </Modal>
  );
}
