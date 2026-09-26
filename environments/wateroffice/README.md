# Wateroffice 0.1.0

Offline hydrometric station search, historical and realtime reports, maps, lists and downloads. Platform: Linux amd64.

## Install and run

```sh
python3 tools/env.py prepare wateroffice --release v0.1.3
python3 tools/env.py start wateroffice --release v0.1.3 --mode preview
python3 tools/env.py verify wateroffice --release v0.1.3
```

Open http://127.0.0.1:8084. For restricted evaluation, omit `--mode preview`; use the browser service through its existing bridge protocol. The web and browser containers are non-root, read-only and on an internal network. Preparation downloads data/images; supported workflows then run offline.

```sh
python3 tools/env.py reset wateroffice --release v0.1.3
python3 tools/env.py stop wateroffice --release v0.1.3
```

Reset clears session lists and browser downloads, retaining the data. Stop removes this deployment's containers and network. For a parallel preview, pass `--port 18084` on startup.

## Data

The dataset combines a 2,248-station catalog, HYDAT 2026-07-17 historical data, archived realtime observations, quality fields, station metadata, datum/reference pages, map resources and watch summaries. Station pages display the observation interval and source quality information. See [data sources and periods](DIFFERENCES.md) for snapshot details.

The compressed data archive is 407,458,840 bytes (about 389 MiB). Allow roughly 2 GiB for extracted runtime data plus image layers and download staging; Docker's shared base layers may already be present. Keep at least 5 GiB free during preparation. See [data coverage](DIFFERENCES.md) and [data preparation](BUILDING.md).

## Upgrade and rollback

Release manifests use separate state directories. Stop the running Wateroffice instance before assigning port 8084 to another version. Retain the old state and images. To roll back:

```sh
python3 tools/env.py stop wateroffice --release v0.1.3
python3 tools/env.py prepare wateroffice --release v0.1.2
python3 tools/env.py start wateroffice --release v0.1.2 --mode preview
```

The v0.1.2 manifest selects application `0.1.0-dev` and the original archive. Do not merge the old and new observation files manually. Other website environments are unchanged.
