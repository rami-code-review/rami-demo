# logtail — roadmap

A live log tailer with filtering: follow a file like `tail -f`, keep only
the lines that match.

## What's built

_(Nothing yet — the app is being scaffolded. This list fills in as the
core slice lands.)_

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
