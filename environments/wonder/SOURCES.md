# Source update — application 0.3 / data 2026.09.18

Only Natality 2021 is rebuilt. The original public Natality archive still has unusable MHISPX; no corrected archive was found in the inspected official sources. The official linked2021 guide documents that the period denominator contains all births in 2021 and identifies imputed missing birthweights with BWTIMP at position 516.

The recovery reads the complete `VS2021LINK.Public.USDENPUB_r2023_05_31` member of `2021PE2020CO-complete.zip` (433,532,955 archive bytes), excludes residence status 4, uses detailed origin at position 112, and restores BWTIMP=1 birthweights to original Not Stated 9999. It uses all 3,664,292 resident births and reverses 2,146 flagged resident imputations. It does not use infant deaths to infer births.

All ten-dimensional joint cells exactly match the preserved original Natality2021 database after collapsing Dominican and Other for comparison only. The restored distribution retains both categories separately. All nine fresh official Natality queries, covering 501 origin and origin-by-birth-characteristic cells, match, including suppression. These selected official comparisons do not claim exhaustive original-site comparison of every possible query.

Reproduce in a new directory on the author host:

```sh
python3 tools/recover_natality_2021.py --source-project ../wonder --reference-db ../wonder/validation/consistency-20260918/before-deploy/data/natality-2021.sqlite --reference-metadata ../wonder/validation/consistency-20260918/before-deploy/data/natality-2021.json --output-dir /absolute/new/output
```

Use the preserved 0.2 reference data after deployment; never pass the newly recovered database as its own reference. The tool refuses an existing output directory and refuses any full-joint mismatch. It generates the SQLite database, provenance metadata and author comparison report. The independent rerun reproduces all candidate rows exactly. Raw sources and comparison diagnostics remain author-side.

Evidence: `wonder/validation/consistency-20260918/`: origin-recovery-comparison.json, official-origin-comparison.json, parent-differences.csv and candidate-cause-checks.json. The 17 national parent-output differences are retained ancestor protection; primary-suppressed death rows also retain protected birth denominators. No protection change is included.

## Historical source inventory and 0.2 audit (superseded only for Natality2021 recovery)

# Data sources and actual coverage

Official sources: [Natality documentation](https://wonder.cdc.gov/wonder/help/natality-expanded.html), [Linked documentation](https://wonder.cdc.gov/wonder/help/lbd-expanded.html), [WONDER API policy](https://wonder.cdc.gov/wonder/help/wonder-api.html). Public-use national files do not supply the identified state/county distributions required for geographic reproduction. No geographic counts are invented.

Full machine-readable source/record/field details: `sources/coverage.json`, `sources/download-manifest.json`, `sources/layouts.json`, and per-year `data/*.json`. Download completion means full archive CRC validation; imported means a completed SQLite database; queryable requires both database and metadata; validated means the checks in `validation/coverage-validation.json` passed. They are deliberately reported separately.

| Product | Year | Archive bytes | Server archive | Prep archive | Imported | Queryable | Annual checks | Resident births | Resident numerator records |
|---|---:|---:|---|---|---|---|---|---:|---:|
| natality | 2016 | 248367974 | True | True | True | True | True | 3945875 | — |
| natality | 2017 | 242776873 | True | True | True | True | True | 3855500 | — |
| natality | 2018 | 228246064 | True | True | True | True | True | 3791712 | — |
| natality | 2019 | 226407903 | True | True | True | True | True | 3747540 | — |
| natality | 2020 | 229997676 | True | True | True | True | True | 3613647 | — |
| natality | 2021 | 232756903 | False | True | True | True | True | 3664292 | — |
| natality | 2022 | 222103574 | False | True | True | True | True | 3667758 | — |
| natality | 2023 | 229522736 | False | True | True | True | True | 3596017 | — |
| natality | 2024 | 231829759 | False | True | True | True | True | 3628934 | — |
| linked | 2017 | 460879295 | False | True | True | True | True | 3855500 | 22249 |
| linked | 2018 | 451827431 | False | True | True | True | True | 3791712 | 21357 |
| linked | 2019 | 447265743 | False | True | True | True | True | 3747540 | 20772 |
| linked | 2020 | 438388388 | False | True | True | True | True | 3613647 | 19446 |
| linked | 2021 | 433532955 | True | True | True | True | True | 3664292 | 19712 |
| linked | 2022 | 437642448 | False | True | True | True | True | 3667758 | 20303 |
| linked | 2023 | 434390502 | False | True | True | True | True | 3596017 | 19919 |

## Provenance and fields

Each annual public archive URL and official filename is a release identifier; downloaded directory listings retain the upstream publication/last-modified information where supplied. Retrieval dates and sizes are in source sidecars. We do not infer publication dates from local filesystem timestamps. Runtime metadata `retrieved_at` is the import completion time; actual source acquisition is the sidecar `retrieved_utc`.

Natality fields: birth month 13–14; birthplace 32/flag 33; age recode 79; residence status 104; race recode 107; Hispanic recode 112 (2018+) or 115 (2016–2017), flag 116; plurality 454; sex 475; obstetric gestation 499–500; birth weight 504–507. Linked uses the corresponding annual layout, early Hispanic recode through 2018, imputed birth weight 512–515, death days 1356–1358, age recode 1359, ICD 1368–1371, cause recode 1373–1375, and period weight 1377–1384. See annual layout evidence for source lines.

All fields preserve joint combinations; unknown/not stated/not reported categories remain distinct in the dictionary where available. Per-year marginal counts enumerate observed codes and missing categories. Explicit birth place codes remain valid even when the home-birth detail flag is not reported. The importer verifies actual record lengths and permits only a blank extension beyond a guide’s declared length.

Import 0.2 corrected handling of the birthplace reporting flag before validated deployment; rejected import 0.1 evidence is retained separately. Records were not rewritten. Natality 2019/2020 and Linked 2021 also have direct full-source independent author calculations and live original-site comparisons. Annual count/marginal validation of other years is not a claim that every possible cross-tabulation was compared to the live site.

Natality 2021 uses the documented coarser Hispanic recode (MHISP_R) at position 115 because position 112 is inconsistent in the public file. All-category expanded origin grouping remains unavailable for that year, but unambiguous origin subgroup filters and grouping are supported. The explicit origin_recode dimension combines Dominican and Other/Unknown Hispanic for every selected year, using the documented MHISP_R categories. Complete comparisons and the rejected preliminary import are retained. Linked 2017/2018 guide birth summaries also differ slightly from the supplied public files; the current final Natality guides agree with the supplied birth files. Source comparisons retain the exact discrepancies.

Linked 2021 period numerator guide national summary reports 19,927 weighted deaths, whereas the downloaded numerator rounds to 19,928, matching the live WONDER response and the final published report. This source discrepancy is retained in evidence; no adjustment is applied to records.

Public report PDFs and help text are copied into the runtime public directory; archives, formal task answers and independent scripts remain author-side only.

## 2026-09-17 recheck

The current official Natality directory still lists `nat2021us.zip`, 232,756,903 bytes, published 2022-11-30; its member is `Nat2021US.txt` (4,943,393,016 bytes, Deflate64). A fresh complete scan of 3,669,928 raw / 3,664,292 resident records confirmed MHISPX (position 112) is always 6; MHISP_R (115), reporting flag (116) and MRACEHISP (117) remain coherent. All reporting flags were 1. This is a field-content inconsistency in the available archive, not a shifted field or a blanket absence of ethnicity. No applicable corrected national archive was found in the official directory or official search during this audit. Linked records and marginal tables were not mixed into Natality.

Resident MHISP_R counts: non-Hispanic 2,741,995; Mexican 485,127; Puerto Rican 70,729; Cuban 24,437; Central/South American 178,067; combined Other/Unknown Hispanic including Dominican 127,556; origin unknown 36,381. Fresh source origin × race × sex × month counts match the installed joint database. Existing 0.3 data already preserved these categories, so no database replacement was needed. Application semantics are release 0.2; the unchanged data release is 2026.09.14.

The older cross-product comparison used position 504 for both products, although Linked birth weight is at 512. Its reported cross-product joint mismatch is therefore not used as evidence that ethnicity itself differs. The fresh audit instead compares Natality records directly with their own installed annual database.

Successful current original-site evidence now includes national 130-cause table, selected viral/P07 categories, cause × year, ordinary cause filtering, leading options, and Request/Results/Chart saves. The original 130-cause list disables totals and selects only explicitly selected list entries. Extra local ancestor protection remains intentionally more conservative; see the measured visibility differences in `cause-checks.json`. Sources: [Linked help](https://wonder.cdc.gov/wonder/help/lbd-expanded.html), [Save documentation](https://wonder.cdc.gov/wonder/help/quickstart.html#Save), [2021 layout](https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Dataset_Documentation/DVS/natality/UserGuide2021.pdf). New raw responses, controls, screenshots, traces and source-field distributions are under `validation/repair-2026-09-17/`.
