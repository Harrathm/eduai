import { useState, useEffect } from "react";
import { useTranslation } from 'react-i18next';
import { useAuthStore } from "../../../store/authStore";
import { aiApi } from "../../../api";
import { Sparkles, BookOpen, FileText, Clock, Zap, Send, Coins } from "lucide-react";
import { conversationApi } from "../../../api";
import { Button, Spinner } from "../../../components/ui";
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

export default function TeacherAIStudio() {
  const { t } = useTranslation();
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

  const CONTENT_TYPES = [
    { id: "homework", label: t('teacher.aiStudio.contentTypes.homework'), icon: "📝" },
    { id: "lesson", label: t('teacher.aiStudio.contentTypes.lesson'), icon: "📖" },
    { id: "lesson_plan", label: t('teacher.aiStudio.contentTypes.lessonPlan'), icon: "📋" },
    { id: "outline", label: t('teacher.aiStudio.contentTypes.outline'), icon: "📅" },
    { id: "quiz", label: t('teacher.aiStudio.contentTypes.quiz'), icon: "❓" },
    { id: "summary", label: t('teacher.aiStudio.contentTypes.summary'), icon: "📄" },
  ];

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
      setResult(t('teacher.aiStudio.error'));
    }
    setGenerating(false);
  };

  const handleExport = async (format: "pdf" | "docx") => {
    if (!result) return;
    setExporting(format);
    try {
      if (format === "pdf") {
        await exportMessagePdf(result, "assistant", `${t('teacher.aiStudio.title')} — ${selectedType}`);
      } else {
        await exportMessageDocx(result, "assistant", `${t('teacher.aiStudio.title')} — ${selectedType}`);
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
              {t('teacher.aiStudio.title')} <span className="italic text-orange">{t('teacher.aiStudio.titleSuffix')}</span>
            </h1>
            <p className="text-gray mt-2">
              {t('teacher.aiStudio.subtitle')}
            </p>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 bg-orange-p px-4 py-2 rounded-xl">
              <Coins className="w-5 h-5 text-orange" />
              <span className="font-semibold text-orange">
                {totalTokens} {t('teacher.aiStudio.tokens')}
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
              {t('teacher.aiStudio.contentType')}
            </h2>
            <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
              {CONTENT_TYPES.map((type) => (
                <Button
                  key={type.id}
                  onClick={() => setSelectedType(type.id)}
                  variant={selectedType === type.id ? "primary" : "ghost"}
                  size="md"
                  className="p-4 rounded-xl text-center transition-all"
                >
                  <div className="text-2xl mb-1">{type.icon}</div>
                  <div className="text-sm font-medium">{type.label}</div>
                </Button>
              ))}
            </div>
          </div>

          {/* Options */}
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray mb-2">
                   {t('teacher.aiStudio.subject')}
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
                   {t('teacher.aiStudio.level')}
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
                   {t('teacher.aiStudio.trimester')}
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
              {t('teacher.aiStudio.description')}
            </h2>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              className="w-full px-5 py-4 bg-cream-m rounded-xl border border-black/5 min-h-[150px]"
              placeholder={t('teacher.aiStudio.placeholder')}
            />
            <div className="flex justify-between items-center mt-4">
              <p className="text-sm text-gray">
                {t('teacher.aiStudio.estimatedCost')}
              </p>
              <Button
                onClick={generateContent}
                disabled={generating || !prompt}
                variant="primary"
                size="md"
                loading={generating}
                className="flex items-center gap-2 px-6 py-3 rounded-xl font-medium"
              >
                <Zap className="w-5 h-5" />
                {generating ? t('teacher.aiStudio.generating') : t('teacher.aiStudio.generate')}
              </Button>
            </div>
          </div>

          {/* Result */}
          {result && (
            <div className="bg-white rounded-2xl shadow-sm border border-black/5 overflow-hidden">
              <div className="bg-navy p-4 flex justify-between items-center">
                <h3 className="text-white font-semibold">{t('teacher.aiStudio.result')}</h3>
                <div className="flex items-center gap-2">
                  <Button
                    onClick={() => handleExport("pdf")}
                    disabled={exporting === "pdf"}
                    variant="ghost"
                    size="sm"
                    loading={exporting === "pdf"}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-white rounded-lg text-sm transition-colors"
                  >
                    {exporting === "pdf" ? (
                      <Spinner className="w-3.5 h-3.5" />
                    ) : (
                      <FileText className="w-3.5 h-3.5" />
                    )}
                    PDF
                  </Button>
                  <Button
                    onClick={() => handleExport("docx")}
                    disabled={exporting === "docx"}
                    variant="ghost"
                    size="sm"
                    loading={exporting === "docx"}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-white rounded-lg text-sm transition-colors"
                  >
                    {exporting === "docx" ? (
                      <Spinner className="w-3.5 h-3.5" />
                    ) : (
                      <FileText className="w-3.5 h-3.5" />
                    )}
                    DOCX
                  </Button>
                  <Button
                    onClick={() => {
                      if (result) navigator.clipboard.writeText(result);
                    }}
                    variant="ghost"
                    size="sm"
                    className="text-white/70 hover:text-white text-sm ms-2"
                  >
                    {t('teacher.aiStudio.copy')}
                  </Button>
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
              {t('teacher.aiStudio.history')}
            </h2>
            {loadingHistory ? (
              <div className="text-center py-8 text-gray">{t('teacher.aiStudio.loading')}</div>
            ) : history.length === 0 ? (
              <div className="text-center py-8 text-gray">
                <Sparkles className="w-10 h-10 mx-auto mb-3 opacity-30" />
                <p>{t('teacher.aiStudio.noHistory')}</p>
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
            <h3 className="text-white font-semibold mb-4">{t('teacher.aiStudio.quickGenerations')}</h3>
            <div className="space-y-2">
              {[t('teacher.aiStudio.quickActions.exam'), t('teacher.aiStudio.quickActions.lesson'), t('teacher.aiStudio.quickActions.outline')].map((q) => (
                <Button
                  key={q}
                  onClick={() => setPrompt(q)}
                  variant="ghost"
                  size="sm"
                  className="w-full p-3 text-white text-start rounded-xl text-sm transition-colors"
                >
                  {q}
                </Button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}