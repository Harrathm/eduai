import { useState, useEffect, useCallback } from "react";
import { Brain, TrendingUp, TrendingDown, Minus, BookOpen, Layers } from "lucide-react";
import { useAuthStore } from "../../../store/authStore";
import { getMatieres, getChapters, getNotions, getNiveauEffectif } from "../../pathway/api";
import type { Matiere, ChapterPathway, Notion, NiveauEffectif } from "../../pathway/api";

const LEVEL_COLORS: Record<string, { bg: string; text: string; label: string; icon: any }> = {
  remediation: { bg: "bg-red-100", text: "text-red-700", label: "Remédiation", icon: TrendingDown },
  standard: { bg: "bg-blue-100", text: "text-blue-700", label: "Standard", icon: Minus },
  avance: { bg: "bg-green-100", text: "text-green-700", label: "Avancé", icon: TrendingUp },
};

export default function StudentAssimilationProfilePage() {
  const { user } = useAuthStore();
  const [matieres, setMatieres] = useState<Matiere[]>([]);
  const [chapters, setChapters] = useState<ChapterPathway[]>([]);
  const [notions, setNotions] = useState<Notion[]>([]);
  const [profiles, setProfiles] = useState<Record<number, NiveauEffectif>>({});
  const [loading, setLoading] = useState(true);
  const [selectedMatiere, setSelectedMatiere] = useState<number | null>(null);

  const load = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    try {
      const [m, c, n] = await Promise.all([getMatieres(), getChapters(), getNotions()]);
      setMatieres(m);
      setChapters(c);
      setNotions(n);

      // Load profile for each chapter
      const profMap: Record<number, NiveauEffectif> = {};
      await Promise.all(
        c.map(async (ch) => {
          try {
            const p = await getNiveauEffectif(user.id, ch.id);
            profMap[ch.id] = p;
          } catch { /* ignore */ }
        })
      );
      setProfiles(profMap);
    } catch { /* ignore */ }
    setLoading(false);
  }, [user]);

  useEffect(() => { load(); }, [load]);

  const filteredChapters = selectedMatiere
    ? chapters.filter(c => c.matiere_id === selectedMatiere)
    : chapters;

  const getLevelStats = () => {
    const counts = { remediation: 0, standard: 0, avance: 0, default: 0 };
    Object.values(profiles).forEach(p => {
      if (p.source === "defaut_matiere") counts.default++;
      else if (p.niveau_effectif in counts) counts[p.niveau_effectif as keyof typeof counts]++;
    });
    return counts;
  };

  const stats = getLevelStats();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-display font-light text-navy">Mon Profil <span className="italic text-orange">d'Assimilation</span></h1>
        <p className="text-gray text-sm mt-1">Votre niveau par chapitre et matière — mis à jour automatiquement</p>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-white rounded-2xl p-5 shadow-sm border border-black/5">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-red-100 rounded-xl"><TrendingDown className="w-5 h-5 text-red-600" /></div>
            <div><p className="text-2xl font-bold text-red-600">{stats.remediation}</p><p className="text-xs text-gray">Remédiation</p></div>
          </div>
        </div>
        <div className="bg-white rounded-2xl p-5 shadow-sm border border-black/5">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-blue-100 rounded-xl"><Minus className="w-5 h-5 text-blue-600" /></div>
            <div><p className="text-2xl font-bold text-blue-600">{stats.standard}</p><p className="text-xs text-gray">Standard</p></div>
          </div>
        </div>
        <div className="bg-white rounded-2xl p-5 shadow-sm border border-black/5">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-green-100 rounded-xl"><TrendingUp className="w-5 h-5 text-green-600" /></div>
            <div><p className="text-2xl font-bold text-green-600">{stats.avance}</p><p className="text-xs text-gray">Avancé</p></div>
          </div>
        </div>
        <div className="bg-white rounded-2xl p-5 shadow-sm border border-black/5">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-gray-100 rounded-xl"><Brain className="w-5 h-5 text-gray-600" /></div>
            <div><p className="text-2xl font-bold text-gray-600">{stats.default}</p><p className="text-xs text-gray">Par défaut</p></div>
          </div>
        </div>
      </div>

      <div className="flex gap-2 flex-wrap">
        <button onClick={() => setSelectedMatiere(null)}
          className={`px-4 py-2 rounded-xl text-sm font-medium transition-colors ${
            !selectedMatiere ? "bg-orange text-white" : "bg-white text-gray border hover:bg-gray-50"
          }`}>Toutes</button>
        {matieres.map(m => (
          <button key={m.id} onClick={() => setSelectedMatiere(m.id)}
            className={`px-4 py-2 rounded-xl text-sm font-medium transition-colors ${
              selectedMatiere === m.id ? "bg-orange text-white" : "bg-white text-gray border hover:bg-gray-50"
            }`}>{m.nom}</button>
        ))}
      </div>

      {loading ? (
        <div className="text-center py-12 text-gray">Chargement...</div>
      ) : (
        <div className="space-y-4">
          {filteredChapters.map(ch => {
            const profile = profiles[ch.id];
            const matiereName = matieres.find(m => m.id === ch.matiere_id)?.nom || "?";
            const notionCount = notions.filter(n => n.chapitre_id === ch.id).length;
            const level = profile?.niveau_effectif || "standard";
            const levelInfo = LEVEL_COLORS[level] || LEVEL_COLORS.standard;
            const LevelIcon = levelInfo.icon;

            return (
              <div key={ch.id} className="bg-white rounded-2xl shadow-sm border border-black/5 p-5">
                <div className="flex items-center gap-4">
                  <div className={`p-3 rounded-xl ${levelInfo.bg}`}>
                    <LevelIcon className={`w-5 h-5 ${levelInfo.text}`} />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-navy">{ch.nom}</h3>
                    <p className="text-xs text-gray">{matiereName} • {notionCount} notion{notionCount > 1 ? "s" : ""}</p>
                  </div>
                  <div className="text-right">
                    <span className={`inline-flex items-center gap-1 px-3 py-1.5 rounded-full text-xs font-medium ${levelInfo.bg} ${levelInfo.text}`}>
                      {levelInfo.label}
                    </span>
                    {profile?.source === "defaut_matiere" && (
                      <p className="text-xs text-gray mt-1">Défaut matière</p>
                    )}
                    {profile?.score_declencheur != null && (
                      <p className="text-xs text-gray mt-1">Score: {Math.round(profile.score_declencheur * 100)}%</p>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
          {filteredChapters.length === 0 && (
            <div className="text-center py-12 text-gray">Aucun chapitre trouvé</div>
          )}
        </div>
      )}
    </div>
  );
}
