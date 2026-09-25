# Query coverage — application 0.3 / data 2026.09.18

The unchanged annual joint data cover Natality 2016–2024 and period Linked 2017–2023, nationwide U.S. residents only. Annual totals are rechecked independently for all 16 product-years.

| Dimension | Natality | Linked | Browser filter | Limits |
|---|---|---|---|---|
| Year | 2016–2024 | 2017–2023 | Multi-select / All / Clear | All includes every imported year; no silent skip |
| Birth month | Yes | Not promised | Natality | Linked is period mortality |
| Maternal race 6, age 9 | Yes | Yes | Yes | Other race/age recodes remain outside scope |
| Broad Hispanic origin | Yes | Yes | Yes | Independent of maternal race |
| Expanded origin | Yes, including 2021 | Yes, early years cannot split Dominican | Yes, year-aware explanation | Nat 2021 expanded origin recovered in the complete supported joint distribution; early-year product restrictions remain |
| Hispanic Origin Recode | Yes | Yes | Yes | Explicitly combines Dominican and Other/Unknown Hispanic in all years |
| Birthplace / Recode 6 / Recode 3 | Yes | Yes | All three classifications | Exactly one active classification; filter applies to birth denominator and death numerator |
| Sex, gestation, birth weight, plurality | Yes | Yes | Yes | Existing public-file coding; Linked imputed weight field |
| Death age group / days | No | Yes | Yes | Exactly one classification; death numerator only |
| 130 cause list | No | Yes | Yes | Selected entries only, no overlapping totals, additional ancestor suppression remains stricter than current original |
| 15 Leading Causes | No | Yes | Grouping; ordinary cause filter separately | Single grouping, no zero/suppressed display, no totals; rank 15 ties included |

No promised query dimension remains available only through the API without its required web filtering controls. Confidence intervals, state/county geography/maps, fertility rates and unlisted original variables remain outside the previously agreed national scope. This repair does not shrink that scope or remove public help, reports or downloads.

`data/*.json` and `sources/coverage.json` retain source/import provenance. Fresh raw-record, independent SQL, browser and original-site evidence lives under `validation/repair-2026-09-17/`. Annual coverage is not a claim that every possible combination has been compared with WONDER.
