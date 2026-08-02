import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useAuthStore } from "../../../store/authStore";
import apiClient from "../../../utils/apiClient";
import { User, Save, Check } from "lucide-react";

const NIVEAUX = [
  "1ère année", "2ème année", "3ème année", "4ème année", "5ème année", "6ème année",
  "7ème année", "8ème année", "9ème année",
  "1ère année secondaire", "2ème année secondaire", "3ème année secondaire", "4ème année secondaire"
];

const LANGUAGES = [
  { code: "fr", label: "Français", flag: "🇫🇷" },
  { code: "en", label: "English", flag: "🇬🇧" },
  { code: "ar", label: "العربية", flag: "🇹🇳" },
];

export default function ProfilePage() {
  const { t, i18n } = useTranslation();
  const { user, setUser, token } = useAuthStore();
  const [language, setLanguage] = useState(user?.language || i18n.language?.slice(0, 2) || "fr");
  const [niveau, setNiveau] = useState(user?.niveau_scolaire || "");
  const [fullName, setFullName] = useState(user?.full_name || "");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const handleLanguageChange = (code: string) => {
    setLanguage(code);
    i18n.changeLanguage(code);
    localStorage.setItem("eduai_language", code);
    document.documentElement.dir = code === "ar" ? "rtl" : "ltr";
    document.documentElement.lang = code;
  };

  const handleSave = async () => {
    setSaving(true);
    setSaved(false);
    try {
      if (token) {
        await apiClient.put(`/auth/me/language?language=${language}`);
        await apiClient.put("/users/me", {
          niveau_scolaire: niveau || undefined,
          full_name: fullName || undefined,
        });
        if (user) {
          setUser({ ...user, language, niveau_scolaire: niveau, full_name: fullName });
        }
      }
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (e) {
      console.error("Profile save error:", e);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-display font-light text-navy">{t("profile.title", "Mon Profil")}</h1>
        <p className="text-gray text-sm mt-1">{t("profile.subtitle", "Gérez vos préférences")}</p>
      </div>

      {/* User Info */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
        <div className="flex items-center gap-4 mb-6">
          <div className="p-3 bg-orange/10 rounded-xl">
            <User className="w-6 h-6 text-orange" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-navy">{t("profile.info", "Informations")}</h2>
          </div>
        </div>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray mb-1">{t("profile.name", "Nom complet")}</label>
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="w-full px-4 py-2.5 bg-cream rounded-xl border-0 text-sm focus:ring-2 focus:ring-orange/30 outline-none"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray mb-1">{t("profile.email", "Email")}</label>
            <input
              type="email"
              value={user?.email || ""}
              disabled
              className="w-full px-4 py-2.5 bg-gray-50 rounded-xl border-0 text-sm text-gray cursor-not-allowed"
            />
          </div>
        </div>
      </div>

      {/* Language Selection */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
        <h2 className="text-lg font-semibold text-navy mb-4">{t("profile.language", "Langue")}</h2>
        <div className="grid grid-cols-3 gap-3">
          {LANGUAGES.map((l) => (
            <button
              key={l.code}
              onClick={() => handleLanguageChange(l.code)}
              className={`p-4 rounded-2xl border-2 transition-all flex flex-col items-center gap-2 ${
                language === l.code
                  ? "border-orange bg-orange/5 shadow-sm"
                  : "border-gray-200 hover:border-gray-300"
              }`}
            >
              <span className="text-2xl">{l.flag}</span>
              <span className="text-sm font-medium">{l.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Niveau Scolaire */}
      {user?.role === "student" && (
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <h2 className="text-lg font-semibold text-navy mb-4">{t("profile.niveau", "Niveau scolaire")}</h2>
          <div className="grid grid-cols-2 gap-2 max-h-60 overflow-y-auto">
            {NIVEAUX.map((n) => (
              <button
                key={n}
                onClick={() => setNiveau(n)}
                className={`p-3 rounded-xl border-2 text-left text-sm transition-all ${
                  niveau === n
                    ? "border-orange bg-orange/5 text-orange font-medium"
                    : "border-gray-200 hover:border-gray-300"
                }`}
              >
                {n}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Save Button */}
      <button
        onClick={handleSave}
        disabled={saving}
        className="flex items-center gap-2 px-6 py-3 bg-orange text-white rounded-xl font-medium hover:bg-orange-w transition-colors disabled:opacity-50"
      >
        {saved ? (
          <><Check className="w-5 h-5" /> {t("profile.saved", "Sauvegardé !")}</>
        ) : saving ? (
          <>{t("profile.saving", "Sauvegarde...")}</>
        ) : (
          <><Save className="w-5 h-5" /> {t("profile.save", "Sauvegarder")}</>
        )}
      </button>
    </div>
  );
}
