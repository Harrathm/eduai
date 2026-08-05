import { useState, useEffect } from "react";
import { UserPlus, Check, X, Clock, RefreshCw, FileText, GraduationCap, Mail } from "lucide-react";
import { AdminTable, KPICard, StatusBadge, Modal, ConfirmModal } from "../components";
import { adminTeacherRegistrations } from "../../../api";
import type { TeacherRegistration } from "../../../api";

export default function AdminTeacherQueuePage() {
  const [registrations, setRegistrations] = useState<TeacherRegistration[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [reviewModal, setReviewModal] = useState<TeacherRegistration | null>(null);
  const [reviewAction, setReviewAction] = useState<"approved" | "rejected">("approved");
  const [rejectionReason, setRejectionReason] = useState("");
  const [processing, setProcessing] = useState(false);
  const [toast, setToast] = useState({ show: false, message: "", type: "success" as "success" | "error" });

  const showToast = (message: string, type: "success" | "error" = "success") => {
    setToast({ show: true, message, type });
    setTimeout(() => setToast({ show: false, message: "", type: "success" }), 3500);
  };

  const fetchRegistrations = async () => {
    setLoading(true);
    try {
      const data = await adminTeacherRegistrations.list(statusFilter || undefined);
      setRegistrations(Array.isArray(data) ? data : data.items || []);
    } catch (err) {
      console.error(err);
      showToast("Failed to load registrations", "error");
    }
    setLoading(false);
  };

  useEffect(() => { fetchRegistrations(); }, [statusFilter]);

  const handleReview = async () => {
    if (!reviewModal) return;
    setProcessing(true);
    try {
      await adminTeacherRegistrations.review(reviewModal.id, reviewAction, rejectionReason || undefined);
      showToast(`Registration ${reviewAction}`);
      setReviewModal(null);
      setRejectionReason("");
      fetchRegistrations();
    } catch (err: any) {
      showToast(err.message || "Failed", "error");
    }
    setProcessing(false);
  };

  const pending = registrations.filter(r => r.status === "pending");
  const approved = registrations.filter(r => r.status === "approved");
  const rejected = registrations.filter(r => r.status === "rejected");

  const columns = [
    { key: "name", header: "Applicant", render: (r: TeacherRegistration) => (
      <div>
        <div className="font-medium text-navy">{r.full_name}</div>
        <div className="flex items-center gap-1 text-xs text-gray">
          <Mail className="w-3 h-3" /> {r.email}
        </div>
      </div>
    )},
    { key: "qualifications", header: "Qualifications", render: (r: TeacherRegistration) => (
      <div className="max-w-xs">
        <div className="flex items-center gap-1 text-xs text-navy">
          <GraduationCap className="w-3 h-3" /> {r.experience_years ? `${r.experience_years}y exp` : "—"}
        </div>
        {r.qualifications && <p className="text-xs text-gray mt-0.5 truncate">{r.qualifications}</p>}
      </div>
    )},
    { key: "school_id", header: "School ID", render: (r: TeacherRegistration) => r.school_id },
    { key: "status", header: "Status", render: (r: TeacherRegistration) => (
      <StatusBadge label={r.status} variant={r.status === "pending" ? "yellow" : r.status === "approved" ? "success" : "red"} dot />
    )},
    { key: "created_at", header: "Applied", render: (r: TeacherRegistration) => (
      <span className="text-xs text-gray">{new Date(r.created_at).toLocaleDateString("fr-TN")}</span>
    )},
    { key: "actions", header: "Actions", render: (r: TeacherRegistration) => r.status === "pending" ? (
      <div className="flex items-center gap-1">
        <button onClick={() => { setReviewModal(r); setReviewAction("approved"); setRejectionReason(""); }}
          className="p-1.5 bg-green-50 text-green-600 rounded-lg hover:bg-green-100" title="Approve">
          <Check className="w-4 h-4" />
        </button>
        <button onClick={() => { setReviewModal(r); setReviewAction("rejected"); setRejectionReason(""); }}
          className="p-1.5 bg-red-50 text-red-400 rounded-lg hover:bg-red-100" title="Reject">
          <X className="w-4 h-4" />
        </button>
      </div>
    ) : <span className="text-xs text-gray">—</span> },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-display font-light text-navy">Teacher <span className="italic text-orange">Queue</span></h1>
          <p className="text-gray text-sm mt-1">Review and approve teacher registrations</p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={fetchRegistrations} className="p-2 hover:bg-white rounded-xl shadow-sm border border-black/5">
            <RefreshCw className={`w-5 h-5 text-gray ${loading ? "animate-spin" : ""}`} />
          </button>
          <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)}
            className="px-4 py-2 bg-white rounded-xl border border-black/5 text-sm focus:outline-none">
            <option value="">All</option>
            <option value="pending">Pending</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <KPICard label="Total" value={registrations.length} icon={<FileText className="w-5 h-5" />} color="blue" loading={loading} />
        <KPICard label="Pending" value={pending.length} icon={<Clock className="w-5 h-5" />} color="yellow" loading={loading} />
        <KPICard label="Approved" value={approved.length} icon={<Check className="w-5 h-5" />} color="green" loading={loading} />
        <KPICard label="Rejected" value={rejected.length} icon={<X className="w-5 h-5" />} color="red" loading={loading} />
      </div>

      <AdminTable columns={columns} data={registrations} loading={loading} emptyMessage="No registrations found" rowKey="id" />

      {/* Review Modal */}
      {reviewModal && (
        <Modal open onClose={() => setReviewModal(null)} title={reviewAction === "approved" ? "Approve Registration" : "Reject Registration"}
          footer={
            <>
              <button onClick={() => setReviewModal(null)} className="flex-1 py-3 bg-cream-m rounded-xl font-medium">Cancel</button>
              <button onClick={handleReview} disabled={processing}
                className={`flex-1 py-3 rounded-xl font-medium text-white ${reviewAction === "approved" ? "bg-green-500 hover:bg-green-600" : "bg-red-500 hover:bg-red-600"} disabled:opacity-50`}>
                {processing ? "..." : reviewAction === "approved" ? "Approve" : "Reject"}
              </button>
            </>
          }>
          <div className="space-y-4">
            <div className="p-4 bg-cream-m rounded-xl">
              <div className="font-semibold text-navy">{reviewModal.full_name}</div>
              <div className="text-sm text-gray mt-1">{reviewModal.email}</div>
              {reviewModal.qualifications && <div className="text-sm text-gray mt-1"><span className="font-medium">Qualifications:</span> {reviewModal.qualifications}</div>}
              {reviewModal.experience_years && <div className="text-sm text-gray"><span className="font-medium">Experience:</span> {reviewModal.experience_years} years</div>}
            </div>
            {reviewAction === "rejected" && (
              <div>
                <label className="block text-sm font-medium text-gray mb-1.5">Rejection Reason (optional)</label>
                <textarea value={rejectionReason} onChange={e => setRejectionReason(e.target.value)} rows={3}
                  className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 focus:outline-none focus:ring-2 focus:ring-red-200 resize-none"
                  placeholder="Reason for rejection..." />
              </div>
            )}
          </div>
        </Modal>
      )}

      {toast.show && (
        <div className={`fixed top-6 right-6 z-50 px-6 py-4 rounded-xl shadow-lg text-white ${toast.type === "success" ? "bg-green-500" : "bg-red-500"}`}>
          {toast.message}
        </div>
      )}
    </div>
  );
}