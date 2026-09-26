# Climate data and sources

Source: [NCEI NClimDiv directory](https://www.ncei.noaa.gov/monitoring-content/data/us/climdiv/monthly/current/), fixed data release **20260904**, acquired 2026-09-13. Website templates and configuration originate from [Climate at a Glance](https://www.ncei.noaa.gov/access/monitoring/climate-at-a-glance/).

## Query scope

48 contiguous states and 344 climate divisions, January 1895 through August 2026. Variables include tavg/tmax/tmin, precipitation, heating/cooling degree days, Z index, PDSI, PHDI and PMDI.

Months are 1–12. Supported windows are 1–12, 18, 24, 36, 48 and 60 months, plus YTD where applicable. Non-Z Palmer indices use one-month windows. Unpublished dates and windows that extend before the source coverage are missing.

State and divisional queries use their respective official series. CONUS code 110 is an overview aggregate. The archive's `coverage.json` records numerical coverage; `metadata.json` provides locations and variables.

## Aggregation

Temperature and Z values use monthly means; degree days and precipitation use sums. The baseline is 1901–2000 for matching ending months and complete windows. Missing months are not interpolated.

Units: temperature °F, precipitation inches, degree days °F-days, and dimensionless Palmer indices. See [numeric channels](PRECISION.md) for rounding, raw values and ranking behavior.

## Installation

Restore the versioned runtime data archive through the installer and prepare the [ZingChart dependency](README.md) before building the web image. Source collectors and author evidence belong outside runtime mounts.
