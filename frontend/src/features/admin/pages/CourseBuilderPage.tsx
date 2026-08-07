import { useState, useEffect, useCallback, useMemo } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { DragDropContext, Droppable, Draggable, type DropResult } from "@hello-pangea/dnd";
import {
  ArrowLeft, Plus, Trash2, GripVertical, Search, Save,
  FileText, Video, HelpCircle, File, Image, Link, CheckCircle, AlertCircle,
} from "lucide-react";
import { courseAdmin, chapterAdmin, lessonAdmin } from "../../../api";
import { PageSpinner } from "../../../components/ui";

/* ─── Types ─────────────────────────────────────────────────────────── */

interface Lesson {
  id: number;
  chapter_id: number;
  title: string;
  description?: string;
  lesson_type: string;
  order: number;
  duration_minutes: number;
  is_free?: boolean;
}

interface Module {
  id: number;
  title: string;
  order: number;
  lessons: Lesson[];
}

/* ─── Helpers ───────────────────────────────────────────────────────── */

const LESSON_TYPES = [
  { value: "text", label: "Texte", icon: FileText, bg: "bg-gray-100 text-gray-600" },
  { value: "video", label: "Vidéo", icon: Video, bg: "bg-blue-100 text-blue-600" },
  { value: "pdf", label: "PDF", icon: File, bg: "bg-red-100 text-red-600" },
  { value: "image", label: "Image", icon: Image, bg: "bg-green-100 text-green-600" },
  { value: "link", label: "Lien", icon: Link, bg: "bg-purple-100 text-purple-600" },
  { value: "quiz", label: "Quiz", icon: HelpCircle, bg: "bg-orange-100 text-orange-600" },
];

function lessonMeta(type: string) {
  return LESSON_TYPES.find(t => t.value === type) || LESSON_TYPES[0];
}

/* ─── Component ─────────────────────────────────────────────────────── */

export default function CourseBuilderPage() {
  const { courseId } = useParams<{ courseId: string }>();
  const navigate = useNavigate();

  const [course, setCourse] = useState<any>(null);
  const [modules, setModules] = useState<Module[]>([]);
  const [allLessons, setAllLessons] = useState<Lesson[]>([]);
  const [librarySearch, setLibrarySearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: "success" | "error" } | null>(null);

  const showToast = useCallback((message: string, type: "success" | "error" = "success") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3500);
  }, []);

  /* ── Data loading ────────────────────────────────────────────────── */

  const fetchModuleLessons = useCallback(async (moduleId: number): Promise<Lesson[]> => {
    try {
      const lessons = await lessonAdmin.list(moduleId) as unknown as Lesson[];
      return Array.isArray(lessons) ? lessons : [];
    } catch { return []; }
  }, []);

  useEffect(() => {
    if (!courseId) return;
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const c = await courseAdmin.get(Number(courseId));
        if (cancelled) return;
        setCourse(c);

        const rawChapters = (c as any).chapters || [];
        const loaded: Module[] = [];
        for (const ch of rawChapters) {
          const lessons = await fetchModuleLessons(ch.id);
          if (cancelled) return;
          loaded.push({ id: ch.id, title: ch.title, order: ch.order ?? ch.order_index ?? 0, lessons });
        }
        if (cancelled) return;
        setModules(loaded);

        try {
          const raw = await lessonAdmin.listAll({ limit: 200 }) as unknown as Lesson[] | { items?: Lesson[] };
          if (cancelled) return;
          const all = Array.isArray(raw) ? raw : ((raw as any).items || []);
          setAllLessons(all);
        } catch { if (!cancelled) setAllLessons([]); }
      } catch { if (!cancelled) showToast("Erreur chargement cours", "error"); }
      finally { if (!cancelled) setLoading(false); }
    })();
    return () => { cancelled = true; };
  }, [courseId, fetchModuleLessons, showToast]);

  /* ── Library (unassigned lessons) ────────────────────────────────── */

  const assignedIds = useMemo(() => {
    const s = new Set<number>();
    modules.forEach(m => m.lessons.forEach(l => s.add(l.id)));
    return s;
  }, [modules]);

  const libraryLessons = useMemo(() => {
    const q = librarySearch.toLowerCase();
    return allLessons.filter(l => !assignedIds.has(l.id) && (
      !q || l.title.toLowerCase().includes(q) || (l.description || "").toLowerCase().includes(q)
    ));
  }, [allLessons, assignedIds, librarySearch]);

  /* ── Drop handler ────────────────────────────────────────────────── */

  const onDragEnd = useCallback(async (result: DropResult) => {
    const { source, destination, draggableId } = result;
    if (!destination) return;
    const lessonId = Number(draggableId.replace("les-", ""));
    const srcModuleId = source.droppableId.startsWith("mod-")
      ? Number(source.droppableId.replace("mod-", "")) : null;
    const dstModuleId = destination.droppableId.startsWith("mod-")
      ? Number(destination.droppableId.replace("mod-", "")) : null;

    if (!dstModuleId) return;

    /* ── Module reorder ──────────────────────────────────────────── */
    if (draggableId.startsWith("mod-") && source.droppableId === "modules") {
      const order = modules.map(m => m.id);
      const [moved] = order.splice(source.index, 1);
      order.splice(destination.index, 0, moved);
      setModules(prev => {
        const map = new Map(prev.map(m => [m.id, m]));
        return order.map(id => map.get(id)!).filter(Boolean);
      });
      try { await chapterAdmin.reorder(Number(courseId), order); }
      catch { showToast("Erreur réordonnancement modules", "error"); }
      return;
    }

    /* ── Same module reorder ─────────────────────────────────────── */
    if (srcModuleId && dstModuleId === srcModuleId) {
      setModules(prev => prev.map(m => {
        if (m.id !== srcModuleId) return m;
        const lessons = [...m.lessons];
        const [moved] = lessons.splice(source.index, 1);
        lessons.splice(destination.index, 0, moved);
        return { ...m, lessons };
      }));
      const mod = modules.find(m => m.id === srcModuleId);
      if (mod) {
        const order = [...mod.lessons.map(l => l.id)];
        const [moved] = order.splice(source.index, 1);
        order.splice(destination.index, 0, moved);
        try { await lessonAdmin.reorder(order); }
        catch { showToast("Erreur réordonnancement", "error"); }
      }
      return;
    }

    /* ── Cross-module move / library → module ────────────────────── */
    const isFromLibrary = !srcModuleId;

    setModules(prev => {
      const next = prev.map(m => {
        if (isFromLibrary) {
          if (m.id !== dstModuleId) return m;
          const lessons = [...m.lessons];
          const moved = allLessons.find(l => l.id === lessonId);
          if (moved && !lessons.some(l => l.id === lessonId)) {
            lessons.splice(destination.index, 0, moved);
          }
          return { ...m, lessons };
        }
        if (m.id === srcModuleId) {
          const lessons = m.lessons.filter(l => l.id !== lessonId);
          return { ...m, lessons };
        }
        if (m.id === dstModuleId) {
          const lessons = [...m.lessons];
          const srcMod = prev.find(mm => mm.id === srcModuleId);
          const moved = srcMod?.lessons.find(l => l.id === lessonId);
          if (moved && !lessons.some(l => l.id === lessonId)) {
            lessons.splice(destination.index, 0, moved);
          }
          return { ...m, lessons };
        }
        return m;
      });
      return next;
    });

    if (isFromLibrary) {
      setAllLessons(prev => prev.filter(l => l.id !== lessonId));
    }

    try {
      await lessonAdmin.update(lessonId, { chapter_id: dstModuleId } as any);
      const dstMod = modules.find(m => m.id === dstModuleId);
      if (dstMod) {
        const order = [...dstMod.lessons.filter(l => l.id !== lessonId).map(l => l.id)];
        order.splice(destination.index, 0, lessonId);
        await lessonAdmin.reorder(order);
      }
      if (srcModuleId && srcModuleId !== dstModuleId) {
        const srcMod = modules.find(m => m.id === srcModuleId);
        if (srcMod) {
          const order = srcMod.lessons.filter(l => l.id !== lessonId).map(l => l.id);
          await lessonAdmin.reorder(order);
        }
      }
      const refetchIds = isFromLibrary ? [dstModuleId] : [srcModuleId!, dstModuleId];
      const updates = await Promise.all(refetchIds.map(async id => {
        const lessons = await fetchModuleLessons(id);
        return { id, lessons };
      }));
      setModules(prev => {
        const map = new Map(prev.map(m => [m.id, m]));
        updates.forEach(u => { const m = map.get(u.id); if (m) m.lessons = u.lessons; });
        return [...map.values()];
      });
    } catch { showToast("Erreur déplacement leçon", "error"); }
  }, [modules, courseId, allLessons, fetchModuleLessons, showToast]);

  /* ── Module CRUD ─────────────────────────────────────────────────── */

  const handleAddModule = useCallback(async () => {
    try {
      const created = await chapterAdmin.create(Number(courseId), {
        title: `Module ${modules.length + 1}`,
      });
      setModules(prev => [...prev, { ...created, lessons: [] }]);
      showToast("Module ajouté");
    } catch { showToast("Erreur ajout module", "error"); }
  }, [courseId, modules.length, showToast]);

  const handleUpdateModuleTitle = useCallback(async (id: number, title: string) => {
    setModules(prev => prev.map(m => m.id === id ? { ...m, title } : m));
    try { await chapterAdmin.update(Number(courseId), id, { title }); }
    catch { showToast("Erreur mise à jour", "error"); }
  }, [courseId, showToast]);

  const handleDeleteModule = useCallback(async (id: number) => {
    if (!confirm("Supprimer ce module et toutes ses leçons ?")) return;
    try {
      await chapterAdmin.delete(Number(courseId), id);
      setModules(prev => prev.filter(m => m.id !== id));
      showToast("Module supprimé");
    } catch { showToast("Erreur suppression", "error"); }
  }, [courseId, showToast]);

  const handleRemoveLesson = useCallback(async (moduleId: number, lessonId: number) => {
    setModules(prev => prev.map(m => {
      if (m.id !== moduleId) return m;
      return { ...m, lessons: m.lessons.filter(l => l.id !== lessonId) };
    }));
    const mod = modules.find(m => m.id === moduleId);
    if (mod) {
      const order = mod.lessons.filter(l => l.id !== lessonId).map(l => l.id);
      try { await lessonAdmin.reorder(order); }
      catch { showToast("Erreur retrait leçon", "error"); }
    }
  }, [modules, showToast]);

  /* ── Loading state ───────────────────────────────────────────────── */

  if (loading) return <PageSpinner message="Chargement du builder..." />;
  if (!course) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-50">
        <div className="text-center">
          <p className="text-gray-600 mb-4">Cours introuvable</p>
          <button onClick={() => navigate("/dashboard/admin/courses")}
            className="px-4 py-2 bg-[#0a2647] text-white rounded-lg hover:bg-[#144272]">
            Retour aux cours
          </button>
        </div>
      </div>
    );
  }

  /* ── Render ───────────────────────────────────────────────────────── */

  return (
    <DragDropContext onDragEnd={onDragEnd}>
      <div className="flex flex-col h-screen bg-gray-100">

        {/* ── Header ─────────────────────────────────────────────── */}
        <header className="bg-white border-b px-4 py-3 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <button onClick={() => navigate("/dashboard/admin/courses")}
              className="p-2 hover:bg-gray-100 rounded-lg" title="Retour">
              <ArrowLeft className="w-5 h-5 text-gray-600" />
            </button>
            <div>
              <h1 className="font-bold text-lg text-gray-900 line-clamp-1">{course.title}</h1>
              <p className="text-xs text-gray-500">
                {modules.length} module{modules !== null && modules.length !== 1 ? "s" : ""}
                {" · "}
                {modules.reduce((s, m) => s + m.lessons.length, 0)} leçon
                {modules.reduce((s, m) => s + m.lessons.length, 0) !== 1 ? "s" : ""}
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <button onClick={() => navigate(`/dashboard/admin/courses/${courseId}`)}
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 text-sm font-medium">
              Éditeur classique
            </button>
            <button onClick={() => navigate("/dashboard/admin/courses")}
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 text-sm font-medium">
              Retour à la liste
            </button>
            <button disabled className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium flex items-center gap-2">
              <Save className="w-4 h-4" /> Sauvegardé automatiquement
            </button>
          </div>
        </header>

        {/* ── Body ──────────────────────────────────────────────── */}
        <div className="flex flex-1 overflow-hidden">

          {/* ── Library (Left) ────────────────────────────────────── */}
          <aside className="w-80 bg-white border-r flex flex-col shrink-0">
            <div className="p-3 border-b">
              <h2 className="font-semibold text-sm text-gray-900 mb-2">📚 Bibliothèque de leçons</h2>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input type="text" placeholder="Rechercher une leçon..." value={librarySearch}
                  onChange={e => setLibrarySearch(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#2c74b3] focus:border-transparent" />
              </div>
              <p className="text-xs text-gray-400 mt-2">
                {libraryLessons.length} leçon{libraryLessons.length !== 1 ? "s" : ""} disponible{libraryLessons.length !== 1 ? "s" : ""}
              </p>
            </div>
            <Droppable droppableId="library" isDropDisabled={true}>
              {(provided) => (
                <div ref={provided.innerRef} {...provided.droppableProps}
                  className="flex-1 overflow-y-auto p-2 space-y-1">
                  {libraryLessons.length === 0 ? (
                    <div className="text-center py-8 text-gray-400">
                      <FileText className="w-10 h-10 mx-auto mb-2 opacity-50" />
                      <p className="text-sm">
                        {allLessons.length === 0 ? "Aucune leçon dans la bibliothèque" : "Toutes les leçons sont assignées"}
                      </p>
                    </div>
                  ) : (
                    libraryLessons.map((lesson, index) => {
                      const meta = lessonMeta(lesson.lesson_type);
                      const Icon = meta.icon;
                      return (
                        <Draggable key={`les-${lesson.id}`} draggableId={`les-${lesson.id}`} index={index}>
                          {(dragProvided, dragSnapshot) => (
                            <div ref={dragProvided.innerRef} {...dragProvided.draggableProps} {...dragProvided.dragHandleProps}
                              className={`flex items-center gap-2 p-2 rounded-lg border cursor-grab transition-shadow ${meta.bg} ${dragSnapshot.isDragging ? "shadow-lg ring-2 ring-[#2c74b3]" : "hover:shadow-sm"}`}>
                              <GripVertical className="w-4 h-4 opacity-40 shrink-0" />
                              <Icon className="w-4 h-4 shrink-0" />
                              <div className="flex-1 min-w-0">
                                <p className="text-sm font-medium truncate">{lesson.title}</p>
                                <p className="text-xs opacity-60">{lesson.duration_minutes || 0} min</p>
                              </div>
                            </div>
                          )}
                        </Draggable>
                      );
                    })
                  )}
                  {provided.placeholder}
                </div>
              )}
            </Droppable>
          </aside>

          {/* ── Builder (Right) ───────────────────────────────────── */}
          <main className="flex-1 flex flex-col overflow-hidden">
            <Droppable droppableId="modules" direction="horizontal">
              {(provided) => (
                <div ref={provided.innerRef} {...provided.droppableProps}
                  className="flex-1 flex gap-4 p-4 overflow-x-auto items-start">
                  {modules.map((mod, modIndex) => (
                    <Draggable key={`mod-${mod.id}`} draggableId={`mod-${mod.id}`} index={modIndex}>
                      {(modDragProvided, modDragSnapshot) => (
                        <div ref={modDragProvided.innerRef} {...modDragProvided.draggableProps}
                          className={`w-80 shrink-0 bg-white rounded-xl shadow-sm border flex flex-col max-h-[calc(100vh-8rem)] ${modDragSnapshot.isDragging ? "shadow-xl ring-2 ring-[#2c74b3]" : ""}`}>

                          {/* Module header */}
                          <div {...modDragProvided.dragHandleProps}
                            className="p-3 border-b bg-gradient-to-r from-[#0a2647] to-[#144272] rounded-t-xl flex items-center gap-2">
                            <GripVertical className="w-4 h-4 text-white/50 shrink-0" />
                            <input type="text" value={mod.title}
                              onChange={e => handleUpdateModuleTitle(mod.id, e.target.value)}
                              className="flex-1 bg-transparent text-white font-semibold text-sm border-none focus:outline-none placeholder-white/50" />
                            <span className="text-xs text-white/60 bg-white/10 px-2 py-0.5 rounded-full shrink-0">
                              {mod.lessons.length}
                            </span>
                            <button onClick={() => handleDeleteModule(mod.id)}
                              className="p-1 hover:bg-white/20 rounded shrink-0" title="Supprimer le module">
                              <Trash2 className="w-4 h-4 text-white/70" />
                            </button>
                          </div>

                          {/* Lessons droppable */}
                          <Droppable droppableId={`mod-${mod.id}`}>
                            {(dropProvided, dropSnapshot) => (
                              <div ref={dropProvided.innerRef} {...dropProvided.droppableProps}
                                className={`flex-1 overflow-y-auto p-2 space-y-1 min-h-[120px] transition-colors ${dropSnapshot.isDraggingOver ? "bg-[#eef4fb]" : ""}`}>
                                {mod.lessons.length === 0 && (
                                  <div className={`h-full min-h-[100px] flex flex-col items-center justify-center rounded-lg border-2 border-dashed transition-colors ${dropSnapshot.isDraggingOver ? "border-[#2c74b3] bg-[#eef4fb]" : "border-gray-200"}`}>
                                    <FileText className="w-8 h-8 text-gray-300 mb-1" />
                                    <p className="text-xs text-gray-400">
                                      {dropSnapshot.isDraggingOver ? "Déposez ici" : "Glissez une leçon ici"}
                                    </p>
                                  </div>
                                )}
                                {mod.lessons.map((lesson, lesIndex) => {
                                  const meta = lessonMeta(lesson.lesson_type);
                                  const Icon = meta.icon;
                                  return (
                                    <Draggable key={`les-${lesson.id}`} draggableId={`les-${lesson.id}`} index={lesIndex}>
                                      {(lesProvided, lesSnapshot) => (
                                        <div ref={lesProvided.innerRef} {...lesProvided.draggableProps} {...lesProvided.dragHandleProps}
                                          className={`flex items-center gap-2 p-2 rounded-lg border transition-shadow cursor-grab group ${meta.bg} ${lesSnapshot.isDragging ? "shadow-lg ring-2 ring-[#2c74b3]" : "hover:shadow-sm"}`}>
                                          <GripVertical className="w-4 h-4 opacity-40 shrink-0" />
                                          <Icon className="w-4 h-4 shrink-0" />
                                          <div className="flex-1 min-w-0">
                                            <p className="text-sm font-medium truncate">{lesson.title}</p>
                                            <p className="text-xs opacity-60">{lesson.duration_minutes || 0} min</p>
                                          </div>
                                          <button onClick={e => { e.stopPropagation(); handleRemoveLesson(mod.id, lesson.id); }}
                                            className="p-1 rounded hover:bg-white/60 opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
                                            title="Retirer du module">
                                            <Trash2 className="w-3.5 h-3.5 text-red-500" />
                                          </button>
                                        </div>
                                      )}
                                    </Draggable>
                                  );
                                })}
                                {dropProvided.placeholder}
                              </div>
                            )}
                          </Droppable>
                        </div>
                      )}
                    </Draggable>
                  ))}

                  {/* Add module button */}
                  <Draggable draggableId="add-module-placeholder" index={modules.length} isDragDisabled={true}>
                    {(provided) => (
                      <div ref={provided.innerRef} {...provided.draggableProps} {...provided.dragHandleProps}
                        className="w-80 shrink-0">
                        <button onClick={handleAddModule}
                          className="w-full h-32 flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-gray-300 text-gray-400 hover:border-[#2c74b3] hover:text-[#2c74b3] hover:bg-[#eef4fb] transition-colors">
                          <Plus className="w-8 h-8 mb-1" />
                          <span className="text-sm font-medium">Ajouter un module</span>
                        </button>
                      </div>
                    )}
                  </Draggable>
                  {provided.placeholder}
                </div>
              )}
            </Droppable>
          </main>
        </div>

        {/* ── Toast ──────────────────────────────────────────────── */}
        {toast && (
          <div className={`fixed top-6 right-6 z-50 px-5 py-3 rounded-xl shadow-lg text-white flex items-center gap-2 text-sm font-medium ${toast.type === "success" ? "bg-green-500" : "bg-red-500"}`}>
            {toast.type === "success" ? <CheckCircle className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
            {toast.message}
          </div>
        )}
      </div>
    </DragDropContext>
  );
}
