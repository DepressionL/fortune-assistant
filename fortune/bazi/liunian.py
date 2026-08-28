"""流年分析：流年干支与原局、大运的交互（确定性部分）。

- 流年干支：以立春为界（与八字年柱同口径）；
- 流年天干十神（对日主）；
- 流年与原局四柱、当前大运的 干合/支冲/支合/支害/子卯刑；
- 岁运并临（流年干支=大运干支）、天克地冲（流年干克大运干且支冲）。

说明：只输出确定性关系事实，不做吉凶断语（吉凶属经验规则）。
"""
from __future__ import annotations

from dataclasses import dataclass, field

from lunar_python import Solar
from lunar_python.util import LunarUtil

from .chart import BaziChart, PILLAR_NAMES

GAN_HE = {"甲": "己", "己": "甲", "乙": "庚", "庚": "乙", "丙": "辛", "辛": "丙",
          "丁": "壬", "壬": "丁", "戊": "癸", "癸": "戊"}
ZHI_CHONG = {"子": "午", "午": "子", "丑": "未", "未": "丑", "寅": "申", "申": "寅",
             "卯": "酉", "酉": "卯", "辰": "戌", "戌": "辰", "巳": "亥", "亥": "巳"}
ZHI_HE = {"子": "丑", "丑": "子", "寅": "亥", "亥": "寅", "卯": "戌", "戌": "卯",
          "辰": "酉", "酉": "辰", "巳": "申", "申": "巳", "午": "未", "未": "午"}
ZHI_HAI = {"子": "未", "未": "子", "丑": "午", "午": "丑", "寅": "巳", "巳": "寅",
           "卯": "辰", "辰": "卯", "申": "亥", "亥": "申", "酉": "戌", "戌": "酉"}


@dataclass
class LiuNianResult:
    year: int
    gan_zhi: str
    shi_shen: str                    # 流年天干十神（对日主）
    na_yin: str
    dayun: str | None                # 当前大运干支
    facts: list[str] = field(default_factory=list)   # 关系事实清单

    def __str__(self) -> str:  # pragma: no cover
        lines = [f"流年 {self.year}（{self.gan_zhi}，{self.shi_shen}，纳音{self.na_yin}）"]
        if self.dayun:
            lines.append(f"当前大运：{self.dayun}")
        if self.facts:
            lines += [f"  · {f}" for f in self.facts]
        else:
            lines.append("  · 与原局及大运无冲合刑害。")
        return "\n".join(lines)


def liunian_ganzhi(year: int) -> str:
    """流年干支（立春换年）。取年中日期避开立春边界。"""
    return Solar.fromYmd(year, 7, 1).getLunar().getYearInGanZhiByLiChun()


def compute(chart: BaziChart, year: int) -> LiuNianResult:
    gz = liunian_ganzhi(year)
    gan, zhi = gz[0], gz[1]
    day = chart.day_master
    shi_shen = LunarUtil.SHI_SHEN[day + gan]
    facts: list[str] = []

    # 当前大运
    dayun = None
    for d in chart.dayun:
        if d.start_year <= year <= d.end_year:
            dayun = d.gan_zhi
            break

    # 与原局关系
    for p in chart.pillars:
        if gan == GAN_HE.get(p.gan):
            facts.append(f"流年干{gan}与{p.name}干{p.gan}五合")
        if zhi == ZHI_CHONG.get(p.zhi):
            facts.append(f"流年支{zhi}冲{p.name}支{p.zhi}")
        elif zhi == ZHI_HE.get(p.zhi):
            facts.append(f"流年支{zhi}与{p.name}支{p.zhi}六合")
        elif zhi == ZHI_HAI.get(p.zhi):
            facts.append(f"流年支{zhi}害{p.name}支{p.zhi}")
        elif {zhi, p.zhi} == {"子", "卯"}:
            facts.append(f"流年支{zhi}与{p.name}支{p.zhi}子卯刑")

    # 与大运关系（岁运并临/天克地冲/干合支冲等）
    if dayun:
        dg, dz = dayun[0], dayun[1]
        if gz == dayun:
            facts.append(f"岁运并临：流年{gz}与大运{dayun}相同")
        if gan == GAN_HE.get(dg):
            facts.append(f"流年干{gan}与大运干{dg}五合")
        if zhi == ZHI_CHONG.get(dz):
            facts.append(f"流年支{zhi}冲大运支{dz}")
        elif zhi == ZHI_HE.get(dz):
            facts.append(f"流年支{zhi}与大运支{dz}六合")
        elif zhi == ZHI_HAI.get(dz):
            facts.append(f"流年支{zhi}害大运支{dz}")
        # 天克地冲：流年干克大运干 且 流年支冲大运支
        gan_ke = {"甲": "戊", "戊": "壬", "壬": "丙", "丙": "庚", "庚": "甲",
                  "乙": "己", "己": "癸", "癸": "丁", "丁": "辛", "辛": "乙"}
        if gan_ke.get(gan) == dg and zhi == ZHI_CHONG.get(dz):
            facts.append(f"天克地冲：流年{gz}与大运{dayun}")

    return LiuNianResult(
        year=year, gan_zhi=gz, shi_shen=shi_shen,
        na_yin=LunarUtil.NAYIN[gz],
        dayun=dayun, facts=facts,
    )
