"""六爻纳甲 —— 起卦装卦（世应、纳甲、六亲、六神、旬空）。

表来源：research/liuyao_tables.md（《增删卜易》《卜筮正宗》公开文本 + 通行教材交叉核验）。
分歧标注：
- 铜钱「背为阳=3（主流）/ 背为阴」两说——通过 config.liuyao_coin_back 切换，报告中注明约定；
- 六神「戊己」分列勾陈/螣蛇（主流），个别版本合为「戊己勾陈」。
"""
from __future__ import annotations

from dataclasses import dataclass

TRIGRAM_BITS = {"乾": (1, 1, 1), "兑": (1, 1, 0), "离": (1, 0, 1), "震": (1, 0, 0),
                "巽": (0, 1, 1), "坎": (0, 1, 0), "艮": (0, 0, 1), "坤": (0, 0, 0)}
BITS_TRIGRAM = {v: k for k, v in TRIGRAM_BITS.items()}

# 八宫卦序：宫名 → 五行；每宫 8 卦（本宫,一世,二世,三世,四世,五世,游魂,归魂）
# (卦名, 上卦, 下卦, 世爻, 应爻)。来源：research/liuyao_tables.md §1.2
PALACE_WUXING = {"乾": "金", "坎": "水", "艮": "土", "震": "木",
                 "巽": "木", "离": "火", "坤": "土", "兑": "金"}

PALACE_GUA = {
    "乾": [("乾为天", "乾", "乾", 6, 3), ("天风姤", "乾", "巽", 1, 4),
           ("天山遁", "乾", "艮", 2, 5), ("天地否", "乾", "坤", 3, 6),
           ("风地观", "巽", "坤", 4, 1), ("山地剥", "艮", "坤", 5, 2),
           ("火地晋", "离", "坤", 4, 1), ("火天大有", "离", "乾", 3, 6)],
    "坎": [("坎为水", "坎", "坎", 6, 3), ("水泽节", "坎", "兑", 1, 4),
           ("水雷屯", "坎", "震", 2, 5), ("水火既济", "坎", "离", 3, 6),
           ("泽火革", "兑", "离", 4, 1), ("雷火丰", "震", "离", 5, 2),
           ("地火明夷", "坤", "离", 4, 1), ("地水师", "坤", "坎", 3, 6)],
    "艮": [("艮为山", "艮", "艮", 6, 3), ("山火贲", "艮", "离", 1, 4),
           ("山天大畜", "艮", "乾", 2, 5), ("山泽损", "艮", "兑", 3, 6),
           ("火泽睽", "离", "兑", 4, 1), ("天泽履", "乾", "兑", 5, 2),
           ("风泽中孚", "巽", "兑", 4, 1), ("风山渐", "巽", "艮", 3, 6)],
    "震": [("震为雷", "震", "震", 6, 3), ("雷地豫", "震", "坤", 1, 4),
           ("雷水解", "震", "坎", 2, 5), ("雷风恒", "震", "巽", 3, 6),
           ("地风升", "坤", "巽", 4, 1), ("水风井", "坎", "巽", 5, 2),
           ("泽风大过", "兑", "巽", 4, 1), ("泽雷随", "兑", "震", 3, 6)],
    "巽": [("巽为风", "巽", "巽", 6, 3), ("风天小畜", "巽", "乾", 1, 4),
           ("风火家人", "巽", "离", 2, 5), ("风雷益", "巽", "震", 3, 6),
           ("天雷无妄", "乾", "震", 4, 1), ("火雷噬嗑", "离", "震", 5, 2),
           ("山雷颐", "艮", "震", 4, 1), ("山风蛊", "艮", "巽", 3, 6)],
    "离": [("离为火", "离", "离", 6, 3), ("火山旅", "离", "艮", 1, 4),
           ("火风鼎", "离", "巽", 2, 5), ("火水未济", "离", "坎", 3, 6),
           ("山水蒙", "艮", "坎", 4, 1), ("风水涣", "巽", "坎", 5, 2),
           ("天水讼", "乾", "坎", 4, 1), ("天火同人", "乾", "离", 3, 6)],
    "坤": [("坤为地", "坤", "坤", 6, 3), ("地雷复", "坤", "震", 1, 4),
           ("地泽临", "坤", "兑", 2, 5), ("地天泰", "坤", "乾", 3, 6),
           ("雷天大壮", "震", "乾", 4, 1), ("泽天夬", "兑", "乾", 5, 2),
           ("水天需", "坎", "乾", 4, 1), ("水地比", "坎", "坤", 3, 6)],
    "兑": [("兑为泽", "兑", "兑", 6, 3), ("泽水困", "兑", "坎", 1, 4),
           ("泽地萃", "兑", "坤", 2, 5), ("泽山咸", "兑", "艮", 3, 6),
           ("水山蹇", "坎", "艮", 4, 1), ("地山谦", "坤", "艮", 5, 2),
           ("雷山小过", "震", "艮", 4, 1), ("雷泽归妹", "震", "兑", 3, 6)],
}

# 纳甲：卦 → (内卦天干, 外卦天干, 内卦三爻地支, 外卦三爻地支)
# 来源：research/liuyao_tables.md §2（纳甲歌）
NAJIA = {
    "乾": ("甲", "壬", ("子", "寅", "辰"), ("午", "申", "戌")),
    "坎": ("戊", "戊", ("寅", "辰", "午"), ("申", "戌", "子")),
    "艮": ("丙", "丙", ("辰", "午", "申"), ("戌", "子", "寅")),
    "震": ("庚", "庚", ("子", "寅", "辰"), ("午", "申", "戌")),
    "巽": ("辛", "辛", ("丑", "亥", "酉"), ("未", "巳", "卯")),
    "离": ("己", "己", ("卯", "丑", "亥"), ("酉", "未", "巳")),
    "坤": ("乙", "癸", ("未", "巳", "卯"), ("丑", "亥", "酉")),
    "兑": ("丁", "丁", ("巳", "卯", "丑"), ("亥", "酉", "未")),
}

ZHI_WUXING = {"子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火",
              "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水"}
ZHI = "子丑寅卯辰巳午未申酉戌亥"

# 六神顺序与日干起首。来源：research/liuyao_tables.md §4
LIU_SHEN = ("青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武")
LIU_SHEN_START = {"甲": 0, "乙": 0, "丙": 1, "丁": 1, "戊": 2, "己": 3,
                  "庚": 4, "辛": 4, "壬": 5, "癸": 5}

# 旬空：旬首 → 空亡两支。来源：research/liuyao_tables.md §5
XUN_KONG = {"甲子": ("戌", "亥"), "甲戌": ("申", "酉"), "甲申": ("午", "未"),
            "甲午": ("辰", "巳"), "甲辰": ("寅", "卯"), "甲寅": ("子", "丑")}

# 六亲生克（宫五行=我，爻支五行=他）：
#   生我→父母，我生→子孙，克我→官鬼，我克→妻财，比和→兄弟
WUXING_SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}


def liu_qin(palace_wx: str, yao_wx: str) -> str:
    if yao_wx == palace_wx:
        return "兄弟"
    if WUXING_SHENG[yao_wx] == palace_wx:   # 他生我
        return "父母"
    if WUXING_SHENG[palace_wx] == yao_wx:   # 我生他
        return "子孙"
    if WUXING_SHENG[WUXING_SHENG[yao_wx]] == palace_wx:  # 他克我（他生x生我 → 我克x... 注：克表）
        return "官鬼"
    return "妻财"


def find_gua(lower: str, upper: str) -> tuple[str, str, int, int]:
    """按上下卦找（宫名, 卦名, 世爻, 应爻）。"""
    for palace, guas in PALACE_GUA.items():
        for name, up, low, shi, ying in guas:
            if up == upper and low == lower:
                return palace, name, shi, ying
    raise ValueError(f"无法定位卦：{lower} {upper}")


def xun_kong(day_ganzhi: str) -> tuple[str, str]:
    """日干支 → 旬空两支。"""
    gan, zhi = day_ganzhi[0], day_ganzhi[1]
    gi, zi = "甲乙丙丁戊己庚辛壬癸".index(gan), ZHI.index(zhi)
    # 旬首 = 甲X：从当前干支回退 (gi) 位得甲干位置
    offset = (zi - gi) % 12
    xun_shou = "甲" + ZHI[offset]
    return XUN_KONG[xun_shou]


@dataclass
class LiuYaoLine:
    """一爻（1-6 自下而上）。"""
    no: int              # 1-6
    value: int           # 6 老阴 / 7 少阳 / 8 少阴 / 9 老阳
    gan_zhi: str         # 纳甲干支
    liu_qin: str         # 六亲
    liu_shen: str        # 六神
    is_moving: bool      # 是否动爻（6/9）
    bian_gan_zhi: str    # 变爻纳甲干支（按变卦纳甲取支；非动爻时为「—」）
    bian_liu_qin: str    # 变爻六亲（按变爻支、本宫五行论；非动爻时为「—」）

    @property
    def yin_yang(self) -> str:
        return "阳" if self.value in (7, 9) else "阴"

    @property
    def name(self) -> str:
        return {6: "老阴(交)", 7: "少阳(单)", 8: "少阴(拆)", 9: "老阳(重)"}[self.value]


@dataclass
class LiuYaoChart:
    ben_gua: str          # 本卦名
    palace: str           # 卦宫
    palace_wuxing: str    # 宫五行
    shi: int              # 世爻（1-6）
    ying: int             # 应爻
    lines: list[LiuYaoLine]
    bian_gua: str         # 变卦名
    xun_kong: tuple[str, str]
    month_zhi: str        # 月建
    day_ganzhi: str       # 日辰
    coin_back: str        # 铜钱约定 "yang"|"yin"

    def __str__(self) -> str:  # pragma: no cover - 展示用
        L = []
        for ln in reversed(self.lines):
            mark = "○" if ln.value == 9 else "×" if ln.value == 6 else "  "
            bian = f"  化{ln.bian_gan_zhi} {ln.bian_liu_qin}" if ln.is_moving else ""
            L.append(
                f"{ln.no}爻 {ln.gan_zhi} {ln.liu_qin} {ln.liu_shen} "
                f"{ln.name}{' (动)' if ln.is_moving else ''} {mark}{bian}"
            )
        return "\n".join([
            f"本卦 {self.ben_gua}（{self.palace}宫{self.palace_wuxing}） 世{self.shi}爻 应{self.ying}爻",
            *L,
            f"变卦 {self.bian_gua}   月建 {self.month_zhi}  日辰 {self.day_ganzhi}  旬空 {self.xun_kong[0]}{self.xun_kong[1]}",
            f"铜钱约定：背={'阳' if self.coin_back == 'yang' else '阴'}（{'主流' if self.coin_back == 'yang' else '另一派'}）",
        ])


def build(lines: list[int], month_zhi: str, day_ganzhi: str, coin_back: str = "yang") -> LiuYaoChart:
    """由六爻数值（自下而上，6/7/8/9）装卦。

    :param lines: 六个爻值（初爻…上爻）。
    :param month_zhi: 月建地支。
    :param day_ganzhi: 日辰干支（如「甲子」）。
    :param coin_back: "yang"（背=3，主流）| "yin"。
    """
    assert len(lines) == 6 and all(v in (6, 7, 8, 9) for v in lines)
    lower_bits = tuple(1 if v in (7, 9) else 0 for v in lines[0:3])
    upper_bits = tuple(1 if v in (7, 9) else 0 for v in lines[3:6])
    lower, upper = BITS_TRIGRAM[lower_bits], BITS_TRIGRAM[upper_bits]
    palace, ben_name, shi, ying = find_gua(lower, upper)

    # 变卦：动爻翻阴阳
    bian_lower_bits = tuple(1 - b if lines[i] in (6, 9) else b for i, b in enumerate(lower_bits))
    bian_upper_bits = tuple(1 - b if lines[i + 3] in (6, 9) else b for i, b in enumerate(upper_bits))
    bian_lower_tri, bian_upper_tri = (BITS_TRIGRAM[bian_lower_bits], BITS_TRIGRAM[bian_upper_bits])
    _, bian_name, _, _ = find_gua(bian_lower_tri, bian_upper_tri)

    # 纳甲干支（本卦）
    l_gan, _, l_zhi3, _ = NAJIA[lower]
    _, u_gan, _, u_zhi3 = NAJIA[upper]
    gan_zhis = [l_gan + z for z in l_zhi3] + [u_gan + z for z in u_zhi3]
    # 变爻纳甲干支：按变卦纳甲取支（《增删卜易》装卦法：动爻变后以变卦纳支为准）
    bl_gan, _, bl_zhi3, _ = NAJIA[bian_lower_tri]
    _, bu_gan, _, bu_zhi3 = NAJIA[bian_upper_tri]
    bian_gan_zhis = [bl_gan + z for z in bl_zhi3] + [bu_gan + z for z in bu_zhi3]

    # 六神
    start = LIU_SHEN_START[day_ganzhi[0]]
    shens = [LIU_SHEN[(start + i) % 6] for i in range(6)]

    kongs = xun_kong(day_ganzhi)

    out = []
    for i, v in enumerate(lines):
        gz = gan_zhis[i]
        zhi = gz[1]
        qin = liu_qin(PALACE_WUXING[palace], ZHI_WUXING[zhi])
        moving = v in (6, 9)
        bgz = bian_gan_zhis[i]
        # 变爻六亲：以变爻支、本宫五行论（《卜筮正宗》通行；另一派以变卦宫论，见注释）
        bqin = liu_qin(PALACE_WUXING[palace], ZHI_WUXING[bgz[1]])
        out.append(LiuYaoLine(
            no=i + 1, value=v, gan_zhi=gz, liu_qin=qin, liu_shen=shens[i],
            is_moving=moving, bian_gan_zhi=bgz, bian_liu_qin=bqin,
        ))
    return LiuYaoChart(
        ben_gua=ben_name, palace=palace, palace_wuxing=PALACE_WUXING[palace],
        shi=shi, ying=ying, lines=out, bian_gua=bian_name,
        xun_kong=kongs, month_zhi=month_zhi, day_ganzhi=day_ganzhi,
        coin_back=coin_back,
    )


def from_coins(backs: list[int], month_zhi: str, day_ganzhi: str,
               coin_back: str = "yang") -> LiuYaoChart:
    """由三枚铜钱每掷「背」的个数起卦。

    :param backs: 六次投掷中「背」的个数（0-3），自下而上。
    :param coin_back: "yang" → 背=3 字=2（值=6+背数，主流）；"yin" → 背=2 字=3（值=9-背数）。
    """
    assert len(backs) == 6 and all(0 <= b <= 3 for b in backs)
    if coin_back == "yang":
        values = [6 + b for b in backs]
    else:
        values = [9 - b for b in backs]
    return build(values, month_zhi, day_ganzhi, coin_back)
