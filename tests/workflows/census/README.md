# Author-side Census regression

Run these deterministic workflow checks in a separate test environment.

`customization.cjs` runs in a dedicated browser test container with the same
Chromium sandbox and network policy. Do not launch it beside an already running
RPC browser in the same 256-process container. It produces `/tmp/repair021-second`
with rendered table observations and ordinary CSV/Excel/ZIP downloads.
Export that directory before recreating the container, then run:

```sh
python3 tests/workflows/census/verify_exports.py /path/to/exported-directory
```

`verify_legacy.py` independently reconstructs the four task results using exact
fractions from ordinary downloaded table ZIPs and compares all eight CG/GO records
in `benchmark/`. It takes a directory containing the 25 `YYYY-TABLE.zip` exports:

```sh
python3 tests/workflows/census/verify_legacy.py /path/to/legacy-table-exports
```

`export_legacy.cjs` performs the 25 normal table ZIP downloads used by
`verify_legacy.py`. In a dedicated author browser container using the same
sandbox/network limits, place `export_jobs.json` at `/tmp/legacy-jobs.json`, then
execute the script with `/usr/local/lib/python3.10/dist-packages/playwright/driver/node` (the bundled Playwright Node runtime). Do not start a second Chromium inside the running
RPC container. Downloads are written to `/tmp/oldtasks`; export that directory
with `docker exec <author-container> tar -C /tmp -cf - oldtasks` before stopping
the temporary container. The input contains table/geography requests, not answers.
Use `verify_legacy.py /path/to/oldtasks` on the host for independent exact-fraction
reconstruction against the repository's current eight records.
