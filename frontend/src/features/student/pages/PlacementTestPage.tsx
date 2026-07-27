import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import apiClient from "../../../utils/apiClient";

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
        const res = await apiClient.get(`/placement/tests/${testId}`);
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
      const res = await apiClient.post(`/placement/tests/${test.id}/submit`, { answers: answerList });
      setResult(res.data);
    } catch {
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <div className="flex justify-center p-12"><div className="animate-spin w-8 h-8 border-2 border-indigo-600 border-t-transparent rounded-full" /></div>;
  if (!test) return null;

  if (result) {
    return (
      <div className="max-w-2xl mx-auto p-8">
        <div className="bg-white rounded-2xl shadow-lg p-8 text-center">
          <div className="text-5xl mb-4">
            {result.competency_level === "avance" ? "🌟" : result.competency_level === "intermediaire" ? "📈" : "🌱"}
          </div>
          <h2 className="text-2xl font-bold text-navy mb-2">{t("placement.result")}</h2>
          <p className="text-4xl font-bold text-indigo-600 mb-2">{result.score}%</p>
          <p className="text-gray-500 mb-6">
            {result.correct}/{result.total} correct — {t(`placement.${result.competency_level}`)}
          </p>
          <button
            onClick={() => navigate("/dashboard")}
            className="px-6 py-3 bg-indigo-600 text-white rounded-xl font-medium hover:bg-indigo-700"
          >
            {t("common.back")}
          </button>
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
                  answers[i] ? "bg-green-500" : i === currentQ ? "bg-indigo-600" : "bg-gray-200"
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
                <button
                  key={i}
                  onClick={() => handleAnswer(currentQ, opt)}
                  className={`w-full text-left px-4 py-3 rounded-xl border-2 transition-all ${
                    answers[currentQ] === opt
                      ? "border-indigo-600 bg-indigo-50 text-indigo-700"
                      : "border-gray-200 hover:border-gray-300"
                  }`}
                >
                  {opt}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="flex justify-between mt-8">
          <button
            onClick={() => setCurrentQ(Math.max(0, currentQ - 1))}
            disabled={currentQ === 0}
            className="px-4 py-2 text-gray-500 disabled:opacity-30"
          >
            {t("common.previous")}
          </button>
          {allAnswered ? (
            <button
              onClick={handleSubmit}
              disabled={submitting}
              className="px-6 py-3 bg-green-600 text-white rounded-xl font-medium hover:bg-green-700 disabled:opacity-50"
            >
              {submitting ? t("common.loading") : t("placement.submit")}
            </button>
          ) : (
            <button
              onClick={() => setCurrentQ(Math.min(questions.length - 1, currentQ + 1))}
              className="px-4 py-2 text-indigo-600"
            >
              {t("common.next")}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
