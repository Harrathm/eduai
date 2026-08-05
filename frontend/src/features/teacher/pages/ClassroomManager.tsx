import { useState, useEffect } from "react";
import { useAuthStore } from "../../../store/authStore";
import { Plus, Users, Trash2, UserPlus } from "lucide-react";
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
    if (!confirm("Supprimer cette classe?")) return;
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
              Classroom <span className="italic text-orange">Manager</span>
            </h1>
            <p className="text-gray mt-2">Gerez vos classes</p>
          </div>
          <button
            onClick={() => setShowNewClass(true)}
            className="flex items-center gap-2 px-5 py-3 bg-orange text-white rounded-xl font-medium"
          >
            <Plus className="w-5 h-5" />
            Nouvelle Classe
          </button>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-1 space-y-4">
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
            <h2 className="text-lg font-semibold text-navy mb-4">Mes Classes</h2>
            {loading ? (
              <div className="text-center py-8 text-gray">Chargement...</div>
            ) : classes.length === 0 ? (
              <div className="text-center py-8 text-gray">
                <Users className="w-10 h-10 mx-auto mb-3 opacity-30" />
                <p>Aucune classe</p>
                <button
                  onClick={() => setShowNewClass(true)}
                  className="mt-3 text-orange text-sm font-medium"
                >
                  + Creer une classe
                </button>
              </div>
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
                          {cls.students_count} eleves · {cls.courses_count} cours
                        </div>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteClass(cls.id);
                        }}
                        className={`p-2 rounded-lg ${
                          selectedClass === cls.id
                            ? "hover:bg-white/20"
                            : "hover:bg-red-100 text-red-600"
                        }`}
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
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
              <Users className="w-16 h-16 mx-auto mb-4 opacity-30" />
              <p>Selectionnez une classe pour voir les details</p>
            </div>
          ) : (
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-semibold text-navy">Eleves</h2>
                <button
                  onClick={() => setShowAddStudent(true)}
                  className="flex items-center gap-2 text-sm text-orange font-medium"
                >
                  <UserPlus className="w-4 h-4" />
                  Ajouter eleve
                </button>
              </div>
              {students.length === 0 ? (
                <div className="text-center py-8 text-gray">
                  Aucun eleve dans cette classe
                </div>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {students.map((s) => (
                    <div
                      key={s.id}
                      className="flex items-center gap-2 bg-cream-m px-3 py-2 rounded-xl"
                    >
                      <span className="text-sm">{s.student_name}</span>
                      <button
                        onClick={() => removeStudent(s.student_id)}
                        className="p-1 hover:bg-red-100 rounded text-red-600"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
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

      {showNewClass && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-3xl max-w-md w-full p-8">
            <h2 className="text-2xl font-semibold text-navy mb-6">
              Nouvelle Classe
            </h2>
            <div className="space-y-4">
              <input
                type="text"
                value={newClassName}
                onChange={(e) => setNewClassName(e.target.value)}
                className="w-full px-5 py-3 bg-cream-m rounded-xl border border-black/5"
                placeholder="Nom de la classe..."
              />
              <textarea
                value={newClassDescription}
                onChange={(e) => setNewClassDescription(e.target.value)}
                className="w-full px-5 py-3 bg-cream-m rounded-xl border border-black/5 min-h-[80px]"
                placeholder="Description (optionnel)..."
              />
            </div>
            <div className="flex gap-4 mt-6">
              <button
                onClick={() => setShowNewClass(false)}
                className="flex-1 py-3 bg-cream-m rounded-xl"
              >
                Annuler
              </button>
              <button
                onClick={createClass}
                className="flex-1 py-3 bg-orange text-white rounded-xl font-medium"
              >
                Creer
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
