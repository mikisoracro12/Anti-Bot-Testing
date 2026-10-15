import { fetchRateLimitConfig, getErrorMessage } from "../api/client";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { useAsync } from "../hooks/useAsync";

export function RateLimitsPage() {
  const { data, error, loading, reload } = useAsync(
    () => fetchRateLimitConfig().catch((e) => Promise.reject(new Error(getErrorMessage(e)))),
    []
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-50">Rate limiting</h1>
        <p className="mt-1 text-sm text-slate-400">
          Configurable limits from environment variables. Violations return HTTP 429 and are logged.
        </p>
      </div>

      {loading && <LoadingState />}
      {error && <ErrorState message={error} onRetry={() => void reload()} />}

      {data && (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="panel p-4">
              <p className="text-xs uppercase text-slate-500">Enabled</p>
              <p className="mt-2 text-xl text-slate-50">{data.enabled ? "Yes" : "No"}</p>
            </div>
            <div className="panel p-4">
              <p className="text-xs uppercase text-slate-500">Requests / window</p>
              <p className="mt-2 font-mono text-xl text-slate-50">{data.requests}</p>
            </div>
            <div className="panel p-4">
              <p className="text-xs uppercase text-slate-500">Window (seconds)</p>
              <p className="mt-2 font-mono text-xl text-slate-50">{data.window_seconds}</p>
            </div>
            <div className="panel p-4">
              <p className="text-xs uppercase text-slate-500">Storage</p>
              <p className="mt-2 font-mono text-xl text-slate-50">{data.storage}</p>
            </div>
          </div>

          <section className="panel p-5">
            <h2 className="text-sm font-semibold text-slate-200">Storage limitations</h2>
            <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-slate-400">
              {data.limitations.map((l) => (
                <li key={l}>{l}</li>
              ))}
            </ul>
            <p className="mt-4 text-sm text-slate-400">
              Redis configured in settings:{" "}
              <span className="font-mono text-slate-200">
                {data.redis_configured ? "yes" : "no"}
              </span>
              . Change limits via{" "}
              <code className="rounded bg-surface-850 px-1.5 py-0.5 font-mono text-xs">
                RATE_LIMIT_REQUESTS
              </code>{" "}
              and{" "}
              <code className="rounded bg-surface-850 px-1.5 py-0.5 font-mono text-xs">
                RATE_LIMIT_WINDOW_SECONDS
              </code>{" "}
              in <code className="font-mono text-xs">.env</code>, then restart the backend.
            </p>
          </section>
        </>
      )}
    </div>
  );
}
