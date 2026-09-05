# -*- coding: utf-8 -*-
"""七政四余（果老星宗式）排盘：十二宫、七政四余躔度（宫+宿）、命宫命度、
十干化曜、宫主。

数据源与口径（详见 fortune/qizheng/text.py）：
- 七政（日月金木水火土）与罗计月孛：瑞士星历（pyswisseph，Moshier）回归黄道实测；
- 二十八宿度：通行《果老星宗》度表 + 「立春太阳在虚一度」锚定（古法口径）；
- 命宫：太阳加生时顺数至卯（《张果星宗》安命法，引文见 text.py）；
- 化曜：甲火乙孛丙木丁金戊土己月庚水辛气壬计癸罗（《星学大成》十干变曜）；
- 紫气：无可靠锚点，不推算（如实标注）。
"""
from __future__ import annotations

from dataclasses import dataclass, field

import swisseph as swe

#: 十二宫（回归黄道宫序：0°=白羊戌起，顺行逆地支序；《张果星宗》宫分所属歌）
GONG_CN = {0: ("戌", "白羊"), 1: ("酉", "金牛"), 2: ("申", "阴阳"),
           3: ("未", "巨蟹"), 4: ("午", "狮子"), 5: ("巳", "双女"),
           6: ("辰", "天秤"), 7: ("卯", "天蝎"), 8: ("寅", "人马"),
           9: ("丑", "磨羯"), 10: ("子", "宝瓶"), 11: ("亥", "双鱼")}
#: 地支 → 宫序索引
_ZHI_GONG_IDX = {zhi: idx for idx, (zhi, _) in GONG_CN.items()}

#: 二十八宿通行《果老星宗》度表（古度，分计）
SU_DU = [("角", 12, 0), ("亢", 9, 0), ("氐", 16, 0), ("房", 5, 0), ("心", 6, 0),
         ("尾", 18, 0), ("箕", 9, 50), ("斗", 22, 75), ("牛", 7, 0), ("女", 11, 0),
         ("虚", 9, 25), ("危", 16, 0), ("室", 18, 25), ("壁", 9, 25), ("奎", 18, 0),
         ("娄", 12, 0), ("胃", 15, 0), ("昴", 11, 0), ("毕", 16, 50), ("觜", 0, 50),
         ("参", 9, 50), ("井", 30, 25), ("鬼", 2, 50), ("柳", 13, 50), ("星", 6, 75),
         ("张", 17, 25), ("翼", 20, 25), ("轸", 18, 25)]

#: 宿界（回归黄经，锚定「立春太阳在虚一度」：虚宿起 314°）
SU_BOUNDS: list[tuple[str, float]] = []
_cur = 314.0
_SU_START_IDX = 10  # 虚宿在 SU_DU 中的索引
for _k in range(28):
    _i = (_SU_START_IDX + _k) % 28
    _name, _d, _f = SU_DU[_i]
    SU_BOUNDS.append((_name, _cur % 360.0))
    _cur += _d + _f / 100.0

#: 十干化曜（《星学大成》十干变曜：甲火乙孛丙木丁金戊土己月庚水辛气壬计癸罗）
HUA_YAO = {"甲": "火", "乙": "孛", "丙": "木", "丁": "金", "戊": "土",
           "己": "月", "庚": "水", "辛": "气", "壬": "计", "癸": "罗"}

#: 宫主（《张果星宗》：子丑土、寅亥木、卯戌火、辰酉金、巳申水、午日、未月）
GONG_ZHU = {"子": "土", "丑": "土", "寅": "木", "亥": "木", "卯": "火", "戌": "火",
            "辰": "金", "酉": "金", "巳": "水", "申": "水", "午": "日", "未": "月"}

#: 七政四余（不含紫气）
PLANETS = [("日", swe.SUN), ("月", swe.MOON), ("水", swe.MERCURY),
           ("金", swe.VENUS), ("火", swe.MARS), ("木", swe.JUPITER),
           ("土", swe.SATURN), ("罗", swe.TRUE_NODE), ("计", None),
           ("孛", swe.MEAN_APOG)]

#: 紫气多口径预设（虚拟星，多套速率×起算点同时计算）：
#: rate=度/日；epoch_jd=起算点儒略日（当日 0h UT 从简，如实标注）；
#: epoch_lon=起算点黄经。出处见各条目 note。
ZIQI_PRESETS = [
    {"key": "guolao1900", "name": "果老·1900白羊初度",
     "rate": 1.0 / 29.0, "epoch": (1900, 1, 1), "lon": 0.0,
     "rate_src": "《张果星宗》「紫气二十九日行一度……二十九年一周天」",
     "epoch_src": "现代排盘软件最常用简化起算（1900-01-01 白羊初度）",
     "note": "默认口径（软件最常用）"},
    {"key": "guolao1984", "name": "果老·甲子1984立春",
     "rate": 1.0 / 29.0, "epoch": (1984, 2, 2), "lon": 0.0,
     "rate_src": "《张果星宗》「紫气二十九日行一度」",
     "epoch_src": "上元甲子（1984 立春）起算，0° 锚",
     "note": "甲子纪元简化口径"},
    {"key": "guolao1910", "name": "果老·立成1910",
     "rate": 1.0 / 29.0, "epoch": (1910, 1, 5), "lon": 202.0,
     "rate_src": "《张果星宗》「紫气二十九日行一度」",
     "epoch_src": "早期七政四余星历立成表锚点：1910-01-05 紫气在辰宫二十二度"
                 "（术数论坛通行引用值，见 research/qizheng_tables.md）",
     "note": "立成表锚点口径"},
    {"key": "xingping1900", "name": "星平会海·1900",
     "rate": 1.0 / 28.0, "epoch": (1900, 1, 1), "lon": 0.0,
     "rate_src": "《星平会海》「紫气二十八日行一度，二十八个月过一宫」",
     "epoch_src": "现代排盘软件常用简化起算（1900-01-01 白羊初度）",
     "note": "星平会海速率"},
    {"key": "xingxue1900", "name": "星学大成·1900",
     "rate": 30.0 / 852.17, "epoch": (1900, 1, 1), "lon": 0.0,
     "rate_src": "《星学大成》「一宫住二十八个月，二十八年行一周天」换算"
                 "（二十八个月=852.17 日；底本「一日行三分五十七秒」与该句"
                 "自相矛盾，按后者，如实标注）",
     "epoch_src": "现代排盘软件常用简化起算（1900-01-01 白羊初度）",
     "note": "星学大成速率"},
    {"key": "minguo1910", "name": "民国星历口径·1910",
     "rate": 1.0 / 9.0, "epoch": (1910, 1, 5), "lon": 202.0,
     "rate_src": "术数论坛对民国星历的比对值：以 1910-01-05 辰宫二十二度起算、"
                 "日行六分四十秒（约 1/9 度/日），与古法 28-29 日行一度不同，"
                 "疑为月孛速率，如实标注",
     "epoch_src": "同上（1910-01-05 辰宫二十二度）",
     "note": "民国星历比对口径（疑误用月孛速率）"},
]


def _lon_to_gong(lon: float) -> int:
    return int(lon // 30) % 12


def _lon_to_su(lon: float) -> tuple[str, float]:
    """回归黄经 → (宿名, 宿内度数)。"""
    lon = lon % 360.0
    for i, (name, b) in enumerate(SU_BOUNDS):
        nxt = SU_BOUNDS[(i + 1) % 28][1]
        hi = nxt if nxt > b else nxt + 360.0
        if b <= lon < hi:
            return name, round(lon - b, 2)
    # 收尾：轸宿（最后一个界）到角宿界之间
    name, b = SU_BOUNDS[-1]
    return name, round((lon - b) % 360.0, 2)


def _ming_gong(sun_gong: int, hour_zhi: str) -> int:
    """命宫：太阳宫加生时，顺数地支至卯（《张果星宗》安命法）。
    顺数地支 = 宫序递减，返回宫序索引。"""
    sun_zhi = GONG_CN[sun_gong][0]
    zi = "子丑寅卯辰巳午未申酉戌亥".index(hour_zhi)
    ming_zhi = "子丑寅卯辰巳午未申酉戌亥"[
        ("子丑寅卯辰巳午未申酉戌亥".index(sun_zhi) + (3 - zi)) % 12]
    return _ZHI_GONG_IDX[ming_zhi]


@dataclass
class QiZhengChart:
    year: int = 0
    month: int = 0
    day: int = 0
    hour: int = 0
    minute: int = 0
    hour_zhi: str = ""
    stars: dict[str, dict] = field(default_factory=dict)   # 星 → {lon, gong, gong_cn, su, su_du}
    ming_gong: str = ""
    ming_du: str = ""
    hua_yao: dict[str, str] = field(default_factory=dict)  # 十神? 化曜名 → 星
    hua_yao_star: dict[str, str] = field(default_factory=dict)  # 星 → 化曜名
    ziqi_sel: dict = field(default_factory=dict)           # 紫气选中口径（含宫宿）
    ziqi_rows: list = field(default_factory=list)          # 紫气多口径对照行


def ziqi_positions(jd: float, preset_key: str = "guolao1900",
                   custom=None) -> tuple[dict, list[dict]]:
    """紫气多口径同时计算：返回 (选中口径结果, 全部口径行列表)。

    custom = (rate, epoch_jd, epoch_lon) 时在对照表中追加「自定义」行。
    每个口径行含 rate/epoch/lon 出处与说明，保证可追溯。
    """
    rows: list[dict] = []
    for p in ZIQI_PRESETS:
        ep_jd = swe.julday(*p["epoch"], 0.0)
        lon = (p["lon"] + (jd - ep_jd) * p["rate"]) % 360.0
        rows.append({"key": p["key"], "name": p["name"], "lon": round(lon, 4),
                     "rate": p["rate"], "rate_src": p["rate_src"],
                     "epoch": f"{p['epoch'][0]}-{p['epoch'][1]:02d}-{p['epoch'][2]:02d}",
                     "epoch_lon": p["lon"], "epoch_src": p["epoch_src"],
                     "note": p["note"]})
    if custom is not None:
        rate, ep_jd, ep_lon = custom
        lon = (ep_lon + (jd - ep_jd) * rate) % 360.0
        rows.append({"key": "custom", "name": "自定义", "lon": round(lon, 4),
                     "rate": rate, "rate_src": "自定义速率（度/日）",
                     "epoch": "自定义", "epoch_lon": ep_lon,
                     "epoch_src": "自定义起算点（儒略日与黄经）", "note": "自定义口径"})
    selected = next((r for r in rows if r["key"] == preset_key), rows[0])
    return selected, rows


def _ziqi_gong_su(lon: float) -> dict:
    gong = _lon_to_gong(lon)
    su, su_du = _lon_to_su(lon)
    return {"lon": round(lon, 4), "gong": GONG_CN[gong][0],
            "gong_cn": GONG_CN[gong][1], "su": su, "su_du": su_du}


def qizheng(year: int, month: int, day: int, hour: int, minute: int = 0,
            day_gan: str | None = None, ziqi_preset: str = "guolao1900",
            ziqi_custom=None) -> QiZhengChart:
    """七政四余排盘（公历输入，北京时间；时区硬编码 +8）。"""
    from lunar_python import Solar

    c = QiZhengChart(year=year, month=month, day=day, hour=hour, minute=minute)
    c.hour_zhi = "子丑寅卯辰巳午未申酉戌亥"[((hour + 1) // 2) % 12]
    if day_gan is None:
        day_gan = Solar.fromYmdHms(year, month, day, hour, minute, 0) \
            .getLunar().getDayInGanZhi()[0]
    ut = hour + minute / 60.0 - 8.0
    jd = swe.julday(year, month, day, ut)
    for name, pid in PLANETS:
        if name == "计":
            continue
        pos, _ = swe.calc_ut(jd, pid)
        lon = pos[0] % 360.0
        gong = _lon_to_gong(lon)
        su, su_du = _lon_to_su(lon)
        c.stars[name] = {"lon": round(lon, 4), "gong": GONG_CN[gong][0],
                         "gong_cn": GONG_CN[gong][1], "su": su, "su_du": su_du}
    # 计都 = 罗睺对宫（180°）
    luo_lon = c.stars["罗"]["lon"]
    ji_lon = (luo_lon + 180.0) % 360.0
    gong = _lon_to_gong(ji_lon)
    su, su_du = _lon_to_su(ji_lon)
    c.stars["计"] = {"lon": round(ji_lon, 4), "gong": GONG_CN[gong][0],
                     "gong_cn": GONG_CN[gong][1], "su": su, "su_du": su_du}
    # 紫气：多口径同时计算（虚拟星，速率×起算点各预设并列，可追溯）
    ziqi_sel, ziqi_rows = ziqi_positions(jd, preset_key=ziqi_preset,
                                         custom=ziqi_custom)
    c.ziqi_sel = dict(ziqi_sel)
    c.ziqi_sel.update(_ziqi_gong_su(ziqi_sel["lon"]))
    c.ziqi_rows = ziqi_rows
    c.stars["气"] = _ziqi_gong_su(ziqi_sel["lon"])
    c.stars["气"]["preset"] = ziqi_sel["name"]
    # 命宫命度：太阳加生时顺数至卯
    sun_gong = _lon_to_gong(c.stars["日"]["lon"])
    ming = _ming_gong(sun_gong, c.hour_zhi)
    c.ming_gong = GONG_CN[ming][0]
    ming_lon = (c.stars["日"]["lon"] + (ming - sun_gong) * 30.0) % 360.0
    su, su_du = _lon_to_su(ming_lon)
    c.ming_du = f"{su}{su_du:g}度"
    # 化曜（十干变曜）
    if day_gan:
        yao = HUA_YAO.get(day_gan, "")
        c.hua_yao = {yao: day_gan} if yao else {}
        for xing in ("火", "孛", "木", "金", "土", "月", "水", "气", "计", "罗"):
            c.hua_yao_star[xing] = [g for g, y in HUA_YAO.items() if y == xing]
    return c


__all__ = ["QiZhengChart", "qizheng", "ziqi_positions", "_lon_to_su",
           "SU_DU", "SU_BOUNDS", "HUA_YAO", "GONG_ZHU", "GONG_CN",
           "ZIQI_PRESETS"]

