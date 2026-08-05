import { Save, FileText, Video, HelpCircle, File, Image, Link } from "lucide-react";
import { Button, Input, Modal } from "../../../../components/ui";
import type { LessonForm } from "../../hooks/useCourseEditor";

const LESSON_TYPES = [
  { value: "text", label: "Texte", icon: FileText },
  { value: "video", label: "Vidéo", icon: Video },
  { value: "pdf", label: "Document PDF", icon: File },
  { value: "image", label: "Image", icon: Image },
  { value: "link", label: "Lien externe", icon: Link },
  { value: "quiz", label: "Quiz/Examen", icon: HelpCircle },
];

interface LessonEditorProps {
  open: boolean;
  form: LessonForm;
  onFormChange: (form: LessonForm) => void;
  onClose: () => void;
  onSave: () => void;
}

export function LessonEditor({ open, form, onFormChange, onClose, onSave }: LessonEditorProps) {
  return (
    <Modal open={open} onClose={onClose} title="Éditer la leçon" maxWidth="max-w-2xl">
      <div className="space-y-4">
        {/* Type selector */}
        <div>
          <label className="block text-sm font-medium mb-2">Type de contenu</label>
          <div className="grid grid-cols-3 gap-2">
            {LESSON_TYPES.map(t => {
              const Icon = t.icon;
              return (
                <button key={t.value}
                  onClick={() => onFormChange({ ...form, lesson_type: t.value })}
                  className={`p-3 rounded-lg border-2 flex flex-col items-center gap-2 ${
                    form.lesson_type === t.value ? "border-navy-600 bg-navy-50" : "border-gray-200 hover:border-gray-300"
                  }`}>
                  <Icon className="w-5 h-5" />
                  <span className="text-sm">{t.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Common fields */}
        <Input label="Titre" value={form.title} onChange={e => onFormChange({ ...form, title: e.target.value })} />
        <Input label="Durée (minutes)" type="number" value={form.duration_minutes} onChange={e => onFormChange({ ...form, duration_minutes: Number(e.target.value) })} />
        <div className="flex items-center gap-2">
          <input type="checkbox" checked={form.is_free} onChange={e => onFormChange({ ...form, is_free: e.target.checked })} className="w-4 h-4" />
          <label className="text-sm">Leçon gratuite (visible sans inscription)</label>
        </div>

        {/* Type-specific fields */}
        {form.lesson_type === "text" && (
          <div>
            <label className="block text-sm font-medium mb-1">Contenu texte</label>
            <textarea value={form.content_text} onChange={e => onFormChange({ ...form, content_text: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg font-mono text-sm" rows={10}
              placeholder="Entrez le contenu de la leçon..." />
          </div>
        )}

        {form.lesson_type === "video" && (
          <div>
            <Input label="URL Vidéo" type="url" value={form.video_url} onChange={e => onFormChange({ ...form, video_url: e.target.value })} placeholder="https://..." />
            <p className="text-xs text-gray-500 mt-1">MP4, YouTube, Vimeo...</p>
          </div>
        )}

        {form.lesson_type === "pdf" && (
          <Input label="URL PDF" type="url" value={form.pdf_url} onChange={e => onFormChange({ ...form, pdf_url: e.target.value })} placeholder="https://.../file.pdf" />
        )}

        {form.lesson_type === "image" && (
          <div>
            <label className="block text-sm font-medium mb-1">URLs Images (une par ligne ou JSON)</label>
            <textarea value={form.image_urls} onChange={e => onFormChange({ ...form, image_urls: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg font-mono text-sm" rows={3}
              placeholder={"https://image1.jpg\nhttps://image2.jpg"} />
          </div>
        )}

        {form.lesson_type === "link" && (
          <>
            <Input label="Titre du lien" value={form.link_title} onChange={e => onFormChange({ ...form, link_title: e.target.value })} />
            <Input label="URL" type="url" value={form.link_url} onChange={e => onFormChange({ ...form, link_url: e.target.value })} placeholder="https://..." />
          </>
        )}

        {form.lesson_type === "quiz" && (
          <div className="p-4 bg-orange-50 rounded-lg">
            <p className="text-sm">Quiz/Examen — Configurez le quiz dans l'éditeur de quiz.</p>
          </div>
        )}
      </div>

      <div className="flex justify-end gap-2 mt-6">
        <Button variant="ghost" onClick={onClose}>Annuler</Button>
        <Button onClick={onSave}><Save className="w-4 h-4" /> Enregistrer</Button>
      </div>
    </Modal>
  );
}
