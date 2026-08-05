import { Input } from "../../../../components/ui";

interface PricingFormProps {
  tokenPrices: Record<string, number>;
  subscriptionPrices: Record<string, number>;
  onTokenPricesChange: (v: Record<string, number>) => void;
  onSubscriptionPricesChange: (v: Record<string, number>) => void;
}

export function PricingForm({ tokenPrices, subscriptionPrices, onTokenPricesChange, onSubscriptionPricesChange }: PricingFormProps) {
  return (
    <div className="space-y-4">
      <div className="bg-white rounded-2xl shadow-sm border border-black/5 p-6 space-y-5">
        <h3 className="text-lg font-display font-semibold text-navy">Token Pack Prices</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {Object.entries(tokenPrices).map(([key, val]) => (
            <Input key={key} label={`${key.replace("_", " ")} (DT)`} type="number" value={val}
              onChange={e => onTokenPricesChange({ ...tokenPrices, [key]: Number(e.target.value) })} min={0} step={0.5} />
          ))}
        </div>
      </div>
      <div className="bg-white rounded-2xl shadow-sm border border-black/5 p-6 space-y-5">
        <h3 className="text-lg font-display font-semibold text-navy">Subscription Prices (DT/month)</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {Object.entries(subscriptionPrices).map(([key, val]) => (
            <Input key={key} label={key.replace("_", " ")} type="number" value={val}
              onChange={e => onSubscriptionPricesChange({ ...subscriptionPrices, [key]: Number(e.target.value) })} min={0} step={0.01} />
          ))}
        </div>
      </div>
    </div>
  );
}
