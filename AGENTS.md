# Rami code review — close the loop

This repo reviews itself with [Rami](https://rami.reviews). Open or push to a pull
request here and Rami reviews it automatically, within about a minute.

**The loop — run it after every push to a PR:**

1. Run `/rami:review` on the PR.
2. Fix the real findings; rebut the false ones (false positive, framework
   guarantee, intentional design, or duplicate).
3. Repeat until `/rami:review` comes back clean.

You still decide what merges.

**First time? Connect your agent to Rami over MCP.** In Claude Code:

```
/plugin marketplace add rami-code-review/claude-code-marketplace
/plugin install rami@rami-code-review
```

Then run `claude` → `/mcp` → select `plugin:rami:rami` → log in.

Two canonical references to point any agent (or human) at:

- Marketplace + plugins, for Claude Code and Codex —
  https://github.com/rami-code-review/claude-code-marketplace
- Setup for every agent, in one file — https://rami.reviews/llms.txt
