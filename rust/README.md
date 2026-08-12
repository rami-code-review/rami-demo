# logtail

A live log tailer with built-in filtering — like `tail -f` and `grep` in
one small CLI. Point it at a file, watch new lines stream in, and keep
only the ones you care about.

Rust standard library only (plus a dev-only crate for tests). See
[`ROADMAP.md`](ROADMAP.md) for what's built and what's open to build.

## Run

Requires a recent stable Rust toolchain.

```bash
cd rust
cargo run -- --filter ERROR /var/log/app.log
```

By default `logtail` starts at the end of the file (like `tail -f`) and
prints new lines as they arrive, keeping only those containing the
`--filter` substring. Pass `--from-start` to read existing content first,
and omit `--filter` to keep every line.

```
logtail [--filter <substring>] [--from-start] <file>
```

Build and test with:

```bash
cargo build
cargo test
```

## Architecture

```
src/
  lib.rs   # arg parsing, the line-match predicate, and filter_available()
  main.rs  # opens the file, seeks to end, polls for new lines
tests/
  follow.rs  # integration tests over a real temp file
```

The reusable logic lives in `lib.rs`: `parse_args` turns argv into a
`Config`, `matches` decides whether one line passes the filter, and
`filter_available` reads every line currently available from any
`BufRead` and writes the matching ones out. Keeping that core free of
real file I/O is what makes it unit-testable; `main.rs` supplies the file
handle and the poll loop.

The pieces are deliberately small so a new feature has an obvious home:
the open [roadmap](ROADMAP.md) items (line numbers, `--tail <N>`, JSON
field extraction, reopen-on-rotate) each slot into the match predicate
plus the argument parser.
