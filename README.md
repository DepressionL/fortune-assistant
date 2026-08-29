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
`--schools wangshuai,tiaohou`（多流派一次对比）、`--shensha-base day|year`、`--json`、`--md 报告.md`、`--svg 五行.svg`。
六爻可用 `--random` 随机模拟三枚铜钱掷六次（真实掷币分布），并自动附带规则化断语
（逐条出处见 `fortune/liuyao/duanyu.py`）；梅花自动附带卦辞爻辞
（通行本《周易》，阮刻《十三经注疏》本文字，见 `fortune/misc/zhouyi.py`）。

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
| 称骨判词 | 通行男命版 | 女命版（未收录，输入「女」时显式警告） | — |
| 铜钱起卦 | 背=阳=3（老阳） | 背=阴 | `liuyao_coin_back` |

## 跨工具口径总表与输入校验

各工具的「时辰」口径不一致是有意为之（术数传统如此），跨工具对比前务必看清：

| 工具 | 时辰口径 | 换日/换年 | 输入校验 |
|---|---|---|---|
| bazi / ziwei / chenggu | **真太阳时校正**（经度+均时差，默认开；`--no-true-solar` 关） | 23:00 换日（可配 0）；八字按立春换年 | 年 1600–2200、公历日期真实性、月 1–12、日 1–31、时 0–23、分 0–59、性别 男/女、经度 ±180、**时区 −12~14（`--timezone`，默认 8=北京时间）**、dst 仅 1986–1991 有效（否则明确报错） |
| solar_info | **钟表时辰**（不做真太阳时校正，输出中已注明） | 同上 | 同上（无性别/经度/时区参数） |
| xiaoliuren / meihua(时间起卦) | **钟表时支**（不校正） | 农历月 1–12、日 1–30 | 时支须为十二地支；梅花数字起卦须 2–3 个正整数 |
| liuyao | 不用出生时间；月建/日辰由占时决定 | — | 月建须十二地支；日辰须为真实存在的六十干支（天干地支阴阳相配）；背数恰 6 个且 0–3；`--random` 随机起卦 |

### 时区与真太阳时的三层校正

记录到的钟面时间通常不是「真太阳时」，本工具按三层处理（报告 steps 逐层可见）：

1. **钟面时间（记录值）**：默认按**北京时间（UTC+8）**理解。海外出生按当地标准时
   传 `--timezone`（如纽约 −5、东京 9）；1949 年前中国「五时区」记录按原时区传
   （昆仑 +5.5 / 新藏 +6 / 陇蜀 +7 / 中原 +8 / 长白 +8.5）。非 8 的时区会先换算为
   北京时间（报告显示「时区 UTC+X → UTC+8」）；1986–1991 夏令时记录传 `--dst`
   先扣 1 小时。
2. **地方平太阳时**：`4×(经度−120)` 分钟。例如东经 112.5° 即 −30.0 分钟——这是
   「经度差」项。
3. **真太阳时**：再加**均时差 EoT**（视太阳时−平太阳时，随日期变化，2 月中约
   −14 分、11 月初约 +16 分）。报告分项显示，如东经 112.5° 的 2000-02-20 10:40：
   「经度差 −30.0 分 + 均时差约 −13.6 分 ≈ −43.6 分」，10:40 → 09:56 前后（巳时）。

> 流派分歧：主流排盘（八字/紫微/称骨）用**真太阳时**；少数派直接用钟表时辰。
> 本工具默认真太阳时，`--no-true-solar` 可切换。梅花/小六壬传统上以钟表时支起课，
> 故不校正——跨工具对比时这是**有意口径差异**，非实现缺陷。

### 文献核验记录（如实说明）

- **《周易》卦辞/爻辞（`fortune/misc/zhouyi.py`）——权威数字版全文比对完成**：
  2026-08-29 抓取 zh.wikisource.org《周易》64 卦子页（通行本经文，Public Domain，
  存档 `research/fetched/zhouyi_pages/`），程序化逐字比对（去句读/爻题/卦名引导、
  繁转简），**64 卦辞 + 384 爻辞 + 用九用六全部一致**，差异仅 6 处且均为已知
  经典异文（咷/啕、己/巳×2、它/他、祐/佑、不复远），其中「不复远」为维基文库
  转录疑误（诸本皆作「不远复」）。全部异文已入模块 YIWEN 表，比对固化为回归
  测试 `tests/test_zhouyi_wikisource.py`（比对工具 `tests/verify_zhouyi_wikisource.py`，
  数据源缺省时自动跳过）。另保留独立默写互证回归测试（`tests/test_zhouyi.py`）。
- **十干四化（紫微）**：由 x_iztro 引擎盘面直接提取（716,314 条黄金用例的独立
  实现），与通行十干四化表逐干核对一致（脚本核验，ALL_MATCH）。
- **《穷通宝鉴》调候（八字 tiaohou 流派）**：抓取维基文库《窮通寶鑑》全文
  （`research/fetched/qiongbao.txt`），程序化提取十干逐月调候原文
  （`fortune/bazi/tiaohou_text.py`，120 条，OpenCC 繁转简、非手工转写），
  tiaohou 流派输出逐字原文与出处，并附**逐月喜用提炼**（XTIQUAN：取/用/先/次/
  须/耑/喜/得等关键词后随天干的规则抽取 + 否定语境排除 + 原文句引文锚点，
  明确标注「规则抽取自原文，仅供参考」）；与抓取页一致性由
  `tests/test_tiaohou.py` 回归锁定（每条目须为原文子串 + 黄金锚点 + 提炼锚点）。
- **《神峰通考》病药流派（八字第 5 用神法）**：由 research/Book《神峰通考》PDF
  文字层抽取（竖排，OCR 噪声已标注）「病药说类」原文，新增 bingyao 流派——
  依「从重者论」定病神（身强取比劫/印最旺者、身弱取克泄耗最旺者）、取克病之
  药神，附原文引文（「有病方为贵，无伤不是奇；格中如去病，财禄两相随」）。
  回归见 `tests/test_shenfeng.py`。
- **《神峰通考》四病四药与盖头说（第二轮扩充）**：抓取维基文库《神峰通考》全文
  （`research/fetched/shenfeng_wikisource.txt`），程序化提取盖头说/病药说类/
  雕枯旺弱四病说类/损益生长四药说类四章（`fortune/bazi/shenfeng_text.py`）；
  **引用句须同时逐字存在于维基文库本与影印本文字层（双源互证）**，文库本转录
  讹误（「而」作「雨」、「枯」作「桔」等）如实标注。bingyao 输出升级为双源互校
  出处并附四病四药引文；病神透干时触发盖头说引注；并按病神所属十神类附
  **雕枯旺弱逐格细分引句**（官杀/财/印/日主/比劫，RULE_QUOTES 双源互证，
  如「苟若官星无根，官从何出？」）。回归见 `tests/test_shenfeng_text.py`。
- **《卜筮正宗》六亲持世逐字引文**：转码存档（`research/fetched/bushizhengzong.txt`），
  duanyu 六亲持世通论升级为「诸爻持世诀」逐字引文（该本「子身/井临」刊误如实
  保留并标注），引文忠实性由 `tests/test_liuyao_duanyu.py` 锁定。
- **《卜筮正宗》十八论（第二轮扩充）**：十八论逐字文本入
  `fortune/liuyao/shiba_lun_text.py`——第 1–11、16–18 章取自校注本，**该本所缺的
  第 12–15 章（伏吟/旺相休囚/合中带克/合处逢冲）取自識典古籍影印 OCR**
  （双源按章标注；「四生逐位论」底本误刻「第六」已标注）。六爻断语对旬空/月破/
  化进退化/卦变反吟/伏吟/**旺相休囚（暂时之用/待时之用）/合中带克（作合论/作克论/
  申化巳化合长生特例）**触发性引用对应论原文。口径见 `research/shiba_lun.md`，
  回归见 `tests/test_shiba_lun.py`。
- **《梅花易数》体用总诀引注**：转码存档（`research/fetched/meihua_yishu.txt`），
  梅花输出附体用总诀原文（与体用生克断语逐字互证），模块与输出标注「题宋·邵雍撰，
  传系后人托名」。
- **《滴天髓》通神论引文**：节选本抽取存档（`research/fetched/ditiansui.txt`，
  题京图撰/刘基注/任铁樵增注），旺衰流派输出附「理承气行岂有常，进兮退兮宜抑扬」
  引文（版本如实标注）。
- **《滴天髓》刘基注本全章 + 何知章速览（第二轮扩充）**：research/Book《滴天髓
  原文（刘基注）》epub 抽取存档（`research/fetched/ditiansui_liuji.txt`），通神论
  各章与何知章 8 句程序化提取（`fortune/bazi/ditiansui_text.py`），与维基文库
  《滴天髓阐微》互校（`research/fetched/ditiansui_wikisource.txt`）；底本异文
  「品泯/财贫神」（通行作「品汇/财神」）如实标注。wangshuai 附理气/衰旺/中和、
  tiaohou 附寒暖/燥湿、tongguan 附通关引文；报告新增**何知章速览**（8 句规则
  映射，经验性简化，`fortune/bazi/ditiansui.py`），并**接大运流年**：逐大运及
  大运内逐年把岁运干支并入原局重算命中（表格列出相对原局/相对大运的变化，
  写入 meta）。回归见 `tests/test_ditiansui_text.py`。
- **《子平真诠评注》（八字 geju 流派）**：由 research/Book 评注 txt 转码存档
  （`research/fetched/ziping_pingzhu.txt`），程序化提取 48 章合刊文本
  （`fortune/bazi/ziping_text.py`，沈孝瞻原著、徐乐吾评注，原文与评注未逐段分离
  并如实标注），geju 流派按取格引用对应章原文；另有原本 epub 存档作对齐底本。
  回归见 `tests/test_ziping.py`，口径见 `research/ziping_tables.md`。
- **《渊海子平》交叉核验**：抓取维基文库《淵海子平》全文（`research/fetched/
  yuanhai.txt`）——该版为赋文类编本、**无通行本卷一神煞起法篇**（如实记录）；
  可核验的「论阳刃」与本仓羊刃表逐字一致（穷举回归）；并据该版新增**魁罡
  （四日）、日贵（四日）、金神（三时）**三项，均附原文出处（魁罡《诗诀》
  「壬戌」刊误已标注）。**足本补核**：由 research/Book 足本 epub 抽取
  `research/fetched/yuanhai_quanben.txt`（含卷一神煞起法篇），逐条比对——
  太极/月德/天德/禄/驿马/华盖/金舆/空亡/羊刃九项一致；**天乙贵人两古本分歧**
  （足本「庚辛逢马虎」版本二 vs 三命通会「甲戊庚牛羊」版本一，从版本一并引）；
  学堂纳音派 vs 日干派两说并列；十恶大败两古本同作「乙丑」、按穷举为「己丑」。
  见 `research/shensha_tables.md` §28 与 `tests/test_shensha_yuanhai*`。
- **《三命通会》卷三神煞扩展**：抓取维基文库《三命通會/卷三》全文
  （`research/fetched/smtj_juan3.txt`），新增金舆、三奇（顺布）、学堂、词馆、
  亡神、天罗、地网、十恶大败、元辰、暗金的煞、六厄、勾煞、绞煞、德秀十四项，
  起法逐条对照原文并附出处与争议标注（学堂词馆日干派 vs 纳音派、天罗地网
  纳音分派、十恶大败「乙丑/己丑」传本异文——穷举 60 甲子验证「禄入空亡」
  恰为十日，己丑为是；元辰/勾绞的年支说 vs 日支说）；驿马补出处注。
  黄金用例见 `tests/test_shensha_smtj.py`、`tests/test_shensha_smtj2.py`，
  起法文档见 `research/shensha_tables.md` §18–§27。
- **六爻诸表（`fortune/liuyao`）**：抓取维基文库《增删卜易》全本核对——纳甲歌
  8/8、起六神诀、六合、六冲、旬空表**与原文完全一致**；六神主事与「六神章
  第十八」原文一致（青龙吉/白虎凶丧/元武主盗贼/朱雀主口舌）。**进神退神章
  第二十九维基文库本列 7 对（无戌化丑），现代排印本通行 8 对**——断语模块
  采用通行 8 对并已标注传本差异。**「六亲持世歌」在维基文库本《增删卜易》中
  不存在（该书为散文论述），歌诀通行于《卜筮正宗》等传本且文字互有出入**，
  断语模块只取各本一致通义，出处已按此修正。详见 `research/liuyao_tables.md`
  §8 与 `research/fetched/README.md`。
- **彖传/大象传引文（`fortune/misc/zhouyi_zhuan.py`）**：由 `tests/tools_extract_zhuan.py`
  从维基文库 64 卦子页程序化提取（繁转简、去模板标记），梅花起卦报告附逐字引文；
  与抓取页的一致性由 `tests/test_zhouyi_zhuan.py` 回归锁定。
- **六爻断语原文短引（`fortune/liuyao/duanyu.py`）**：六亲持世通论附带《增删卜易》
  原文短引（逐字、保持底本繁体），引文须逐字存在于原文存档，由
  `tests/test_liuyao_duanyu.py::test_shichi_quotes_verbatim_in_source` 回归锁定。
- 变爻纳甲取支口径：见 `research/liuyao_tables.md` §6.3。

紫微报告表头已按实际生年显示四化（如丁年：太阴化禄、天同化权、天机化科、巨门化忌），
庚年两派为**配置口径**（表头「配置口径」行），不再混排。
六爻变爻纳甲按变卦取支、六亲按本宫五行论（《增删卜易》装卦法；另一派按变卦宫论，见
`research/liuyao_tables.md` §6.3）。

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
- **测试**：`tests/` 共 191 项断言（黄金用例、HKO 官方数据 4 个年份、穷举表校验、
  争议开关、第二轮审查回归、周易表完整性、六爻变爻纳甲与断语、CLI 输入校验、
  穷通宝鉴调候表忠实性与喜用提炼、三命通会新神煞黄金用例、渊海子平交叉核验
  （赋文本+足本）、子平真诠评注忠实性与 geju 接线、神峰通考病药流派、卜筮正宗/
  梅花易数/滴天髓引文忠实性、十八论双源逐字锁定与触发、神峰通考四病四药双源
  互证与逐格细分、滴天髓何知章规则映射与大运流年），
  另 `plugin/test/` 17 项 node 测试（含 `e2e.cli.test.mjs` 端到端契约测试：真跑
  `python -m fortune.cli`，断言工具 schema 广告的每个参数组合 exit 0、非法输入
  返回可读报错——此前的 ziwei `--day-change` 崩溃即由该层契约测试防住）；全部通过。
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
tests/               # 191 项断言
```

## 文献与数据来源（硬编码表依据）

- `research/bazi_golden_cases.md` —— 八字双引擎对照与 lunar_python 行为逐条核实
- `research/solar_time.md` —— 真太阳时方案选型、EoT 三源对照、夏令时逐日核验
- `research/shensha_tables.md` —— 神煞表（《三命通会》维基文库、《渊海子平》原文核验）
- `research/ziwei_tables.md` —— 紫微安星诀核验清单（含 §6.1 引擎修正附注）
- `research/liuyao_tables.md` —— 六爻纳甲/世应/六亲/六神/旬空（《增删卜易》《卜筮正宗》）
- `research/shiba_lun.md` —— 《卜筮正宗》十八论双源分章标注与触发性引用口径
- `research/chenggu_table.md` —— 称骨通行男命版全表
- `research/xiaoliuren.md` —— 小六壬掌诀与断辞
- 《神峰通考》四章、《滴天髓》各章与何知章：出处与异文见 `fortune/bazi/shenfeng_text.py`、
  `fortune/bazi/ditiansui_text.py` 模块注释与 `research/fetched/README.md`
- 梅花易数 64 卦表：通行本《周易》六十四卦（上象+下象规则），与 King Wen 序逐卦核对

## 局限与免责

- 八字用神、旺衰打分、称骨/小六壬断辞为**经验规则**，非确定性算法，不同流派结论可能矛盾；
- 称骨仅收录男命通行版判词；小六壬「小吉五行」等异文已标注存疑；
- 紫微排盘按时辰（两小时）粒度，分钟仅影响跨时辰边界（真太阳时校正后）；
- 传统术数无科学依据，本工具定位为「历法计算正确 + 排盘可复现 + 解读透明可追溯」的民俗研究工具。
