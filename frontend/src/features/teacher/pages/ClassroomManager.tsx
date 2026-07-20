import { useState, useEffect } from "react";
import { useAuthStore } from "../../../store/authStore";
import { Plus, Users, BookOpen, FileText, Trash2, Clock, UserPlus } from "lucide-react";

const API_URL = "";

interface Class {
  id: number;
  name: string;
  student_count: number;
  course_count: number;
}

interface Student {
  id: number;
  full_name: string;
  email: string;
}

interface Assignment {
  id: number;
  title: string;
  due_date: string;
  status: string;
}

export default function ClassroomManager() {
  const { token, user } = useAuthStore();
  const [classes, setClasses] = useState<Class[]>([]);
  const [selectedClass, setSelectedClass] = useState<number | null>(null);
  const [students, setStudents] = useState<Student[]>([]);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [showNewClass, setShowNewClass] = useState(false);
  const [showNewAssignment, setShowNewAssignment] = useState(false);
  const [newClassName, setNewClassName] = useState("");
  const [newAssignment, setNewAssignment] = useState({
    title: "",
    description: "",
    due_date: "",
  });
  const [loading, setLoading] = useState(true);
  const [showAddStudent, setShowAddStudent] = useState(false);
  const [availableStudents, setAvailableStudents] = useState<Student[]>([]);
  const [studentSearch, setStudentSearch] = useState("");

  useEffect(() => {
    fetchClasses();
  }, [token]);

  useEffect(() => {
    if (selectedClass) {
      fetchClassDetails(selectedClass);
    }
  }, [selectedClass]);

  const fetchClasses = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/lms/classes`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) setClasses(await res.json());
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const fetchClassDetails = async (classId: number) => {
    if (!token) return;
    try {
      const [studentsRes, assignmentsRes] = await Promise.all([
        fetch(`${API_URL}/api/lms/classes/${classId}/students`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        fetch(`${API_URL}/api/lms/classes/${classId}/assignments`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
      ]);
      if (studentsRes.ok) setStudents(await studentsRes.json());
      if (assignmentsRes.ok) setAssignments(await assignmentsRes.json());
    } catch (err) {
      console.error(err);
    }
  };

  const createClass = async () => {
    if (!token || !newClassName) return;
    try {
      const res = await fetch(`${API_URL}/api/lms/classes`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ name: newClassName }),
      });
      if (res.ok) {
        setShowNewClass(false);
        setNewClassName("");
        fetchClasses();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const createAssignment = async () => {
    if (!token || !selectedClass || !newAssignment.title) return;
    try {
      const res = await fetch(`${API_URL}/api/lms/classes/${selectedClass}/assignments`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(newAssignment),
      });
      if (res.ok) {
        setShowNewAssignment(false);
        setNewAssignment({ title: "", description: "", due_date: "" });
        fetchClassDetails(selectedClass);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const removeStudent = async (studentId: number) => {
    if (!token || !selectedClass) return;
    try {
      const res = await fetch(
        `${API_URL}/api/lms/classes/${selectedClass}/students/${studentId}`,
        { method: "DELETE", headers: { Authorization: `Bearer ${token}` } }
      );
      if (res.ok) fetchClassDetails(selectedClass);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchAvailableStudents = async (searchTerm = "") => {
    if (!token || !selectedClass) return;
    try {
      const params = new URLSearchParams();
      if (searchTerm) params.set("search", searchTerm);
      const res = await fetch(
        `${API_URL}/api/lms/classes/${selectedClass}/available-students?${params.toString()}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (res.ok) setAvailableStudents(await res.json());
    } catch (err) {
      console.error(err);
    }
  };

  const addStudent = async (studentId: number) => {
    if (!token || !selectedClass) return;
    try {
      const res = await fetch(`${API_URL}/api/lms/enrollments`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ classroom_id: selectedClass, student_id: studentId }),
      });
      if (res.ok) {
        fetchClassDetails(selectedClass);
        fetchAvailableStudents();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const deleteClass = async (classId: number) => {
    if (!token || !confirm("Supprimer cette classe?")) return;
    try {
      const res = await fetch(`${API_URL}/api/lms/classes/${classId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        setSelectedClass(null);
        fetchClasses();
      }
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
            <p className="text-gray mt-2">Gérez vos classes et devoirs</p>
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
        {/* Class List */}
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
                  + Créer une classe
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
                          {cls.student_count} élèves · {cls.course_count} cours
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

        {/* Class Details */}
        <div className="lg:col-span-2 space-y-4">
          {!selectedClass ? (
            <div className="bg-white rounded-2xl p-12 text-center text-gray shadow-sm border border-black/5">
              <Users className="w-16 h-16 mx-auto mb-4 opacity-30" />
              <p>Sélectionnez une classe pour voir les détails</p>
            </div>
          ) : (
            <>
              {/* Students */}
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-lg font-semibold text-navy">Élèves</h2>
                  <button
                    onClick={() => { setShowAddStudent(true); setStudentSearch(""); fetchAvailableStudents(""); }}
                    className="flex items-center gap-2 text-sm text-orange font-medium"
                  >
                    <UserPlus className="w-4 h-4" />
                    Ajouter élève
                  </button>
                </div>
                {students.length === 0 ? (
                  <div className="text-center py-8 text-gray">
                    Aucun élève dans cette classe
                  </div>
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {students.map((s) => (
                      <div
                        key={s.id}
                        className="flex items-center gap-2 bg-cream-m px-3 py-2 rounded-xl"
                      >
                        <span className="text-sm">{s.full_name}</span>
                        <button
                          onClick={() => removeStudent(s.id)}
                          className="p-1 hover:bg-red-100 rounded text-red-600"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Assignments */}
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-lg font-semibold text-navy">Devoirs</h2>
                  <button
                    onClick={() => setShowNewAssignment(true)}
                    className="flex items-center gap-2 text-sm text-orange font-medium"
                  >
                    <Plus className="w-4 h-4" />
                    Nouveau devoir
                  </button>
                </div>
                {assignments.length === 0 ? (
                  <div className="text-center py-8 text-gray">
                    Aucun devoir
                  </div>
                ) : (
                  <div className="space-y-3">
                    {assignments.map((a) => (
                      <div
                        key={a.id}
                        className="flex items-center justify-between p-4 bg-cream-m rounded-xl"
                      >
                        <div className="flex items-center gap-3">
                          <FileText className="w-5 h-5 text-gray" />
                          <span className="font-medium">{a.title}</span>
                        </div>
                        <div className="flex items-center gap-4">
                          <span className="flex items-center gap-1 text-sm text-gray">
                            <Clock className="w-4 h-4" />
                            {new Date(a.due_date).toLocaleDateString("fr-FR")}
                          </span>
                          <span
                            className={`px-2 py-0.5 text-xs rounded-full ${
                              a.status === "active"
                                ? "bg-green-100 text-green-700"
                                : "bg-gray-100 text-gray-700"
                            }`}
                          >
                            {a.status}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>

      {/* Add Student Modal */}
      {showAddStudent && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-3xl max-w-md w-full p-8 max-h-[80vh] overflow-y-auto">
            <h2 className="text-2xl font-semibold text-navy mb-6">
              Ajouter un élève
            </h2>
            <input
              type="text"
              value={studentSearch}
              onChange={(e) => {
                setStudentSearch(e.target.value);
                fetchAvailableStudents(e.target.value);
              }}
              className="w-full px-5 py-3 bg-cream-m rounded-xl border border-black/5 mb-4"
              placeholder="Rechercher par nom ou email..."
              autoFocus
            />
            {availableStudents.length === 0 ? (
              <p className="text-center text-gray py-4">Aucun élève disponible</p>
            ) : (
              <div className="space-y-2">
                {availableStudents.map((s) => (
                  <div
                    key={s.id}
                    className="flex items-center justify-between p-3 bg-cream-m rounded-xl"
                  >
                    <div>
                      <div className="font-medium">{s.full_name}</div>
                      <div className="text-sm text-gray">{s.email}</div>
                    </div>
                    <button
                      onClick={() => addStudent(s.id)}
                      className="px-3 py-1 bg-orange text-white text-sm rounded-lg font-medium"
                    >
                      Ajouter
                    </button>
                  </div>
                ))}
              </div>
            )}
            <div className="mt-6">
              <button
                onClick={() => { setShowAddStudent(false); setStudentSearch(""); }}
                className="w-full py-3 bg-cream-m rounded-xl"
              >
                Fermer
              </button>
            </div>
          </div>
        </div>
      )}

      {/* New Class Modal */}
      {showNewClass && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-3xl max-w-md w-full p-8">
            <h2 className="text-2xl font-semibold text-navy mb-6">
              Nouvelle Classe
            </h2>
            <input
              type="text"
              value={newClassName}
              onChange={(e) => setNewClassName(e.target.value)}
              className="w-full px-5 py-3 bg-cream-m rounded-xl border border-black/5 mb-6"
              placeholder="Nom de la classe..."
            />
            <div className="flex gap-4">
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
                Créer
              </button>
            </div>
          </div>
        </div>
      )}

      {/* New Assignment Modal */}
      {showNewAssignment && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-3xl max-w-md w-full p-8">
            <h2 className="text-2xl font-semibold text-navy mb-6">
              Nouveau Devoir
            </h2>
            <div className="space-y-4">
              <input
                type="text"
                value={newAssignment.title}
                onChange={(e) =>
                  setNewAssignment({ ...newAssignment, title: e.target.value })
                }
                className="w-full px-5 py-3 bg-cream-m rounded-xl border border-black/5"
                placeholder="Titre du devoir..."
              />
              <textarea
                value={newAssignment.description}
                onChange={(e) =>
                  setNewAssignment({
                    ...newAssignment,
                    description: e.target.value,
                  })
                }
                className="w-full px-5 py-3 bg-cream-m rounded-xl border border-black/5 min-h-[100px]"
                placeholder="Instructions..."
              />
              <input
                type="date"
                value={newAssignment.due_date}
                onChange={(e) =>
                  setNewAssignment({ ...newAssignment, due_date: e.target.value })
                }
                className="w-full px-5 py-3 bg-cream-m rounded-xl border border-black/5"
              />
            </div>
            <div className="flex gap-4 mt-6">
              <button
                onClick={() => setShowNewAssignment(false)}
                className="flex-1 py-3 bg-cream-m rounded-xl"
              >
                Annuler
              </button>
              <button
                onClick={createAssignment}
                className="flex-1 py-3 bg-orange text-white rounded-xl font-medium"
              >
                Créer
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}