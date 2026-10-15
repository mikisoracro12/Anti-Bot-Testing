import { useState } from "react";
import {
  fetchCaptchaStatus,
  getErrorMessage,
  postDemo,
  verifyCaptcha,
} from "../api/client";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { StatusBadge } from "../components/StatusBadge";
import { useAsync } from "../hooks/useAsync";
import type { DemoResponse } from "../types/api";

export function CaptchaPage() {
  const { data, error, loading, reload } = useAsync(
    () => fetchCaptchaStatus().catch((e) => Promise.reject(new Error(getErrorMessage(e)))),
    []
  );
  const [token, setToken] = useState("mock-valid-token");
  const [verifyResult, setVerifyResult] = useState<string | null>(null);
  const [demoResult, setDemoResult] = useState<DemoResponse | null>(null);
  const [busy, setBusy] = useState(false);

  const onVerify = async () => {
    setBusy(true);
    setVerifyResult(null);
    try {
      const res = await verifyCaptcha(token);
      setVerifyResult(
        res.success
          ? `Verified via ${res.provider}: ${res.message}`
          : `Failed (${res.provider}): ${res.message} [${(res.error_codes || []).join(", ")}]`
      );
    } catch (err) {
      setVerifyResult(getErrorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  const onDemo = async () => {
    setBusy(true);
    setDemoResult(null);
    try {
      const res = await postDemo({ message: "captcha-demo", captcha_token: token });
      setDemoResult(res);
    } catch (err) {
      const axiosErr = err as { response?: { data?: DemoResponse } };
      if (axiosErr.response?.data?.status) {
        setDemoResult(axiosErr.response.data);
      } else {
        setVerifyResult(getErrorMessage(err));
      }
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-50">CAPTCHA</h1>
        <p className="mt-1 text-sm text-slate-400">
          Cloudflare Turnstile server-side verification, plus an explicit local mock for offline
          development. Secrets never leave the backend.
        </p>
      </div>

      {loading && <LoadingState />}
      {error && <ErrorState message={error} onRetry={() => void reload()} />}

      {data && (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="panel p-4">
              <p className="text-xs uppercase text-slate-500">Enabled</p>
              <p className="mt-2 text-xl">{data.enabled ? "Yes" : "No"}</p>
            </div>
            <div className="panel p-4">
              <p className="text-xs uppercase text-slate-500">Provider</p>
              <p className="mt-2 font-mono text-xl">{data.provider}</p>
            </div>
            <div className="panel p-4">
              <p className="text-xs uppercase text-slate-500">Ready</p>
              <p className="mt-2 text-xl">{data.ready ? "Yes" : "No"}</p>
            </div>
            <div className="panel p-4">
              <p className="text-xs uppercase text-slate-500">Secret configured</p>
              <p className="mt-2 text-xl">{data.secret_configured ? "Yes" : "No"}</p>
            </div>
          </div>

          {data.warnings.length > 0 && (
            <div className="rounded-xl border border-warning/30 bg-warning/5 p-4 text-sm text-amber-200">
              <ul className="list-disc space-y-1 pl-5">
                {data.warnings.map((w) => (
                  <li key={w}>{w}</li>
                ))}
              </ul>
            </div>
          )}

          <section className="panel space-y-4 p-5">
            <h2 className="text-sm font-semibold text-slate-200">Demo verification form</h2>
            <p className="text-sm text-slate-400">
              For mock mode use token <code className="font-mono text-xs">mock-valid-token</code>.
              With Turnstile, paste the widget token after solving the challenge. Client-side
              success messages are never trusted as proof of verification.
            </p>
            {data.site_key && data.provider === "turnstile" && (
              <p className="text-xs text-slate-500">
                Site key (public): <span className="font-mono">{data.site_key}</span>
              </p>
            )}
            <div>
              <label className="label" htmlFor="token">
                CAPTCHA token
              </label>
              <input
                id="token"
                className="input"
                value={token}
                onChange={(e) => setToken(e.target.value)}
                placeholder="Token from Turnstile widget or mock-valid-token"
              />
            </div>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                className="btn-secondary"
                disabled={busy}
                onClick={() => void onVerify()}
              >
                Verify token
              </button>
              <button
                type="button"
                className="btn-primary"
                disabled={busy}
                onClick={() => void onDemo()}
              >
                Submit protected demo
              </button>
            </div>
            {verifyResult && <p className="text-sm text-slate-300">{verifyResult}</p>}
            {demoResult && (
              <div className="rounded-lg bg-surface-850 p-4 text-sm">
                <div className="mb-2 flex flex-wrap gap-2">
                  <StatusBadge value={demoResult.status} />
                  <StatusBadge value={demoResult.captcha_status} />
                </div>
                <p className="text-slate-300">{demoResult.message}</p>
              </div>
            )}
          </section>

          <section className="panel p-5 text-sm text-slate-400">
            <h2 className="mb-2 text-sm font-semibold text-slate-200">Turnstile setup</h2>
            <ol className="list-decimal space-y-1 pl-5">
              <li>
                Create a widget at{" "}
                <a
                  className="text-accent hover:underline"
                  href="https://developers.cloudflare.com/turnstile/"
                  target="_blank"
                  rel="noreferrer"
                >
                  Cloudflare Turnstile
                </a>
              </li>
              <li>
                Set <code className="font-mono text-xs">CAPTCHA_PROVIDER=turnstile</code>
              </li>
              <li>
                Set <code className="font-mono text-xs">TURNSTILE_SITE_KEY</code> and{" "}
                <code className="font-mono text-xs">TURNSTILE_SECRET_KEY</code>
              </li>
              <li>
                Never commit secrets. Mock mode is blocked when{" "}
                <code className="font-mono text-xs">APP_ENV=production</code>.
              </li>
            </ol>
          </section>
        </>
      )}
    </div>
  );
}
