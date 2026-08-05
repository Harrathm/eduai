import { Eye, EyeOff, TestTube, Bot, Key, AlertCircle, ChevronDown } from "lucide-react";
import { Button, Input } from "../../../../components/ui";
import type { ApiProviderConfig } from "../../hooks/useAdminSettings";

const AI_PROVIDERS = [
  { id: "freetokenfaucet", name: "FreeTokenFaucet", icon: "🆓" },
  { id: "nvidia", name: "NVIDIA", icon: "🟢" },
  { id: "openai", name: "OpenAI", icon: "🤖" },
  { id: "groq", name: "Groq", icon: "⚡" },
  { id: "openrouter", name: "OpenRouter", icon: "🌐" },
  { id: "minimax", name: "MiniMax", icon: "🔮" },
  { id: "anthropic", name: "Anthropic", icon: "🧠" },
  { id: "azure", name: "Azure OpenAI", icon: "☁️" },
  { id: "google", name: "Google AI", icon: "🔵" },
] as const;

const PROVIDER_MODELS: Record<string, string[]> = {
  freetokenfaucet: ["mimo-v2.5"],
  nvidia: ["z-ai/glm-5.2", "meta/llama-3.1-8b-instruct", "meta/llama-3.1-70b-instruct", "meta/llama-3.1-405b-instruct", "mistralai/mistral-7b-instruct-v0.3", "google/gemma-2-9b-it"],
  openai: ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4"],
  groq: ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768", "gemma2-9b-it"],
  openrouter: [
    "openai/gpt-4o", "openai/gpt-4o-mini", "anthropic/claude-sonnet-4", "anthropic/claude-3.5-sonnet",
    "meta-llama/llama-3.3-70b-instruct", "google/gemini-2.0-flash-001", "mistralai/mistral-large-2411",
    "deepseek/deepseek-chat", "qwen/qwen-2.5-72b-instruct",
  ],
  minimax: ["MiniMaxAI/MiniMax-M2.7", "moonshotai/Kimi-K2.6", "GLM-5.2"],
  anthropic: ["claude-sonnet-4-20250514", "claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"],
  azure: ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
  google: ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"],
};

interface AIProviderTesterProps {
  apiConfig: Record<string, ApiProviderConfig>;
  onToggleProvider: (id: string) => void;
  onUpdateProvider: (id: string, updates: Partial<ApiProviderConfig>) => void;
  testConnection: string | null;
  testResult: { success: boolean; message: string } | null;
  onTestConnection: (id: string) => void;
  customModel: Record<string, string>;
  onCustomModelChange: (v: Record<string, string>) => void;
  showCustomInput: Record<string, boolean>;
  onShowCustomInputChange: (v: Record<string, boolean>) => void;
  getActiveProvider: () => string | null;
  stripeKey: string;
  onStripeKeyChange: (v: string) => void;
  showStripeKey: boolean;
  onShowStripeKeyChange: (v: boolean) => void;
  onCopy: (v: string) => void;
}

export function AIProviderTester({
  apiConfig, onToggleProvider, onUpdateProvider,
  testConnection, testResult, onTestConnection,
  customModel, onCustomModelChange,
  showCustomInput, onShowCustomInputChange,
  getActiveProvider, stripeKey, onStripeKeyChange,
  showStripeKey, onShowStripeKeyChange, onCopy,
}: AIProviderTesterProps) {
  const activeProvider = getActiveProvider();

  return (
    <div className="space-y-4">
      {/* Active Configuration Summary */}
      <div className={`rounded-2xl shadow-sm border p-6 ${
        activeProvider
          ? "bg-gradient-to-r from-green-50 to-emerald-50 border-green-200"
          : "bg-gradient-to-r from-red-50 to-orange-50 border-red-200"
      }`}>
        <h3 className="text-sm font-semibold text-navy mb-3 flex items-center gap-2">
          <Bot className="w-5 h-5" /> Configuration IA Active
        </h3>
        {activeProvider ? (
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-3">
              <span className="text-3xl">{AI_PROVIDERS.find(p => p.id === activeProvider)?.icon}</span>
              <div>
                <div className="text-lg font-bold text-navy">{AI_PROVIDERS.find(p => p.id === activeProvider)?.name}</div>
                <div className="text-sm text-gray">Fournisseur actif</div>
              </div>
            </div>
            <div className="h-12 w-px bg-green-300" />
            <div>
              <div className="text-xs text-gray uppercase tracking-wide">Modèle</div>
              <div className="text-lg font-mono font-bold text-navy">{apiConfig[activeProvider]?.model || "—"}</div>
            </div>
            <div className="h-12 w-px bg-green-300" />
            <div>
              <div className="text-xs text-gray uppercase tracking-wide">Clé API</div>
              <div className="text-sm font-mono text-green-700">
                {apiConfig[activeProvider]?.key?.substring(0, 8)}...{apiConfig[activeProvider]?.key?.slice(-4)}
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

      {/* Provider Cards */}
      <div className="bg-white rounded-2xl shadow-sm border border-black/5 p-6 space-y-5">
        <h3 className="text-lg font-display font-semibold text-navy flex items-center gap-2">
          <Bot className="w-5 h-5 text-orange" /> AI Providers & API Keys
        </h3>

        <div className="space-y-4">
          {AI_PROVIDERS.map((provider) => {
            const config = apiConfig[provider.id];
            const models = PROVIDER_MODELS[provider.id] || [];
            const isActive = config.enabled && config.key && activeProvider === provider.id;

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
                        {isActive && <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full font-medium">Actif</span>}
                      </div>
                      <div className="text-sm text-gray">{models.length} models available</div>
                    </div>
                  </div>
                  <button onClick={() => onToggleProvider(provider.id)}
                    className={`w-14 h-8 rounded-full transition-colors ${config.enabled ? "bg-green-500" : "bg-gray-300"}`}>
                    <div className={`w-6 h-6 bg-white rounded-full transition-transform ${config.enabled ? "translate-x-7" : "translate-x-1"}`} />
                  </button>
                </div>

                {config.enabled && (
                  <div className="space-y-4 mt-4 pt-4 border-t">
                    <Input label="API Key" type="password" value={config.key}
                      onChange={e => onUpdateProvider(provider.id, { key: e.target.value })} placeholder="sk-..." />

                    {provider.id === "azure" && (
                      <Input label="Azure Endpoint" value={config.extra?.endpoint || ""}
                        onChange={e => onUpdateProvider(provider.id, { extra: { ...config.extra, endpoint: e.target.value } })}
                        placeholder="https://your-resource.openai.azure.com/" />
                    )}

                    {provider.id === "minimax" && (
                      <Input label="Base URL" value={config.extra?.base_url || "https://inference.dahl.global/v1"}
                        onChange={e => onUpdateProvider(provider.id, { extra: { ...config.extra, base_url: e.target.value } })}
                        placeholder="https://inference.dahl.global/v1" />
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
                                    onShowCustomInputChange({ ...showCustomInput, [provider.id]: true });
                                  } else {
                                    onShowCustomInputChange({ ...showCustomInput, [provider.id]: false });
                                    onUpdateProvider(provider.id, { model: e.target.value });
                                  }
                                }}
                                className="w-full px-4 py-3 bg-white rounded-xl border border-black/5 text-sm appearance-none cursor-pointer focus:outline-none focus:ring-2 focus:ring-orange/20"
                              >
                                {isCustom && <option value="__custom_saved__">{config.model} (personnalisé)</option>}
                                {models.map((model) => <option key={model} value={model}>{model}</option>)}
                                <option value="__custom__">+ Modèle personnalisé...</option>
                              </select>
                            );
                          })()}
                          <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray pointer-events-none" />
                        </div>
                        {showCustomInput[provider.id] && (
                          <div className="flex gap-2">
                            <input type="text" value={customModel[provider.id] || ""}
                              onChange={(e) => onCustomModelChange({ ...customModel, [provider.id]: e.target.value })}
                              className="flex-1 px-4 py-3 bg-white rounded-xl border border-black/5 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-orange/20"
                              placeholder={provider.id === "openrouter" ? "vendor/model-name" : "model-name"}
                              onKeyDown={(e) => {
                                if (e.key === "Enter" && customModel[provider.id]?.trim()) {
                                  onUpdateProvider(provider.id, { model: customModel[provider.id].trim() });
                                  onShowCustomInputChange({ ...showCustomInput, [provider.id]: false });
                                }
                              }} />
                            <Button variant="success" size="sm" onClick={() => {
                              const val = customModel[provider.id]?.trim();
                              if (val) { onUpdateProvider(provider.id, { model: val }); onShowCustomInputChange({ ...showCustomInput, [provider.id]: false }); }
                            }}>OK</Button>
                            <Button variant="ghost" size="sm" onClick={() => onShowCustomInputChange({ ...showCustomInput, [provider.id]: false })}>Annuler</Button>
                          </div>
                        )}
                        {config.model && !showCustomInput[provider.id] && (
                          <p className="text-xs text-gray">Modèle actuel: <span className="font-mono text-navy">{config.model}</span></p>
                        )}
                      </div>
                    </div>

                    <Button variant="secondary" size="sm" onClick={() => onTestConnection(provider.id)}
                      disabled={testConnection !== null || !config.key}>
                      {testConnection === provider.id ? <span className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" /> : <TestTube className="w-4 h-4" />}
                      Test Connection
                    </Button>
                  </div>
                )}
              </div>
            );
          })}

          {testResult && (
            <div className={`p-4 rounded-xl text-sm ${testResult.success ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}`}>
              {testResult.message}
            </div>
          )}
        </div>

        {/* Stripe Key */}
        <div className="mt-6 pt-4 border-t">
          <h4 className="text-sm font-semibold text-navy mb-3 flex items-center gap-2"><Key className="w-4 h-4" /> Other Keys</h4>
          <div>
            <label className="block text-xs font-medium text-gray mb-1.5">Stripe Secret Key</label>
            <div className="flex gap-2">
              <div className="relative flex-1">
                <input type={showStripeKey ? "text" : "password"} value={stripeKey} onChange={e => onStripeKeyChange(e.target.value)}
                  placeholder="sk_live_..." className="w-full px-4 py-3 bg-white rounded-xl border border-black/5 text-sm focus:outline-none focus:ring-2 focus:ring-orange/20 font-mono" />
                <button onClick={() => onShowStripeKeyChange(!showStripeKey)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray hover:text-navy">
                  {showStripeKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              <Button variant="ghost" size="sm" onClick={() => onCopy(stripeKey)}>Copy</Button>
            </div>
            <p className="text-xs text-gray mt-1">Used for subscription payments and course purchases</p>
          </div>
        </div>
      </div>
    </div>
  );
}
