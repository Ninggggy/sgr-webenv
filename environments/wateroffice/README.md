# Wateroffice

Hydrometric station search, historical and realtime observations, maps and downloads.

From the repository root:

```sh
python3 tools/env.py prepare wateroffice --release v0.1.4
python3 tools/env.py start wateroffice --release v0.1.4 --mode preview
```

Open http://127.0.0.1:8084/. Use `verify`, `reset` and `stop` with the same environment and release. Use `--mode eval` for the isolated browser. See [operation instructions](../../docs/OPERATIONS.md).
