# logtail — roadmap

A live log tailer with filtering: follow a file like `tail -f`, keep only
the lines that match.

## What's built

The core slice: a stdlib-only CLI that follows a file and filters lines.

- `logtail [--filter <substring>] [--regex] [--invert] [--from-start]
  [--since <timestamp>] [--color] <file> [<file> ...]`
- Follows from end of file by default (like `tail -f`); `--from-start`
  reads existing content; `--filter` keeps only matching lines
- **`--regex`** — match by regular expression, not just plain substring
- **`--invert`** — show the lines that *don't* match, like `grep -v`
- **`--since <timestamp>`** — show only lines logged after a given time
- **Multi-file tail** — follow several files at once, prefixing each line
  with its source
- **`--color`** — highlight the matched portion of each line
- Match logic split into a testable library; unit tests plus integration
  tests over a real temp file

See [`README.md`](README.md) to run it.

## What's intentionally not built

Pick one of these and open a PR. (Or invent your own — these are a menu,
not a contract.)

### Line numbers
Prefix each printed line with its line number in the source file.

### `--tail <N>`
Print the last N matching lines before following (like `tail -n N`).

### JSON field extract
For JSON-per-line logs, match/print a specific field (e.g. `--field
level`) instead of the whole line.

### Reopen on rotate
Detect log rotation/truncation and reopen the file (like `tail -F`).

## How to contribute

Fork the repo, pick a feature above (or your own), and open a PR back to
your fork. Rami reviews it within about a minute.

This repo is for trying Rami — PRs here aren't merged.
