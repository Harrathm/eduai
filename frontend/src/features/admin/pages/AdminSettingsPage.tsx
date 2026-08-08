import { Save, RefreshCw, Globe, Coins, Gauge, Wrench, FileWarning, Bot } from "lucide-react";
import { PageSpinner, Button } from "../../../components/ui";
import { useAdminSettings, type TabId } from "../hooks/useAdminSettings";
import {
  GeneralSettingsForm, AIProviderTester, PricingForm,
  TokenLimitsForm, MaintenanceForm, ErrorLogsView,
} from "../components/settings";

const TABS: { id: TabId; label: string; icon: React.ReactNode }[] = [
  { id: "general", label: "General", icon: <Globe className="w-4 h-4" /> },
  { id: "api-keys", label: "AI Providers", icon: <Bot className="w-4 h-4" /> },
  { id: "pricing", label: "Pricing", icon: <Coins className="w-4 h-4" /> },
  { id: "token-limits", label: "Token Limits", icon: <Gauge className="w-4 h-4" /> },
  { id: "maintenance", label: "Maintenance", icon: <Wrench className="w-4 h-4" /> },
  { id: "logs", label: "Error Logs", icon: <FileWarning className="w-4 h-4" /> },
];

export default function AdminSettingsPage() {
  const s = useAdminSettings();

  if (s.loading) return <PageSpinner message="Chargement des paramètres..." />;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-display font-light text-navy">Settings <span className="italic text-orange">& Config</span></h1>
          <p className="text-gray text-sm mt-1">Platform configuration, API keys, pricing, and limits</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={s.loadSettings}>
            <RefreshCw className="w-5 h-5 text-gray" />
          </Button>
          <Button onClick={s.handleSaveAll} loading={s.saving}>
            <Save className="w-4 h-4" /> {s.saving ? "Saving..." : "Save All"}
          </Button>
        </div>
      </div>

      {/* Error */}
      {s.error && (
        <div className="flex items-center gap-3 px-4 py-3 bg-red-50 text-red-600 rounded-xl text-sm">
          {s.error}
          <Button variant="ghost" size="sm" onClick={() => {}}>&times;</Button>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 bg-white p-1.5 rounded-2xl shadow-sm border border-black/5 overflow-x-auto">
        {TABS.filter(t => s.isSuperAdmin || !["api-keys", "maintenance"].includes(t.id)).map(t => (
          <Button key={t.id} variant={s.tab === t.id ? "secondary" : "ghost"} onClick={() => s.setTab(t.id)}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all whitespace-nowrap">
            {t.icon} {t.label}
          </Button>
        ))}
      </div>

      {/* Tab Content */}
      {s.tab === "general" && (
        <GeneralSettingsForm
          platformName={s.platformName} supportEmail={s.supportEmail} allowSignups={s.allowSignups}
          onPlatformNameChange={s.setPlatformName} onSupportEmailChange={s.setSupportEmail} onAllowSignupsChange={s.setAllowSignups}
        />
      )}

      {s.tab === "api-keys" && (
        <AIProviderTester
          apiConfig={s.apiConfig} onToggleProvider={s.toggleApiProvider} onUpdateProvider={s.updateApiProvider}
          testConnection={s.testConnection} testResult={s.testResult} onTestConnection={s.testApiConnection}
          customModel={s.customModel} onCustomModelChange={s.setCustomModel}
          showCustomInput={s.showCustomInput} onShowCustomInputChange={s.setShowCustomInput}
          getActiveProvider={s.getActiveProvider}
          stripeKey={s.stripeKey} onStripeKeyChange={s.setStripeKey}
          showStripeKey={s.showStripeKey} onShowStripeKeyChange={s.setShowStripeKey}
          onCopy={(v) => { navigator.clipboard.writeText(v); s.showToast("Copied"); }}
        />
      )}

      {s.tab === "pricing" && (
        <PricingForm
          tokenPrices={s.tokenPrices} subscriptionPrices={s.subscriptionPrices}
          onTokenPricesChange={s.setTokenPrices} onSubscriptionPricesChange={s.setSubscriptionPrices}
        />
      )}

      {s.tab === "token-limits" && (
        <TokenLimitsForm tokenLimits={s.tokenLimits} onChange={s.setTokenLimits} />
      )}

      {s.tab === "maintenance" && (
        <MaintenanceForm
          maintenanceMode={s.maintenanceMode} maintenanceMessage={s.maintenanceMessage}
          onToggle={s.setMaintenanceMode} onMessageChange={s.setMaintenanceMessage}
        />
      )}

      {s.tab === "logs" && (
        <ErrorLogsView
          errorLogs={s.errorLogs} logsLoading={s.logsLoading}
          logSearch={s.logSearch} logLevelFilter={s.logLevelFilter}
          onLogSearchChange={s.setLogSearch} onLogLevelFilterChange={s.setLogLevelFilter}
          onRefresh={s.loadErrorLogs}
        />
      )}

      {/* Toast */}
      {s.toast.show && (
        <div className={`fixed top-6 right-6 z-50 flex items-center gap-3 px-6 py-4 rounded-xl shadow-lg ${s.toast.type === "success" ? "bg-green-500" : "bg-red-500"} text-white`}>
          <span className="font-medium">{s.toast.message}</span>
        </div>
      )}
    </div>
  );
}
