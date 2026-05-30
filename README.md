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

That's it. The ROADMAPs are a menu, not a contract; the goal is to give
you a real, self-contained slice of work so the review has something to
chew on.

## See real reviews

Want to see what a Rami review actually looks like before you fork? These
apps are built up through small pull requests, each one reviewed by Rami
as it lands. Browse the [merged PRs](../../pulls?q=is%3Apr+is%3Amerged)
and open any of them — the reviews you find there are real, on real
iterative work.

## Want Rami to fix its own findings?

Rami speaks [MCP](https://modelcontextprotocol.io), so your coding agent
(Claude Code, Cursor, Codex, …) can pull Rami's findings and apply the
fixes for you. Setup instructions for every agent live at
**https://rami.reviews/llms.txt**.

Once it's wired up, the magic prompt is just:

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
