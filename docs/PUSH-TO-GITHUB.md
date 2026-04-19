# Pushing FlowStack by Verodyn to GitHub

This repository was generated offline. Here's how to get it onto GitHub.

## Prerequisites

- A GitHub account
- Either the [GitHub CLI](https://cli.github.com/) (`gh`) or Git with SSH/HTTPS configured
- Node.js ≥ 20.10 and pnpm ≥ 9 installed locally (only needed for verification, not for pushing)

## One-time setup

```bash
# 1. Unzip the archive somewhere sensible
cd ~/code
unzip flowstack-verodyn.zip
cd flowstack-verodyn

# 2. Verify the project actually builds before pushing (recommended but optional)
pnpm install
cp .env.example .env.local
# Generate a real NEXTAUTH_SECRET:
openssl rand -base64 48
# Paste the output into .env.local
pnpm run check   # typecheck + lint + test
```

## Option A — GitHub CLI (fastest)

```bash
git init -b main
git add .
git commit -m "chore: initial commit — FlowStack by Verodyn hardened rework"

gh repo create flowstack-verodyn --private --source=. --remote=origin --push
```

That's it. The repo is now on GitHub, the remote is configured, and `main` is pushed.

## Option B — manual

```bash
git init -b main
git add .
git commit -m "chore: initial commit — FlowStack by Verodyn hardened rework"
```

Then on github.com, click **New repository**, name it `flowstack-verodyn`, leave it empty (no README, no .gitignore, no license — they're already in the repo), and copy the SSH or HTTPS URL.

```bash
git remote add origin git@github.com:<your-user>/flowstack-verodyn.git   # or https://github.com/<your-user>/flowstack-verodyn.git
git push -u origin main
```

## After the first push

1. **Enable branch protection on `main`**
   - Settings → Branches → Add rule for `main`
   - Require pull requests, require status checks (`CI / Lint · Typecheck · Test · Build`), require signed commits if your workflow supports it
2. **Enable Dependabot**
   - Settings → Code security → Enable Dependabot alerts + security updates
3. **Enable CodeQL**
   - The workflow is already shipped in `.github/workflows/codeql.yml`. It runs on push, PR, and weekly
4. **Add a deploy target** (optional)
   - Vercel: `vercel link` then `vercel env add NEXTAUTH_SECRET` etc.
   - Or configure your own hosting. Remember to set `NEXTAUTH_URL` to the public URL.

## Safety check before pushing

Run this first to make sure no secrets sneak in:

```bash
git diff --cached --name-only | grep -E '\.env$|\.env\.local$'
# should output nothing
```

And confirm `.gitignore` is present and matches what you expect.

## Troubleshooting

- **`next-env.d.ts` missing** — it's in `.gitignore` on purpose; Next.js regenerates it on the first `pnpm run dev` or `pnpm run build`.
- **Husky not running** — `pnpm run prepare` once after install, or `chmod +x .husky/pre-commit`.
- **CI fails on `format:check`** — run `pnpm run format` locally and commit the result.
