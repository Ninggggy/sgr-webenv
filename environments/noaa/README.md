# NOAA: local setup with a user-supplied chart dependency

Install NOAA by **downloading ZingChart from its official distribution and building the images locally**. Follow this guide on Linux amd64 with Docker Compose v2 and Python 3.9+.

## 1. Download the dependency yourself

Use the [official ZingChart download page](https://www.zingchart.com/download), which also links to the npm package. The required package version is **2.9.16-1**; the archived library is identified internally as **2.9.16-hf1**. Use this version for the local build.

Use ZingChart under the [applicable license terms](https://www.zingchart.com/pricing/branded-license), retaining the required branding and notices. Distribution in installable software products requires the applicable OEM permission; see [third-party terms](../../docs/THIRD_PARTY.md).

From the repository root, an explicit download through the official npm channel is:

```bash
mkdir -p .state/noaa-dependency
curl --fail --location \
  https://registry.npmjs.org/zingchart/-/zingchart-2.9.16-1.tgz \
  --output .state/noaa-dependency/zingchart-2.9.16-1.tgz

mkdir -p environments/noaa/app/static/cag/assets/zingchart-2.9.16-1
tar -xzf .state/noaa-dependency/zingchart-2.9.16-1.tgz \
  --strip-components=1 \
  -C environments/noaa/app/static/cag/assets/zingchart-2.9.16-1
```

Alternatively download through the official page and place the package contents in the same directory. Keep the full package and its embedded notices. Store the package and any license keys locally; the dependency directory is excluded from Git.

## 2. Check the files and build locally

Before building, check the package version and required files:

```bash
python3 - <<'PY'
import json
from pathlib import Path
p = Path('environments/noaa/app/static/cag/assets/zingchart-2.9.16-1')
for name in ('package.json', 'es6.js', 'zingchart-es6.min.js'):
    if not (p / name).is_file() or not (p / name).stat().st_size:
        raise SystemExit('Missing chart dependency: ' + str(p / name))
if json.loads((p / 'package.json').read_text())['version'] != '2.9.16-1':
    raise SystemExit('Expected ZingChart 2.9.16-1')
print('Required chart files are present.')
PY
```

Build the two images locally using the tags selected by the release manifest. Docker obtains the public base images when needed.

```bash
docker build --platform linux/amd64 \
  -t ghcr.io/ninggggy/sgr-webenv-release-noaa-web:2 \
  -f environments/noaa/Dockerfile.web environments/noaa

docker build --platform linux/amd64 \
  -t ghcr.io/ninggggy/sgr-webenv-release-noaa-browser:2 \
  -f environments/noaa/Dockerfile.browser environments/noaa
```

Use the two `docker build` commands above for NOAA.

## 3. Prepare data and run

```bash
python3 tools/env.py prepare noaa --release v0.1.3 \
  --local-images
python3 tools/env.py start noaa --release v0.1.3 \
  --mode preview
# Open http://127.0.0.1:8080/

python3 tools/env.py verify noaa --release v0.1.3
python3 tools/env.py reset noaa --release v0.1.3
python3 tools/env.py stop noaa --release v0.1.3
```

`--local-images` selects the locally built images. `start`, `verify`, `reset`, and `stop` use the prepared environment.

For evaluation, replace `--mode preview` with `--mode eval`; no host port is published. Chart files are served by the local application, without a runtime CDN dependency. Data remain mounted read-only. Keep at least 5 GiB free while preparing and building.

See [operation and resource requirements](../../docs/OPERATIONS.md) and [data definitions](SOURCES.md).
