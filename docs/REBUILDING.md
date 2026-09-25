# Rebuilding versus restoring a release

The supported repeatable runtime input is a versioned Release data archive, not a
new crawl of a changing website. Acquisition scripts are author-side tools; they
require Internet access and may produce a different data version. Do not overwrite
an accepted data directory with a new crawl. Benchmark records remain separate.

## WONDER data is withheld

There is no downloadable prepared database in this release candidate.
`sources/download-manifest.json` lists the original annual public-use archives;
`sources/layouts.json` records the reviewed record layouts used by the importer.
Readers must review the NCHS data-use conditions before obtaining or processing
those inputs. `tools/import_data.py` requires a product, year and a local annual
archive; it refuses to overwrite an existing import or use an unreviewed layout.
The source descriptor is not authorization to redistribute a prepared small-cell
database. Website suppression does not apply to direct database access.

## arXiv

The archive contains the latest descriptive metadata and complete version times.
`prepare` builds a new Elasticsearch index with the preserved official query
mapping. `start` compares the index count with source records and refuses partial
results. An interrupted build must be diagnosed before retry; never point a
production service at an in-progress index. Older version content and daily
announcement features remain unsupported regardless of any author-side material.

## Census, NOAA and Wateroffice

Restore the per-site Release archive for the published snapshot. Census source
collectors require the originally selected products, years and geography, and
some author import tools refer to acquisition/validation material that is not
in the runtime package. Their presence is not a claim that a fresh live crawl
recreates the frozen release byte for byte.

NOAA's proprietary chart component is deliberately absent. Its source/data
materials do not form a complete chart-capable install without an appropriate
license or a separately tested replacement.

Wateroffice requires HYDAT plus all listed real-time snapshots, dictionaries,
datum/reference information and map material. HYDAT alone is not sufficient.
The replacement NRCan basemap and dev maturity must remain disclosed.
