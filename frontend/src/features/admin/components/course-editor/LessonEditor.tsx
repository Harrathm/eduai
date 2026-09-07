import { Save, FileText, Video, HelpCircle, File, Image, Link, FileCode } from "lucide-react";
import { Button, Input, Modal } from "../../../../components/ui";
import { RichTextEditor } from "../../../../components/ui/RichTextEditor";
import type { LessonForm } from "../../hooks/useCourseEditor";

const LESSON_TYPES = [
  { value: "text", label: "Texte", icon: FileText },
  { value: "video", label: "Vidéo", icon: Video },
  { value: "pdf", label: "Document PDF", icon: File },
  { value: "image", label: "Image", icon: Image },
  { value: "html", label: "Page HTML", icon: FileCode },
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
      <div className="max-h-[70vh] overflow-y-auto pr-1 space-y-4">
        {/* Type selector */}
        <div>
          <label className="block text-sm font-medium mb-2">Type de contenu</label>
          <div className="grid grid-cols-3 gap-2">
            {LESSON_TYPES.map(t => {
              const Icon = t.icon;
              return (
                <Button key={t.value}
                  variant="ghost"
                  size="md"
                  onClick={() => onFormChange({ ...form, lesson_type: t.value })}>
                  <Icon className="w-5 h-5" />
                  <span className="text-sm">{t.label}</span>
                </Button>
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
            <label className="block text-sm font-medium mb-1">Contenu texte (mise en page riche)</label>
            <RichTextEditor
              value={form.content_html}
              onChange={(html, text) => onFormChange({ ...form, content_html: html, content_text: text })}
            />
            <p className="text-xs text-gray-500 mt-1">Gras, italique, titres, couleurs, images, vidéos, listes... Le tout s'affichera comme une seule leçon enrichie.</p>
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

        {form.lesson_type === "html" && (
          <div>
            <label className="block text-sm font-medium mb-1">Code HTML</label>
            <textarea
              value={form.content_html}
              onChange={e => onFormChange({ ...form, content_html: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg font-mono text-sm"
              rows={14}
              placeholder={"<section>\n  <h1>Ma page interactive</h1>\n  <p>Écrivez votre code HTML ici...</p>\n</section>"}
            />
            <p className="text-xs text-gray-500 mt-1">Le code HTML saisi sera affiché à l'apprenant comme une page interactive complète.</p>
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

      <div className="flex justify-end gap-2 mt-4 pt-4 border-t">
        <Button variant="ghost" onClick={onClose}>Annuler</Button>
        <Button onClick={onSave}><Save className="w-4 h-4" /> Enregistrer</Button>
      </div>
    </Modal>
  );
}
