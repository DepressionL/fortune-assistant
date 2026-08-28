# 八字双引擎排盘对照：lunar_python (6tail) vs sxtwl (寿星天文历)

> 本文件为 **fortune-assistant** 项目八字引擎选型的实地验证报告。
> 所有结论均来自实际安装并运行的代码，**未虚构任何 API 或输出**。
> 验证环境：Windows，Python 3.11.3，虚拟环境 `D:\ai工作区\fortune-assistant\.venv`。

---

## 0. 环境与版本（实际安装结果）

```
Python 3.11.3
lunar-python 1.4.8   （6tail，纯 Python，主引擎）
sxtwl        2.0.7   （寿星天文历，SWIG 封装 + _sxtwl.cp311-win_amd64.pyd 编译扩展，交叉验证）
```

两库均已通过 `import` 验证可用。sxtwl 在 pip 上存在对应 win_amd64 wheel（`_sxtwl.cp311-win_amd64.pyd`），**本机成功安装**，无需退回仅用 lunar_python。

可运行参考实现：`research/bazi_crosscheck.py`（本文代码即出自该文件，实测通过）。

---

## 1. 两库完整可运行代码示例

### 1.1 lunar_python：`Solar → Lunar → EightChar → Yun` 调用链

```python
# -*- coding: utf-8 -*-
from lunar_python import Solar
from lunar_python.util import LunarUtil

def lunar_chart(y, m, d, hh, mm, ss=0, gender=1, sect=2):
    solar = Solar.fromYmdHms(y, m, d, hh, mm, ss)   # ① 公历出生时刻
    lunar = solar.getLunar()                        # ② 公历 -> 农历(含节气表)
    ec = lunar.getEightChar()                       # ③ 八字对象
    ec.setSect(sect)                                # ④ 流派 1/2
    pillars = [ec.getYear(), ec.getMonth(), ec.getDay(), ec.getTime()]
    hide    = [LunarUtil.ZHI_HIDE_GAN.get(p[1:]) for p in pillars]
    nayin   = [LunarUtil.NAYIN.get(p) for p in pillars]
    yun = ec.getYun(gender, 1)                      # ⑤ 运(sect1 = 3天折1年)
    dy  = [yun.getDaYun(10)[i] for i in range(1, 5)]  # 前4步大运
    return {
        "pillars": pillars, "hide": hide, "nayin": nayin,
        "forward": yun.isForward(),
        "start": (yun.getStartYear(), yun.getStartMonth(),
                  yun.getStartDay(), yun.getStartHour()),
        "start_solar": yun.getStartSolar().toYmd() + " " + yun.getStartSolar().toYmdHms()[11:16],
        "start_age_xu": yun.getDaYun(10)[1].getStartAge(),
        "dayuns": [(x.getGanZhi(), x.getStartYear(), x.getEndYear(),
                    x.getStartAge(), x.getEndAge()) for x in dy],
    }
```

**关键方法签名与含义（lunar_python）**

| 方法 | 签名 | 含义 |
|---|---|---|
| `Solar.fromYmdHms` | `(y,m,d,h,min,s)` | 构造公历时刻 `Solar` |
| `Solar.getLunar()` | `() -> Lunar` | 公历转农历 `Lunar`（内部预计算当年全部节气） |
| `Lunar.getEightChar()` | `() -> EightChar` | 八字对象（**缓存单例**，对同一 Lunar 只创建一个；改 sect 需在读取前设置） |
| `EightChar.setSect(n)` | `(1\|2)` | 设置八字流派（详见 §4.1） |
| `EightChar.getYear/Month/Day/Time` | `() -> str` | 年/月/日/时四柱干支字符串 |
| `EightChar.getYearGan/getYearZhi/...` | `() -> str` | 逐干/逐支 |
| `EightChar.getYun(gender, sect)` | `(1男0女, 1\|2)` | 起运对象（sect1=3天折1年，sect2=按分钟） |
| `Yun.getStartYear/Month/Day/Hour` | `() -> int` | 起运偏移量（年限/月/日/时） |
| `Yun.getStartSolar()` | `() -> Solar` | 起运公历日期 |
| `Yun.isForward()` | `() -> bool` | 大运是否顺行 |
| `Yun.getDaYun(n)` | `(n) -> [DaYun]` | 大运列表；索引 `0` 为起运前，`1..` 为正式大运 |
| `DaYun.getGanZhi()` | `() -> str` | 该步大运干支 |
| `DaYun.getStartYear/getEndYear/getStartAge/getEndAge` | `() -> int` | 大运起止年份与起止岁数（`getStartAge` 为虚岁） |

### 1.2 sxtwl：`fromSolar → Day → getYearGZ / getMonthGZ / getDayGZ / getHourGZ / 节气`

```python
# -*- coding: utf-8 -*-
from lunar_python.util import LunarUtil   # 仅用于把 sxtwl 索引转成字串
import sxtwl

GAN = ["", "甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
ZHI = ["", "子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

def gzstr(gz):
    return GAN[gz.tg + 1] + ZHI[gz.dz + 1]     # GZ.tg 天干索引(0-9), GZ.dz 地支索引(0-11)

def sxtwl_chart(y, m, d, hh):
    day = sxtwl.fromSolar(y, m, d)             # 公历 -> Day(历法日)
    return {
        "year":      gzstr(day.getYearGZ(False)),   # 年柱(False=不以正月初一为界 -> 立春)
        "year_cny":  gzstr(day.getYearGZ(True)),    # 年柱(True=以正月初一为界)
        "month":     gzstr(day.getMonthGZ()),       # 月柱(以节)
        "day":       gzstr(day.getDayGZ()),         # 日柱
        "hour_zw":   gzstr(day.getHourGZ(hh, True)),   # 时柱(早晚子时开)
        "hour_nzw":  gzstr(day.getHourGZ(hh, False)),  # 时柱(早晚子时关)
    }
```

**关键方法签名与含义（sxtwl）**

| 方法 | 签名 | 含义 |
|---|---|---|
| `sxtwl.fromSolar(y, m, d)` | `(int,int,int) -> Day` | 公历转历法日 `Day` |
| `Day.getYearGZ(chineseNewYearBoundary)` | `(bool) -> GZ` | 年柱干支。`False`（默认）= 以**立春**为年界；`True` = 以**正月初一**为年界 |
| `Day.getMonthGZ()` | `() -> GZ` | 月柱干支（以**节**为月界） |
| `Day.getDayGZ()` | `() -> GZ` | 日柱干支（按公历日，以午时 12 时为基准，与早晚子时无关） |
| `Day.getHourGZ(hour, isZaoWanZiShi)` | `(int, bool) -> GZ` | 时柱干支。`isZaoWanZiShi=True`（默认）区分早晚子时 |
| `Day.hasJieQi()` | `() -> bool` | 当天是否有节气 |
| `Day.getJieQi()` | `() -> int` | 节气序号（0=冬至,1=小寒,2=大寒,3=立春,…；非节气日行为未定义） |
| `Day.getJieQiJD()` | `() -> float` | 该节气儒略日 `JD` |
| `sxtwl.JD2DD(jd)` | `(float) -> Time` | 儒略日转 `Time`（属性 `.Y .M .D .h .m .s`） |
| `GZ.tg / GZ.dz` | `int` | 天干/地支索引（0 基） |

---

## 2. 双库结果对照表（北京时间，默认男命）

图例：`❗` 表示两库在某一项上结果不一致（或流派选择导致不一致）。

### 案例 1 —— `2000-01-01 12:00`（立春前）

| 项目 | lunar_python (sect?=2) | sxtwl | 结论 |
|---|---|---|---|
| 年柱 | 己卯 | 己卯 | ✅ |
| 月柱 | 丙子 | 丙子 | ✅ |
| 日柱 | 戊午 | 戊午 | ✅ |
| 时柱 | 戊午 | 戊午 | ✅ |
| 藏干 | 乙 / 癸 / 丁己 / 丁己 | 历法层不提供 | |
| 纳音 | 城头土 / 涧下水 / 天上火 / 天上火 | 历法层不提供 | |
| 起运 | 逆行 8年2月10日0时 → **2008-03-11 12:00**（虚岁9） | 历法层不提供 | |
| 前4步大运 | 乙亥(2008-17,9-18) 甲戌(2018-27,19-28) 癸酉(2028-37,29-38) 壬申(2038-47,39-48) | 历法层不提供 | |

> 四大柱两库完全一致。`己卯` 为 1999 癸卯岁次后的阴年（己属阴），阴年男命 → **逆行**大运，符合「阴男逆排」。

### 案例 2 —— `2000-02-04 18:00`（立春约当日 20:40，边界内）❗

| 项目 | lunar_python (sect=2) | sxtwl（立春为年界） | sxtwl（正月初一为年界） | 结论 |
|---|---|---|---|---|
| 年柱 | 己卯 | 庚辰 | 己卯 | ❗ |
| 月柱 | 丁丑 | 戊寅 | 戊寅 | ❗ |
| 日柱 | 壬辰 | 壬辰 | 壬辰 | ✅ |
| 时柱 | 己酉 | 己酉 | 己酉 | ✅ |
| 藏干 | 乙/己癸辛/戊乙癸/辛 | 历法层不提供 | | |
| 纳音 | 城头土/涧下水/长流水/大驿土 | 历法层不提供 | | |
| 起运 | 逆行 9年9月10日0时 → **2009-11-14 18:00**（虚岁10） | 历法层不提供 | | |
| 前4步大运 | 丙子(2009-18) 乙亥(19-28) 甲戌(29-38) 癸酉(39-48) | 历法层不提供 | | |

> ❗ **这是两库唯一真正的分歧案例**，正是「立春交接时刻在当日」的边界场景。
> lunar_python 以**立春精确时刻（2000-02-04 20:40:24）**为换年/换月界：18:00 仍在立春前，故年柱 **己卯**、月柱 **丁丑**（丑月未过）。
> sxtwl 的 `getYearGZ(False)` 与 `getMonthGZ()` 以**立春整日**为界（忽略时分秒），立春日（0:00 起）即视为 **庚辰年 / 戊寅月**。
> 实测 sxtwl（`getYearGZ(False)`）在 2000-02-04 的 00:00、12:00、18:00、23:00 均返回 `庚辰`，证明确为「按日」而非「按时刻」。
> 结论：**做边界换月/换年判定时建议以 lunar_python 的 `getXxxExact`（按立春交接时刻）为准**；sxtwl 更适合验证非边界日的干支（其 `getYearGZ(True)` 用正月初一，与八字流派×春节界不同）。

### 案例 3 —— `2000-02-05 09:00`（立春后）

| 项目 | lunar_python (sect=2) | sxtwl | 结论 |
|---|---|---|---|
| 年柱 | 庚辰 | 庚辰 | ✅ |
| 月柱 | 戊寅 | 戊寅 | ✅ |
| 日柱 | 癸巳 | 癸巳 | ✅ |
| 时柱 | 丁巳 | 丁巳 | ✅ |
| 藏干 | 戊乙癸/甲丙戊/丙庚戊/丙庚戊 | 历法层不提供 | |
| 纳音 | 白蜡金/城头土/长流水/沙中土 | 历法层不提供 | |
| 起运 | 顺行 9年8月20日0时 → **2009-10-25 09:00**（虚岁10） | 历法层不提供 | |
| 前4步大运 | 己卯(10-19) 庚辰(20-29) 辛巳(30-39) 壬午(40-49) | 历法层不提供 | |

> ✅ 完全一致。庚辰为阳年，阳年男命 → **顺行**。

### 案例 4 —— `1984-02-02 12:00`（甲子年立春边界，立春为 2-04）❗(仅春节界选项)

| 项目 | lunar_python (sect=2) | sxtwl（立春为年界） | sxtwl（正月初一为年界） | 结论 |
|---|---|---|---|---|
| 年柱 | 癸亥 | 癸亥 | 甲子 | ✅/❗ |
| 月柱 | 乙丑 | 乙丑 | 乙丑 | ✅ |
| 日柱 | 丙寅 | 丙寅 | 丙寅 | ✅ |
| 时柱 | 甲午 | 甲午 | 甲午 | ✅ |
| 藏干 | 壬甲/己癸辛/甲丙戊/丁己 | 历法层不提供 | | |
| 纳音 | 大海水/海中金/炉中火/沙中金 | 历法层不提供 | | |
| 起运 | 逆行 9年0月0日0时 → **1993-02-02 12:00**（虚岁10） | 历法层不提供 | | |
| 前4步大运 | 甲子(10-19) 癸亥(20-29) 壬戌(30-39) 辛酉(40-49) | 历法层不提供 | | |

> ✅ 两库在**立春界**下一致：1984-02-02 是**正月初一（春节）**，但**尚未到立春（2-04 23:18:44）**，故八字年柱仍为 **癸亥**（猪年），月柱 **乙丑**。
> ❗ 只有当主动使用 sxtwl `getYearGZ(True)`（正月初一为年界）时才会看到年柱变为 **甲子**。这正是「八字以立春为年界」与「农历生肖以春节为年界」的差别，lunar_python 与 sxtwl 的立春界完全一致。

### 案例 5 —— `1990-06-15 13:30`

| 项目 | lunar_python (sect=2) | sxtwl | 结论 |
|---|---|---|---|
| 年柱 | 庚午 | 庚午 | ✅ |
| 月柱 | 壬午 | 壬午 | ✅ |
| 日柱 | 辛亥 | 辛亥 | ✅ |
| 时柱 | 乙未 | 乙未 | ✅ |
| 藏干 | 丁己/丁己/壬甲/己丁乙 | 历法层不提供 | |
| 纳音 | 路旁土/杨柳木/钗钏金/沙中金 | 历法层不提供 | |
| 起运 | 顺行 7年4月20日0时 → **1997-11-04 13:30**（虚岁8） | 历法层不提供 | |
| 前4步大运 | 癸未(8-17) 甲申(18-27) 乙酉(28-37) 丙戌(38-47) | 历法层不提供 | |

> ✅ 完全一致。

### 案例 6 —— `2024-02-10 00:30`（春节 + 早晚子时边界）

| 项目 | lunar_python (sect=2) | sxtwl | 结论 |
|---|---|---|---|
| 年柱 | 甲辰 | 甲辰 | ✅ |
| 月柱 | 丙寅 | 丙寅 | ✅ |
| 日柱 | 甲辰 | 甲辰 | ✅ |
| 时柱 | 甲子 | 甲子 | ✅ |
| 藏干 | 戊乙癸/甲丙戊/戊乙癸/癸 | 历法层不提供 | |
| 纳音 | 覆灯火/炉中火/覆灯火/海中金 | 历法层不提供 | |
| 起运 | 顺行 8年1月20日0时 → **2032-03-30 00:30**（虚岁9） | 历法层不提供 | |
| 前4步大运 | 丁卯(9-18) 戊辰(19-28) 己巳(29-38) 庚午(39-48) | 历法层不提供 | |

> ✅ 完全一致。00:30 属**早子时**，不触发换日，两库时柱均为 **甲子**（甲辰日 → 甲子时，五鼠遁「甲己还加甲」）。

### 案例 7 —— `1976-07-28 03:42`

| 项目 | lunar_python (sect=2) | sxtwl | 结论 |
|---|---|---|---|
| 年柱 | 丙辰 | 丙辰 | ✅ |
| 月柱 | 乙未 | 乙未 | ✅ |
| 日柱 | 辛巳 | 辛巳 | ✅ |
| 时柱 | 庚寅 | 庚寅 | ✅ |
| 藏干 | 戊乙癸/己丁乙/丙庚戊/甲丙戊 | 历法层不提供 | |
| 纳音 | 沙中土/沙中金/白蜡金/松柏木 | 历法层不提供 | |
| 起运 | 顺行 3年6月10日0时 → **1980-02-07 03:42**（虚岁5） | 历法层不提供 | |
| 前4步大运 | 丙申(5-14) 丁酉(15-24) 戊戌(25-34) 己亥(35-44) | 历法层不提供 | |

> ✅ 完全一致。

### 案例 8 —— `1949-10-01 15:00`

| 项目 | lunar_python (sect=2) | sxtwl | 结论 |
|---|---|---|---|
| 年柱 | 己丑 | 己丑 | ✅ |
| 月柱 | 癸酉 | 癸酉 | ✅ |
| 日柱 | 甲子 | 甲子 | ✅ |
| 时柱 | 壬申 | 壬申 | ✅ |
| 藏干 | 己癸辛/辛/癸/庚壬戊 | 历法层不提供 | |
| 纳音 | 霹雳火/剑锋金/海中金/剑锋金 | 历法层不提供 | |
| 起运 | 逆行 7年9月10日0时 → **1957-07-11 15:00**（虚岁9） | 历法层不提供 | |
| 前4步大运 | 壬申(9-18) 辛未(19-28) 庚午(29-38) 己巳(39-48) | 历法层不提供 | |

> ✅ 完全一致。己丑为阴年，阴年男命 → **逆行**，四柱（己丑/癸酉/甲子/壬申）与公开在线命盘结果一致（见 §3）。

### 案例 9 —— `2000-02-29 23:30`（晚子时 23:00 后）❗（流派差异）

| 项目 | lunar_python sect=2 | lunar_python sect=1 | sxtwl | 结论 |
|---|---|---|---|---|
| 年柱 | 庚辰 | 庚辰 | 庚辰 | ✅ |
| 月柱 | 戊寅 | 戊寅 | 戊寅 | ✅ |
| 日柱 | 丁巳 | 戊午 | 丁巳 | ❗ |
| 时柱 | 壬子 | 壬子 | 壬子（zw）/ 庚子（nzw） | ❗ |
| 藏干 | 戊乙癸/甲丙戊/丙庚戊/癸 | 戊乙癸/甲丙戊/丁己/癸 | 历法层不提供 | |
| 纳音 | 白蜡金/城头土/沙中土/桑柘木 | 白蜡金/城头土/天上火/桑柘木 | 历法层不提供 | |
| 起运 | 顺行 1年6月20日0时 → **2001-09-17 23:30**（虚岁2） | 同左 | 历法层不提供 | |
| 前4步大运 | 己卯(2-11) 庚辰(12-21) 辛巳(22-31) 壬午(32-41) | 同左 | 历法层不提供 | |

> ❗ 这是**早晚子时**（晚子时 23:00–23:59）的处理差异：
> - **日柱**：lunar_python `sect=2`（默认）= **丁巳**（晚子时日柱**算当天**）；`sect=1` = **戊午**（晚子时日柱**算明天**）。sxtwl `getDayGZ()` = **丁巳**，与 sect=2 一致。
> - **时柱**：lunar = **壬子**；sxtwl `getHourGZ(23, True)`（默认，早晚子时开）= **壬子**，两者一致；只有 sxtwl `getHourGZ(23, False)`（早晚子时关）= **庚子**。
> - 即：两库**默认配置**（lunar sect=2 / sxtwl isZaoWanZiShi=True）在晚子时上**完全一致**（丁巳 / 壬子）；分歧仅来自主动切换流派 1 或关闭 sxtwl 的早晚子时开关。
> 说明：lunar_python 的时柱**始终**按「晚子时用明日日干」的规则计算（`__computeTime` 固定用 `__dayGanIndexExact`，即 23:00 后加一日），故时柱同为 `壬子`（戊日→壬子时），与 sxtwl 的 zhī 一致。

---

## 3. web_search 权威出处核对（公开排盘实例）

以下为网上可查的公开排盘/教程实例，与 lunar_python 输出逐项核对：

1. **2000-02-05 出生**（案例 3），某在线命盘给出「庚辰 戊寅 癸巳 ＊」——年柱 **庚辰**、月柱 **戊寅**、日柱 **癸巳** 与 lunar_python 完全一致（时柱随出生时辰而异）。来源：http://m-mfsm.kvov.com/fx/2000-02-05/bzmp-3-2.html （标题「庚辰戊寅癸巳癸丑」）。

2. **1949-10-01 出生**（案例 8），在线命盘给出「己丑 癸酉 甲子 ＊」——年 **己丑**、月 **癸酉**、日 **甲子** 与 lunar_python 完全一致（其标题时柱「庚午」为午时版本；我们测试用 15:00 申时，得 **壬申**，二者同一日柱之五鼠遁结果）。来源：http://m-mfsm.kvov.com/fx/1949-10-01/bzmp-13-1.html。

3. **lunar-python 官方 demo.py**（6tail 维护）——展示 `Solar→Lunar→getEightChar→getYun→getDaYun` 的标准调用链，与本文 §1.1 代码结构一致。来源：https://gitee.com/solmyr888/lunar-python/blob/master/demo.py 。

4. **大运方向规则**「阳男阴女顺排，阴男阳女逆排，一般排八步运」——与 lunar_python `Yun.__init__` 中 `forward = (yang and man) or (not yang and not man)`（男人阳干则顺）一致。来源：http://mt.sohu.com/20170528/n494854843.shtml ；https://bazi.cc/learn/classics/yuanhai-luck-pillars 。

5. **起运「三日折一年」与「日干推时干口诀（五鼠遁）」**——lunar_python `Yun.__compute_start` 的 sect=1「3天折1年、1天折4月、1时辰折10天」实现与通行规则一致；时干按「甲己还加甲、…、戊癸起壬子」逐日推算。来源：https://www.zhycw.com/art/wap.aspx?nid=249&p=1&cp=1&cid=5&sp=9 ；http://www.360doc.com/content/25/0810/10/9881723_1159111919.shtml 。

> 注：上述个别来源为免费算命/信息站，权威度中等，但对**四柱干支**这类确定性结果可作为独立实现的交叉校验；第 3、4、5 项为权威教程/官方代码，用于印证规则与接口。

---

## 4. lunar_python 关键行为逐条核实（读安装包源码）

以下结论均来自 `site-packages\lunar_python` 源码（EightChar.py / Lunar.py / eightchar\Yun.py / util\LunarUtil.py）。

### 4.1 `EightChar.setSect(n)`（流派 1/2 的确切区别）

- 默认 `sect = 2`（`EightChar.__init__`）。**唯一受流派影响的字段是「日柱」**（年/月/时柱不受 sect 影响）。
- **sect=1**：晚子时（23:00–23:59）**日柱算明天**（`getDayInGanZhiExact`），即 23:00 换日。
- **sect=2**：晚子时（23:00–23:59）**日柱算当天**（`getDayInGanZhiExact2`），即 23:00 不换日。
- 代码依据（`Lunar.__computeDay`）：
  ```python
  # 八字流派2，晚子时（夜子/子夜）日柱算当天
  self.__dayGanIndexExact2 = day_gan_exact
  # 八字流派1，晚子时（夜子/子夜）日柱算明天
  if "23:00" <= hm <= "23:59":
      day_gan_exact += 1; day_zhi_exact += 1
  ```
- 注意：**`藏干表（ZHI_HIDE_GAN）和起运算法与 sect 无关**；`sect` 仅影响日柱的「晚子时是否换日」。这点容易误解，需明确。
- **易错点（实测确认）**：`Lunar.getEightChar()` 返回**缓存单例**（`self.__eightChar` 只建一次）。因此要对比流派 1/2 时，**必须为每个流派新建一个 `Lunar` 对象**，或每次读取前重新 `setSect`；同一 `Lunar` 上先 `setSect(1)` 再 `setSect(2)` 会共用最后一个 sect。

### 4.2 早晚子时如何处理（23:00 是否换日）

- 换日与否由 sect 决定（见上）。**时柱**（`getTimeGan`）不受 sect 影响：`__computeTime` 固定用 `self.__dayGanIndexExact`（即「23:00 后按明日日干当 子时」）计算，因此晚子时 `时干` 恒为「明日日干的子时」。
- 时支划分（`LunarUtil.getTimeZhiIndex`）：`01:00–02:59→丑`、…、`21:00–22:59→亥`，而 **`23:00–23:59` 与 `00:00–00:59` 均落入「子」**（返回索引 0），即晚子时与早子时同为子时。
- 实测（2000-02-29 23:30）：sect1 日=戊午，sect2 日=丁巳，二者时柱均为 **壬子**；与 sxtwl `getHourGZ(23, True)`=壬子 一致。

### 4.3 换年用立春还是正月初一

- 三种并存，**八字（EightChar）用的是「立春精确时刻」**：
  - `getYearInGanZhi()` → 用**农历年干支**（以正月初一为年界）。
  - `getYearInGanZhiByLiChun()` → 用**立春日**（按日期，不含时分）。
  - `getYearInGanZhiExact()`（EightChar 采用）→ 用**立春交接时刻**（按 `toYmdHms` 精确比较）。
- 依据（`Lunar.__computeYear`）：比较 `solar_ymd_hms < li_chun_ymd_hms` 决定是否提前一年。立春时刻取自 `self.__jieQi["立春"]`。
- 同理月柱：`getMonthInGanZhiExact()` 按**节交接时刻**（`__computeMonth` 第二段，用 `toYmdHms` 比较）确定月支，且只取「节」（`JIE_QI_IN_USE` 偶数位：立春、惊蛰、清明…），立春为寅月起点。

### 4.4 `Yun.getStartYear/getStartMonth/getStartDay/getStartSolar` 算法

- 正/逆行：`yang = (年干为阳)`（`getYearGanIndexExact() % 2 == 0` 为阳），`forward = (yang and 男) or (not yang and 女)`。即**阳男、阴女顺行**；**阴男、阳女逆行**。

- sect=1（默认，**3 天折 1 岁**）：
  ```
  取 prev_jie（上一节）与 next_jie（下一节）阳历
  forward: start=出生时刻, end=next_jie时刻
  逆行:    start=prev_jie时刻, end=出生时刻
  hour_diff = 时辰差(子时23:00按索引11处理；<0则+12且day_diff-1)
  month_diff = int(hour_diff*10/30)
  month = day_diff*4 + month_diff          # 1天=4月 => 3天=1年
  day   = hour_diff*10 - month_diff*30      # 1时辰=10天
  year  = int(month/12); month -= year*12
  ```
  即把出生时刻到最近「节」的时日差，换算成「岁→月→日」的起运偏移量。

- sect=2（按分钟）：
  ```
  minutes = 最近节与出生时刻的分钟差
  year  = minutes // 4320      # 4320分=3天 => 1年
  month = (余)   // 360        # 360分  = 1月
  day   = (余)   // 12         # 12分   = 1天
  hour  = (余)   * 2           # 1分    = 2时
  ```

- `getStartSolar()`：`bornSolar.nextYear(startYear).nextMonth(startMonth).next(startDay).nextHour(startHour)`，即出生时刻加上偏移量得到**起运公历日期**。
- 大运：`getDaYun(n)` 返回列表，索引 0=起运前（`startAge=1`），索引 `i≥1` 的干支＝月柱干支顺/逆行 `i` 位；起算年份＝起运年＋(i-1)×10。

### 4.5 `EightChar` 提供的现成方法（逐个签名）

| 类别 | 方法 |
|---|---|
| 四柱干支 | `getYear/getMonth/getDay/getTime`（→字符串）、`getYearGan/getYearZhi/getMonthGan/getMonthZhi/getDayGan/getDayZhi/getTimeGan/getTimeZhi` |
| 藏干 | `getYearHideGan/getMonthHideGan/getDayHideGan/getTimeHideGan`（返回主气/余气/杂气 1–3 元素列表） |
| 五行 | `getYearWuXing/getMonthWuXing/getDayWuXing/getTimeWuXing` |
| 纳音 | `getYearNaYin/getMonthNaYin/getDayNaYin/getTimeNaYin/getTaiYuanNaYin/getTaiXiNaYin/getMingGongNaYin/getShenGongNaYin` |
| 十神 | `getYearShiShenGan/getMonthShiShenGan/getTimeShiShenGan`、`getYearShiShenZhi/getMonthShiShenZhi/getDayShiShenZhi/getTimeShiShenZhi`（藏干十神）、`getDayShiShenGan()`（恒返「日主」） |
| 地势（十二长生） | `getYearDiShi/getMonthDiShi/getDayDiShi/getTimeDiShi` |
| 旬/空亡 | `getYearXun/getMonthXun/getDayXun/getTimeXun`、`getYearXunKong/getMonthXunKong/getDayXunKong/getTimeXunKong` |
| 胎元/胎息 | `getTaiYuan/getTaiXi`（+各自纳音） |
| 命宫/身宫 | `getMingGong/getShenGong`（+各自纳音） |
| 运/大运 | `getYun(gender, sect)`、`getLunar()`、`toString()` |
| 流派 | `getSect/setSect` |

### 4.6 `LunarUtil` 中与合冲刑害 / 神煞 / 禄刃相关的常量与方法

实际源码中**存在**的命名（部分用户猜测的名字并**不存在**，需澄清）：

| 常量 / 方法 | 内容样例 | 说明 |
|---|---|---|
| `LunarUtil.CHONG` | `("午","未","申","酉","戌","亥","子","丑","寅","卯","辰","巳")` | 地支六冲（索引0=子→午）。`Lunar.getDayChong()` 用它 |
| `LunarUtil.CHONG_GAN` | `("戊","己",…)` | 冲干（索引0=甲→戊） |
| `LunarUtil.CHONG_GAN_TIE` | `("己","戊",…)` | 冲干（贴身冲） |
| `LunarUtil.CHONG_GAN_4` | `("庚","辛",…)` | 冲干（四柱用） |
| `LunarUtil.HE_GAN_5` | `("己","庚",…)` | 天干五合（甲己合等，索引0=甲→己） |
| `LunarUtil.HE_ZHI_6` | `("丑","子",…)` | 地支六合（索引0=子→丑） |
| `LunarUtil.LU` | `{"甲":"寅","乙":"卯","丙":"巳","戊":"巳",…,"寅":"甲","巳":"丙,戊",…}` | 天干禄 / 地支所藏禄（含 十干禄） |
| `LunarUtil.SHA` | `{"子":"南","丑":"东",…}` | 坐山煞（方位） |
| `LunarUtil.XUN` | `("甲子","甲戌","甲申","甲午","甲辰","甲寅")` | 六旬 |
| `LunarUtil.XUN_KONG` | `("戌亥","申酉","午未","辰巳","寅卯","子丑")` | 旬空/空亡（索引与 XUN 对应） |
| `LunarUtil.NAYIN` | `{"甲子":"海中金","乙丑":"海中金",…}` | 六十甲子纳音 |
| `LunarUtil.SHI_SHEN` | `{"甲甲":"比肩","甲乙":"劫财",…}` | 十神表（键=日干+他干） |
| `LunarUtil.ZHI_HIDE_GAN` | `{"子":["癸"],"丑":["己","癸","辛"],…}` | 藏干表 |
| `LunarUtil.WU_XING_GAN` / `WU_XING_ZHI` | `{"甲":"木",…}` / `{"寅":"木",…}` | 干支五行 |
| `LunarUtil.getJiaZiIndex(gan_zhi)` | `(static)` | 干支→甲子序号 |
| `LunarUtil.getXun(gan_zhi)` | `(static)` | 干支→所在旬 |
| `LunarUtil.getXunKong(gan_zhi)` | `(static)` | 干支→旬空 |
| `LunarUtil.getXunIndex(gan_zhi)` | `(static)` | 干支→旬索引(0–5) |

> ⚠️ **你猜测的 `HARM`（刑/害）、`LIU_HE`、`CHANG_SHENG`（长生）这三项在 `LunarUtil` 里并不存在。**
> - `CHANG_SHENG` 是 `EightChar` 的类常量（`EightChar.CHANG_SHENG = ("长生","沐浴",…)`），不在 `LunarUtil`。
> - 六合在 `LunarUtil` 中叫 `HE_ZHI_6`，六冲叫 `CHONG`；**「害」「刑」没有现成常量**（需自行用五合/六冲/相刑表扩展）。
> - 因此做「合冲刑害」需自行补「相害（六害）」「相刑（三刑/自刑）」表，lunar_python 未内置。

---

## 5. sxtwl 是否提供藏干 / 十神 / 大运等高级八字功能？

**结论：sxtwl 是「历法层」库，只提供四柱干支与节气，不提供藏干、十神、纳音、地势、起运、大运等任何高级断命功能。**

- `Day` 对象仅有：`getYearGZ/getMonthGZ/getDayGZ/getHourGZ`（返回 `GZ{tg,dz}`），以及月/日/时/星期的历法信息（`getLunarYear/getLunarMonth/getLunarDay/isLunarLeap/getWeek/getConstellation`）和节气（`hasJieQi/getJieQi/getJieQiJD`）。
- 无 `藏干`、`十神`、`大运`、`起运`、`纳音` 等接口。
- **用它验证四柱干支的方法**：由于藏干/纳音/十神都是「干支→表」的确定性转换，只要两库四柱干支一致，则这些扩展项必然一致。因此把 sxtwl 输出的 `GZ` 交给（lunar_python 的）`LunarUtil` 表格做查表即可获得与 lunar_python 完全一致的藏干/纳音，从而把 sxtwl 当作**独立的干支/节气校验器**：
  ```python
  hide = LunarUtil.ZHI_HIDE_GAN.get(pillar[1:])   # 从 sxtwl 的月支查藏干
  nayin = LunarUtil.NAYIN.get(pillar)             # 从 sxtwl 的柱干支查纳音
  ```
- 已验证：对 9 个基准日，除「立春当日边界」的年/月柱外，sxtwl 的四柱与 lunar_python 完全一致，进而藏干/纳音/十神/大运均一致。

---

## 6. 结论与选型建议

1. **主引擎用 lunar_python 完全足够且正确**：它内置完整八字体系（四柱、藏干、纳音、十神、地势、旬空、胎元、命宫、身宫、大运、起运、流年/小运），属「纯 Python、零编译依赖」，便于打包与后续断命逻辑扩展。
2. **sxtwl 用作交叉验证很有价值**：它是独立的 C++ 天文历实现（算法与 lunar_python 不同源），可在非边界日严格校验四柱干支与节气时刻；两库的节气经纬度几乎完全一致（2000 年立春同为 `2000-02-04 20:40:24`，1984 年同为 `1984-02-04 23:18:44`）。
3. **唯一的真实分歧在「立春当日边界」**：lunar_python 用立春**精确时刻**换年/月；sxtwl 用立春**整日**换年/月。涉及边界换月/换年（尤其立春前后 24h 内）时必须**以 lunar_python 的 `getXxxExact` 为准**，sxtwl 此处仅作参考。
4. **早晚子时务必明确流派**：两库默认（lunar sect=2 / sxtwl isZaoWanZiShi=True）一致（晚子时日柱算当天、时柱用明日日干）；不同流派需在配置层显式给定，避免交叉验证时误判为「不一致」。
5. **关于「合冲刑害」**：lunar_python 只内置**六冲（CHONG）**、**天干五合（HE_GAN_5）**、**地支六合（HE_ZHI_6）**、**禄（LU）**、**旬空（XUN_KONG）**；**相害、相刑未内置**，如需要应在 `fortune` 包内补充六害/三刑表（建议在 `config.py` 中做成可配置表并标注文献出处）。

---

### 附：踩坑备忘（fast-check 事实）

- `Lunar.getEightChar()` 缓存单例 → 切换流派需新建 Lunar 或重设 sect。
- lunar_python 日柱的「晚子时换日」只在 sect=1 生效；sect 不影响月/年/时柱与起运。
- sxtwl `getYearGZ(b)` 的 `b` 是「正月初一界」开关：`False`=立春、`True`=正月初一；且立春为**整日**粒度。
- sxtwl 的 `getJieQi()` 返回 `int`（节气序号），`getJieQiJD()` 返回儒略日；`GZ.tg/dz` 为 0 基索引。
