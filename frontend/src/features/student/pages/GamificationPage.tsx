import { useState, useEffect, useCallback } from "react";
import { Trophy, Flame, Star, Award, Medal, Crown, TrendingUp, CheckCircle } from "lucide-react";
import { useAuthStore } from "../../../store/authStore";
import { gamificationApi } from "../../../api";

interface Badge {
  id: number; nom: string; description: string; icon_url: string | null;
  couleur: string; categorie: string; points: number;
  obtenu: boolean; date_obtention: string | null;
}

interface StreakData {
  current_streak: number; total_points: number;
  history: { date: string; login: boolean; quiz: boolean; objectif: boolean; points: number }[];
}

interface Ranking {
  rang: number; eleve_id: number; points: number;
}

const categorieLabels: Record<string, string> = {
  progression: "Progression", quiz: "Quiz", streak: "Série", special: "Spécial",
};
const categorieColors: Record<string, string> = {
  progression: "bg-blue-100 text-blue", quiz: "bg-green-100 text-green",
  streak: "bg-orange-100 text-orange", special: "bg-purple-100 text-purple",
};

export default function GamificationPage() {
  const { user } = useAuthStore();
  const [badges, setBadges] = useState<Badge[]>([]);
  const [streak, setStreak] = useState<StreakData | null>(null);
  const [rankings, setRankings] = useState<Ranking[]>([]);
  const [myRank, setMyRank] = useState<{ rang: number; points: number } | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"badges" | "streak" | "rankings">("badges");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [badgesRes, streakRes, rankRes] = await Promise.all([
        gamificationApi.badges(),
        gamificationApi.streak(),
        gamificationApi.rankings(),
      ]);
      setBadges(badgesRes);
      setStreak(streakRes);
      setRankings(rankRes.rankings || []);
      setMyRank(rankRes.me || null);
    } catch { /* ignore */ }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) {
    return <div className="text-center py-12 text-gray">Chargement...</div>;
  }

  const earnedCount = badges.filter(b => b.obtenu).length;
  const totalPoints = badges.filter(b => b.obtenu).reduce((acc, b) => acc + b.points, 0);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-display font-light text-navy">Gamification <span className="italic text-orange">& Récompenses</span></h1>
          <p className="text-gray text-sm mt-1">Badges, séries et classements</p>
        </div>
        <div className="flex gap-4 text-center">
          <div className="bg-white rounded-xl px-4 py-2 shadow-sm border border-black/5">
            <p className="text-2xl font-bold text-orange">{totalPoints}</p>
            <p className="text-xs text-gray">Points</p>
          </div>
          <div className="bg-white rounded-xl px-4 py-2 shadow-sm border border-black/5">
            <p className="text-2xl font-bold text-blue">{earnedCount}/{badges.length}</p>
            <p className="text-xs text-gray">Badges</p>
          </div>
          <div className="bg-white rounded-xl px-4 py-2 shadow-sm border border-black/5">
            <p className="text-2xl font-bold text-orange flex items-center gap-1 justify-center">
              <Flame className="w-5 h-5" />{streak?.current_streak || 0}
            </p>
            <p className="text-xs text-gray">Streak</p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 p-1 bg-cream-m rounded-xl w-fit">
        {(["badges", "streak", "rankings"] as const).map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
              activeTab === tab ? "bg-white text-navy shadow-sm" : "text-gray hover:text-navy"
            }`}
          >
            {tab === "badges" ? "Badges" : tab === "streak" ? "Séries" : "Classements"}
          </button>
        ))}
      </div>

      {/* Badges */}
      {activeTab === "badges" && (
        <div className="space-y-4">
          {Object.keys(categorieLabels).map(cat => {
            const catBadges = badges.filter(b => b.categorie === cat);
            if (catBadges.length === 0) return null;
            return (
              <div key={cat}>
                <h3 className={`text-sm font-semibold mb-3 px-3 py-1 rounded-full inline-block ${categorieColors[cat]}`}>
                  {categorieLabels[cat]}
                </h3>
                <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
                  {catBadges.map(badge => (
                    <div key={badge.id} className={`bg-white rounded-2xl p-4 border transition-all ${
                      badge.obtenu ? "border-orange/30 shadow-sm" : "border-black/5 opacity-60"
                    }`}>
                      <div className="flex items-start gap-3">
                        <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-2xl ${
                          badge.obtenu ? "bg-orange/10" : "bg-gray-100"
                        }`} style={badge.obtenu ? { borderColor: badge.couleur } : {}}>
                          {badge.obtenu ? <Award className="w-6 h-6" style={{ color: badge.couleur }} /> : <Award className="w-6 h-6 text-gray-300" />}
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <p className="font-semibold text-navy text-sm">{badge.nom}</p>
                            {badge.obtenu && <CheckCircle className="w-4 h-4 text-green" />}
                          </div>
                          <p className="text-xs text-gray mt-0.5">{badge.description}</p>
                          <div className="flex items-center gap-2 mt-2">
                            <span className="text-xs font-bold text-orange">{badge.points} pts</span>
                            {badge.obtenu && badge.date_obtention && (
                              <span className="text-xs text-gray">• {new Date(badge.date_obtention).toLocaleDateString("fr-FR")}</span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Streak */}
      {activeTab === "streak" && streak && (
        <div className="space-y-4">
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-16 h-16 bg-orange/10 rounded-2xl flex items-center justify-center">
                <Flame className="w-8 h-8 text-orange" />
              </div>
              <div>
                <p className="text-3xl font-bold text-navy">{streak.current_streak} jours</p>
                <p className="text-sm text-gray">Série actuelle</p>
              </div>
            </div>
            <div className="flex gap-4">
              <div className="flex items-center gap-2 text-sm text-gray">
                <span className="w-3 h-3 bg-green rounded-full" /> Login
              </div>
              <div className="flex items-center gap-2 text-sm text-gray">
                <span className="w-3 h-3 bg-blue rounded-full" /> Quiz
              </div>
              <div className="flex items-center gap-2 text-sm text-gray">
                <span className="w-3 h-3 bg-purple-500 rounded-full" /> Objectif
              </div>
            </div>
          </div>

          <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
            <h3 className="font-semibold text-navy mb-4">30 derniers jours</h3>
            <div className="grid grid-cols-10 gap-2">
              {streak.history.slice(0, 30).map(day => (
                <div
                  key={day.date}
                  className={`w-full aspect-square rounded-lg flex items-center justify-center text-xs font-bold ${
                    day.points >= 15 ? "bg-green text-white" :
                    day.points >= 8 ? "bg-blue text-white" :
                    day.points >= 3 ? "bg-orange/20 text-orange" :
                    "bg-gray-100 text-gray-300"
                  }`}
                  title={`${day.date}: ${day.points} pts`}
                >
                  {new Date(day.date).getDate()}
                </div>
              ))}
            </div>
            <p className="text-xs text-gray mt-3">{streak.total_points} points gagnés sur 30 jours</p>
          </div>
        </div>
      )}

      {/* Rankings */}
      {activeTab === "rankings" && (
        <div className="bg-white rounded-2xl shadow-sm border border-black/5 overflow-hidden">
          {myRank && (
            <div className="px-6 py-4 bg-orange/5 border-b border-orange/20">
              <div className="flex items-center gap-3">
                <Crown className="w-6 h-6 text-orange" />
                <div>
                  <p className="text-sm text-gray">Votre position</p>
                  <p className="text-xl font-bold text-navy">#{myRank.rang} — {myRank.points} points</p>
                </div>
              </div>
            </div>
          )}
          <div className="divide-y divide-gray-100">
            {rankings.map(r => {
              const medal = r.rang === 1 ? "text-yellow-500" : r.rang === 2 ? "text-gray-400" : r.rang === 3 ? "text-orange" : "text-gray-300";
              return (
                <div key={r.eleve_id} className={`flex items-center gap-4 px-6 py-3 ${
                  r.eleve_id === user?.id ? "bg-orange/5" : ""
                }`}>
                  <div className={`w-8 text-center font-bold ${medal}`}>
                    {r.rang <= 3 ? <Medal className="w-5 h-5 mx-auto" /> : `#${r.rang}`}
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-navy">{r.eleve_id === user?.id ? "Vous" : `Élève #${r.eleve_id}`}</p>
                  </div>
                  <p className="font-bold text-orange">{r.points} pts</p>
                </div>
              );
            })}
            {rankings.length === 0 && (
              <p className="text-center py-8 text-gray">Aucun classement disponible</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
