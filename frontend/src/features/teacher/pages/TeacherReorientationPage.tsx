import { useState, useEffect, useCallback } from "react";
import { useTranslation } from 'react-i18next';
import { Bell, CheckCircle, XCircle, Clock, AlertTriangle } from "lucide-react";
import { useAuthStore } from "../../../store/authStore";
import { getNotificationsReorientation, validerReorientation } from "../../../api";
import type { NotificationReorientation } from "../../../api";

export default function TeacherReorientationPage() {
  const { t } = useTranslation();
  const { token, user } = useAuthStore();
  const [notifications, setNotifications] = useState<NotificationReorientation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState({ show: false, message: "", type: "success" as "success" | "error" });

  const showToast = (message: string, type: "success" | "error" = "success") => {
    setToast({ show: true, message, type });
    setTimeout(() => setToast({ show: false, message: "", type: "success" }), 3000);
  };

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      if (!user?.id) {
        setError(t('teacher.reorientation.loading'));
        setLoading(false);
        return;
      }
      const data = await getNotificationsReorientation(user.id);
      setNotifications(data);
    } catch (err: any) {
      if (err?.status === 403 || err?.message?.includes("403")) {
        setError(t('teacher.reorientation.accessDenied'));
      } else {
        setError(t('teacher.reorientation.noResults'));
      }
    }
    setLoading(false);
  }, [token, user?.id]);

  useEffect(() => { load(); }, [load]);

  const handleValidate = async (profilId: number, action: "confirme" | "annule") => {
    try {
      await validerReorientation(profilId, action);
      showToast(action === "confirme" ? t('teacher.reorientation.toasts.confirmed') : t('teacher.reorientation.toasts.cancelled'));
      setNotifications(prev => prev.filter(n => n.profil_assimilation_id !== profilId));
    } catch (err: any) {
      showToast(err.message || t('teacher.reorientation.toasts.error'), "error");
    }
  };

  const isExpired = (dateLimite: string) => new Date(dateLimite) < new Date();

  return (
    <div className="space-y-6">
      {toast.show && (
        <div className={`fixed top-4 right-4 z-50 px-4 py-3 rounded-xl shadow-lg text-sm font-medium ${
          toast.type === "success" ? "bg-green-500 text-white" : "bg-red-500 text-white"
        }`}>{toast.message}</div>
      )}

      <div>
        <h1 className="text-3xl font-display font-light text-navy">{t('teacher.reorientation.title')} <span className="italic text-orange">{t('teacher.reorientation.titleSuffix')}</span></h1>
        <p className="text-gray text-sm mt-1">{t('teacher.reorientation.subtitle')}</p>
      </div>

      {loading ? (
        <div className="text-center py-12 text-gray">{t('teacher.reorientation.loading')}</div>
      ) : error ? (
        <div className="bg-white rounded-2xl shadow-sm border border-black/5 p-12 text-center">
          <Bell className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray">{error}</p>
        </div>
      ) : notifications.length === 0 ? (
        <div className="bg-white rounded-2xl shadow-sm border border-black/5 p-12 text-center">
          <Bell className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray">{t('teacher.reorientation.noPending')}</p>
        </div>
      ) : (
        <div className="space-y-3">
          {notifications.map(n => (
            <div key={n.id} className={`bg-white rounded-2xl shadow-sm border p-5 ${
              isExpired(n.date_limite_action) ? "border-amber-200 bg-amber-50" : "border-black/5"
            }`}>
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    {isExpired(n.date_limite_action) ? (
                      <Clock className="w-5 h-5 text-amber-500" />
                    ) : (
                      <AlertTriangle className="w-5 h-5 text-blue-500" />
                    )}
                    <span className="font-semibold text-navy">
                      {t('teacher.reorientation.labels.profile')} #{n.profil_assimilation_id}
                    </span>
                    <span className="text-xs text-gray">
                      — {t('teacher.reorientation.labels.student')} #{/* would need to resolve */ "—"}
                    </span>
                  </div>
                  <p className="text-sm text-gray">
                    {t('teacher.reorientation.labels.notified')} {new Date(n.date_notification).toLocaleDateString("fr-FR")}
                    {isExpired(n.date_limite_action) ? (
                      <span className="ml-2 text-amber-600 font-medium">• {t('teacher.reorientation.labels.expired')}</span>
                    ) : (
                      <span className="ml-2">— {t('teacher.reorientation.labels.deadline')}: {new Date(n.date_limite_action).toLocaleDateString("fr-FR")}</span>
                    )}
                  </p>
                </div>

                {n.action_prise === "aucune" && !isExpired(n.date_limite_action) && (
                  <div className="flex gap-2">
                    <button onClick={() => handleValidate(n.profil_assimilation_id, "confirme")}
                      className="flex items-center gap-1.5 px-4 py-2 bg-green-100 text-green-700 rounded-xl text-sm font-medium hover:bg-green-200 transition-colors">
                      <CheckCircle className="w-4 h-4" /> {t('teacher.reorientation.btn.confirm')}
                    </button>
                    <button onClick={() => handleValidate(n.profil_assimilation_id, "annule")}
                      className="flex items-center gap-1.5 px-4 py-2 bg-red-100 text-red-700 rounded-xl text-sm font-medium hover:bg-red-200 transition-colors">
                      <XCircle className="w-4 h-4" /> {t('teacher.reorientation.btn.cancel')}
                    </button>
                  </div>
                )}

                {n.action_prise !== "aucune" && (
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                    n.action_prise === "confirme" ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
                  }`}>
                    {n.action_prise === "confirme" ? t('teacher.reorientation.badges.confirmed') : t('teacher.reorientation.badges.cancelled')}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
