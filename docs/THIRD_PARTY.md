# Third-party materials and data redistribution

The root Apache-2.0 license applies only to original project contributions.
This inventory is being checked before public release. Unresolved components
must not be described as cleared merely because the repository remains private.

| Material | Source / terms | Release handling |
|---|---|---|
| arXiv descriptive metadata | [API terms](https://info.arxiv.org/help/api/tou.html): CC0 descriptive metadata | No PDFs or paper source. Source acquisition identifiers retained. |
| arXiv base/search/browse code and templates | Official arXiv GitHub repositories | Original notices in `environments/arxiv/runtime/licenses`; revisions in `upstream/versions.json`. |
| Open Sans | SIL Open Font License | Notice retained with arXiv runtime. |
| NOAA data/site assets | [NOAA disclaimer](https://www.noaa.gov/disclaimer) | Climate data originate from NCEI; chart redistribution is blocked below. Included third-party library/font notices are preserved separately. |
| Census data/site assets | [Census policies](https://www.census.gov/about/policies.html) | Published ACS aggregate data and official CitySDK boundaries; CitySDK MIT notice is retained. The logo is used only to identify this unaffiliated research reproduction. |
| WONDER / NCHS | [WONDER data use](https://wonder.cdc.gov/datause.html), original public-use file terms | Data packages withheld pending direct-database redistribution review. Never weaken query suppression to simplify release. |
| Wateroffice hydrometric data | [Environment Canada disclaimer](https://wateroffice.ec.gc.ca/disclaimer_info_e.html) | Retain attribution and source warnings; map/font rights separately reviewed. |
| Chromium / Chrome for Testing | Official download and bundled notices | Download pinned browser in build; preserve bundled notices. |
| Elasticsearch / ICU / JNA | Elastic distribution, ICU plugin and JNA 4.5.1 Maven artifact | Preserve upstream image and artifact notices; security boundary remains isolated. |

WONDER inspection found many cells with n=1–9 in the prepared SQLite databases,
including mortality tables. They originate from public-use source processing,
so their applicable source terms must be distinguished from WONDER's query
output restrictions. Until that analysis is resolved, the databases are not
included in a Release. A protected web interface does not protect a downloaded DB.

No agency affiliation, endorsement, or trademark license is implied.

## Confirmed NOAA distribution blocker

The archived NOAA chart dependency is ZingChart 2.9.16-hf1. Its embedded notice
requires permission. The [Branded License](https://www.zingchart.com/pricing/branded-license)
explicitly excludes distribution in installable software products and requires
an OEM license for that use. Public NOAA hosting does not grant that OEM license.
Until an applicable authorization is supplied, do not publish NOAA containers or
include the library in public source history. The new main branch has been cleaned;
other release work may continue.
No purchase or request to the vendor has been made on the user's behalf.

The proprietary ZingChart files have been removed from the distribution tree. NOAA source and data are retained, but its chart-dependent install is incomplete. Acquisition or replacing the library is not silently automated. Original private server deployments remain unchanged.

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

## WONDER review conclusion for this candidate

The reviewed NCHS public-use agreement restricts use to statistical analysis and
forbids identification, identifiable-data linkage and re-identification research.
The WONDER data-use page adds a prohibition on publishing birth/death statistics
with counts of nine or fewer. These are distinct source/use conditions; a raw
NCHS public-use archive is not a WONDER query export. The import manifests point
to NCHS annual ZIPs, while the prepared joint-distribution database contains
small cells readable without the website's suppression layer. No statement in
this review establishes clearance to redistribute that prepared database.
It is therefore withheld; this is a release decision under unresolved terms,
not a claim that every use of NCHS public-use data is forbidden. Source collectors
and public source descriptors remain available for readers to assess their own
permitted preparation. No contacts were sent or permissions invented.
