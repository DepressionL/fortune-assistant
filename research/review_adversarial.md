# Fortune-assistant 对抗性安全与正确性审查报告

> 审查者视角：攻击者 / 挑刺者（独立审查），以「宁可误报也不漏报」为原则。
> 审查时间基线：本会话。⚠️ 审查期间发现工作区正被另一进程**并发修改**（`fortune/bazi/liunian.py`、`tests/test_liunian.py`、`tests/test_exhaustive.py`、`tests/test_hko.py` 等为新加；`fortune/bazi/relation.py` 于 08:24:27 被改写）。
> 结论以**当前磁盘快照**为准；凡明确标注「已修复」者为审查中途被我证实、随后被并发改动修正的问题。
> 环境：Python 3.11.3，`.venv`；`pytest tests -q` 当前 **71 passed**（README 宣称 52 项，已过时）。

---

## 结论速览

- 硬编码表（神煞 18 项、纳音、称骨 60+12+30+12、64 卦名、八宫卦序、纳甲地支、六神、旬空、天德月德、禄刃）**经独立核对全部正确**，可与 `research/*.md` 逐项对上。
- 发现 **2 个严重逻辑 bug**（均在 `fortune/misc/meihua.py`：时支数公式、体用生克判读），会把梅花易数起卦结果算错。
- 发现 **6 个配置项静默失效**（`config.longitude/timezone/is_dst/canggan_sect/show_sources/ziwei_age_type` 设置了但从未被读取）。
- 发现若干中低级问题：CSS/文档不一致、DST 02:00 边界未建模、裸 `assert` 报错信息缺失、紫微文档 §6.1 内部自相矛盾等。
- 曾发现「子卯刑漏检」，但当前快照 `relation.py` 已修复（见 §0）。

---

## 一、严重 bug

### 1.1 梅花易数「时支数」公式错误 —— `fortune/misc/meihua.py:141`

```python
nh = hour // 2 + 1   # 时支数：0/23点=子=1 … 21-22点=亥=12
```

该公式把钟表小时按「0–1=子、2–3=丑、…、22–23=亥」划分，而标准时辰（本项目其它模块与 lunar_python 均采用）是「**子时 = 23:00–00:59**」。后果：**奇数小时（1、3、5…23）全部取错一个地支**，`hour=23`（晚子时）被误判为「亥」而非「子」。

与 lunar_python `LunarUtil.getTimeZhiIndex`（`util/LunarUtil.py:675`）实测对比：

| 钟点 | lunar_python 时支 | meihua `hour//2+1` | 是否一致 |
|---|---|---|---|
| 0 | 子(1) | 1(子) | ✅ |
| 1 | 丑(2) | 1(子) | ❌ |
| 2 | 丑(2) | 2(丑) | ✅ |
| 3 | 寅(3) | 2(丑) | ❌ |
| 22 | 亥(12) | 12(亥) | ✅ |
| 23 | 子(1) | 12(亥) | ❌ |

- **复现**：`meihua.by_time(1984, 1, 1, 1)` 得 `upper=离 lower=震 动爻=4`（与 `hour=0` 完全相同，因为 `0//2+1 == 1//2+1 == 1`）；而 `hour=1` 的正确时支为丑(2)，应得 `上离下坎 动爻=5`。
- **影响**：时间起卦对任意奇数钟点出生的盘算错上下卦/动爻；`23:00`（晚子时）这一常见输入尤其错误。
- **建议修法**：改 `nh = ((hour + 1) // 2) % 12 + 1`（子=1…亥=12，匹配 lunar_python）。若仍想沿用陈旧约定，须在 docstring 明确，并与 chenggu/ziwei/bazi 的时支口径统一。

### 1.2 梅花易数「体用生克」—— 体克用 / 用克体 判读互换 —— `fortune/misc/meihua.py:99-102`

```python
if w[w[u]] == t:   # 体克用（五行中 u 生 x 生 t → t 克 u 的反向：t 克 u）
    return "体克用", "体克用，可成但费力（小吉）"
return "用克体", "用克体，事多阻逆（凶）"
```

`w` 是「我生」链（木→火→土→金→水→木）。推导：`w[w[u]] == t` 等价于「`u` 生 `x` 生 `t`」，即 `u` 与 `t` 在生链上相隔两格，而相生链隔一格=相克，故 `w[w[u]]==t` 等价于 **`u` 克 `t`（用克体）**，**不是** `t` 克 `u`。代码注释「即 t 克 u」推理反了。

- **复现**：穷举 64 组（8 用 × 8 体），**26 组**出现判读反转。
  - `用=震(木), 体=艮(土)`：木克土 → 正确应为 **用克体（凶）**；代码却输出 「体克用，可成但费力（小吉）」。
  - `用=乾(金), 体=离(火)`：火克金 → 正确应为 **体克用（小吉）**；代码却输出 「用克体，事多阻逆（凶）」。
- **影响**：梅花体用断语的吉凶在主克关系上**系统性反转**（原凶断成小吉、原小吉断成凶）。
- **建议修法**：两条克分支互换，或显式用克表：
  - `if KE[u] == t: return "用克体", "…凶"`（`u` 克 `t`）
  - `else: return "体克用", "…小吉"`（`t` 克 `u`，并断言 `KE[t]==u`）。

---

## 二、一般 bug

### 2.1 子卯刑（无礼之刑）曾漏检 —— `fortune/bazi/relation.py`（已修复）

审查初版 `relation.scan`（旧 `XING_GROUPS=(寅巳申,丑戌未,子卯)`，三刑只在「三支组合」里 `set(trio)==set(grp)` 匹配，而 `trio` 恒为 3 支、`子卯` 仅 2 支，故**永不匹配**）：
- 复现：四柱 `甲子/乙卯/丙寅/丁午`（子、卯各一）→ **无任何刑**；`丙戌/丁丑/…` 中「子卯」漏检。
- 当前快照已在地支两两扫描中加：
  ```python
  if {a, b} == {"子", "卯"}:
      hits.append(RelationHit("子卯刑", …))
  ```
  实测 `甲子/乙卯/丙寅/丁午` 现能正确检出 `子卯刑`。**本项在当前快照已修复，予以确认；原实现确为 bug。**

### 2.2 `config.longitude / timezone / is_dst` 静默失效（库 API 路径）—— `fortune/core/calendar.py`

`normalize`（`calendar.py:89,98,106`）只读取 **`birth.is_dst` / `birth.timezone` / `birth.longitude`**；`config.longitude/timezone/is_dst` 在 `fortune/` 包内**从未被读取**（grep 证实），是死字段。二者值一旦不一致即静默错算。

- **复现**：
  ```python
  cfg = FortuneConfig(use_true_solar_time=True, longitude=105.0)  # 设 config
  birth = BirthInfo(…, longitude=120.0)                          # birth 仍 120
  nb = normalize(birth, cfg)   # 结果与 longitude=120 完全相同（-0.27 分钟）
  ```
  正确应体现 `105°E` 的约 −60 分钟经度差。当 `birth.longitude=105` 时，shift= **−60.27 分钟**（正确），证明经度差逻辑本身无误，只是取数来源用错。
- **影响**：CLI 因为同时写 `birth` 与 `config`（`cli._resolve`）故不受影响；但**库使用者**只改 `config.*` 会静默得不到经度/时区/夏令时修正。
- **建议**：`normalize` 统一从 `config` 取 `longitude/timezone/is_dst`（或 `birth` 回退到 `config`），并去掉重复字段；README/`config.py` 注明哪一个是权威值。

### 2.3 `config.canggan_sect` 完全没有作用 —— `fortune/config.py:55`

`canggan_sect` docstring 声称「传给 lunar_python EightChar.sect」，但：
- `calendar.py:116` 只调 `ec.setSect(1 if day_change_hour==23 else 2)`，从未传递 `canggan_sect`；
- 按 `research/bazi_golden_cases.md` §4.1，lunar_python 的 `sect` **只影响日柱晚子时**，`藏干表 ZHI_HIDE_GAN 与 sect 无关`，lunar_python **并无**「藏干流派」概念。
- **结论**：`canggan_sect` 是一个**无法生效、也不应存在**的开关，纯属误导（README 第 55 行同样写错「传给 EightChar.sect」）。建议删除或改为文档化说明。

### 2.4 `config.show_sources` / `config.ziwei_age_type` 死字段 —— `fortune/config.py:76,85`

`show_sources`（默认真，声称控制报告是否附出处）在 `report/markdown.py` 从未读取；`ziwei_age_type`（虚岁/实岁）在 `ziwei/chart.py` 从未读取（x_iztro 大限口径为虚岁，未做任何按年龄类型切换）。二者都是「配置了却没效果」。

---

## 三、隐患与建议

### 3.1 DST 边界按「日」粒度，未建模 02:00 时刻 —— `fortune/core/calendar.py:89-95`、`fortune/core/solar_time.py:44-50`

`is_china_dst(year,month,day)` 与 `normalize` 的 `rng[0] <= dt.date() <= rng[1]` 只按**整日**判定。1986–1991 夏令时为「当年 4 月第 2 个周日 **02:00** 拨快、9 月第 2 个周日 **02:00** 拨回」，因此：
- 开始日 **00:00–01:59** 实为夏令时前（标准时间），却被判为夏令时；
- 结束日 **02:00–23:59** 实为夏令时后，却被判为夏令时。
- 复现：`is_china_dst(1986,5,4)` 返回 `True`；`normalize(1986-05-04 01:30, is_dst=True)` 得到 `00:30`（被错误扣 1 小时，应为标准时间不扣）。
- 影响：仅涉及夏令时边界当日出生者，误差 ≤1 小时，属边缘；测试 `test_china_dst` 也编码了「整日」约定，属**明确但简化**的约定。
- 建议：`is_china_dst` 改为按时刻（比对时分秒）或至少在报告中注明「整日粒度」。

### 3.2 输入校验裸 `assert`，报错信息缺失 —— `fortune/core/model.py:46-54`

`BirthInfo.validate()` 全部是裸 `assert`（无消息）。`hour=24`、`minute=60`、`month=2 day=30` 等会抛出无文字的 `AssertionError`（`day=30` 的 2 月则直接 `ValueError: day is out of range for month`），CLI 端显示整段堆栈（见下），对用户不友好。
- CLI 复现：`python -m fortune.cli bazi -y 1990 -m 6 -d 15 -H 24` → 打印完整 Traceback 后 exit 1。
- 建议：改为带明确消息的 `ValueError`/自定义异常，并在 CLI 顶层捕获统一输出；用 `pytest.raises(ValueError, match=…)` 断言，替换「恒真断言」式的 `test_config_validation`（该测试目前断言的是裸 `AssertionError`，等于把「报错信息缺失」固化为规范）。
- 附加：`calendar.py:92` 的 `assert rng and …`、`config.validate()` 均有消息，但 `BirthInfo.validate()` 无。

### 3.3 农历「闰月」非法输入报错含糊 —— `fortune/core/calendar.py:79`

`Lunar.fromYmd(year, -1, day)` 当该年并无闰一月时会抛 `Exception("wrong lunar year 1990 month -1")`；`lunar_month=-13` 则裸 `AssertionError`。均为「非零崩溃但信息含糊」。建议：输入侧先校验该农历年是否真有对应闰月（用 `lunar_python` 的闰月表），给出中文明确提示。

### 3.4 梅花 64 卦 docstring 表述自相矛盾 —— `fortune/misc/meihua.py:33`

docstring 写「卦名 = 上卦象 + 下卦象」，但表中实际名是「**上象+下象+卦名**」三字及以上（如 `水雷屯`=上坎水/下震雷+名「屯」、`天泽履`）。「上卦象+下卦象」只是描述性前缀，并非完整卦名。建议改 docstring。

### 3.5 `research/ziwei_tables.md` §6.1 内部自相矛盾（文档，非代码）

- §6.1 修正附注（`ziwei_tables.md:206-226`）已把紫微↔天府关系更正为「**天府 = (4 − 紫微索引) mod 12**（索引和 ≡ 4）」；
- 但同节下方「Python 落地」示例（`ziwei_tables.md:250-251`）仍写 `tianfu_from_ziwei(zw_idx)` 用 **`(10 - zw_idx) % 12`**（旧的对宫/180° 错误映射）。
- 代码自检（`test_ziwei.py:test_ziwei_tianfu_axis_symmetry`）用的是 `(zw+tf)%12==4` 即修正后正确式，故**代码正确**，仅为文档内部不一致。建议删除或更正该 Python 片段。

### 3.6 测试质量观察

- **优点**：黄金八字用例与 `research/bazi_golden_cases.md` 一致（抽查 `2000-01-01`→己卯丙子戊午戊午、`2000-02-04 18:00`→己卯/丁丑 均吻合）；`test_zaowan_zishi_sect` 正确覆盖 sect1/sect2 日柱分歧；`test_geng_sihua_switch`、`test_ziwei_tianfu_axis_symmetry` 覆盖紫微关键开关与锚点。
- **缺口**：
  - `test_meihua_numbers`/`test_meihua_time` 选用的数字/小时（`1,1`、`hour=0`）恰好都落在**错误公式不触发**的路径上，因此**掩盖了 §1.1、§1.2 两处严重 bug**。建议补 `by_time(…, hour=1/23)`、`用克体/体克用` 的组合断言。
  - `test_meihua_64_names_unique` 只断言 64 个**互异**，未断言与 King Wen 序**对应正确**（我独立核对了全 64 个，正确；但仓库内没有对照断言）。
  - `test_liuyao_tables_integrity` 只校验表内自洽（8×8、无重名、世应 1-6），未与八宫「逐爻变」推导规则做独立对照。
  - `test_strength_month_states`/`test_relation_sanxing` 等用伪造 `FakeChart`，绕过了真实排盘链，为纯逻辑单测（可接受）。
  - README「共 52 项断言」已过时（现 71 项）。

---

## 四、已确认正确的部分（一行结论）

以下为**逐一独立核对后确认无误**（不再展开）：

- **神煞 18 项表**（天乙/太极/文昌/禄/羊刃/驿马/桃花/华盖/将星/劫煞/灾煞/孤辰/寡宿/红鸾/天喜/天德/月德/空亡）：与 `research/shensha_tables.md` 逐条一致；天乙「甲戊庚牛羊」、文昌主流口诀、月德丙壬甲庚、羊刃阳干无刃均按文档口径。✅
- **称骨四表**（60 年 + 12 月 + 30 日 + 12 时）：与 `research/chenggu_table.md` 全部一致；判词 21–72 共 52 档与文档对应；最大可达总重 19+18+18+16=**71 钱**（七两一），`72` 档为不可达（与文档“七两二”为传说上限的事实一致），非 bug。✅
- **64 卦名**（`meihua.GUA64`）：与独立 King Wen 序逐卦核对 **0 偏差**（我用权威表重建 `(下卦×8+上卦)→卦名` 后对照，全部吻合）；`PALACE_GUA` 的 64 个卦名同样全部落在 King Wen 集合内。✅
- **八宫卦序**：可由「本宫卦逐爻变」（1世初爻变→5世→游魂四爻回→归魂内卦回）**独立复现**；我对 8 宫×8 卦逐一推导，**爻组成 + 世爻/应爻位置全部一致**（如乾宫 111111→姤→遁→否→观→剥→晋→大有，世应 6/3,1/4,2/5,3/6,4/1,5/2,4/1,3/6）。✅
- **纳甲地支/干**（`NAJIA`）与 `research/liuyao_tables.md` §2 一致（乾甲壬、坤乙癸、震巽坎离艮兑各纳一干；阳顺阴逆地支链）。✅
- **六神起首**（甲乙青龙…戊勾陈己螣蛇庚辛白虎壬癸玄武）与文档一致；**旬空表**与公式（`offset=(支-干)%12→甲旬首`）正确。✅
- **六亲** `liu_qin`：生我父母/我生子孙/克我官鬼/我克妻财/比和兄弟，逻辑正确（用「隔格生=克」推导，抽查官鬼、子孙均对）。✅
- **小六壬**：`_count(start,n)=(start+n-1)%6` 递推正确；正月初一子时→大安、三月初七午时→速喜速喜速喜 与测试一致。✅
- **真太阳时 EoT 符号**：`equation_of_time` 与 astral 输出 2/14≈−14.2、11/3≈+16.4，符号（视太阳时−平太阳时）与符号约定一致；`conv = 4×(经度−120)+EoT` 正确；经度 105° 实测 −60.27 分钟。✅
- **紫微**：x_iztro `by_solar`/`ChartConfig.mutagens` 调用正确；`_time_index`（0=早子…12=晚子）正确；命身宫公式 `yue=(2+m-1)%12, ming=(yue-h)%12, shen=(yue+h)%12` 与《紫微斗数全书》一致；紫微↔天府寅申对称 `(zw+tf)%12==4` 与修正后文档及实测一致；庚年四化开关（天同/天相化忌）切换生效。✅
- **八字流派**：`day_change_hour` 23→sect1(23:00 换日)、0→sect2(0:00 换日) 实测生效（`2000-02-29 23:30` → 戊午/丁巳）；立春精确时刻边界（lunar_python）正确；起运 sect=1「3天折1年」正确；`year_change!=lichun` 时明确 `NotImplementedError`。✅
- **年份范围**：lunar_python 对 1、1899、1900、1950、2024 均正常出柱，支持范围宽。✅
- **报告/CLI**：`--json` 用 `dataclasses.asdict` 可序列化且运行通过；SVG 用 `html.escape` 转义标题/星名/宫名（无注入）；marKdown 不含用户自由文本（安全）；`liuyao --backs` 非数字输入有清晰 `typer.Exit(1)` 提示。✅

---

## 五、复现/证据脚本

以下脚本在 `research/tmp_review/` 下（已生成，可用）：`probe1.py`（子卯刑、小时映射、配置开关、边界）、`probe2.py`（干净子卯、梅花小时、农历闰月）、`probe3.py`（梅花体用 64 组穷举 + 实例）、`probe_hexagram.py`（64 卦名 + 八宫推导）、`probe4.py`(配置效果 + 紫微)、`probe5.py`（年份范围、DST、称骨上限）。

---

## 六、修复优先级建议

1. **P0**：`meihua.by_time` 时支数公式（§1.1）；`meihua._interact` 体用生克反转（§1.2）。
2. **P1**：统一 `longitude/timezone/is_dst` 取数来源，删除或文档化死字段（§2.2-2.4）。
3. **P2**：补齐测试到「会触发 bug 的输入」（奇数小时、`用克体/体克用`、King Wen 逐卦对照、八宫推导对照）。
4. **P3**：DST 时刻边界、裸 assert 报错信息、农历闰月预校验、文档内部矛盾（§3.1-3.5）。
