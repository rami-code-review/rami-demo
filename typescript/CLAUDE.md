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
- **Stacked PRs:** nothing here gets merged (this repo is for *trying* Rami). Base each PR on
  your **previous branch**, not `main`, so work stacks. One small feature per PR.
- **Public repo:** never commit secrets, API keys, tokens, or `.env` — it's world-visible.

## Set up Rami (once)
Reviews are already enabled here — **no account needed**; open a PR and the review appears in
~a minute. Driving the loop from this agent over MCP needs a one-time OAuth login (separate:
reviews come via the GitHub App, the tools need you signed in). **Ask me before installing globally.**

1. Install the plugin (ask before global):
   ```
   claude plugin marketplace add rami-code-review/claude-code-marketplace
   claude plugin install rami@rami-code-review
   ```
   If I decline global, project-scope it: `claude mcp add rami --transport http https://rami.reviews/mcp`
2. `/mcp` → select `rami` → complete OAuth login. Verify: `/rami:usage`.

Ref: https://rami.reviews/llms.txt

## The loop (after every push)
Run `/rami:review` → fix real findings (`get_fix_prompt` for detail) or rebut false ones with
evidence → push → repeat until clean (`ready_for_review: true`). You decide what's real.
