# SGR-WebEnv

Reproducible offline website environments for SGR-BENCH. [中文说明](README.zh-CN.md).

**v0.1.0: public distribution for Census, arXiv, and Wateroffice (development version). NOAA and WONDER remain partial releases; see the limitations below.**
See [release status](docs/STATUS.md), [known differences](docs/SCOPE.md), and [third-party terms](docs/THIRD_PARTY.md).

This repository contains independent reconstructions of NOAA Climate at a Glance,
Census / ACS, CDC WONDER, arXiv, and Wateroffice. It is not affiliated with or endorsed
by these agencies or services. These environments reproduce a documented subset
of interactions and data; they are not complete replicas of the original websites.

## Distribution

- Source, Dockerfiles, acquisition tools and tests: this repository.
- Versioned data archives: [v0.1.0 Release](https://github.com/Ninggggy/sgr-webenv/releases/tag/v0.1.0).
- Runtime containers: associated GHCR packages (when builds pass).
- Task answers and author audit directories are never mounted in runtime containers.

## Installation

The supported target is Linux amd64, Docker Engine with Compose v2 and Python 3.9+.
The Docker version must support isolated bridge networks. Preparation downloads
artifacts; evaluation runtime uses internal networks and does not require the Internet.

For Census, arXiv, or Wateroffice:

```sh
python3 tools/env.py prepare arxiv --release v0.1.0
python3 tools/env.py start arxiv --mode preview
# Open http://127.0.0.1:8083
python3 tools/env.py verify arxiv
python3 tools/env.py reset arxiv
python3 tools/env.py stop arxiv
```

Replace `arxiv` with `census` or `wateroffice`. NOAA has no redistributable chart image; WONDER has no public data archive. The default start
mode is `eval`, with no host ports. Preview exposes only a proxy on loopback.
`verify` performs a health smoke check, **not benchmark correctness acceptance**.
Unreleased environments refuse installation unless the author explicitly uses
`--allow-candidate`; unpublished data cannot be downloaded automatically.

State is stored under `.state/<release>/<site>` or `--state-dir`. Stopping does not
remove data or the arXiv index. Reset recreates website/browser containers, clears
their transient state and leaves read-only data and the index intact. Do not run
two instances of one site with the same Compose project name concurrently.

## Building

```sh
python3 tools/build.py base
python3 tools/build.py arxiv
python3 -m unittest discover -s tests -v
```

After building, use `prepare --local-images --data-archive /path/to/data.tar.gz`
to install the locally built images without pulling replacement tags. This still
requires a released environment (or explicit author `--allow-candidate`), and
validates that the local images target Linux amd64.

Builds require online access to Ubuntu, PyPI, Chrome for Testing and (for arXiv)
Elastic/Maven artifacts. Runtime does not. arXiv keeps Elasticsearch 6.2.4 and ICU
compatibility; this research environment must not be exposed as a public service.
Resource measurements and clean-install results will be recorded in
[STATUS](docs/STATUS.md); do not infer minimum RAM or install time from original-host runs.

## License and citation

New project code is Apache-2.0. Upstream source, archived website assets, fonts,
maps, and data retain their respective terms; the root license does not relicense
them. See [NOTICE](NOTICE) and [third-party inventory](docs/THIRD_PARTY.md).

Cite the SGR-BENCH paper and the exact repository/data release used. Bibliographic
paper metadata is not invented here; the release tag and repository URL identify
this software independently of the paper.

[Operation, upgrades and rollback](docs/OPERATIONS.md).
