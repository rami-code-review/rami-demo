# rami-demo

Four small apps, four languages. Fork one, build a feature, open a PR —
and watch [Rami](https://rami.reviews) review the code you wrote.

This repo exists so you can try Rami on real code before installing it on
your own. No signup, no quota — every PR opened here gets a free Rami
review.

## What's in here

Four small but complete-enough apps, each in a different language:

| Directory | App | What it is |
|---|---|---|
| [`typescript/`](typescript/) | Task manager | A small to-do web app (the kind you'd build for yourself) |
| [`python/`](python/) | Ledger | A personal-finance tracker — transactions, categories, summaries |
| [`go/`](go/) | URL shortener | Turn long links into short ones, count the clicks |
| [`rust/`](rust/) | Log tailer | A `tail -f` with built-in filtering |

Each one is the scrappy version of a tool you already use. None of them
is finished — that's the point.

## Why these apps

We picked apps you can grok in a few minutes, not toy snippets and not
sprawling production codebases.

- **Toy snippets** ("reverse a string") don't have enough surface area
  for a code review to mean anything. There's nowhere for a real bug to
  hide.
- **Full production apps** take an hour just to understand before you can
  contribute. Too much friction for a "let me just try this" visit.

A small-but-real app is the sweet spot: recognizable enough that you
already have intuitions about how it should work, real enough that adding
a feature surfaces the kind of mistake a reviewer should catch — an
unhandled error path, an injection-prone query, an off-by-one in date
math.

The reviews you get here are honest. Nothing is staged. We didn't plant
bugs for Rami to "find." You write a real feature; Rami reviews your
actual code; whatever it catches, it catches — and sometimes it'll just
say "looks good" and approve. That's the product working the way it would
on your own repo.

## How to use this repo

1. **Pick an app** in a language you're comfortable in.
2. **Open its `ROADMAP.md`.** Each app lists a handful of features we
   intentionally left unbuilt, plus a one-line description of each.
3. **Fork this repo**, and implement one of those features (or invent
   your own — go wild).
4. **Open a pull request** back to your fork.
5. **Watch Rami review it.** Within about a minute, Rami posts its review
   right on your PR. Address what it found, or push back if you disagree —
   the same loop you'd run on real work.
6. **Close the loop — don't fix it by hand.** Let your agent pull Rami's
   findings over MCP and apply them, then watch Rami re-review until the
   flags clear. This repo already ships the rule, so your agent knows the
   drill — see [Experience the full loop](#experience-the-full-loop).

That's it. The ROADMAPs are a menu, not a contract; the goal is to give
you a real, self-contained slice of work so the review has something to
chew on.

## See real reviews

Want to see what a Rami review actually looks like before you fork? These
apps are built up through small pull requests, each one reviewed by Rami
as it lands. Browse the [merged PRs](../../pulls?q=is%3Apr+is%3Amerged)
and open any of them — the reviews you find there are real, on real
iterative work. Some threads show the whole loop: Rami flags an issue, an
agent pushes a fix over MCP, and Rami re-reviews and clears it.

## Experience the full loop

The review is only half the story. Rami speaks
[MCP](https://modelcontextprotocol.io), so your coding agent — Claude Code,
Cursor, or Codex — can pull the findings and fix them for you, then Rami
re-reviews until the flags clear. You decide what merges. This is the part
that's hard to believe until you feel it.

**This repo is already wired for it.** The `CLAUDE.md` and `AGENTS.md` at the
root tell your agent the loop:

> After every push, run `/rami:review` on the PR. Fix the real findings,
> rebut the false ones. Repeat until `/rami:review` comes back clean.

So once Rami is connected, you just push — your agent runs the loop.

**Connect your agent (one time)** — in Claude Code:

```
/plugin marketplace add rami-code-review/claude-code-marketplace
/plugin install rami@rami-code-review
```

Then run `claude` → `/mcp` → select `plugin:rami:rami` → log in.

**Two places to point any agent — or yourself:**

- **Marketplace + plugins**, for Claude Code and Codex —
  https://github.com/rami-code-review/claude-code-marketplace
- **Setup for every agent**, in one file — **https://rami.reviews/llms.txt**

**Or just let your agent set it up** — paste this into Claude Code, Cursor, or
Codex:

> Set up the Rami code review plugin (MCP server + skills) and add a rule to run
> /rami:review after every push until clean. See https://rami.reviews/llms.txt.

**Already have a PR open here?** The one-liner is just:

> "Fetch the Rami findings on my open PR and apply them."

## A few honest notes

- **PRs here aren't merged.** This repo is for *trying* Rami, not for
  contributing fixes. Open whatever PR you like — it won't land, and
  that's expected.
- **Stale PRs auto-close after 48 hours**, to keep the repo tidy. Open a
  fresh one anytime.
- **Want to actually contribute to Rami?** This isn't the place — head to
  [rami.reviews](https://rami.reviews) instead.

## License

[MIT](LICENSE).
