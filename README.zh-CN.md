# SGR-WebEnv

SGR-BENCH 配套的离线网站环境，结合网站界面、固定数据和隔离浏览器，支持交互式搜索、页面浏览与数据查询。

[English](README.md)

| 环境 | 功能 | 端口 |
|---|---|---:|
| Census / ACS | ACS 表格、地理选区、地图和导出 | 8081 |
| CDC WONDER | 全国出生与关联婴儿死亡数据查询 | 8082 |
| arXiv | 元数据搜索、论文详情和分类浏览 | 8083 |
| Wateroffice | 水文站搜索、观测、地图和下载 | 8084 |
| ChemExpo / CPDat | 化学物质与产品搜索、分类、关联查询和下载 | 8085 |
| Cellosaurus | 细胞系搜索、记录、下载和 CLASTR | 8086 |
| NOAA Climate at a Glance | 气候查询、地图、时间序列和导出 | 8080 |

## 运行环境

使用 Linux amd64、支持 Compose v2 的 Docker Engine 和 Python 3.9+，在仓库根目录执行。准备阶段下载数据与镜像，准备完成后离线运行。

```sh
python3 tools/env.py prepare cellosaurus --release v0.1.4
python3 tools/env.py start cellosaurus --release v0.1.4 --mode preview
```

打开 `http://127.0.0.1:8086`。将 `cellosaurus` 替换为 `census`、`wonder`、`arxiv` 或 `wateroffice`，并使用表中对应端口。NOAA 请先按照[图表依赖与本地构建说明](environments/noaa/README.md)准备。

```sh
python3 tools/env.py verify cellosaurus --release v0.1.4
python3 tools/env.py reset cellosaurus --release v0.1.4
python3 tools/env.py stop cellosaurus --release v0.1.4
```

`verify` 检查服务健康；`reset` 清空会话和下载，保留数据；`stop` 停止环境。隔离评测使用 `--mode eval`。

详见[运行说明](docs/OPERATIONS.md)。代码和组件条款见 [LICENSE](LICENSE)、[NOTICE](NOTICE) 和[第三方说明](docs/THIRD_PARTY.md)。

ChemExpo / CPDat 使用[本地构建与安装步骤](environments/chemexpo/README.md)。
