# Third-party materials and licenses

Apache-2.0 applies to original project code. Data, upstream software, templates, maps, fonts and branding retain their respective terms.

| Material | Source and terms | Use in this repository |
|---|---|---|
| arXiv descriptive metadata | [API terms](https://info.arxiv.org/help/api/tou.html), CC0 descriptive metadata | Bibliographic records and version timelines |
| arXiv source and templates | Official arXiv repositories | Preserve notices under `environments/arxiv/runtime/licenses` and revisions in `upstream/versions.json` |
| Open Sans | SIL Open Font License | Notice accompanies the font |
| NOAA climate data | [NOAA disclaimer](https://www.noaa.gov/disclaimer), [NCEI notice](https://data.ngdc.noaa.gov/ngdcinfo/privacy.html) | Attribute NCEI; third-party resources retain separate terms |
| Census ACS and boundaries | [Census policies](https://www.census.gov/about/policies.html), [CitySDK](https://github.com/uscensusbureau/citysdk) MIT license | Published ACS aggregates and yearly boundaries; preserve the CitySDK notice |
| WONDER / NCHS | [Data-use conditions](https://wonder.cdc.gov/datause.html) and original public-use file terms | Preserve the [data-use notice](../environments/wonder/licenses/DATA_USE_NOTICE.md) and query protections |
| Wateroffice hydrometric data | [Environment Canada disclaimer](https://wateroffice.ec.gc.ca/disclaimer_info_e.html) | Retain attribution and source notices; redistribution of bundled raw data is on a non-resale basis |
| NRCan Toporama map data | Open Government Licence – Canada | Archived replacement basemap with source attribution |
| Chromium / Chrome for Testing | Bundled upstream notices | Download the pinned browser during build and retain notices |
| Elasticsearch / ICU / JNA | Respective upstream distribution terms | Preserve dependency notices and the isolated runtime configuration |
| Cellosaurus data and owned resources | CC BY 4.0 | Retain CALIPHO/SIB attribution and source release identities |
| CLASTR and modifications | GPL-3.0 | Complete corresponding source and notices included |

## NOAA chart dependency

ZingChart is user-supplied. Follow the [download and local-build guide](../environments/noaa/README.md). Its [Branded License](https://www.zingchart.com/pricing/branded-license) specifies branding requirements. Distribution in installable software products requires applicable OEM permission.

Store the downloaded package and license keys locally. Obtain the applicable redistribution permission before publishing images containing ZingChart.

Other NOAA dependency notices accompany jQuery, jQuery UI, Bootstrap, Bootstrap Icons, Font Awesome Free, Leaflet, noUiSlider, tablesorter, leaflet-easyPrint, dom-to-image and FileSaver. Font notices are under the environment's static font directory.

## Wateroffice resources

The map uses NRCan Toporama rather than Google Maps. Bundled library notices cover Font Awesome Free 5.15.3 (MIT/OFL/CC BY 4.0 by component), Lato and Noto Sans (OFL), Chart.js (MIT), WET-BOEW, GCWeb and Leaflet. See `environments/wateroffice/app/static/licenses/` for notices and source links.

## WONDER data

The runtime data derive from national NCHS public-use files. Preserve source attribution, statistical-use restrictions and small-cell protection rules. NCHS terms govern the data. See [source and use conditions](reviews/WONDER_DATA_REDISTRIBUTION.md).

## Cellosaurus resources

See [component notices](../environments/cellosaurus/licenses/NOTICE.md) for Cellosaurus CC BY 4.0, CLASTR GPL-3.0 and bundled JavaScript/Java dependencies. Preserve corresponding modified source with GPL-covered distributions. Institutional partner badges are represented by text attribution.

Agency names and identity artwork identify the source websites.
