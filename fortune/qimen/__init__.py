# -*- coding: utf-8 -*-
"""奇门遁甲（时家奇门）排盘：节气定局（阴阳遁、三元）→ 地盘三奇六仪 →
值符值使 → 天盘九星 / 八门 / 八神。

规则逐字依据：
- 《奇门遁甲秘笈大全》（research/fetched/奇门秘笈大全.txt，明清汇编，
  题诸葛武侯/刘基，托名已按通行说法标注）「奇门掌中金要诀」与阳遁/阴遁九宫起例歌；
- 《烟波钓叟歌》（维基文库本，research/fetched/wikisource_yanbodiao sou.txt）。

口径（如实标注，见 NOTES）：
- 三元按「日干支符头」（甲己 + 子午卯酉=上元、寅申巳亥=中元、辰戌丑未=下元）
  的拆补简化法；置闰、超神接气未实现；
- 中宫（五宫）寄坤二宫（天禽寄坤、值使落中宫取死门），见《秘笈大全》
  「惟天禽则无定位，寄西南而属中宫」；
- 值使门加时支宫（时支按地支所在九宫：子坎一、丑寅艮八、卯震三、辰巳巽四、
  午离九、未申坤二、酉兑七、戌亥乾六），其余门按门序顺布——此口径与
  《秘笈大全》「阳遁二局甲子日乙丑时，休门飞到坤二宫」互证。
"""
from __future__ import annotations

import datetime as _dt

from dataclasses import dataclass, field

from lunar_python import Lunar

#: 九宫序（含中五）
GONG_XU = [1, 2, 3, 4, 5, 6, 7, 8, 9]
#: 八门排布宫序（门不入中五）
MEN_GONG_XU = [1, 2, 3, 4, 6, 7, 8, 9]

#: 九宫 → 本位九星（坎一蓬…离九英）
GONG_XING = {1: "天蓬", 2: "天芮", 3: "天冲", 4: "天辅", 5: "天禽",
             6: "天心", 7: "天柱", 8: "天任", 9: "天英"}
#: 九星序列（值符星起，顺布用）
XING_XU = ["天蓬", "天芮", "天冲", "天辅", "天禽", "天心", "天柱", "天任", "天英"]
#: 九宫 → 本位八门（休坎一生艮八…开乾六）
GONG_MEN = {1: "休门", 8: "生门", 3: "伤门", 4: "杜门", 9: "景门",
            2: "死门", 7: "惊门", 6: "开门"}
#: 八门序列（值使门起，顺布用）
MEN_XU = ["休门", "生门", "伤门", "杜门", "景门", "死门", "惊门", "开门"]
#: 地支 → 九宫（奇门时支宫）
ZHI_GONG = {"子": 1, "丑": 8, "寅": 8, "卯": 3, "辰": 4, "巳": 4,
            "午": 9, "未": 2, "申": 2, "酉": 7, "戌": 6, "亥": 6}
#: 六甲旬首 → 遁干
LIU_JIA_DUN = {"甲子": "戊", "甲戌": "己", "甲申": "庚", "甲午": "辛",
               "甲辰": "壬", "甲寅": "癸"}
#: 阳遁八神（值符起，顺布）；阴遁以白虎玄武替勾陈朱雀并逆布
SHEN_YANG = ["值符", "螣蛇", "太阴", "六合", "勾陈", "朱雀", "九地", "九天"]
SHEN_YIN = ["值符", "螣蛇", "太阴", "六合", "白虎", "玄武", "九地", "九天"]

#: 二十四节气 → (上元局, 中元局, 下元局)（《秘笈大全》阳遁/阴遁九宫起例歌）
JU_TABLE = {
    "冬至": (1, 7, 4), "小寒": (2, 8, 5), "大寒": (3, 9, 6),
    "立春": (8, 5, 2), "雨水": (9, 6, 3), "惊蛰": (1, 7, 4),
    "春分": (3, 9, 6), "清明": (4, 1, 7), "谷雨": (5, 2, 8),
    "立夏": (4, 1, 7), "小满": (5, 2, 8), "芒种": (6, 3, 9),
    "夏至": (9, 3, 6), "小暑": (8, 2, 5), "大暑": (7, 1, 4),
    "立秋": (2, 5, 8), "处暑": (1, 4, 7), "白露": (9, 3, 6),
    "秋分": (7, 1, 4), "寒露": (6, 9, 3), "霜降": (5, 8, 2),
    "立冬": (6, 9, 3), "小雪": (5, 8, 2), "大雪": (4, 7, 1),
}

NOTES = {
    "三元": "三元按日干支符头（甲己+子午卯酉=上元、寅申巳亥=中元、辰戌丑未=下元）"
            "的拆补简化法；置闰、超神接气未实现，如实标注。",
    "中宫": "中五宫寄坤二宫（天禽寄坤、值使落中宫取死门），《秘笈大全》"
            "「惟天禽则无定位，寄西南而属中宫」。",
    "值使": "值使门加时支宫（地支所在九宫），其余门按门序顺布；与《秘笈大全》"
            "「阳遁二局甲子日乙丑时，休门飞到坤二宫」互证。",
    "八神": "阳遁值符螣蛇太阴六合勾陈朱雀九地九天顺布；阴遁以白虎玄武替勾陈朱雀、逆布"
            "（《秘笈大全》「阳遁朱雀即阴遁元武」「阳遁勾陈，阴遁白虎」）。",
}


def _solar_dt(solar):
    return _dt.datetime(solar.getYear(), solar.getMonth(), solar.getDay(),
                        solar.getHour(), solar.getMinute(), solar.getSecond())


def governing_jieqi(dt: "_dt.datetime") -> str:
    """最近过去的节气（二十四节气全量，含中气）名。"""
    y = dt.year
    seen: set = set()
    cands = []
    for yy in (y - 1, y, y + 1):
        table = Lunar.fromYmdHms(yy, 6, 15, 12, 0, 0).getJieQiTable()
        for k, t in table.items():
            if k in JU_TABLE and t is not None:
                d = _solar_dt(t)
                if d in seen:
                    continue
                seen.add(d)
                cands.append((d, k))
    past = [c for c in cands if c[0] <= dt]
    if not past:
        return "冬至"
    return max(past, key=lambda c: c[0])[1]


def day_yuan(day_ganzhi: str) -> str:
    """日干支符头定元：甲己+子午卯酉=上元、寅申巳亥=中元、辰戌丑未=下元
    （拆补法简化口径：按当日支归元）。"""
    zhi = day_ganzhi[1]
    if zhi in "子午卯酉":
        return "上元"
    if zhi in "寅申巳亥":
        return "中元"
    return "下元"


@dataclass
class QimenChart:
    year: int = 0
    month: int = 0
    day: int = 0
    hour: int = 0
    minute: int = 0
    jie_qi: str = ""          # 节气
    dun: str = ""             # 阳遁/阴遁
    ju: int = 0               # 局数
    yuan: str = ""            # 上元/中元/下元
    day_ganzhi: str = ""      # 日干支
    hour_ganzhi: str = ""     # 时干支
    xun_shou: str = ""        # 时旬首
    di_pan: dict[int, str] = field(default_factory=dict)   # 宫 → 地盘奇仪
    zhi_fu_xing: str = ""     # 值符星
    zhi_fu_gong: int = 0      # 值符宫（旬首遁干宫）
    zhi_shi_men: str = ""     # 值使门
    tian_pan: dict[int, str] = field(default_factory=dict)  # 宫 → 天盘星
    men_pan: dict[int, str] = field(default_factory=dict)   # 宫 → 八门
    shen_pan: dict[int, str] = field(default_factory=dict)  # 宫 → 八神
    fu_yin: bool = False      # 星门全伏吟
    fan_yin: bool = False     # 星门全反吟（值符值使俱对宫）


def bu_ju(year: int, month: int, day: int, hour: int, minute: int = 0) -> QimenChart:
    """时家奇门排盘（公历输入）。"""
    from lunar_python import Solar

    solar = Solar.fromYmdHms(year, month, day, hour, minute, 0)
    lunar = solar.getLunar()
    dt = _solar_dt(solar)
    jq = governing_jieqi(dt)
    day_gz = lunar.getDayInGanZhi()
    hour_gz = lunar.getTimeInGanZhi()

    c = QimenChart(year=year, month=month, day=day, hour=hour, minute=minute)
    c.jie_qi = jq
    c.day_ganzhi = day_gz
    c.hour_ganzhi = hour_gz
    shang, zhong, xia = JU_TABLE[jq]
    c.yuan = day_yuan(day_gz)
    c.ju = {"上元": shang, "中元": zhong, "下元": xia}[c.yuan]
    c.dun = "阳遁" if jq in ("冬至", "小寒", "大寒", "立春", "雨水", "惊蛰",
                            "春分", "清明", "谷雨", "立夏", "小满", "芒种") else "阴遁"
    yang = c.dun == "阳遁"

    # 地盘三奇六仪：阳遁顺布六仪逆布三奇（戊己庚辛壬癸丁丙乙）；阴遁反之
    seq = "戊己庚辛壬癸" + ("丁丙乙" if yang else "乙丙丁")
    start = c.ju
    step = 1 if yang else -1
    for i, g in enumerate(seq):
        gong = ((start - 1 + i * step) % 9) + 1
        c.di_pan[gong] = g

    # 值符值使：时旬首 → 六甲遁干 → 宫
    gan_idx = "甲乙丙丁戊己庚辛壬癸".index(hour_gz[0])
    zhi_idx = "子丑寅卯辰巳午未申酉戌亥".index(hour_gz[1])
    xun_zhi = "子丑寅卯辰巳午未申酉戌亥"[(zhi_idx - gan_idx) % 12]
    c.xun_shou = "甲" + xun_zhi
    dun_gan = LIU_JIA_DUN[c.xun_shou]
    zhi_fu_gong = next(g for g, d in c.di_pan.items() if d == dun_gan)
    c.zhi_fu_gong = zhi_fu_gong
    c.zhi_fu_xing = GONG_XING[zhi_fu_gong]
    c.zhi_shi_men = GONG_MEN.get(zhi_fu_gong, "死门")  # 中五寄坤二 → 死门

    # 天盘九星：值符星加时干宫（时干甲 → 值符宫），其余按星序顺飞（阳顺阴逆）
    hour_gan = hour_gz[0]
    if hour_gan == "甲":
        shi_gan_gong = zhi_fu_gong
    else:
        shi_gan_gong = next(g for g, d in c.di_pan.items() if d == hour_gan)
    anchor = XING_XU.index(c.zhi_fu_xing)
    for i in range(9):
        gong = ((shi_gan_gong - 1 + i * (1 if yang else -1)) % 9) + 1
        c.tian_pan[gong] = XING_XU[(anchor + i) % 9]

    # 八门：值使门加时支宫，其余按门序顺布（宫序跳中五）
    shi_zhi = hour_gz[1]
    shi_zhi_gong = ZHI_GONG[shi_zhi]
    men_anchor = MEN_XU.index(c.zhi_shi_men)
    men_order = MEN_GONG_XU if yang else list(reversed(MEN_GONG_XU))
    # 值使门定位在时支宫（该宫在排布序中的位置）
    try:
        pos = men_order.index(shi_zhi_gong)
    except ValueError:
        pos = 0
    for i in range(8):
        gong = men_order[(pos + i) % 8]
        c.men_pan[gong] = MEN_XU[(men_anchor + i) % 8]

    # 八神：值符加值符星宫（天盘值符星所在宫；中五寄坤二），阳顺阴逆，八神不入中五
    fu_xing_gong = next(g for g, x in c.tian_pan.items() if x == c.zhi_fu_xing)
    if fu_xing_gong == 5:
        fu_xing_gong = 2
    shen = SHEN_YANG if yang else SHEN_YIN
    gongs: list[int] = []
    i = 0
    while len(gongs) < 8:
        g = ((fu_xing_gong - 1 + i * (1 if yang else -1)) % 9) + 1
        if g != 5:
            gongs.append(g)
        i += 1
    for j, g in enumerate(gongs):
        c.shen_pan[g] = shen[j]

    # 伏吟/反吟：值符星落本宫且值使门落本宫 → 伏吟；值符星落对宫 → 反吟
    ben_gong = {x: g for g, x in GONG_XING.items()}
    men_ben = {m: g for g, m in GONG_MEN.items()}
    fu_xing_ben = ben_gong[c.zhi_fu_xing]
    fu_xing_ben = 2 if fu_xing_ben == 5 else fu_xing_ben
    men_ben_gong = men_ben.get(c.zhi_shi_men, 2)
    c.fu_yin = (fu_xing_gong == fu_xing_ben
                and c.men_pan.get(men_ben_gong) == c.zhi_shi_men)
    c.fan_yin = fu_xing_gong == 10 - fu_xing_ben
    return c


__all__ = ["QimenChart", "bu_ju", "governing_jieqi", "day_yuan",
           "JU_TABLE", "GONG_XING", "GONG_MEN", "ZHI_GONG", "NOTES"]
