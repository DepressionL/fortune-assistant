"""六爻规则化断语 —— 由确定性规则生成的「规则结论」，非自由解读。

每条断语均可回溯到通行规则，出处（已对照维基文库《增删卜易》原文核验，
见 research/liuyao_tables.md）：
- 六亲持世通论：通义取《增删卜易》身命诸章散文与《卜筮正宗》「诸爻持世诀」
  各传本一致处；**引文逐字摘自《卜筮正宗》**（research/fetched/bushizhengzong.txt，
  该本三处刊误「子身/井临/夬母」已如实保留并标注）；
- 动变生克（回头生/回头克/化泄/化出/化进神/化退神）：《增删卜易》卷三
  「进神退神章第二十九」、《卜筮正宗》「十八论」。进神 8 对（亥化子、丑化辰、
  寅化卯、辰化未、巳化午、未化戌、申化酉、戌化丑）为现代排印本通行表；
  维基文库本该章仅列 7 对（无「戌化丑」），属传本差异，此处采用通行 8 对；
- 月建/日辰对爻的生克冲合（月破、日破、六合绊住等）：《增删卜易》卷二
  「月建章」「日辰章」；
- 旬空（出空填实）：《增删卜易》卷二「旬空章」；
- 六神主事：《增删卜易》「六神章第十八」原文（青龙为吉、白虎主凶丧、
  「元武主盜賊，朱雀主口舌」）；勾陈田土、螣蛇虚惊等为通行象意归纳，
  各本措辞有出入，此处取共同核心。

争议标注：变爻六亲按「本宫五行」论（主流），另有按变卦卦宫论者
（见 research/liuyao_tables.md §6.3）。

断语只陈述规则结论（事实性判断），不做吉凶总断；一事一占的综合判断
仍须占者结合所问之事自断。全部内容为传统文化参考。
"""
from __future__ import annotations

from . import ZHI_WUXING, WUXING_SHENG, LiuYaoChart, PALACE_GUA
from ..misc.zhouyi import meaning as gua_meaning
from .shiba_lun_text import QUOTES as LUN_QUOTES

#: 十八论中取自識典古籍影印 OCR 的章（第 12–15 章），引用时附底本说明
_LUN_OCR_KEYS = {"伏吟卦定例第十二", "旺相休囚論第十三",
                 "合中帶剋論第十四", "合處逢冲，冲中逢合論第十五"}

#: 卦之反吟 = 卦变相冲（方位对冲：乾↔巽、坎↔离、艮↔坤、震↔兑），
#: 见《卜筮正宗》反吟卦定例第十一（非逐爻地支相冲——后者为爻之反吟）。
_CHONG_TRI = {"乾": "巽", "巽": "乾", "坎": "离", "离": "坎",
              "艮": "坤", "坤": "艮", "震": "兑", "兑": "震"}
_GUA_TRI = {name: (up, low)
            for rows in PALACE_GUA.values() for (name, up, low, _, _) in rows}

#: 六合（子丑合土、寅亥合木、卯戌合火、辰酉合金、巳申合水、午未合土）
LIU_HE = {"子": "丑", "丑": "子", "寅": "亥", "亥": "寅", "卯": "戌", "戌": "卯",
          "辰": "酉", "酉": "辰", "巳": "申", "申": "巳", "午": "未", "未": "午"}
#: 六冲（子午、丑未、寅申、卯酉、辰戌、巳亥）
LIU_CHONG = {"子": "午", "午": "子", "丑": "未", "未": "丑", "寅": "申", "申": "寅",
             "卯": "酉", "酉": "卯", "辰": "戌", "戌": "辰", "巳": "亥", "亥": "巳"}

#: 化进神 8 对（现代排印本通行表：《增删卜易》进神退神章——
#: 亥化子、丑化辰、寅化卯、辰化未、巳化午、未化戌、申化酉、戌化丑）；
#: 化退神即反之。维基文库本该章仅列 7 对（无戌化丑），传本差异，见模块注释。
JIN_SHEN = {("亥", "子"), ("丑", "辰"), ("寅", "卯"), ("辰", "未"),
            ("巳", "午"), ("未", "戌"), ("申", "酉"), ("戌", "丑")}

#: 六亲持世通论：通义（概括）+ 原文引文（逐字）。
#: 通义取《增删卜易》身命诸章散文与《卜筮正宗》「诸爻持世诀」各传本一致处；
#: 引文摘自《卜筮正宗》（research/fetched/bushizhengzong.txt，保持底本原字）。
#: 该本三处刊误已如实保留并标注：「子身持世」通行作「子孙持世」、
#: 「朱雀井临」当为「并临」、「夬母」当为「父母」。
SHI_CHI = {
    "子孙": ("子孙为福神，持世主无忧、灾祸易解、谋事安然；但子孙克官鬼，占官求名不利。",
             "「子身持世事无忧，求名切忌坐当头，避乱许安失可得，官讼从今了便休」"
             "（该本「子身」通行作「子孙」）"),
    "官鬼": ("官鬼为忧疑之神，持世主忧虑缠身、病讼多扰；占名望、官职、功名反利。",
             "「鬼爻持世事难安，占身不病也遭官，财物时时忧失脱，功名最喜世当权」"),
    "妻财": ("妻财持世，财利可求、妻贤财聚；但财克父母（文书），占名望考试不利。",
             "「财爻持世益财荣，兄若交重不可逢，更遇子孙明暗动，利身克父丧文风」"),
    "兄弟": ("兄弟为劫财之神，持世主破耗、同辈竞争，求财费力，合作合伙防损。",
             "「兄弟持世莫求财，官兴须虑祸将来，朱雀井临防口舌，如摇必定损妻财」"
             "（该本「井临」当为「并临」）"),
    "父母": ("父母持世主辛苦劳碌、文书操心；父母克子孙，占六畜、子嗣不利。",
             "「父母持世主身劳，求嗣妾众也难招，官动财旺宜赴试，财摇谋利莫心焦，占身财动无贤妇，又恐区区寿不高」"),
}

#: 六神主事（《卜筮正宗》六神章通行归纳，各本措辞有出入，取共同核心）
LIU_SHEN_SHI = {
    "青龙": "青龙主喜庆、酒色之事",
    "朱雀": "朱雀主口舌、文书、言语是非",
    "勾陈": "勾陈主田土、迟滞、牵连拖延",
    "螣蛇": "螣蛇主虚惊、怪异、缠绕不安",
    "白虎": "白虎主急病、伤灾、丧服凶事",
    "玄武": "玄武主暗昧、盗失、暧昧不明",
}


def _rel(a_zhi: str, b_zhi: str) -> str:
    """a 对 b 的五行关系：生（a 生 b）/克（a 克 b）/比和/泄（b 生 a）/耗（b 克 a）。"""
    wa, wb = ZHI_WUXING[a_zhi], ZHI_WUXING[b_zhi]
    if wa == wb:
        return "比和"
    if WUXING_SHENG[wa] == wb:
        return "生"
    if WUXING_SHENG[WUXING_SHENG[wa]] == wb:
        return "克"
    if WUXING_SHENG[wb] == wa:
        return "泄"
    return "耗"


def _bian_rel(ben_zhi: str, bian_zhi: str) -> str:
    """变爻对本爻：回头生/回头克/化泄/化出(本克变)/比和。"""
    wa, wb = ZHI_WUXING[ben_zhi], ZHI_WUXING[bian_zhi]
    if wa == wb:
        return "比和"
    if WUXING_SHENG[wb] == wa:
        return "回头生"
    if WUXING_SHENG[WUXING_SHENG[wb]] == wa:
        return "回头克"
    if WUXING_SHENG[wa] == wb:
        return "化泄"
    return "化出"


def _date_rel(date_zhi: str, line_zhi: str) -> list[str]:
    """月建/日辰对一爻的关系事实（生/克/比和/冲/合；泄耗不入断）。"""
    out = []
    if LIU_CHONG.get(date_zhi) == line_zhi:
        out.append("冲")
    if LIU_HE.get(date_zhi) == line_zhi:
        out.append("六合")
    r = _rel(date_zhi, line_zhi)
    if r == "生":
        out.append("生")
    elif r == "克":
        out.append("克")
    elif r == "比和":
        out.append("比和")
    return out


def _phrase(rels: list[str], date_zhi: str, line_zhi: str, who: str) -> str:
    parts = []
    for r in rels:
        if r == "生":
            parts.append(f"{who}生本爻（旺相得助）")
        elif r == "克":
            parts.append(f"{who}克本爻（休囚受制）")
        elif r == "比和":
            parts.append(f"{who}与本爻比和（当令得气）")
        elif r == "冲":
            parts.append(f"{who}冲本爻（{'月破' if who == '月建' else '日破' if who == '日辰' else '冲'}之象）")
        elif r == "六合":
            parts.append(f"{who}与本爻六合（合住/扶助之象）")
    return "；".join(parts)


def duanyu(chart: LiuYaoChart) -> str:
    """生成规则化断语（Markdown 多行文本）。"""
    L: list[str] = []
    L.append("### 断语（规则化生成，逐条可回溯；非自由解读）")
    L.append("")
    L.append("> 断语由确定性规则生成：六亲持世通论、动变生克、月建日辰生克冲合、"
             "旬空、六神主事（出处：《增删卜易》《卜筮正宗》，详见 fortune/liuyao/duanyu.py "
             "模块注释）。断语只陈述规则结论，不做吉凶总断；一事一占仍须结合所问之事自断。")
    L.append("")

    # 卦名释义
    mb = gua_meaning(chart.ben_gua)
    if mb:
        L.append(f"- 本卦「{chart.ben_gua}」：{mb}（卦名释义，通行传注概括，参考）")
    if chart.bian_gua != chart.ben_gua:
        mb2 = gua_meaning(chart.bian_gua)
        if mb2:
            L.append(f"- 变卦「{chart.bian_gua}」：{mb2}（卦名释义，通行传注概括，参考）")

    # 世应
    shi_line = chart.lines[chart.shi - 1]
    ying_line = chart.lines[chart.ying - 1]
    gloss, quotes = SHI_CHI[shi_line.liu_qin]
    L.append(f"- 世爻（第{chart.shi}爻，{shi_line.gan_zhi} {shi_line.liu_qin} {shi_line.liu_shen}）："
             f"{gloss}（《卜筮正宗》诸爻持世诀原文：{quotes}）")
    ying_kong = ying_line.gan_zhi[1] in chart.xun_kong
    L.append(f"- 应爻（第{chart.ying}爻，{ying_line.gan_zhi} {ying_line.liu_qin}）："
             f"所占之事、对方或目标之代表"
             + ("；应爻逢旬空，对方/目标尚未落实，待出空（填实）之日月方见分晓。" if ying_kong else "。"))

    # 旬空
    kong_lines = [ln for ln in chart.lines if ln.gan_zhi[1] in chart.xun_kong]
    if kong_lines:
        L.append("- 旬空 " + "".join(chart.xun_kong) + "："
                 + "、".join(f"第{ln.no}爻（{ln.gan_zhi} {ln.liu_qin}）" for ln in kong_lines)
                 + " 逢空（空亡之爻暂不主事，出空填实方应）。")

    # 动爻
    for ln in chart.lines:
        if not ln.is_moving:
            continue
        ben_zhi, bian_zhi = ln.gan_zhi[1], ln.bian_gan_zhi[1]
        head = (f"- 第{ln.no}爻 {ln.gan_zhi} {ln.liu_qin} {ln.liu_shen} 动，"
                f"化 {ln.bian_gan_zhi} {ln.bian_liu_qin}：")
        items = []
        rel = _bian_rel(ben_zhi, bian_zhi)
        if rel == "回头生":
            items.append("变爻生本爻（回头生），动而受益（吉象）。")
        elif rel == "回头克":
            items.append("变爻克本爻（回头克），动而受制，此爻所主之事难成（不利）。")
        elif rel == "化泄":
            items.append("本爻生变爻（化泄），动而耗气费力。")
        elif rel == "化出":
            items.append("本爻克变爻（化出），动而费力求成。")
        else:
            pair = (ben_zhi, bian_zhi)
            if pair in JIN_SHEN:
                items.append("化进神，动而渐强（吉象）。")
            elif (bian_zhi, ben_zhi) in JIN_SHEN:
                items.append("化退神，动而渐衰（不利）。")
            else:
                items.append("动化比和。")
        if ln.liu_qin != ln.bian_liu_qin:
            items.append(f"六亲由{ln.liu_qin}化{ln.bian_liu_qin}。")
        items.append(f"{ln.liu_shen}动：{LIU_SHEN_SHI[ln.liu_shen]}。")
        mr = _phrase(_date_rel(chart.month_zhi, ben_zhi), chart.month_zhi, ben_zhi, "月建")
        dr = _phrase(_date_rel(chart.day_ganzhi[1], ben_zhi), chart.day_ganzhi[1], ben_zhi, "日辰")
        if mr:
            items.append(f"月建{chart.month_zhi}：{mr}。")
        if dr:
            items.append(f"日辰{chart.day_ganzhi[1]}：{dr}。")
        if ben_zhi in chart.xun_kong:
            items.append("本爻又逢旬空，动而无力，出空方应。")
        L.append(head + "".join(items))

    if not any(ln.is_moving for ln in chart.lines):
        L.append("- 六爻安静无动变，主所问之事平稳，以世应旺衰与用神定吉凶（静卦断法）。")

    # 十八论触发性引注（《卜筮正宗》卷三）
    lun_hits: list[str] = []

    def _lun_quote(key: str, idx: int = 0, extra: str = "") -> str:
        note = ("（第 12–15 章底本为識典古籍影印 OCR，个别字或存噪声）"
                if key in _LUN_OCR_KEYS else "")
        return f"《卜筮正宗》十八论·{key}：「{LUN_QUOTES[key][idx]}」{note}{extra}"

    moving = [ln for ln in chart.lines if ln.is_moving]
    jin = any((ln.gan_zhi[1], ln.bian_gan_zhi[1]) in JIN_SHEN for ln in moving)
    tui = any((ln.bian_gan_zhi[1], ln.gan_zhi[1]) in JIN_SHEN for ln in moving)
    if jin:
        lun_hits.append(_lun_quote("变出进退神论第十七", 0))
    if tui:
        lun_hits.append(_lun_quote("变出进退神论第十七", 1))
    yue_po = [ln for ln in chart.lines
              if LIU_CHONG.get(chart.month_zhi) == ln.gan_zhi[1]]
    if yue_po:
        lun_hits.append(_lun_quote("月破论第九", 0,
                                   f"（月建{chart.month_zhi}冲"
                                   f"{'、'.join(ln.gan_zhi[1] for ln in yue_po)}为月破）"))
    if kong_lines:
        lun_hits.append(_lun_quote("旬空论第十", 0))
    # 卦变反吟/伏吟（反吟按卦之对冲方位，伏吟按六爻地支全同）
    btri = _GUA_TRI.get(chart.ben_gua)
    vtri = _GUA_TRI.get(chart.bian_gua)
    fan = bool(btri and vtri and chart.bian_gua != chart.ben_gua
               and _CHONG_TRI[btri[1]] == vtri[1] and _CHONG_TRI[btri[0]] == vtri[0])
    fu = all(ln.gan_zhi[1] == ln.bian_gan_zhi[1] for ln in chart.lines) \
        and chart.bian_gua != chart.ben_gua
    if fan:
        lun_hits.append(_lun_quote("反吟卦定例第十一", 0,
                                   f"（{chart.ben_gua}变{chart.bian_gua}，六爻相冲）"))
    if fu:
        lun_hits.append(_lun_quote("伏吟卦定例第十二", 0,
                                   f"（{chart.ben_gua}变{chart.bian_gua}，六爻地支伏吟）"))
    if lun_hits:
        L.append("")
        L.append("### 十八论引注（《卜筮正宗》卷三，触发性引用）")
        for h in lun_hits:
            L.append(f"- {h}")

    L.append("")
    L.append("> 口径提示：变爻六亲按本宫五行论（主流）；铜钱约定见上文。"
             "月建/日辰生克冲合为确定性关系事实，吉凶程度（旺相休囚）"
             "尚需结合爻之旺衰，此处仅列关系。"
             "十八论引注为触发性引用（旬空/月破/进退/反吟/伏吟），"
             "章文逐字存档见 fortune/liuyao/shiba_lun_text.py。")
    return "\n".join(L)


__all__ = ["duanyu"]
