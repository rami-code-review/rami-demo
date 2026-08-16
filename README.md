# Try Rami on real code

Welcome 😸

This is a public demo repository for [Rami Code Review](https://rami.reviews).

It exists so you can see how Rami works on real pull requests before installing it on your own repositories.

## Start here

If you want the shortest path, start with [one good example PR](https://github.com/rami-code-review/rami-demo/pull/9).

If you just want to see what Rami looks like in action, start with these:

- **Browse real reviewed PRs:** [20 merged demo PRs](https://github.com/rami-code-review/rami-demo/pulls?q=is%3Apr+is%3Amerged+author%3AShavakan)
- **Try it yourself:** fork this repo, implement a feature, and open a PR against **`rami-code-review/rami-demo`**
- **Use the full MCP loop:** connect your agent and let it fetch findings, fix them, and ask for re-review

## What's in this repo?

There are four unfinished small apps, each in a different language:

| Directory                    | App           | What it is                                                       |
| ---------------------------- | ------------- | ---------------------------------------------------------------- |
| [`typescript/`](typescript/) | Task manager  | A small to-do web app (the kind you'd build for yourself)        |
| [`python/`](python/)         | Ledger        | A personal-finance tracker — transactions, categories, summaries |
| [`go/`](go/)                 | URL shortener | Turn long links into short ones, count the clicks                |
| [`rust/`](rust/)             | Log tailer    | A `tail -f` with built-in filtering                              |

Each app is intentionally unfinished, with a ROADMAP.md to help you pick the next thing to build.

## Why these work as a demo

We picked apps that are quick to understand, but still real enough for code review to matter.

Toy problems don't leave enough room for meaningful review. Large production codebases take too long to learn. These apps sit in the middle: small enough to grasp quickly, real enough for bugs, edge cases, and risky patterns to show up.

The reviews here are honest. We did not plant bugs for Rami to "find." You write a real change, Rami reviews the actual diff, and sometimes it will simply approve it. That is the point.


## Try it yourself

1. **Pick an app** in a language you are comfortable with.
2. **Open its `ROADMAP.md`** and choose a feature.
3. **Fork this repository** and implement the feature yourself or with your coding agent.
4. **Open a pull request against `rami-code-review/rami-demo`**.
5. **Wait for Rami to review it** on the PR.
6. **Fix or rebut the findings**, then re-run the loop until it clears.

That's it.

### Important: open the PR against the demo repo

Your PR must target:

**Base repository: `rami-code-review/rami-demo`**

If the base is your own fork, Rami will not review it here.

If you use GitHub CLI:

```bash
gh pr create --repo rami-code-review/rami-demo
```

## See real reviews

If you want to see what a Rami review looks like before forking, start here:

[Browse merged demo PRs](https://github.com/rami-code-review/rami-demo/pulls?q=is%3Apr+is%3Amerged+author%3AShavakan)

Those reviews are real. Most PRs started from a single-line prompt and were fixed end to end through the full loop.

A small note: the early PRs were written with a weaker model on purpose so the review flow would be easier to see. Use whatever model you want when you try it yourself.


## Experience the full loop

The review is only half the story.

Rami speaks [MCP](https://modelcontextprotocol.io), so Claude Code, Cursor, or Codex can fetch findings, apply fixes, and ask for re-review until things clear. You still decide what merges.

This repo is already wired for that flow. The `CLAUDE.md` and `AGENTS.md` at the root tell your agent what to do after each push.

> After every push, run `/rami:review` on the PR. Fix the real findings,
> rebut the false ones. Repeat until `/rami:review` comes back clean.

**Connect your agent once** — for Claude Code:

```
/plugin marketplace add rami-code-review/claude-code-marketplace
/plugin install rami@rami-code-review
/reload-plugins
```

Then run `claude` → `/mcp` → select `plugin:rami:rami` → log in.

Useful links:

- **Claude Code / Codex marketplace setup:** https://github.com/rami-code-review/claude-code-marketplace
- **All setup instructions:** https://rami.reviews/llms.txt

Or just paste this into Claude Code, Cursor, or Codex:

> Set up the Rami code review plugin (MCP server + skills) and add a rule to run /rami:review after every push until clean. See https://rami.reviews/llms.txt.

If you already have a PR open here, the one-liner is:

> Fetch the Rami findings on my open PR and apply them.

## Review configuration

Rami reads an optional [`.rami.yaml`](.rami.yaml) at the repo root.

This repo includes one pinned to the current defaults, so it mostly acts as a reference. You can use it to control things like review language, tone, auto-approval, and whether findings can fail CI.

If you want to experiment, changing `.rami.yaml` in your fork is a good way to do it.

The settings reference is also available in the [web console](https://rami.reviews/console#repository-configuration).

## A few notes about this repo

- **PRs here are not merged.** This repo exists to try Rami, not to accept contributions.
- **Idle PRs are auto-closed.** You'll get a warning after 7 days of inactivity, then the PR closes 2 days later.
- **This is a public repo.** Don't commit credentials, tokens, API keys, or anything sensitive, even on your fork.

## FAQ

**Do I need a Rami account or a subscription to try this?**

No. PRs opened against `rami-code-review/rami-demo` can be reviewed for free here.

If you want to use the MCP fix loop from your agent, that requires signing in. The sign-in is free.

### Where should I open my PR?

From your fork, with the **base repo set to `rami-code-review/rami-demo`**.

If the base is your own fork, Rami will not review it here.

### I opened a PR but nothing happened

Usually one of these:

- the PR base is your fork, not `rami-code-review/rami-demo`
- the PR is a draft — auto-review waits until you mark it **Ready for review** (or ask your agent to review it now)
- it has only been a short while

### Will my PR get merged?

No, by design. This repo is for trying Rami, not for contributing code.

### Do I need to use an AI agent?

No. You can write the change yourself.

If you do use an agent, Claude Code, Cursor, and Codex all work well with the MCP flow.

### Can I use Rami on my own repositories?

Yes. Start at [rami.reviews](https://rami.reviews/).

### Is it safe to commit secrets here?

Never. This repo and your fork are public. Keep credentials, tokens, and API keys out of anything you push.

### How long do PRs stay open?

Idle PRs get a warning after 7 days, then close 2 days later.

### I already have a PR open. How do I just get the findings and fix them?

Tell your agent:

> Fetch the Rami findings on my open PR and apply them.
