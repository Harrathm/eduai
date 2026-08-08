import { RefreshCw } from "lucide-react";
import { Button, Input, Spinner } from "../../../../components/ui";
import type { ErrorLogResponse } from "../../../api/adminApi";

interface ErrorLogsViewProps {
  errorLogs: ErrorLogResponse | null;
  logsLoading: boolean;
  logSearch: string;
  logLevelFilter: string;
  onLogSearchChange: (v: string) => void;
  onLogLevelFilterChange: (v: string) => void;
  onRefresh: () => void;
}

export function ErrorLogsView({
  errorLogs, logsLoading, logSearch, logLevelFilter,
  onLogSearchChange, onLogLevelFilterChange, onRefresh,
}: ErrorLogsViewProps) {
  return (
    <div className="bg-white rounded-2xl shadow-sm border border-black/5 p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-display font-semibold text-navy">Backend Error Logs</h3>
          <p className="text-xs text-gray mt-1">{errorLogs ? `${errorLogs.total_lines} log entries` : <Spinner />}</p>
        </div>
        <Button variant="ghost" size="sm" onClick={onRefresh} loading={logsLoading}>
          <RefreshCw className={`w-4 h-4 ${logsLoading ? "animate-spin" : ""}`} /> Refresh
        </Button>
      </div>

      <div className="flex gap-3">
        <Input value={logSearch} onChange={e => onLogSearchChange(e.target.value)} placeholder="Search logs..." className="flex-1" />
        <select value={logLevelFilter} onChange={e => onLogLevelFilterChange(e.target.value)}
          className="px-4 py-2.5 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none">
          <option value="">All Levels</option>
          <option value="ERROR">ERROR</option>
          <option value="WARNING">WARNING</option>
          <option value="INFO">INFO</option>
        </select>
      </div>

      {logsLoading ? (
        <div className="flex items-center justify-center py-12">
          <Spinner size="lg" className="text-orange" />
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
  );
}
