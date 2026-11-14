# Prototype Instructions

Run the local server yourself and open the preview in the browser available to this environment. Do not give the user server-start instructions when you can run it.

Before making substantial visual changes, use the Product Design plugin's `get-context` skill when the visual source is unclear or no longer matches the current goal. When the user gives durable prototype-specific design feedback, preferences, or decisions, record them in `AGENTS.md`.

When implementing from a selected generated mock, treat that image as the source of truth for layout, component anatomy, density, spacing, color, typography, visible content, and hierarchy.

Build app UI in `src/`. Keep `.openai/hosting.json`, `worker/index.js`, `scripts/prepare-sites-build.mjs`, and `tests/sites-worker.test.mjs` intact so the same local prototype can be handed to Sites. Before a Sites handoff, run `npm run build` and `npm run test:sites`; the build must leave `dist/client/index.html`, `dist/server/index.js`, and `dist/.openai/hosting.json`.
User priority: responsive layouts on phones, tablets and desktops. Keep the main-branch maintenance page untouched; development belongs to recovery.

Registration/legal extension: keep rules acceptance separate from personal-data consent; both unchecked by default. Documents are drafts until operator and final conditions are confirmed. Admin remains an openly labelled demo with fictional records until server role enforcement exists. Never publish runtime data, SMTP passwords or real participant screenshots.

Rules now incorporate owner-provided prizes and indoor HR/outdoor GPS conditions. Keep missing dates, ages and numerical thresholds explicit; do not invent them. PWA must never cache API or participant uploads. Demo totals must use the shared approved-workout model.

Latest owner decision supersedes indoor HR acceptance: GPS mandatory; no gym/treadmill/no-GPS workouts; any pace. Count workout dates from 2026-10-29 inclusive. Recognition fields: date and km only. Guard against duplicate credit. Do not reintroduce pace, duration or HR requirements.

OpenAI recognition is connected for loopback-only operator testing via the Vite proxy. Never expose recognition_server publicly before authentication. Keep provider key outside source. Live results are real but participant history/credit remains an in-memory test. Files are sent only after the explicit upload-processing checkbox.

Latest implementation supersedes prior demo-only notes: owner requested automatic credit and removal of sample data. app_server.py enforces email-code sessions and server admin role; app_store.py persists consent, workouts and audit in SQLite. Clear valid OpenAI results auto-approve; ambiguous/suspected repeated workouts remain pending. Admin allowlist is private server config. No fake records or fallback login. Keep loopback-only until public HTTPS, backup, retention and deployment checks are complete; preserve main maintenance.

Owner UI decision: workout upload shows only the Send button, without the automatic-check heading, OpenAI implementation copy or per-image checkbox. Clicking Send initiates processing; do not auto-submit on file selection. Registration rules and personal-data consent remain separate and unchecked by default.

Owner explicitly authorized replacing the public app maintenance page on 2026-11-13, despite the known DNS blocker for api.sportfondhm.ru. Publish frontend from main with GitHub Pages Actions. Public pages must render without API; show an honest service-unavailable notice and never claim public auth works before API is reachable.

Public API preparation 14.11: backend supports exact public origin with CORS and Secure cookies; infra/home provides Caddy, unprivileged API and daily consistent backup. Router public ports still require explicit action-time confirmation; do not enable old saved port forwards accidentally. Windows network script requires Administrator and checks conflicts. Public readiness is not established by a healthy local container.
