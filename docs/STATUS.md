# Release preparation status

Version: **v0.1.0 candidate**, updated 2026-09-26. Repository and data Release
remain private/draft. All 11 non-NOAA images passed authenticated GHCR pulls;
anonymous downloads and pulls have not passed yet. Package visibility is
independent of repository visibility: see [publication steps](PUBLICATION.md).

## What is verified

| Environment | Independent packaged-install evidence | Remaining limits |
|---|---|---|
| Census 0.2.1 | 25 table exports; exact-fraction reconstruction of eight CG/GO; 36 customization checks; CSV/Excel comparison; lifecycle/isolation pass. Actual draft-Release archive downloaded and installed in a second clean directory; all 25 exports and eight exact-fraction answers passed again. | Declared partial geographic/product coverage and visual differences; anonymous installation pending. |
| arXiv 0.1.0 | Fresh complete index of 1,685,244 records; source archive has 2,787,373 version rows. 100 background papers, 40 exploration queries, 14 calendar/navigation actions and 23 HTTP feature-boundary checks pass. Three-record rebuild succeeds and partial-index startup is refused. | All eight records passed information replay: 1,860 candidate detail visits over 76 result pages. Reset/restart and full-index persistence checks passed. Visual differences remain documented; anonymous installation pending. |
| WONDER 0.3 | 70 webpage queries; four CG/GO and 48 source-count checks pass in an independent private install; session reset, isolation and restart pass. | Raw databases withheld for unresolved small-cell redistribution review. No complete public install. |
| Wateroffice 0.1.0-dev | 41 information-access checks across five workflows; session reset, isolation and restart pass. Downloaded Release archive passed required-file and SQLite checks. | Development release, replacement basemap and documented coverage/visual limits; no full visual or autonomous-task acceptance. |
| NOAA 2 | Data archive downloaded and validated. Source and upstream notices prepared. | Proprietary ZingChart absent; no released image or complete install. New packaged-browser replay is not claimed. Rank/tie differences remain. |

Reports are in [verification](verification/). These are webpage and data checks,
not newly measured autonomous model success rates. 34 records are included as
author-side regression inputs, but **not all 34 have passed packaged acceptance**.
No task files or author evidence are mounted in runtime containers.

## Build, downloads and privacy

The full shared runtime/browser dependency chain and four non-NOAA image families
were built and uploaded using a temporary self-hosted Actions runner. All 11
images pulled with authentication are Linux amd64 and associated with this
repository (`verification/registry-pulls.json`). The runner is unregistered and
its registration credentials removed. No metered hosted build was used.

Four datasets are uploaded as five private draft assets. arXiv is split below
GitHub's per-asset limit and rebuilt locally into a search index. Downloaded
archives were safely extracted and checked independently. WONDER data is absent.
The source whitelist excludes deployment histories, private credentials, raw
author research material and the proprietary chart library. A bounded scan of
2,995 tracked files found no tested credential/personal-path patterns; a recursive
scan of 12,644 packaged JSON files found none of the tested author-answer,
credential or personal-path patterns. These checks are not an exhaustive security
or legal audit. Main history was cleaned of inadvertently copied withheld files;
a direct read-only check confirmed the excluded chart library remains retrievable through an old GitHub commit. The affected repository was renamed to private staging with user authorization. This repository is a new independent clean snapshot; the excluded old commit and file are not retrievable here. Data assets are being migrated; unchanged validated images use new `sgr-webenv-release-*` packages because the new repository token cannot access the old private packages. See `PUBLICATION.md`.

## Resource measurements and failed attempts

Server root must retain **5 GiB**, as revised by the user. Existing deployments
and unrelated user data remain unchanged. Only existing/free resources are used.
The native validation directory is independent of production. arXiv's fresh
index occupies about 4.6 GiB in a host RAM-backed directory. This is a measured
index size, not a minimum-memory claim. The public configuration uses persistent
disk, an 8 GiB search-container limit and 2 GiB Java heap; full-build memory on
that disk-backed configuration is not established by the RAM-backed test.

The first author index attempt used a 16 GiB container tmpfs with an 8 GiB memory
limit and was OOM-killed. The successful retry used a host RAM directory and a
24 GiB container bound. A small-index test first failed because its author fixture
omitted `harvest_state`; the corrected fixture built three documents. A partial
index was refused, and the full index was untouched. No failure was hidden by
serving partial results or relaxing isolation.

Local ARM emulation could not launch the Chromium sandbox, so behavioral tests
used native Linux amd64. One Census harness attempt launched duplicate browsers
and hit the existing 256-process limit; the corrected harness used one browser
without changing that limit. The independent source data and production services
were preserved throughout.

## Remaining publication work

arXiv full replay and lifecycle checks are complete. Keep NOAA/WONDER incomplete status explicit. Set final Release tag/URLs
only when publishing. Verify repository, assets and every applicable GHCR package
anonymously after visibility changes. Current private download success does not
substitute for that check. See [operations and rollback](OPERATIONS.md).

Visual comparison details and a non-answer form screenshot pair are in [VISUAL_CHECKS](VISUAL_CHECKS.md).

Point-in-time memory and unpacked data sizes are recorded in `verification/resource-observations.json`; they are not peak-install or minimum hardware requirements. The four runnable environments also passed 24 direct private-path requests (`verification/private-paths.json`).
