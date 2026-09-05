import { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { useAuthStore } from "../../../store/authStore";
import {
  Plus, Users, Trash2, UserPlus, AlertCircle,
  BookOpen, Route, ChevronDown, ChevronUp,
} from "lucide-react";
import { Button, Modal, EmptyState, PageSpinner } from "../../../components/ui";
import AddStudentModal from "./AddStudentModal";
import {
  teacherClassesApi, teacherCoursesApi, teacherParcoursClassApi, api,
} from "../../../api";

/* ── Types ─────────────────────────────────────────────────────────────── */

interface Class {
  id: number;
  teacher_id: number;
  school_id: number;
  name: string;
  description: string;
  code: string;
  is_active: boolean;
  courses_count: number;
  parcours_count: number;
  students_count: number;
}

interface Student {
  id: number;
  student_id: number;
  class_id: number;
  student_name: string;
  student_email: string;
  enrolled_at: string;
  is_active: boolean;
}

interface ClassCourse {
  id: number;
  class_id: number;
  course_id: number;
  course_title: string | null;
  assigned_at: string | null;
  is_active: boolean;
}

interface ClassParcours {
  id: number;
  class_id: number;
  parcours_id: number;
  parcours_titre: string | null;
  parcours_matiere: string | null;
  assigned_at: string | null;
  is_active: boolean;
}

/* ── Component ─────────────────────────────────────────────────────────── */

export default function ClassroomManager() {
  const { t } = useTranslation();
  const { token, user } = useAuthStore();

  /* class list */
  const [classes, setClasses] = useState<Class[]>([]);
  const [selectedClass, setSelectedClass] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  /* create class modal */
  const [showNewClass, setShowNewClass] = useState(false);
  const [newClassName, setNewClassName] = useState("");
  const [newClassDescription, setNewClassDescription] = useState("");

  /* students */
  const [students, setStudents] = useState<Student[]>([]);
  const [showAddStudent, setShowAddStudent] = useState(false);

  /* courses */
  const [classCourses, setClassCourses] = useState<ClassCourse[]>([]);
  const [myCourses, setMyCourses] = useState<any[]>([]);
  const [showAssignCourse, setShowAssignCourse] = useState(false);

  /* parcours */
  const [classParcours, setClassParcours] = useState<ClassParcours[]>([]);
  const [myParcours, setMyParcours] = useState<any[]>([]);
  const [showAssignParcours, setShowAssignParcours] = useState(false);

  /* expanded tabs in right panel */
  const [tab, setTab] = useState<"students" | "courses" | "parcours">("students");

  /* ── Fetch helpers ──────────────────────────────────────────────────── */

  const fetchClasses = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await teacherClassesApi.list();
      setClasses(Array.isArray(data) ? data : (data.items || data || []));
    } catch {
      setError(t("teacher.classroom.loadError"));
    }
    setLoading(false);
  }, [t]);

  const fetchClassDetails = useCallback(async (classId: number) => {
    try {
      const [sData, cData, pData] = await Promise.all([
        teacherClassesApi.listStudents(classId),
        teacherCoursesApi.listClassCourses(classId),
        teacherParcoursClassApi.listClassParcours(classId),
      ]);
      setStudents(Array.isArray(sData) ? sData : (sData.items || sData || []));
      setClassCourses(Array.isArray(cData) ? cData : (cData.items || cData || []));
      setClassParcours(Array.isArray(pData) ? pData : (pData.items || pData || []));
    } catch {
      setError(t("teacher.classroom.loadStudentsError"));
    }
  }, [t]);

  const fetchMyCourses = useCallback(async () => {
    try {
      const res: any = await api.get("/api/courses/my-courses");
      const items = Array.isArray(res) ? res : (res.items || res || []);
      setMyCourses(items);
    } catch { /* */ }
  }, []);

  const fetchMyParcours = useCallback(async () => {
    try {
      const res: any = await api.get("/api/pathway/parcours");
      const items = Array.isArray(res) ? res : (res.items || res || []);
      setMyParcours(items);
    } catch { /* */ }
  }, []);

  /* ── Effects ─────────────────────────────────────────────────────────── */

  useEffect(() => { fetchClasses(); }, [fetchClasses]);

  useEffect(() => {
    if (selectedClass) {
      fetchClassDetails(selectedClass);
      setTab("students");
    }
  }, [selectedClass, fetchClassDetails]);

  /* ── Actions ─────────────────────────────────────────────────────────── */

  const createClass = async () => {
    if (!newClassName) return;
    try {
      await teacherClassesApi.create({ name: newClassName, description: newClassDescription });
      setShowNewClass(false);
      setNewClassName("");
      setNewClassDescription("");
      fetchClasses();
    } catch {
      setError(t("teacher.classroom.createError"));
    }
  };

  const deleteClass = async (classId: number) => {
    if (!confirm(t("teacher.classroom.confirmDelete"))) return;
    try {
      await teacherClassesApi.delete(classId);
      setSelectedClass(null);
      fetchClasses();
    } catch {
      setError(t("teacher.classroom.deleteError"));
    }
  };

  const removeStudent = async (studentId: number) => {
    if (!selectedClass) return;
    try {
      await teacherClassesApi.removeStudent(selectedClass, studentId);
      fetchClassDetails(selectedClass);
    } catch {
      setError(t("teacher.classroom.removeStudentError"));
    }
  };

  const assignCourse = async (courseId: number) => {
    if (!selectedClass) return;
    try {
      await teacherCoursesApi.assignCourse(selectedClass, courseId);
      setShowAssignCourse(false);
      fetchClassDetails(selectedClass);
    } catch (e: any) {
      setError(e?.message || t("teacher.classroom.assignCourseError"));
    }
  };

  const removeCourse = async (courseId: number) => {
    if (!selectedClass) return;
    try {
      await teacherCoursesApi.removeCourse(selectedClass, courseId);
      fetchClassDetails(selectedClass);
    } catch { /* */ }
  };

  const assignParcours = async (parcoursId: number) => {
    if (!selectedClass) return;
    try {
      await teacherParcoursClassApi.assignParcours(selectedClass, parcoursId);
      setShowAssignParcours(false);
      fetchClassDetails(selectedClass);
    } catch (e: any) {
      setError(e?.message || t("teacher.classroom.assignParcoursError"));
    }
  };

  const removeParcours = async (parcoursId: number) => {
    if (!selectedClass) return;
    try {
      await teacherParcoursClassApi.removeParcours(selectedClass, parcoursId);
      fetchClassDetails(selectedClass);
    } catch { /* */ }
  };

  /* ── Derived ─────────────────────────────────────────────────────────── */

  const assignedCourseIds = new Set(classCourses.map((c) => c.course_id));
  const assignedParcoursIds = new Set(classParcours.map((p) => p.parcours_id));
  const availableCourses = myCourses.filter((c: any) => !assignedCourseIds.has(c.id));
  const availableParcours = myParcours.filter((p: any) => !assignedParcoursIds.has(p.id));
  const selectedClassObj = classes.find((c) => c.id === selectedClass);

  /* ── Render ──────────────────────────────────────────────────────────── */

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-3xl p-8 shadow-sm border border-black/5">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-[300] text-navy">
              {t("teacher.classroom.title")}{" "}
              <span className="italic text-orange">{t("teacher.classroom.titleSuffix")}</span>
            </h1>
            <p className="text-gray mt-2">{t("teacher.classroom.subtitle")}</p>
          </div>
          <Button variant="primary" onClick={() => setShowNewClass(true)}>
            <Plus className="w-5 h-5" />
            {t("teacher.classroom.newClass")}
          </Button>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 px-4 py-3 text-sm text-red-600 bg-red-50 rounded-xl">
          <AlertCircle className="w-4 h-4 shrink-0" />
          {error}
          <button onClick={() => setError(null)} className="ml-auto text-red-400 hover:text-red-600">✕</button>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        {/* ── Left: class list ── */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
            <h2 className="text-lg font-semibold text-navy mb-4">{t("teacher.classroom.myClasses")}</h2>
            {loading ? (
              <PageSpinner message={t("teacher.classroom.loading")} />
            ) : classes.length === 0 ? (
              <EmptyState
                icon={<Users className="w-10 h-10" />}
                title={t("teacher.classroom.noClasses")}
                action={
                  <Button variant="ghost" size="sm" onClick={() => setShowNewClass(true)}>
                    + {t("teacher.classroom.createClass")}
                  </Button>
                }
              />
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
                          {cls.students_count} {t("teacher.classroom.students")}{" "}
                          · {cls.courses_count} {t("teacher.classroom.courses")}{" "}
                          · {cls.parcours_count || 0} {t("teacher.classroom.parcours")}
                        </div>
                      </div>
                      <Button
                        variant="danger"
                        size="sm"
                        onClick={(e) => { e.stopPropagation(); deleteClass(cls.id); }}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* ── Right: details ── */}
        <div className="lg:col-span-2 space-y-4">
          {!selectedClass ? (
            <div className="bg-white rounded-2xl p-12 text-center text-gray shadow-sm border border-black/5">
              <EmptyState icon={<Users className="w-16 h-16" />} title={t("teacher.classroom.selectClass")} />
            </div>
          ) : (
            <>
              {/* Tabs */}
              <div className="bg-white rounded-2xl shadow-sm border border-black/5 overflow-hidden">
                <div className="flex border-b border-black/5">
                  {([
                    ["students", <Users className="w-4 h-4" />, t("teacher.classroom.studentsTab")],
                    ["courses", <BookOpen className="w-4 h-4" />, t("teacher.classroom.coursesTab")],
                    ["parcours", <Route className="w-4 h-4" />, t("teacher.classroom.parcoursTab")],
                  ] as const).map(([key, icon, label]) => (
                    <button
                      key={key}
                      onClick={() => setTab(key)}
                      className={`flex items-center gap-2 px-6 py-4 text-sm font-medium transition-colors ${
                        tab === key
                          ? "text-orange border-b-2 border-orange"
                          : "text-gray hover:text-navy"
                      }`}
                    >
                      {icon}
                      {label}
                    </button>
                  ))}
                </div>

                <div className="p-6">
                  {/* ── Students tab ── */}
                  {tab === "students" && (
                    <div>
                      <div className="flex justify-between items-center mb-4">
                        <h3 className="font-semibold text-navy">
                          {t("teacher.classroom.studentsTitle")} ({students.length})
                        </h3>
                        <Button variant="ghost" size="sm" onClick={() => setShowAddStudent(true)}>
                          <UserPlus className="w-4 h-4" />
                          {t("teacher.classroom.addStudent")}
                        </Button>
                      </div>
                      {students.length === 0 ? (
                        <p className="text-center py-8 text-gray">{t("teacher.classroom.noStudents")}</p>
                      ) : (
                        <div className="flex flex-wrap gap-2">
                          {students.map((s) => (
                            <div key={s.id} className="flex items-center gap-2 bg-cream-m px-3 py-2 rounded-xl">
                              <span className="text-sm">{s.student_name}</span>
                              <Button variant="danger" size="sm" onClick={() => removeStudent(s.student_id)}>
                                <Trash2 className="w-3 h-3" />
                              </Button>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {/* ── Courses tab ── */}
                  {tab === "courses" && (
                    <div>
                      <div className="flex justify-between items-center mb-4">
                        <h3 className="font-semibold text-navy">
                          {t("teacher.classroom.assignedCourses")} ({classCourses.length})
                        </h3>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => { fetchMyCourses(); setShowAssignCourse(true); }}
                        >
                          <Plus className="w-4 h-4" />
                          {t("teacher.classroom.assignCourse")}
                        </Button>
                      </div>
                      {classCourses.length === 0 ? (
                        <p className="text-center py-8 text-gray">{t("teacher.classroom.noCourses")}</p>
                      ) : (
                        <div className="space-y-2">
                          {classCourses.map((cc) => (
                            <div key={cc.id} className="flex items-center justify-between bg-cream-m px-4 py-3 rounded-xl">
                              <div>
                                <div className="font-medium text-navy">{cc.course_title}</div>
                                <div className="text-xs text-gray">{cc.course_id}</div>
                              </div>
                              <Button variant="danger" size="sm" onClick={() => removeCourse(cc.course_id)}>
                                <Trash2 className="w-3 h-3" />
                              </Button>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {/* ── Parcours tab ── */}
                  {tab === "parcours" && (
                    <div>
                      <div className="flex justify-between items-center mb-4">
                        <h3 className="font-semibold text-navy">
                          {t("teacher.classroom.assignedParcours")} ({classParcours.length})
                        </h3>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => { fetchMyParcours(); setShowAssignParcours(true); }}
                        >
                          <Plus className="w-4 h-4" />
                          {t("teacher.classroom.assignParcours")}
                        </Button>
                      </div>
                      {classParcours.length === 0 ? (
                        <p className="text-center py-8 text-gray">{t("teacher.classroom.noParcours")}</p>
                      ) : (
                        <div className="space-y-2">
                          {classParcours.map((cp) => (
                            <div key={cp.id} className="flex items-center justify-between bg-cream-m px-4 py-3 rounded-xl">
                              <div>
                                <div className="font-medium text-navy">{cp.parcours_titre}</div>
                                <div className="text-xs text-gray">{cp.parcours_matiere}</div>
                              </div>
                              <Button variant="danger" size="sm" onClick={() => removeParcours(cp.parcours_id)}>
                                <Trash2 className="w-3 h-3" />
                              </Button>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* ── Modals ─────────────────────────────────────────────────────── */}

      {/* Add student modal */}
      {token && selectedClass && (
        <AddStudentModal
          token={token}
          classId={selectedClass}
          open={showAddStudent}
          onClose={() => setShowAddStudent(false)}
          onEnrolled={() => fetchClassDetails(selectedClass)}
        />
      )}

      {/* Create class modal */}
      <Modal open={showNewClass} onClose={() => setShowNewClass(false)} title={t("teacher.classroom.newClass")}>
        <div className="space-y-4">
          <input
            type="text"
            value={newClassName}
            onChange={(e) => setNewClassName(e.target.value)}
            className="w-full px-5 py-3 bg-cream-m rounded-xl border border-black/5"
            placeholder={t("teacher.classroom.classNamePlaceholder")}
          />
          <textarea
            value={newClassDescription}
            onChange={(e) => setNewClassDescription(e.target.value)}
            className="w-full px-5 py-3 bg-cream-m rounded-xl border border-black/5 min-h-[80px]"
            placeholder={t("teacher.classroom.descriptionPlaceholder")}
          />
        </div>
        <div className="flex gap-4 mt-6">
          <Button variant="ghost" className="flex-1" onClick={() => setShowNewClass(false)}>
            {t("teacher.classroom.btnCancel")}
          </Button>
          <Button variant="primary" className="flex-1" onClick={createClass}>
            {t("teacher.classroom.btnCreate")}
          </Button>
        </div>
      </Modal>

      {/* Assign course modal */}
      <Modal open={showAssignCourse} onClose={() => setShowAssignCourse(false)} title={t("teacher.classroom.assignCourseTitle")}>
        {availableCourses.length === 0 ? (
          <p className="text-center py-8 text-gray">{t("teacher.classroom.noMyCourses")}</p>
        ) : (
          <div className="space-y-2 max-h-80 overflow-y-auto">
            {availableCourses.map((c: any) => (
              <div key={c.id} className="flex items-center justify-between bg-cream-m px-4 py-3 rounded-xl">
                <div className="font-medium text-navy">{c.title}</div>
                <Button variant="primary" size="sm" onClick={() => assignCourse(c.id)}>
                  <Plus className="w-3 h-3" /> {t("teacher.classroom.btnAdd")}
                </Button>
              </div>
            ))}
          </div>
        )}
        <div className="flex justify-end mt-4">
          <Button variant="ghost" onClick={() => setShowAssignCourse(false)}>{t("teacher.classroom.btnCancel")}</Button>
        </div>
      </Modal>

      {/* Assign parcours modal */}
      <Modal open={showAssignParcours} onClose={() => setShowAssignParcours(false)} title={t("teacher.classroom.assignParcoursTitle")}>
        {availableParcours.length === 0 ? (
          <p className="text-center py-8 text-gray">{t("teacher.classroom.noMyParcours")}</p>
        ) : (
          <div className="space-y-2 max-h-80 overflow-y-auto">
            {availableParcours.map((p: any) => (
              <div key={p.id} className="flex items-center justify-between bg-cream-m px-4 py-3 rounded-xl">
                <div>
                  <div className="font-medium text-navy">{p.titre}</div>
                  <div className="text-xs text-gray">{p.matiere}</div>
                </div>
                <Button variant="primary" size="sm" onClick={() => assignParcours(p.id)}>
                  <Plus className="w-3 h-3" /> {t("teacher.classroom.btnAdd")}
                </Button>
              </div>
            ))}
          </div>
        )}
        <div className="flex justify-end mt-4">
          <Button variant="ghost" onClick={() => setShowAssignParcours(false)}>{t("teacher.classroom.btnCancel")}</Button>
        </div>
      </Modal>
    </div>
  );
}
