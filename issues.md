# fortune-assistant 评审问题清单

> 评审来源：一次全功能运行（男 · 天津 117.2°E · 公历 1991-01-11 00:05 北京时间 · 真太阳时校正）。
> 真太阳时校正 −18.8 分 → 1991-01-10 23:46:13，落夜子时（23:00–01:00）换日敏感窗口。
> 状态标记：`[已确认]` = 源码验证问题真实存在；`[已修复]` = 已修复并通过回归（262 tests passed）；
> `[未修复-待数据]` = 确认存在但修复需外部数据源核验。

## P0（高优先级：影响结果正确性或自洽性）

### P0-1 换日敏感窗口缺少自动提示 —— [已修复]
- **修复**：`core/calendar.py` normalize 第 6 步检测夜子时（23:00–23:59），计算另一换日口径的日柱
  （用 `EightChar.fromLunar` 建独立实例——`Lunar.getEightChar()` 返回同一缓存对象，直接 setSect
  会污染主盘，此坑已写进代码注释并加回归测试 `test_i1_night_zi_alt_day`）。
- 报告头部输出「⚠ 换日敏感警告」块（`report/markdown.py`），`BirthContext` 增
  `day_change_sensitive`/`alt_day_ganzhi` 字段；紫微盘附换日口径提示 note（`ziwei/chart.py`）。
- **验证**：1991-01-11 00:05 天津：23 派日柱辛巳/对照庚辰；0 派日柱庚辰/对照辛巳，双向正确。

### P0-2 跨工具日期口径不统一、无统一声明 —— [已修复]
- **修复**：
  - `misc/chenggu.py`、`misc/meihua.py`、`misc/xiaoliuren.py` 的 caliber 统一改为
    「日期/时辰口径」声明（明确写出所用农历日期与校正值）；
  - 修 `by_birth`/`calc_from_birth` 的钟表口径 bug：`use_true_solar=False` 时不再沿用校正后的
    农历日期，改按钟表公历重算农历（`test_i1_misc_clock_date_recalc` 回归锁定）；
  - CLI 层 `meihua`/`xiaoliuren` 新增 `--from-birth "YYYY-MM-DD HH:MM"` + `--lng` +
    `--no-true-solar` 出生信息派生入口（`_misc_from_birth`）；`meihua` 农历输入增加
    lunar_python 日期真实性校验（不存在的农历日期直接报错）。
- **验证**：`--from-birth "1991-01-11 00:05" --lng 117.2` 自动派生 11月25日并声明口径。

### P0-3 紫微格局引擎自相矛盾（禄马交驰） —— [已修复]
- **根因**：`ziwei/chart.py` `pattern_review` 只索引主星 `p.major`，禄存/天马是辅星（`p.minor`），
  复核永远查不到 → 「盘面未见」。**非 x-iztro 引擎 bug，是复核索引遗漏**。
- **修复**：`pattern_review` 同时索引主星+辅星+杂曜；复核输出增加「复核结论：与标称宫
  一致 / 不完全一致」的确定性判定。
- **验证**：禄马交驰（财帛）→ 禄存→财帛、天马→财帛、结论一致；禄马交驰（命宫）如实标注不一致。

## P1（中优先级：误导性展示或审计性缺失）

### P1-1 何知章门槛条件展示误导 —— [已修复]
- **修复**：`bazi/ditiansui.py` 贵句未命中 reason 改为两条件分列：
  「条件① 官杀透干或月支藏官：不满足；条件② 官杀得分 满足（1.00 ≥ 0.5）——须两条件同时满足，
  故未命中」。命中分支同样分列。
- **验证**：本例输出两条件状态清晰，不再出现「得分达标却未命中」的误导。

### P1-2 聚合报告证据方向不可审计 —— [已修复]
- **修复**：`comprehensive/__init__.py` 证据链每条渲染方向标记 `[+]`/`[−]`/`[○]`，指标说明增加
  图例；合参节头部增加占事/命理口径声明；liuren note 措辞修正（原「含真太阳时校正口径」与
  实际用钟表时间矛盾）；`markdown()` 补渲染 `notes`（附注节，随机六爻等提示此前被静默丢弃）。
- **验证**：近运维证据里梅花/小六壬口径行现含完整日期口径声明。

### P1-3 重复输出严重、无头部摘要 —— [已修复]
- **修复**：`report/markdown.py` 头部新增「摘要（速览）」块（四柱/五行最旺最弱/旺衰/各派用神）；
  CLI `bazi` 新增 `--sections` 小节裁剪参数（summary,bazi,dayun,wuxing,relation,shensha,
  strength,yongshen,hezhi,suiyun,liunian），对比神煞基准只需 `--sections summary,shensha`。
- **验证**：`--sections summary,shensha` 只输出摘要+神煞节；`--sections summary` 只输出摘要。

## P2（低优先级：体验与完整性）

### P2-1 占事盘与命理盘时间口径混淆、无免责声明 —— [已修复]
- **修复**：`liuren/duanyu.py`、`qimen/duanyu.py` 输出头固定声明占事口径（钟表时间、
  以出生时刻代占时属非常规用法、日干支与八字日柱可能不同）；comprehensive 合参节同声明。

### P2-2 细节缺口清单
- [x] 流年变例「其余 N 条从略」截断 → `--hezhi-full` 显示全部；meta 结构化输出不再截断 —— [已修复]
- [x] 岁运并入计分「月令状态沿用原局」→ 报告标注增强（说明误差性质）—— [已修复]
- [x] 紫微「命主/身主」释义待补 → 补通行释义（命主=命宫地支所值星/先天禀赋，身主=生年支所值星/后天安身）—— [已修复]
- [ ] 称骨女命版判词未收录 → **[未修复-待数据]**：女命版通行表各源分歧大，须先完成多源交叉核验
  （docs/修复与改进计划.md I4-e 已列），本次不编造数据；CLI 已有明确提示
- [x] comprehensive 六爻 backs 需手动复制 → 新增 `--liuyao-random`（随机掷币一键带入，
  报告附注标注随机模拟）—— [已修复]
- [x] 流年速览无法回溯 → `--liunian-back N` 自锚年前 N 年起列 —— [已修复]
- [x] 紫微未提示换日口径影响日系星曜 → 夜子时盘附 note —— [已修复]（见 P0-1）

## 修复附带发现并一并修复的问题

1. **`Lunar.getEightChar()` 返回同一缓存对象**：夜子时对照盘直接 setSect 会污染主盘 sect，
   导致主盘日柱错按另一口径（test_zaowan_zishi_sect 曾失败）。改 `EightChar.fromLunar`。
2. **Windows GBK 控制台 UnicodeEncodeError**：报告含 ⚠ 字符时 CLI 直接崩溃
   （此前只有不经用神多流派节等路径才不触发）。模块加载时统一
   `stdout/stderr.reconfigure(encoding="utf-8")`，`__main__` 改走 `main()`。
3. **comprehensive 的 notes 从不渲染**：随机六爻/模块不可用等附注被静默丢弃，补「附注」节。

## 回归验证

- 测试套件：**262 passed**（含新增 2 个回归测试：`test_i1_night_zi_alt_day`、
  `test_i1_misc_clock_date_recalc`；更新 2 处旧断言以匹配新口径契约）。
- 手动 CLI 全流程复核：bazi 双口径警示/摘要/`--sections`/`--hezhi-full`/`--liunian-back`、
  ziwei 格局复核、meihua/xiaoliuren `--from-birth`、liuren/qimen 口径声明、
  comprehensive 证据方向与附注——全部符合预期。

---

## 第二轮：与 DSH 桥接/客户端插件兼容性验证

### 兼容性结论（无冲突）
- **桥接层 `plugin/lib/index.js`**：`splitMeta` 契约不变（`lastIndexOf` 取末标记后 JSON）；
  meta schema 为宽松 `{type:"object"}`，新增字段（night_zi/alt_day_ganzhi/hezhi_liunian 全量/
  liunian_start）安全透传；`PYTHONIOENCODING=utf-8` 插件早已内置（与 CLI 的 reconfigure 双保险）。
- **客户端 `plugin-client/lib/client.js`**：消费的 meta 字段结构（chart/strength/palaces/
  patterns/conclusions/hepai 等）均未改动，pattern_review 等文本型字段内容变化兼容渲染。
- **验证方式**：node 关键断言（12 工具注册/splitMeta 拆解+新字段透传/参数转发，全部通过）
  + 经 DSH 工具 `fortune_bazi` 端到端调用确认（模型面输出含警示/摘要/条件分列，工具正常返回）。

### 本轮修复的渲染缺口（"算了但没渲染"）
1. **DSH 工具面未暴露新 CLI 参数** —— `plugin/lib/index.js` 补：bazi 增
   `sections/hezhiFull/liunianBack`；comprehensive 增 `liuyaoRandom`；
   meihua/xiaoliuren 增 `fromBirth/lng/noTrueSolar`（含参数兜底报错）。
2. **综合视图证据卡无方向徽章** —— `client.js` ComprehensiveView 证据链补
   `[+] 正面 / [−] 负面 / [○] 事实` 徽章（与 Python 报告方向标记对齐）。
3. **紫微视图不渲染 notes** —— ZiweiView 补「口径与备注」节（换日口径提示在 UI 可见）。
4. **八字视图不渲染夜子时警示** —— BaziView 头部补「夜子时」警示 pill + 另一口径日柱。
5. **六爻综合主题不显示占题聚焦** —— 去掉 `topic !== "综合"` 排除条件。
6. **回溯年份与时间轴标题不一致** —— meta 增 `liunian_start`，客户端优先用之。

### 生效说明
- Python 侧修复：**已即时生效**（DSH 工具每次调用 spawn 新进程读新代码，端到端已验证）。
- 桥接层/客户端 JS 改动：需 DSH 重启（宿主插件重载）与 Web 页面刷新后生效；
  web profile 以 `link:` 直连本工作区目录，无需重新安装。

