import { useState } from "react";
import { RefreshCw } from "lucide-react";
import { fetchEvents, getErrorMessage } from "../api/client";
import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { StatusBadge } from "../components/StatusBadge";
import { useAsync } from "../hooks/useAsync";
import type { RequestEvent } from "../types/api";
import { formatDateTime } from "../utils/format";

export function EventsPage() {
  const [page, setPage] = useState(1);
  const [outcome, setOutcome] = useState("");
  const [classification, setClassification] = useState("");
  const [reason, setReason] = useState("");
  const [selected, setSelected] = useState<RequestEvent | null>(null);

  const { data, error, loading, reload } = useAsync(
    () =>
      fetchEvents({
        page,
        page_size: 15,
        outcome: outcome || undefined,
        classification: classification || undefined,
        detection_reason: reason || undefined,
      }).catch((e) => Promise.reject(new Error(getErrorMessage(e)))),
    [page, outcome, classification, reason]
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-50">Request events</h1>
          <p className="mt-1 text-sm text-slate-400">
            Sanitized history with filters, pagination, and detection details.
          </p>
        </div>
        <button type="button" className="btn-primary" onClick={() => void reload()}>
          <RefreshCw className="h-4 w-4" />
          Refresh
        </button>
      </div>

      <div className="panel grid gap-3 p-4 md:grid-cols-3">
        <div>
          <label className="label" htmlFor="outcome">
            Status
          </label>
          <select
            id="outcome"
            className="input"
            value={outcome}
            onChange={(e) => {
              setPage(1);
              setOutcome(e.target.value);
            }}
          >
            <option value="">All</option>
            <option value="allowed">Allowed</option>
            <option value="rate_limited">Rate limited</option>
            <option value="captcha_failed">CAPTCHA failed</option>
            <option value="captcha_required">CAPTCHA required</option>
            <option value="blocked">Blocked</option>
          </select>
        </div>
        <div>
          <label className="label" htmlFor="classification">
            Classification
          </label>
          <select
            id="classification"
            className="input"
            value={classification}
            onChange={(e) => {
              setPage(1);
              setClassification(e.target.value);
            }}
          >
            <option value="">All</option>
            <option value="normal">Normal</option>
            <option value="suspicious">Suspicious</option>
            <option value="high_risk">High risk</option>
          </select>
        </div>
        <div>
          <label className="label" htmlFor="reason">
            Detection reason
          </label>
          <select
            id="reason"
            className="input"
            value={reason}
            onChange={(e) => {
              setPage(1);
              setReason(e.target.value);
            }}
          >
            <option value="">All</option>
            <option value="request_frequency">request_frequency</option>
            <option value="repeated_endpoint">repeated_endpoint</option>
            <option value="missing_user_agent">missing_user_agent</option>
            <option value="unusual_user_agent">unusual_user_agent</option>
            <option value="suspicious_pattern">suspicious_pattern</option>
            <option value="rate_limit">rate_limit</option>
          </select>
        </div>
      </div>

      {loading && <LoadingState />}
      {error && <ErrorState message={error} onRetry={() => void reload()} />}

      {!loading && !error && data && (
        <div className="grid gap-4 xl:grid-cols-3">
          <div className="panel overflow-hidden xl:col-span-2">
            {data.items.length === 0 ? (
              <EmptyState
                title="No matching events"
                description="Adjust filters or generate traffic with the simulator."
              />
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full text-left text-sm">
                  <thead className="border-b border-white/5 bg-surface-850 text-xs uppercase tracking-wide text-slate-500">
                    <tr>
                      <th className="px-4 py-3 font-medium">Time</th>
                      <th className="px-4 py-3 font-medium">Endpoint</th>
                      <th className="px-4 py-3 font-medium">Outcome</th>
                      <th className="px-4 py-3 font-medium">Risk</th>
                      <th className="px-4 py-3 font-medium">Class</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {data.items.map((e) => (
                      <tr
                        key={e.id}
                        className={`cursor-pointer hover:bg-surface-850/80 ${
                          selected?.id === e.id ? "bg-accent-soft" : ""
                        }`}
                        onClick={() => setSelected(e)}
                      >
                        <td className="whitespace-nowrap px-4 py-3 font-mono text-xs text-slate-400">
                          {formatDateTime(e.timestamp)}
                        </td>
                        <td className="px-4 py-3 text-slate-200">{e.endpoint}</td>
                        <td className="px-4 py-3">
                          <StatusBadge value={e.outcome} />
                        </td>
                        <td className="px-4 py-3 font-mono tabular-nums">{e.risk_score}</td>
                        <td className="px-4 py-3">
                          <StatusBadge value={e.classification} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <div className="flex items-center justify-between border-t border-white/5 px-4 py-3 text-sm text-slate-400">
              <span>
                {data.total} total · page {data.page}
                {data.pages ? ` of ${data.pages}` : ""}
              </span>
              <div className="flex gap-2">
                <button
                  type="button"
                  className="btn-secondary"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                >
                  Previous
                </button>
                <button
                  type="button"
                  className="btn-secondary"
                  disabled={!data.pages || page >= data.pages}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Next
                </button>
              </div>
            </div>
          </div>

          <aside className="panel p-5">
            <h2 className="text-sm font-semibold text-slate-200">Detection details</h2>
            {!selected ? (
              <p className="mt-4 text-sm text-slate-500">Select an event to inspect reasons.</p>
            ) : (
              <div className="mt-4 space-y-3 text-sm">
                <div>
                  <p className="label">Event ID</p>
                  <p className="break-all font-mono text-xs text-slate-300">{selected.id}</p>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <p className="label">Outcome</p>
                    <StatusBadge value={selected.outcome} />
                  </div>
                  <div>
                    <p className="label">CAPTCHA</p>
                    <StatusBadge value={selected.captcha_status} />
                  </div>
                </div>
                <div>
                  <p className="label">Client ID (hashed)</p>
                  <p className="font-mono text-slate-300">{selected.client_id}</p>
                </div>
                <div>
                  <p className="label">Reasons</p>
                  {selected.detection_reasons.length === 0 ? (
                    <p className="text-slate-500">None triggered</p>
                  ) : (
                    <ul className="space-y-2">
                      {selected.detection_reasons.map((r, i) => (
                        <li key={`${r.rule}-${i}`} className="rounded-lg bg-surface-850 p-3">
                          <div className="flex justify-between gap-2">
                            <span className="font-mono text-accent">{r.rule}</span>
                            <span className="font-mono text-xs text-slate-400">+{r.score}</span>
                          </div>
                          <p className="mt-1 text-xs leading-relaxed text-slate-400">
                            {r.explanation}
                          </p>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            )}
          </aside>
        </div>
      )}
    </div>
  );
}
