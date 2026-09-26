# arXiv HTTP scope regression

Run the standard-library script through the isolated web container's loopback
HTTP interface using `docker exec -i <web-container> python3 < http_scope.py`.
It exercises existing website/API/citation paths only. No answer interface is
introduced and no benchmark file is mounted.

Expected statuses distinguish unsupported historical/identifier/fulltext features
(501), unknown versions (404), and out-of-scope categories (503). The historical
submission-date example comes from the existing source record, not its identifier.

## Restricted-browser workflow replay

From the repository root on the Docker host, after starting an isolated arXiv
installation:

```sh
python3 tests/workflows/arxiv/replay.py \
  --container sgr-arxiv-v0-1-0_browser_1 \
  --all-candidates --output /path/to/author-evidence/arxiv
```

This author-side script reads the eight records from `benchmark/`; none are
copied into a runtime container. It enumerates every result page, checks all
candidate detail pages, and compares required visible fields against those
existing records. It checks access to the information required by each task. The search intentionally uses
an inclusive superset around UTC date boundaries; source-based task adjudication
must apply the exact rubric afterward.

The trace helper saves completed browser evidence before removing its temporary
duplicates to keep the sandbox's bounded `/tmp` usable. It checks archive
readability first and does not clear webpage state. Keep at least 6 GiB free in
the output filesystem. `--tasks arxiv_001` selects a workflow; `--resume` skips
completed workflows, not partially traversed candidates. Run one driver at a time
against a browser container.

The fixed non-answer sample and exploration queries can also be repeated:

```sh
python3 tests/workflows/arxiv/background.py --container sgr-arxiv-v0-1-0_browser_1 --output /path/to/evidence/background.json
python3 tests/workflows/arxiv/export_browser_evidence.py --container sgr-arxiv-v0-1-0_browser_1 --output /path/to/evidence/traces
python3 tests/workflows/arxiv/exploration.py --container sgr-arxiv-v0-1-0_browser_1 --output /path/to/evidence/exploration.json
```

These scripts check rendering and resource availability.
The background IDs are listed in `background_ids.json`. Reset the
browser before long independent batches or export evidence between batches.

`boolean_search.py` can be passed through `docker exec -i <web-container>
python3 -` in the same way as `http_scope.py`. It exhausts pagination for two
ordinary terms over a fixed month and verifies AND/intersection, OR/union and
NOT/difference. This checks the consistency of search set operations.
