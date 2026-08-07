import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import apiClient from "../../../utils/apiClient";
import { Button, Spinner } from "../../../components/ui";

interface Question {
  question: string;
  options: string[];
  correct: string;
  difficulty: number;
}

interface Test {
  id: number;
  matiere: string;
  niveau: string;
  title: string;
  questions: { questions: Question[] };
}

export default function PlacementTestPage() {
  const { t } = useTranslation();
  const { testId } = useParams();
  const navigate = useNavigate();
  const [test, setTest] = useState<Test | null>(null);
  const [currentQ, setCurrentQ] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTest = async () => {
      try {
        const res = await apiClient.get(`/api/placement/tests/${testId}`);
        setTest(res.data);
      } catch {
        navigate("/dashboard");
      } finally {
        setLoading(false);
      }
    };
    fetchTest();
  }, [testId, navigate]);

  const handleAnswer = (qIndex: number, selected: string) => {
    setAnswers((prev) => ({ ...prev, [qIndex]: selected }));
    if (test && qIndex < test.questions.questions.length - 1) {
      setCurrentQ(qIndex + 1);
    }
  };

  const handleSubmit = async () => {
    if (!test) return;
    setSubmitting(true);
    try {
      const answerList = Object.entries(answers).map(([qi, sel]) => ({
        question_index: parseInt(qi),
        selected: sel,
      }));
      const res = await apiClient.post(`/api/placement/tests/${test.id}/submit`, { answers: answerList });
      // Auto-enroll in pathway
      try {
        const enrollRes = await apiClient.post(`/api/pathway/auto-enroll-from-test`);
        setResult({ ...res.data, auto_enroll: enrollRes.data });
      } catch {
        setResult({ ...res.data, auto_enroll: null });
      }
    } catch {
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <div className="flex justify-center p-12"><Spinner size="lg" /></div>;
  if (!test) return null;

  if (result) {
    return (
      <div className="max-w-2xl mx-auto p-8">
        <div className="bg-white rounded-2xl shadow-lg p-8 text-center">
          <div className="text-5xl mb-4">
            {result.competency_level === "avance" ? "🌟" : result.competency_level === "intermediaire" ? "📈" : "🌱"}
          </div>
          <h2 className="text-2xl font-bold text-navy mb-2">{t("placement.result")}</h2>
          <p className="text-4xl font-bold text-navy-600 mb-2">{result.score}%</p>
          <p className="text-gray-500 mb-6">
            {result.correct}/{result.total} correct — {t(`placement.${result.competency_level}`)}
          </p>
          <div className="flex flex-col gap-3 items-center">
            {result.auto_enroll && (
              <div className="w-full max-w-sm bg-green-50 border border-green-200 rounded-xl p-4 text-sm text-green-800">
                <p className="font-semibold mb-1">Parcours initialisé !</p>
                <p>{result.auto_enroll.chapters_initialized} chapitre(s) configuré(s) pour <b>{result.auto_enroll.niveau}</b></p>
                <p className="text-xs text-green-600 mt-1">Niveau: {result.auto_enroll.niveau_assimilation}</p>
              </div>
            )}
            <Button
              onClick={() => navigate(result.auto_enroll ? "/dashboard/mon-parcours" : "/dashboard/parcours-catalog")}
              variant="primary"
              size="md"
            >
              {result.auto_enroll ? "Voir mon parcours" : "Voir le catalogue"}
            </Button>
            <Button
              onClick={() => navigate("/dashboard")}
              variant="ghost"
              size="md"
            >
              {t("common.back")}
            </Button>
          </div>
        </div>
      </div>
    );
  }

  const questions = test.questions.questions || [];
  const q = questions[currentQ];
  const allAnswered = Object.keys(answers).length === questions.length;

  return (
    <div className="max-w-2xl mx-auto p-8">
      <h1 className="text-2xl font-bold text-navy mb-2">{test.title}</h1>
      <p className="text-gray-500 mb-8">{t("placement.description")}</p>

      <div className="bg-white rounded-2xl shadow-lg p-8">
        <div className="flex items-center justify-between mb-6">
          <span className="text-sm text-gray-500">
            {t("common.next")} {currentQ + 1} / {questions.length}
          </span>
          <div className="flex gap-1">
            {questions.map((_, i) => (
              <div
                key={i}
                className={`w-2 h-2 rounded-full ${
                  answers[i] ? "bg-green-500" : i === currentQ ? "bg-navy-600" : "bg-gray-200"
                }`}
              />
            ))}
          </div>
        </div>

        {q && (
          <div>
            <p className="text-lg font-medium text-navy mb-4">{q.question}</p>
            <div className="space-y-3">
              {q.options.map((opt, i) => (
                <Button
                  key={i}
                  onClick={() => handleAnswer(currentQ, opt)}
                  variant="ghost"
                  size="md"
                  className={`w-full text-start border-2 transition-all ${
                    answers[currentQ] === opt
                      ? "border-navy-600 bg-navy-50 text-navy-700"
                      : "border-gray-200 hover:border-gray-300"
                  }`}
                >
                  {opt}
                </Button>
              ))}
            </div>
          </div>
        )}

        <div className="flex justify-between mt-8">
          <Button
            onClick={() => setCurrentQ(Math.max(0, currentQ - 1))}
            disabled={currentQ === 0}
            variant="ghost"
            size="sm"
          >
            {t("common.previous")}
          </Button>
          {allAnswered ? (
            <Button
              onClick={handleSubmit}
              disabled={submitting}
              variant="success"
              size="md"
              loading={submitting}
            >
              {t("placement.submit")}
            </Button>
          ) : (
            <Button
              onClick={() => setCurrentQ(Math.min(questions.length - 1, currentQ + 1))}
              variant="secondary"
              size="sm"
            >
              {t("common.next")}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
