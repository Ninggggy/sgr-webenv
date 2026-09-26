# Cellosaurus 0.1.0

Independent offline core website and CLASTR, distributed with SGR-WebEnv v0.1.2. Linux amd64 only.

## Install and use

From the repository root:

```sh
python3 tools/env.py prepare cellosaurus --release v0.1.2
python3 tools/env.py start cellosaurus --release v0.1.2 --mode preview
python3 tools/env.py verify cellosaurus --release v0.1.2
python3 tools/env.py reset cellosaurus --release v0.1.2
python3 tools/env.py stop cellosaurus --release v0.1.2
```

Open http://127.0.0.1:8086/ ; CLASTR: http://127.0.0.1:8086/str-search/ . Omit `--mode preview` for isolated evaluation without a host port. The web application can reach CLASTR on an internal backend network; the browser can only reach the web application. Only read-only data are mounted. `reset` recreates transient browser/download state without deleting the dataset.

For source builds, run `python3 tools/build.py cellosaurus` before prepare and pass `--local-images`. All three Linux amd64 images are built from public inputs; Maven dependencies are resolved during build. Java core and Web tests run during build. Maven 3.9.11, Java 17, Tomcat 11.0.11 and application dependencies are specified in the Dockerfile/POM files. Shared runtime/browser bases have their build sources in the top-level `docker/` directory.

Allow approximately 5.2 GiB of runtime memory limits (web 1.5 GiB, CLASTR 1.5 GiB, browser 2 GiB, preview proxy 128 MiB). Data unpack to approximately 528 MiB; installation also needs archive/cache and image/build space. A full clean Java build uses additional dependency cache and intermediate layers. Keep at least 5 GiB free on the root filesystem.

## Features and data

* Complete Cellosaurus Release 56.0 (2026-06-25), 168,970 entries; 30,159 parsed references.
* Twelve original download files plus separate full Release 53/54 name-conflict files; main records are not mixed with historical releases.
* Search, records, original TXT, parent/child/same-individual links, groups/panels, references, downloads, and CLASTR human/mouse/dog authentication search, uploads and exports.
* Equal-name results use accession order. Search returns the full matching record set, and STR displays use source XML names.
* Task files and expected answers belong in author-side test directories and are not mounted by runtime containers.

See [licenses/NOTICE.md](licenses/NOTICE.md), [upstream changes](docs/upstream.json), and [shared operations](../../docs/OPERATIONS.md).

## Data reconstruction and rollback

The Release asset is the stable data input. Source URLs and collection times are in its `sources.json` and `history/sources.json`. `tools/fetch_sources.py` and `tools/fetch_history.py` are acquisition helpers; a live upstream URL may have moved to a newer release, so the importer requires version 56.0 and refuses to overwrite an existing database. From this environment directory, place the archived `.gz` sources in `data/`, then run `python3 tools/import_data.py` to derive SQLite. `python3 ../../tools/package_cellosaurus_data.py data output.tar.gz --temporary-dir /path/to/space` creates a consistent runtime-only archive.

Stop the installed distribution before an upgrade. Install the new release into its separate versioned state directory; retain the old directory and image tags to roll back with the corresponding `--release`. Never copy a live database with incomplete WAL files.

## Re-run verification

With the data archive extracted under this environment's `data/` directory (author/test use only), run `python3 tests/data_sources.py`, `python3 tests/index_sources.py` and `python3 tests/search_sources.py`. These compare the SQLite representation with the source XML and archived search responses. `validation/` outputs are ignored by Git and never mounted by runtime Compose.

For an installed v0.1.2 environment, run `python3 tools/browser_smoke.py cellosaurus --release v0.1.2` from repository root. To run the 15-step structured browser regression, set `CELLOSAURUS_BROWSER_CONTAINER` to the installed browser container name and run `python3 environments/cellosaurus/tests/browser_rpc.py`. `tests/browser_interactions.py` is an author-only Playwright suite; run it in a separate restricted test browser attached to the instance's browsing network, mount only the test script and an empty `/results` output directory, and stop the instance browser during this test to avoid duplicating browser memory. It is never exposed through the agent RPC.

Use the manifest-selected web image `0.1.0-1` for streaming preview downloads. Pin the image tags from the manifest when deploying.
