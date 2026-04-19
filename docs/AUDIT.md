# Audit trail — enterprise-dashboard V1 → Dash V2 → FlowStack by Verodyn

This codebase went through three stages. The V1 audit is preserved here; Dash V2 fixed the structural issues; FlowStack by Verodyn added the domain model + design system from the FlowStack 2.0 reference implementation.

## Stage 1 — V1 critical/major findings (all resolved in V2)

| Area | V1 issue | Resolution |
|------|----------|------------|
| Credentials | Hardcoded `admin@test.com / 1234` in the auth route | bcrypt hashes, swap-in user repository, timing-attack mitigation |
| Secret | `NEXTAUTH_SECRET` absent; prod build would fail | Zod-validated env, fails fast at boot |
| RBAC | `role` on token but never enforced | Declarative `PERMISSIONS` matrix, enforced in middleware + every API route |
| Validation | Login accepted empty strings | `loginSchema`, both client and server |
| Headers | No CSP, HSTS, X-Frame-Options | All three shipped in `next.config.mjs` |
| Types | `strict: true` but untyped components | Fully typed; `noUncheckedIndexedAccess` added |
| Data | `react-query`, `axios` installed but unused | Thin API layer + hooks actually consume them |
| Error states | No `error.tsx`, `loading.tsx`, `not-found.tsx` | All three at root |
| Tests | Zero | Vitest unit (rbac, validation) + Playwright e2e (auth) |
| A11y | `<div>` sidebar items, tables without `scope` | `<Link>` with `aria-current`, sortable/expandable tables with `aria-expanded`/`aria-sort` |
| i18n | Hardcoded English | `next-intl`, full DE + EN |
| Theming | Light-only | HSL tokens + dark-mode parity, anti-FOUC init script |
| Responsive | `grid-cols-4` without breakpoints | `grid-cols-1 sm:grid-cols-2 lg:grid-cols-4` |
| CI | None | Lint + format + typecheck + test + build + CodeQL |

## Stage 2 — Verodyn design-system migration

| Change | From | To |
|--------|------|-----|
| Typeface | Inter/Fraunces mixed | **Plus Jakarta Sans** (primary) wired via `next/font`, JetBrains Mono for code |
| Radius | Mixed 6/8/12/16 | Unified 12px (`rounded-lg`) |
| Elevation | Hard shadows on every card | **1px borders only**, `shadow-card` removed |
| Hover | Color swaps | Minor brightness shift (`filter: brightness(1.08)`) |
| Text hierarchy | Arbitrary grays | **Deep Slate** — `#0F172A` / `#64748B` / `#94A3B8` |
| Accents | Classic green/red | **Mint** `#10B981` / **Soft Rose** `#F43F5E` / **Soft Purple** `#8B5CF6` |
| Sidebar | White surface | `#F1F5F9` surface-muted, duo-tone icons |
| Charts | Full grid + axis lines | **Glassmorphism-light** — no grid, gradient fills (12%→0%), sparse tick labels |
| Labels | Inline body text for stat labels | `.label-xs` utility: 10px uppercase with 0.08em tracking |
| Numerics | Regular numerals | `.nums` class: tabular-nums + optical kerning |

## Stage 3 — FlowStack domain integration

| Change | Before | After |
|--------|--------|-------|
| Roles | `admin` / `editor` / `viewer` | **`admin` / `write` / `read`** (FlowStack model) |
| Data model | Abstract "revenue/users/orders" | Workflows, Executions, Calendar events, Tasks, Microsoft Tokens |
| Workflows | None | 23 seeded workflows matching `legal-automation/workflows/*` slugs |
| Categories | None | 5 domains: client-lifecycle, deadline-followup, review-reporting, meeting-protocols, triage-error-handling |
| Permissions | Generic CRUD | `workflows.{read/execute/upload/delete}`, `executions.{read/retry}`, `calendar.{read/write}`, `tasks.close`, `tenant.manage`, `audit.read` |
| Routes | `/dashboard` | `/overview`, `/workflows`, `/workflows/[slug]`, `/executions`, `/calendar`, `/tasks`, `/settings` |
| API | `/api/metrics`, `/api/users` | `/api/workflows`, `/api/workflows/[slug]`, `/api/executions`, `/api/calendar/events`, `/api/metrics` (all RBAC-gated) |

## Stage 4 — Design-review iterations

After the first Verodyn preview was reviewed, three refinements were baked in:

1. **Calendar promoted to hero on `/overview`** — the weekly grid sits directly under the stat cards, replacing the chart's former position. The "Volle Ansicht"-link deep-links to `/calendar`.
2. **Auswertung moved left** — the 30-day executions chart + recent-executions side panel now live below the calendar, chart occupying 2/3 width and executions 1/3.
3. **Alert banner** — shipped as `features/alerts/AlertBanner`. Collapsed: one-line summary with pulsing warning badge. Expanded: per-error card with monospace error message, **recommended action** in a blue info panel, and three actions (primary retry/escalate + Workflow öffnen + Stummschalten). The primary action label adapts to the error type (`"Jetzt neu starten"` for rate limits, `"An Vertretung senden"` for approval timeouts).
4. **Workflow table rows expand** — clicking a row reveals 4 performance panels: last 7 runs as status pips, 10-day success-trend sparkline with pp delta, ⌀ duration, and 7-day throughput. Quick actions live at the bottom of the expansion.
