import { useState } from "react";
import { useAuthStore } from "../../../store/authStore";
import { Plus, Trash2, GripVertical, Image, Video, FileText, Save, X, DollarSign, AlertCircle } from "lucide-react";

const API_URL = "";

interface Chapter {
  id: number;
  title: string;
  subchapters: Subchapter[];
}

interface Subchapter {
  id: number;
  title: string;
  content: string;
  video_url?: string;
  image_url?: string;
  quiz?: Quiz;
}

interface Quiz {
  id: number;
  questions: Question[];
}

interface Question {
  id: number;
  text: string;
  options: string[];
  correct: number;
}

export default function CourseBuilder() {
  const { token, user } = useAuthStore();
  const [courseTitle, setCourseTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priceTokens, setPriceTokens] = useState(10);
  const [priceDT, setPriceDT] = useState(0);
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [activeChapter, setActiveChapter] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  
  // Champs pour enseignant indépendant
  const isIndependentTeacher = user?.role === "teacher" && !user?.school_id;
  const [coursePrice, setCoursePrice] = useState(0);
  const [courseVisibility, setCourseVisibility] = useState<"private" | "school_only" | "public_catalog">("private");

  const addChapter = () => {
    const newChapter: Chapter = {
      id: Date.now(),
      title: `Chapitre ${chapters.length + 1}`,
      subchapters: [],
    };
    setChapters([...chapters, newChapter]);
    setActiveChapter(newChapter.id);
  };

  const addSubchapter = (chapterId: number) => {
    setChapters(chapters.map((ch) =>
      ch.id === chapterId
        ? {
            ...ch,
            subchapters: [
              ...ch.subchapters,
              {
                id: Date.now(),
                title: `Leçon ${ch.subchapters.length + 1}`,
                content: "",
              },
            ],
          }
        : ch
    ));
  };

  const updateSubchapter = (chapterId: number, subId: number, data: Partial<Subchapter>) => {
    setChapters(chapters.map((ch) =>
      ch.id === chapterId
        ? {
            ...ch,
            subchapters: ch.subchapters.map((sub) =>
              sub.id === subId ? { ...sub, ...data } : sub
            ),
          }
        : ch
    ));
  };

  const addQuestion = (chapterId: number, subId: number) => {
    setChapters(chapters.map((ch) =>
      ch.id === chapterId
        ? {
            ...ch,
            subchapters: ch.subchapters.map((sub) => {
              if (sub.id !== subId) return sub;
              const quiz = sub.quiz || { id: Date.now(), questions: [] };
              return {
                ...sub,
                quiz: {
                  ...quiz,
                  questions: [
                    ...quiz.questions,
                    {
                      id: Date.now(),
                      text: "",
                      options: ["", "", "", ""],
                      correct: 0,
                    },
                  ],
                },
              };
            }),
          }
        : ch
    ));
  };

  const saveCourse = async () => {
    if (!token || !courseTitle) return;
    setSaving(true);
    try {
      const res = await fetch(`${API_URL}/api/admin/courses`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          title: courseTitle,
          description,
          price_tokens: priceTokens,
          price_dt: priceDT,
          // Champs enseignant indépendant
          ...(isIndependentTeacher && {
            price: coursePrice,
            currency: "TND",
            visibility: courseVisibility,
            owner_type: "independent_teacher",
          }),
          chapters: chapters.map((ch) => ({
            title: ch.title,
            subchapters: ch.subchapters.map((sub) => ({
              title: sub.title,
              content: sub.content,
              video_url: sub.video_url,
              image_url: sub.image_url,
              quiz: sub.quiz,
            })),
          })),
        }),
      });
      if (res.ok) {
        alert("Cours enregistré avec succès!");
        setCourseTitle("");
        setDescription("");
        setChapters([]);
        setCoursePrice(0);
      }
    } catch (err) {
      console.error(err);
    }
    setSaving(false);
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-3xl p-8 shadow-sm border border-black/5">
        <h1 className="text-3xl font-[300] text-navy mb-2">
          Course <span className="italic text-orange">Builder</span>
        </h1>
        <p className="text-gray">Créez du contenu de formation structuré</p>
      </div>

      {/* Course Info */}
      <div className="bg-white rounded-3xl p-8 shadow-sm border border-black/5">
        <h2 className="text-xl font-semibold text-navy mb-6">Informations du cours</h2>
        <div className="grid gap-6">
          <div>
            <label className="block text-sm font-medium text-gray mb-2">Titre</label>
            <input
              type="text"
              value={courseTitle}
              onChange={(e) => setCourseTitle(e.target.value)}
              className="w-full px-5 py-3 bg-cream-m rounded-xl border border-black/5 focus:border-orange focus:outline-none"
              placeholder="Introduction à l'IA pédagogique"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray mb-2">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-5 py-3 bg-cream-m rounded-xl border border-black/5 focus:border-orange focus:outline-none min-h-[100px]"
              placeholder="Description du cours..."
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray mb-2">Prix (Tokens)</label>
              <input
                type="number"
                value={priceTokens}
                onChange={(e) => setPriceTokens(Number(e.target.value))}
                className="w-full px-5 py-3 bg-cream-m rounded-xl border border-black/5 focus:border-orange focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray mb-2">Prix (DT)</label>
              <input
                type="number"
                value={priceDT}
                onChange={(e) => setPriceDT(Number(e.target.value))}
                className="w-full px-5 py-3 bg-cream-m rounded-xl border border-black/5 focus:border-orange focus:outline-none"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Section Enseignant Indépendant */}
      {isIndependentTeacher && (
        <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-3xl p-8 border border-purple-200">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-purple-100 rounded-xl">
              <DollarSign className="w-6 h-6 text-purple-600" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-navy">Tarification Enseignant Indépendant</h2>
              <p className="text-sm text-gray">Configurez le prix de votre cours en TND</p>
            </div>
          </div>
          
          <div className="grid gap-6">
            <div className="bg-white rounded-2xl p-6 border border-purple-100">
              <label className="block text-sm font-medium text-gray mb-2">Prix du cours (TND) *</label>
              <div className="relative">
                <input
                  type="number"
                  value={coursePrice}
                  onChange={(e) => setCoursePrice(Number(e.target.value))}
                  min={0}
                  max={500}
                  step={0.5}
                  className="w-full px-5 py-3 bg-cream-m rounded-xl border border-black/5 focus:border-purple focus:outline-none"
                  placeholder="0 = Gratuit"
                />
                <span className="absolute right-4 top-1/2 -translate-y-1/2 text-gray text-sm">TND</span>
              </div>
              <div className="mt-2 flex items-center gap-2 text-sm text-gray">
                <AlertCircle className="w-4 h-4" />
                <span>Prix maximum: 500 TND</span>
              </div>
            </div>

            <div className="bg-white rounded-2xl p-6 border border-purple-100">
              <label className="block text-sm font-medium text-gray mb-2">Visibilité du cours *</label>
              <select
                value={courseVisibility}
                onChange={(e) => setCourseVisibility(e.target.value as any)}
                className="w-full px-5 py-3 bg-cream-m rounded-xl border border-black/5 focus:border-purple focus:outline-none"
              >
                <option value="private">Privé (moi seulement)</option>
                <option value="school_only">Mon école uniquement</option>
                <option value="public_catalog">Catalogue public (B2B)</option>
              </select>
              <p className="mt-2 text-sm text-gray">
                {courseVisibility === "public_catalog" 
                  ? "⚠️ Votre cours sera visible par toutes les écoles. Il devra être approuvé par un pédagogue avant distribution."
                  : "Visibilité limitée à votre école ou vous-même."}
              </p>
            </div>

            {coursePrice > 0 && (
              <div className="bg-green-50 rounded-2xl p-6 border border-green-200">
                <h4 className="font-medium text-green-800 mb-2">Répartition des revenus</h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray">Prix du cours:</span>
                    <span className="ml-2 font-semibold text-navy">{coursePrice} TND</span>
                  </div>
                  <div>
                    <span className="text-gray">Commission EDUAI (30%):</span>
                    <span className="ml-2 font-semibold text-orange">{(coursePrice * 0.3).toFixed(2)} TND</span>
                  </div>
                  <div className="col-span-2 pt-2 border-t border-green-200">
                    <span className="text-gray">Votre revenu:</span>
                    <span className="ml-2 font-semibold text-green-600 text-lg">{(coursePrice * 0.7).toFixed(2)} TND</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Chapters */}
      <div className="bg-white rounded-3xl p-8 shadow-sm border border-black/5">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold text-navy">Chapitres</h2>
          <button
            onClick={addChapter}
            className="flex items-center gap-2 px-4 py-2 bg-orange text-white rounded-xl text-sm font-medium"
          >
            <Plus className="w-4 h-4" />
            Ajouter Chapitre
          </button>
        </div>

        {chapters.length === 0 ? (
          <div className="text-center py-12 text-gray">
            <FileText className="w-12 h-12 mx-auto mb-4 opacity-30" />
            <p>Aucun chapitre. Ajoutez votre premier chapitre.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {chapters.map((chapter, idx) => (
              <div key={chapter.id} className="border border-black/5 rounded-2xl overflow-hidden">
                {/* Chapter Header */}
                <div
                  className={`p-5 flex items-center gap-4 cursor-pointer ${
                    activeChapter === chapter.id ? "bg-orange/5" : "bg-cream-m"
                  }`}
                  onClick={() => setActiveChapter(activeChapter === chapter.id ? null : chapter.id)}
                >
                  <GripVertical className="w-5 h-5 text-gray" />
                  <div className="flex-1">
                    <input
                      type="text"
                      value={chapter.title}
                      onChange={(e) => {
                        e.stopPropagation();
                        setChapters(
                          chapters.map((ch) =>
                            ch.id === chapter.id
                              ? { ...ch, title: e.target.value }
                              : ch
                          )
                        );
                      }}
                      className="bg-transparent font-medium focus:outline-none"
                      onClick={(e) => e.stopPropagation()}
                    />
                  </div>
                  <span className="text-sm text-gray">
                    {chapter.subchapters.length} leçons
                  </span>
                </div>

                {/* Subchapters */}
                {activeChapter === chapter.id && (
                  <div className="p-5 space-y-4">
                    {chapter.subchapters.map((sub, subIdx) => (
                      <div key={sub.id} className="border border-black/5 rounded-xl p-4 space-y-4">
                        <div className="flex items-center gap-4">
                          <span className="text-sm font-medium text-orange">
                            Leçon {subIdx + 1}
                          </span>
                          <input
                            type="text"
                            value={sub.title}
                            onChange={(e) =>
                              updateSubchapter(chapter.id, sub.id, { title: e.target.value })
                            }
                            className="flex-1 px-3 py-2 bg-cream-m rounded-lg border border-black/5"
                            placeholder="Titre de la leçon"
                          />
                        </div>

                        <textarea
                          value={sub.content}
                          onChange={(e) =>
                            updateSubchapter(chapter.id, sub.id, { content: e.target.value })
                          }
                          className="w-full px-3 py-2 bg-cream-m rounded-lg border border-black/5 min-h-[100px]"
                          placeholder="Contenu de la leçon (Markdown supporté)..."
                        />

                        <div className="grid grid-cols-2 gap-4">
                          <div className="flex items-center gap-2">
                            <Video className="w-4 h-4 text-gray" />
                            <input
                              type="url"
                              value={sub.video_url || ""}
                              onChange={(e) =>
                                updateSubchapter(chapter.id, sub.id, { video_url: e.target.value })
                              }
                              className="flex-1 px-3 py-2 bg-cream-m rounded-lg border border-black/5 text-sm"
                              placeholder="Lien vidéo"
                            />
                          </div>
                          <div className="flex items-center gap-2">
                            <Image className="w-4 h-4 text-gray" />
                            <input
                              type="url"
                              value={sub.image_url || ""}
                              onChange={(e) =>
                                updateSubchapter(chapter.id, sub.id, { image_url: e.target.value })
                              }
                              className="flex-1 px-3 py-2 bg-cream-m rounded-lg border border-black/5 text-sm"
                              placeholder="Image URL"
                            />
                          </div>
                        </div>

                        {/* Quiz */}
                        <div className="mt-4 pt-4 border-t border-black/5">
                          <button
                            onClick={() => addQuestion(chapter.id, sub.id)}
                            className="text-sm text-orange font-medium"
                          >
                            + Ajouter un quiz
                          </button>
                          {sub.quiz?.questions.map((q, qIdx) => (
                            <div key={q.id} className="mt-3 p-3 bg-cream rounded-lg">
                              <input
                                type="text"
                                value={q.text}
                                onChange={(e) => {
                                  const newChapters = [...chapters];
                                  const ch = newChapters.find((c) => c.id === chapter.id);
                                  if (!ch) return;
                                  const s = ch.subchapters.find((s) => s.id === sub.id);
                                  if (!s?.quiz) return;
                                  s.quiz.questions[qIdx].text = e.target.value;
                                  setChapters(newChapters);
                                }}
                                className="w-full px-3 py-2 bg-white rounded-lg border border-black/5 mb-2"
                                placeholder="Question"
                              />
                              <div className="grid grid-cols-2 gap-2">
                                {q.options.map((opt, oIdx) => (
                                  <div key={oIdx} className="flex items-center gap-2">
                                    <input
                                      type="radio"
                                      name={`correct-${q.id}`}
                                      checked={q.correct === oIdx}
                                      onChange={() => {
                                        const newChapters = [...chapters];
                                        const ch = newChapters.find(
                                          (c) => c.id === chapter.id
                                        );
                                        if (!ch) return;
                                        const s = ch.subchapters.find(
                                          (s) => s.id === sub.id
                                        );
                                        if (!s?.quiz) return;
                                        s.quiz.questions[qIdx].correct = oIdx;
                                        setChapters(newChapters);
                                      }}
                                    />
                                    <input
                                      type="text"
                                      value={opt}
                                      onChange={(e) => {
                                        const newChapters = [...chapters];
                                        const ch = newChapters.find(
                                          (c) => c.id === chapter.id
                                        );
                                        if (!ch) return;
                                        const s = ch.subchapters.find(
                                          (s) => s.id === sub.id
                                        );
                                        if (!s?.quiz) return;
                                        s.quiz.questions[qIdx].options[oIdx] =
                                          e.target.value;
                                        setChapters(newChapters);
                                      }}
                                      className="flex-1 px-3 py-2 bg-white rounded-lg border border-black/5 text-sm"
                                      placeholder={`Option ${oIdx + 1}`}
                                    />
                                  </div>
                                ))}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}

                    <button
                      onClick={() => addSubchapter(chapter.id)}
                      className="w-full py-3 border-2 border-dashed border-gray/30 rounded-xl text-gray hover:border-orange hover:text-orange transition-colors"
                    >
                      + Ajouter une leçon
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <button
          onClick={saveCourse}
          disabled={saving || !courseTitle}
          className="flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-orange to-orange-l text-white rounded-xl font-semibold disabled:opacity-50"
        >
          <Save className="w-5 h-5" />
          {saving ? "Enregistrement..." : "Enregistrer le cours"}
        </button>
      </div>
    </div>
  );
}