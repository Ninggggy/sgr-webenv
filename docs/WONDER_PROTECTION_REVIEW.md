# WONDER 保护规则专项核验（2026-09-26）

**结论：17 项均为保留的额外祖先保护；未发现计数、加权舍入、分母或传播范围错误。应用继续使用 0.3，数据与镜像不变。**

## 原因与范围

当前实现会隐藏同一分组中受抑制类别的已显示祖先。例如同时选择父类别和某个受保护子类别时，父类别也会受到额外保护；只选择父类别时，不会凭空加入未选择的子类别来触发这条规则。保护不跨年份、性别或无关分类传播。

这是与归档原站结果的显示策略差异，不是底层统计量缺失。出生分母在受保护死亡行中也继续隐藏；这一独立差异同样保留。此次没有删除保护规则，也没有通过隐藏正常分类来消除差异。

官方要求抑制 1–9 的出生或死亡统计，并保护包含单个受抑制项的总计、小计。详见 [官方说明](https://wonder.cdc.gov/wonder/help/lbd-expanded.html)。本次比较基于 2026-09-17 保存的官方页面，不宣称是新的实时原站比较。

## 逐项结论

下列各项的原始计数、加权舍入、出生分母和可比较的官方数值均核对通过，且均存在同组内受保护的已显示后代。

| 类别代码 | 类别名称 | 结论 |
|---|---|---|
| GR130-001 | Certain infectious and parasitic diseases (A00-B99,U07.1) | 额外祖先保护，保留 |
| GR130-012 | Viral diseases (A80-B34,U07.1) | 额外祖先保护，保留 |
| GR130-033 | Endocrine, nutritional and metabolic diseases (E00-E88) | 额外祖先保护，保留 |
| GR130-039 | Diseases of the nervous system (G00-G98) | 额外祖先保护，保留 |
| GR130-046 | #Diseases of the circulatory system (I00-I99) | 额外祖先保护，保留 |
| GR130-053 | Diseases of the respiratory system (J00-J98,U04) | 额外祖先保护，保留 |
| GR130-055 | #Influenza and pneumonia (J09-J18) | 额外祖先保护，保留 |
| GR130-070 | Certain conditions originating in the perinatal period (P00-P96) | 额外祖先保护，保留 |
| GR130-071 | Newborn affected by maternal factors and by complications of pregnancy, labor and delivery (P00-P04) | 额外祖先保护，保留 |
| GR130-079 | #Newborn affected by complications of placenta, cord and membranes (P02) | 额外祖先保护，保留 |
| GR130-086 | Disorders related to length of gestation and fetal malnutrition (P05-P08) | 额外祖先保护，保留 |
| GR130-105 | Infections specific to the perinatal period (P35-P39) | 额外祖先保护，保留 |
| GR130-109 | Hemorrhagic and hematological disorders of newborn (P50-P61) | 额外祖先保护，保留 |
| GR130-138 | External causes of mortality (*U01,V01-Y84) | 额外祖先保护，保留 |
| GR130-139 | #Accidents (unintentional injuries) (V01-X59) | 额外祖先保护，保留 |
| GR130-140 | Transport accidents (V01-V99) | 额外祖先保护，保留 |
| GR130-152 | #Assault (homicide) (*U01,X85-Y09) | 额外祖先保护，保留 |

## 验证结果

- 重新读取原始归档，按官方分类控件独立建立层级；叶类别计数与权重均与数据库一致。
- 10 组独立计算对照通过：全部类别、父类别单选、重叠、少量类别、无关分支、跨年、合并年份、性别、人群和死亡年龄；同时核对 API、CSV、状态及禁用汇总。
- 8 组新增合成测试通过，覆盖小计数、舍入、可靠性边界、祖先传播范围、一个或多个受抑制项、隐藏行和选择顺序。
- 70 条查询重新通过网页提交与下载，API 结果及 CSV 均与此前验收结果一致；四条 CG/GO 答案回归通过，另有 48 项来源计数核对通过。
- 32 项网页检查及 2 项隐藏行检查通过，包括 HTML 与 API 单元格一致、图表保护、保存与恢复；无 JavaScript 错误。
- 当前页面没有用户可切换的表格排序控件；本轮验证选择顺序不影响结果，不新增排序功能。

初次在现有浏览器容器内启动额外浏览器时触及进程数上限。后续使用独立临时容器完成测试，沿用原有限额与安全配置，未调整现有部署。

## 交付与复测

[逐项 CSV](verification/wonder-parent-classification-20260926.csv) · [机器可读报告](verification/wonder-protection-20260926.json)

仅公开分类结论和测试结果，不公开受限制的小计数、题目答案或作者资料。没有代码修复需求，因此不发布 0.3.1，也不重新打包数据。

```bash
python3 -m unittest discover -s tests -p test_wonder_protection.py -v
```

这些检查是来源核验与网页工作流回放，不是模型自主解题成功率。
