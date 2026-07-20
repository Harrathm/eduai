import { useState, useEffect } from "react";
import { useAuthStore } from "../../../store/authStore";
import { 
  Settings, 
  Save, 
  Key, 
  DollarSign, 
  Zap, 
  Users,
  Wrench,
  Eye,
  EyeOff,
  CheckCircle,
  Loader2,
  TestTube,
  AlertTriangle,
  Wifi,
  WifiOff,
  Lock,
  ChevronDown,
  Bot,
  Sparkles
} from "lucide-react";

const API_URL = "";

interface PlatformSettings {
  ai_generation_cost_lesson: number;
  ai_generation_cost_quiz: number;
  ai_generation_cost_homework: number;
  ai_generation_cost_plan: number;
  token_pack_100_price: number;
  token_pack_500_price: number;
  token_pack_1000_price: number;
  subscription_teacher_pro: number;
  subscription_school: number;
  subscription_institution: number;
  maintenance_mode: boolean;
  allow_teacher_registration: boolean;
  allow_new_signups: boolean;
}

const AI_PROVIDERS = [
  { id: "freetokenfaucet", name: "FreeTokenFaucet", icon: "🆓", color: "bg-teal-600" },
  { id: "nvidia", name: "NVIDIA", icon: "🟢", color: "bg-green-700" },
  { id: "openai", name: "OpenAI", icon: "🤖", color: "bg-green-600" },
  { id: "groq", name: "Groq", icon: "⚡", color: "bg-orange-600" },
  { id: "openrouter", name: "OpenRouter", icon: "🌐", color: "bg-blue-600" },
  { id: "minimax", name: "MiniMax", icon: "🔮", color: "bg-violet-600" },
  { id: "anthropic", name: "Anthropic", icon: "🧠", color: "bg-purple-600" },
  { id: "azure", name: "Azure OpenAI", icon: "☁️", color: "bg-blue-500" },
  { id: "google", name: "Google AI", icon: "🔵", color: "bg-red-500" },
] as const;

const PROVIDER_MODELS = {
  freetokenfaucet: ["mimo-v2.5"],
  nvidia: ["z-ai/glm-5.2", "meta/llama-3.1-8b-instruct", "meta/llama-3.1-70b-instruct", "meta/llama-3.1-405b-instruct", "mistralai/mistral-7b-instruct-v0.3", "google/gemma-2-9b-it"],
  openai: ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4"],
  groq: ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768", "gemma2-9b-it"],
  openrouter: ["openai/gpt-4o", "openai/gpt-4o-mini", "anthropic/claude-3.5-sonnet", "meta/llama-3.3-70b", "google/gemini-2.0-flash"],
  minimax: ["MiniMaxAI/MiniMax-M2.7", "moonshotai/Kimi-K2.6", "GLM-5.2"],
  anthropic: ["claude-sonnet-4-20250514", "claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"],
  azure: ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
  google: ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"],
};

export default function PlatformSettings() {
  const { token } = useAuthStore();
  const [settings, setSettings] = useState<PlatformSettings>({
    ai_generation_cost_lesson: 15,
    ai_generation_cost_quiz: 10,
    ai_generation_cost_homework: 25,
    ai_generation_cost_plan: 50,
    token_pack_100_price: 5,
    token_pack_500_price: 20,
    token_pack_1000_price: 35,
    subscription_teacher_pro: 29,
    subscription_school: 199,
    subscription_institution: 999,
    maintenance_mode: false,
    allow_teacher_registration: true,
    allow_new_signups: true,
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [activeTab, setActiveTab] = useState<"economy" | "system" | "api">("economy");
  const [testConnection, setTestConnection] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<{success: boolean; message: string} | null>(null);
  
  const [apiConfig, setApiConfig] = useState<Record<string, {key: string, model: string, enabled: boolean, extra?: {endpoint?: string, base_url?: string}}>>({
    freetokenfaucet: { key: "", model: "mimo-v2.5", enabled: false, extra: { base_url: "https://freetokenfaucet.com/v1" } },
    nvidia: { key: "", model: "z-ai/glm-5.2", enabled: false, extra: { base_url: "https://integrate.api.nvidia.com/v1" } },
    openai: { key: "", model: "gpt-4o", enabled: false },
    groq: { key: "", model: "llama-3.3-70b", enabled: false },
    openrouter: { key: "", model: "openai/gpt-4o", enabled: false },
    minimax: { key: "", model: "MiniMaxAI/MiniMax-M2.7", enabled: false, extra: { base_url: "https://inference.dahl.global/v1" } },
    anthropic: { key: "", model: "claude-sonnet-4-20250514", enabled: false },
    azure: { key: "", model: "gpt-4o", enabled: false, extra: { endpoint: "" } },
    google: { key: "", model: "gemini-2.0-flash", enabled: false },
  });

  useEffect(() => {
    if (token) {
      fetchSettings();
      fetchApiConfig();
    }
  }, [token]);

  const fetchSettings = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/admin/settings`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        // Transform array to object — parse booleans and numbers
        const settingsObj: any = { ...settings };
        data.forEach((s: any) => {
          if (s.key in settingsObj && s.value !== null) {
            const raw = s.value;
            if (raw === "true") settingsObj[s.key] = true;
            else if (raw === "false") settingsObj[s.key] = false;
            else {
              const num = Number(raw);
              settingsObj[s.key] = !isNaN(num) && raw !== "" ? num : raw;
            }
          }
        });
        setSettings(settingsObj);
      }
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const fetchApiConfig = async () => {
    if (!token) return;
    try {
      const res = await fetch(`${API_URL}/api/admin/settings`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        const apiConfigObj: Record<string, {key: string, model: string, enabled: boolean, extra?: {endpoint?: string, base_url?: string}}> = { ...apiConfig };
        
        // Find AI provider settings
        const aiProvidersSetting = data.find((s: any) => s.key === "ai_providers_config");
        if (aiProvidersSetting) {
          try {
            const parsed = JSON.parse(aiProvidersSetting.value);
            Object.keys(parsed).forEach((providerId: string) => {
              if (providerId in apiConfigObj) {
                apiConfigObj[providerId] = { ...apiConfigObj[providerId], ...parsed[providerId] };
              }
            });
          } catch {
            // Keep default
          }
        }
        
        setApiConfig(apiConfigObj);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const saveSettings = async () => {
    if (!token) return;
    setSaving(true);
    setSaved(false);
    try {
      // Save each setting — all values must be strings (SettingsUpdate schema)
      const settingsToSave = [
        { key: "ai_generation_cost_lesson", value: String(settings.ai_generation_cost_lesson) },
        { key: "ai_generation_cost_quiz", value: String(settings.ai_generation_cost_quiz) },
        { key: "ai_generation_cost_homework", value: String(settings.ai_generation_cost_homework) },
        { key: "ai_generation_cost_plan", value: String(settings.ai_generation_cost_plan) },
        { key: "token_pack_100_price", value: String(settings.token_pack_100_price) },
        { key: "token_pack_500_price", value: String(settings.token_pack_500_price) },
        { key: "token_pack_1000_price", value: String(settings.token_pack_1000_price) },
        { key: "subscription_teacher_pro", value: String(settings.subscription_teacher_pro) },
        { key: "subscription_school", value: String(settings.subscription_school) },
        { key: "subscription_institution", value: String(settings.subscription_institution) },
        { key: "ai_providers_config", value: JSON.stringify(apiConfig) },
        { key: "maintenance_mode", value: String(settings.maintenance_mode) },
        { key: "allow_teacher_registration", value: String(settings.allow_teacher_registration) },
        { key: "allow_new_signups", value: String(settings.allow_new_signups) },
      ];

      for (const s of settingsToSave) {
        const res = await fetch(`${API_URL}/api/admin/settings`, {
          method: "PUT",
          headers: { 
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}` 
          },
          body: JSON.stringify(s),
        });
        if (!res.ok) {
          const errBody = await res.text();
          console.warn(`Failed to save ${s.key}: ${res.status} ${errBody}`);
        }
      }
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      console.error(err);
    }
    setSaving(false);
  };

  const testApiConnection = async (apiType: string) => {
    setTestConnection(apiType);
    setTestResult(null);
    try {
      const config = apiConfig[apiType];
      if (!config?.key) {
        setTestResult({ success: false, message: "Veuillez entrer une clé API" });
        setTestConnection(null);
        return;
      }
      const res = await fetch(`${API_URL}/api/admin/settings/test-provider`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ provider_id: apiType, key: config.key, model: config.model }),
      });
      const data = await res.json();
      setTestResult({ success: data.ok, message: data.ok ? data.message : data.error });
    } catch (err: any) {
      setTestResult({ success: false, message: err.message || "Erreur de connexion" });
    }
    setTestConnection(null);
  };

  const getActiveProvider = () => {
    const order = ["openai", "groq", "openrouter", "anthropic", "azure", "google"];
    for (const pid of order) {
      if (apiConfig[pid]?.enabled && apiConfig[pid]?.key) return pid;
    }
    return null;
  };

  const updateSetting = (key: keyof PlatformSettings, value: any) => {
    setSettings({ ...settings, [key]: value });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-3xl p-8 shadow-sm border border-black/5">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-[300] text-navy">
              Platform <span className="italic text-orange">Settings</span>
            </h1>
            <p className="text-gray mt-2">Configurez votre plateforme</p>
          </div>
          <button
            onClick={saveSettings}
            disabled={saving}
            className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-orange to-orange-l text-white rounded-xl font-medium disabled:opacity-50"
          >
            {saving ? <Loader2 className="w-5 h-5 animate-spin" /> : <Save className="w-5 h-5" />}
            {saving ? "Saving..." : "Save Changes"}
          </button>
        </div>
        {saved && (
          <div className="mt-4 p-3 bg-green-100 text-green-700 rounded-xl flex items-center gap-2">
            <CheckCircle className="w-5 h-5" />
            Settings saved successfully!
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-2xl shadow-sm border border-black/5 overflow-hidden">
        <div className="flex border-b">
          <button
            onClick={() => setActiveTab("economy")}
            className={`flex-1 px-6 py-4 text-sm font-medium ${
              activeTab === "economy" ? "text-orange border-b-2 border-orange" : "text-gray"
            }`}
          >
            Economy & Pricing
          </button>
          <button
            onClick={() => setActiveTab("system")}
            className={`flex-1 px-6 py-4 text-sm font-medium ${
              activeTab === "system" ? "text-orange border-b-2 border-orange" : "text-gray"
            }`}
          >
            System Config
          </button>
          <button
            onClick={() => setActiveTab("api")}
            className={`flex-1 px-6 py-4 text-sm font-medium ${
              activeTab === "api" ? "text-orange border-b-2 border-orange" : "text-gray"
            }`}
          >
            API Keys
          </button>
        </div>

        <div className="p-8">
          {activeTab === "economy" && (
            <div className="space-y-8">
              <div>
                <h3 className="text-lg font-semibold text-navy mb-4 flex items-center gap-2">
                  <Zap className="w-5 h-5 text-orange" />
                  AI Token Costs
                </h3>
                <div className="grid md:grid-cols-2 gap-4">
                  {[
                    { key: "ai_generation_cost_lesson", label: "Lesson Generation" },
                    { key: "ai_generation_cost_quiz", label: "Quiz Generation" },
                    { key: "ai_generation_cost_homework", label: "Homework Generation" },
                    { key: "ai_generation_cost_plan", label: "Learning Plan" },
                  ].map((field) => (
                    <div key={field.key} className="bg-cream-m p-4 rounded-xl">
                      <label className="block text-sm font-medium text-gray mb-2">{field.label}</label>
                      <div className="flex items-center gap-2">
                        <input
                          type="number"
                          value={settings[field.key as keyof PlatformSettings] as number}
                          onChange={(e) => updateSetting(field.key as keyof PlatformSettings, Number(e.target.value))}
                          className="flex-1 px-4 py-2 bg-white rounded-lg border"
                        />
                        <span className="text-gray">tokens</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-navy mb-4 flex items-center gap-2">
                  <DollarSign className="w-5 h-5 text-green-600" />
                  Token Pack Prices (DT)
                </h3>
                <div className="grid md:grid-cols-3 gap-4">
                  {[
                    { key: "token_pack_100_price", label: "100 Tokens" },
                    { key: "token_pack_500_price", label: "500 Tokens" },
                    { key: "token_pack_1000_price", label: "1000 Tokens" },
                  ].map((field) => (
                    <div key={field.key} className="bg-cream-m p-4 rounded-xl">
                      <label className="block text-sm font-medium text-gray mb-2">{field.label}</label>
                      <div className="flex items-center gap-2">
                        <input
                          type="number"
                          value={settings[field.key as keyof PlatformSettings] as number}
                          onChange={(e) => updateSetting(field.key as keyof PlatformSettings, Number(e.target.value))}
                          className="flex-1 px-4 py-2 bg-white rounded-lg border"
                        />
                        <span className="text-yellow-700 font-medium">DT</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-navy mb-4 flex items-center gap-2">
                  <Users className="w-5 h-5 text-purple-600" />
                  Subscriptions (DT/month)
                </h3>
                <div className="grid md:grid-cols-3 gap-4">
                  {[
                    { key: "subscription_teacher_pro", label: "Teacher Pro" },
                    { key: "subscription_school", label: "School" },
                    { key: "subscription_institution", label: "Institution" },
                  ].map((field) => (
                    <div key={field.key} className="bg-cream-m p-4 rounded-xl">
                      <label className="block text-sm font-medium text-gray mb-2">{field.label}</label>
                      <div className="flex items-center gap-2">
                        <input
                          type="number"
                          value={settings[field.key as keyof PlatformSettings] as number}
                          onChange={(e) => updateSetting(field.key as keyof PlatformSettings, Number(e.target.value))}
                          className="flex-1 px-4 py-2 bg-white rounded-lg border"
                        />
                        <span className="text-yellow-700 font-medium">DT</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === "system" && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-navy mb-4">Platform State</h3>
                <div className="space-y-4">
                  {[
                    { key: "maintenance_mode", label: "Maintenance Mode", desc: "When enabled, only admins can access" },
                    { key: "allow_teacher_registration", label: "Allow Teacher Registrations", desc: "Allow new teachers to register" },
                    { key: "allow_new_signups", label: "Allow New Signups", desc: "Allow new students to register" },
                  ].map((field) => (
                    <div key={field.key} className="flex items-center justify-between p-4 bg-cream-m rounded-xl">
                      <div>
                        <div className="font-medium">{field.label}</div>
                        <div className="text-sm text-gray">{field.desc}</div>
                      </div>
                      <button
                        onClick={() => updateSetting(field.key as keyof PlatformSettings, !settings[field.key as keyof PlatformSettings])}
                        className={`w-14 h-8 rounded-full transition-colors ${
                          settings[field.key as keyof PlatformSettings] ? "bg-green-500" : "bg-gray-300"
                        }`}
                      >
                        <div className={`w-6 h-6 bg-white rounded-full transition-transform ${
                          settings[field.key as keyof PlatformSettings] ? "translate-x-7" : "translate-x-1"
                        }`} />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === "api" && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-navy mb-4 flex items-center gap-2">
                  <Key className="w-5 h-5 text-orange" />
                  AI Providers & API Keys
                </h3>
                <p className="text-sm text-gray mb-6">
                  Configure your AI providers. At least one provider must be enabled with a valid API key.
                </p>
                
                <div className="space-y-4">
                  {AI_PROVIDERS.map((provider) => {
                    const config = apiConfig[provider.id];
                    const models = PROVIDER_MODELS[provider.id] || [];
                    
                    return (
                      <div key={provider.id} className={`bg-cream-m p-6 rounded-xl border-2 transition-colors ${
                        config.enabled ? "border-green-500" : "border-transparent"
                      }`}>
                        <div className="flex items-center justify-between mb-4">
                          <div className="flex items-center gap-3">
                            <span className="text-2xl">{provider.icon}</span>
                            <div>
                              <div className="font-semibold text-navy flex items-center gap-2">
                                {provider.name}
                                {config.enabled && config.key && getActiveProvider() === provider.id && (
                                  <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full font-medium">
                                    Actif
                                  </span>
                                )}
                              </div>
                              <div className="text-sm text-gray">
                                {models.length} models available
                              </div>
                            </div>
                          </div>
                          <button
                            onClick={() => setApiConfig({
                              ...apiConfig,
                              [provider.id]: { ...config, enabled: !config.enabled }
                            })}
                            className={`w-14 h-8 rounded-full transition-colors ${
                              config.enabled ? "bg-green-500" : "bg-gray-300"
                            }`}
                          >
                            <div className={`w-6 h-6 bg-white rounded-full transition-transform ${
                              config.enabled ? "translate-x-7" : "translate-x-1"
                            }`} />
                          </button>
                        </div>
                        
                        {config.enabled && (
                          <div className="space-y-4 mt-4 pt-4 border-t">
                            <div>
                              <label className="block text-sm font-medium text-gray mb-2">API Key</label>
                              <input
                                type="password"
                                value={config.key}
                                onChange={(e) => setApiConfig({
                                  ...apiConfig,
                                  [provider.id]: { ...config, key: e.target.value }
                                })}
                                className="w-full px-4 py-3 bg-white rounded-lg border"
                                placeholder={provider.id === "azure" ? "Azure API Key..." : "sk-..."}
                              />
                            </div>

                            {provider.id === "azure" && (
                              <div>
                                <label className="block text-sm font-medium text-gray mb-2">Azure Endpoint</label>
                                <input
                                  type="text"
                                  value={config.extra?.endpoint || ""}
                                  onChange={(e) => setApiConfig({
                                    ...apiConfig,
                                    [provider.id]: { ...config, extra: { ...config.extra, endpoint: e.target.value } }
                                  })}
                                  className="w-full px-4 py-3 bg-white rounded-lg border"
                                  placeholder="https://your-resource.openai.azure.com/"
                                />
                              </div>
                            )}

                            {provider.id === "minimax" && (
                              <div>
                                <label className="block text-sm font-medium text-gray mb-2">Base URL</label>
                                <input
                                  type="text"
                                  value={config.extra?.base_url || "https://inference.dahl.global/v1"}
                                  onChange={(e) => setApiConfig({
                                    ...apiConfig,
                                    [provider.id]: { ...config, extra: { ...config.extra, base_url: e.target.value } }
                                  })}
                                  className="w-full px-4 py-3 bg-white rounded-lg border"
                                  placeholder="https://inference.dahl.global/v1"
                                />
                              </div>
                            )}
                            
                            <div>
                              <label className="block text-sm font-medium text-gray mb-2">Default Model</label>
                              <div className="relative">
                                <select
                                  value={config.model}
                                  onChange={(e) => setApiConfig({
                                    ...apiConfig,
                                    [provider.id]: { ...config, model: e.target.value }
                                  })}
                                  className="w-full px-4 py-3 bg-white rounded-lg border appearance-none cursor-pointer"
                                >
                                  {models.map((model) => (
                                    <option key={model} value={model}>{model}</option>
                                  ))}
                                </select>
                                <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray pointer-events-none" />
                              </div>
                            </div>
                            
                            <button
                              onClick={() => testApiConnection(provider.id)}
                              disabled={testConnection !== null || !config.key}
                              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
                            >
                              {testConnection === provider.id ? (
                                <Loader2 className="w-4 h-4 animate-spin" />
                              ) : (
                                <TestTube className="w-4 h-4" />
                              )}
                              Test Connection
                            </button>
                          </div>
                        )}
                      </div>
                    );
                  })}
                  
                  {testResult && (
                    <div className={`p-4 rounded-xl ${
                      testResult.success ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
                    }`}>
                      {testResult.message}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}