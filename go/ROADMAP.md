# shortener — roadmap

A small URL shortener: long link in, short code out, click counts
tracked.

## What's built

_(Nothing yet — the app is being scaffolded. This list fills in as the
core slice lands.)_

## What's intentionally not built

Pick one of these and open a PR. (Or invent your own — these are a menu,
not a contract.)

### Custom slugs
Let the user choose their own short code instead of a random one.

### Per-link expiration
Give a link an expiry time, after which it stops resolving.

### Per-link click cap
Cap a link at N clicks, then retire it automatically.

### Rate limiting
Throttle link creation per client IP to curb abuse.

### Admin endpoint
A simple endpoint listing every link with its click stats.

## How to contribute

Fork the repo, pick a feature above (or your own), and open a PR back to
your fork. Rami reviews it within about a minute.

This repo is for trying Rami — PRs here aren't merged.
