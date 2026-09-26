# Cellosaurus

Cell-line search, record browsing, downloads and CLASTR STR matching.

From the repository root:

```sh
python3 tools/env.py prepare cellosaurus --release v0.1.4
python3 tools/env.py start cellosaurus --release v0.1.4 --mode preview
```

Open http://127.0.0.1:8086/. Use `verify`, `reset` and `stop` with the same environment and release. Use `--mode eval` for the isolated browser. See [operation instructions](../../docs/OPERATIONS.md).

CLASTR is at `/str-search/`. See [component notices](licenses/NOTICE.md).
