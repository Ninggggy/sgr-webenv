# Source, data and images

| Material | Location |
|---|---|
| Applications, deployment files, collectors and tests | This repository |
| Versioned runtime data archives | [GitHub Releases](https://github.com/Ninggggy/sgr-webenv/releases) |
| Container images | [Repository packages](https://github.com/Ninggggy/sgr-webenv/packages) |
| Data URLs, image tags and application versions | [Release manifest](../releases/v0.1.2.json) |

`tools/env.py prepare <site> --release v0.1.2` downloads the artifacts selected by the manifest. A release may reuse unchanged data or images from an earlier version. arXiv data are split into archive parts; the installer assembles them and builds the local search index.

NOAA uses a [user-supplied ZingChart dependency and local image build](../environments/noaa/README.md). Keep that dependency and images containing it out of redistribution unless your license permits it.

## Preparing a distribution

Use a runtime-file whitelist. Keep credentials, browser profiles, author research materials and task answers out of images and data archives. Export SQLite through a consistent backup rather than copying a live database with incomplete WAL files. Preserve source metadata and component licenses.

Retain the prior release and its artifacts for rollback. Check that a reader without repository credentials can retrieve the intended source, data and images. Repository visibility and GHCR package visibility are separate settings; consult [GitHub package access guidance](https://docs.github.com/en/packages/learn-github-packages/configuring-a-packages-access-control-and-visibility).

Use a trusted build runner and remove its registration credentials after use. Do not publish excluded proprietary files or private staging history. See [third-party terms](THIRD_PARTY.md) and [operation and rollback](OPERATIONS.md).
