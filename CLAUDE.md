# rami-demo

This repo tries [Rami](https://rami.reviews) on itself: open or push a PR here and Rami
reviews it automatically, in about a minute. No PR merges — it's a playground.

**Pick an app and work in its directory** — each has its own `CLAUDE.md` with how to build
there and run the Rami loop:

- [`python/`](python/) — ledger (FastAPI + SQLite)
- [`go/`](go/) — shortener (net/http)
- [`typescript/`](typescript/) — task-manager (Express)
- [`rust/`](rust/) — logtail (tail -f + filtering)

**The loop, wherever you are:** after every push, run `/rami:review`, fix the real findings
or rebut the false ones, repeat until it's clean. You decide what's real.

**Connect Rami (once)** — in Claude Code: `/plugin marketplace add rami-code-review/claude-code-marketplace`
then `/plugin install rami@rami-code-review`, then `/mcp` → select `rami` → log in.
Reviews need no account; the MCP tools need the one-time login. Details:
https://rami.reviews/llms.txt
