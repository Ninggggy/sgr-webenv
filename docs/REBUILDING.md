# Restoring and rebuilding data

Use the versioned Release archive as the input for a repeatable installation. Acquisition tools retrieve upstream data and require Internet access; a new crawl may have a different source date. Keep new acquisitions separate from an installed dataset.

## Restore an environment

```sh
python3 tools/env.py prepare census --release v0.1.2
python3 tools/env.py start census --release v0.1.2 --mode preview
```

To use an archive already stored locally, add `--data-archive /path/to/data.tar.gz`. Add `--local-images` when using images built on the same Docker host. See [operations](OPERATIONS.md).

## WONDER

The Release archive contains national NCHS public-use-derived runtime databases. Preserve the [data-use notice](../environments/wonder/licenses/DATA_USE_NOTICE.md).

The environment's `sources/download-manifest.json` identifies original annual archives and `sources/layouts.json` records importer layouts. `tools/import_data.py` takes a product, year and local annual archive; use a new output location. Source and 2021 field definitions are described in [SOURCES](../environments/wonder/SOURCES.md). Website suppression rules do not turn raw database rows into publication-ready tables.

## arXiv

The data archive contains latest descriptive metadata and version times. Preparation builds Elasticsearch using the packaged query mapping. Startup checks the index against the source record count. Diagnose interrupted builds before retrying, and use a separate index for a new data version. Historical content and daily announcement features are outside this dataset.

## Census and NOAA

Restore the corresponding fixed Release archive. Census collectors select explicit years, products and states; see [Census sources](../environments/census/SOURCES.md). For NOAA, prepare the [chart dependency](../environments/noaa/README.md) before building the web image.

## Wateroffice

Use the complete per-site archive: HYDAT, realtime snapshots, dictionaries, datum/reference information and map resources. HYDAT alone supplies historical observations but not the other website workflows. See [Wateroffice data and map behavior](../environments/wateroffice/DIFFERENCES.md).

## Cellosaurus

Place the archived Release 56.0 source files in the environment's `data/` directory and run `python3 tools/import_data.py` from that environment directory. Keep Release 53/54 historical name-conflict files separate. The importer checks the source release and refuses to overwrite an existing database; see [the environment guide](../environments/cellosaurus/README.md).
