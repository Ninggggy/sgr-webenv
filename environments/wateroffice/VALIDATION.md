# Wateroffice snapshot validation

The thirty-day upgrade is validated for the declared station subset; see the [release report](../../reports/wateroffice-0.1.0/README.md). The user-approved scope is 483 upgraded stations; other stations retain their existing seven-day observations. The previously published development snapshot remains available for rollback.

## Collect and verify source data

Use the released data directory as `OLD_DATA`. `stations.json` lists the selected upgrade stations from the 2,248-station real-time catalog. The complete catalog and existing observations are preserved. Run the collector on an author machine with working HTTPS access to Wateroffice; do not mount these programs or author reports into the evaluation container.

```bash
python environments/wateroffice/tools/collect_realtime_month.py \
  --data OLD_DATA --output WORK/realtime --station-list stations.json
python environments/wateroffice/tools/verify_realtime_month.py \
  --data WORK/realtime --original OLD_DATA --station-list stations.json
```

The collector uses two workers and seven-day segments, with bounded retries and shorter segments after transport failures. It resumes complete requests. A response without a final newline is valid if HTTP transport and every CSV record are complete. Conflicting boundary observations are rejected. Official access refusals stop further acquisition; do not increase concurrency or rotate identities to bypass them.

The verifier checks station and parameter scope, segment continuity, duplicates and source values, and reports changes relative to the original snapshot. Only successful verification writes the runtime `window.json`, including the upgraded station list and the retained legacy window for a partial upgrade. Official empty observations, unpublished parameters and failed collection are separate outcomes.

Select source-check stations before inspecting results. Compare one complete local day against the official graph service:

```bash
python environments/wateroffice/tools/verify_realtime_source.py \
  --data WORK/realtime --original OLD_DATA --station-list sample-stations.json \
  --reference WORK/reference --report WORK/source-check.json
```

Use the initial twelve stratified samples plus at least thirty additional stations within the published upgrade subset. Cached reference responses retain their request URLs and acquisition times. `--fetch-only` saves reference responses but does not validate the runtime data. Values are compared at the published CSV precision. Internal graph approval codes are not inferred from CSV labels; published Provisional/Final status, Grade and Qualifiers are checked separately.

## Browser checks

The browser programs are author-side Playwright tests, separate from the restricted agent RPC. They need a Playwright installation and the pinned Chromium executable. Set `PLAYWRIGHT_MODULE` and `CHROMIUM_PATH` if these are not available through the defaults. Use `WATEROFFICE_ORIGIN` for the local service and `WATEROFFICE_OUTPUT` for screenshots and reports.

```bash
node environments/wateroffice/tools/check_workflows.cjs
node environments/wateroffice/tools/check_month_ui.cjs
python -m unittest discover -s tests
```

The monthly checks cover 1440×1000, 1280×800 and 390×844. The existing workflow suite accepts `VIEWPORT_WIDTH`, `VIEWPORT_HEIGHT` and an optional comma-separated `TESTS` selection for focused regression. A full-width mobile map popup is expected to remain inside the viewport after a drag; desktop popups have space to move horizontally.

Compare the original and local pages in matching content and control states. Wait for table, graph and map loading to finish before taking screenshots. The agreed Leaflet/Toporama basemap exception does not waive popup, filtering or download checks. Record source checks, deterministic legacy-task replays and browser interaction results separately; none measures autonomous model success.

## Package without copying HYDAT

After every declared upgrade station and its independent checks pass, reuse the immutable earlier public archive:

```bash
python tools/package_wateroffice_month.py \
  --base-archive wateroffice-data-v0.1.0.tar.gz \
  --realtime WORK/realtime --verification WORK/month-verification.json \
  --output wateroffice-data-30d.tar.gz
```

This streams unchanged historical and static members into the new archive and replaces observations only for upgraded stations. Other observations and legacy daily means remain available. It does not unpack or rewrite HYDAT. It excludes collection scratch files, logs and author task materials. Keep at least 5 GiB free on the server throughout validation and deployment.

Before release, perform clean installation, offline restricted-browser checks, reset/restart tests, the ten legacy CG/GO records, all 41 information checks and the 29 existing interaction workflows against the final package. A successful sample test does not establish completeness of the published subset, and a partial upgrade is never described as national thirty-day coverage. Retain the prior application and data for rollback.
