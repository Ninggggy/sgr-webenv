# SGR-WebEnv

面向 SGR-BENCH 与网页智能体研究的可复现离线网站环境。

[English](README.md) · [发布版本](https://github.com/Ninggggy/sgr-webenv/releases) · [功能与数据](docs/SCOPE.md) · [操作指南](docs/OPERATIONS.md)

SGR-WebEnv 将网站应用、固定数据和受限浏览器打包为 Docker 环境，支持在本地开展交互式搜索、页面浏览和数据查询研究。资源准备完成后，已支持的工作流可以离线运行，无需连接原网站。

仓库包含六个网站的独立复现。各环境均有明确的数据与功能范围。各网站以独立的离线环境提供。

## 网站环境

| 环境 | 主要功能 | 安装方式 | 预览端口 |
|---|---|---|---:|
| Census / ACS | ACS 表格、地理选区、地图和定制导出 | 预构建镜像 | 8081 |
| CDC WONDER | 全国出生与关联婴儿死亡数据查询、图表和 CSV 导出 | 预构建镜像 | 8082 |
| arXiv | cs/math/stat 元数据、搜索、版本时间线和分类浏览 | 预构建镜像 | 8083 |
| Wateroffice | 水文站搜索、历史与归档实时观测、地图和下载 | 预构建镜像 | 8084 |
| Cellosaurus | 细胞系记录、搜索、关联导航、下载和 CLASTR | 预构建镜像 | 8086 |
| NOAA Climate at a Glance | 气候查询、地图、时间序列图表和数据导出 | Available · [自行准备图表依赖](environments/noaa/README.md) | 8080 |

具体数据与查询边界见[功能与数据范围](docs/SCOPE.md)。

## 快速开始

运行要求：**Linux amd64**、支持 **Compose v2** 的 Docker Engine，以及 **Python 3.9+**。准备阶段需要联网下载数据和镜像。各环境的资源需求不同，安装前请查看 [资源配置说明](docs/OPERATIONS.md)。

```bash
git clone --branch main https://github.com/Ninggggy/sgr-webenv.git
cd sgr-webenv

python3 tools/env.py prepare cellosaurus --release v0.1.3
python3 tools/env.py start cellosaurus --release v0.1.3 --mode preview
# 浏览器打开 http://127.0.0.1:8086/
```

将 `cellosaurus` 替换为 `census`、`wonder`、`arxiv` 或 `wateroffice`，并使用上表对应端口即可。发布清单会选择对应的数据包和镜像版本；未变更的材料沿用早期发布附件。arXiv 的准备过程还会构建本地搜索索引。

本版本的后续命令也请显式指定 `--release v0.1.3`：

```bash
python3 tools/env.py verify cellosaurus --release v0.1.3
python3 tools/env.py reset cellosaurus --release v0.1.3
python3 tools/env.py stop cellosaurus --release v0.1.3
```

- `verify` 检查服务健康。
- `reset` 清空网站和浏览器的临时状态及下载，保留数据与 arXiv 索引。
- `stop` 停止环境，保留持久化数据。

预览模式仅绑定 `127.0.0.1`。评测时省略 `--mode preview` 或指定 `--mode eval`：这是默认模式，不向宿主机开放端口。运行容器使用隔离网络，不挂载题目答案或作者审计目录。

状态默认保存在 `.state/<release>/<site>`，可用 `--state-dir` 修改基础目录。浏览器接入、升级、回退和多实例管理见 [操作指南](docs/OPERATIONS.md)；Cellosaurus 的具体功能见 [站点说明](environments/cellosaurus/README.md)。

## NOAA：先自行准备图表依赖

NOAA 采用本地源码构建方式提供。**请从官方渠道自行下载 ZingChart，并在本地构建 NOAA 镜像。**

1. 从 [ZingChart 官方下载页](https://www.zingchart.com/download)或其提供的 npm 渠道获取 **2.9.16-1**，并确保所持许可适用于自己的使用方式。
2. 将完整包内容放入 `environments/noaa/app/static/cag/assets/zingchart-2.9.16-1/`，其中应包含 `es6.js` 和 `zingchart-es6.min.js`。
3. 按 [NOAA 专用说明](environments/noaa/README.md)检查依赖、构建本地镜像并启动。准备 NOAA 时使用 `--local-images` 选择本地构建的镜像。

准备完成后，图表库从本地加载，运行时不依赖在线 CDN。保留组件版权声明及许可要求的品牌标识；若要再分发组件或包含它的镜像，应另行确认相应权限。具体见[许可说明](docs/THIRD_PARTY.md)。

## 源码、数据与镜像

| 材料 | 位置 |
|---|---|
| 应用源码、Dockerfile、数据准备工具与测试 | 本仓库 |
| 固定版本的数据包 | [GitHub Releases](https://github.com/Ninggggy/sgr-webenv/releases) |
| 应用与受限浏览器镜像 | [GHCR Packages](https://github.com/Ninggggy/sgr-webenv/packages) |
| 具体下载地址与镜像版本 | [v0.1.3 发布清单](releases/v0.1.3.json) |

如需从源码构建，以 Cellosaurus 为例：

```bash
python3 tools/build.py base
python3 tools/build.py cellosaurus
python3 tools/env.py prepare cellosaurus --release v0.1.3 \
  --local-images --data-archive /path/to/cellosaurus-data-v0.1.2.tar.gz
```

构建阶段需要联网获取上游依赖，运行阶段使用已准备好的本地资源。arXiv 为保持查询兼容性，保留 Elasticsearch 6.2.4 及对应 ICU 配置；这些研究环境应在本地或隔离网络中使用，不应直接作为公共服务开放。

## 许可与引用

项目自有代码采用 **Apache-2.0**。上游代码、数据、字体、地图和归档资源保留各自条款，详见 [NOTICE](NOTICE) 与 [第三方材料清单](docs/THIRD_PARTY.md)。

Cellosaurus 数据采用 **CC BY 4.0**；CLASTR 及其修改保留 **GPL-3.0**，并提供对应源码。WONDER 数据须遵守 [NCHS 使用条件](environments/wonder/licenses/DATA_USE_NOTICE.md)。

研究中使用这些环境时，请引用 SGR-BENCH，并记录仓库地址、发布标签以及所用环境和数据版本。

Wateroffice `0.1.0` 保留2,248站目录，其中483站提供30天观测及官方状态，其余1,765站沿用原快照。详见[安装与回退说明](environments/wateroffice/README.md)和[验收报告](reports/wateroffice-0.1.0/README.md)。
