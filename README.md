# SGR-WebEnv

Offline website environments for reproducible web-agent research with SGR-BENCH.

[中文](README.zh-CN.md) · [Releases](https://github.com/Ninggggy/sgr-webenv/releases) · [Features and data](docs/SCOPE.md) · [Operations](docs/OPERATIONS.md)

SGR-WebEnv packages website applications, fixed datasets, and restricted browsers into Docker environments. Researchers can run interactive search, navigation, and data-retrieval workflows locally. After preparation, supported workflows run without contacting the live websites.

The repository covers six websites. Each environment has a documented data and feature scope. Each website is reconstructed as a standalone offline environment.

## Environments

| Environment | Features | Setup | Preview port |
|---|---|---|---:|
| Census / ACS | ACS tables, geographic selection, maps, and customized exports | Prebuilt images | 8081 |
| CDC WONDER | National natality and linked infant mortality queries, charts, and CSV exports | Prebuilt images | 8082 |
| arXiv | cs/math/stat metadata, search, version timelines, and category browsing | Prebuilt images | 8083 |
| Wateroffice | Hydrometric station search, historical and archived realtime observations, maps, and downloads | Prebuilt images | 8084 |
| Cellosaurus | Cell-line records, search, linked entities, downloads, and CLASTR | Prebuilt images | 8086 |
| NOAA Climate at a Glance | Climate queries, maps, time-series charts, and data exports | Available · [manual chart dependency](environments/noaa/README.md) | 8080 |

See [data and feature scope](docs/SCOPE.md) for the included datasets and query boundaries.

## Quick start

Requirements: **Linux amd64**, Docker Engine with **Compose v2**, and **Python 3.9+**. Preparation requires Internet access to download data and images. See [resource configuration](docs/OPERATIONS.md) before installing; requirements vary by environment.

```sh
git clone --branch main https://github.com/Ninggggy/sgr-webenv.git
cd sgr-webenv

python3 tools/env.py prepare cellosaurus --release v0.1.2
python3 tools/env.py start cellosaurus --release v0.1.2 --mode preview
# Open http://127.0.0.1:8086/
```

Replace `cellosaurus` with `census`, `wonder`, `arxiv`, or `wateroffice` and use the port listed above. The release manifest selects the appropriate data archives and image versions; some unchanged artifacts come from earlier releases. arXiv preparation also builds its local search index.

Always pass `--release v0.1.2` for this release, including subsequent commands:

```sh
python3 tools/env.py verify cellosaurus --release v0.1.2
python3 tools/env.py reset cellosaurus --release v0.1.2
python3 tools/env.py stop cellosaurus --release v0.1.2
```

- `verify` checks service health.
- `reset` clears transient website/browser state and downloads, preserving datasets and the arXiv index.
- `stop` stops the environment and retains its persistent data.

Preview binds only to `127.0.0.1`. For evaluation, omit `--mode preview` or use `--mode eval`: this is the default mode and publishes no host ports. Runtime containers use isolated networks and do not mount task answers or author audit directories.

State is stored in `.state/<release>/<site>`; `--state-dir` changes the base directory. See [operations](docs/OPERATIONS.md) for browser access, upgrades, rollback, and instance management, and the [Cellosaurus guide](environments/cellosaurus/README.md) for its specific features.

## NOAA: prepare the chart dependency first

NOAA is available through a local source build. **Download ZingChart from its official distribution and build the NOAA images locally.**

1. Obtain **ZingChart 2.9.16-1** through the [official download page](https://www.zingchart.com/download) or its linked npm package, under a license appropriate for your use.
2. Place the complete package contents in `environments/noaa/app/static/cag/assets/zingchart-2.9.16-1/`, including `es6.js` and `zingchart-es6.min.js`.
3. Follow the [dependency checks and local build/start commands](environments/noaa/README.md). Use `--local-images` when preparing NOAA with your locally built images.

Once prepared, the chart library is served locally during offline operation. Keep its notices and required branding, and do not redistribute the library or images containing it without the applicable permission. The [license notes](docs/THIRD_PARTY.md) distinguish local use from redistribution.

## Source, data, and images

| Material | Location |
|---|---|
| Application source, Dockerfiles, preparation tools, and tests | This repository |
| Versioned data archives | [GitHub Releases](https://github.com/Ninggggy/sgr-webenv/releases) |
| Application and restricted-browser images | [GHCR packages](https://github.com/Ninggggy/sgr-webenv/packages) |
| Exact artifact URLs and image versions | [v0.1.2 manifest](releases/v0.1.2.json) |

To build from source, for example:

```sh
python3 tools/build.py base
python3 tools/build.py cellosaurus
python3 tools/env.py prepare cellosaurus --release v0.1.2 \
  --local-images --data-archive /path/to/cellosaurus-data-v0.1.2.tar.gz
```

Builds require online access to upstream dependencies. Runtime uses the prepared local resources. arXiv retains Elasticsearch 6.2.4 and its ICU configuration for compatibility; keep these research environments local or isolated rather than exposing them as public services.

## Licenses and citation

Original project code is licensed under **Apache-2.0**. Upstream code, data, fonts, maps, and archived assets retain their own terms; see [NOTICE](NOTICE) and the [third-party inventory](docs/THIRD_PARTY.md).

Cellosaurus data use **CC BY 4.0**; CLASTR and its modifications retain **GPL-3.0** with corresponding source. WONDER data carry [NCHS use conditions](environments/wonder/licenses/DATA_USE_NOTICE.md).

When using these environments in research, cite SGR-BENCH and record the repository URL, release tag, and environment/data versions used.
