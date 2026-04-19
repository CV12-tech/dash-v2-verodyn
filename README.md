# FlowStack by Verodyn

**Empathic high-tech** automation dashboard for regulated industries. Built on Next.js 14 App Router with a hardened multi-tenant foundation and a Verodyn-designed interface.

## Highlights

- **Verodyn design system**: Plus Jakarta Sans, 12px unified radius, border-first elevation (no hard shadows), Deep Slate text hierarchy, Electric Blue primary with Mint/Rose/Purple accents. HSL token architecture with full dark-mode parity.
- **FlowStack domain**: 23 workflows across 5 categories (client-lifecycle, deadline-followup, review-reporting, meeting-protocols, triage-error-handling), taken from the FlowStack 2.0 `legal-automation` catalog.
- **Security first**: CSP + HSTS + frame-deny headers, bcrypt password hashing with timing-attack mitigation, Zod-validated env + inputs, declarative RBAC permission matrix (Admin/Write/Read), audited via CodeQL.
- **Strict TypeScript**: `strict`, `noUncheckedIndexedAccess`, `noImplicitOverride` — no implicit `any` anywhere.
- **Modules**:
  - **Übersicht** — stat cards, weekly calendar hero, 30-day executions chart (auswertung) with recent-executions side panel, category tiles
  - **Workflows** — filter chips + table with expandable performance panels (7-run pips, 10-day success sparkline, ⌀ duration, throughput)
  - **Kalender** — full week view with upcoming list
  - **Alert banner** on every dashboard page — pulsing, collapsible, action-oriented; maps errors to recommended actions
- **A11y**: skip-to-content, `aria-current`, `aria-expanded`, keyboard-navigable sidebar, ARIA-annotated tables, visible focus-visible rings
- **i18n**: Full DE + EN via `next-intl`, DE default
- **Tooling**: ESLint + jsx-a11y, Prettier + Tailwind plugin, Husky + lint-staged, Vitest unit + Playwright e2e, GitHub Actions CI + CodeQL

## Quick start

```bash
pnpm install
cp .env.example .env.local
# Generate a real secret:
openssl rand -base64 48   # paste into NEXTAUTH_SECRET
pnpm run dev
```

Open http://localhost:3000 → redirects to `/overview`. Demo credentials (rotate before production):

| Role  | Email                   | Password        |
| ----- | ----------------------- | --------------- |
| admin | admin@verodyn.local     | ChangeMe!2025   |
| write | write@verodyn.local     | ChangeMe!2025   |
| read  | read@verodyn.local      | ChangeMe!2025   |

## Scripts

| Command              | Purpose                                            |
| -------------------- | -------------------------------------------------- |
| `pnpm dev`           | Dev server                                         |
| `pnpm build`         | Production build                                   |
| `pnpm start`         | Run production build                               |
| `pnpm lint`          | ESLint                                             |
| `pnpm typecheck`     | `tsc --noEmit`                                     |
| `pnpm format`        | Prettier write                                     |
| `pnpm test`          | Vitest unit tests                                  |
| `pnpm test:e2e`      | Playwright e2e (builds + starts the app)           |
| `pnpm check`         | Typecheck + lint + test (pre-merge gate)           |

## Project structure

```
src/
├── app/                          # Next.js App Router
│   ├── (auth)/login/             # Public auth pages
│   ├── (dashboard)/              # Protected route group
│   │   ├── overview/             # stat cards + calendar hero + auswertung
│   │   ├── workflows/            # filter + expandable table
│   │   ├── calendar/             # full week view + upcoming
│   │   ├── executions/ tasks/ settings/
│   │   └── layout.tsx            # Sidebar + Topbar shell
│   ├── api/                      # Route handlers (RBAC-gated)
│   │   ├── auth/[...nextauth]/
│   │   ├── workflows/            # + [slug] for detail
│   │   ├── executions/
│   │   ├── calendar/events/
│   │   └── metrics/
│   ├── error.tsx · loading.tsx · not-found.tsx
│   ├── layout.tsx · providers.tsx · page.tsx
│   └── globals.css               # Verodyn tokens
├── components/
│   ├── ui/                       # Primitives: Button, Card, Input, Badge, Skeleton
│   ├── layout/                   # Sidebar (duo-tone icons), Topbar, ThemeToggle
│   └── charts/                   # Sparkline
├── features/
│   ├── alerts/                   # AlertBanner (with error→recommendation mapping)
│   ├── calendar/                 # CalendarWeek (compact + full), UpcomingEvents
│   ├── dashboard/                # StatCard, shared hooks
│   ├── executions/               # RecentExecutions
│   ├── metrics/                  # ExecutionsChart (Recharts with Verodyn tokens)
│   └── workflows/                # WorkflowTable (expandable rows, 4 perf panels)
├── lib/                          # env, cn, logger, rbac, validation, workflow-categories
├── server/
│   ├── auth/                     # NextAuth config (bcrypt, timing-attack mit.)
│   └── services/                 # workflow-service, execution-service,
│                                 # calendar-service, metrics-service, user-service
├── i18n/                         # config + request + messages/{de,en}.json
├── types/                        # Module augmentations
└── middleware.ts                 # Route-level RBAC

tests/
├── unit/                         # Vitest (rbac, validation)
└── e2e/                          # Playwright (auth flow)

docs/
├── AUDIT.md                      # V1 → Dash V2 → Verodyn audit trail
└── PUSH-TO-GITHUB.md             # Publishing instructions
```

## Design system reference

The Verodyn tokens live in `src/app/globals.css` and `tailwind.config.ts`:

- **Surfaces**: `bg` `#F8FAFC`, `surface` `#FFFFFF`, `surface-muted` `#F1F5F9`
- **Text (Deep Slate)**: `ink` `#0F172A`, `ink-muted` `#64748B`, `ink-subtle` `#94A3B8`
- **Brand**: `primary` `#2D5BFF` with `primary-soft` `#EEF2FF` background chip
- **Accents**: `success` `#10B981` (Mint), `warning` `#F43F5E` (Soft Rose), `info` `#8B5CF6` (Soft Purple)
- **Radius**: 12px unified (`rounded-lg`)
- **Elevation**: 1px `border-border`, never hard shadows
- **Motion**: `filter: brightness(1.08)` on hover — brightness shifts, never hue swaps
- **Typography**: Plus Jakarta Sans (400/500/600/700/800) as `--font-sans`, loaded via `next/font`; `.nums` class applies tabular-nums + optical kerning for statistics; `.label-xs` applies uppercase 10px labels with tracking

## Data flow

UI → React Query hook (`useMetrics`, `useWorkflows`, `useExecutions`, `useCalendarEvents`) → `/api/…` route handler → `getServerSession` + `can()` check → `server/services/*` → (future) Prisma repository. Zod parses at both API boundary and client-side response. The in-memory seed data in `server/services` mirrors the FlowStack 2.0 `legal-automation/workflows/*` tree.

## Pushing to GitHub

See `docs/PUSH-TO-GITHUB.md`. TL;DR:

```bash
cd flowstack-verodyn
git init -b main
git add .
git commit -m "chore: initial commit — FlowStack by Verodyn"
gh repo create flowstack-verodyn --private --source=. --remote=origin --push
```

## Security checklist before production

- [ ] Rotate `NEXTAUTH_SECRET` (`openssl rand -base64 48`)
- [ ] Replace the in-memory user store with a Prisma-backed repository against the FlowStack multi-tenant schema (Tenant / User / MicrosoftToken / WorkflowExecution)
- [ ] Wire `/api/calendar/events` to Microsoft Graph `/me/calendar/events` using the `MicrosoftToken` table
- [ ] Wire `/api/workflows` and `/api/executions` to the n8n instance (see FlowStack `api/src/services/n8n.ts` for the existing client)
- [ ] Enable rate limiting on `/api/auth/*`
- [ ] Tighten CSP — drop `'unsafe-inline'`/`'unsafe-eval'` for scripts in production by switching to nonces
- [ ] Add Sentry or similar for error tracking; the logger already emits structured JSON
- [ ] Turn on Dependabot + CodeQL on the GitHub repo

## License

MIT — see `LICENSE`.
