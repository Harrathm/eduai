import { AlertCircle } from "lucide-react";
import { Button } from "../../../../components/ui";

interface MaintenanceFormProps {
  maintenanceMode: boolean;
  maintenanceMessage: string;
  onToggle: (v: boolean) => void;
  onMessageChange: (v: string) => void;
}

export function MaintenanceForm({ maintenanceMode, maintenanceMessage, onToggle, onMessageChange }: MaintenanceFormProps) {
  return (
    <div className="bg-white rounded-2xl shadow-sm border border-black/5 p-6 space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-display font-semibold text-navy">Maintenance Mode</h3>
          <p className="text-xs text-gray mt-1">When enabled, non-admin users will see a maintenance message instead of the platform</p>
        </div>
        <Button onClick={() => onToggle(!maintenanceMode)}
          className={`relative w-14 h-8 rounded-full transition-colors ${maintenanceMode ? "bg-red-500" : "bg-gray-300"}`}>
          <span className={`absolute top-1 w-6 h-6 bg-white rounded-full shadow transition-transform ${maintenanceMode ? "right-1" : "left-1"}`} />
        </Button>
      </div>
      {maintenanceMode && (
        <>
          <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4 text-sm text-yellow-800 flex items-center gap-3">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            Maintenance mode is active. All non-admin traffic will be blocked.
          </div>
          <div>
            <label className="block text-xs font-medium text-gray mb-1.5">Maintenance Message</label>
            <textarea value={maintenanceMessage} onChange={e => onMessageChange(e.target.value)}
              className="w-full h-24 px-4 py-3 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none focus:ring-2 focus:ring-orange/20 resize-none" />
            <p className="text-xs text-gray mt-1">This message will be shown to users when maintenance mode is enabled</p>
          </div>
        </>
      )}
    </div>
  );
}
