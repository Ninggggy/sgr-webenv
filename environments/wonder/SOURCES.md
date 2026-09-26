# WONDER data sources and definitions

The runtime archive derives from national CDC/NCHS public-use Natality 2016–2024 and Period Linked Birth–Infant Death 2017–2023 data for U.S. residents. Original archives and reviewed layouts are listed in `sources/download-manifest.json` and `sources/layouts.json`.

Preserve the [data-use notice](licenses/DATA_USE_NOTICE.md). The databases contain computational inputs; apply the query/export protection rules when presenting statistics.

## Provenance

Source sidecars identify official archive names, URLs, retrieval dates and layouts. Runtime `retrieved_at` denotes import completion; source acquisition uses `retrieved_utc`. Category values for unknown, not stated and not reported remain distinct where the source distinguishes them.

Each yearly import preserves the supported joint fields and original death weights. Linked birth weight uses its imputed-weight field; death days denotes infant age at death rather than an event date. Birthplace is a delivery-setting category, not state or county geography.

## 2021 Natality origin

The 2021 public Natality archive has an inconsistent detailed-origin field. The runtime 2021 derivative uses the same-year public linked birth denominator from `2021PE2020CO-complete.zip`, member `VS2021LINK.Public.USDENPUB_r2023_05_31`. Residence status 4 is excluded. Detailed origin uses position 112; BWTIMP at position 516 restores the birthweight not-stated category.

The explicit origin-recode query groups Dominican with Other/Unknown Hispanic across selected years. Detailed-origin queries use the year's available categories; see [query coverage](COVERAGE.md).

## Aggregation and protection

Linked death rates use the matching birth denominator and original period weights, rounding after aggregation. Cause queries apply the selected categories and avoid totals over overlapping classifications. Small-count, reliability, ancestor and denominator rules are described in [query protection](../../docs/WONDER_PROTECTION_REVIEW.md).

## Building a separate dataset

Use `tools/import_data.py` with an explicit product, year and local official archive. Keep source inputs and comparison material outside runtime mounts, and use a new output directory rather than overwriting an installed dataset. Restore the published Release archive when the same data version is required.
