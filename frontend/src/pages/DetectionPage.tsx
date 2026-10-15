import { fetchDetectionConfig, getErrorMessage, postDemo } from "../api/client";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { StatusBadge } from "../components/StatusBadge";
import { useAsync } from "../hooks/useAsync";
import { useState } from "react";
import type { DemoResponse } from "../types/api";

export function DetectionPage() {
  const { data, error, loading, reload } = useAsync(
    () => fetchDetectionConfig().catch((e) => Promise.reject(new Error(getErrorMessage(e)))),
    []
  );
  const [message, setMessage] = useState("detection-probe");
  const [result, setResult] = useState<DemoResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const runProbe = async () => {
    setBusy(true);
    setSubmitError(null);
    try {
      const res = await postDemo({ message, captcha_token: "mock-valid-token" });
      setResult(res);
    } catch (err) {
      // Axios may throw on 403/429 — extract body if present
      const axiosErr = err as { response?: { data?: DemoResponse }; message?: string };
      if (axiosErr.response?.data?.status) {
        setResult(axiosErr.response.data);
      } else {
        setSubmitError(getErrorMessage(err));
      }
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-50">Bot detection</h1>
        <p className="mt-1 text-sm text-slate-400">
          Transparent rule-based scoring. User-Agent alone never reliably identifies a bot.
        </p>
      </div>

      {loading && <LoadingState />}
      {error && <ErrorState message={error} onRetry={() => void reload()} />}

      {data && (
        <>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {[
              ["Window (seconds)", data.window_seconds],
              ["Frequency threshold", data.frequency_threshold],
              ["Repeat endpoint threshold", data.repeat_endpoint_threshold],
              ["Suspicious score ≥", data.suspicious_score_threshold],
              ["High risk score ≥", data.high_risk_score_threshold],
              ["CAPTCHA trigger score", data.captcha_trigger_score],
            ].map(([label, value]) => (
              <div key={String(label)} className="panel p-4">
                <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
                <p className="mt-2 font-mono text-xl text-slate-50">{value}</p>
              </div>
            ))}
          </div>

          <section className="panel p-5">
            <h2 className="text-sm font-semibold text-slate-200">Scoring notes</h2>
            <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-slate-400">
              {data.notes.map((n) => (
                <li key={n}>{n}</li>
              ))}
            </ul>
          </section>

          <section className="panel p-5">
            <h2 className="mb-3 text-sm font-semibold text-slate-200">Live probe</h2>
            <p className="mb-4 text-sm text-slate-400">
              Send a request to the protected demo endpoint and inspect the explainable score.
            </p>
            <div className="flex flex-col gap-3 sm:flex-row">
              <input
                className="input"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                maxLength={500}
                aria-label="Probe message"
              />
              <button
                type="button"
                className="btn-primary shrink-0"
                disabled={busy}
                onClick={() => void runProbe()}
              >
                {busy ? "Sending…" : "Send probe"}
              </button>
            </div>
            {submitError && <p className="mt-3 text-sm text-danger">{submitError}</p>}
            {result && (
              <div className="mt-4 space-y-3 rounded-lg bg-surface-850 p-4 text-sm">
                <div className="flex flex-wrap items-center gap-3">
                  <StatusBadge value={result.status} />
                  <StatusBadge value={result.classification} />
                  <span className="font-mono text-slate-400">risk {result.risk_score}</span>
                </div>
                <p className="text-slate-300">{result.message}</p>
                {result.detection_reasons.length > 0 && (
                  <ul className="space-y-2">
                    {result.detection_reasons.map((r, i) => (
                      <li key={`${r.rule}-${i}`} className="border-l-2 border-accent/40 pl-3">
                        <span className="font-mono text-accent">{r.rule}</span>
                        <span className="ml-2 font-mono text-xs text-slate-500">+{r.score}</span>
                        <p className="text-xs text-slate-400">{r.explanation}</p>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
}
