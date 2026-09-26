# SGR-WebEnv

面向 SGR-BENCH 与网页智能体研究的可复现离线网站环境。

[English](README.md) · [发布版本](https://github.com/Ninggggy/sgr-webenv/releases) · [覆盖与限制](docs/SCOPE.md) · [验收记录](docs/STATUS.md)

SGR-WebEnv 将网站应用、固定数据和受限浏览器打包为 Docker 环境，支持在本地开展交互式搜索、页面浏览和数据查询研究。资源准备完成后，已支持的工作流可以离线运行，无需连接原网站。

仓库包含六个网站的独立复现。各环境均有明确的数据与功能范围。本项目与原网站及其运营机构无隶属或背书关系。

## 环境与发布范围

**v0.1.2 新增 Cellosaurus**，并继续提供 Census、WONDER、arXiv 和 Wateroffice 的已有发布材料。

| 环境 | 发布状态 | 包含内容与主要限制 | 预览端口 |
|---|---|---|---:|
| Census / ACS | 可安装 · 0.2.1 | 已归档的地区、年份与表格；不覆盖全国所有 ACS 产品。 | 8081 |
| CDC WONDER | 可安装 · 0.3 | 全国出生与关联婴儿死亡数据的分组查询、图表及 CSV 导出；已通过查询、交互和旧题回归。 | 8082 |
| arXiv | 可安装 · 0.1.0 | 1,685,244 篇 cs/math/stat 论文的最新元数据与版本时间线；不含旧版本内容、每日公告及全文。 | 8083 |
| Wateroffice | 开发版 · 0.1.0-dev | 已归档水文数据与查询流程；地图、覆盖和外观仍有限制。 | 8084 |
| Cellosaurus | 可安装 · 0.1.0 | Release 56.0 的 168,970 条元数据、核心网站与 CLASTR；不包含完整 REST/RDF/SPARQL 接口。 | 8086 |
| NOAA Climate at a Glance | 源码与数据 | 气候数据与应用源码；组件配置及适用工作流详见[发布说明](docs/STATUS.md)。 | 8080* |

*8080 为 NOAA 配置中的预览端口，部署准备要求见[发布说明](docs/STATUS.md)。*

各站详细功能边界见 [覆盖与差异](docs/SCOPE.md)，发布依据见 [验收记录](docs/STATUS.md)。

## 快速开始

运行要求：**Linux amd64**、支持 **Compose v2** 的 Docker Engine，以及 **Python 3.9+**。准备阶段需要联网下载数据和镜像。各环境的资源需求不同，安装前请查看 [资源测量与验证情况](docs/STATUS.md)。

```bash
git clone https://github.com/Ninggggy/sgr-webenv.git
cd sgr-webenv
git checkout v0.1.2

python3 tools/env.py prepare cellosaurus --release v0.1.2
python3 tools/env.py start cellosaurus --release v0.1.2 --mode preview
# 浏览器打开 http://127.0.0.1:8086/
```

将 `cellosaurus` 替换为 `census`、`wonder`、`arxiv` 或 `wateroffice`，并使用上表对应端口即可。发布清单会选择对应的数据包和镜像版本；未变更的材料沿用早期发布附件。arXiv 的准备过程还会构建本地搜索索引。

本版本的后续命令也请显式指定 `--release v0.1.2`：

```bash
python3 tools/env.py verify cellosaurus --release v0.1.2
python3 tools/env.py reset cellosaurus --release v0.1.2
python3 tools/env.py stop cellosaurus --release v0.1.2
```

- `verify` 检查服务健康，不执行题目正确性验收。
- `reset` 清空网站和浏览器的临时状态及下载，保留数据与 arXiv 索引。
- `stop` 停止环境，保留持久化数据。

预览模式仅绑定 `127.0.0.1`。评测时省略 `--mode preview` 或指定 `--mode eval`：这是默认模式，不向宿主机开放端口。运行容器使用隔离网络，不挂载题目答案或作者审计目录。

状态默认保存在 `.state/<release>/<site>`，可用 `--state-dir` 修改基础目录。浏览器接入、升级、回退和多实例管理见 [操作指南](docs/OPERATIONS.md)；Cellosaurus 的具体功能见 [站点说明](environments/cellosaurus/README.md)。

## 源码、数据与镜像

| 材料 | 位置 |
|---|---|
| 应用源码、Dockerfile、数据准备工具与测试 | 本仓库 |
| 固定版本的数据包与发布报告 | [GitHub Releases](https://github.com/Ninggggy/sgr-webenv/releases) |
| 应用与受限浏览器镜像 | [GHCR Packages](https://github.com/Ninggggy/sgr-webenv/packages) |
| 具体下载地址与镜像版本 | [v0.1.2 发布清单](releases/v0.1.2.json) |

如需从源码构建，以 Cellosaurus 为例：

```bash
python3 tools/build.py base
python3 tools/build.py cellosaurus
python3 tools/env.py prepare cellosaurus --release v0.1.2 \
  --local-images --data-archive /path/to/cellosaurus-data-v0.1.2.tar.gz
```

构建阶段需要联网获取上游依赖，运行阶段使用已准备好的本地资源。arXiv 为保持查询兼容性，保留 Elasticsearch 6.2.4 及对应 ICU 配置；这些研究环境应在本地或隔离网络中使用，不应直接作为公共服务开放。

## 验证与适用范围

验收报告分别记录来源数据核对、网页工作流回放、打包安装和隔离测试，并说明实际安装方式与未验证的配置。这些结果不代表模型自主解题成功率。

WONDER 已通过 10 组独立查询对照、8 组边界测试、70 条网页查询与 CSV 回归，以及四条 CG/GO 和 34 项网页交互检查。17 项父类别显示差异已逐项确认属于保留的额外隐私保护，未发现统计计算或保护传播范围错误；详见 [专项核验报告](docs/WONDER_PROTECTION_REVIEW.md)。应用、数据与镜像继续沿用已发布版本。

Cellosaurus 已完成全量记录来源核对、337 项数据与导出检查、75 项浏览器检查、四条补充题回放，以及数据和镜像的匿名下载验证。详见 [发布报告](docs/verification/cellosaurus-publication-report-v0.1.2.json) 和 [各环境验收记录](docs/STATUS.md)。原有 100 条正式题目中不包含 Cellosaurus。

## 许可与引用

项目自有代码采用 **Apache-2.0**。上游代码、数据、字体、地图和归档资源保留各自条款，详见 [NOTICE](NOTICE) 与 [第三方材料清单](docs/THIRD_PARTY.md)。

Cellosaurus 数据采用 **CC BY 4.0**；CLASTR 及其修改保留 **GPL-3.0**，并提供对应源码。WONDER 数据须遵守 [NCHS 使用条件](environments/wonder/licenses/DATA_USE_NOTICE.md)。

研究中使用这些环境时，请引用 SGR-BENCH，并记录仓库地址、发布标签以及所用环境和数据版本。
