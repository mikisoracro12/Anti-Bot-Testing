import { useMemo, useState } from "react";
import {
  Ban,
  Bot,
  CheckCircle2,
  RefreshCw,
  ShieldOff,
  Timer,
  Waves,
} from "lucide-react";
import { Link } from "react-router-dom";
import { fetchDashboard, getErrorMessage } from "../api/client";
import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { MetricCard } from "../components/MetricCard";
import { StatusBadge } from "../components/StatusBadge";
import { ActivityChart } from "../features/dashboard/ActivityChart";
import { useAsync } from "../hooks/useAsync";
import { formatDateTime, formatNumber, toLocalInputValue } from "../utils/format";

export function DashboardPage() {
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");

  const params = useMemo(
    () => ({
      start_time: start ? new Date(start).toISOString() : undefined,
      end_time: end ? new Date(end).toISOString() : undefined,
      bucket_minutes: 5,
    }),
    [start, end]
  );

  const { data, error, loading, reload } = useAsync(
    () => fetchDashboard(params).catch((e) => Promise.reject(new Error(getErrorMessage(e)))),
    [params.start_time, params.end_time]
  );

  const setLastHour = () => {
    const now = new Date();
    const hourAgo = new Date(now.getTime() - 60 * 60 * 1000);
    setStart(toLocalInputValue(hourAgo));
    setEnd(toLocalInputValue(now));
  };

  const clearRange = () => {
    setStart("");
    setEnd("");
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-50">Overview</h1>
          <p className="mt-1 text-sm text-slate-400">
            Live metrics from the BotShield Lab backend — no fabricated stats.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button type="button" className="btn-secondary" onClick={setLastHour}>
            Last hour
          </button>
          <button type="button" className="btn-secondary" onClick={clearRange}>
            All time
          </button>
          <button type="button" className="btn-primary" onClick={() => void reload()}>
            <RefreshCw className="h-4 w-4" aria-hidden />
            Refresh
          </button>
        </div>
      </div>

      <div className="panel grid gap-3 p-4 sm:grid-cols-2">
        <div>
          <label className="label" htmlFor="start">
            Start
          </label>
          <input
            id="start"
            type="datetime-local"
            className="input"
            value={start}
            onChange={(e) => setStart(e.target.value)}
          />
        </div>
        <div>
          <label className="label" htmlFor="end">
            End
          </label>
          <input
            id="end"
            type="datetime-local"
            className="input"
            value={end}
            onChange={(e) => setEnd(e.target.value)}
          />
        </div>
      </div>

      {loading && <LoadingState label="Loading dashboard metrics…" />}
      {error && <ErrorState message={error} onRetry={() => void reload()} />}

      {!loading && !error && data && (
        <>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            <MetricCard
              label="Total requests"
              value={formatNumber(data.summary.total_requests)}
              icon={Waves}
            />
            <MetricCard
              label="Allowed"
              value={formatNumber(data.summary.allowed_requests)}
              icon={CheckCircle2}
              accent="text-success"
            />
            <MetricCard
              label="Blocked"
              value={formatNumber(data.summary.blocked_requests)}
              icon={Ban}
              accent="text-danger"
            />
            <MetricCard
              label="Suspected bots"
              value={formatNumber(data.summary.suspected_bot_requests)}
              icon={Bot}
              accent="text-warning"
            />
            <MetricCard
              label="Rate-limit violations"
              value={formatNumber(data.summary.rate_limit_violations)}
              icon={Timer}
              accent="text-warning"
            />
            <MetricCard
              label="CAPTCHA failures"
              value={formatNumber(data.summary.captcha_failures)}
              icon={ShieldOff}
              accent="text-danger"
            />
          </div>

          <section className="panel p-5">
            <h2 className="mb-4 text-sm font-semibold text-slate-200">Request activity</h2>
            <ActivityChart data={data.activity} />
          </section>

          <div className="grid gap-4 lg:grid-cols-2">
            <section className="panel p-5">
              <h2 className="mb-4 text-sm font-semibold text-slate-200">Detection reasons</h2>
              {data.detection_reasons.length === 0 ? (
                <EmptyState
                  title="No detection reasons yet"
                  description="Behavioral rules will appear here after flagged traffic."
                />
              ) : (
                <ul className="space-y-2">
                  {data.detection_reasons.map((r) => (
                    <li
                      key={r.reason}
                      className="flex items-center justify-between rounded-lg bg-surface-850 px-3 py-2 text-sm"
                    >
                      <span className="font-mono text-slate-300">{r.reason}</span>
                      <span className="tabular-nums text-slate-400">{r.count}</span>
                    </li>
                  ))}
                </ul>
              )}
            </section>

            <section className="panel p-5">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-sm font-semibold text-slate-200">Recent events</h2>
                <Link to="/events" className="text-xs text-accent hover:underline">
                  View all
                </Link>
              </div>
              {data.recent_events.length === 0 ? (
                <EmptyState
                  title="No events recorded"
                  description="Use the simulator or demo form to generate traffic."
                  action={
                    <Link to="/simulator" className="btn-primary">
                      Open simulator
                    </Link>
                  }
                />
              ) : (
                <ul className="divide-y divide-white/5">
                  {data.recent_events.map((e) => (
                    <li key={e.id} className="flex items-start justify-between gap-3 py-3 text-sm">
                      <div className="min-w-0">
                        <p className="truncate font-mono text-xs text-slate-500">
                          {formatDateTime(e.timestamp)}
                        </p>
                        <p className="mt-0.5 truncate text-slate-300">
                          {e.http_method} {e.endpoint}
                        </p>
                      </div>
                      <div className="flex shrink-0 flex-col items-end gap-1">
                        <StatusBadge value={e.outcome} />
                        <span className="font-mono text-xs text-slate-500">
                          risk {e.risk_score}
                        </span>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </div>
        </>
      )}
    </div>
  );
}
