# shortener — roadmap

A small URL shortener: long link in, short code out, click counts
tracked.

## What's built

The core slice: a stdlib `net/http` service over an in-memory store.

- `POST /shorten` → random base62 code + short URL
- `GET /{code}` → 302 redirect to the original, counting a click
- `GET /api/stats/{code}` → click stats
- URL validation, collision-retried code generation, a concurrency-safe
  store (`go test -race`), and httptest endpoint tests
- **Per-link expiration** — give a link an expiry, after which it stops
  resolving
- **Rate limiting** — throttle link creation per client IP
- **Custom slugs** — choose your own short code instead of a random one
- **Per-link click cap** — retire a link automatically after N clicks
- **Admin endpoint** — `GET /api/admin/links` lists every link with stats

See [`README.md`](README.md) to run it.

## What's intentionally not built

Pick one of these and open a PR. (Or invent your own — these are a menu,
not a contract.)

### Bulk shorten
Accept a list of URLs in one request and return all the short codes.

### QR code
Return a QR-code image (PNG or SVG) for a short link.

### Per-link password
Protect a link with a password that must be supplied to resolve it.

### Query passthrough
Forward query parameters (e.g. UTM tags) from the short URL onto the
destination on redirect.

## How to contribute

Fork the repo, pick a feature above (or your own), and open a PR back to
your fork. Rami reviews it within about a minute.

This repo is for trying Rami — PRs here aren't merged.
