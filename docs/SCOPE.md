# Features and data scope

Each environment serves a fixed archive. Use the release manifest and included source metadata to identify data versions and collection dates.

| Environment | Data and features | Dataset and usage |
|---|---|---|
| NOAA Climate at a Glance | Archived statewide/divisional climate queries, maps, time series, values and anomalies | 48 contiguous states and 344 climate divisions, 1895-01 through 2026-08. Prepare ZingChart separately. For exact-ranking tasks, consult the [numeric rules](../environments/noaa/PRECISION.md). |
| Census / ACS | ACS tables, E/M values, geographic selection, maps and customized downloads | Archived 2016–2019 ACS1/ACS5 regions and tables; national selection maps accompany the archived numerical data. See [sources](../environments/census/SOURCES.md) and [precision](../environments/census/PRECISION.md). |
| CDC WONDER | National U.S.-resident Natality 2016–2024 and Period Linked 2017–2023 queries, charts and exports | National queries with the fields in [COVERAGE](../environments/wonder/COVERAGE.md). [Protection rules](WONDER_PROTECTION_REVIEW.md) apply to results and exports. |
| arXiv | 1,685,244 cs/math/stat records, latest metadata, 2,787,373 version timestamps, search and year/month browsing | Metadata search, latest-record details, submission timelines and year/month category lists. |
| Wateroffice | HYDAT 2026-07-17, a 2,248-station catalog, archived realtime observations and quality fields, station metadata, maps and downloads | Historical and realtime sources have separate dates. Map areas and observation fields are described in [the data guide](../environments/wateroffice/DIFFERENCES.md). |
| Cellosaurus | Release 56.0: 168,970 records, core website and CLASTR, plus separate Release 53/54 name-conflict archives | Record browsing, search, downloads and CLASTR workflows. See [the environment guide](../environments/cellosaurus/README.md). |

arXiv retains every category assigned to an included record, including cross-listings. First submission, latest submission, first-announcement month and source update times have distinct meanings. Relative-date queries use the archive's reference date.

Each release provides a fixed dataset for repeatable experiments. Prepare a separate dataset to use a different source date.
