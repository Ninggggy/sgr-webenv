# Installation, operation and rollback

Use Linux amd64, Docker Engine with Compose v2 and Python 3.9+. Run commands from the repository root. Census, WONDER, arXiv, Wateroffice and Cellosaurus use the prebuilt-image workflow below. NOAA uses the [manual chart dependency and local build workflow](../environments/noaa/README.md).

## Prepare once and run

```sh
python3 tools/env.py prepare census --release v0.1.2
python3 tools/env.py start census --release v0.1.2 --mode preview
python3 tools/env.py verify census --release v0.1.2
python3 tools/env.py reset census --release v0.1.2
python3 tools/env.py stop census --release v0.1.2
```

Preview is loopback-only: NOAA 8080, Census 8081, WONDER 8082, arXiv 8083,
Wateroffice 8084, Cellosaurus 8086.
For a remote host, forward the selected port with your own SSH account. Do not
change the bind address to expose this research stack to the Internet.
Omitting `--mode preview` starts the isolated evaluation mode with no host ports.
Use the same `--state-dir /your/writable/path` on every command to relocate data.

`prepare` downloads archives, verifies expected sizes, safely extracts them,
checks SQLite integrity and builds the arXiv search index. Allow space for the
compressed parts, assembled archive, uncompressed data, images and index.
For arXiv, plan a host with at least 24 GiB available for the search service plus
space for the web/browser and operating system. The search container is configured with a 24 GiB memory limit and a 2 GiB Java heap. These are configuration values; size the host for the search service, web/browser containers and operating system. The index uses persistent disk storage. Keep at least 5 GiB free on the root filesystem during preparation and building.
`start` reuses prepared data; for arXiv it refuses an index with an incomplete
record count. Do not run `prepare` again merely to restart an existing index:
the importer refuses to overwrite it. Diagnose failed builds before creating a
fresh index; never delete a production index as a test.

`reset` recreates web/browser/preview containers and clears their transient
browser sessions and download registry. It preserves data and the arXiv index.
`stop` removes the instance's containers/networks, not data or named volumes.
Author-exported evidence outside the containers is not deleted by reset.
`verify` checks HTTP availability only. Use the scripts and reports under
`tests/workflows/` for behavioral checks.

## Source build or prebuilt images

```sh
python3 tools/build.py base
python3 tools/build.py census
python3 tools/env.py prepare census --release v0.1.2 --local-images --data-archive /path/to/census-data-v0.1.0.tar.gz
```

The default preparation path pulls versioned GHCR images. `--local-images`
checks already built images instead. Runtime has no need for source collectors,
benchmark files, personal credentials or network access to upstream websites.
Keep those files outside container mounts.

## Upgrade and rollback

Distribution versions retain separate manifests/state directories. No in-place
database migration is implied. For an upgrade, retain the previous Git tag, manifest, image
versions and prepared state directory. Stop the old instance before using the
same preview port. Prepare the new version in its own versioned state directory;
never overwrite the old database or mutate its read-only mount. Test the new
version before switching evaluation jobs to it.

Rollback means stopping the new version, checking out the old source tag and
starting the old release with its original state directory. Compose project and
arXiv volume names include the release version. No database migration or host
reboot is needed. Do not use `docker system prune` or `docker compose down -v`
as a reset/rollback procedure: they can destroy unrelated or retained state.

For Cellosaurus, explicitly pass `--release v0.1.2` to its commands. Its Java backend is on a separate internal network. `--port 18086` can be added to preview startup for a parallel test instance without taking over an existing listener. See [Cellosaurus operations and tests](../environments/cellosaurus/README.md).

Wateroffice `0.1.0` uses `--release v0.1.3`. See its [install, data scope and rollback guide](../environments/wateroffice/README.md). The prior development application is retained by `v0.1.2`.
