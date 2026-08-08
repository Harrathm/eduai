import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuthStore } from "../../../store/authStore";
import apiClient from "../../../utils/apiClient";
import { Button } from "@/components/ui";

const NIVEAUX = [
  "1ère année", "2ème année", "3ème année", "4ème année", "5ème année", "6ème année",
  "7ème année", "8ème année", "9ème année",
  "1ère année secondaire", "2ème année secondaire", "3ème année secondaire", "4ème année secondaire"
];

export default function OnboardingPage() {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const { token, setUser, user } = useAuthStore();
  const [step, setStep] = useState(0);
  const [language, setLanguage] = useState(i18n.language?.slice(0, 2) || "fr");
  const [niveau, setNiveau] = useState(user?.niveau_scolaire || "");
  const [saving, setSaving] = useState(false);

  const handleLanguageSelect = (code: string) => {
    setLanguage(code);
    i18n.changeLanguage(code);
    localStorage.setItem("eduai_language", code);
    document.documentElement.dir = code === "ar" ? "rtl" : "ltr";
    document.documentElement.lang = code;
  };

  const handleFinish = async () => {
    setSaving(true);
    try {
      if (token) {
        await apiClient.put(`/auth/me/language?language=${language}`);
        if (niveau) {
          await apiClient.put("/users/me", { niveau_scolaire: niveau });
        }
        await apiClient.put("/auth/me/onboarding-complete");
        if (user) setUser({ ...user, language, niveau_scolaire: niveau, onboarding_complete: true } as any);
      }
      navigate("/dashboard");
    } catch {
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-navy-50 via-white to-purple-50 flex items-center justify-center p-8">
      <div className="max-w-lg w-full">
        {step === 0 && (
          <div className="bg-white rounded-3xl shadow-xl p-10 text-center">
            <div className="text-5xl mb-6">🎓</div>
            <h1 className="text-3xl font-bold text-navy mb-3">{t("onboarding.welcome_title")}</h1>
            <p className="text-gray-500 mb-8">{t("onboarding.welcome_desc")}</p>
            
            <h2 className="text-lg font-semibold text-navy mb-4">{t("onboarding.choose_language")}</h2>
            <div className="grid grid-cols-3 gap-3 mb-8">
              {[
                { code: "fr", label: "Français", flag: "🇫🇷" },
                { code: "en", label: "English", flag: "🇬🇧" },
                { code: "ar", label: "العربية", flag: "🇹🇳" },
              ].map((l) => (
                <Button
                  key={l.code}
                  variant="ghost"
                  size="md"
                  onClick={() => handleLanguageSelect(l.code)}
                >
                  <span className="text-2xl">{l.flag}</span>
                  <span className="text-sm font-medium">{l.label}</span>
                </Button>
              ))}
            </div>
            
            <Button
              variant="secondary"
              size="md"
              onClick={() => setStep(1)}
            >
              {t("onboarding.next")}
            </Button>
          </div>
        )}

        {step === 1 && (
          <div className="bg-white rounded-3xl shadow-xl p-10">
            <h2 className="text-2xl font-bold text-navy mb-2 text-center">{t("onboarding.choose_level")}</h2>
            <p className="text-gray-500 mb-6 text-center">{t("profile.niveau")}</p>
            
            <div className="grid grid-cols-2 gap-2 mb-8 max-h-80 overflow-y-auto">
              {NIVEAUX.map((n) => (
                <Button
                  key={n}
                  variant={niveau === n ? "primary" : "ghost"}
                  size="md"
                  onClick={() => setNiveau(n)}
                >
                  {n}
                </Button>
              ))}
            </div>
            
            <div className="flex gap-3">
              <Button
                variant="ghost"
                size="md"
                onClick={() => setStep(0)}
              >
                {t("common.back")}
              </Button>
              <Button
                variant="primary"
                size="lg"
                loading={saving}
                onClick={handleFinish}
                disabled={saving}
              >
                {saving ? t("common.loading") : t("onboarding.finish")}
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
