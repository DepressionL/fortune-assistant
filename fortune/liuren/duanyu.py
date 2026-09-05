"""大六壬规则化断语与报告 —— 由确定性规则生成，非自由解读。

断语只陈述排盘事实与《六壬大全》通论规则结论（课体、四课、三传、天将乘神
生克、旬空、年命行年），不做吉凶总断。引文逐字出自《六壬大全》四库本
（fortune/liuren/text.py，程序化提取、回归锁定）。
"""
from __future__ import annotations

from . import (CHONG, KE, SHENG, XING, YUE_JIANG, ZHI, ZHI_WUXING,
               LiuRenChart, liu_qin)
from .text import NOTES, QUOTES


def _shen_name(zhi: str) -> str:
    return f"{zhi}（{YUE_JIANG[zhi]}）"


def format_chart(c: LiuRenChart, with_sources: bool = True) -> str:
    """起课报告（Markdown）。"""
    L: list[str] = []
    L.append("## 大六壬（起课排盘）")
    L.append("")
    L.append(f"- 占时：{c.year}-{c.month:02d}-{c.day:02d} {c.hour:02d}:{c.minute:02d}，"
             f"日干支 {c.day_ganzhi}，时支 {c.hour_zhi}")
    L.append(f"- 月将：{c.yue_jiang_name}{c.yue_jiang_zhi}（{c.jie_qi}后日躔，"
             f"《六壬大全》卷二口径；{NOTES['月将寅']}）")
    L.append(f"- 昼夜：{c.day_night}占（{NOTES['贵人昼夜分界']}）")
    L.append("")

    # 天地盘
    rows = []
    for z in ZHI:
        rows.append([z, f"{c.tian_pan[z]}（{YUE_JIANG[c.tian_pan[z]]}）",
                     c.tian_jiang.get(z, ""), c.dun_gan.get(z, "")])
    L.append("| 地盘 | 天盘神 | 天将 | 遁干 |")
    L.append("| --- | --- | --- | --- |")
    for r in rows:
        L.append("| " + " | ".join(r) + " |")
    L.append("")

    # 四课
    L.append("### 四课")
    L.append("")
    L.append(f"- 第一课（干上神）：{_shen_name(c.gan_shang)}"
             f"（{liu_qin(c.day_ganzhi, c.gan_shang)}）")
    L.append(f"- 第二课：{_shen_name(c.gan_yin)}（{liu_qin(c.day_ganzhi, c.gan_yin)}）")
    L.append(f"- 第三课（支上神）：{_shen_name(c.zhi_shang)}"
             f"（{liu_qin(c.day_ganzhi, c.zhi_shang)}）")
    L.append(f"- 第四课：{_shen_name(c.zhi_yin)}（{liu_qin(c.day_ganzhi, c.zhi_yin)}）")
    L.append("")

    # 三传
    L.append(f"### 三传（{c.ke_ti}，{c.ke_ti_note}）")
    L.append("")
    chu, zhong, mo = c.san_chuan
    parts = []
    for i, (name, shen) in enumerate([("初传", chu), ("中传", zhong), ("末传", mo)]):
        jiang = c.tian_jiang.get(c.pan_tian.get(shen, ""), "")
        kong = "（旬空）" if shen in c.xun_kong else ""
        parts.append(f"{name}：{_shen_name(shen)}"
                     f"（{liu_qin(c.day_ganzhi, shen)}，天将{jiang}，"
                     f"遁干{c.dun_gan.get(c.pan_tian.get(shen, ''), '')}{kong}）")
    L.append("；".join(parts) + "。")
    # 三传结构提示
    rels = []
    for a, b in ((chu, zhong), (zhong, mo)):
        r = _shen_rel(a, b)
        if r:
            rels.append(r)
    if rels:
        L.append("- 三传结构：" + "；".join(rels) + "。")
    L.append("")

    # 贵人
    L.append("### 十二天将（贵人顺逆）")
    L.append("")
    L.append(f"- 天乙贵人：{c.day_ganzhi[0]}日{c.day_night}贵临"
             f"{_shen_name(c.gui_ren_zhi)}（地盘{c.pan_tian.get(c.gui_ren_zhi, '')}），"
             f"{'顺治' if c.gui_shun else '逆治'}布将"
             f"（《六壬大全》卷二：「{QUOTES['贵人顺逆']}」）。")
    L.append("")

    # 旬空
    L.append(f"- 旬首 {c.xun_shou}，旬空 " + "".join(c.xun_kong)
             + "；四课三传逢空者已标注（空亡不主事，出空填实方应）。")
    if c.ben_ming:
        L.append(f"- 本命 {c.ben_ming}（上神 {_shen_name(c.tian_pan[c.ben_ming])}"
                 f"，{liu_qin(c.day_ganzhi, c.tian_pan[c.ben_ming])}）；"
                 f"行年 {c.xing_nian}（上神 {_shen_name(c.tian_pan[c.xing_nian])}"
                 f"，{liu_qin(c.day_ganzhi, c.tian_pan[c.xing_nian])}）"
                 + ("（男顺女逆数至虚岁，通法）" if c.xing_nian else "") + "。")
    L.append("")

    if with_sources:
        L.append("### 起课歌诀出处（《六壬大全》四库本，逐字引文）")
        L.append("")
        L.append(f"- 十干寄宫：「{QUOTES['寄宫']}」")
        L.append(f"- 贼克法：「{QUOTES['贼克']}」")
        L.append(f"- 比用法：「{QUOTES['比用']}」")
        L.append(f"- 涉害法：「{QUOTES['涉害']}」")
        L.append(f"- 遥克法：「{QUOTES['遥克']}」")
        L.append(f"- 昴星法：「{QUOTES['昴星']}……刚日先辰而后日，柔日先日而后辰（论中末）」")
        L.append(f"- 别责法：「{QUOTES['别责']}」")
        L.append(f"- 八专法：「{QUOTES['八专']}……{QUOTES['八专2']}」")
        L.append(f"- 伏吟法：「{QUOTES['伏吟']}」")
        L.append(f"- 返吟法：「{QUOTES['返吟']}……（阳日用辰，阴日用日，辰上作中，日上作末）」")
        L.append(f"- 天将吉凶：「{QUOTES['天将吉凶']}」")
        L.append("")
        L.append("> 断语只陈述排盘事实与规则结论，不做吉凶总断；一事一占仍须结合所问之事自断。")
        L.append("")
    return "\n".join(L)


def _shen_rel(a: str, b: str) -> str:
    """三传相邻关系：生/克/比/合/冲/刑（三合）。"""
    wa, wb = ZHI_WUXING[a], ZHI_WUXING[b]
    out = []
    if SHENG[wa] == wb:
        out.append(f"{a}生{b}")
    if KE[wa] == wb:
        out.append(f"{a}克{b}")
    if wa == wb:
        out.append(f"{a}与{b}比和")
    if CHONG.get(a) == b:
        out.append(f"{a}冲{b}")
    if XING.get(a) == b:
        out.append(f"{a}刑{b}")
    he = {"子": "丑", "丑": "子", "寅": "亥", "亥": "寅", "卯": "戌", "戌": "卯",
          "辰": "酉", "酉": "辰", "巳": "申", "申": "巳", "午": "未", "未": "午"}
    if he.get(a) == b:
        out.append(f"{a}合{b}")
    return "、".join(out)


__all__ = ["format_chart", "liu_qin"]
