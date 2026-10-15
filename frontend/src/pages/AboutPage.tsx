export function AboutPage() {
  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-50">About BotShield Lab</h1>
        <p className="mt-2 text-sm leading-relaxed text-slate-400">
          BotShield Lab is an open-source portfolio project that demonstrates how web applications
          can detect suspicious automated traffic, enforce rate limits, validate CAPTCHA challenges,
          and monitor request activity in a controlled local environment.
        </p>
      </div>

      <section className="panel space-y-3 p-5 text-sm text-slate-300">
        <h2 className="text-sm font-semibold text-slate-100">What this is</h2>
        <ul className="list-disc space-y-1 pl-5 text-slate-400">
          <li>A local learning and demonstration platform</li>
          <li>Explainable, rule-based detection (not ML black boxes)</li>
          <li>Safe traffic simulation against this app only</li>
        </ul>
      </section>

      <section className="panel space-y-3 p-5 text-sm text-slate-300">
        <h2 className="text-sm font-semibold text-slate-100">What this is not</h2>
        <ul className="list-disc space-y-1 pl-5 text-slate-400">
          <li>A production-ready WAF or bot management product</li>
          <li>A tool for attacking third-party websites</li>
          <li>A claim that User-Agent checks alone identify bots</li>
        </ul>
      </section>

      <section className="panel space-y-3 p-5 text-sm text-slate-300">
        <h2 className="text-sm font-semibold text-slate-100">Documentation</h2>
        <ul className="space-y-2 text-slate-400">
          <li>
            API docs (when backend is running):{" "}
            <a className="text-accent hover:underline" href="http://127.0.0.1:8000/docs">
              http://127.0.0.1:8000/docs
            </a>
          </li>
          <li>See the repository README for setup, threat model, and contribution guidelines.</li>
          <li>License: MIT</li>
        </ul>
      </section>
    </div>
  );
}
