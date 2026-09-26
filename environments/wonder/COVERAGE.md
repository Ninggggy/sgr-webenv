# Query coverage — application 0.3 / data 2026.09.18

The annual joint data cover Natality 2016–2024 and period Linked 2017–2023, nationwide U.S. residents only.

| Dimension | Natality | Linked | Browser filter | Limits |
|---|---|---|---|---|
| Year | 2016–2024 | 2017–2023 | Multi-select / All / Clear | All includes every imported year; no silent skip |
| Birth month | Yes | — | Natality | Birth-month queries use Natality; Linked queries use period mortality |
| Maternal race 6, age 9 | Yes | Yes | Yes | Other race/age recodes remain outside scope |
| Broad Hispanic origin | Yes | Yes | Yes | Independent of maternal race |
| Expanded origin | Yes, including 2021 | Yes, early years cannot split Dominican | Yes, year-aware explanation | Nat 2021 uses the detailed origin categories; early-year product restrictions apply |
| Hispanic Origin Recode | Yes | Yes | Yes | Explicitly combines Dominican and Other/Unknown Hispanic in all years |
| Birthplace / Recode 6 / Recode 3 | Yes | Yes | All three classifications | Exactly one active classification; filter applies to birth denominator and death numerator |
| Sex, gestation, birth weight, plurality | Yes | Yes | Yes | Existing public-file coding; Linked imputed weight field |
| Death age group / days | No | Yes | Yes | Exactly one classification; death numerator only |
| 130 cause list | No | Yes | Yes | Selected entries only, no overlapping totals, additional ancestor protection applies |
| 15 Leading Causes | No | Yes | Grouping; ordinary cause filter separately | Single grouping, no zero/suppressed display, no totals; rank 15 ties included |

Confidence intervals, state/county geography/maps, fertility rates and unlisted variables are outside the national dataset. Use the corresponding browser controls to select the supported query dimensions. Source/import metadata accompany the archive; see [sources](SOURCES.md) and [protection rules](../../docs/WONDER_PROTECTION_REVIEW.md).
