# SGR-WebEnv：离线网站环境

本仓库整理 NOAA、Census / ACS、WONDER、arXiv、Wateroffice 五个独立环境。
**目前仍是私有发布候选，不表示五站已经完成开源安装验收。**

源码放在仓库，固定数据放在 GitHub Releases，镜像放在关联 GHCR。
不需要原作者的服务器账号。本站不是任何原网站的官方产品或背书项目。

## 使用方式

正式支持 Linux amd64、Docker Compose v2、Python 3.9+；先准备资源，再断网运行。
当前草稿尚不能匿名一键安装。对应环境在发布清单中标为 `ready` 后，可执行：

```bash
git clone https://github.com/Ninggggy/sgr-webenv.git
cd sgr-webenv
git checkout v0.1.0
python3 tools/env.py prepare arxiv --release v0.1.0
python3 tools/env.py start arxiv --mode preview
# 浏览器打开 http://127.0.0.1:8083
python3 tools/env.py verify arxiv
python3 tools/env.py reset arxiv
python3 tools/env.py stop arxiv
```

`prepare` 下载固定数据和镜像，并为 arXiv 构建本地索引。索引不完整时拒绝启动。
数据目录默认是 `.state/v0.1.0/arxiv`；每次命令都可用 `--state-dir` 指定其他目录。
`--allow-candidate` 仅供作者验证候选版，不代表许可问题或验收问题已解决。
当前 NOAA 缺少可再分发的图表组件，WONDER 未提供数据附件，两者不能套用上述
命令宣称完成安装。资源要求与实测情况见 [状态报告](docs/STATUS.md)。

站名与预览端口分别为：

| 站名 | 端口 | 已有任务记录 | 发布范围 |
|---|---:|---:|---|
| noaa | 8080 | 4 | Rank/并列差异；ZingChart 授权未确认，完整安装暂不可发布 |
| census | 8081 | 8 | 当前收录地区、年份和表；非全国全量 |
| wonder | 8082 | 4 | 全国分组与既有保护；数据包再分发仍需审查 |
| arxiv | 8083 | 8 | cs/math/stat 最新元数据和版本时间线 |
| wateroffice | 8084 | 10 | 0.1.0-dev，不升级为完整复刻通过 |

`start` 默认隔离评测模式，无宿主机端口。`--mode preview` 仅向本机回环地址开放。
`reset` 清空容器中的会话和下载状态；`stop` 保留数据与索引。
`verify` 只检查服务健康，不代表旧题或模型自主解题验收通过。

## 版本、升级和回退

每个总发布版本记录站点应用、浏览器、数据和来源版本。升级应先停止旧实例，
再在独立状态目录准备新版本；失败时使用旧 Git 标签和旧状态目录恢复。
不要覆盖旧数据库，不要把同一站点的两个版本同时使用相同 Compose 项目名启动。

查看 [当前状态](docs/STATUS.md)、[覆盖与差异](docs/SCOPE.md)、
[第三方材料条款](docs/THIRD_PARTY.md)。准备下载阶段需要网络；网页运行阶段不访问原站。

原有网页回放证据与本次新安装验收分别记录，不表示重新完成了付费模型盲测。

[安装、重置、升级与回退说明](docs/OPERATIONS.md)。
