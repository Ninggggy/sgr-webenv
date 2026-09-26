# WONDER data sources and use conditions

The runtime archive contains national NCHS public-use-derived computational data. These conditions apply to the data independently of the repository's code license.

## Sources

- [Vital Statistics Online](https://www.cdc.gov/nchs/data_access/vitalstatsonline.htm): Natality and Period Linked Birth–Infant Death public-use archives.
- [NVSS data release policy](https://www.cdc.gov/nchs/nvss/dvs_data_release.htm): national downloadable microdata and restricted geographic data have different release scopes.
- [NCHS Data User Agreement](https://www.cdc.gov/nchs/policy/data-user-agreement.html): permitted purposes and prohibited identification/linkage uses.
- [CDC reproduction conditions](https://www.cdc.gov/other/agencymaterials.html): attribution, substantive content and agency identity.
- [WONDER data use](https://wonder.cdc.gov/datause.html): restrictions on small birth/death statistics and associated rates.

## Archive representation

The sixteen SQLite files represent Natality 2016–2024 and Period Linked 2017–2023 using selected fields, grouped multiplicities and original death weights. They contain national U.S.-resident data, without restricted geography, direct identifiers or exact calendar event dates. Delivery-setting and infant-age fields are not geographic or event-date identifiers.

The 2021 Natality derivative uses the same-year public linked birth denominator and its birthweight imputation flag. See [source definitions](../../environments/wonder/SOURCES.md). Project recodings and grouped representations are adaptations rather than an unchanged official CDC database.

Small multiplicities are computational inputs. Apply query suppression and reliability rules when displaying or exporting statistics; raw runtime tables are not publication-ready small-cell tables.

## Conditions for use and redistribution

1. Attribute CDC/NCHS NVSS and identify the original public sources, available without charge from CDC.
2. Preserve the accompanying [data-use notice](../../environments/wonder/licenses/DATA_USE_NOTICE.md) with redistributed copies.
3. Use the data for statistical reporting and analysis. Do not identify people or establishments, link to individually identifiable data, or conduct re-identification/disclosure-protection-method research prohibited by the NCHS agreement.
4. Retain the website/export small-cell protections. Do not use this archive to reconstruct suppressed geographic WONDER information.
5. Keep project transformations distinct from source data; do not imply CDC endorsement or apply Apache-2.0 to the data.
6. Review the applicable source terms separately before adding other datasets or using the materials for a different purpose.

The linked source terms describe data use and redistribution conditions.
