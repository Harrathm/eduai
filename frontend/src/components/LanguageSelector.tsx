import { useTranslation } from "react-i18next";
import { useAuthStore } from "../store/authStore";
import apiClient from "../utils/apiClient";

const LANGUAGES = [
  { code: "fr", label: "Français", flag: "🇫🇷" },
  { code: "en", label: "English", flag: "🇬🇧" },
  { code: "ar", label: "العربية", flag: "🇹🇳" },
];

export default function LanguageSelector() {
  const { i18n } = useTranslation();
  const { token } = useAuthStore();
  const current = i18n.language?.slice(0, 2) || "fr";

  const handleChange = async (code: string) => {
    i18n.changeLanguage(code);
    localStorage.setItem("eduai_language", code);
    document.documentElement.dir = code === "ar" ? "rtl" : "ltr";
    document.documentElement.lang = code;
    if (token) {
      try {
        await apiClient.put(`/auth/me/language?language=${code}`);
      } catch {}
    }
  };

  return (
    <div className="flex items-center gap-1 bg-white/10 rounded-lg px-2 py-1">
      {LANGUAGES.map((l) => (
        <button
          key={l.code}
          onClick={() => handleChange(l.code)}
          className={`px-2 py-1 text-xs rounded transition-colors ${
            current === l.code
              ? "bg-navy-600 text-white font-medium"
              : "text-gray-600 hover:bg-gray-100"
          }`}
          title={l.label}
        >
          {l.flag}
        </button>
      ))}
    </div>
  );
}
