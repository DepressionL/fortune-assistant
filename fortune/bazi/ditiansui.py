"""何知章速览 —— 《滴天髓》六亲论「何知章」8 句的规则映射（经验性简化）。

8 句原文逐字出自 fortune/bazi/ditiansui_text.py（本仓《滴天髓原文（刘基注）》
epub 底本，与维基文库《滴天髓阐微》互校）。每条映射是一个可审计的 if-then：
以四柱透干/藏干十神与五行旺衰得分为事实输入，只陈述「命中与否 + 事实依据」，
不做吉凶总断。

⚠ 映射规则为经验性简化（「通门户/有理会/元神厚」等原注义理极简化为可计算
条件），仅作速览参考，不等于《滴天髓》原注断法。
"""
from __future__ import annotations

import dataclasses as _dc

from dataclasses import dataclass

from lunar_python.util import LunarUtil

from .chart import BaziChart, Pillar
from .ditiansui_text import HZ_LINES
from .strength import KE, SHENG, StrengthResult, WUXING_ORDER

CAI = ("正财", "偏财")
GUAN = ("正官", "七杀")
YIN = ("正印", "偏印")

#: 何知章 8 句典籍顺序（排序用）
HZ_ORDER = ["富", "贵", "贫", "贱", "吉", "凶", "寿", "夭"]


@dataclass
class HZHit:
    key: str        # 富/贵/贫/贱/吉/凶/寿/夭
    line: str       # 何知章原句（底本逐字）
    matched: bool   # 规则是否命中
    reason: str     # 事实依据（命中/未命中的具体说明）


def _tou_cang(chart: BaziChart):
    """透干与藏干十神事实。"""
    tou = [(p.name, p.gan, p.shi_shen_gan) for p in chart.pillars if p.name != "日柱"]
    cang = [(p.name, g, s) for p in chart.pillars
            for g, s in zip(p.hide_gan, p.shi_shen_zhi)]
    return tou, cang


def hezhi(chart: BaziChart, st: StrengthResult) -> list[HZHit]:
    """8 句逐条规则映射（HZ_LINES 顺序：富贵贫贱吉凶寿夭）。"""
    from . import yongshen as ys

    day_wx = st.day_wx
    yin_wx = next(w for w in WUXING_ORDER if SHENG[w] == day_wx)
    bi_wx = day_wx
    cai_wx = KE[day_wx]
    guan_wx = next(w for w in WUXING_ORDER if KE[w] == day_wx)

    tou, cang = _tou_cang(chart)
    cai_tou = [g for _, g, s in tou if s in CAI]
    cai_cang = [(p, g) for p, g, s in cang if s in CAI]
    guan_tou = [g for _, g, s in tou if s in GUAN]
    guan_cang = [(p, g) for p, g, s in cang if s in GUAN]
    tou_wx = [LunarUtil.WU_XING_GAN[g] for _, g, _ in tou]

    ws = ys.wangshuai(chart, st)
    yong_wx, ji_wx = ws.yong_wuxing, ws.ji_wuxing
    top = max(st.scores, key=st.scores.get)

    hits: list[HZHit] = []

    # 富：财气通门户 —— 财星透干，或月/日支（岁运并入时含大运/流年支）藏财
    menhu = ("月柱", "日柱", "大运", "流年")
    if cai_tou or any(p in menhu for p, _ in cai_cang):
        detail = f"财星{'、'.join(cai_tou) + '透干' if cai_tou else ''}" \
                 + (f"{'；' if cai_tou else ''}门户藏财"
                    f"{'、'.join(g for p, g in cai_cang if p in menhu)}"
                    if any(p in menhu for p, _ in cai_cang) else "")
        hits.append(HZHit("富", HZ_LINES[0], True, f"{detail}——财气通门户之象"))
    else:
        hits.append(HZHit("富", HZ_LINES[0], False,
                          f"财星未透干且月/日支不藏财（财{cai_wx}得分 {st.scores[cai_wx]:.2f}）——财气未通门户"))

    # 贵：官星有理会 —— 官杀透干或月支藏官，且官杀不弱
    guan_ok = bool(guan_tou) or any(p == "月柱" for p, _ in guan_cang)
    if guan_ok and st.scores[guan_wx] >= 0.3:
        hits.append(HZHit("贵", HZ_LINES[1], True,
                          f"官杀{guan_wx}透干/月令得气（得分 {st.scores[guan_wx]:.2f}）——官星有理会之象"))
    else:
        hits.append(HZHit("贵", HZ_LINES[1], False,
                          f"官杀未透干/月令不得气（得分 {st.scores[guan_wx]:.2f}）——官星未得理会"))

    # 贫：财神反不真 —— 财弱或被比劫夺（简化）
    if st.scores[cai_wx] < 0.5 or st.scores[bi_wx] >= st.scores[cai_wx]:
        hits.append(HZHit("贫", HZ_LINES[2], True,
                          f"财{cai_wx}得分 {st.scores[cai_wx]:.2f} 弱于比劫{bi_wx} "
                          f"{st.scores[bi_wx]:.2f}（或被劫夺）——财神不真之象"))
    else:
        hits.append(HZHit("贫", HZ_LINES[2], False,
                          f"财{cai_wx}得分 {st.scores[cai_wx]:.2f} 有气于比劫——财神尚真"))

    # 贱：官星还不见 —— 全局（透干+藏干）不见官杀
    if not guan_tou and not guan_cang:
        hits.append(HZHit("贱", HZ_LINES[3], True, "四柱透干与藏干俱不见官杀——官星不见之象"))
    else:
        hits.append(HZHit("贱", HZ_LINES[3], False, "原局见官杀（透干或藏干）——官星见"))

    # 吉：喜神为辅弼 —— 用神五行（旺衰派）有气
    yong_strong = [w for w in yong_wx if st.scores[w] >= 0.5]
    if yong_strong:
        hits.append(HZHit("吉", HZ_LINES[4], True,
                          f"用神{'、'.join(yong_strong)}得分 ≥0.5——喜神为辅弼之象"))
    else:
        hits.append(HZHit("吉", HZ_LINES[4], False,
                          f"用神{'、'.join(yong_wx)}俱弱（<0.5）——喜神不辅"))

    # 凶：忌神辗转攻 —— 忌神（旺衰派）为全局最旺且透干
    if top in ji_wx and st.scores[top] >= 1.5 and top in tou_wx:
        hits.append(HZHit("凶", HZ_LINES[5], True,
                          f"忌神{top}全局最旺（{st.scores[top]:.2f}）且透干——忌神辗转攻之象"))
    else:
        hits.append(HZHit("凶", HZ_LINES[5], False,
                          f"最旺之{top}非透干忌神或未达 1.5——忌神未成攻局"))

    # 寿：性定元神厚 —— 印星（元神）旺或身强（简化）
    if st.scores[yin_wx] >= 0.5 or st.level == "身强":
        hits.append(HZHit("寿", HZ_LINES[6], True,
                          f"印星{yin_wx}得分 {st.scores[yin_wx]:.2f}"
                          + ("（元神厚）" if st.scores[yin_wx] >= 0.5 else f"（{st.level}）")
                          + "——元神厚之象"))
    else:
        hits.append(HZHit("寿", HZ_LINES[6], False,
                          f"印星{yin_wx}得分 {st.scores[yin_wx]:.2f} 且{st.level}——元神不厚"))

    # 夭：气浊神枯了 —— 身弱且印比俱弱（简化）
    if st.level == "身弱" and st.scores[yin_wx] < 0.5 and st.scores[bi_wx] < 0.5:
        hits.append(HZHit("夭", HZ_LINES[7], True,
                          f"{st.level}且印{yin_wx}（{st.scores[yin_wx]:.2f}）比劫{bi_wx}"
                          f"（{st.scores[bi_wx]:.2f}）俱弱——气浊神枯之象"))
    else:
        hits.append(HZHit("夭", HZ_LINES[7], False, "身非极弱或印比有气——不属气浊神枯"))

    return hits


def _virtual_pillar(chart: BaziChart, name: str, ganzhi: str) -> Pillar:
    """把大运/流年干支构造为虚拟柱（十神按日主起算；旬空/纳音同排盘口径）。"""
    day = chart.day_master
    gan, zhi = ganzhi[0], ganzhi[1]
    hide = list(LunarUtil.ZHI_HIDE_GAN[zhi])
    xun = LunarUtil.getXun(ganzhi)
    return Pillar(
        name=name, gan_zhi=ganzhi, gan=gan, zhi=zhi,
        hide_gan=hide,
        shi_shen_gan="日主" if gan == day else LunarUtil.SHI_SHEN[day + gan],
        shi_shen_zhi=[LunarUtil.SHI_SHEN[day + g] if g != day else "日主"
                      for g in hide],
        na_yin=LunarUtil.NAYIN[ganzhi],
        wu_xing=LunarUtil.WU_XING_GAN[gan],
        di_shi="", xun=xun,
        xun_kong=LunarUtil.XUN_KONG[LunarUtil.XUN.index(xun)])


def _extend_chart(chart: BaziChart, extra_ganzhi: list[str]) -> BaziChart:
    """原局 + 岁运干支（1-2 个）合成排盘，供 strength/hezhi 重算。"""
    names = ["大运", "流年"][:len(extra_ganzhi)]
    extra = [_virtual_pillar(chart, n, gz) for n, gz in zip(names, extra_ganzhi)]
    return _dc.replace(chart, pillars=list(chart.pillars) + extra)


def hezhi_suiyun(chart: BaziChart, st: StrengthResult):
    """何知章速览接大运流年：逐大运（及大运内逐年）并入原局重算 8 句命中。

    返回 (dayun_rows, liunian_diffs)：
    - dayun_rows: [{"index","gan_zhi","matched":[…],"delta":…}]，delta 为相对原局变化；
    - liunian_diffs: [{"dayun","year","gan_zhi","added":[…],"matched":[…]}]
      （只列相对该步大运新增命中的流年）。
    """
    from lunar_python import LunarYear

    from .strength import compute as strength_compute

    base_keys = {h.key for h in hezhi(chart, st) if h.matched}
    dayun_rows: list[dict] = []
    per_dayun: dict[int, set] = {}
    for d in chart.dayun:
        ext = _extend_chart(chart, [d.gan_zhi])
        keys = {h.key for h in hezhi(ext, strength_compute(ext)) if h.matched}
        per_dayun[d.index] = keys
        added = sorted(keys - base_keys, key=HZ_ORDER.index)
        removed = sorted(base_keys - keys, key=HZ_ORDER.index)
        delta = ""
        if added or removed:
            delta = ("新增" + "、".join(added) if added else "")
            if removed:
                delta += ("；消失" if delta else "消失") + "、".join(removed)
        dayun_rows.append({"index": d.index, "gan_zhi": d.gan_zhi,
                           "matched": sorted(keys, key=HZ_ORDER.index),
                           "delta": delta or "同原局"})

    liunian_diffs: list[dict] = []
    for d in chart.dayun:
        base = per_dayun[d.index]
        for y in range(d.start_year, d.end_year + 1):
            gz = LunarYear.fromYear(y).getGanZhi()
            if gz == d.gan_zhi:      # 流年干支同大运，无新增信息
                continue
            ext2 = _extend_chart(chart, [d.gan_zhi, gz])
            keys = {h.key for h in hezhi(ext2, strength_compute(ext2)) if h.matched}
            added = sorted(keys - base, key=HZ_ORDER.index)
            if added:
                liunian_diffs.append({"dayun": d.index, "year": y, "gan_zhi": gz,
                                      "added": added,
                                      "matched": sorted(keys, key=HZ_ORDER.index)})
    return dayun_rows, liunian_diffs


__all__ = ["HZHit", "hezhi", "hezhi_suiyun"]
