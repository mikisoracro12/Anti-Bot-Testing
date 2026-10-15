# Security notes — BotShield Lab

## Scope

BotShield Lab is a **local demonstration** of anti-bot techniques. It is **not** a production bot-management product and should not be exposed to the public Internet without a full security review, hardened deployment, and operational monitoring.

## Threat model (simplified)

| Asset | Risk | Mitigation in this demo |
| --- | --- | --- |
| Turnstile secret key | Leak via frontend or logs | Stored only in backend env; redacted from logs; never returned by API |
| Request event store | PII accumulation | Hashed client IDs; no passwords/tokens/cookies stored |
| Rate limiter | Bypass via spoofed identity | Direct peer IP by default; forwarded headers only if trusted proxy configured |
| Simulator | Abuse against third parties | Fixed allowlist of local hosts; no arbitrary URLs |
| Mock CAPTCHA | Accidental production use | Explicit enablement; blocked when `APP_ENV=production` |

## Important limitations

1. **User-Agent is a weak signal.** Legitimate clients may omit or customize it; automation can forge it. This project never claims UA checks alone identify bots and never auto-bans on weak signals alone.
2. **IP-based identity is unreliable** behind CGNAT, VPNs, and reverse proxies. Set `TRUST_FORWARDED_HEADERS=true` only when a trusted reverse proxy is the sole path to the app, and list that proxy in `TRUSTED_PROXY_IPS`.
3. **In-memory rate limiting** does not share state across workers. Use Redis for multi-worker deployments.
4. **SQLite** is suitable for local demos, not high-concurrency production writes.
5. **CAPTCHA** proves a challenge was solved for a token at verification time; it is not a permanent proof of humanity.

## Safe defaults checklist

- [ ] `APP_ENV=production` only after review
- [ ] `CAPTCHA_PROVIDER=turnstile` with real keys (never mock) in production
- [ ] Restrictive `CORS_ORIGINS`
- [ ] `TRUST_FORWARDED_HEADERS=false` unless behind a known proxy
- [ ] Secrets only in environment / secret manager — never in git
