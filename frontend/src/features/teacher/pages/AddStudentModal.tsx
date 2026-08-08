import { useState, useEffect, useCallback } from "react";
import { useTranslation } from 'react-i18next';
import { Search, UserPlus, Users } from "lucide-react";
import { Button, Modal } from "../../../components/ui";
import { studentSearchApi } from "../../../api";

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
  const { t } = useTranslation();
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
      const data = await studentSearchApi.search(query);
      setSearchResults(data);
    } catch (err) {
      console.error(err);
    }
    setSearching(false);
  }, []);

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
      await studentSearchApi.addToClass(classId, studentId);
      onEnrolled();
      setSearchResults((prev) => prev.filter((s) => s.id !== studentId));
    } catch (err) {
      console.error(err);
    }
    setEnrolling(null);
  };

  return (
    <Modal open={open} onClose={onClose} title={t('teacher.addStudent.title')} maxWidth="max-w-md">
      <div className="max-h-[80vh] overflow-y-auto">
        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full ps-11 pe-4 py-3 bg-cream-m rounded-xl border border-black/5 focus:outline-none focus:ring-2 focus:ring-orange/30"
            placeholder={t('teacher.addStudent.searchPlaceholder')}
            autoFocus
          />
        </div>

        <div className="space-y-2">
          {searching && (
            <div className="text-center py-4 text-gray text-sm">{t('teacher.addStudent.searching')}</div>
          )}
          {!searching && searchQuery.trim().length >= 2 && searchResults.length === 0 && (
            <div className="text-center py-8 text-gray">
              <Users className="w-8 h-8 mx-auto mb-2 opacity-30" />
              <p className="text-sm">{t('teacher.addStudent.noResults')}</p>
            </div>
          )}
          {!searching && searchQuery.trim().length < 2 && (
            <div className="text-center py-8 text-gray">
              <Search className="w-8 h-8 mx-auto mb-2 opacity-30" />
              <p className="text-sm">{t('teacher.addStudent.hint')}</p>
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
              <Button
                variant="primary"
                size="sm"
                onClick={() => enrollStudent(student.id)}
                disabled={enrolling === student.id}
                loading={enrolling === student.id}
              >
                <UserPlus className="w-4 h-4" />
                {t('teacher.addStudent.addButton')}
              </Button>
            </div>
          ))}
        </div>

        <div className="mt-6">
          <Button variant="ghost" onClick={onClose}>
            {t('teacher.addStudent.closeButton')}
          </Button>
        </div>
      </div>
    </Modal>
  );
}
