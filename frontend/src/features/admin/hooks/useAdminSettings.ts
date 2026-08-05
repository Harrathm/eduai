import { useState, useEffect, useCallback } from "react";
import { adminSettings, adminLogs } from "../../../api";
import type { TokenLimits, ErrorLogResponse } from "../../../api/adminApi";
import { useAuthStore } from "@/store/authStore";

export type TabId = "general" | "api-keys" | "pricing" | "token-limits" | "maintenance" | "logs";

export interface ApiProviderConfig {
  key: string;
  model: string;
  enabled: boolean;
  extra?: { endpoint?: string; base_url?: string };
}

interface Toast {
  show: boolean;
  message: string;
  type: "success" | "error";
}

const DEFAULT_API_CONFIG: Record<string, ApiProviderConfig> = {
  freetokenfaucet: { key: "", model: "mimo-v2.5", enabled: false, extra: { base_url: "https://freetokenfaucet.com/v1" } },
  nvidia: { key: "", model: "z-ai/glm-5.2", enabled: false, extra: { base_url: "https://integrate.api.nvidia.com/v1" } },
  openai: { key: "", model: "gpt-4o", enabled: false },
  groq: { key: "", model: "llama-3.3-70b-versatile", enabled: false },
  openrouter: { key: "", model: "openai/gpt-4o", enabled: false },
  minimax: { key: "", model: "MiniMaxAI/MiniMax-M2.7", enabled: false, extra: { base_url: "https://inference.dahl.global/v1" } },
  anthropic: { key: "", model: "claude-sonnet-4-20250514", enabled: false },
  azure: { key: "", model: "gpt-4o", enabled: false, extra: { endpoint: "" } },
  google: { key: "", model: "gemini-2.0-flash", enabled: false },
};

const DEFAULT_TOKEN_LIMITS: TokenLimits = {
  student_free: { monthly: 1000, daily: 100, per_request: 50 },
  student_premium: { monthly: 10000, daily: 500, per_request: 200 },
  teacher: { monthly: 50000, daily: 2000, per_request: 500 },
  admin: { monthly: 100000, daily: 5000, per_request: 1000 },
  super_admin: { monthly: 1000000, daily: 50000, per_request: 5000 },
};

export function useAdminSettings() {
  const { user } = useAuthStore();
  const isSuperAdmin = user?.role === "SUPER_ADMIN" || user?.role === "super_admin" || user?.is_super_admin;

  const [tab, setTab] = useState<TabId>("general");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<Toast>({ show: false, message: "", type: "success" });

  // General
  const [platformName, setPlatformName] = useState("EDUAI Platform");
  const [supportEmail, setSupportEmail] = useState("");
  const [allowSignups, setAllowSignups] = useState(true);

  // API Keys
  const [openaiKey, setOpenaiKey] = useState("");
  const [stripeKey, setStripeKey] = useState("");
  const [showOpenaiKey, setShowOpenaiKey] = useState(false);
  const [showStripeKey, setShowStripeKey] = useState(false);

  // AI Providers
  const [apiConfig, setApiConfig] = useState<Record<string, ApiProviderConfig>>(DEFAULT_API_CONFIG);
  const [testConnection, setTestConnection] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);
  const [customModel, setCustomModel] = useState<Record<string, string>>({});
  const [showCustomInput, setShowCustomInput] = useState<Record<string, boolean>>({});

  // Pricing
  const [tokenPrices, setTokenPrices] = useState({ pack_100: 5, pack_500: 20, pack_1000: 35 });
  const [subscriptionPrices, setSubscriptionPrices] = useState({ teacher_pro: 29.99, school: 99.99, institution: 299.99 });

  // Token limits
  const [tokenLimits, setTokenLimits] = useState<TokenLimits>(DEFAULT_TOKEN_LIMITS);

  // Maintenance
  const [maintenanceMode, setMaintenanceMode] = useState(false);
  const [maintenanceMessage, setMaintenanceMessage] = useState("Platform is under maintenance. Please check back later.");

  // Error Logs
  const [errorLogs, setErrorLogs] = useState<ErrorLogResponse | null>(null);
  const [logsLoading, setLogsLoading] = useState(false);
  const [logSearch, setLogSearch] = useState("");
  const [logLevelFilter, setLogLevelFilter] = useState("");

  const showToast = useCallback((message: string, type: "success" | "error" = "success") => {
    setToast({ show: true, message, type });
    setTimeout(() => setToast({ show: false, message: "", type: "success" }), 3000);
  }, []);

  const loadSettings = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const settings = await adminSettings.list();
      const kv: Record<string, string> = {};
      settings.forEach((s: any) => { kv[s.key] = s.value; });

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

      if (kv.token_pack_prices) { try { setTokenPrices(JSON.parse(kv.token_pack_prices)); } catch { /* ignore */ } }
      if (kv.subscription_prices) { try { setSubscriptionPrices(JSON.parse(kv.subscription_prices)); } catch { /* ignore */ } }
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

  const getActiveProvider = useCallback(() => {
    const order = ["nvidia", "freetokenfaucet", "openai", "groq", "openrouter", "minimax", "anthropic", "azure", "google"];
    for (const pid of order) {
      if (apiConfig[pid]?.enabled && apiConfig[pid]?.key) return pid;
    }
    return null;
  }, [apiConfig]);

  const testApiConnection = useCallback(async (providerId: string) => {
    setTestConnection(providerId);
    setTestResult(null);
    try {
      const config = apiConfig[providerId];
      if (!config?.key) {
        setTestResult({ success: false, message: "Veuillez entrer une clé API" });
        setTestConnection(null);
        return;
      }
      const data = await adminSettings.testProvider(providerId, config.key, config.model);
      setTestResult({ success: data.ok, message: data.ok ? data.message : data.error });
    } catch (err: any) {
      setTestResult({ success: false, message: err.message || "Erreur de connexion" });
    }
    setTestConnection(null);
  }, [apiConfig]);

  const handleSaveAll = useCallback(async () => {
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
  }, [platformName, supportEmail, allowSignups, openaiKey, stripeKey, tokenPrices, subscriptionPrices, maintenanceMode, maintenanceMessage, apiConfig, tokenLimits, showToast]);

  const updateApiProvider = useCallback((providerId: string, updates: Partial<ApiProviderConfig>) => {
    setApiConfig(prev => ({
      ...prev,
      [providerId]: { ...prev[providerId], ...updates },
    }));
  }, []);

  const toggleApiProvider = useCallback((providerId: string) => {
    setApiConfig(prev => ({
      ...prev,
      [providerId]: { ...prev[providerId], enabled: !prev[providerId].enabled },
    }));
  }, []);

  return {
    // Auth
    isSuperAdmin,
    // Tab
    tab, setTab,
    // Loading
    loading, saving, error, toast, showToast,
    // General
    platformName, setPlatformName,
    supportEmail, setSupportEmail,
    allowSignups, setAllowSignups,
    // API Keys
    openaiKey, setOpenaiKey,
    stripeKey, setStripeKey,
    showOpenaiKey, setShowOpenaiKey,
    showStripeKey, setShowStripeKey,
    // AI Providers
    apiConfig, updateApiProvider, toggleApiProvider,
    testConnection, testResult, testApiConnection,
    customModel, setCustomModel,
    showCustomInput, setShowCustomInput,
    getActiveProvider,
    // Pricing
    tokenPrices, setTokenPrices,
    subscriptionPrices, setSubscriptionPrices,
    // Token limits
    tokenLimits, setTokenLimits,
    // Maintenance
    maintenanceMode, setMaintenanceMode,
    maintenanceMessage, setMaintenanceMessage,
    // Error Logs
    errorLogs, logsLoading,
    logSearch, setLogSearch,
    logLevelFilter, setLogLevelFilter,
    loadErrorLogs,
    // Actions
    loadSettings, handleSaveAll,
  };
}
