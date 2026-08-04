import { useState, useEffect, useCallback } from "react";
import { Search, X, UserPlus, Users } from "lucide-react";

const API_URL = "";

interface SearchResult {
  id: number;
  full_name: string;
  email: string;
  niveau_scolaire: string | null;
}

interface AddStudentModalProps {
  token: string;
  classId: number;
  open: boolean;
  onClose: () => void;
  onEnrolled: () => void;
}

export default function AddStudentModal({ token, classId, open, onClose, onEnrolled }: AddStudentModalProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [enrolling, setEnrolling] = useState<number | null>(null);

  const searchStudents = useCallback(async (query: string) => {
    if (query.trim().length < 2) {
      setSearchResults([]);
      return;
    }
    setSearching(true);
    try {
      const res = await fetch(
        `${API_URL}/api/teacher/students/search?q=${encodeURIComponent(query)}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (res.ok) {
        setSearchResults(await res.json());
      }
    } catch (err) {
      console.error(err);
    }
    setSearching(false);
  }, [token]);

  useEffect(() => {
    const timer = setTimeout(() => {
      if (open) searchStudents(searchQuery);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery, open, searchStudents]);

  useEffect(() => {
    if (!open) {
      setSearchQuery("");
      setSearchResults([]);
    }
  }, [open]);

  const enrollStudent = async (studentId: number) => {
    setEnrolling(studentId);
    try {
      const res = await fetch(
        `${API_URL}/api/teacher/classes/${classId}/students`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ student_id: studentId }),
        }
      );
      if (res.ok) {
        onEnrolled();
        setSearchResults((prev) => prev.filter((s) => s.id !== studentId));
      }
    } catch (err) {
      console.error(err);
    }
    setEnrolling(null);
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-3xl max-w-md w-full p-8 max-h-[80vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-semibold text-navy">Ajouter un eleve</h2>
          <button onClick={onClose} className="p-2 hover:bg-cream-m rounded-lg">
            <X className="w-5 h-5 text-gray" />
          </button>
        </div>

        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full ps-11 pe-4 py-3 bg-cream-m rounded-xl border border-black/5 focus:outline-none focus:ring-2 focus:ring-orange/30"
            placeholder="Rechercher par nom ou email..."
            autoFocus
          />
        </div>

        <div className="space-y-2">
          {searching && (
            <div className="text-center py-4 text-gray text-sm">Recherche en cours...</div>
          )}
          {!searching && searchQuery.trim().length >= 2 && searchResults.length === 0 && (
            <div className="text-center py-8 text-gray">
              <Users className="w-8 h-8 mx-auto mb-2 opacity-30" />
              <p className="text-sm">Aucun eleve trouve</p>
            </div>
          )}
          {!searching && searchQuery.trim().length < 2 && (
            <div className="text-center py-8 text-gray">
              <Search className="w-8 h-8 mx-auto mb-2 opacity-30" />
              <p className="text-sm">Tapez au moins 2 caracteres pour rechercher</p>
            </div>
          )}
          {searchResults.map((student) => (
            <div
              key={student.id}
              className="flex items-center justify-between p-3 bg-cream-m rounded-xl hover:bg-cream transition-colors"
            >
              <div className="flex-1 min-w-0">
                <div className="font-medium text-navy truncate">{student.full_name}</div>
                <div className="text-sm text-gray truncate">{student.email}</div>
                {student.niveau_scolaire && (
                  <div className="text-xs text-gray/70">{student.niveau_scolaire}</div>
                )}
              </div>
              <button
                onClick={() => enrollStudent(student.id)}
                disabled={enrolling === student.id}
                className="ml-3 flex items-center gap-1 px-3 py-2 bg-orange text-white rounded-lg text-sm font-medium hover:bg-orange/90 disabled:opacity-50 shrink-0"
              >
                {enrolling === student.id ? (
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : (
                  <UserPlus className="w-4 h-4" />
                )}
                Ajouter
              </button>
            </div>
          ))}
        </div>

        <div className="mt-6">
          <button onClick={onClose} className="w-full py-3 bg-cream-m rounded-xl font-medium">
            Fermer
          </button>
        </div>
      </div>
    </div>
  );
}
