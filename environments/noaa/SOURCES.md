第二版来源与计算更新请优先参见 作者侧修复报告（未随运行包发布） 与 [渠道精度](PRECISION.md)。下文保留第一版取证，旧排名区间不代表第二版当前结果。

# 来源、计算与覆盖

## 原始来源

- NCEI 官方目录：https://www.ncei.noaa.gov/monitoring-content/data/us/climdiv/monthly/current/
- 固定发布版 20260904；2026-09-13 取得。`sources/directory.html` 保存目录；`sources/manifest.json` 逐文件记录 URL、字节数和取得时间。92 文件合计 1,776,441,760 字节，无下载失败。包含县/分区/州、AK/HI、SPI、常态值、站点清单与说明/边界等目录全部条目，不宣称归档整个 NOAA 门户。
- 页面与资源来自 https://www.ncei.noaa.gov/access/monitoring/climate-at-a-glance/ 。当前页面、配置、递归资源在 sources/site；代表性真实 Chrome 截图为 sources/source-complete.png，视口1440×1000；sources/source-complete-observation.json 记录实际控件。
- 历史 HTML 在 sources/archive.html；保留五下拉框语义。原题文件与历史三个 JSON 留在作者目录，未复制进运行镜像。
- sources/Q1-current.json 至 Q7-current.json 为七组完整官方候选响应；sources/checks 为34组额外官方响应；这些证据不会在运行时使用。

## 实际可查询

48 个本土州、344 气候分区，1895-01—2026-08。tavg/tmax/tmin、pcp、hdd/cdd、zndx、pdsi/phdi/pmdi。月份1–12；时长1–12、18、24、36、48、60及 YTD（Palmer 三个非Z指标仅1月）。2026年后续未发布月份以及历史起点前的完整窗口为缺失。

州与分区使用各自官方序列，不用分区平均替代州数据。官方州文件前三位编码，分区前四位编码。110为官方CONUS汇总，仅概览使用，不能计为第49州。SQLite存全年12个月、缺失标志、地点/参数/年份主键。data/coverage.json 为实际导入统计；data/metadata.json 为地点和参数元数据。

温度和Z按月平均；HDD/CDD/降水求和。基期1901–2000，针对相同终止月与时长的完整窗口取均值；任何缺月窗口不插补。内部有理数计算、显示四舍五入与负零归一。单位温度°F、降水inch、度日°Df、Palmer无量纲。实现与测试分别对照官方输出，而非仅彼此重复公式。

## 初版排名缺口（历史记录，修复前）

离线按显示精度数值计算最低并列位置，输出 rankEnd 和其他并列数量。七组必要查询的官方排名均位于离线并列区间，但并列序位常不同。34组扩展查询还发现：

| 官方查询 | 分区 | 官方Rank | 离线区间 |
|---|---:|---:|---:|
| California tmax / 193402 / 10 | 0401 | 90 | 83–89 |
| California tmin / 193402 / 10 | 0406 | 22 | 24–29 |

数值/距平/均值一致不足以推出历史排名一致。已试验原始/显示精度、不同排序方式、正反序、缺失值与不同NumPy版本，未复现统一官方规则；可能涉及发布或内部精度，尚无证据可确定归因。不能通过硬编码上述名次、隐藏差异或扩大并列范围宣称通过。保留原始回答、rank-probe 程序/输出及 final-data-report.json；此项仍需可复核的官方精度或排名实现依据。

## 网页与下载精度

官方 `?raw=1` 给前端Z等指标四位小数值/距平（度日仍为整数），mean为显示精度；标准JSON下载按参数精度舍入。七组原始响应已保存为 Q*-current-raw.json，并在 raw-ui-check.json 独立比较。前端使用原站格式化逻辑，因此恰好位于中点时，网页可能与下载差0.01，例如1907-04十月Z的4101网页1.32、下载1.33；这是实测原站行为，不是数据改写。离线保留该精度路径。
