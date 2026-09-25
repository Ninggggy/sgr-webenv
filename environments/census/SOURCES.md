# 来源与发布覆盖 — 应用 0.2.1

本文件保留数据来源记录；其中 `sources/`、`validation/` 是作者侧取证路径，不随运行包提供。当前打包验收见 [发布状态](../../docs/STATUS.md)。应用版本为 0.2.1，数据沿用既有归档。

旧历史CSV、官方API元数据、按年地图和2026-04原站截图证据保持原样。全国API/目录取得成功并不等于全国数值已归档。

## 本次官方Summary批次

原件在`sources/summary/{2016..2019}/{acs5|acs1}`。28个州发布ZIP：DE/ME/WY各四年ACS5与ACS1，加PA2016/CA2017/NC2018/NM2019 ACS1。每个ZIP旁`*.source.json`记录原URL、固定年/产品、取得及检查时间、字节、ZIP成员数和展开字节。布局TXT、Geo模板ZIP、官方附录XLS及`appendix-fields.json`一并保存。附录取得日和来源在字段JSON内；完整清单见`raw-source-inventory.json`（作者侧证据）。

官方路径为`https://www2.census.gov/programs-surveys/acs/summary_file/{year}/data/{5|1}_year_by_state/`。ACS5文件为`{State}_All_Geographies_Not_Tracts_Block_Groups.zip`，ACS1为`{State}_All_Geographies.zip`。下载自官方本机可访问路径，未用第三方推测值。服务器403及API返回MissingKey HTML的失败证据保留；本机标准HTTP Range续传按响应范围、长度及ZIP检查，下载失败不会换成HTML归档。元数据来源固定年度API及Summary lookup。

## 原始归档与UI分别统计

`coverage-inventory.csv`（作者侧证据）列逐州年数值格、可查询表数、地理数和原件状态，JSON另列全部表ID。ACS5三州导入全部序列中的040/050、component00记录，州行来自直接发布值。完整原始ZIP还包含更细或其他地理，UI只开放州县。ACS1所有原始表已在16个州年包内归档，UI仅导入15核心表：B01001、B08201、B09010、B11010、B16004、B18105、B19013、B25003、B25014、B25024、B25044、B25070、B28002、B28011、C16002。

ACS5目录2016/17/18/19分别1046/1127/1135/1136表；ACS1为1310/1372/1376/1376，2016 Summary比API目录多7张PR表，两个渠道的差异保留。表数不代表每个地区都发布；nation-only、state-only、PR等限制依据原始附录和表标题。全空来源单元格与本地缺档分开，不推测全空原因。

发布地区来自每个原始包的当年地理文件，覆盖表同时保留选中地区和官方发布地区。全国地图每年52州级、3220县级边界仅用于选区；不证明未下载州年产品的发布资格。`national-missing-inventory.csv`（作者侧证据）逐项记录未完成部分。完整全国数值、全部必要历史修订/勘误归档尚未完成。

2017附录Universe列存在与表标题不相符的行，不覆盖已有年度lookup/API定义；独立检查说明保留。变量层级来自年度官方标签；单位依据表标题识别，未逐变量人工认证所有特殊单位。新题作者仍须检查所用变量定义。

## 维护

`tools/fetch-summary.py`用于明确州、年份、产品的官方归档，支持已验证缓存复用和续传；失败退出非零并记录证据。原工程的 `prepare-data` 命令只从已缓存资料重建独立库，拒绝覆盖当前数据库。2016/17 XLS解析依赖作者环境`tools/requirements-author.txt`，不进入网站运行期。独立重建与候选库所有数据表比较相同，见rebuild-comparison-final.json。部署是单独步骤。

## 交互参考与边界

采用原任务2026-04保存的表格组织和官方2025–2026说明，数据发布年仍固定为2016–2019，不把前端伪称2016年的网站。

- [2026-02换表指南](https://www2.census.gov/data/api-documentation/how-to-search-for-a-new-table-without-losing-selected-geos.pdf)：搜索按钮保留地理，点击建议项会丢失先前筛选。重建建议项行为有官方文档依据，不是人为设置陷阱。当前线上版本未能实时交互复测。
- [连续变量custom filter说明](https://www.census.gov/data/what-is-data-census-gov/guidance-for-data-users/frequently-asked-questions/how-can-i-create-a-custom-filter.html)：使用大于等于等比较，URL示例 `tableFilters=ESTAB~(50ge)`。本环境实现相同运算符编码用于ACS变量；旧表筛选在换表时清除。跨表自动清除是本地明确的作用域规则，未获得当前原站该边界操作的实时对照。
- [表格与下载功能](https://www.census.gov/data/what-is-data-census-gov/guidance-for-data-users/frequently-asked-questions/can-i-modify-tables-download-data-and-print-data.html)及[定制是否带入下载](https://www.census.gov/data/what-is-data-census-gov/guidance-for-data-users/frequently-asked-questions/do-the-customizations-in-my-table-view-carry-over-to-the-download.html)：CSV/Excel保留定制，ZIP不保留。本环境导出全部定制行，不按滚动窗口截断。
- 原始CSV和DOM展示转置后地理组下Estimate/MOE两行；本地按此修复。原站多级列头、结果/过滤器三栏及部分工具条视觉仍与本地不完全相同，截图并列保留，未宣布像素或全行为一致。

## 工具协议

原项目 `runs/open-source/sgr-bench/README-开源用.md`第181行起声明Serper、Fetch和PDF工具，并未规定只能在浏览器中点击。离线版将外部搜索限制为本地表目录；保留网页可见接口和下载，并提供有界Census API请求格式。浏览器模式与API模式必须分别报告，当前没有付费模型实验或新分数。

本地API的NAME附带标准州后缀，E/M/EA/MA来自同一运行库；历史格式化CSV没有保存的原API特殊负值标记不重建。外部Census来源仅固定映射到本地Census路由，不提供任意URL代理。三个原始域名在本版本合并为一个本地origin；尚未验证依赖跨origin存储隔离的流程。


本次地图选区参考[官方2025-06-17地图指南，第61、69页](https://www2.census.gov/about/training-workshops/2025/2025-06-17-mapping-made-simple-presentation.pdf)的“Select geographies”工作流：点击地理后显式选择/取消，再更新选区。实现的URL、表格、下载联动已实测；具体工具条布局、逐步提示和所有原站切换边界仍未取得完整实时对照，不宣称完全一致。同源合并仅认证当前无cookie/localStorage的URL状态工作流；跨origin认证、嵌入、历史记录等未进入本次范围。
