"""奇门遁甲排盘报告 —— 排盘事实 + 歌诀逐字引文，不做吉凶总断。"""
from __future__ import annotations

from . import (GONG_MEN, GONG_XING, JU_TABLE, NOTES, QimenChart, ZHI_GONG)
from .text import NOTES as TEXT_NOTES
from .text import QUOTES

GONG_MING = {1: "坎一", 2: "坤二", 3: "震三", 4: "巽四", 5: "中五",
             6: "乾六", 7: "兑七", 8: "艮八", 9: "离九"}


def format_chart(c: QimenChart, with_sources: bool = True) -> str:
    L: list[str] = []
    L.append("## 奇门遁甲（时家奇门排盘）")
    L.append("")
    L.append(f"- 用事时刻：{c.year}-{c.month:02d}-{c.day:02d} "
             f"{c.hour:02d}:{c.minute:02d}，日干支 {c.day_ganzhi}，时干支 {c.hour_ganzhi}")
    L.append(f"- 节气：{c.jie_qi}（{c.dun} {c.ju} 局，{c.yuan}）")
    L.append(f"- 值符：{c.zhi_fu_xing}（旬首 {c.xun_shou} 遁干落{gong_name(c.zhi_fu_gong)}）；"
             f"值使：{c.zhi_shi_men}")
    L.append("")

    L.append("| 宫 | 地盘 | 天盘星 | 八门 | 八神 |")
    L.append("| --- | --- | --- | --- | --- |")
    for g in range(1, 10):
        di = c.di_pan.get(g, "—")
        tian = c.tian_pan.get(g, "—")
        men = c.men_pan.get(g, "—")
        shen = c.shen_pan.get(g, "—")
        ji = "（中五寄坤二）" if g == 5 else ""
        L.append(f"| {gong_name(g)}{ji} | {di} | {tian} | {men} | {shen} |")
    L.append("")

    flags = []
    if c.fu_yin:
        flags.append("值符值使俱伏吟（星门归本宫，主迟滞闭塞，宜静守）")
    if c.fan_yin:
        flags.append("值符星落对宫（反吟之象）")
    if flags:
        L.append("- " + "；".join(flags) + "。")
    L.append("")

    L.append("### 口径与出处")
    L.append("")
    L.append(f"- {TEXT_NOTES['三元']}")
    L.append(f"- {TEXT_NOTES['中宫']}")
    L.append(f"- {TEXT_NOTES['值使']}")
    L.append(f"- {TEXT_NOTES['八神']}")
    L.append("- 局数依《奇门遁甲秘笈大全》阳遁/阴遁九宫起例歌："
            f"「{QUOTES['局数阳'][:24]}……」「{QUOTES['局数阴'][:24]}……」（逐字存档于"
            " research/fetched/奇门秘笈大全.txt）；《烟波钓叟歌》（维基文库本）："
            f"「{QUOTES['烟波布仪']}」。")
    L.append(f"- 布盘依《秘笈大全》「奇门掌中金要诀」：{QUOTES['布仪']}；"
             f"{QUOTES['符使'][:24]}……；九星「{QUOTES['九星']}」；"
             f"八门「{QUOTES['八门']}」；八神「{QUOTES['八神阳'][:30]}……」"
             f"「{QUOTES['八神阴']}」。")
    L.append("")
    L.append("> 本报告只陈述排盘事实（局、盘、符使、伏吟反吟），吉凶格与用事择方"
             "为经验规则，需另按《烟波钓叟歌》《秘笈大全》格局断法参详，不做总断。")
    return "\n".join(L)


def gong_name(g: int) -> str:
    return GONG_MING[g]


__all__ = ["format_chart"]
