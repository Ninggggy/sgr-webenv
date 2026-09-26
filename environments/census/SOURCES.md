# ACS sources and coverage

The archive combines historical formatted CSV, fixed-year Census API metadata, ACS Summary Files and yearly geographic boundaries. Runtime data use 2016–2019 releases.

## Source datasets

Official Summary File paths:

```text
https://www2.census.gov/programs-surveys/acs/summary_file/{year}/data/{5|1}_year_by_state/
```

The collection includes DE, ME and WY for each year 2016–2019 in ACS5 and ACS1, plus PA 2016, CA 2017, NC 2018 and NM 2019 ACS1. Per-source metadata records URLs, products, years and retrieval information.

ACS5 imports state/county records from all sequences for the three listed states. ACS1 exposes these tables: B01001, B08201, B09010, B11010, B16004, B18105, B19013, B25003, B25014, B25024, B25044, B25070, B28002, B28011 and C16002.

Annual national boundaries support map selection. Numerical data are organized by the archived state, year and product files listed above. The application distinguishes unarchived values, source missing values and publication restrictions. The year-specific lookup/API defines variables; check each table's universe and units.

## Collection and restoration

Restore the release archive for repeatable experiments. `tools/fetch-summary.py` collects explicitly selected state/year/product files and supports resumption. Use separate output locations for new acquisitions. Author parsing dependencies are listed in `tools/requirements-author.txt` and are not required at website runtime.

## Query and export behavior

Search, geography and table customization are encoded in the URL. Numeric filters are table-specific; changing the table clears them. CSV and Excel carry the complete customized view; ZIP contains the complete archived table for the selected geographies.

The interface provides table and geography selection, year-specific boundaries, toolbars, multilevel column headers and a three-column layout.

The local Census API supports the documented table variables and archived geographies. E/M/EA/MA values come from the same runtime database. Three upstream domains map to one local origin; use the URL-based workflows rather than cross-origin authentication or storage flows.

Official references: [table changes](https://www2.census.gov/data/api-documentation/how-to-search-for-a-new-table-without-losing-selected-geos.pdf), [custom filters](https://www.census.gov/data/what-is-data-census-gov/guidance-for-data-users/frequently-asked-questions/how-can-i-create-a-custom-filter.html), and [customized downloads](https://www.census.gov/data/what-is-data-census-gov/guidance-for-data-users/frequently-asked-questions/do-the-customizations-in-my-table-view-carry-over-to-the-download.html). See [precision and statistical populations](PRECISION.md).
