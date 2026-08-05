import { Input } from "../../../../components/ui";

interface GeneralSettingsFormProps {
  platformName: string;
  supportEmail: string;
  allowSignups: boolean;
  onPlatformNameChange: (v: string) => void;
  onSupportEmailChange: (v: string) => void;
  onAllowSignupsChange: (v: boolean) => void;
}

export function GeneralSettingsForm({
  platformName, supportEmail, allowSignups,
  onPlatformNameChange, onSupportEmailChange, onAllowSignupsChange,
}: GeneralSettingsFormProps) {
  return (
    <div className="bg-white rounded-2xl shadow-sm border border-black/5 p-6 space-y-5">
      <h3 className="text-lg font-display font-semibold text-navy">General Settings</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <Input label="Platform Name" value={platformName} onChange={e => onPlatformNameChange(e.target.value)} />
        <Input label="Support Email" value={supportEmail} onChange={e => onSupportEmailChange(e.target.value)} />
      </div>
      <div className="flex items-center justify-between p-4 bg-cream-m rounded-xl">
        <div>
          <div className="font-medium text-navy text-sm">Allow New Registrations</div>
          <div className="text-xs text-gray mt-0.5">Enable or disable new user signups across the platform</div>
        </div>
        <button onClick={() => onAllowSignupsChange(!allowSignups)}
          className={`relative w-12 h-7 rounded-full transition-colors ${allowSignups ? "bg-green-500" : "bg-gray-300"}`}>
          <span className={`absolute top-1 w-5 h-5 bg-white rounded-full shadow transition-transform ${allowSignups ? "right-1" : "left-1"}`} />
        </button>
      </div>
    </div>
  );
}
