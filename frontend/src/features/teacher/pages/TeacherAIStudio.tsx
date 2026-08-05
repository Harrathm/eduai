import { useState, useEffect } from "react";
import { useAuthStore } from "../../../store/authStore";
import { aiApi } from "../../../api";
import { Sparkles, BookOpen, FileText, Clock, Zap, Send, Coins, Loader2 } from "lucide-react";
import { conversationApi } from "../../../api";
const { exportMessagePdf, exportMessageDocx } = conversationApi;

const SUBJECTS = [
  "Mathématiques",
  "Physique",
  "Chimie",
  "Biologie",
  "Histoire",
  "Géographie",
  "Français",
  "Anglais",
  "Informatique",
  "Pédagogie",
];

const LEVELS = [
  "Primaire",
  "Collège",
  "Lycée",
  "Université",
];

const TRIMESTERS = [
  "Trimestre 1",
  "Trimestre 2",
  "Trimestre 3",
];

const CONTENT_TYPES = [
  { id: "homework", label: "Devoir", icon: "📝" },
  { id: "lesson", label: "Leçon", icon: "📖" },
  { id: "lesson_plan", label: "Plan de leçon", icon: "📋" },
  { id: "outline", label: "Plan annuel", icon: "📅" },
  { id: "quiz", label: "Quiz", icon: "❓" },
  { id: "summary", label: "Résumé", icon: "📄" },
];

export default function TeacherAIStudio() {
  const { token, user } = useAuthStore();
  const [selectedType, setSelectedType] = useState("homework");
  const [prompt, setPrompt] = useState("");
  const [subject, setSubject] = useState(SUBJECTS[0]);
  const [level, setLevel] = useState(LEVELS[0]);
  const [trimester, setTrimester] = useState(TRIMESTERS[0]);
  const [generating, setGenerating] = useState(false);
  const [result, setResult] = useState<string>("");
  const [history, setHistory] = useState<{ id: number; prompt: string; type: string }[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [exporting, setExporting] = useState<"pdf" | "docx" | null>(null);
  const [balanceData, setBalanceData] = useState<{ total: number; pools: { pool: string; balance: number }[] } | null>(null);

  useEffect(() => {
    fetchHistory();
    fetchBalance();
  }, [token]);

  const fetchHistory = async () => {
    if (!token) return;
    setLoadingHistory(true);
    try {
      const data = await aiApi.history();
      setHistory(data);
    } catch (err) {
      console.error(err);
    }
    setLoadingHistory(false);
  };

  const fetchBalance = async () => {
    if (!token) return;
    try {
      const data = await aiApi.wallet();
      setBalanceData(data);
    } catch (err) {
      console.error(err);
    }
  };

  const totalTokens = balanceData?.total ?? 0;
  const totalDT = balanceData?.pools?.find((p) => p.pool === "dt_purchased")?.balance ?? 0;

  const generateContent = async () => {
    if (!token || !prompt) return;
    setGenerating(true);
    try {
      const data = await aiApi.generate({
        prompt,
        type: selectedType,
      });
      setResult(data.content);
    } catch (err) {
      console.error(err);
      setResult("Erreur de connexion.");
    }
    setGenerating(false);
  };

  const handleExport = async (format: "pdf" | "docx") => {
    if (!result) return;
    setExporting(format);
    try {
      if (format === "pdf") {
        await exportMessagePdf(result, "assistant", `Studio IA — ${selectedType}`);
      } else {
        await exportMessageDocx(result, "assistant", `Studio IA — ${selectedType}`);
      }
    } catch (err) {
      console.error("Export error:", err);
    }
    setExporting(null);
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-3xl p-8 shadow-sm border border-black/5">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-[300] text-navy">
              AI <span className="italic text-orange">Studio</span>
            </h1>
            <p className="text-gray mt-2">
              Générez du contenu pédagogique avec l'IA
            </p>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 bg-orange-p px-4 py-2 rounded-xl">
              <Coins className="w-5 h-5 text-orange" />
              <span className="font-semibold text-orange">
                {totalTokens} tokens
              </span>
            </div>
            <div className="flex items-center gap-2 bg-yellow-50 px-4 py-2 rounded-xl">
              <span className="font-semibold text-yellow-700">
                {totalDT} DT
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Generator */}
        <div className="lg:col-span-2 space-y-6">
          {/* Content Type */}
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
            <h2 className="text-lg font-semibold text-navy mb-4">
              Type de contenu
            </h2>
            <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
              {CONTENT_TYPES.map((type) => (
                <button
                  key={type.id}
                  onClick={() => setSelectedType(type.id)}
                  className={`p-4 rounded-xl text-center transition-all ${
                    selectedType === type.id
                      ? "bg-orange text-white"
                      : "bg-cream-m hover:bg-cream text-gray"
                  }`}
                >
                  <div className="text-2xl mb-1">{type.icon}</div>
                  <div className="text-sm font-medium">{type.label}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Options */}
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray mb-2">
                  Matière
                </label>
                <select
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5"
                >
                  {SUBJECTS.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray mb-2">
                  Niveau
                </label>
                <select
                  value={level}
                  onChange={(e) => setLevel(e.target.value)}
                  className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5"
                >
                  {LEVELS.map((l) => (
                    <option key={l} value={l}>
                      {l}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray mb-2">
                  Trimestre
                </label>
                <select
                  value={trimester}
                  onChange={(e) => setTrimester(e.target.value)}
                  className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5"
                >
                  {TRIMESTERS.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Prompt */}
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
            <h2 className="text-lg font-semibold text-navy mb-4">
              Description du contenu désiré
            </h2>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              className="w-full px-5 py-4 bg-cream-m rounded-xl border border-black/5 min-h-[150px]"
              placeholder="Décrivez ce que vous voulez générer... Ex: 'Un devoir sur les équations du premier degré pour les élèves de 3ème année collège, comprenant 5 exercices de difficulté progressive'"
            />
            <div className="flex justify-between items-center mt-4">
              <p className="text-sm text-gray">
                Coût estimé: ~5 tokens
              </p>
              <button
                onClick={generateContent}
                disabled={generating || !prompt}
                className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-orange to-orange-l text-white rounded-xl font-medium disabled:opacity-50"
              >
                <Zap className="w-5 h-5" />
                {generating ? "Génération..." : "Générer"}
              </button>
            </div>
          </div>

          {/* Result */}
          {result && (
            <div className="bg-white rounded-2xl shadow-sm border border-black/5 overflow-hidden">
              <div className="bg-navy p-4 flex justify-between items-center">
                <h3 className="text-white font-semibold">Résultat</h3>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleExport("pdf")}
                    disabled={exporting === "pdf"}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-white/10 hover:bg-white/20 text-white rounded-lg text-sm transition-colors disabled:opacity-50"
                  >
                    {exporting === "pdf" ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <FileText className="w-3.5 h-3.5" />
                    )}
                    PDF
                  </button>
                  <button
                    onClick={() => handleExport("docx")}
                    disabled={exporting === "docx"}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-white/10 hover:bg-white/20 text-white rounded-lg text-sm transition-colors disabled:opacity-50"
                  >
                    {exporting === "docx" ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <FileText className="w-3.5 h-3.5" />
                    )}
                    DOCX
                  </button>
                  <button
                    onClick={() => {
                      if (result) navigator.clipboard.writeText(result);
                    }}
                    className="text-white/70 hover:text-white text-sm ms-2"
                  >
                    Copier
                  </button>
                </div>
              </div>
              <div className="p-6 prose max-w-none">
                <pre className="whitespace-pre-wrap font-sans text-sm">
                  {result}
                </pre>
              </div>
            </div>
          )}
        </div>

        {/* History */}
        <div className="space-y-4">
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
            <h2 className="text-lg font-semibold text-navy mb-4">
              Historique
            </h2>
            {loadingHistory ? (
              <div className="text-center py-8 text-gray">Chargement...</div>
            ) : history.length === 0 ? (
              <div className="text-center py-8 text-gray">
                <Sparkles className="w-10 h-10 mx-auto mb-3 opacity-30" />
                <p>Aucun historique</p>
              </div>
            ) : (
              <div className="space-y-2">
                {history.slice(0, 10).map((h) => (
                  <div
                    key={h.id}
                    className="p-3 bg-cream-m rounded-xl text-sm cursor-pointer hover:bg-cream"
                  >
                    <div className="font-medium">{h.prompt}</div>
                    <div className="text-xs text-gray mt-1">{h.type}</div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Quick Actions */}
          <div className="bg-gradient-to-br from-navy to-navy-m rounded-2xl p-6">
            <h3 className="text-white font-semibold mb-4">Générations rapides</h3>
            <div className="space-y-2">
              {["Devoir type examen", "Leçon complète", "Plan annuel"].map((q) => (
                <button
                  key={q}
                  onClick={() => setPrompt(q)}
                  className="w-full p-3 bg-white/10 text-white text-start rounded-xl text-sm hover:bg-white/20 transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}