import { X, FileText } from "lucide-react";
import { Modal } from "../../../../components/ui";

interface CoursePreviewModalProps {
  previewCourse: any;
  onClose: () => void;
}

export function CoursePreviewModal({ previewCourse, onClose }: CoursePreviewModalProps) {
  if (!previewCourse) return null;

  return (
    <Modal open={!!previewCourse} onClose={onClose} title="Aperçu du cours" maxWidth="max-w-3xl">
      {previewCourse.cover_url && (
        <img src={previewCourse.cover_url} alt="" className="w-full h-48 object-cover rounded-xl mb-4" />
      )}
      <div className="flex items-center gap-2 mb-2">
        <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${
          previewCourse.status === "published" ? "bg-green-100 text-green-800" :
          previewCourse.status === "archived" ? "bg-orange-100 text-orange-700" : "bg-yellow-100 text-yellow-800"
        }`}>
          {previewCourse.status === "published" ? "Publié" : previewCourse.status === "archived" ? "Archivé" : "Brouillon"}
        </span>
        <span className="text-xs text-gray-500">{previewCourse.level}</span>
        {previewCourse.category && <span className="text-xs text-gray-500">/ {previewCourse.category}</span>}
      </div>
      <h2 className="text-2xl font-bold text-navy mb-2">{previewCourse.title}</h2>
      {previewCourse.short_description && <p className="text-gray-600 mb-4">{previewCourse.short_description}</p>}
      {previewCourse.description && <p className="text-gray-600 mb-4">{previewCourse.description}</p>}

      <div className="grid grid-cols-3 gap-4 mb-6 text-sm">
        {[
          { label: "Chapitres", value: previewCourse.total_modules },
          { label: "Leçons", value: previewCourse.total_lessons },
          { label: "Durée", value: `${previewCourse.total_duration_minutes || 0} min` },
        ].map((s) => (
          <div key={s.label} className="bg-gray-50 rounded-lg p-3 text-center">
            <div className="font-bold text-navy">{s.value}</div>
            <div className="text-gray-500">{s.label}</div>
          </div>
        ))}
      </div>

      {previewCourse.prerequisites && (
        <div className="mb-4">
          <h4 className="font-medium text-sm mb-1">Prérequis</h4>
          <p className="text-sm text-gray-600">{previewCourse.prerequisites}</p>
        </div>
      )}
      {previewCourse.learning_objectives && (
        <div className="mb-4">
          <h4 className="font-medium text-sm mb-1">Objectifs pédagogiques</h4>
          <p className="text-sm text-gray-600">{previewCourse.learning_objectives}</p>
        </div>
      )}

      {previewCourse.modules?.length > 0 && (
        <div>
          <h4 className="font-medium text-sm mb-2">Programme du cours</h4>
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
                        {les.is_free && <span className="text-green-600">(Gratuit)</span>}
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
    </Modal>
  );
}
