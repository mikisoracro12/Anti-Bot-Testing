# Contributing to BotShield Lab

Thank you for your interest in improving this educational anti-bot testing platform.

## Ground rules

- This project demonstrates **defensive** controls in a **local** environment.
- Do not add features that target third-party sites, rotate proxies, bypass CAPTCHAs, or implement stealth evasion.
- Do not commit secrets, API keys, or production credentials.
- Keep changes focused, tested, and documented.

## Development setup

1. Fork and clone the repository.
2. Copy `.env.example` to `.env`.
3. Follow the development workflow in the README (backend + frontend).
4. Run backend tests: `cd backend && pytest`
5. Run frontend checks: `cd frontend && npm run lint && npm run typecheck && npm run test`

## Pull requests

- Describe the problem and the solution.
- Include tests for new behavior.
- Update the README when user-facing behavior or configuration changes.
- Ensure CI passes.

## Code style

- Backend: Python 3.12+, Ruff-compatible style, type hints where practical.
- Frontend: TypeScript strict mode, functional React components, accessible controls.

## Security disclosures

If you discover a security issue in this demo project, open a private advisory or email the maintainers rather than filing a public exploit-oriented issue. Remember this software is a demonstration and is **not** claimed to be production-ready without a security review.
