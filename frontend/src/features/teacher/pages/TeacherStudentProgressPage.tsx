import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { Users, BarChart3, AlertTriangle, Mail, ChevronRight, Trophy, Clock } from "lucide-react";
import { teacherClassesApi, teacherProgressApi } from "../../../api";
import type { StudentProgress } from "../../../api/teacherApi";
import { Button, PageSpinner } from "../../../components/ui";

interface Class {
  id: number;
  name: string;
  students_count: number;
  courses_count: number;
}

function packBadge(status: string, label: string) {
  switch (status) {
    case "ok":
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium bg-green-50 text-green-700 rounded-full">
          <span className="w-1.5 h-1.5 rounded-full bg-green-500" />
          {label}
        </span>
      );
    case "expired":
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium bg-red-50 text-red-700 rounded-full">
          <AlertTriangle className="w-3 h-3" />
          Bloqué (Pack expiré)
        </span>
      );
    case "quota_exceeded":
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium bg-orange-50 text-orange-700 rounded-full">
          <AlertTriangle className="w-3 h-3" />
          Quota dépassé
        </span>
      );
    default:
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-600 rounded-full">
          Aucun pack
        </span>
      );
  }
}

function ProgressBar({ percent }: { percent: number }) {
  const color = percent >= 70 ? "bg-green-500" : percent >= 40 ? "bg-orange" : "bg-red-400";
  return (
    <div className="flex items-center gap-2">
      <div className="w-20 h-2 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${Math.min(percent, 100)}%` }} />
      </div>
      <span className="text-sm font-medium text-navy w-10 text-right">{percent}%</span>
    </div>
  );
}

export default function TeacherStudentProgressPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [classes, setClasses] = useState<Class[]>([]);
  const [selectedClass, setSelectedClass] = useState<number | null>(null);
  const [students, setStudents] = useState<StudentProgress[]>([]);
  const [loadingClasses, setLoadingClasses] = useState(true);
  const [loadingStudents, setLoadingStudents] = useState(false);

  useEffect(() => {
    fetchClasses();
  }, []);

  useEffect(() => {
    if (selectedClass) fetchProgress(selectedClass);
  }, [selectedClass]);

  const fetchClasses = async () => {
    setLoadingClasses(true);
    try {
      const data = await teacherClassesApi.list();
      setClasses(data.items || data || []);
    } catch (err) {
      console.error(err);
    }
    setLoadingClasses(false);
  };

  const fetchProgress = async (classId: number) => {
    setLoadingStudents(true);
    try {
      const data = await teacherProgressApi.getClassProgress(classId);
      setStudents(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error(err);
      setStudents([]);
    }
    setLoadingStudents(false);
  };

  const selectedClassName = classes.find((c) => c.id === selectedClass)?.name || "";
  const blockedCount = students.filter((s) => s.pack_status === "expired" || s.pack_status === "quota_exceeded").length;
  const avgProgress = students.length > 0
    ? Math.round(students.reduce((sum, s) => sum + s.progress_percent, 0) / students.length)
    : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-3xl p-8 shadow-sm border border-black/5">
        <h1 className="text-3xl font-[300] text-navy">
          {t('teacher.suivi.title', 'Suivi des Élèves')}
        </h1>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left: Class list */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
            <h2 className="text-lg font-semibold text-navy mb-4">{t('teacher.classroom.myClasses', 'Mes Classes')}</h2>
            {loadingClasses ? (
              <PageSpinner />
            ) : classes.length === 0 ? (
              <p className="text-gray text-sm text-center py-6">
                {t('teacher.classroom.noClasses', 'Aucune classe')}
              </p>
            ) : (
              <div className="space-y-2">
                {classes.map((cls) => (
                  <div
                    key={cls.id}
                    onClick={() => setSelectedClass(cls.id)}
                    className={`p-4 rounded-xl cursor-pointer transition-all ${
                      selectedClass === cls.id
                        ? "bg-orange text-white"
                        : "bg-cream-m hover:bg-cream"
                    }`}
                  >
                    <div className="flex justify-between items-center">
                      <div>
                        <div className="font-medium">{cls.name}</div>
                        <div className={`text-sm ${selectedClass === cls.id ? "text-white/70" : "text-gray"}`}>
                          {cls.students_count} {t('teacher.classroom.students', 'élèves')} · {cls.courses_count} {t('teacher.classroom.courses', 'cours')}
                        </div>
                      </div>
                      <ChevronRight className={`w-4 h-4 ${selectedClass === cls.id ? "text-white/70" : "text-gray"}`} />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right: Student progress table */}
        <div className="lg:col-span-2 space-y-4">
          {!selectedClass ? (
            <div className="bg-white rounded-2xl p-12 text-center text-gray shadow-sm border border-black/5">
              <BarChart3 className="w-16 h-16 mx-auto mb-4 text-gray-300" />
              <p className="text-lg">{t('teacher.suivi.noClassSelected', 'Veuillez sélectionner une classe pour voir les élèves.')}</p>
            </div>
          ) : loadingStudents ? (
            <div className="bg-white rounded-2xl p-12 shadow-sm border border-black/5">
              <PageSpinner />
            </div>
          ) : (
            <>
              {/* Stats cards */}
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-white rounded-2xl p-5 shadow-sm border border-black/5">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center">
                      <Users className="w-5 h-5 text-blue-600" />
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-navy">{students.length}</p>
                       <p className="text-xs text-gray">{t('teacher.suivi.stats.students', 'Élèves')}</p>
                    </div>
                  </div>
                </div>
                <div className="bg-white rounded-2xl p-5 shadow-sm border border-black/5">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-green-50 flex items-center justify-center">
                      <Trophy className="w-5 h-5 text-green-600" />
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-navy">{avgProgress}%</p>
                       <p className="text-xs text-gray">{t('teacher.suivi.stats.avgProgress', 'Progression Moyenne')}</p>
                    </div>
                  </div>
                </div>
                <div className="bg-white rounded-2xl p-5 shadow-sm border border-black/5">
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-xl ${blockedCount > 0 ? "bg-red-50" : "bg-green-50"} flex items-center justify-center`}>
                      <AlertTriangle className={`w-5 h-5 ${blockedCount > 0 ? "text-red-600" : "text-green-600"}`} />
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-navy">{blockedCount}</p>
                       <p className="text-xs text-gray">{t('teacher.suivi.stats.blocked', 'Élèves Bloqués')}</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Student table */}
              <div className="bg-white rounded-2xl shadow-sm border border-black/5 overflow-hidden">
                <div className="px-6 py-4 border-b border-black/5">
                  <h3 className="font-semibold text-navy">{selectedClassName} — {t('teacher.suivi.title', 'Suivi des Élèves')}</h3>
                </div>
                {students.length === 0 ? (
                  <div className="p-12 text-center text-gray">
                    {t('teacher.suivi.noClassSelected', 'Aucun élève dans cette classe.')}
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="bg-gray-50 border-b border-black/5">
                           <th className="text-left px-6 py-3 font-medium text-gray">{t('teacher.suivi.table.name', 'Élève')}</th>
                           <th className="text-left px-4 py-3 font-medium text-gray">{t('teacher.suivi.table.progress', 'Progression')}</th>
                           <th className="text-left px-4 py-3 font-medium text-gray">{t('teacher.suivi.table.lastQuiz', 'Dernier Quiz')}</th>
                           <th className="text-left px-4 py-3 font-medium text-gray">{t('teacher.suivi.table.packStatus', 'Statut Pack')}</th>
                           <th className="text-right px-6 py-3 font-medium text-gray">{t('teacher.suivi.table.contact', 'Contacter')}</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-black/5">
                        {students.map((s) => (
                          <tr key={s.student_id} className="hover:bg-gray-50/50 transition-colors">
                            <td className="px-6 py-4">
                              <div className="flex items-center gap-3">
                                <div className="w-8 h-8 rounded-full bg-orange/10 flex items-center justify-center text-sm font-semibold text-orange">
                                  {(s.student_name || "?")[0].toUpperCase()}
                                </div>
                                <div>
                                  <p className="font-medium text-navy">{s.student_name || "—"}</p>
                                  <p className="text-xs text-gray">{s.student_email}</p>
                                </div>
                              </div>
                            </td>
                            <td className="px-4 py-4">
                              <ProgressBar percent={s.progress_percent} />
                              <p className="text-xs text-gray mt-1">
                                {s.courses_enrolled}/{s.total_class_courses} {t('teacher.classroom.courses', 'cours')}
                              </p>
                            </td>
                            <td className="px-4 py-4">
                              {s.last_quiz_score !== null ? (
                                <div>
                                  <span className={`inline-flex items-center gap-1 text-sm font-semibold ${
                                    s.last_quiz_passed ? "text-green-600" : "text-red-600"
                                  }`}>
                                    {s.last_quiz_score}%
                                  </span>
                                  {s.last_quiz_passed !== null && (
                                    <span className={`ml-1 text-xs ${s.last_quiz_passed ? "text-green-500" : "text-red-500"}`}>
                                      {s.last_quiz_passed ? "✓" : "✗"}
                                    </span>
                                  )}
                                  {s.last_quiz_at && (
                                    <p className="text-xs text-gray flex items-center gap-1 mt-0.5">
                                      <Clock className="w-3 h-3" />
                                      {new Date(s.last_quiz_at).toLocaleDateString("fr-FR")}
                                    </p>
                                  )}
                                </div>
                              ) : (
                                <span className="text-xs text-gray">—</span>
                              )}
                            </td>
                            <td className="px-4 py-4">
                              {packBadge(s.pack_status, s.pack_label)}
                            </td>
                            <td className="px-6 py-4 text-right">
                              {(s.pack_status === "expired" || s.pack_status === "quota_exceeded") && (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => navigate("/dashboard/inbox")}
                                   title={t('teacher.suivi.table.contact', 'Contacter')}
                                >
                                  <Mail className="w-4 h-4 text-orange" />
                                </Button>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
