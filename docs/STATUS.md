# Release preparation status

Version: **v0.1.2**, updated 2026-09-26. Census, arXiv and WONDER are distributed
within their declared scope; Cellosaurus is added with core website/CLASTR scope; Wateroffice remains 0.1.0-dev. NOAA uses a user-supplied chart dependency and local source build; no bundled NOAA image is published. All 14 images now pass
anonymous pulls. Public package pages display the correct new repository link.
Public data URL checks have passed; see `verification/anonymous-publication.json`
for the latest result (earlier failure reports are historical, not new acceptance).

## What is verified

| Environment | Independent packaged-install evidence | Remaining limits |
|---|---|---|
| Census 0.2.1 | 25 table exports; exact-fraction reconstruction of eight CG/GO; 36 customization checks; CSV/Excel comparison; lifecycle/isolation pass. Actual draft-Release archive downloaded and installed in a second clean directory; all 25 exports and eight exact-fraction answers passed again. | Declared partial geographic/product coverage and visual differences; independent-machine installation not claimed. |
| arXiv 0.1.0 | Fresh complete index of 1,685,244 records; source archive has 2,787,373 version rows. 100 background papers, 40 exploration queries, 14 calendar/navigation actions and 23 HTTP feature-boundary checks pass. Three-record rebuild succeeds and partial-index startup is refused. | All eight records passed information replay: 1,860 candidate detail visits over 76 result pages. Reset/restart and full-index persistence checks passed. Visual differences remain documented; independent-machine installation not claimed. |
| WONDER 0.3 | 70 webpage queries; four CG/GO and 48 source-count checks pass in an independent private install; session reset, isolation and restart pass. | Source-specific review completed; national public-use-derived data carry NCHS usage conditions. 16 consistent database copies retain every runtime row; 70 packaged query replays match earlier browser exports. |
| Wateroffice 0.1.0-dev | 41 information-access checks across five workflows; session reset, isolation and restart pass. Downloaded Release archive passed required-file and SQLite checks. | Development release, replacement basemap and documented coverage/visual limits; no full visual or autonomous-task acceptance. |
| Cellosaurus 0.1.0 (web packaging 0.1.0-1) | Full 168,970-record source reconciliation; 40 official queries plus four full partitions; 337 source-to-HTTP checks; 15 RPC and 60 interaction checks; four supplementary author replays (89 raw records); reset/restart, private paths and isolation pass. Three new images anonymously pull and link to this repository. | Not complete REST/RDF/SPARQL or pixel-equivalent; original equal-name ties, large-result truncation and STR display-name differences remain documented. Preview streams large files within 128 MiB after fixing an initial OOM. |
| NOAA 2 | Data archive downloaded and validated. Source and upstream notices prepared. | User-supplied ZingChart and a local build are required; see the NOAA setup guide. No bundled image or newly verified clean-install/browser replay is claimed. Rank/tie differences remain. |

Reports are in [verification](verification/). These are webpage and data checks,
not newly measured autonomous model success rates. 34 records are included as
author-side regression inputs, but **not all 34 have passed packaged acceptance**.
No task files or author evidence are mounted in runtime containers.

## Build, downloads and privacy

The shared runtime/browser dependency chain and four non-NOAA image families
were built and migrated using a temporary self-hosted Actions runner. All 11
new packages pulled successfully and are Linux amd64, with unchanged image
content (`verification/image-migration.json`, `verification/registry-pulls.json`).
Earlier REST/GraphQL association checks were inconclusive. After public visibility
was enabled, all 11 package pages displayed the new repository link and no staging
repository link. Anonymous pulls passed with an empty Docker credential directory.
See `verification/public-package-pages.json` and `verification/anonymous-publication.json`.

Migration run `36177201820` succeeded. Verification runs `36179035281` and
`36179277485` pulled every image but failed the association check. The temporary
runner was then unregistered; GitHub reports zero runners, and local runner
registration credentials were removed. No metered hosted build was used.

Four datasets are provided as five Release assets. arXiv is split below
GitHub's per-asset limit and rebuilt locally into a search index. Downloaded
archives were safely extracted and checked independently. The initial v0.1.0 omitted WONDER data; v0.1.1 adds its reviewed archive.
The source whitelist excludes deployment histories, private credentials, raw
author research material and the proprietary chart library. A bounded scan of
2,995 tracked files found no tested credential/personal-path patterns; a recursive
scan of 12,644 packaged JSON files found none of the tested author-answer,
credential or personal-path patterns. These checks are not an exhaustive security
or legal audit. Main history was cleaned of inadvertently copied withheld files;
a direct read-only check confirmed the excluded chart library remains retrievable through an old GitHub commit. The affected repository was renamed to private staging with user authorization. This repository is a new independent clean snapshot; the excluded old commit and file are not retrievable here. All five cleared data assets have been migrated and compared byte-for-byte with the validated archives (`verification/release-migration.json`); unchanged validated images have been uploaded to new `sgr-webenv-release-*` packages because the new repository token cannot access the old private packages. See `PUBLICATION.md`.

## Resource measurements and failed attempts

Server root must retain **5 GiB**, as revised by the user. Existing deployments
and unrelated user data remain unchanged. Only existing/free resources are used.
The native validation directory is independent of production. arXiv's fresh
index occupies about 4.6 GiB in a host RAM-backed directory. This is a measured
index size, not a minimum-memory claim. The public configuration uses persistent
disk and now adopts the successful test's 24 GiB search-container bound with a
2 GiB Java heap. This replaces the unverified 8 GiB default. Minimum memory and
full-build peak on persistent disk are not established by the RAM-backed test.

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

## Distribution boundaries

NOAA remains incomplete. WONDER is released within its documented national scope. Public data and image access checks are separate
from the earlier native isolated-install tests. The Docker daemon may reuse
cached layers, and this is not a second-machine clean install. Public access does
not change Wateroffice's development maturity or any documented website differences.
See [operations and rollback](OPERATIONS.md).

Visual comparison details and a non-answer form screenshot pair are in [VISUAL_CHECKS](VISUAL_CHECKS.md).

Point-in-time memory and unpacked data sizes are recorded in `verification/resource-observations.json`; they are not peak-install or minimum hardware requirements. The four runnable environments also passed 24 direct private-path requests (`verification/private-paths.json`).

## Public access verification

The final source, five data URLs and 11 image-pull checks all pass anonymously
(`verification/anonymous-publication.json`). All 11 package pages resolve to
`Ninggggy/sgr-webenv/pkgs/container/...`, confirming the correct association
(`verification/public-package-pages.json`). The previous zero-, eight- and
nine-image intermediate results are superseded. Immediately after publishing,
some asset URLs briefly returned 404; subsequent checks returned 200 with the
expected sizes. Full streamed comparisons are recorded in
`verification/anonymous-asset-content.json`.

An unauthenticated clone of the published `v0.1.0` tag succeeded. Its six
distribution-tool tests passed, with Census/arXiv/Wateroffice marked `ready` and
NOAA/WONDER explicitly blocked in that historical v0.1.0 tag. The v0.1.1 manifest enables WONDER after the completed source-specific review. `ready` describes available installation
materials, not complete website parity or a change to Wateroffice's maturity.
The older staging repository remains private and no temporary Actions runner is
registered. No original production website was changed during publication.

## WONDER data review and v0.1.1

The [completed review](reviews/WONDER_DATA_REDISTRIBUTION.md) distinguishes NCHS
national public-use computational data from WONDER output restrictions. This
release preserves NCHS usage conditions and agency attribution, not an
unrestricted-data license. All 16 SQLite copies retain every original runtime
row; 70 query results match previously validated browser exports. The website's
suppression and conservative parent protection are unchanged. Packaged metadata
omits author marginal tables/timings and retains all runtime catalog fields.

Existing images and other sites' v0.1.0 data assets are reused. No original
production service or original dataset was changed. See `wonder-data-release.json`
and `wonder-packaged-queries.json` under verification.

WONDER's 34,507,734-byte v0.1.1 archive passed anonymous full-download byte
comparison. A fresh independent native installation from the public source/data
archives and exact public images passed health, browser isolation, reset/restart
and six private-path checks. All 70 query replays also matched under the actual
public image. Direct GitHub downloads on the server timed out and its registry
proxy was unavailable, so anonymously obtained public artifacts were transferred
from the author machine. No global proxy or original service was changed. This
is same-server isolated acceptance, not an independent-machine/direct-download
claim. The temporary v0.1.1 acceptance containers were stopped afterward.
See `verification/wonder-v011-install.json` and `wonder-anonymous-data.json`.

Cellosaurus detailed acceptance: [report](verification/cellosaurus-acceptance-v0.1.2.json). The post-publication anonymous data-download report is attached to the v0.1.2 Release. Original services and earlier release tags remain unchanged.

## WONDER protection recheck — 2026-09-26

All 17 recorded parent visibility differences were independently reproduced from the original archive and classified as retained additional ancestor protection. No arithmetic or propagation-scope error was found in the tested cases. Ten independent cause-query cases, eight synthetic tests, 70 browser/export replays and four CG/GO regressions pass. Application 0.3 and data remain unchanged. See the [itemized review](WONDER_PROTECTION_REVIEW.md).

## NOAA manual dependency setup — 2026-09-26

The README now labels NOAA **Available · manual dependency setup**, referring to source/data availability plus the [user-supplied dependency route](../environments/noaa/README.md). The official npm package 2.9.16-1 was successfully retrieved and its module entry checked. The chart library and NOAA images containing it are not redistributed. Historical manifests, existing acceptance findings, and public image availability remain unchanged. This documentation change is not a new clean-install or chart-rendering acceptance result.
