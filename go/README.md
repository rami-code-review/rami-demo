# shortener

A small URL shortener. Turn a long link into a short code, follow the
short code back to the original, and count how many times each link was
clicked. A self-hostable bit.ly in a few hundred lines.

It's a small HTTP service (Go standard library, no dependencies) over an
in-memory store. See [`ROADMAP.md`](ROADMAP.md) for what's built and
what's open to build.

## Run

Requires Go 1.22+.

```bash
cd go
go run .        # listens on :8080 (set ADDR to change, BASE_URL for short links)
```

Then, in another terminal:

```bash
# shorten a URL
curl -X POST localhost:8080/shorten \
  -H 'Content-Type: application/json' \
  -d '{"url": "https://example.com/some/very/long/path"}'
# => {"code":"aB3xY9z","short_url":"http://localhost:8080/aB3xY9z"}

# follow the short code (302 redirect to the original, counts a click)
curl -i localhost:8080/aB3xY9z

# click stats for a code
curl localhost:8080/api/stats/aB3xY9z
```

Test with:

```bash
go test ./...
```

## API

| Method | Path | Description |
|---|---|---|
| `POST` | `/shorten` | Shorten a URL (`{ "url": "..." }`) → `{ code, short_url }` |
| `GET` | `/{code}` | Redirect (302) to the original URL; counts a click |
| `GET` | `/api/stats/{code}` | Click stats for a code (404 if unknown) |

The URL must be an absolute `http`/`https` URL. Codes are random base62,
seven characters long.

## Architecture

```
code.go      # random base62 code generation (crypto/rand)
store.go     # in-memory, mutex-guarded link store: create, resolve, stats
handlers.go  # HTTP routes, JSON encoding, URL validation
main.go      # wires the store to a server and listens
*_test.go    # store unit tests + httptest endpoint tests
```

Codes are generated with `crypto/rand` and retried on the (vanishingly
rare) collision. The store is guarded by a mutex so concurrent requests
are safe — `go test -race` covers this. The pieces are deliberately small
so a new feature has an obvious home: the open [roadmap](ROADMAP.md) items
(bulk shorten, QR codes, per-link passwords, query passthrough) each slot
into `store.go` plus a handler in `handlers.go`.
