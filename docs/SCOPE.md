# Supported scope and known differences

The following describes existing website implementations. It is not a claim that
newly packaged containers have passed release acceptance.

| Site | App | Supported scope | Known differences |
|---|---|---|---|
| NOAA | 2 | Archived Climate at a Glance queries, values and anomalies | Rank/tie mismatches remain, including boundary windows. Do not use unresolved Rank paths as exact-parity tasks. |
| Census / ACS | 0.2.1 | Archived tables, years and geographies; corrected 002/004 definitions | Not nationwide all-product coverage; 95 median investigations and complete visual equivalence deferred. |
| WONDER | 0.3 | Resident national natality 2016–2024 and linked 2017–2023 fields in the archive | 17 parent-category visibility differences and stronger suppression propagation retained. Natality 2021 cannot separately resolve Dominican versus Other/Unknown Hispanic; only verified coarser/unambiguous queries are supported. No fabricated local geography data. |
| arXiv | 0.1.0 | 1,685,244 current cs/math/stat records, 2,787,373 version timestamps, search/latest details/monthly browsing | Historical content/citations/search, daily new/recent/catchup, incomplete author identifiers and MSC/ACM queries return unsupported responses. PDF/fulltext/account/third-party functions excluded. |
| Wateroffice | 0.1.0-dev | HYDAT 2026-07-17 and separately dated archived realtime/reference datasets | Map provider/zoom and visual differences; unavailable ApprovalGrade; snapshot cutoffs differ by product. Remains development status. |

The arXiv archive retains all categories of included records, not just cs/math/stat.
Data was acquired over a source interval, not a simultaneous snapshot of the live site.
Submission timestamps, first-announcement month, and OAI update dates are not interchangeable.

Current task coverage is 4 + 8 + 4 + 8 + 10 CG/GO records. Prior original-host
verification is historical evidence only. New package acceptance must verify
candidate completeness, output fields, background queries, isolation and recovery.
