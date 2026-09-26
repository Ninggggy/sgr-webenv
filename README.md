# SGR-WebEnv

Offline website environments accompanying SGR-BENCH. The environments combine website interfaces, fixed datasets and an isolated browser for interactive search, navigation and data queries.

[中文](README.zh-CN.md)

| Environment | Features | Port |
|---|---|---:|
| Census / ACS | ACS tables, geographic selection, maps and exports | 8081 |
| CDC WONDER | National natality and linked infant mortality queries | 8082 |
| arXiv | Metadata search, record details and category browsing | 8083 |
| Wateroffice | Station search, observations, maps and downloads | 8084 |
| Cellosaurus | Cell-line search, records, downloads and CLASTR | 8086 |
| NOAA Climate at a Glance | Climate queries, maps, time series and exports | 8080 |

## Run an environment

Use Linux amd64, Docker Engine with Compose v2 and Python 3.9+. Run from the repository root. Preparation downloads data and images; the prepared environment runs offline.

```sh
python3 tools/env.py prepare cellosaurus --release v0.1.3
python3 tools/env.py start cellosaurus --release v0.1.3 --mode preview
```

Open `http://127.0.0.1:8086`. Replace `cellosaurus` with `census`, `wonder`, `arxiv` or `wateroffice` and use the corresponding port. For NOAA, first follow the [chart dependency and local-build steps](environments/noaa/README.md).

```sh
python3 tools/env.py verify cellosaurus --release v0.1.3
python3 tools/env.py reset cellosaurus --release v0.1.3
python3 tools/env.py stop cellosaurus --release v0.1.3
```

`verify` checks service health. `reset` clears session state and downloads while retaining data. `stop` stops the environment. Use `--mode eval` for the isolated evaluation mode.

See [operation and resource requirements](docs/OPERATIONS.md) and [data details](docs/SCOPE.md). Code and component terms are listed in [LICENSE](LICENSE), [NOTICE](NOTICE) and [third-party notices](docs/THIRD_PARTY.md).
