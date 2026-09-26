# Cellosaurus

Cell-line search, record browsing, linked entities, downloads and CLASTR STR matching. The dataset contains Cellosaurus Release 56.0, with separate Release 53/54 name-conflict files.

## Run

From the repository root:

```sh
python3 tools/env.py prepare cellosaurus --release v0.1.3
python3 tools/env.py start cellosaurus --release v0.1.3 --mode preview
```

Open `http://127.0.0.1:8086/`; CLASTR is at `/str-search/`. Use `verify`, `reset` and `stop` with the same release parameter. For evaluation, use `--mode eval`.

## Prepare data from source

Place the archived Release 56.0 source files in this environment's `data/` directory and run `python3 tools/import_data.py`. Keep Release 53/54 files in their separate history directories. Source URLs are recorded in `sources.json` and `history/sources.json`.

See [resource requirements](../../docs/OPERATIONS.md), [search and export behavior](docs/repair-evidence.md), and [component notices](licenses/NOTICE.md).
