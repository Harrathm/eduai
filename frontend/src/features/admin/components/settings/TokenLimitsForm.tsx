import type { TokenLimits } from "../../../api/adminApi";

const ROLE_LABELS: Record<string, string> = {
  student_free: "Student (Free)",
  student_premium: "Student (Premium)",
  teacher: "Teacher",
  admin: "Admin / School Admin",
  super_admin: "Super Admin",
};

interface TokenLimitsFormProps {
  tokenLimits: TokenLimits;
  onChange: (v: TokenLimits) => void;
}

export function TokenLimitsForm({ tokenLimits, onChange }: TokenLimitsFormProps) {
  return (
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
                {(["monthly", "daily", "per_request"] as const).map((field) => (
                  <td key={field} className="py-3 px-2">
                    <input type="number" value={limits[field]}
                      onChange={e => onChange({ ...tokenLimits, [role]: { ...limits, [field]: Number(e.target.value) } })}
                      className="w-full px-3 py-2 bg-cream-m rounded-lg border border-black/5 text-xs text-center focus:outline-none focus:ring-2 focus:ring-orange/20" min={0} />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
