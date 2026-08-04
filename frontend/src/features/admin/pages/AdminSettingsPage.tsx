import { useState, useEffect, useCallback } from "react";
import { Save, RefreshCw, Eye, EyeOff, Check, AlertCircle, Loader2, Globe, Key, Coins, Gauge, Wrench, FileWarning, ChevronDown, TestTube, Bot, Sparkles } from "lucide-react";
import { adminSettings, adminLogs } from "../api";
import type { PlatformSettingItem, TokenLimits, ErrorLogResponse } from "../api";
import { useAuthStore } from "@/store/authStore";
import { tokenStorage } from "../../../utils/tokenStorage";

type TabId = "general" | "api-keys" | "pricing" | "token-limits" | "maintenance" | "logs";

const TABS: { id: TabId; label: string; icon: React.ReactNode }[] = [
  { id: "general", label: "General", icon: <Globe className="w-4 h-4" /> },
  { id: "api-keys", label: "AI Providers", icon: <Bot className="w-4 h-4" /> },
  { id: "pricing", label: "Pricing", icon: <Coins className="w-4 h-4" /> },
  { id: "token-limits", label: "Token Limits", icon: <Gauge className="w-4 h-4" /> },
  { id: "maintenance", label: "Maintenance", icon: <Wrench className="w-4 h-4" /> },
  { id: "logs", label: "Error Logs", icon: <FileWarning className="w-4 h-4" /> },
];

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

const PROVIDER_MODELS: Record<string, string[]> = {
  freetokenfaucet: ["mimo-v2.5"],
  nvidia: ["z-ai/glm-5.2", "meta/llama-3.1-8b-instruct", "meta/llama-3.1-70b-instruct", "meta/llama-3.1-405b-instruct", "mistralai/mistral-7b-instruct-v0.3", "google/gemma-2-9b-it"],
  openai: ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4"],
  groq: ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768", "gemma2-9b-it"],
  openrouter: [
    "openai/gpt-4o", "openai/gpt-4o-mini", "openai/gpt-4-turbo",
    "anthropic/claude-sonnet-4", "anthropic/claude-3.5-sonnet", "anthropic/claude-3-haiku",
    "meta-llama/llama-3.3-70b-instruct", "meta-llama/llama-3.1-8b-instruct",
    "google/gemini-2.0-flash-001", "google/gemini-1.5-pro",
    "mistralai/mistral-large-2411", "mistralai/mixtral-8x7b-instruct",
    "deepseek/deepseek-chat", "deepseek/deepseek-r1",
    "qwen/qwen-2.5-72b-instruct",
  ],
  minimax: [
    "MiniMaxAI/MiniMax-M2.7",
    "moonshotai/Kimi-K2.6",
    "GLM-5.2",
  ],
  anthropic: ["claude-sonnet-4-20250514", "claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"],
  azure: ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
  google: ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"],
};

const ROLE_LABELS: Record<string, string> = {
  student_free: "Student (Free)",
  student_premium: "Student (Premium)",
  teacher: "Teacher",
  admin: "Admin / School Admin",
  super_admin: "Super Admin",
};

export default function AdminSettingsPage() {
  const { user } = useAuthStore();
  const isSuperAdmin = user?.role === "SUPER_ADMIN" || user?.role === "super_admin" || user?.is_super_admin;
  const [tab, setTab] = useState<TabId>("general");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<{ show: boolean; message: string; type: "success" | "error" }>({ show: false, message: "", type: "success" });

  const showToast = (message: string, type: "success" | "error" = "success") => {
    setToast({ show: true, message, type });
    setTimeout(() => setToast({ show: false, message: "", type: "success" }), 3000);
  };

  // General settings
  const [platformName, setPlatformName] = useState("EDUAI Platform");
  const [supportEmail, setSupportEmail] = useState("");
  const [allowSignups, setAllowSignups] = useState(true);

  // API Keys
  const [openaiKey, setOpenaiKey] = useState("");
  const [stripeKey, setStripeKey] = useState("");
  const [showOpenaiKey, setShowOpenaiKey] = useState(false);
  const [showStripeKey, setShowStripeKey] = useState(false);

  // Multi-provider AI config
  const [apiConfig, setApiConfig] = useState<Record<string, {key: string, model: string, enabled: boolean, extra?: {endpoint?: string, base_url?: string}}>>({
    freetokenfaucet: { key: "", model: "mimo-v2.5", enabled: false, extra: { base_url: "https://freetokenfaucet.com/v1" } },
    nvidia: { key: "", model: "z-ai/glm-5.2", enabled: false, extra: { base_url: "https://integrate.api.nvidia.com/v1" } },
    openai: { key: "", model: "gpt-4o", enabled: false },
    groq: { key: "", model: "llama-3.3-70b-versatile", enabled: false },
    openrouter: { key: "", model: "openai/gpt-4o", enabled: false },
    minimax: { key: "", model: "MiniMaxAI/MiniMax-M2.7", enabled: false, extra: { base_url: "https://inference.dahl.global/v1" } },
    anthropic: { key: "", model: "claude-sonnet-4-20250514", enabled: false },
    azure: { key: "", model: "gpt-4o", enabled: false, extra: { endpoint: "" } },
    google: { key: "", model: "gemini-2.0-flash", enabled: false },
  });
  const [testConnection, setTestConnection] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<{success: boolean; message: string} | null>(null);
  const [customModel, setCustomModel] = useState<Record<string, string>>({});
  const [showCustomInput, setShowCustomInput] = useState<Record<string, boolean>>({});

  // Pricing
  const [tokenPrices, setTokenPrices] = useState({ pack_100: 5, pack_500: 20, pack_1000: 35 });
  const [subscriptionPrices, setSubscriptionPrices] = useState({ teacher_pro: 29.99, school: 99.99, institution: 299.99 });

  // Token limits
  const [tokenLimits, setTokenLimits] = useState<TokenLimits>({
    student_free: { monthly: 1000, daily: 100, per_request: 50 },
    student_premium: { monthly: 10000, daily: 500, per_request: 200 },
    teacher: { monthly: 50000, daily: 2000, per_request: 500 },
    admin: { monthly: 100000, daily: 5000, per_request: 1000 },
    super_admin: { monthly: 1000000, daily: 50000, per_request: 5000 },
  });

  // Maintenance
  const [maintenanceMode, setMaintenanceMode] = useState(false);
  const [maintenanceMessage, setMaintenanceMessage] = useState("Platform is under maintenance. Please check back later.");

  // Error Logs
  const [errorLogs, setErrorLogs] = useState<ErrorLogResponse | null>(null);
  const [logsLoading, setLogsLoading] = useState(false);
  const [logSearch, setLogSearch] = useState("");
  const [logLevelFilter, setLogLevelFilter] = useState("");

  const loadSettings = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const settings = await adminSettings.list();
      const kv: Record<string, string> = {};
      settings.forEach(s => { kv[s.key] = s.value; });

      if (kv.platform_name) setPlatformName(kv.platform_name);
      if (kv.support_email) setSupportEmail(kv.support_email);
      if (kv.allow_new_signups !== undefined) setAllowSignups(kv.allow_new_signups === "true");

      if (kv.openai_api_key) setOpenaiKey(kv.openai_api_key);
      if (kv.stripe_secret_key) setStripeKey(kv.stripe_secret_key);

      if (kv.ai_providers_config) {
        try {
          const parsed = JSON.parse(kv.ai_providers_config);
          setApiConfig(prev => {
            const next = { ...prev };
            Object.keys(parsed).forEach((pid: string) => {
              if (pid in next) next[pid] = { ...next[pid], ...parsed[pid] };
            });
            return next;
          });
        } catch { /* ignore */ }
      }

      if (kv.token_pack_prices) {
        try { setTokenPrices(JSON.parse(kv.token_pack_prices)); } catch { /* ignore */ }
      }
      if (kv.subscription_prices) {
        try { setSubscriptionPrices(JSON.parse(kv.subscription_prices)); } catch { /* ignore */ }
      }

      if (kv.maintenance_mode) setMaintenanceMode(kv.maintenance_mode === "true");
      if (kv.maintenance_message) setMaintenanceMessage(kv.maintenance_message);

      try {
        const limitsRes = await adminSettings.getTokenLimits();
        if (limitsRes?.limits) setTokenLimits(limitsRes.limits);
      } catch { /* use defaults */ }
    } catch (err: any) {
      setError(err.message || "Failed to load settings");
    }
    setLoading(false);
  }, []);

  useEffect(() => { loadSettings(); }, [loadSettings]);

  const loadErrorLogs = useCallback(async () => {
    setLogsLoading(true);
    try {
      const data = await adminLogs.errors({ lines: 200, search: logSearch || undefined, level: logLevelFilter || undefined });
      setErrorLogs(data);
    } catch (err: any) {
      setErrorLogs({ total_lines: 0, lines: [], file: "", truncated: false, error: err.message });
    }
    setLogsLoading(false);
  }, [logSearch, logLevelFilter]);

  useEffect(() => {
    if (tab === "logs") loadErrorLogs();
  }, [tab, loadErrorLogs]);

  const getActiveProvider = () => {
    const order = ["nvidia", "freetokenfaucet", "openai", "groq", "openrouter", "minimax", "anthropic", "azure", "google"];
    for (const pid of order) {
      if (apiConfig[pid]?.enabled && apiConfig[pid]?.key) return pid;
    }
    return null;
  };

  const testApiConnection = async (providerId: string) => {
    setTestConnection(providerId);
    setTestResult(null);
    try {
      const config = apiConfig[providerId];
      if (!config?.key) {
        setTestResult({ success: false, message: "Veuillez entrer une clé API" });
        setTestConnection(null);
        return;
      }
      const res = await fetch(`/api/admin/settings/test-provider`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${tokenStorage.getToken()}`,
        },
        body: JSON.stringify({ provider_id: providerId, key: config.key, model: config.model }),
      });
      const data = await res.json();
      setTestResult({ success: data.ok, message: data.ok ? data.message : data.error });
    } catch (err: any) {
      setTestResult({ success: false, message: err.message || "Erreur de connexion" });
    }
    setTestConnection(null);
  };

  const handleSaveAll = async () => {
    setSaving(true);
    setError(null);
    try {
      const payload: { key: string; value: string }[] = [
        { key: "platform_name", value: platformName },
        { key: "support_email", value: supportEmail },
        { key: "allow_new_signups", value: String(allowSignups) },
        { key: "openai_api_key", value: openaiKey },
        { key: "stripe_secret_key", value: stripeKey },
        { key: "token_pack_prices", value: JSON.stringify(tokenPrices) },
        { key: "subscription_prices", value: JSON.stringify(subscriptionPrices) },
        { key: "maintenance_mode", value: String(maintenanceMode) },
        { key: "maintenance_message", value: maintenanceMessage },
        { key: "ai_providers_config", value: JSON.stringify(apiConfig) },
      ];
      await adminSettings.apply(payload);
      await adminSettings.updateTokenLimits(tokenLimits);
      showToast("All settings saved and cache refreshed");
    } catch (err: any) {
      setError(err.message || "Failed to save settings");
      showToast(err.message || "Failed to save", "error");
    }
    setSaving(false);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 text-orange animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-display font-light text-navy">Settings <span className="italic text-orange">& Config</span></h1>
          <p className="text-gray text-sm mt-1">Platform configuration, API keys, pricing, and limits</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={loadSettings} className="p-2.5 bg-white rounded-xl shadow-sm border border-black/5 hover:bg-cream">
            <RefreshCw className="w-5 h-5 text-gray" />
          </button>
          <button onClick={handleSaveAll} disabled={saving}
            className="flex items-center gap-2 px-5 py-2.5 bg-orange text-white rounded-xl font-medium text-sm hover:bg-orange-w disabled:opacity-50 shadow-sm">
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            {saving ? "Saving..." : "Save All"}
          </button>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-3 px-4 py-3 bg-red-50 text-red-600 rounded-xl text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          {error}
          <button onClick={() => setError(null)} className="ml-auto text-red-400 hover:text-red-600">&times;</button>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 bg-white p-1.5 rounded-2xl shadow-sm border border-black/5 overflow-x-auto">
        {TABS.filter(t => isSuperAdmin || !["api-keys", "maintenance"].includes(t.id)).map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all whitespace-nowrap ${tab === t.id ? "bg-navy text-white shadow-sm" : "text-gray hover:bg-cream-m"}`}>
            {t.icon} {t.label}
          </button>
        ))}
      </div>

      {/* ─── General Tab ───────────────────────────────────── */}
      {tab === "general" && (
        <div className="bg-white rounded-2xl shadow-sm border border-black/5 p-6 space-y-5">
          <h3 className="text-lg font-display font-semibold text-navy">General Settings</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div>
              <label className="block text-xs font-medium text-gray mb-1.5">Platform Name</label>
              <input value={platformName} onChange={e => setPlatformName(e.target.value)}
                className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none focus:ring-2 focus:ring-orange/20" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray mb-1.5">Support Email</label>
              <input value={supportEmail} onChange={e => setSupportEmail(e.target.value)}
                className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none focus:ring-2 focus:ring-orange/20" />
            </div>
          </div>
          <div className="flex items-center justify-between p-4 bg-cream-m rounded-xl">
            <div>
              <div className="font-medium text-navy text-sm">Allow New Registrations</div>
              <div className="text-xs text-gray mt-0.5">Enable or disable new user signups across the platform</div>
            </div>
            <button onClick={() => setAllowSignups(!allowSignups)}
              className={`relative w-12 h-7 rounded-full transition-colors ${allowSignups ? "bg-green-500" : "bg-gray-300"}`}>
              <span className={`absolute top-1 w-5 h-5 bg-white rounded-full shadow transition-transform ${allowSignups ? "right-1" : "left-1"}`} />
            </button>
          </div>
        </div>
      )}

      {/* ─── API Keys Tab (Multi-Provider) ─────────────────── */}
      {tab === "api-keys" && (
        <div className="space-y-4">
          {/* Active Configuration Summary */}
          <div className={`rounded-2xl shadow-sm border p-6 ${
            getActiveProvider() 
              ? "bg-gradient-to-r from-green-50 to-emerald-50 border-green-200" 
              : "bg-gradient-to-r from-red-50 to-orange-50 border-red-200"
          }`}>
            <h3 className="text-sm font-semibold text-navy mb-3 flex items-center gap-2">
              <Bot className="w-5 h-5" />
              Configuration IA Active
            </h3>
            {getActiveProvider() ? (
              <div className="flex items-center gap-6">
                <div className="flex items-center gap-3">
                  <span className="text-3xl">{AI_PROVIDERS.find(p => p.id === getActiveProvider())?.icon}</span>
                  <div>
                    <div className="text-lg font-bold text-navy">
                      {AI_PROVIDERS.find(p => p.id === getActiveProvider())?.name}
                    </div>
                    <div className="text-sm text-gray">Fournisseur actif</div>
                  </div>
                </div>
                <div className="h-12 w-px bg-green-300" />
                <div>
                  <div className="text-xs text-gray uppercase tracking-wide">Modèle</div>
                  <div className="text-lg font-mono font-bold text-navy">
                    {apiConfig[getActiveProvider()!]?.model || "—"}
                  </div>
                </div>
                <div className="h-12 w-px bg-green-300" />
                <div>
                  <div className="text-xs text-gray uppercase tracking-wide">Clé API</div>
                  <div className="text-sm font-mono text-green-700">
                    {apiConfig[getActiveProvider()!]?.key?.substring(0, 8)}...{apiConfig[getActiveProvider()!]?.key?.slice(-4)}
                  </div>
                </div>
                <div className="h-12 w-px bg-green-300" />
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 bg-green-500 rounded-full animate-pulse" />
                  <span className="text-sm font-medium text-green-700">Connecté</span>
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-3">
                <AlertCircle className="w-6 h-6 text-red-500" />
                <div>
                  <div className="text-sm font-semibold text-red-700">Aucun fournisseur IA configuré</div>
                  <div className="text-xs text-red-500 mt-0.5">Activez un fournisseur et entrez une clé API ci-dessous</div>
                </div>
              </div>
            )}
          </div>

          <div className="bg-white rounded-2xl shadow-sm border border-black/5 p-6 space-y-5">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-display font-semibold text-navy flex items-center gap-2">
                  <Bot className="w-5 h-5 text-orange" />
                  AI Providers & API Keys
                </h3>
                <p className="text-xs text-gray mt-1">
                  Configure your AI providers. The first enabled provider with a key will be used.
                  {getActiveProvider() && (
                    <span className="ml-2 text-green-600 font-medium">
                      Active: {AI_PROVIDERS.find(p => p.id === getActiveProvider())?.name}
                    </span>
                  )}
                </p>
              </div>
            </div>

            <div className="space-y-4">
              {AI_PROVIDERS.map((provider) => {
                const config = apiConfig[provider.id];
                const models = PROVIDER_MODELS[provider.id] || [];
                const isActive = config.enabled && config.key && getActiveProvider() === provider.id;

                return (
                  <div key={provider.id} className={`bg-cream-m p-6 rounded-xl border-2 transition-colors ${
                    isActive ? "border-green-500" : config.enabled ? "border-blue-300" : "border-transparent"
                  }`}>
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <span className="text-2xl">{provider.icon}</span>
                        <div>
                          <div className="font-semibold text-navy flex items-center gap-2">
                            {provider.name}
                            {isActive && (
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
                          <label className="block text-xs font-medium text-gray mb-1.5">API Key</label>
                          <input
                            type="password"
                            value={config.key}
                            onChange={(e) => setApiConfig({
                              ...apiConfig,
                              [provider.id]: { ...config, key: e.target.value }
                            })}
                            className="w-full px-4 py-3 bg-white rounded-xl border border-black/5 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-orange/20"
                            placeholder="sk-..."
                          />
                        </div>

                        {provider.id === "azure" && (
                          <div>
                            <label className="block text-xs font-medium text-gray mb-1.5">Azure Endpoint</label>
                            <input
                              type="text"
                              value={config.extra?.endpoint || ""}
                              onChange={(e) => setApiConfig({
                                ...apiConfig,
                                [provider.id]: { ...config, extra: { ...config.extra, endpoint: e.target.value } }
                              })}
                              className="w-full px-4 py-3 bg-white rounded-xl border border-black/5 text-sm focus:outline-none focus:ring-2 focus:ring-orange/20"
                              placeholder="https://your-resource.openai.azure.com/"
                            />
                          </div>
                        )}

                        {provider.id === "minimax" && (
                          <div>
                            <label className="block text-xs font-medium text-gray mb-1.5">Base URL</label>
                            <input
                              type="text"
                              value={config.extra?.base_url || "https://inference.dahl.global/v1"}
                              onChange={(e) => setApiConfig({
                                ...apiConfig,
                                [provider.id]: { ...config, extra: { ...config.extra, base_url: e.target.value } }
                              })}
                              className="w-full px-4 py-3 bg-white rounded-xl border border-black/5 text-sm focus:outline-none focus:ring-2 focus:ring-orange/20"
                              placeholder="https://inference.dahl.global/v1"
                            />
                          </div>
                        )}

                        <div>
                          <label className="block text-xs font-medium text-gray mb-1.5">Modèle par défaut</label>
                          <div className="space-y-2">
                            <div className="relative">
                              {(() => {
                                const isCustom = config.model && !models.includes(config.model) && !showCustomInput[provider.id];
                                return (
                                  <select
                                    value={showCustomInput[provider.id] ? "__custom__" : isCustom ? "__custom_saved__" : config.model}
                                    onChange={(e) => {
                                      if (e.target.value === "__custom__") {
                                        setShowCustomInput({ ...showCustomInput, [provider.id]: true });
                                      } else {
                                        setShowCustomInput({ ...showCustomInput, [provider.id]: false });
                                        setApiConfig({
                                          ...apiConfig,
                                          [provider.id]: { ...config, model: e.target.value }
                                        });
                                      }
                                    }}
                                    className="w-full px-4 py-3 bg-white rounded-xl border border-black/5 text-sm appearance-none cursor-pointer focus:outline-none focus:ring-2 focus:ring-orange/20"
                                  >
                                    {isCustom && (
                                      <option value="__custom_saved__">{config.model} (personnalisé)</option>
                                    )}
                                    {models.map((model) => (
                                      <option key={model} value={model}>{model}</option>
                                    ))}
                                    <option value="__custom__">+ Modèle personnalisé...</option>
                                  </select>
                                );
                              })()}
                              <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray pointer-events-none" />
                            </div>
                            {showCustomInput[provider.id] && (
                              <div className="flex gap-2">
                                <input
                                  type="text"
                                  value={customModel[provider.id] || ""}
                                  onChange={(e) => setCustomModel({ ...customModel, [provider.id]: e.target.value })}
                                  className="flex-1 px-4 py-3 bg-white rounded-xl border border-black/5 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-orange/20"
                                  placeholder={provider.id === "openrouter" ? "vendor/model-name" : "model-name"}
                                  onKeyDown={(e) => {
                                    if (e.key === "Enter" && customModel[provider.id]?.trim()) {
                                      const val = customModel[provider.id].trim();
                                      setApiConfig({
                                        ...apiConfig,
                                        [provider.id]: { ...config, model: val }
                                      });
                                      setShowCustomInput({ ...showCustomInput, [provider.id]: false });
                                      showToast(`Modèle "${val}" défini`);
                                    }
                                  }}
                                />
                                <button
                                  onClick={() => {
                                    const val = customModel[provider.id]?.trim();
                                    if (val) {
                                      setApiConfig({
                                        ...apiConfig,
                                        [provider.id]: { ...config, model: val }
                                      });
                                      setShowCustomInput({ ...showCustomInput, [provider.id]: false });
                                      showToast(`Modèle "${val}" défini`);
                                    }
                                  }}
                                  className="px-4 py-2 bg-green-600 text-white rounded-xl text-sm hover:bg-green-700"
                                >
                                  OK
                                </button>
                                <button
                                  onClick={() => setShowCustomInput({ ...showCustomInput, [provider.id]: false })}
                                  className="px-3 py-2 bg-gray-200 text-gray-600 rounded-xl text-sm hover:bg-gray-300"
                                >
                                  Annuler
                                </button>
                              </div>
                            )}
                            {config.model && !showCustomInput[provider.id] && (
                              <p className="text-xs text-gray">
                                Modèle actuel: <span className="font-mono text-navy">{config.model}</span>
                              </p>
                            )}
                          </div>
                        </div>

                        <button
                          onClick={() => testApiConnection(provider.id)}
                          disabled={testConnection !== null || !config.key}
                          className="px-4 py-2 bg-blue-600 text-white rounded-xl text-sm hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
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
                <div className={`p-4 rounded-xl text-sm ${
                  testResult.success ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
                }`}>
                  {testResult.message}
                </div>
              )}
            </div>

            <div className="mt-6 pt-4 border-t">
              <h4 className="text-sm font-semibold text-navy mb-3 flex items-center gap-2">
                <Key className="w-4 h-4" />
                Other Keys
              </h4>
              <div>
                <label className="block text-xs font-medium text-gray mb-1.5">Stripe Secret Key</label>
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <input type={showStripeKey ? "text" : "password"} value={stripeKey} onChange={e => setStripeKey(e.target.value)}
                      placeholder="sk_live_..."
                      className="w-full px-4 py-3 bg-white rounded-xl border border-black/5 text-sm focus:outline-none focus:ring-2 focus:ring-orange/20 font-mono" />
                    <button onClick={() => setShowStripeKey(!showStripeKey)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray hover:text-navy">
                      {showStripeKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                  <button onClick={() => { navigator.clipboard.writeText(stripeKey); showToast("Copied"); }}
                    className="px-3 py-2 bg-cream-m rounded-xl text-xs text-gray hover:text-navy">Copy</button>
                </div>
                <p className="text-xs text-gray mt-1">Used for subscription payments and course purchases</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ─── Pricing Tab ────────────────────────────────────── */}
      {tab === "pricing" && (
        <div className="space-y-4">
          <div className="bg-white rounded-2xl shadow-sm border border-black/5 p-6 space-y-5">
            <h3 className="text-lg font-display font-semibold text-navy">Token Pack Prices</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {Object.entries(tokenPrices).map(([key, val]) => (
                <div key={key}>
                  <label className="block text-xs font-medium text-gray mb-1.5 capitalize">{key.replace("_", " ")} (DT)</label>
                  <input type="number" value={val} onChange={e => setTokenPrices({ ...tokenPrices, [key]: Number(e.target.value) })}
                    className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none focus:ring-2 focus:ring-orange/20" min={0} step={0.5} />
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-2xl shadow-sm border border-black/5 p-6 space-y-5">
            <h3 className="text-lg font-display font-semibold text-navy">Subscription Prices (DT/month)</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {Object.entries(subscriptionPrices).map(([key, val]) => (
                <div key={key}>
                  <label className="block text-xs font-medium text-gray mb-1.5 capitalize">{key.replace("_", " ")}</label>
                  <input type="number" value={val} onChange={e => setSubscriptionPrices({ ...subscriptionPrices, [key]: Number(e.target.value) })}
                    className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none focus:ring-2 focus:ring-orange/20" min={0} step={0.01} />
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ─── Token Limits Tab ──────────────────────────────── */}
      {tab === "token-limits" && (
        <div className="bg-white rounded-2xl shadow-sm border border-black/5 p-6 space-y-5">
          <h3 className="text-lg font-display font-semibold text-navy">Token Limits Per Role</h3>
          <p className="text-xs text-gray">Configure how many tokens each role can consume monthly, daily, and per request.</p>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-black/5">
                  <th className="text-start py-3 px-2 font-medium text-gray">Role</th>
                  <th className="text-center py-3 px-2 font-medium text-gray">Monthly</th>
                  <th className="text-center py-3 px-2 font-medium text-gray">Daily</th>
                  <th className="text-center py-3 px-2 font-medium text-gray">Per Request</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(tokenLimits).map(([role, limits]) => (
                  <tr key={role} className="border-b border-black/5 hover:bg-cream-m/50">
                    <td className="py-3 px-2 font-medium text-navy">{ROLE_LABELS[role] || role}</td>
                    <td className="py-3 px-2">
                      <input type="number" value={limits.monthly}
                        onChange={e => setTokenLimits({ ...tokenLimits, [role]: { ...limits, monthly: Number(e.target.value) } })}
                        className="w-full px-3 py-2 bg-cream-m rounded-lg border border-black/5 text-xs text-center focus:outline-none focus:ring-2 focus:ring-orange/20" min={0} />
                    </td>
                    <td className="py-3 px-2">
                      <input type="number" value={limits.daily}
                        onChange={e => setTokenLimits({ ...tokenLimits, [role]: { ...limits, daily: Number(e.target.value) } })}
                        className="w-full px-3 py-2 bg-cream-m rounded-lg border border-black/5 text-xs text-center focus:outline-none focus:ring-2 focus:ring-orange/20" min={0} />
                    </td>
                    <td className="py-3 px-2">
                      <input type="number" value={limits.per_request}
                        onChange={e => setTokenLimits({ ...tokenLimits, [role]: { ...limits, per_request: Number(e.target.value) } })}
                        className="w-full px-3 py-2 bg-cream-m rounded-lg border border-black/5 text-xs text-center focus:outline-none focus:ring-2 focus:ring-orange/20" min={0} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ─── Maintenance Tab ────────────────────────────────── */}
      {tab === "maintenance" && (
        <div className="space-y-4">
          <div className="bg-white rounded-2xl shadow-sm border border-black/5 p-6 space-y-5">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-display font-semibold text-navy">Maintenance Mode</h3>
                <p className="text-xs text-gray mt-1">When enabled, non-admin users will see a maintenance message instead of the platform</p>
              </div>
              <button onClick={() => setMaintenanceMode(!maintenanceMode)}
                className={`relative w-14 h-8 rounded-full transition-colors ${maintenanceMode ? "bg-red-500" : "bg-gray-300"}`}>
                <span className={`absolute top-1 w-6 h-6 bg-white rounded-full shadow transition-transform ${maintenanceMode ? "right-1" : "left-1"}`} />
              </button>
            </div>
            {maintenanceMode && (
              <>
                <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4 text-sm text-yellow-800 flex items-center gap-3">
                  <AlertCircle className="w-5 h-5 flex-shrink-0" />
                  Maintenance mode is active. All non-admin traffic will be blocked.
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray mb-1.5">Maintenance Message</label>
                  <textarea value={maintenanceMessage} onChange={e => setMaintenanceMessage(e.target.value)}
                    className="w-full h-24 px-4 py-3 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none focus:ring-2 focus:ring-orange/20 resize-none" />
                  <p className="text-xs text-gray mt-1">This message will be shown to users when maintenance mode is enabled</p>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* ─── Error Logs Tab ─────────────────────────────────── */}
      {tab === "logs" && (
        <div className="space-y-4">
          <div className="bg-white rounded-2xl shadow-sm border border-black/5 p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-display font-semibold text-navy">Backend Error Logs</h3>
                <p className="text-xs text-gray mt-1">{errorLogs ? `${errorLogs.total_lines} log entries` : "Loading..."}</p>
              </div>
              <button onClick={loadErrorLogs} disabled={logsLoading}
                className="flex items-center gap-2 px-4 py-2 bg-cream-m rounded-xl text-sm font-medium hover:bg-cream">
                <RefreshCw className={`w-4 h-4 ${logsLoading ? "animate-spin" : ""}`} /> Refresh
              </button>
            </div>

            <div className="flex gap-3">
              <input value={logSearch} onChange={e => setLogSearch(e.target.value)} placeholder="Search logs..."
                className="flex-1 px-4 py-2.5 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none focus:ring-2 focus:ring-orange/20" />
              <select value={logLevelFilter} onChange={e => setLogLevelFilter(e.target.value)}
                className="px-4 py-2.5 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none">
                <option value="">All Levels</option>
                <option value="ERROR">ERROR</option>
                <option value="WARNING">WARNING</option>
                <option value="INFO">INFO</option>
              </select>
            </div>

            {logsLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-6 h-6 text-orange animate-spin" />
              </div>
            ) : errorLogs ? (
              <>
                {errorLogs.error && (
                  <div className="px-4 py-3 bg-yellow-50 text-yellow-700 rounded-xl text-sm">{errorLogs.error}</div>
                )}
                {errorLogs.truncated && (
                  <div className="text-xs text-gray">Showing last 200 lines. Use search to narrow results.</div>
                )}
                <div className="bg-navy text-green-300 rounded-xl p-4 max-h-[60vh] overflow-y-auto text-xs font-mono leading-relaxed">
                  {errorLogs.lines.length === 0 ? (
                    <span className="text-gray">No log entries found.</span>
                  ) : (
                    errorLogs.lines.map((line, i) => (
                      <div key={i} className={`hover:bg-white/5 px-2 py-0.5 ${line.includes("ERROR") ? "text-red-300" : line.includes("WARNING") ? "text-yellow-300" : ""}`}>
                        {line}
                      </div>
                    ))
                  )}
                </div>
              </>
            ) : null}
          </div>
        </div>
      )}

      {toast.show && (
        <div className={`fixed top-6 right-6 z-50 flex items-center gap-3 px-6 py-4 rounded-xl shadow-lg ${toast.type === "success" ? "bg-green-500" : "bg-red-500"} text-white`}>
          <span className="font-medium">{toast.message}</span>
        </div>
      )}
    </div>
  );
}
