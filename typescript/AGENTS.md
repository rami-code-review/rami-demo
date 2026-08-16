# Working in task-manager (TypeScript)

See `README.md` for what this app is + how to run it, and `ROADMAP.md` for the feature menu.
This file is agent instructions for building here and getting reviewed by [Rami](https://rami.reviews).

## Build one feature
Pick one from `ROADMAP.md` (or a small one in the same spirit — ask me if unsure). Match the
existing style (`ValidationError` → 400, the `normalize*` helpers; store logic in `store.ts`,
a route in `app.ts`). Add tests, keep `npm run typecheck && npm test` green.

## Rules
- **On-project:** if I ask for something off-road (a new app, unrelated domain, heavy
  dependency), flag it and check I mean it before building — then do it if I confirm; it's my repo.
- **PR into the upstream repo:** work on your **fork**, and open every PR against
  `rami-code-review/rami-demo` (the PR's *base* repo) — it's set up to review your PR for
  free, no account needed. Nothing merges — it's a playground.
- **Stack your work:** base each new branch on your previous branch on your fork, so features
  build on each other instead of conflicting. One small feature per PR.
- **Public repo:** never commit secrets, API keys, tokens, or `.env` — it's world-visible.

## Set up Rami (once)
PRs opened against `rami-code-review/rami-demo` are reviewed automatically — **no account
needed**; the review appears in ~a minute. Driving the loop from this agent over MCP needs a one-time login (separate: reviews
come via the GitHub App, the tools need you signed in). **Ask me before installing globally.**

Install the `rami` plugin from the marketplace
(https://github.com/rami-code-review/claude-code-marketplace — serves Codex too) and connect
its MCP server (`https://rami.reviews/mcp`), then authenticate on first use. See
https://rami.reviews/llms.txt for your agent's exact setup commands and scope options.

## The loop (after every push)
Get Rami's review → fix real findings (`get_fix_prompt` for detail) or rebut false ones with
evidence → push → repeat until clean (`ready_for_review: true`). You decide what's real.
