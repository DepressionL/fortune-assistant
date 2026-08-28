# fortune-assistant —— 可靠的 Python 算命辅助工具

一个把「历法换算 + 排盘」做扎实、把「解读」明确标注为经验规则的命令行工具。
核心原则：

1. **历法/干支/安星一律依赖经过验证的第三方库**，不硬造天文轮子；
2. **必须硬编码的表逐项标注古籍出处**（核验过程见 `research/*.md`）；
3. **所有流派分歧做成配置项**，默认取主流口径，报告里注明；
4. **黄金用例回归测试**，双引擎交叉验证。

> ⚠️ 使用声明：八字/紫微等术数属传统民俗文化。本工具保证的是**排盘与历法换算的正确性**
> （可验证、可复现），用神、断语等解读输出为流派相关的经验规则，仅供参考研究。

---

## 功能一览

| 模块 | 内容 | 数据来源/引擎 |
|---|---|---|
| 历法核心 | 公历↔农历、干支、节气精确时刻、真太阳时（经度差+均时差）、1986–1991 夏令时 | lunar-python（主）、astral（EoT）、sxtwl（交叉验证） |
| 八字 | 四柱、藏干、十神、纳音、地势、旬空、胎元命宫身宫、大运起运、合冲刑害、神煞（18 项）、五行旺衰打分、用神（4 流派规则引擎） | lunar-python EightChar/Yun + 《三命通会》《渊海子平》核验表 |
| 紫微斗数 | 十二宫、十四主星、辅星杂曜、四化、大限、命主身主、五行局；Markdown + SVG 盘面 | **x-iztro**（iztro v2.5.8 移植，716,314 条黄金用例） |
| 六爻 | 起卦装卦：世应、纳甲、六亲、六神、旬空、动变 | 《增删卜易》《卜筮正宗》核验表 |
| 梅花易数 | 数字起卦/农历时间起卦：本卦互卦变卦、体用生克 | 邵雍《梅花易数》通行本 + 通行《周易》64 卦 |
| 小六壬 | 月日时三数落宫 + 六宫断辞 | 通行本多源交叉核验 |
| 称骨 | 年/月/日/时骨重 + 判词（通行男命版） | 通行本多源交叉核验（托名袁天罡） |

## 安装与运行

```powershell
cd path-to-fortune-assistant
python -m venv .venv
# 建议使用清华镜像（本机已写入 .venv\pip.ini；命令行可再显式指定）：
.venv\Scripts\python -m pip install -e . -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
.venv\Scripts\python -m pip install pytest sxtwl -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn

# 运行（任选其一）：
fortune.cmd bazi -y 1990 -m 6 -d 15 -H 13 -M 30 -g 男          # 项目内启动器（无需安装）
.venv\Scripts\fortune.exe bazi -y 1990 -m 6 -d 15 -H 13 -M 30 -g 男   # 可编辑安装后的命令
.venv\Scripts\python -m fortune.cli bazi -y 1990 -m 6 -d 15 -H 13 -M 30 -g 男

fortune ziwei -y 1990 -m 6 -d 15 -H 13 -M 30 -g 男 --svg ziwei.svg
fortune chenggu -y 1990 -m 6 -d 15 -H 13
fortune xiaoliuren --month 5 --day 23 --hour-zhi 未
fortune meihua 12 34
fortune liuyao --backs 2,3,1,0,3,2 --month-zhi 午 --day-ganzhi 甲子
fortune solar-info -y 2024 -m 2 -d 10
```

常用选项（八字）：`--lng 116.4`（出生地东经）、`--no-true-solar`（关闭真太阳时）、
`--day-change 23|0`（换日时刻）、`--dst`（1986–1991 夏令时）、`--school wangshuai|tiaohou|tongguan|geju`、
`--shensha-base day|year`、`--json`、`--md 报告.md`、`--svg 五行.svg`。

## 争议项与默认口径（可配置）

| 争议 | 默认（主流） | 对立口径 | 配置项 |
|---|---|---|---|
| 夜子时换日 | **23:00 换日**（传统子平主流，邵伟华《四柱预测学》等） | 0:00 换日（lunar-python/sxtwl 库默认，部分现代软件） | `day_change_hour` |
| 换年 | 八字按**立春精确时刻**；生肖/称骨按正月初一 | 少数以正月初一论八字年柱 | `year_change`（生肖口径固定） |
| 起大运 | 3 天折 1 年 | 2 天/5 天折 1 年（本工具未实现，需自行扩展） | `yun_days_per_year` |
| 真太阳时 | 校正（经度+均时差） | 直接用钟表时间 | `use_true_solar_time` |
| 神煞基准 | 日干/日支（子平法） | 年干/年支（古法禄命） | `shensha_base` |
| 天乙贵人 | 「甲戊庚牛羊」版 | 「庚辛逢虎马」别传（庚→寅午） | 未开放（默认主流） |
| 羊刃 | 阴干无刃 | 少数派阴刃（帝旺位） | 未开放（默认主流） |
| 月德 | 丙壬甲庚（《三命通会》小结「癸」为讹） | 含「癸」的讹本 | 未开放 |
| 用神 | 旺衰平衡 | 调候/通关/格局 | `yongshen_school` |
| 紫微庚年四化 | **天同化忌**（中州派/iztro/现代主流） | 天相化忌（《紫微斗数全书》古法） | `ziwei_geng_sihua` |
| 紫微闰月 | 按当月 | 十五分界（iztro 默认 fix_leap）；按下月不支持 | `ziwei_leap_month` |
| 称骨判词 | 通行男命版 | 女命版（未收录） | — |
| 铜钱起卦 | 背=阳=3（老阳） | 背=阴 | `liuyao_coin_back` |

## 正确性保障

- **香港天文台官方数据回归**：`research/hko/` 收录 HKO《公历与农历日期对照表》
  （1901、2024 两年官方文本，来源 hko.gov.hk），`tests/test_hko.py` 逐年逐日核对
  农历月/日（含闰月）与全部节气日期，lunar_python 全部一致。
- **双引擎交叉验证**：八字四柱用 lunar-python 与 sxtwl（独立 C++ 天文历实现）对 9 个基准日
  （含立春边界、早晚子时）逐项对照；唯一真实分歧是「立春当日整日 vs 精确时刻」，
  本工具以 lunar-python 精确时刻为准。见 `research/bazi_golden_cases.md`。
- **均时差实测**：astral 与 NOAA/Meeus 公布值对照（2 月中 −14.2、11 月初 +16.4 分钟），
  见 `research/solar_time.md`。
- **紫微**：不自建安星表，直接用 x-iztro（与 iztro 逐字段对齐、71 万条黄金用例），
  并额外用古籍锚点反验：命身宫公式、紫微天府寅申线镜面对称（索引和≡4）、
  庚年四化、五行局=命宫纳音、大限顺逆。见 `tests/test_ziwei.py`。
- **穷举表校验**：`tests/test_exhaustive.py` 用独立权威清单全量核对 64 卦名（King Wen 序）、
  由「本宫卦逐爻变」规则独立推导复现八宫 64 卦与世应、纳甲地支经典口诀清单、
  神煞公式全干全支穷举、驿马桃花华盖将星劫煞灾煞由三合长生位公式推导核验。
- **测试**：`tests/` 共 80 项断言（黄金用例、HKO 官方数据 4 个年份、穷举表校验、
  争议开关、第二轮审查回归），另 `plugin/test/` 8 项 node 测试；全部通过。
  第二轮攻击者视角独立审查记录见 `research/review_adversarial.md`（发现的
  梅花时支公式/体用生克反转等已全部修复并有回归测试）。

## DSH 原生插件

`plugin/` 目录是 DSH 原生插件（`dsh.bundle` 包，零 npm 依赖，模板与本机已验证的
dsh-stable-asr 一致），提供 `fortune_bazi` / `fortune_ziwei` / `fortune_liuyao` /
`fortune_meihua` / `fortune_xiaoliuren` / `fortune_chenggu` / `fortune_solar_info`
7 个工具，全部调用 `python -m fortune.cli`（计算单一事实源在 Python 侧）。
安装与配置见 [plugin/README.md](plugin/README.md)。

## 项目结构

```
fortune/
├── config.py        # 所有流派争议开关（FortuneConfig）
├── core/            # model(输入)、calendar(归一化)、solar_time(真太阳时/EoT/夏令时)
├── bazi/            # chart(排盘)、shensha(神煞)、relation(合冲刑害)、liunian(流年)、
│                    # strength(旺衰打分)、yongshen(用神规则引擎)
├── ziwei/           # x_iztro 引擎封装 + 争议开关 + Markdown/SVG
├── liuyao/          # 六爻起卦装卦
├── misc/            # meihua / xiaoliuren / chenggu
├── report/          # markdown 报告、svg 盘面
└── cli.py           # typer 命令行
plugin/              # DSH 原生插件（dsh.bundle，7 个 fortune_* 工具）
research/            # 文献核验文档 + HKO 官方历法数据（表出处与分歧的依据）
tests/               # 80 项断言
```

## 文献与数据来源（硬编码表依据）

- `research/bazi_golden_cases.md` —— 八字双引擎对照与 lunar_python 行为逐条核实
- `research/solar_time.md` —— 真太阳时方案选型、EoT 三源对照、夏令时逐日核验
- `research/shensha_tables.md` —— 神煞表（《三命通会》维基文库、《渊海子平》原文核验）
- `research/ziwei_tables.md` —— 紫微安星诀核验清单（含 §6.1 引擎修正附注）
- `research/liuyao_tables.md` —— 六爻纳甲/世应/六亲/六神/旬空（《增删卜易》《卜筮正宗》）
- `research/chenggu_table.md` —— 称骨通行男命版全表
- `research/xiaoliuren.md` —— 小六壬掌诀与断辞
- 梅花易数 64 卦表：通行本《周易》六十四卦（上象+下象规则），与 King Wen 序逐卦核对

## 局限与免责

- 八字用神、旺衰打分、称骨/小六壬断辞为**经验规则**，非确定性算法，不同流派结论可能矛盾；
- 称骨仅收录男命通行版判词；小六壬「小吉五行」等异文已标注存疑；
- 紫微排盘按时辰（两小时）粒度，分钟仅影响跨时辰边界（真太阳时校正后）；
- 传统术数无科学依据，本工具定位为「历法计算正确 + 排盘可复现 + 解读透明可追溯」的民俗研究工具。
