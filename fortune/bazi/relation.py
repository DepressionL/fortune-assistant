"""八字合冲刑害关系扫描。

表来源：
- 天干五合、地支六合、六冲：lunar_python LunarUtil（HE_GAN_5/HE_ZHI_6/CHONG）同源通行表；
- 六害（子未、丑午、寅巳、卯辰、申亥、酉戌）、三刑（寅巳申、丑戌未、子卯）与
  自刑（辰午酉亥）：《三命通会》卷二〈论三刑〉〈论六害〉、《渊海子平》通行表。
  这两张表是全行业一致的稳定表（未在 research/ 专项核验，由 tests/test_relation.py
  的自洽性测试保证，见测试文件）。
- 三合（申子辰水/寅午戌火/巳酉丑金/亥卯未木）、三会（寅卯辰/巳午未/申酉戌/亥子丑）：
  《三命通会》卷二通行表。
"""
from __future__ import annotations

from dataclasses import dataclass

from .chart import BaziChart, PILLAR_NAMES

# 天干五合（甲己合土……）来源：LunarUtil.HE_GAN_5 同表
GAN_HE = {"甲": ("己", "土"), "己": ("甲", "土"), "乙": ("庚", "金"), "庚": ("乙", "金"),
          "丙": ("辛", "水"), "辛": ("丙", "水"), "丁": ("壬", "木"), "壬": ("丁", "木"),
          "戊": ("癸", "火"), "癸": ("戊", "火")}

# 地支六合（子丑合土……）来源：LunarUtil.HE_ZHI_6 同表
ZHI_HE = {"子": ("丑", "土"), "丑": ("子", "土"), "寅": ("亥", "木"), "亥": ("寅", "木"),
          "卯": ("戌", "火"), "戌": ("卯", "火"), "辰": ("酉", "金"), "酉": ("辰", "金"),
          "巳": ("申", "水"), "申": ("巳", "水"), "午": ("未", "土"), "未": ("午", "土")}

# 地支六冲 来源：LunarUtil.CHONG 同表
ZHI_CHONG = {"子": "午", "午": "子", "丑": "未", "未": "丑", "寅": "申", "申": "寅",
             "卯": "酉", "酉": "卯", "辰": "戌", "戌": "辰", "巳": "亥", "亥": "巳"}

# 地支六害 来源：《三命通会》卷二论六害（通行表）
ZHI_HAI = {"子": "未", "未": "子", "丑": "午", "午": "丑", "寅": "巳", "巳": "寅",
           "卯": "辰", "辰": "卯", "申": "亥", "亥": "申", "酉": "戌", "戌": "酉"}

# 三刑/自刑 来源：《三命通会》卷二论三刑（通行表）
XING_GROUPS = (("寅", "巳", "申"), ("丑", "戌", "未"), ("子", "卯"))
ZI_XING = ("辰", "午", "酉", "亥")

# 三合局
SAN_HE = {"申子辰": "水", "寅午戌": "火", "巳酉丑": "金", "亥卯未": "木"}
# 三会方
SAN_HUI = {"寅卯辰": "木", "巳午未": "火", "申酉戌": "金", "亥子丑": "水"}


@dataclass
class RelationHit:
    name: str              # 关系名（合/冲/害/刑/三合/三会）
    positions: list[str]   # 涉及的柱
    values: list[str]      # 涉及的干支/地支
    detail: str = ""

    def __str__(self) -> str:  # pragma: no cover
        pos = "、".join(f"{p}({v})" for p, v in zip(self.positions, self.values))
        return f"{self.name}：{pos}{'（' + self.detail + '）' if self.detail else ''}"


def scan(chart: BaziChart) -> list[RelationHit]:
    """扫描四柱（不含大运）内的合冲刑害。"""
    hits: list[RelationHit] = []
    gans = chart.gans()
    zhis = chart.zhis()

    # 天干五合
    seen = set()
    for i in range(4):
        for j in range(i + 1, 4):
            if gans[j] == GAN_HE[gans[i]][0] and (i, j) not in seen:
                seen.add((i, j))
                hits.append(RelationHit("天干五合", [PILLAR_NAMES[i], PILLAR_NAMES[j]],
                                        [gans[i], gans[j]],
                                        f"化{GAN_HE[gans[i]][1]}（是否化气成局另有条件，此处仅记合）"))

    # 地支两两关系
    for i in range(4):
        for j in range(i + 1, 4):
            a, b = zhis[i], zhis[j]
            if ZHI_CHONG[a] == b:
                hits.append(RelationHit("六冲", [PILLAR_NAMES[i], PILLAR_NAMES[j]], [a, b]))
            elif ZHI_HE[a][0] == b:
                hits.append(RelationHit("六合", [PILLAR_NAMES[i], PILLAR_NAMES[j]], [a, b],
                                        f"合{ZHI_HE[a][1]}"))
            elif ZHI_HAI[a] == b:
                hits.append(RelationHit("六害", [PILLAR_NAMES[i], PILLAR_NAMES[j]], [a, b]))
            # 子卯相刑（无礼之刑，两支即论，《三命通会》卷二论三刑）
            if {a, b} == {"子", "卯"}:
                hits.append(RelationHit("子卯刑", [PILLAR_NAMES[i], PILLAR_NAMES[j]], [a, b]))

    # 三支组合：三合/三会/三刑
    for combo in ((0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3)):
        trio = sorted(zhis[i] for i in combo)
        key = "".join(trio)
        found = False
        for k, wx in SAN_HE.items():
            if set(trio) == set(k):
                hits.append(RelationHit("三合局", [PILLAR_NAMES[i] for i in combo], trio,
                                        f"合{wx}局"))
                found = True
                break
        if found:
            continue
        for k, wx in SAN_HUI.items():
            if set(trio) == set(k):
                hits.append(RelationHit("三会方", [PILLAR_NAMES[i] for i in combo], trio,
                                        f"会{wx}方"))
                found = True
                break
        if found:
            continue
        for grp in XING_GROUPS:
            if set(trio) == set(grp):
                hits.append(RelationHit("三刑", [PILLAR_NAMES[i] for i in combo], trio))
                found = True
                break
        if found:
            continue
        if key in ("辰辰辰", "午午午", "酉酉酉", "亥亥亥"):
            hits.append(RelationHit("三自刑", [PILLAR_NAMES[i] for i in combo], trio))

    # 两见自刑（辰午酉亥 重复出现两次以上）
    from collections import Counter
    cnt = Counter(z for z in zhis if z in ZI_XING)
    for z, c in cnt.items():
        if c >= 2:
            pos = [PILLAR_NAMES[i] for i, zz in enumerate(zhis) if zz == z]
            hits.append(RelationHit("自刑", pos, [z] * len(pos)))

    return hits
