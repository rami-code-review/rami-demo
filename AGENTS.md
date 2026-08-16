# rami-demo

This repo tries [Rami](https://rami.reviews) on itself: open or push a PR here and Rami
reviews it automatically, in about a minute. No PR merges — it's a playground.

**Pick an app and work in its directory** — each has its own `AGENTS.md` with how to build
there and run the Rami loop:

- [`python/`](python/) — ledger (FastAPI + SQLite)
- [`go/`](go/) — shortener (net/http)
- [`typescript/`](typescript/) — task-manager (Express)
- [`rust/`](rust/) — logtail (tail -f + filtering)

**The loop, wherever you are:** after every push, get Rami's review, fix the real findings
or rebut the false ones, repeat until it's clean. You decide what's real.

**Connect Rami (once):** install the `rami` plugin from the marketplace
(https://github.com/rami-code-review/claude-code-marketplace, which serves Codex too) and
connect its MCP server (`https://rami.reviews/mcp`), then authenticate. Reviews need no
account; the MCP tools need the one-time login. Exact steps for your agent:
https://rami.reviews/llms.txt
