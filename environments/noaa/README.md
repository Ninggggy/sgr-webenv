# NOAA: local setup with a user-supplied chart dependency

NOAA is available as source and data with a **manual chart-dependency step**. The project does not distribute ZingChart or prebuilt NOAA images containing it. Follow this guide on Linux amd64 with Docker Compose v2 and Python 3.9+.

## 1. Download the dependency yourself

Use the [official ZingChart download page](https://www.zingchart.com/download), which also links to the npm package. The required package version is **2.9.16-1**; the archived library is identified internally as **2.9.16-hf1**. Do not substitute an unpinned latest version.

Before using the library, check the [applicable terms](https://www.zingchart.com/pricing/branded-license). The Branded license permits use subject to its branding requirements but excludes distributing the library in installable software products. This repository does not grant you a license, remove branding, or provide an OEM redistribution right. If your use is not covered by your license, obtain suitable permission before proceeding. Do not publish locally built images containing the library without that permission.

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

Alternatively download through the official page and place the package contents in the same directory. Keep the full package and its embedded notices. The directory is ignored by Git; do not force-add it, commit license keys, or upload the downloaded package to this repository or its Releases.

## 2. Check the files and build locally

Run the following check before building. A successful check verifies the package version and required files, not your licensing rights.

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

Build the two images locally. The registry-shaped tags below match the existing manifest; these commands **do not push** them to the registry. Docker obtains the public base images when needed.

```bash
docker build --platform linux/amd64 \
  -t ghcr.io/ninggggy/sgr-webenv-release-noaa-web:2 \
  -f environments/noaa/Dockerfile.web environments/noaa

docker build --platform linux/amd64 \
  -t ghcr.io/ninggggy/sgr-webenv-release-noaa-browser:2 \
  -f environments/noaa/Dockerfile.browser environments/noaa
```

`tools/build.py noaa` remains disabled for the public distribution workflow. Use the explicit local commands above; the public build workflow must not publish user-supplied proprietary files.

## 3. Prepare data and run

```bash
python3 tools/env.py prepare noaa --release v0.1.2 \
  --local-images --allow-candidate
python3 tools/env.py start noaa --release v0.1.2 \
  --allow-candidate --mode preview
# Open http://127.0.0.1:8080/

python3 tools/env.py verify noaa --release v0.1.2
python3 tools/env.py reset noaa --release v0.1.2
python3 tools/env.py stop noaa --release v0.1.2
```

`--local-images` selects the locally built images. The commands retain `--allow-candidate` for compatibility with the original release-tag installer; the main-branch installer recognizes NOAA as a local-build distribution. `verify`, `reset`, and `stop` use the installed configuration.

For evaluation, replace `--mode preview` with `--mode eval`; no host port is published. Chart files are served by the local application, without a runtime CDN dependency. Data remain mounted read-only. Keep at least 5 GiB free while preparing and building.

## Using the environment

`verify` checks HTTP health. Open a time-series page after installation to check the locally supplied chart dependency. For calculations and exact-ranking queries, consult [numeric rules](PRECISION.md) and [data scope](../../docs/SCOPE.md).

## 中文说明

NOAA 采用“自行准备依赖 + 本地构建”的方式安装：

1. 自行从 ZingChart 官方渠道下载 **2.9.16-1**，确认自己的使用方式符合相应许可。
2. 按上方目录放置完整包，运行文件与版本检查。
3. 使用上方两条 `docker build` 命令构建本地镜像，不推送含图表库的镜像。
4. `prepare` 使用 `--local-images --allow-candidate`，`start` 使用 `--allow-candidate`；数据包由现有公开 Release 下载。
5. 打开 `http://127.0.0.1:8080/`，检查查询与时间序列图表。评测模式使用 `--mode eval`。

`--local-images` 使用本地构建的镜像。上述命令保留 `--allow-candidate` 以兼容原始发布标签中的安装工具；主分支安装工具直接识别 NOAA 的本地构建方式。图表库由用户准备，运行时从本地加载。组件使用与再分发遵循其许可条款。
