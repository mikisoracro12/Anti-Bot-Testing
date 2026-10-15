import { useState } from "react";
import {
  cancelSimulation,
  fetchSimulationLimits,
  getErrorMessage,
  runSimulation,
} from "../api/client";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { StatusBadge } from "../components/StatusBadge";
import { useAsync } from "../hooks/useAsync";
import type { SimulationResponse } from "../types/api";

export function SimulatorPage() {
  const { data: limits, error, loading, reload } = useAsync(
    () =>
      fetchSimulationLimits().catch((e) => Promise.reject(new Error(getErrorMessage(e)))),
    []
  );

  const [mode, setMode] = useState<"normal" | "burst" | "repeat">("normal");
  const [count, setCount] = useState(10);
  const [intervalMs, setIntervalMs] = useState(200);
  const [endpoint, setEndpoint] = useState<"demo" | "health">("demo");
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<SimulationResponse | null>(null);
  const [runError, setRunError] = useState<string | null>(null);

  const onRun = async () => {
    setRunning(true);
    setRunError(null);
    setResult(null);
    try {
      const res = await runSimulation({
        mode,
        request_count: count,
        interval_ms: intervalMs,
        endpoint,
      });
      setResult(res);
    } catch (err) {
      setRunError(getErrorMessage(err));
    } finally {
      setRunning(false);
    }
  };

  const onCancel = async () => {
    try {
      await cancelSimulation();
    } catch (err) {
      setRunError(getErrorMessage(err));
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-50">Traffic simulator</h1>
        <p className="mt-1 text-sm text-slate-400">
          Controlled local traffic only — demonstrates defensive controls. No arbitrary URLs,
          proxies, or CAPTCHA bypass.
        </p>
      </div>

      {loading && <LoadingState />}
      {error && <ErrorState message={error} onRetry={() => void reload()} />}

      {limits && (
        <>
          <div className="rounded-xl border border-accent/20 bg-accent-soft p-4 text-sm text-slate-300">
            Max {limits.max_requests} requests · min interval {limits.min_interval_ms}ms · hosts:{" "}
            {limits.allowed_hosts.join(", ")}
          </div>

          <section className="panel grid gap-4 p-5 md:grid-cols-2">
            <div>
              <label className="label" htmlFor="mode">
                Mode
              </label>
              <select
                id="mode"
                className="input"
                value={mode}
                onChange={(e) => setMode(e.target.value as typeof mode)}
              >
                <option value="normal">Normal</option>
                <option value="burst">Burst</option>
                <option value="repeat">Repeat (library User-Agent)</option>
              </select>
            </div>
            <div>
              <label className="label" htmlFor="endpoint">
                Endpoint
              </label>
              <select
                id="endpoint"
                className="input"
                value={endpoint}
                onChange={(e) => setEndpoint(e.target.value as typeof endpoint)}
              >
                <option value="demo">Protected demo</option>
                <option value="health">Health</option>
              </select>
            </div>
            <div>
              <label className="label" htmlFor="count">
                Request count (max {limits.max_requests})
              </label>
              <input
                id="count"
                type="number"
                className="input"
                min={1}
                max={limits.max_requests}
                value={count}
                onChange={(e) =>
                  setCount(
                    Math.min(
                      limits.max_requests,
                      Math.max(1, Number(e.target.value) || 1)
                    )
                  )
                }
              />
            </div>
            <div>
              <label className="label" htmlFor="interval">
                Interval ms (min {limits.min_interval_ms})
              </label>
              <input
                id="interval"
                type="number"
                className="input"
                min={limits.min_interval_ms}
                value={intervalMs}
                onChange={(e) =>
                  setIntervalMs(
                    Math.max(limits.min_interval_ms, Number(e.target.value) || limits.min_interval_ms)
                  )
                }
              />
            </div>
            <div className="flex flex-wrap gap-2 md:col-span-2">
              <button
                type="button"
                className="btn-primary"
                disabled={running}
                onClick={() => void onRun()}
              >
                {running ? "Running…" : "Start simulation"}
              </button>
              <button
                type="button"
                className="btn-danger"
                disabled={!running}
                onClick={() => void onCancel()}
              >
                Cancel
              </button>
            </div>
          </section>

          <section className="panel p-5">
            <h2 className="mb-2 text-sm font-semibold text-slate-200">Safety notes</h2>
            <ul className="list-disc space-y-1 pl-5 text-sm text-slate-400">
              {limits.notes.map((n) => (
                <li key={n}>{n}</li>
              ))}
            </ul>
          </section>

          {runError && <ErrorState message={runError} />}

          {result && (
            <section className="panel p-5">
              <h2 className="text-sm font-semibold text-slate-200">Results</h2>
              <p className="mt-1 text-sm text-slate-400">{result.message}</p>
              <div className="mt-4 grid gap-3 sm:grid-cols-4">
                <div className="rounded-lg bg-surface-850 p-3">
                  <p className="text-xs text-slate-500">Total</p>
                  <p className="font-mono text-xl">{result.total}</p>
                </div>
                <div className="rounded-lg bg-surface-850 p-3">
                  <p className="text-xs text-slate-500">Successful</p>
                  <p className="font-mono text-xl text-success">{result.successful}</p>
                </div>
                <div className="rounded-lg bg-surface-850 p-3">
                  <p className="text-xs text-slate-500">Rejected</p>
                  <p className="font-mono text-xl text-warning">{result.rejected}</p>
                </div>
                <div className="rounded-lg bg-surface-850 p-3">
                  <p className="text-xs text-slate-500">Failed</p>
                  <p className="font-mono text-xl text-danger">{result.failed}</p>
                </div>
              </div>
              <div className="mt-4 max-h-72 overflow-auto">
                <table className="min-w-full text-left text-sm">
                  <thead className="text-xs uppercase text-slate-500">
                    <tr>
                      <th className="px-2 py-2">#</th>
                      <th className="px-2 py-2">Status</th>
                      <th className="px-2 py-2">Outcome</th>
                      <th className="px-2 py-2">Risk</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {result.results.map((r) => (
                      <tr key={r.index}>
                        <td className="px-2 py-2 font-mono text-xs">{r.index}</td>
                        <td className="px-2 py-2 font-mono text-xs">{r.status_code}</td>
                        <td className="px-2 py-2">
                          <StatusBadge value={r.outcome} />
                        </td>
                        <td className="px-2 py-2 font-mono text-xs">
                          {r.risk_score ?? "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}
