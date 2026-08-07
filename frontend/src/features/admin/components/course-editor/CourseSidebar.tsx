import { useState, useEffect } from "react";
import { ArrowLeft, Eye, EyeOff, Copy, Archive, Save, GripVertical, Plus, AlertCircle, LayoutGrid } from "lucide-react";
import { Button, Input } from "../../../../components/ui";
import { pathwayApi } from "../../../../api";
import { useAuthStore } from "../../../../store/authStore";
import type { Chapter } from "../../hooks/useCourseEditor";

interface CourseSidebarProps {
  course: any;
  chapters: Chapter[];
  activeChapter: number | null;
  saving: boolean;
  previewLoading: boolean;
  publishErrors: string[];
  onBack: () => void;
  onPreview: () => void;
  onDuplicate: () => void;
  onPublish: () => void;
  onUnpublish: () => void;
  onArchive: () => void;
  onSave: () => void;
  onAddChapter: () => void;
  onSetActiveChapter: (id: number | null) => void;
  onUpdateChapterTitle: (id: number, title: string) => void;
  onCourseFieldChange: (field: string, value: any) => void;
  onOpenBuilder?: () => void;
}

export function CourseSidebar({
  course, chapters, activeChapter, saving, previewLoading, publishErrors,
  onBack, onPreview, onDuplicate, onPublish, onUnpublish, onArchive,
  onSave, onAddChapter, onSetActiveChapter, onUpdateChapterTitle, onCourseFieldChange, onOpenBuilder,
}: CourseSidebarProps) {
  const { user } = useAuthStore();
  const isTeacher = user?.role === "teacher" || user?.activeRole === "teacher";
  const categoryCible = course.category_cible || "Scolaire";
  const isScolaire = categoryCible === "Scolaire";
  const [matieres, setMatieres] = useState<{id: number; nom: string}[]>([]);

  useEffect(() => {
    if (isScolaire && course.niveau_scolaire) {
      pathwayApi.getMatieresByNiveau(course.niveau_scolaire)
        .then(data => setMatieres(Array.isArray(data) ? data : []))
        .catch(() => setMatieres([]));
    }
  }, [isScolaire, course.niveau_scolaire]);

  const tagsDisplay = course.tags
    ? (typeof course.tags === "string" ? JSON.parse(course.tags) : course.tags)
    : [];

  return (
    <div className="w-80 bg-white border-r flex flex-col">
      {/* Header */}
      <div className="p-4 border-b space-y-2">
        <button onClick={onBack} className="flex items-center gap-1 text-sm text-gray-600 hover:text-gray-900">
          <ArrowLeft className="w-4 h-4" /> Retour
        </button>
        <h2 className="font-semibold text-lg line-clamp-1">{course.title}</h2>
        <div className="flex gap-2 flex-wrap">
          <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${
            course.status === "published" ? "bg-green-100 text-green-800" :
            course.status === "archived" ? "bg-orange-100 text-orange-700" : "bg-yellow-100 text-yellow-800"
          }`}>
            {course.status === "published" ? "Publié" : course.status === "archived" ? "Archivé" : "Brouillon"}
          </span>
          <span className="text-xs text-gray-500">{chapters.length} chapitres</span>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" size="sm" className="flex-1" onClick={onPreview} loading={previewLoading}>
            <Eye className="w-3 h-3" /> Aperçu
          </Button>
          <Button variant="ghost" size="sm" className="flex-1" onClick={onDuplicate} loading={saving}>
            <Copy className="w-3 h-3" /> Dupliquer
          </Button>
        </div>
        {onOpenBuilder && (
          <Button variant="primary" size="sm" className="w-full" onClick={onOpenBuilder}>
            <LayoutGrid className="w-3 h-3" /> Builder Drag & Drop
          </Button>
        )}
        <div className="flex gap-2">
          {course.status === "published" ? (
            <Button variant="secondary" size="sm" className="flex-1" onClick={onUnpublish} loading={saving}>
              <EyeOff className="w-3 h-3" /> Dépublier
            </Button>
          ) : (
            <Button variant="success" size="sm" className="flex-1" onClick={onPublish} loading={saving}>
              <Eye className="w-3 h-3" /> Publier
            </Button>
          )}
          {course.status !== "archived" && (
            <Button variant="ghost" size="sm" className="flex-1" onClick={onArchive} loading={saving}>
              <Archive className="w-3 h-3" /> Archiver
            </Button>
          )}
        </div>
        {publishErrors.length > 0 && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-2 space-y-1">
            {publishErrors.map((e, i) => (
              <div key={i} className="flex items-start gap-1 text-xs text-red-600">
                <AlertCircle className="w-3 h-3 mt-0.5 shrink-0" /> {e}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Course Settings */}
      <div className="p-3 border-b bg-gray-50 space-y-3 max-h-[50vh] overflow-y-auto">
        <h4 className="text-xs font-medium text-gray-500 uppercase">Paramètres du cours</h4>
        <Input label="Titre *" value={course.title || ""} onChange={e => onCourseFieldChange("title", e.target.value)} />
        <div>
          <label className="block text-xs font-medium mb-1">Description courte</label>
          <textarea value={course.short_description || ""} onChange={e => onCourseFieldChange("short_description", e.target.value)}
            className="w-full px-2 py-1 text-sm border rounded" rows={2} />
        </div>
        <div>
          <label className="block text-xs font-medium mb-1">Description</label>
          <textarea value={course.description || ""} onChange={e => onCourseFieldChange("description", e.target.value)}
            className="w-full px-2 py-1 text-sm border rounded" rows={3} />
        </div>
        <div className="grid grid-cols-2 gap-2">
          <Input label="Catégorie" value={course.category || ""} onChange={e => onCourseFieldChange("category", e.target.value)} />
          <div>
            <label className="block text-xs font-medium mb-1">Niveau</label>
            <select value={course.level || "beginner"} onChange={e => onCourseFieldChange("level", e.target.value)}
              className="w-full px-2 py-1 text-sm border rounded">
              <option value="beginner">Débutant</option>
              <option value="intermediate">Intermédiaire</option>
              <option value="advanced">Avancé</option>
            </select>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="block text-xs font-medium mb-1">Type de formation *</label>
            <select
              value={categoryCible}
              onChange={e => onCourseFieldChange("category_cible", e.target.value)}
              disabled={isTeacher}
              className="w-full px-2 py-1 text-sm border rounded disabled:opacity-50 disabled:bg-gray-100">
              <option value="Scolaire">Scolaire</option>
              <option value="Soft_Skill">Soft Skill</option>
              <option value="Teacher_Training">Teacher Training</option>
            </select>
          </div>
          {isScolaire && (
            <div>
              <label className="block text-xs font-medium mb-1">Niveau scolaire *</label>
              <input value={course.niveau_scolaire || ""} onChange={e => onCourseFieldChange("niveau_scolaire", e.target.value)}
                className="w-full px-2 py-1 text-sm border rounded" placeholder="Ex: 3ème année secondaire" />
            </div>
          )}
        </div>
        {isScolaire && (
          <div>
            <label className="block text-xs font-medium mb-1">Matière (catégorie) *</label>
            {matieres.length > 0 ? (
              <select value={course.category || ""} onChange={e => onCourseFieldChange("category", e.target.value)}
                className="w-full px-2 py-1 text-sm border rounded">
                <option value="">-- Choisir --</option>
                {matieres.map(m => <option key={m.id} value={m.nom}>{m.nom}</option>)}
              </select>
            ) : (
              <input value={course.category || ""} onChange={e => onCourseFieldChange("category", e.target.value)}
                className="w-full px-2 py-1 text-sm border rounded" placeholder="Ex: Mathématiques" />
            )}
          </div>
        )}
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="block text-xs font-medium mb-1">Visibilité</label>
            <select value={course.visibility || "public"} onChange={e => onCourseFieldChange("visibility", e.target.value)}
              className="w-full px-2 py-1 text-sm border rounded">
              <option value="public">Public</option>
              <option value="private">Privé</option>
              <option value="school">Par école</option>
              <option value="role">Par rôle</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium mb-1">Inscription</label>
            <select value={course.enrollment_type || "open"} onChange={e => onCourseFieldChange("enrollment_type", e.target.value)}
              className="w-full px-2 py-1 text-sm border rounded">
              <option value="open">Libre</option>
              <option value="manual">Manuelle</option>
            </select>
          </div>
        </div>
        <div>
          <label className="block text-xs font-medium mb-1">Prérequis</label>
          <textarea value={course.prerequisites || ""} onChange={e => onCourseFieldChange("prerequisites", e.target.value)}
            className="w-full px-2 py-1 text-sm border rounded" rows={2} placeholder="Prérequis pour suivre ce cours" />
        </div>
        <div>
          <label className="block text-xs font-medium mb-1">Objectifs pédagogiques</label>
          <textarea value={course.learning_objectives || ""} onChange={e => onCourseFieldChange("learning_objectives", e.target.value)}
            className="w-full px-2 py-1 text-sm border rounded" rows={2} placeholder="Ce que les apprenants sauront faire" />
        </div>
        <Input label="Tags (virgules)" value={tagsDisplay.join(", ")} onChange={e => onCourseFieldChange("tags", e.target.value.split(",").map((t: string) => t.trim()).filter(Boolean))} placeholder="python, débutant" />
        <div>
          <label className="block text-xs font-medium mb-1">Langue</label>
          <select value={course.language || "fr"} onChange={e => onCourseFieldChange("language", e.target.value)}
            className="w-full px-2 py-1 text-sm border rounded">
            <option value="fr">Français</option>
            <option value="en">English</option>
            <option value="ar">العربية</option>
          </select>
        </div>
        <div className="grid grid-cols-2 gap-2">
          <Input label="Prix (Tokens)" type="number" value={course.price_tokens || 0} onChange={e => onCourseFieldChange("price_tokens", Number(e.target.value))} />
          <Input label="Prix (DT)" type="number" step="0.01" value={course.price_dt || 0} onChange={e => onCourseFieldChange("price_dt", Number(e.target.value))} />
        </div>
        <div className="grid grid-cols-2 gap-2">
          <Input label="Max étudiants" type="number" value={course.max_students || ""} onChange={e => onCourseFieldChange("max_students", e.target.value ? Number(e.target.value) : null)} placeholder="Illimité" />
          <Input label="Durée estimée (min)" type="number" value={course.total_duration_minutes || 0} readOnly className="bg-gray-100" />
        </div>
        <Input label="URL Couverture" value={course.cover_url || course.thumbnail_url || ""} onChange={e => onCourseFieldChange("cover_url", e.target.value) || onCourseFieldChange("thumbnail_url", e.target.value)} placeholder="https://..." />
        {(course.cover_url || course.thumbnail_url) && (
          <img src={course.cover_url || course.thumbnail_url} alt="Couverture" className="w-full h-24 object-cover rounded border" />
        )}
        <div className="text-xs text-gray-400 space-y-0.5">
          <div>Créé: {course.created_at ? new Date(course.created_at).toLocaleDateString() : "—"}</div>
          <div>Modifié: {course.updated_at ? new Date(course.updated_at).toLocaleDateString() : "—"}</div>
          {course.published_at && <div>Publié: {new Date(course.published_at).toLocaleDateString()}</div>}
          {course.modifier_name && <div>Modifié par: {course.modifier_name}</div>}
        </div>
        <Button className="w-full" onClick={onSave} loading={saving}>
          <Save className="w-4 h-4" /> Enregistrer
        </Button>
      </div>

      {/* Chapters */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {chapters.map(ch => (
          <div key={ch.id}
            className={`rounded cursor-pointer ${activeChapter === ch.id ? "bg-navy-50" : "hover:bg-gray-50"}`}>
            <div onClick={() => onSetActiveChapter(ch.id)} className="flex items-center gap-2 p-2">
              <GripVertical className="w-4 h-4 text-gray-400" />
              <div className="flex-1">
                <input type="text" value={ch.title} onChange={e => onUpdateChapterTitle(ch.id, e.target.value)}
                  onClick={e => e.stopPropagation()}
                  className="w-full text-sm font-medium bg-transparent border-none focus:outline-none" />
                <span className="text-xs text-gray-400">{ch.lessons?.length || 0} leçons</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="p-3 border-t">
        <Button variant="ghost" className="w-full" onClick={onAddChapter}>
          <Plus className="w-4 h-4" /> Nouveau chapitre
        </Button>
      </div>
    </div>
  );
}
