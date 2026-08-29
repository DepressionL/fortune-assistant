# research/fetched —— 联网抓取的权威原文存档

> 抓取日期：2026-08-29。用途：文献核验（程序化逐字比对）。全部为公共领域古籍
> （Public Domain），仅存档不随分发版权风险；本目录体积较大，如不需要可比对后删除。

## 文件清单与来源

| 文件 | 来源 | 说明 |
|---|---|---|
| `zhouyi_pages/*.txt`（64 个） | zh.wikisource.org `周易/<卦名>` 子页（action=raw），如 `周易/乾` | 《周易》通行本经文（卦辞+爻辞+彖/象/文言），Textquality 50%。比对入口：`tests/verify_zhouyi_wikisource.py`、回归测试 `tests/test_zhouyi_wikisource.py` |
| `zengshan_toc.txt` | zh.wikisource.org `增刪卜易`（action=raw） | 《增删卜易》全本（含进神退神章第二十九、纳甲歌、起六神诀等） |
| `zengshan_18_liushen.txt` | `增刪卜易/18` | 六神章第十八 |
| `zengshan_19.txt` | `增刪卜易/19` | 六合章第十九 |
| `zengshan_20.txt` | `增刪卜易/20` | 六冲章第二十 |
| `zengshan_26.txt` | `增刪卜易/26` | 旬空章第二十六 |
| `smtj_juan3.txt` | zh.wikisource.org `三命通會/卷三`（action=raw） | 《三命通会》卷三（神煞诸篇：驿马、金舆、三奇、学堂词馆、劫煞亡神、天罗地网、十恶大败等 23 篇），用于神煞起法核验 |
| `qiongbao.txt` | zh.wikisource.org `窮通寶鑑`（action=raw） | 《穷通宝鉴》（《栏江网》）全文：十干逐月调候原文，用于 tiaohou 流派逐字表 |
| `yuanhai.txt` | zh.wikisource.org `淵海子平`（action=raw） | 《渊海子平》全文（赋文类编本，73 篇；**无通行本卷一神煞起法篇**，见核验附记） |
| `yuanhai_quanben.txt` | research/Book《渊海子平》足本 epub 抽取（合并官板音义评注本，293K 字） | **含卷一神煞起法篇**，用于与 shensha 表逐条交叉核验（tests/test_shensha_yuanhai_quanben.py） |
| `ziping_pingzhu.txt` | research/Book《子平真诠评注》txt 转码（GB18030→UTF-8，109K 字） | 沈孝瞻原著、徐乐吾评注合刊本，geju 流派原文数据源 |
| `ziping_yuanben.txt` | research/Book《子平真诠》原本 epub 抽取（28K 字） | 纯原文，留作原文/评注逐段对齐底本 |
| `bushizhengzong.txt` | research/Book《卜筮正宗》txt 转码（GB18030→UTF-8，106K 字） | 诸爻持世诀等逐字引文源（该本「子身/井临」刊误已标注）；**十八论第 1–11、16–18 章数据源**（第 12–15 章此本缺） |
| `shenfeng.txt` | research/Book《神峰通考》PDF 文字层抽取（竖排，175K 字） | 病药说类原文，bingyao 流派数据源（OCR 噪声已标注）；四病四药/盖头说引用句的双源互校参照之一 |
| `shenfeng_wikisource.txt` | zh.wikisource.org `神峰通考`（HTML 抽段，154K 字） | 盖头说/病药说类/雕枯旺弱四病说类/损益生长四药说类逐字文本主源（个别字转录讹误已标注），生成 fortune/bazi/shenfeng_text.py |
| `wikisource_shenfeng.html` | 同上（原始 HTML，227K） | 抽段脚本输入存档 |
| `meihua_yishu.txt` | research/Book《梅花易数》txt 转码（GB18030→UTF-8，44K 字） | 体用总诀引注源（网络转载排印版，托名邵雍已标注） |
| `ditiansui.txt` | research/Book《滴天髓阐微》epub 抽取（节选本，20K 字） | 通神论引文源（题京图撰/刘基注/任铁樵增注） |
| `ditiansui_liuji.txt` | research/Book《滴天髓原文（刘基注）》epub 抽取（21K 字，tests/tools_extract_ditiansui.py） | 《滴天髓》通神论各章+何知章逐字文本主源，生成 fortune/bazi/ditiansui_text.py（底本 OCR 噪声如「品泯/财贫神」如实标注） |
| `ditiansui_wikisource.txt` | zh.wikisource.org `滴天髓闡微`（HTML 抽段，135K 字） | 与 epub 底本互校（何知章/衰旺/寒暖等关键行一致，异文见 VARIANTS） |
| `wikisource_ditiansui.html` | 同上（原始 HTML，325K） | 抽段脚本输入存档 |
| `shidian_18lun_raw.txt` | 識典古籍 shidianguji.com《卜筮正宗》卷三影印 OCR 文字层（内联 JSON 解析，11K 字） | **十八论第 12–15 章数据源**（伏吟/旺相休囚/合中带克/合处逢冲，校注本所缺；个别字存 OCR 噪声已标注） |
| `shidian_18lun_raw.html` | 同上（原始页面，300K） | 解析脚本输入存档 |
| `ctext_yh_search.html` | ctext.org 书名检索页 | ctext《渊海子平》资源定位（维基文字版需人工验证，未采用） |

## 核验结论摘要（详见各模块注释与 README「文献核验记录」）

- 《周易》：本地 `fortune/misc/zhouyi.py` 与维基文库本 64 卦辞 + 384 爻辞 + 用九用六
  逐字一致；仅 6 处差异全部为已知经典异文（本表从阮刻注疏本用字），其中
  复初九「不复远」为维基文库转录疑误（诸本皆作「不远复」）。
- 《增删卜易》纳甲歌、起六神诀、六合、六冲、旬空：与 `fortune/liuyao` 各表逐条一致。
- 进神退神：维基文库本「进神退神章第二十九」列 7 对（无「戌化丑」），现代排印本
  通行 8 对；`duanyu.py` 采用 8 对并已标注传本差异。
- 六亲持世：维基文库本《增删卜易》无「六亲持世歌」章节（为散文论述）；歌诀通行于
  《卜筮正宗》等传本，`duanyu.py` 只取各本一致通义，已修正出处表述。
- 《三命通会》卷三：驿马/金舆/三奇/学堂词馆/劫煞亡神/天罗地网起法已逐条与原文
  核对后并入 `fortune/bazi/shensha.py`（见各条目 note 出处）；「十恶大败」维基文库本
  作「乙丑」，按「禄入空亡」定义应为「己丑」，实现从通行本并已标注传本异文。
- 《穷通宝鉴》：十干逐月调候原文程序化提取为 `fortune/bazi/tiaohou_text.py`，
  tiaohou 流派输出逐字原文（回归测试锁定与原文子串一致）；另生成 XTIQUAN
  逐月喜用提炼（规则抽取 + 引文锚点）。
- 《渊海子平》（维基文库赋文编本）：论阳刃与本仓羊刃表逐字一致；新增魁罡、日贵、
  金神三项；该版无卷一神煞起法篇，如实记录（见 shensha_tables.md §28）。
- 《神峰通考》维基文库本：盖头说/病药说类/雕枯旺弱四病说类/损益生长四药说类四章
  程序化提取为 `fortune/bazi/shenfeng_text.py`；引用句须同时逐字存在于维基文库本与
  影印本文字层（双源互证）；文库本个别字转录讹误（「而」作「雨」、「至」作「全」、
  「枯」作「桔」等）已如实标注，引用句均取两源一致的干净句。
- 《卜筮正宗》十八论：第 1–11、16–18 章取自校注本（`bushizhengzong.txt`），
  第 12–15 章该校注本所缺，取自識典古籍影印 OCR（`shidian_18lun_raw.txt`），
  双源按章标注于 `fortune/liuyao/shiba_lun_text.py`；「四生逐位论」底本误刻
  「第六」（目录作第八）已标注。六爻断语对旬空/月破/进退/反吟/伏吟触发对应论原文。
- 《滴天髓》：通神论各章与何知章 8 句程序化提取为 `fortune/bazi/ditiansui_text.py`
  （epub 刘基注本底本，与维基文库阐微本互校）；「品泯/财贫神」两底本俱同而通行
  排印本作「品汇/财神」等异文如实标注；何知章速览为规则映射（经验性简化）。

## 已知数据源缺陷

- 维基文库 Textquality 50%：个别页存在转录问题（已发现复卦初九「不复远」一处），
  比对结果中凡与「诸本一致」冲突处，以阮刻注疏本/通行排印本为准并已在异文表注明。
