# Wateroffice 0.1.0 validation — 2026-09-26

Scope: supported English Wateroffice workflows, unchanged HYDAT/catalog/static resources, and a user-approved **483-station** thirty-day upgrade. The remaining **1,765 catalog stations** retain their prior data. Collection was stopped deliberately; two incomplete scratch stations are excluded. No nationwide thirty-day completeness claim is made.

## Results

| Check | Result |
|---|---|
| Declared thirty-day subset | 483/483 stations; 7,405,038 observations; no failed or conflicting segments |
| Initial source sample | 12 stratified stations; 44 graph/CSV checks; 12 rendered table/no-data checks |
| Additional source sample | 30 stations within the release subset; 111 checks passed |
| CSV/TXT/XML values and timestamps | 132 endpoint comparisons passed; published unit-value quality fields compared |
| Old task information | All ten CG/GO records retain their information paths; 41 restricted-browser checks passed |
| Existing interactions | 29 workflows passed |
| Monthly/responsive interactions | 24 checks across 1440×1000, 1280×800 and 390×844 passed |
| Isolation/reset | 13 checks passed on the application image, repeated after container restart |
| Unit tests | 30 passed |
| Archive preservation | 17,257 unchanged members / 1,421,471,881 bytes identical to the previous public archive |
| Fresh extraction | 18,226 files extracted; SQLite validation passed; 24.4 seconds on the author Docker VM |

Browser replays establish deterministic information and interaction compatibility, not model autonomous success. Task answers and author source archives are not mounted or packaged. The five base workflows cover both corresponding CG and GO records; no benchmark answers were modified.

## Source revisions and status

Against the original seven-day unit-value snapshot, 1,656,507 values agree at official CSV precision, 49,153 are revised, 1,993 old observations are absent and 13,214 are additional. New-source observations replace the whole station snapshot; status fields are never spliced onto old values. These source revisions do not alter the verified historical/catalog task information.

Official CSV precision can be lower than the graph service's internal precision. Published status labels are used directly; internal approval codes are not guessed. Blank Grade/Qualifiers remain blank. Empty sample stations were verified against the original site's explicit no-data message. The 30-day interval may contain genuine gaps and partial first/last local dates.

## Visual review and fixes

Search, realtime table/graph, station list, download and map states were compared at all three viewports, including control inventories and rendered screenshots. Historical report modes are covered by the existing interaction regression. Fixes include single-daily-parameter table sorting, full local-standard-time names, non-wrapping timestamps, no-data feedback, source-aware quality labels, quick-graph date ranges and original download-product order.

The short per-station coverage notice is a deliberate offline addition and can shift content downward on mobile. Leaflet/Toporama, map control placement and the captured zoom coverage remain agreed differences; Google Maps, satellite/terrain and new high-resolution tiles are excluded. Mobile map popups remain within the viewport; table content can scroll horizontally where the original table requires it. The report does not claim pixel identity or support for excluded external pages.

## Installation evidence

The archive was extracted into a fresh Docker volume and validated with the public installer's extraction/database routines. The release image serves this data without a source-code bind mount. Native Linux amd64 image behavior, browser isolation and restart were checked on the deployment server; the independent extraction used a Linux amd64 container on a macOS arm64 host. Server validation reused verified unchanged historical/static files through hardlinks to avoid a second HYDAT copy. No server-private dependencies are included in the public package.

Both Linux amd64 images were pulled anonymously using an empty Docker credential configuration; their image IDs match the tested images. [Build and publication workflow](https://github.com/Ninggggy/sgr-webenv/actions/runs/36222256971). The public data download is verified after the release becomes visible. The shared prepare/start/verify/reset commands passed on native Linux using the verified runtime files, and its installed restricted browser passed all 13 isolation checks. The new preview uses loopback port 8084. The prior development application and archive remain available for rollback.
