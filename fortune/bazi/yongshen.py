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

#: 天干 → 五行（用于把《穷通宝鉴》喜用提炼 gan 映射为用神五行字段）
_GAN_WUXING = {"甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土", "己": "土",
               "庚": "金", "辛": "金", "壬": "水", "癸": "水"}


def _clip(text: str, limit: int, source: str) -> str:
    """按句读截断长引文（保持句子完整）并注明节选来源。"""
    if len(text) <= limit:
        return text
    head = text[:limit]
    cut = max(head.rfind("。"), head.rfind("；"), head.rfind("，"))
    if cut > limit // 2:
        head = head[:cut + 1]
    return f"{head}……（节选，全文见 {source}）"


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
    """调候（《穷通宝鉴》逐月原文）：按（日主, 月令）查逐字表，附喜用提炼与五行提示。

    用神五行字段由「喜用提炼」的天干映射而来（与所引原文一致）；
    原文无明确取用句的月份，退回月令寒暖简化规则并明确标注「非原文结论」。
    """
    from .tiaohou_text import TIAOHOU_TEXT, XTIQUAN

    mz = chart.pillar("月柱").zhi
    day = chart.day_master
    mo = "寅卯辰巳午未申酉戌亥子丑".index(mz) + 1
    text = TIAOHOU_TEXT.get(day, {}).get(mo, "")
    tiquan = XTIQUAN.get(day, {}).get(mo, {})
    y = YongshenResult(school="tiaohou（调候，《穷通宝鉴》逐月原文）")
    gan = tiquan.get("gan", "")
    quote = tiquan.get("quote", "")
    lines = [
        f"{_MONTH_CN[mo]}{day}日主（《穷通宝鉴》原文）："
        f"{_clip(text, 120, 'fortune/bazi/tiaohou_text.py')}",
    ]
    if gan:
        y.yong_wuxing = list(dict.fromkeys(_GAN_WUXING[g] for g in gan))
        lines.append(f"喜用提炼（规则抽取自原文，仅供参考）：{'、'.join(gan)}"
                     f"（用神五行：{'、'.join(y.yong_wuxing)}）"
                     + (f"（原文：「{_clip(quote, 60, 'fortune/bazi/tiaohou_text.py')}」）"
                        if quote else ""))
    else:
        # 原文无明确取用句：字段退回月令寒暖简化规则，并明确标注非原文结论
        y.yong_wuxing, wx_conclusions = _tiaohou_wuxing(mz)
        lines.append("喜用提炼：原文无明确取用句（以原文为准）")
        lines.append("（该月原文无明确取用句，以下为月令寒暖简化提示，非原文结论，仅供参考）")
        lines += wx_conclusions
    lines.append("出处：《穷通宝鉴》维基文库本（research/fetched/qiongbao.txt，程序化提取、繁转简）")
    if "噼" in text + quote:
        lines.append("校注：底本此处「噼」当为「劈」（同书七月丁火段作「劈」，"
                     "通行排印本作「劈」），本报告如实保留底本原字。")
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
    """格局（《子平真诠》原文+徐乐吾评注驱动）：羊刃/建禄/月劫三分支 + 六正格。

    比肩/劫财缺口修复（docs/修复与改进计划.md F2）：
    - 羊刃格：阳干月支为刃地（甲卯/丙午/戊午/庚酉/壬子），宜官杀制刃（论阳刃）；
    - 建禄格：月支为日主禄地，宜财官（论建禄月劫）；
    - 月劫格：月支藏干之比劫透天干（月支非禄/刃地），宜财官（与建禄同格）。
    """
    from .ziping_text import ZIPING

    y = YongshenResult(school="geju（格局，《子平真诠》原文+徐乐吾评注）")
    mz = chart.pillar("月柱").zhi
    day = chart.day_master
    day_wx = LunarUtil.WU_XING_GAN[day]
    cai = KE[day_wx]
    guan = next(w for w in WUXING_ORDER if KE[w] == day_wx)

    def _cite(chapter: str | None) -> None:
        if chapter and chapter in ZIPING:
            y.conclusions.append(
                f"《子平真诠》{chapter}（沈孝瞻原著、徐乐吾评注合刊本）："
                f"{_clip(ZIPING[chapter], 100, 'fortune/bazi/ziping_text.py')}")

    # 禄地与阳干刃地表（《子平真诠》论建禄月劫 / 论阳刃）
    _LU = {"甲": "寅", "乙": "卯", "丙": "巳", "丁": "午", "戊": "巳", "己": "午",
           "庚": "申", "辛": "酉", "壬": "亥", "癸": "子"}
    _REN = {"甲": "卯", "丙": "午", "戊": "午", "庚": "酉", "壬": "子"}

    # 1) 羊刃格（先判：阳干刃地与阴干禄地同支，如卯/午/酉/子）
    if mz == _REN.get(day):
        y.conclusions = [
            f"月令{mz}为日主{day}之羊刃，羊刃格（《子平真诠》论阳刃："
            "禄前一位为刃，刃宜伏制，官煞皆宜，财印相随，尤为贵显）",
            "格局喜忌：刃宜官杀制之；忌刃旺无制",
        ]
        y.yong_wuxing = [guan]
        _cite("论阳刃")
        return y

    # 2) 建禄格
    if mz == _LU.get(day):
        y.conclusions = [
            f"月令{mz}为日主{day}之禄地，建禄格（《子平真诠》：建禄与月劫可同一格，"
            "禄即是劫，皆以透干支，别取财官煞食为用）",
            "格局喜忌：宜财官（另取财官煞食用神）",
        ]
        y.yong_wuxing = [cai, guan]
        _cite("论建禄月劫")
        return y

    # 3) 透干取格：月支藏干中透出天干者
    hide = chart.pillar("月柱").hide_gan
    yue_gan = chart.pillar("月柱").gan
    shown = [g for g in chart.gans() if g in hide]      # 天干中透出的月支藏干（含月干）
    if yue_gan in hide:
        ge = yue_gan
    elif shown:
        ge = shown[0]
    else:
        ge = hide[0]
    shi = LunarUtil.SHI_SHEN[day + ge]  # 日主+定格干 → 十神

    # 4) 月劫格：定格之比劫透干（月支非禄/刃地）
    if shi in ("比肩", "劫财"):
        y.conclusions = [
            f"月令{mz}藏干{hide}，{ge}（{'、'.join(shown)}透）为日主{day}之{shi}，"
            "月劫格（《子平真诠》：建禄与月劫可同一格，皆以透干支，别取财官煞食为用）",
            "格局喜忌：宜财官（透财官煞食者别取为用）",
        ]
        y.yong_wuxing = [cai, guan]
        _cite("论建禄月劫")
        return y

    # 5) 六正格（正官/七杀/正财/偏财/正印/偏印/食神/伤官）
    _SHI_CHAPTER = {
        "正官": "论正官", "七杀": "论偏官", "偏官": "论偏官",
        "正财": "论财", "偏财": "论财",
        "正印": "论印绶", "偏印": "论印绶",
        "食神": "论食神", "伤官": "论伤官",
    }
    yin_wx = next(w for w in WUXING_ORDER if SHENG[w] == day_wx)  # 印
    shi_wx = SHENG[day_wx]                                        # 食伤
    rules = {
        "正官": ("喜财印相随", [cai, yin_wx]),
        "七杀": ("杀宜制化：食神制杀或印化", [shi_wx, yin_wx]),
        "正财": ("喜食伤生财、官星护财", [shi_wx, guan]),
        "偏财": ("喜食伤生财", [shi_wx]),
        "正印": ("印喜官杀生印、比劫帮身", [guan, day_wx]),
        "偏印": ("枭喜偏财制枭", [cai]),
        "食神": ("食喜比劫生食、财星流通", [day_wx, cai]),
        "伤官": ("伤官喜佩印或生财", [yin_wx, cai]),
    }
    tip, wx = rules.get(shi, ("按格局定喜忌（详见《子平真诠》）", []))
    y.conclusions = [
        f"月令{mz}藏干{hide}，定格之干取{ge}，日主{day}见之为「{shi}」格",
        f"格局喜忌：{tip}",
    ]
    y.yong_wuxing = wx
    _cite(_SHI_CHAPTER.get(shi))
    return y


def bingyao(chart: BaziChart, st: StrengthResult) -> YongshenResult:
    """病药（《神峰通考》病药说类）：依「从重者论」找病神、取克病之药神；
    附四病四药（雕枯旺弱/损益生长）与盖头说引文（维基文库本，与影印本互校），
    并按病神所属十神细分引用（RULE_QUOTES，双源互证）。"""
    from .shenfeng_text import RULE_QUOTES as SF_RULE
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
    # 雕枯旺弱逐十神细分：病神所属十神类的四病四药引句
    bing_lei = {guan: "官杀", cai: "财", yin: "印", bi: "日主", shi: "食伤"}[bing]
    rule_qs = SF_RULE.get(bing_lei, [])
    if rule_qs:
        parts = " ".join(f"「{q}」（{lab}）" for q, lab in rule_qs)
        y.conclusions.append(
            f"雕枯旺弱·{bing_lei}细分（《神峰通考》四病四药，双源互证）：{parts}")
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
