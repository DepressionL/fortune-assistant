"""用神/喜忌推断 —— 透明的规则引擎。

⚠️ 重要声明：用神没有确定性算法，属经验规则。本模块把各流派的核心规则
转成可审计的 if-then，输出「规则依据 + 结论」，并在每条结论上标注流派。
结论仅供研究参考。

支持的流派（config.yongshen_school）：
- wangshuai：旺衰平衡（身强克泄耗、身弱生扶），引《滴天髓》理气/衰旺/中和章；
- tiaohou：调候（寒暖燥湿），简化自《穷通宝鉴》纲领，引《滴天髓》寒暖/燥湿章；
- tongguan：通关（两强相战取中间五行），引《滴天髓》通关章；
- geju：格局（月令取格 + 格局喜忌），简化自《子平真诠》；
- bingyao：病药（《神峰通考》病药说类），附四病四药（雕枯旺弱/损益生长）
  与盖头说引文（维基文库本，与影印本文字层双源互校）。
引文均逐字出自 fortune/bazi/ditiansui_text.py、fortune/bazi/shenfeng_text.py
（程序化提取，回归测试锁定），底本异文如实标注。
"""
from __future__ import annotations

from dataclasses import dataclass, field

from lunar_python.util import LunarUtil

from .chart import BaziChart
from .strength import KE, SHENG, StrengthResult, WUXING_ORDER, compute

SHI_SHEN_WUXING = {  # 十神 → 五行含义（相对日主）
    "比肩": "same", "劫财": "same",
    "食神": "out", "伤官": "out",
    "正财": "ke_out", "偏财": "ke_out",
    "正官": "ke_in", "七杀": "ke_in",
    "正印": "in", "偏印": "in",
}


@dataclass
class YongshenResult:
    school: str
    conclusions: list[str] = field(default_factory=list)   # 结论条目
    yong_wuxing: list[str] = field(default_factory=list)   # 用神五行
    ji_wuxing: list[str] = field(default_factory=list)     # 忌神五行
    caveat: str = ("用神推断为流派相关的经验规则，非确定性结论；"
                   "不同流派结论可能相互矛盾，仅供参考研究。")

    def __str__(self) -> str:  # pragma: no cover
        lines = [f"用神（{self.school} 流派）"]
        lines += [f"  · {c}" for c in self.conclusions]
        if self.yong_wuxing:
            lines.append(f"  用神五行：{'、'.join(self.yong_wuxing)}")
        if self.ji_wuxing:
            lines.append(f"  忌神五行：{'、'.join(self.ji_wuxing)}")
        lines.append(f"  ⚠ {self.caveat}")
        return "\n".join(lines)


def wangshuai(chart: BaziChart, st: StrengthResult) -> YongshenResult:
    from .ditiansui_text import QUOTES as DT_QUOTES

    day_wx = st.day_wx
    yin = next(w for w in WUXING_ORDER if SHENG[w] == day_wx)   # 印（生日主）
    bi = day_wx                                                # 比劫（同日主）
    shi = SHENG[day_wx]                                        # 食伤（日主生）
    cai = KE[day_wx]                                           # 财（日主克）
    guan = next(w for w in WUXING_ORDER if KE[w] == day_wx)    # 官杀（克日主）
    y = YongshenResult(school="wangshuai（旺衰平衡）")
    if st.level == "身弱":
        y.yong_wuxing = [yin, bi]
        y.ji_wuxing = [shi, cai, guan]
        y.conclusions = [
            f"日主{day_wx}偏弱（同类 {st.same_score:.2f} < 异类 {st.diff_score:.2f}）",
            f"用神取生扶：印星（{yin}，生我）与比劫（{bi}，同我）",
            f"忌神：食伤（{shi}）、财（{cai}）、官杀（{guan}）",
        ]
    elif st.level == "身强":
        y.yong_wuxing = [guan, shi, cai]
        y.ji_wuxing = [yin, bi]
        y.conclusions = [
            f"日主{day_wx}偏强（同类 {st.same_score:.2f} > 异类 {st.diff_score:.2f}）",
            f"用神取克泄耗：官杀（{guan}）、食伤（{shi}）、财（{cai}）",
            f"忌神：印（{yin}）、比劫（{bi}）",
        ]
    else:
        y.conclusions = [
            f"日主{day_wx}中和（同类 {st.same_score:.2f} ≈ 异类 {st.diff_score:.2f}），"
            "旺衰法以中和为贵，用神随大运流年取平衡",
        ]
        y.yong_wuxing = [yin, bi, shi, cai, guan]
    y.conclusions.append(
        "《滴天髓》通神论（题宋·京图撰、明·刘基注；本仓 epub 底本，与维基文库"
        "《滴天髓阐微》互校）引：「" + DT_QUOTES["理气"] + "」"
        "「" + DT_QUOTES["衰旺"] + "」"
        "「" + DT_QUOTES["中和"] + "」——旺衰进退、抑扬取中之义")
    return y


_MONTH_CN = {1: "正月", 2: "二月", 3: "三月", 4: "四月", 5: "五月", 6: "六月",
             7: "七月", 8: "八月", 9: "九月", 10: "十月", 11: "十一月", 12: "十二月"}


def _tiaohou_wuxing(mz: str) -> tuple[list[str], list[str]]:
    """原简化规则：由月令寒暖燥湿给五行级调候提示（保留兼容）。"""
    cold, hot = ("亥", "子", "丑"), ("巳", "午", "未")
    dry, wet = ("戌", "未"), ("辰", "丑")
    if mz in cold:
        return ["火"], [f"月令{mz}冬寒，调候用神取火（丙丁/巳午），暖局为急",
                        "天干透丙丁、地支见巳午则调候有力"]
    if mz in hot:
        return ["水"], [f"月令{mz}夏燥，调候用神取水（壬癸/亥子），润局为急",
                        "天干透壬癸、地支见亥子则调候有力"]
    if mz in dry:
        return ["水"], [f"月令{mz}燥土当令，调候喜水（壬癸/亥子）润燥"]
    if mz in wet:
        return ["火"], [f"月令{mz}湿土当令，调候喜火（丙丁/巳午）暖湿"]
    if mz in ("寅", "卯"):
        return ["火"], [f"月令{mz}春木当令，木旺火相，调候喜火泄秀（简化规则）"]
    return ["水"], [f"月令{mz}秋金当令，调候喜水流通（简化规则）"]


def tiaohou(chart: BaziChart) -> YongshenResult:
    """调候（《穷通宝鉴》逐月原文）：按（日主, 月令）查逐字表，附喜用提炼与五行提示。"""
    from .tiaohou_text import TIAOHOU_TEXT, XTIQUAN

    mz = chart.pillar("月柱").zhi
    day = chart.day_master
    mo = "寅卯辰巳午未申酉戌亥子丑".index(mz) + 1
    text = TIAOHOU_TEXT.get(day, {}).get(mo, "")
    tiquan = XTIQUAN.get(day, {}).get(mo, {})
    y = YongshenResult(school="tiaohou（调候，《穷通宝鉴》逐月原文）")
    y.yong_wuxing, wx_conclusions = _tiaohou_wuxing(mz)
    lines = [
        f"{_MONTH_CN[mo]}{day}日主（《穷通宝鉴》原文）："
        f"{text[:120]}{'…' if len(text) > 120 else ''}",
    ]
    gan = tiquan.get("gan", "")
    quote = tiquan.get("quote", "")
    if gan:
        lines.append(f"喜用提炼（规则抽取自原文，仅供参考）：{'、'.join(gan)}"
                     + (f"（原文：「{quote[:60]}」）" if quote else ""))
    else:
        lines.append("喜用提炼：原文无明确取用句（以原文为准）")
    lines.append("出处：《穷通宝鉴》维基文库本（research/fetched/qiongbao.txt，程序化提取、繁转简）")
    lines += [f"调候五行提示（简化规则）：{c}" for c in wx_conclusions]
    from .ditiansui_text import QUOTES as DTQ
    lines.append(f"《滴天髓》寒暖/燥湿（调候总纲）：「{DTQ['寒暖']}」「{DTQ['燥湿']}」"
                 "（底本「品泯」通行排印本多作「品汇」）")
    y.conclusions = lines
    return y


def tongguan(chart: BaziChart, st: StrengthResult) -> YongshenResult:
    """通关：得分最高的相克两行之间取中间五行。"""
    y = YongshenResult(school="tongguan（通关）")
    ranked = sorted(st.scores, key=st.scores.get, reverse=True)
    found = False
    for i, a in enumerate(ranked):
        for b in ranked[i + 1:]:
            if st.scores[a] > 0.8 and st.scores[b] > 0.8 and (KE[a] == b or KE[b] == a):
                strong, weak = (a, b) if KE[a] == b else (b, a)
                x = SHENG[strong]  # strong 生 x 生 weak
                y.yong_wuxing = [x]
                y.conclusions = [
                    f"{strong}({st.scores[strong]:.2f}) 与 {weak}({st.scores[weak]:.2f}) 两强相战，"
                    f"取 {x} 通关（{strong}生{x}生{weak}）",
                ]
                found = True
                break
        if found:
            break
    if not found:
        y.conclusions = ["原局无明显两强相战，无需通关用神（通关法不适用时）"]
    else:
        from .ditiansui_text import QUOTES as DTQ
        y.conclusions.append(
            f"《滴天髓》通关：「{DTQ['通关']}」"
            "（本仓 epub 与维基文库阐微本俱作「相邀入洞户」，通行排印本或作「相将入洞房」）")
    return y


def geju(chart: BaziChart) -> YongshenResult:
    """格局（《子平真诠》原文+徐乐吾评注驱动）：月支本气/透干取格 + 格局喜忌 + 原文引文。"""
    from .ziping_text import ZIPING

    y = YongshenResult(school="geju（格局，《子平真诠》原文+徐乐吾评注）")
    mz = chart.pillar("月柱").zhi
    day = chart.day_master
    day_wx = LunarUtil.WU_XING_GAN[day]

    # 透干者定格：月支藏干中透出天干（年/月/时干）者
    hide = chart.pillar("月柱").hide_gan
    shown = [g for g in chart.gans() if g in hide and g != chart.pillar("月柱").gan or
             (g == chart.pillar("月柱").gan and g in hide)]
    # 简化：月支本气或透出的藏干
    ge = None
    for g in [chart.pillar("月柱").gan] + shown:
        if g in hide:
            ge = g
            break
    if ge is None:
        ge = hide[0]
    ge_wx = LunarUtil.WU_XING_GAN[ge]
    shi = LunarUtil.SHI_SHEN[day + ge]  # 日主+定格干 → 十神

    # 十神 → 《子平真诠》章名（合刊本；杂气/建禄另归）
    _SHI_CHAPTER = {
        "正官": "论正官", "七杀": "论偏官", "偏官": "论偏官",
        "正财": "论财", "偏财": "论财",
        "正印": "论印绶", "偏印": "论印绶",
        "食神": "论食神", "伤官": "论伤官",
        "比肩": "论建禄月劫", "劫财": "论建禄月劫",
    }

    if mz in ("寅", "申", "巳", "亥") and ge == chart.pillar("月柱").gan and ge_wx == day_wx:
        y.conclusions = [f"月令{mz}为日主禄地，建禄格（月刃格另论）；喜财官（《子平真诠》）"]
        y.yong_wuxing = [KE[day_wx], next(w for w in WUXING_ORDER if KE[w] == day_wx)]
        chapter = "论建禄月劫"
    else:
        rules = {
            "正官": ("喜财印相随", [KE[day_wx], next(w for w in WUXING_ORDER if SHENG[w] == day_wx)]),
            "七杀": ("杀宜制化：食神制杀或印化", [SHENG[day_wx], next(w for w in WUXING_ORDER if SHENG[w] == day_wx)]),
            "正财": ("喜食伤生财、官星护财", [SHENG[day_wx], next(w for w in WUXING_ORDER if KE[w] == day_wx)]),
            "偏财": ("喜食伤生财", [SHENG[day_wx]]),
            "正印": ("印喜官杀生印、比劫帮身", [next(w for w in WUXING_ORDER if KE[w] == day_wx), day_wx]),
            "偏印": ("枭喜偏财制枭", [KE[day_wx]]),
            "食神": ("食喜比劫生食、财星流通", [day_wx, KE[day_wx]]),
            "伤官": ("伤官喜佩印或生财", [next(w for w in WUXING_ORDER if SHENG[w] == day_wx), KE[day_wx]]),
        }
        tip, wx = rules.get(shi, ("按格局定喜忌（详见《子平真诠》）", []))
        y.conclusions = [
            f"月令{mz}藏干{hide}，定格之干取{ge}，日主{day}见之为「{shi}」格",
            f"格局喜忌：{tip}",
        ]
        y.yong_wuxing = wx
        chapter = _SHI_CHAPTER.get(shi)
    if chapter and chapter in ZIPING:
        text = ZIPING[chapter]
        y.conclusions.append(
            f"《子平真诠》{chapter}（沈孝瞻原著、徐乐吾评注合刊本）："
            f"{text[:100]}{'…' if len(text) > 100 else ''}")
    return y


def bingyao(chart: BaziChart, st: StrengthResult) -> YongshenResult:
    """病药（《神峰通考》病药说类）：依「从重者论」找病神、取克病之药神；
    附四病四药（雕枯旺弱/损益生长）与盖头说引文（维基文库本，与影印本互校）。"""
    from .shenfeng_text import SHENFENG_QUOTES as SFQ

    y = YongshenResult(school="bingyao（病药，《神峰通考》）")
    day_wx = st.day_wx
    yin = next(w for w in WUXING_ORDER if SHENG[w] == day_wx)   # 印
    bi = day_wx                                                # 比劫
    shi = SHENG[day_wx]                                        # 食伤
    cai = KE[day_wx]                                           # 财
    guan = next(w for w in WUXING_ORDER if KE[w] == day_wx)    # 官杀
    if st.level == "身强":
        bing = max([bi, yin], key=lambda w: st.scores.get(w, 0.0))
    elif st.level == "身弱":
        bing = max([guan, shi, cai], key=lambda w: st.scores.get(w, 0.0))
    else:
        y.conclusions = ["日主中和，无明显病神（病药法以「有病方为贵」立论，中和者另参旺衰）"]
        return y
    yao = next(w for w in WUXING_ORDER if KE[w] == bing)        # 克病之五行
    y.yong_wuxing = [yao]
    y.conclusions = [
        f"日主{day_wx}（{st.level}），依「从重者论」病神取{bing}"
        f"（最旺忌神，得分 {st.scores.get(bing, 0.0):.2f}）",
        f"药神取{yao}（克病之神）；「或本身病重而得药重，又宜行运」——喜行{yao}旺之运",
        "《神峰通考》病药说类原文：「" + SFQ["病药说类"][0] + "」"
        "「" + SFQ["病药说类"][1] + "」"
        "（维基文库本，与影印本文字层双源互校，见 fortune/bazi/shenfeng_text.py）",
        "《神峰通考》雕枯旺弱四病说类：「" + SFQ["雕枯旺弱四病说类"][0] + "…"
        + SFQ["雕枯旺弱四病说类"][1] + "」；损益生长四药说类：「"
        + SFQ["损益生长四药说类"][0] + "」「" + SFQ["损益生长四药说类"][1]
        + "」——病药说的四病四药扩展",
    ]
    # 盖头说：病神透干则「病」显于头面
    shown_wx = [LunarUtil.WU_XING_GAN[g] for g in chart.gans()]
    if bing in shown_wx:
        y.conclusions.append(
            f"病神{bing}透干（盖头）：《神峰通考》盖头说「"
            + SFQ["盖头说"][1] + "」——病显于天干，尤须药制")
    return y


def compute_yongshen(chart: BaziChart, school: str = "wangshuai") -> YongshenResult:
    """按流派计算用神。"""
    if school in ("wangshuai", "tongguan", "bingyao"):
        st = compute(chart)
        if school == "wangshuai":
            return wangshuai(chart, st)
        if school == "bingyao":
            return bingyao(chart, st)
        return tongguan(chart, st)
    if school == "tiaohou":
        return tiaohou(chart)
    if school == "geju":
        return geju(chart)
    raise ValueError(f"未知用神流派：{school}")
