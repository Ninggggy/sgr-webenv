# Third-party materials and data redistribution

The root Apache-2.0 license applies only to original project contributions.
This inventory records component-specific publication decisions. Source code,
application assets and data have separate terms; no blanket agency clearance is implied.

| Material | Source / terms | Release handling |
|---|---|---|
| arXiv descriptive metadata | [API terms](https://info.arxiv.org/help/api/tou.html): CC0 descriptive metadata | No PDFs or paper source. Source acquisition identifiers retained. |
| arXiv base/search/browse code and templates | Official arXiv GitHub repositories | Original notices in `environments/arxiv/runtime/licenses`; revisions in `upstream/versions.json`. |
| Open Sans | SIL Open Font License | Notice retained with arXiv runtime. |
| NOAA data/site assets | [NOAA disclaimer](https://www.noaa.gov/disclaimer) | Climate data originate from NCEI; chart redistribution is blocked below. Included third-party library/font notices are preserved separately. |
| Census data/site assets | [Census policies](https://www.census.gov/about/policies.html) | Published ACS aggregate data and official CitySDK boundaries; CitySDK MIT notice is retained. The logo is used only to identify this unaffiliated research reproduction. |
| WONDER / NCHS | [WONDER data use](https://wonder.cdc.gov/datause.html), original public-use file terms | Audited national public-use derivative released with DATA_USE_NOTICE; website suppression retained. See the detailed review. |
| Wateroffice hydrometric data | [Environment Canada disclaimer](https://wateroffice.ec.gc.ca/disclaimer_info_e.html) | Retain attribution and source warnings; map/font rights separately reviewed. |
| Chromium / Chrome for Testing | Official download and bundled notices | Download pinned browser in build; preserve bundled notices. |
| Elasticsearch / ICU / JNA | Elastic distribution, ICU plugin and JNA 4.5.1 Maven artifact | Preserve upstream image and artifact notices; security boundary remains isolated. |

WONDER's national runtime archive is derived from NCHS public-use files,
not unsuppressed WONDER query captures. The completed [source-specific review](reviews/WONDER_DATA_REDISTRIBUTION.md)
permits release with the included NCHS use conditions and attribution. Small
multiplicities remain computational inputs; website/export protection is unchanged.

No agency affiliation, endorsement, or trademark license is implied.

## NOAA user-supplied dependency and redistribution

The archived NOAA chart dependency is ZingChart 2.9.16-hf1. Its embedded notice
requires permission. The [Branded License](https://www.zingchart.com/pricing/branded-license)
explicitly excludes distribution in installable software products and requires
an OEM license for that use. Public NOAA hosting does not grant that OEM license.
Until an applicable authorization is supplied, do not publish NOAA containers or
include the library in public source history. The new main branch has been cleaned;
other release work may continue.
No purchase or request to the vendor has been made on the user's behalf.

ZingChart is excluded from the distribution tree. Users may obtain the required version themselves under an applicable license and build for their own use following the [NOAA setup guide](../environments/noaa/README.md). This manual-dependency route does not grant redistribution permission or authorize publishing images containing the library. Download and placement are explicit user steps; original private server deployments remain unchanged.

## Wateroffice assets checked during packaging

The hydrometric data disclaimer permits copying/distribution with Environment
Canada attribution and prohibits reselling bundled raw data. This release is
provided without charge and does not relabel those data as Apache-2.0.
The packaged map manifest identifies NRCan Toporama WMS under the Open Government
Licence - Canada; it is a replacement basemap, not an exact Google Maps replica.
Map visual equivalence remains unaccepted.

The distribution includes upstream license text for Font Awesome Free 5.15.3
(code MIT, fonts OFL, icons CC BY 4.0), Lato and Noto Sans (OFL), Chart.js 4.5.1
(MIT), WET-BOEW and GCWeb. URLs are recorded alongside the texts under
`environments/wateroffice/app/static/licenses/`. Existing Leaflet notices and
Chart.js bundle notices are preserved. This inventory does not grant rights in
agencies' trademarks or imply agency endorsement.

## Census and remaining NOAA notices

Census ACS aggregates are published statistical products. The Bureau's
[Research Transparency and Public Access policy](https://www2.census.gov/foia/ds_policies/ds027.pdf)
states that employee-created data/works generally are not subject to US copyright.
The packaged yearly boundaries come from the official
[CitySDK repository](https://github.com/uscensusbureau/citysdk); its MIT text is
retained in `environments/census/licenses/`. The front end is a local
reconstruction and uses system fonts; no third-party commercial basemap is bundled.
The Census identity artwork is not licensed as a project trademark.

NOAA's remaining bundled dependency notices are under
`environments/noaa/app/static/licenses/`: jQuery, jQuery UI, Bootstrap,
Bootstrap Icons, Font Awesome Free, Leaflet, noUiSlider, tablesorter,
leaflet-easyPrint and its dom-to-image/FileSaver dependencies. Font notices are
under `static/fonts/`. `sources.json` records upstream URLs; dependency versions
are taken from the bundled paths/headers where available. Adding these notices
does not resolve the separately excluded ZingChart component or establish full
NOAA installation acceptance.

The NOAA data-only archive contains NCEI climate series, metadata and coverage information. The [NCEI copyright notice](https://data.ngdc.noaa.gov/ngdcinfo/privacy.html) permits copying its public information, with source credit, while retaining third-party exceptions. NCEI government data in this archive are identified as such and are not relicensed under Apache-2.0. The chart code is outside that data permission.

## WONDER source-specific review completed

The earlier hold treated the presence of 1–9 multiplicities as sufficient reason
to withhold all prepared public-use data. That reasoning was incomplete. The
[NVSS policy](https://www.cdc.gov/nchs/nvss/dvs_data_release.htm) distinguishes
national downloadable public-use microdata from geography-rich web tabulations.
All 16 installed databases trace to the former. They add no direct identifiers,
restricted geography or exact calendar event dates and contain no WONDER query
capture. The 2021 source substitution is separately disclosed in the review.

Release these audited derivatives with `environments/wonder/licenses/DATA_USE_NOTICE.md`,
source attribution, original usage restrictions and no implied CDC endorsement.
This is the project's interpretation of published terms, not individual CDC
permission or an unrestricted-data license. Do not replace data terms with the
code's Apache-2.0 license. The existing query suppression, reliability indicators
and more conservative parent protection are not weakened. Details and limits:
[completed review](reviews/WONDER_DATA_REDISTRIBUTION.md).

## Cellosaurus

Cellosaurus data and owned resources use CC BY 4.0; modified CLASTR source and frontend use GPL-3.0. Separate bundled dependency terms remain in force. Complete corresponding source is included. Institutional partner badges are omitted from the distribution interface. See [component notices](../environments/cellosaurus/licenses/NOTICE.md).
