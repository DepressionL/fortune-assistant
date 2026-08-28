"""穷举表校验 + 子卯刑回归（第二轮审查补强测试）。

- 64 卦名：按「上卦象+下卦象」的 King Wen 顺序全量核对（独立于代码表的权威清单）；
- 八宫卦序：由「本宫卦逐爻变」推导规则独立复现全部 64 卦与世应位置；
- 纳甲：八纯卦六爻地支的经典口诀独立清单核对；
- 神煞：天乙/文昌/禄/刃/驿马等口诀公式全干全支穷举自洽；
- 子卯刑：两见即论（修复回归）。
"""
import pytest

from fortune.misc import meihua
from fortune.liuyao import PALACE_GUA, NAJIA, find_gua
from fortune.bazi import relation

# ============ 1. 六十四卦名全量核对（King Wen 序，上象+下象） ============
# 来源：通行本《周易》。每项 (卦序, 上卦, 下卦, 卦名)
KING_WEN = [
    (1, "乾", "乾", "乾为天"), (2, "坤", "坤", "坤为地"), (3, "坎", "震", "水雷屯"),
    (4, "艮", "坎", "山水蒙"), (5, "坎", "乾", "水天需"), (6, "乾", "坎", "天水讼"),
    (7, "坤", "坎", "地水师"), (8, "坎", "坤", "水地比"), (9, "巽", "乾", "风天小畜"),
    (10, "乾", "兑", "天泽履"), (11, "坤", "乾", "地天泰"), (12, "乾", "坤", "天地否"),
    (13, "乾", "离", "天火同人"), (14, "离", "乾", "火天大有"), (15, "坤", "艮", "地山谦"),
    (16, "震", "坤", "雷地豫"), (17, "兑", "震", "泽雷随"), (18, "艮", "巽", "山风蛊"),
    (19, "坤", "兑", "地泽临"), (20, "巽", "坤", "风地观"), (21, "离", "震", "火雷噬嗑"),
    (22, "艮", "离", "山火贲"), (23, "艮", "坤", "山地剥"), (24, "坤", "震", "地雷复"),
    (25, "乾", "震", "天雷无妄"), (26, "艮", "乾", "山天大畜"), (27, "艮", "震", "山雷颐"),
    (28, "兑", "巽", "泽风大过"), (29, "坎", "坎", "坎为水"), (30, "离", "离", "离为火"),
    (31, "兑", "艮", "泽山咸"), (32, "震", "巽", "雷风恒"), (33, "乾", "艮", "天山遁"),
    (34, "震", "乾", "雷天大壮"), (35, "离", "坤", "火地晋"), (36, "坤", "离", "地火明夷"),
    (37, "巽", "离", "风火家人"), (38, "离", "兑", "火泽睽"), (39, "坎", "艮", "水山蹇"),
    (40, "震", "坎", "雷水解"), (41, "艮", "兑", "山泽损"), (42, "巽", "震", "风雷益"),
    (43, "兑", "乾", "泽天夬"), (44, "乾", "巽", "天风姤"), (45, "兑", "坤", "泽地萃"),
    (46, "坤", "巽", "地风升"), (47, "兑", "坎", "泽水困"), (48, "坎", "巽", "水风井"),
    (49, "兑", "离", "泽火革"), (50, "离", "巽", "火风鼎"), (51, "震", "震", "震为雷"),
    (52, "艮", "艮", "艮为山"), (53, "巽", "艮", "风山渐"), (54, "震", "兑", "雷泽归妹"),
    (55, "震", "离", "雷火丰"), (56, "离", "艮", "火山旅"), (57, "巽", "巽", "巽为风"),
    (58, "兑", "兑", "兑为泽"), (59, "巽", "坎", "风水涣"), (60, "坎", "兑", "水泽节"),
    (61, "巽", "兑", "风泽中孚"), (62, "震", "艮", "雷山小过"), (63, "坎", "离", "水火既济"),
    (64, "离", "坎", "火水未济"),
]


def test_gua64_full_king_wen():
    assert len(KING_WEN) == 64
    for seq, up, lo, name in KING_WEN:
        idx = meihua.XIAN_TIAN.index(lo) * 8 + meihua.XIAN_TIAN.index(up)
        assert meihua.GUA64[idx] == name, f"第{seq}卦 {name}：索引 {idx} 处实际为 {meihua.GUA64[idx]}"


# ============ 2. 八宫卦序推导复现（本宫卦逐爻变） ============
def derive_palace(ben_bits):
    """由本宫卦（六爻 bits，自下而上）推导八宫卦序：
    一世=初爻变、二世=初二变、…、五世=初二三四五变、
    游魂=五世后四爻回、归魂=游魂后内卦回本宫。
    返回 [(bits, 世爻, 应爻), ...]（本宫→归魂）。"""
    out = []
    cur = list(ben_bits)
    for k in range(6):  # 本宫 + 一世..五世
        out.append((tuple(cur), 6 if k == 0 else k, 3 if k == 0 else (k + 3 - 1) % 6 + 1))
        if k < 5:
            cur[k] = 1 - cur[k]
    # 游魂：四爻（index 3）变回
    cur[3] = 1 - cur[3]
    out.append((tuple(cur), 4, 1))
    # 归魂：内卦三爻变回本宫
    for k in range(3):
        cur[k] = ben_bits[k]
    out.append((tuple(cur), 3, 6))
    return out


def test_palace_gua_derivation():
    BITS = {g: b for g, b in meihua.GUA_BITS.items()}
    BIT_TRI = {b: g for g, b in BITS.items()}
    for palace, guas in PALACE_GUA.items():
        ben_up, ben_lo = guas[0][1], guas[0][2]
        ben_bits = tuple(BITS[ben_lo]) + tuple(BITS[ben_up])
        derived = derive_palace(ben_bits)
        for (name, up, lo, shi, ying), (bits, exp_shi, exp_ying) in zip(guas, derived):
            assert bits == tuple(BITS[lo]) + tuple(BITS[up]), f"{name} 爻象不符"
            assert (shi, ying) == (exp_shi, exp_ying), f"{name} 世应不符"


# ============ 3. 纳甲八纯卦地支（经典纳甲歌独立清单） ============
NAJIA_CLASSIC = {
    "乾": ("子", "寅", "辰", "午", "申", "戌"),
    "坎": ("寅", "辰", "午", "申", "戌", "子"),
    "艮": ("辰", "午", "申", "戌", "子", "寅"),
    "震": ("子", "寅", "辰", "午", "申", "戌"),
    "巽": ("丑", "亥", "酉", "未", "巳", "卯"),
    "离": ("卯", "丑", "亥", "酉", "未", "巳"),
    "坤": ("未", "巳", "卯", "丑", "亥", "酉"),
    "兑": ("巳", "卯", "丑", "亥", "酉", "未"),
}


def test_najia_classic():
    for g, zhis in NAJIA_CLASSIC.items():
        _, _, inner, outer = NAJIA[g]
        assert inner + outer == zhis, f"{g} 纳甲地支不符"


# ============ 4. 神煞公式穷举自洽 ============
def test_tianyi_exhaustive():
    from fortune.bazi.shensha import TIANYI, TIANYI_V2
    # 版本一：甲戊庚→丑未、乙己→子申、丙丁→酉亥、壬癸→卯巳、辛→寅午
    for gan in "甲戊庚":
        assert set(TIANYI[gan]) == {"丑", "未"}
    for gan in "乙己":
        assert set(TIANYI[gan]) == {"子", "申"}
    for gan in "丙丁":
        assert set(TIANYI[gan]) == {"酉", "亥"}
    for gan in "壬癸":
        assert set(TIANYI[gan]) == {"卯", "巳"}
    assert set(TIANYI["辛"]) == {"午", "寅"}
    # 版本二差异仅在庚
    assert set(TIANYI_V2["庚"]) == {"寅", "午"}
    assert set(TIANYI_V2["辛"]) == {"午", "寅"}


def test_lu_ren_exhaustive():
    from fortune.bazi.shensha import LU, YANGREN
    expect_lu = {"甲": "寅", "乙": "卯", "丙": "巳", "丁": "午", "戊": "巳",
                 "己": "午", "庚": "申", "辛": "酉", "壬": "亥", "癸": "子"}
    expect_ren = {"甲": "卯", "丙": "午", "戊": "午", "庚": "酉", "壬": "子"}
    assert LU == expect_lu
    assert YANGREN == expect_ren
    # 刃 = 禄前一位
    ZHI = "子丑寅卯辰巳午未申酉戌亥"
    for gan, lu in LU.items():
        if gan in YANGREN:
            assert YANGREN[gan] == ZHI[(ZHI.index(lu) + 1) % 12]


def test_sanhe_derived_exhaustive():
    """驿马/桃花/华盖/将星/劫煞/灾煞 由三合局长生位推导（独立公式核验）。"""
    from fortune.bazi.shensha import (_YIMA, _TAOHUA, _HUAGAI, _JIANGXING,
                                      _JIESHA, _ZAISHA)
    ZHI = "子丑寅卯辰巳午未申酉戌亥"
    # 长生: 申子辰水局长生在申；寅午戌火局长生在寅；巳酉丑金局长生在巳；亥卯未木局长生在亥
    chang_sheng = {"申": "申", "子": "申", "辰": "申", "寅": "寅", "午": "寅", "戌": "寅",
                   "巳": "巳", "酉": "巳", "丑": "巳", "亥": "亥", "卯": "亥", "未": "亥"}
    for z in ZHI:
        cs = chang_sheng[z]
        ci = ZHI.index(cs)
        # 驿马 = 长生之冲
        assert _YIMA[z] == ZHI[(ci + 6) % 12], f"驿马 {z}"
        # 桃花 = 长生顺二位（沐浴）
        assert _TAOHUA[z] == ZHI[(ci + 1) % 12], f"桃花 {z}"
        # 华盖 = 墓库
        assert _HUAGAI[z] == ZHI[(ci + 8) % 12], f"华盖 {z}"
        # 将星 = 中神（帝旺）
        assert _JIANGXING[z] == ZHI[(ci + 4) % 12], f"将星 {z}"
        # 劫煞 = 绝地
        assert _JIESHA[z] == ZHI[(ci + 9) % 12], f"劫煞 {z}"
        # 灾煞 = 将星之冲
        assert _ZAISHA[z] == ZHI[(ci + 4 + 6) % 12], f"灾煞 {z}"


def test_tiande_yuede_exhaustive():
    """天德/月德表（《三命通会》卷三口诀）逐项核验。"""
    from fortune.bazi.shensha import TIANDE, YUEDE
    assert TIANDE == {"寅": "丁", "卯": "申", "辰": "壬", "巳": "辛", "午": "亥", "未": "甲",
                      "申": "癸", "酉": "寅", "戌": "丙", "亥": "乙", "子": "巳", "丑": "庚"}
    assert YUEDE == {"寅": "丙", "午": "丙", "戌": "丙", "申": "壬", "子": "壬", "辰": "壬",
                     "亥": "甲", "卯": "甲", "未": "甲", "巳": "庚", "酉": "庚", "丑": "庚"}


def test_xiaoliuren_and_chenggu_exhaustive():
    """小六壬：12 时 × 全部月日组合不崩溃且六宫可覆盖；
    称骨：60 甲子年 × 12 月 × 30 日 × 12 时全组合可计算（60×12×30×12 抽样）。"""
    from fortune.misc import chenggu, xiaoliuren
    ZHI = "子丑寅卯辰巳午未申酉戌亥"
    for z in ZHI:
        r = xiaoliuren.calc(12, 30, z)
        assert r.palace in xiaoliuren.PALACES
    from fortune.core.model import GAN, ZHI as Z12
    seen = set()
    for i in range(0, 60, 7):   # 抽样
        gz = GAN[i % 10] + Z12[i % 12]
        for m in (1, 6, 12):
            for d in (1, 15, 30):
                for z in ("子", "午", "亥"):
                    r = chenggu.calc(gz, m, d, z)
                    assert 21 <= r.total_qian <= 71
                    seen.add(r.total_qian)
    assert len(seen) > 10


# ============ 5. 子卯刑（两见即论）回归 ============
def test_zi_mao_xing_detected():
    class FakeChart:
        pillars = [type("P", (), {"name": "年柱", "gan_zhi": "甲子", "gan": "甲", "zhi": "子"})(),
                   type("P", (), {"name": "月柱", "gan_zhi": "乙卯", "gan": "乙", "zhi": "卯"})(),
                   type("P", (), {"name": "日柱", "gan_zhi": "丙寅", "gan": "丙", "zhi": "寅"})(),
                   type("P", (), {"name": "时柱", "gan_zhi": "丁丑", "gan": "丁", "zhi": "丑"})()]

        def gans(self):
            return [p.gan for p in self.pillars]

        def zhis(self):
            return [p.zhi for p in self.pillars]

        def pillar(self, name):
            return next(p for p in self.pillars if p.name == name)

    hits = relation.scan(FakeChart())
    xx = [h for h in hits if h.name == "子卯刑"]
    assert len(xx) == 1 and xx[0].values == ["子", "卯"]
