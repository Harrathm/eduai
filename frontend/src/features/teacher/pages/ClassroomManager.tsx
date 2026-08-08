import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useAuthStore } from "../../../store/authStore";
import { Plus, Users, Trash2, UserPlus } from "lucide-react";
import { Button, Modal, EmptyState, PageSpinner } from "../../../components/ui";
import AddStudentModal from "./AddStudentModal";
import { teacherClassesApi } from "../../../api";

interface Class {
  id: number;
  teacher_id: number;
  school_id: number;
  name: string;
  description: string;
  code: string;
  is_active: boolean;
  courses_count: number;
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

export default function ClassroomManager() {
  const { t } = useTranslation();
  const { token, user } = useAuthStore();
  const [classes, setClasses] = useState<Class[]>([]);
  const [selectedClass, setSelectedClass] = useState<number | null>(null);
  const [students, setStudents] = useState<Student[]>([]);
  const [showNewClass, setShowNewClass] = useState(false);
  const [newClassName, setNewClassName] = useState("");
  const [newClassDescription, setNewClassDescription] = useState("");
  const [loading, setLoading] = useState(true);
  const [showAddStudent, setShowAddStudent] = useState(false);

  useEffect(() => {
    fetchClasses();
  }, [token]);

  useEffect(() => {
    if (selectedClass) {
      fetchClassDetails(selectedClass);
    }
  }, [selectedClass]);

  const fetchClasses = async () => {
    setLoading(true);
    try {
      const data = await teacherClassesApi.list();
      setClasses(data.items || []);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const fetchClassDetails = async (classId: number) => {
    try {
      const data = await teacherClassesApi.listStudents(classId);
      setStudents(data.items || []);
    } catch (err) {
      console.error(err);
    }
  };

  const createClass = async () => {
    if (!newClassName) return;
    try {
      await teacherClassesApi.create({ name: newClassName, description: newClassDescription });
      setShowNewClass(false);
      setNewClassName("");
      setNewClassDescription("");
      fetchClasses();
    } catch (err) {
      console.error(err);
    }
  };

  const removeStudent = async (studentId: number) => {
    if (!selectedClass) return;
    try {
      await teacherClassesApi.removeStudent(selectedClass, studentId);
      fetchClassDetails(selectedClass);
    } catch (err) {
      console.error(err);
    }
  };

  const deleteClass = async (classId: number) => {
    if (!confirm(t('teacher.classroom.confirmDelete'))) return;
    try {
      await teacherClassesApi.delete(classId);
      setSelectedClass(null);
      fetchClasses();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-3xl p-8 shadow-sm border border-black/5">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-[300] text-navy">
              {t('teacher.classroom.title')} <span className="italic text-orange">{t('teacher.classroom.titleSuffix')}</span>
            </h1>
            <p className="text-gray mt-2">{t('teacher.classroom.subtitle')}</p>
          </div>
          <Button variant="primary" onClick={() => setShowNewClass(true)}>
            <Plus className="w-5 h-5" />
              {t('teacher.classroom.newClass')}
          </Button>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-1 space-y-4">
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
            <h2 className="text-lg font-semibold text-navy mb-4">{t('teacher.classroom.myClasses')}</h2>
            {loading ? (
              <PageSpinner message={t('teacher.classroom.loading')} />
            ) : classes.length === 0 ? (
              <EmptyState
                icon={<Users className="w-10 h-10" />}
                title={t('teacher.classroom.noClasses')}
                action={
                  <Button variant="ghost" size="sm" onClick={() => setShowNewClass(true)}>
                    + {t('teacher.classroom.createClass')}
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
                        <div className={`text-sm ${
                          selectedClass === cls.id ? "text-white/70" : "text-gray"
                        }`}>
                          {cls.students_count} {t('teacher.classroom.students')} · {cls.courses_count} {t('teacher.classroom.courses')}
                        </div>
                      </div>
                      <Button
                        variant="danger"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteClass(cls.id);
                        }}
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

        <div className="lg:col-span-2 space-y-4">
          {!selectedClass ? (
            <div className="bg-white rounded-2xl p-12 text-center text-gray shadow-sm border border-black/5">
              <EmptyState
                icon={<Users className="w-16 h-16" />}
                title={t('teacher.classroom.selectClass')}
              />
            </div>
          ) : (
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-semibold text-navy">{t('teacher.classroom.studentsTitle')}</h2>
                <Button variant="ghost" size="sm" onClick={() => setShowAddStudent(true)}>
                  <UserPlus className="w-4 h-4" />
                  {t('teacher.classroom.addStudent')}
                </Button>
              </div>
              {students.length === 0 ? (
                <div className="text-center py-8 text-gray">
                  {t('teacher.classroom.noStudents')}
                </div>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {students.map((s) => (
                    <div
                      key={s.id}
                      className="flex items-center gap-2 bg-cream-m px-3 py-2 rounded-xl"
                    >
                      <span className="text-sm">{s.student_name}</span>
                      <Button
                        variant="danger"
                        size="sm"
                        onClick={() => removeStudent(s.student_id)}
                      >
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

      {token && selectedClass && (
        <AddStudentModal
          token={token}
          classId={selectedClass}
          open={showAddStudent}
          onClose={() => setShowAddStudent(false)}
          onEnrolled={() => fetchClassDetails(selectedClass)}
        />
      )}

      <Modal open={showNewClass} onClose={() => setShowNewClass(false)} title={t('teacher.classroom.newClass')}>
        <div className="space-y-4">
          <input
            type="text"
            value={newClassName}
            onChange={(e) => setNewClassName(e.target.value)}
            className="w-full px-5 py-3 bg-cream-m rounded-xl border border-black/5"
            placeholder={t('teacher.classroom.classNamePlaceholder')}
          />
          <textarea
            value={newClassDescription}
            onChange={(e) => setNewClassDescription(e.target.value)}
            className="w-full px-5 py-3 bg-cream-m rounded-xl border border-black/5 min-h-[80px]"
            placeholder="Description (optionnel)..."
          />
        </div>
        <div className="flex gap-4 mt-6">
          <Button variant="ghost" className="flex-1" onClick={() => setShowNewClass(false)}>
            Annuler
          </Button>
          <Button variant="primary" className="flex-1" onClick={createClass}>
            Creer
          </Button>
        </div>
      </Modal>
    </div>
  );
}
