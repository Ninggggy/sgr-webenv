# SGR-WebEnv

Offline website environments for reproducible web-agent research with SGR-BENCH.

[中文](README.zh-CN.md) · [Releases](https://github.com/Ninggggy/sgr-webenv/releases) · [Coverage and limitations](docs/SCOPE.md) · [Verification](docs/STATUS.md)

SGR-WebEnv packages website applications, fixed datasets, and restricted browsers into Docker environments. Researchers can run interactive search, navigation, and data-retrieval workflows locally. After preparation, supported workflows run without contacting the live websites.

The repository covers six websites. Each environment has a documented data and feature scope. These are independent reconstructions, unaffiliated with the original services.

## Available environments

**v0.1.2 adds Cellosaurus** and retains the existing distributions of Census, WONDER, arXiv, and Wateroffice.

| Environment | Distribution | Included scope and main limitations | Preview port |
|---|---|---|---:|
| Census / ACS | Available · 0.2.1 | Archived regions, years, and tables; not nationwide coverage of all ACS products. | 8081 |
| CDC WONDER | Available · 0.3 | National grouped queries within the documented coverage; protection-rule differences and NCHS data-use conditions apply. | 8082 |
| arXiv | Available · 0.1.0 | 1,685,244 cs/math/stat records with latest metadata and version timelines; excludes historical version content, daily announcements, and full text. | 8083 |
| Wateroffice | Development · 0.1.0-dev | Archived hydrometric data and query workflows; map, coverage, and visual limitations remain. | 8084 |
| Cellosaurus | Available · 0.1.0 | Release 56.0 metadata: 168,970 records, core website, and CLASTR; excludes the complete REST/RDF/SPARQL interface. | 8086 |
| NOAA Climate at a Glance | Source and data | Climate data and application source; component availability and supported workflows are documented in the [release notes](docs/STATUS.md). | 8080* |

*8080 is the configured NOAA preview port. See the [deployment status](docs/STATUS.md) for preparation requirements.*

See [coverage and known differences](docs/SCOPE.md) for feature boundaries and [verification results](docs/STATUS.md) for the evidence behind each release.

## Quick start

Requirements: **Linux amd64**, Docker Engine with **Compose v2**, and **Python 3.9+**. Preparation requires Internet access to download data and images. See the [resource measurements](docs/STATUS.md) before installing; requirements vary by environment.

```sh
git clone https://github.com/Ninggggy/sgr-webenv.git
cd sgr-webenv
git checkout v0.1.2

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

- `verify` checks service health. It does not run benchmark correctness tests.
- `reset` clears transient website/browser state and downloads, preserving datasets and the arXiv index.
- `stop` stops the environment and retains its persistent data.

Preview binds only to `127.0.0.1`. For evaluation, omit `--mode preview` or use `--mode eval`: this is the default mode and publishes no host ports. Runtime containers use isolated networks and do not mount task answers or author audit directories.

State is stored in `.state/<release>/<site>`; `--state-dir` changes the base directory. See [operations](docs/OPERATIONS.md) for browser access, upgrades, rollback, and instance management, and the [Cellosaurus guide](environments/cellosaurus/README.md) for its specific features.

## Source, data, and images

| Material | Location |
|---|---|
| Application source, Dockerfiles, preparation tools, and tests | This repository |
| Versioned data archives and publication reports | [GitHub Releases](https://github.com/Ninggggy/sgr-webenv/releases) |
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

## Verification and scope

Published reports distinguish source-data checks, webpage workflow replay, packaged installation, and isolation tests. These checks are not measurements of autonomous model success. Installation methods and untested configurations are recorded alongside the results.

Cellosaurus includes full source-record reconciliation, 337 data/export checks, 75 browser checks, four supplementary task replays, and anonymous data/image download verification. See its [publication report](docs/verification/cellosaurus-publication-report-v0.1.2.json) and the [cross-environment status report](docs/STATUS.md). The original 100-task set contains no Cellosaurus tasks.

## Licenses and citation

Original project code is licensed under **Apache-2.0**. Upstream code, data, fonts, maps, and archived assets retain their own terms; see [NOTICE](NOTICE) and the [third-party inventory](docs/THIRD_PARTY.md).

Cellosaurus data use **CC BY 4.0**; CLASTR and its modifications retain **GPL-3.0** with corresponding source. WONDER data carry [NCHS use conditions](environments/wonder/licenses/DATA_USE_NOTICE.md).

When using these environments in research, cite SGR-BENCH and record the repository URL, release tag, and environment/data versions used.
