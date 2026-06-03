# logtail — roadmap

A live log tailer with filtering: follow a file like `tail -f`, keep only
the lines that match.

## What's built

The core slice: a stdlib-only CLI that follows a file and filters lines.

- `logtail [--filter <substring>] [--from-start] <file>`
- Follows from end of file by default (like `tail -f`); `--from-start`
  reads existing content; `--filter` keeps only matching lines
- Match logic split into a testable library; unit tests plus integration
  tests over a real temp file

See [`README.md`](README.md) to run it.

## What's intentionally not built

Pick one of these and open a PR. (Or invent your own — these are a menu,
not a contract.)

### `--since <timestamp>`
Show only lines logged after a given time.

### Regex mode
Match lines by regular expression, not just plain substring.

### `--invert`
Show the lines that *don't* match, like `grep -v`.

### Multi-file tail
Follow several files at once, prefixing each line with its source.

### Color highlighting
Highlight the matched portion of each line in color.

## How to contribute

Fork the repo, pick a feature above (or your own), and open a PR back to
your fork. Rami reviews it within about a minute.

This repo is for trying Rami — PRs here aren't merged.
