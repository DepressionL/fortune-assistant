"""梅花易数 —— 时间起卦 / 数字起卦，体用互变。

硬编码表来源：
- 先天八卦数（乾一兑二离三震四巽五坎六艮七坤八）：邵雍《梅花易数》通行本；
- 六十四卦名：通行本《周易》（该表与 King Wen 序无关，按 (下卦×8+上卦) 索引）；
- 八卦五行（乾兑金、离火、震巽木、坎水、艮坤土）：《梅花易数》通行本。

争议说明：动爻所在卦为「用」、不动为「体」是通行主流；个别流派以静卦为用，
本项目采用主流约定。
"""
from __future__ import annotations

from dataclasses import dataclass

# 先天八卦数 → 卦（索引 0-7）
XIAN_TIAN = ("乾", "兑", "离", "震", "巽", "坎", "艮", "坤")
#: 先天数（1-8）→ 索引
NUM_TO_IDX = {1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 7}
#: 卦 → 先天数
GUA_TO_NUM = {g: i + 1 for i, g in enumerate(XIAN_TIAN)}
#: 卦 → 五行
GUA_WUXING = {"乾": "金", "兑": "金", "离": "火", "震": "木",
              "巽": "木", "坎": "水", "艮": "土", "坤": "土"}
#: 卦 → 三爻符号（自下而上）
GUA_YAO = {"乾": "☰", "兑": "☱", "离": "☲", "震": "☳",
           "巽": "☴", "坎": "☵", "艮": "☶", "坤": "☷"}
#: 卦 → 二进制爻（自下而上，1=阳 0=阴）
GUA_BITS = {"乾": (1, 1, 1), "兑": (1, 1, 0), "离": (1, 0, 1), "震": (1, 0, 0),
            "巽": (0, 1, 1), "坎": (0, 1, 0), "艮": (0, 0, 1), "坤": (0, 0, 0)}
#: 二进制爻 → 卦（反查）
BITS_GUA = {v: k for k, v in GUA_BITS.items()}

# 六十四卦名，索引 = 下卦索引×8 + 上卦索引；卦名形如「天泽履」
# = 上卦象(天) + 下卦象(泽) + 卦名本体(履)。来源：通行本《周易》六十四卦；
# 与 King Wen 序的逐卦对应核对见 tests/test_exhaustive.py。
GUA64 = (
    # 下乾
    "乾为天", "泽天夬", "火天大有", "雷天大壮", "风天小畜", "水天需", "山天大畜", "地天泰",
    # 下兑
    "天泽履", "兑为泽", "火泽睽", "雷泽归妹", "风泽中孚", "水泽节", "山泽损", "地泽临",
    # 下离
    "天火同人", "泽火革", "离为火", "雷火丰", "风火家人", "水火既济", "山火贲", "地火明夷",
    # 下震
    "天雷无妄", "泽雷随", "火雷噬嗑", "震为雷", "风雷益", "水雷屯", "山雷颐", "地雷复",
    # 下巽
    "天风姤", "泽风大过", "火风鼎", "雷风恒", "巽为风", "水风井", "山风蛊", "地风升",
    # 下坎
    "天水讼", "泽水困", "火水未济", "雷水解", "风水涣", "坎为水", "山水蒙", "地水师",
    # 下艮
    "天山遁", "泽山咸", "火山旅", "雷山小过", "风山渐", "水山蹇", "艮为山", "地山谦",
    # 下坤
    "天地否", "泽地萃", "火地晋", "雷地豫", "风地观", "水地比", "山地剥", "坤为地",
)


@dataclass
class MeiHuaResult:
    """梅花易数起卦结果。"""
    method: str              # 起卦方式描述
    upper: str               # 上卦
    lower: str               # 下卦
    moving_line: int         # 动爻（1-6，自下而上）
    ben_gua: str             # 本卦名
    hu_gua: str              # 互卦名
    bian_gua: str            # 变卦名
    ti_gua: str              # 体卦（静卦）
    yong_gua: str            # 用卦（动爻所在卦）
    relation: str            # 用→体 五行关系：生/克/比和/泄(体生用)/耗(体克用)
    verdict: str             # 简要吉凶断（体用生克通行断法）
    #: 互卦/变卦的上下卦（供图形化界面直接绘制卦符）
    hu_upper: str = ""
    hu_lower: str = ""
    bian_upper: str = ""
    bian_lower: str = ""

    def symbols(self) -> str:
        return f"{GUA_YAO[self.upper]}{GUA_YAO[self.lower]}"

    def __str__(self) -> str:  # pragma: no cover - 展示用
        return (
            f"{self.method}\n"
            f"  本卦 {self.ben_gua} {self.symbols()}  动爻第{self.moving_line}爻\n"
            f"  互卦 {self.hu_gua}   变卦 {self.bian_gua}\n"
            f"  体卦 {self.ti_gua}({GUA_WUXING[self.ti_gua]})  用卦 {self.yong_gua}"
            f"({GUA_WUXING[self.yong_gua]})  →  {self.relation}（{self.verdict}）"
        )


def _gua_name(lower_idx: int, upper_idx: int) -> str:
    return GUA64[lower_idx * 8 + upper_idx]


def _interact(use: str, ti: str) -> tuple[str, str]:
    """体用五行生克 → (关系名, 断语)。通行断法：用生体吉、体用比和吉、
    体克用小吉（费力）、体生用泄气、用克体凶。来源：《梅花易数》体用总诀。"""
    w = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}  # 我生
    u, t = GUA_WUXING[use], GUA_WUXING[ti]
    if u == t:
        return "比和", "体用比和，谋为可成（吉）"
    if w[u] == t:      # 用生体
        return "用生体", "用生体，得助之象（吉）"
    if w[t] == u:      # 体生用
        return "体生用", "体生用，泄气耗神，谋事费力（小凶）"
    if w[w[u]] == t:   # u 生 x 生 t ⟺ u 克 t → 用克体
        return "用克体", "用克体，事多阻逆（凶）"
    # 余下情形：t 克 u → 体克用
    return "体克用", "体克用，可成但费力（小吉）"


def _make(method: str, lower_idx: int, upper_idx: int, moving: int) -> MeiHuaResult:
    lower, upper = XIAN_TIAN[lower_idx], XIAN_TIAN[upper_idx]
    moving -= 1  # 转 0 基，自下而上
    bits = list(GUA_BITS[lower]) + list(GUA_BITS[upper])
    # 互卦：取本卦 2,3,4 爻为下互；3,4,5 爻为上互（动爻翻转前）
    hu_lower = BITS_GUA[tuple(bits[1:4])]
    hu_upper = BITS_GUA[tuple(bits[2:5])]
    # 动爻翻阴阳 → 变卦
    bits[moving] = 1 - bits[moving]
    bian_lower = BITS_GUA[tuple(bits[0:3])]
    bian_upper = BITS_GUA[tuple(bits[3:6])]
    # 体用：动爻在上卦 → 上为用、下为体；反之亦然
    if moving < 3:
        ti, yong = upper, lower
    else:
        ti, yong = lower, upper
    rel, verdict = _interact(yong, ti)
    return MeiHuaResult(
        method=method,
        upper=upper, lower=lower, moving_line=moving + 1,
        ben_gua=_gua_name(lower_idx, upper_idx),
        hu_gua=_gua_name(XIAN_TIAN.index(hu_lower), XIAN_TIAN.index(hu_upper)),
        bian_gua=_gua_name(XIAN_TIAN.index(bian_lower), XIAN_TIAN.index(bian_upper)),
        ti_gua=ti, yong_gua=yong,
        relation=rel, verdict=verdict,
        hu_upper=hu_upper, hu_lower=hu_lower,
        bian_upper=bian_upper, bian_lower=bian_lower,
    )


def by_time(lunar_year: int, lunar_month: int, lunar_day: int, hour: int) -> MeiHuaResult:
    """时间起卦（农历）：年、时用地支数（子1…亥12），月日用农历数。

    上卦 = (年+月+日)÷8 余数；下卦 = (年+月+日+时)÷8 余数；
    动爻 = (年+月+日+时)÷6 余数。余 0 取 8（卦）或 6（爻）。
    来源：《梅花易数》「年月日时起例」。
    """
    ny = (lunar_year - 4) % 12 + 1   # 年支数：甲子年=1984 → 子=1，…，亥=12
    # 时支数（标准时辰口径）：子时=23:00-00:59=1，丑=1-3点=2，…，亥=21-23点=12
    nh = ((hour + 1) // 2) % 12 + 1
    s = ny + lunar_month + lunar_day
    up = (s % 8) or 8
    down = ((s + nh) % 8) or 8
    mv = ((s + nh) % 6) or 6
    return _make(f"时间起卦（农历{lunar_year}年{lunar_month}月{lunar_day}日{hour}时）",
                 NUM_TO_IDX[down], NUM_TO_IDX[up], mv)


def by_numbers(a: int, b: int, c: int | None = None) -> MeiHuaResult:
    """数字起卦（通用）。

    - 两数：上卦 = a÷8，下卦 = b÷8，动爻 = (a+b)÷6；
    - 三数：上卦 = a÷8，下卦 = b÷8，动爻 = c÷6。
    余 0 取 8（卦）或 6（爻）。来源：《梅花易数》「物数占」。
    """
    up = (a % 8) or 8
    down = (b % 8) or 8
    mv = ((c if c is not None else a + b) % 6) or 6
    return _make(f"数字起卦（{a},{b}" + (f",{c}" if c is not None else "") + "）",
                 NUM_TO_IDX[down], NUM_TO_IDX[up], mv)
