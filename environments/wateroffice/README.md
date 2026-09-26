# Wateroffice 0.1.0

Offline hydrometric station search, historical and realtime reports, maps, lists and downloads. Linux amd64 is the validated platform.

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

The 2,248-station realtime catalog is retained. **483 stations** have official CSV observations from **2026-08-26 09:40 UTC to 2026-09-25 09:40 UTC**, with published Approval, Grade and Qualifiers. The other **1,765 stations** retain the original seven-day GeoMet observations and separately dated daily means; unit Approval/Grade are unavailable in that source. The report and coverage page identify each station's available interval. This is a fixed, partly upgraded dataset, not a nationwide thirty-day capture.

HYDAT 2026-07-17, station metadata, datum/reference pages, map resources and watch summaries are retained. Official no-data observations and blank quality fields remain empty. Watch summaries have their own capture times. No new status is attached to an old observation.

The compressed data archive is 407,458,840 bytes (about 389 MiB). Allow roughly 2 GiB for extracted runtime data plus image layers and download staging; Docker's shared base layers may already be present. The server-side validation preserved at least 5 GiB free. See [validation results](../../reports/wateroffice-0.1.0/README.md), [coverage](DIFFERENCES.md) and [rebuild/tests](VALIDATION.md).

## Upgrade and rollback

Release manifests use separate state directories. Stop the running Wateroffice instance before assigning port 8084 to another version. Retain the old state and images. To roll back:

```sh
python3 tools/env.py stop wateroffice --release v0.1.3
python3 tools/env.py prepare wateroffice --release v0.1.2
python3 tools/env.py start wateroffice --release v0.1.2 --mode preview
```

The v0.1.2 manifest selects application `0.1.0-dev` and the original archive. Do not merge the old and new observation files manually. Other website environments are unchanged.
