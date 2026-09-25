# Installation, operation and rollback

Use Linux amd64, Docker Engine/Compose and Python 3.9+. Commands run from a
checkout of the release repository. Only environments marked `ready` in the
release manifest support normal installation. During private acceptance, the
author adds `--allow-candidate`; this does not waive the documented limitations.
NOAA has no distributable chart image and WONDER has no downloadable database.

## Prepare once and run

```sh
python3 tools/env.py prepare census --release v0.1.0
python3 tools/env.py start census --release v0.1.0 --mode preview
python3 tools/env.py verify census --release v0.1.0
python3 tools/env.py reset census --release v0.1.0
python3 tools/env.py stop census --release v0.1.0
```

Preview is loopback-only: NOAA 8080, Census 8081, WONDER 8082, arXiv 8083,
Wateroffice 8084. The table is a port convention, not an availability claim.
For a remote host, forward the selected port with your own SSH account. Do not
change the bind address to expose this research stack to the Internet.
Omitting `--mode preview` starts the isolated evaluation mode with no host ports.
Use the same `--state-dir /your/writable/path` on every command to relocate data.

`prepare` downloads archives, verifies expected sizes, safely extracts them,
checks SQLite integrity and builds the arXiv search index. Allow space for the
compressed parts, assembled archive, uncompressed data, images and index.
`start` reuses prepared data; for arXiv it refuses an index with an incomplete
record count. Do not run `prepare` again merely to restart an existing index:
the importer refuses to overwrite it. Diagnose failed builds before creating a
fresh index; never delete a production index as a test.

`reset` recreates web/browser/preview containers and clears their transient
browser sessions and download registry. It preserves data and the arXiv index.
`stop` removes the instance's containers/networks, not data or named volumes.
Author-exported evidence outside the containers is not deleted by reset.
`verify` checks HTTP availability only. Use the scripts and reports under
`tests/workflows/` and `docs/verification/` for the documented behavioral checks.

## Source build or prebuilt images

```sh
python3 tools/build.py base
python3 tools/build.py census
python3 tools/env.py prepare census --local-images --data-archive /path/to/census-data-v0.1.0.tar.gz
```

The default preparation path pulls versioned GHCR images. `--local-images`
checks already built images instead. Runtime has no need for source collectors,
benchmark files, personal credentials or network access to upstream websites.
Keep those files outside container mounts.

## Upgrade and rollback

There is one candidate release so far; no cross-version upgrade has been
accepted. For a future version, retain the previous Git tag, manifest, image
versions and prepared state directory. Stop the old instance before using the
same preview port. Prepare the new version in its own versioned state directory;
never overwrite the old database or mutate its read-only mount. Test the new
version before switching evaluation jobs to it.

Rollback means stopping the new version, checking out the old source tag and
starting the old release with its original state directory. Compose project and
arXiv volume names include the release version. No database migration or host
reboot is needed. Do not use `docker system prune` or `docker compose down -v`
as a reset/rollback procedure: they can destroy unrelated or retained state.
