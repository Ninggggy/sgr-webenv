# Wateroffice

Hydrometric station search, historical and realtime observations, maps, saved lists and downloads. The data combine a 2,248-station catalog, HYDAT historical observations and archived realtime sources.

## Run

From the repository root:

```sh
python3 tools/env.py prepare wateroffice --release v0.1.3
python3 tools/env.py start wateroffice --release v0.1.3 --mode preview
```

Open `http://127.0.0.1:8084`. Use `verify`, `reset` and `stop` with the same release parameter. For evaluation, use `--mode eval`.

Station pages show observation periods and quality information. See [data details](DIFFERENCES.md), [data preparation](BUILDING.md), and [resources and version switching](../../docs/OPERATIONS.md).
