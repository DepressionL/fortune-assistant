"""报告生成：Markdown 文本 + SVG 盘面。

所有解读类内容都在报告中标注「经验规则/流派相关」；
硬编码表的数据出处集中在各模块 docstring 与 research/*.md。
"""
from __future__ import annotations

from ..bazi import ditiansui as hz_mod
from ..bazi import liunian as ln_mod
from ..bazi import relation, shensha, strength, yongshen
from ..bazi.chart import BaziChart
from ..config import FortuneConfig
from ..core.model import BirthInfo

__all__ = ["bazi_markdown", "full_report"]


def _table(headers: list[str], rows: list[list[str]]) -> str:
    head = "| " + " | ".join(headers) + " |\n"
    sep = "| " + " | ".join("---" for _ in headers) + " |\n"
    body = "".join("| " + " | ".join(r) + " |\n" for r in rows)
    return head + sep + body


def bazi_markdown(chart: BaziChart, config: FortuneConfig,
                  birth: BirthInfo | None = None,
                  schools: list[str] | None = None) -> str:
    lines: list[str] = []
    lines.append("## 八字（子平法）")
    lines.append("")
    if birth is not None:
        lines.append(f"- 原始输入：{birth.solar_str() if birth.calendar == 'solar' else '农历'}，"
                     f"性别：{birth.gender}")
    lines.append("- 排盘时刻：" + chart.solar_used)
    for s in chart.steps:
        lines.append(f"  - {s}")
    lines.append("")

    rows = []
    for p in chart.pillars:
        hide = " ".join(f"{g}（{s}）" for g, s in zip(p.hide_gan, p.shi_shen_zhi))
        rows.append([p.name, p.gan_zhi, p.wu_xing, p.na_yin, p.shi_shen_gan, hide,
                     p.di_shi, p.xun_kong])
    lines.append(_table(["柱", "干支", "五行", "纳音", "天干十神", "藏干（十神）", "地势", "旬空"],
                        rows))
    lines.append(f"- 胎元 {chart.tai_yuan}　命宫 {chart.ming_gong}　身宫 {chart.shen_gong}")
    lines.append("")

    # 大运
    lines.append(f"### 大运（{'顺行' if chart.yun_forward else '逆行'}，"
                 f"起运 {chart.yun_start_solar}，虚岁 {chart.yun_start_age}）")
    lines.append("")
    lines.append(_table(["大运", "干支", "起止年份", "起止虚岁"],
                        [[str(d.index), d.gan_zhi, f"{d.start_year}–{d.end_year}",
                          f"{d.start_age}–{d.end_age}"] for d in chart.dayun]))
    lines.append("")

    # 五行统计
    wx = chart.wuxing_count
    total = sum(wx.values())
    bars = "　".join(f"{w}{'█' * wx[w]}" for w in ("木", "火", "土", "金", "水"))
    lines.append(f"### 五行统计（干支本气计数，共 {total}）")
    lines.append(f"```\n{bars}\n```")
    lines.append("")

    # 合冲刑害
    rels = relation.scan(chart)
    lines.append("### 合冲刑害")
    lines.append("")
    if rels:
        lines.append("\n".join(f"- {r}" for r in rels))
    else:
        lines.append("- 四柱间无明显合冲刑害。")
    lines.append("")

    # 神煞
    lines.append(f"### 神煞（以{config.shensha_base == 'day' and '日干/日支' or '年干/年支'}为基准查）")
    lines.append("")
    hits = shensha.compute(chart, config.shensha_base)
    for h in hits:
        if h.positions:
            lines.append(f"- {h}")
    nohit = [h for h in hits if not h.positions]
    if nohit:
        lines.append("- " + "；".join(h.name + "：" + (h.note or "原局不现") for h in nohit))
    lines.append("")

    # 旺衰
    st = strength.compute(chart)
    lines.append("### 五行旺衰（月令旺相休囚死 + 藏干加权，经验参数）")
    lines.append("")
    lines.append("```")
    lines.append(str(st))
    lines.append("```")
    lines.append("")
    if config.show_strength_detail:
        lines.append("<details><summary>旺衰计分明细（逐柱逐藏干得分，供人工复核；权重见 fortune/bazi/strength.py 模块注释）</summary>")
        lines.append("")
        lines.append("```")
        lines += list(st.detail)
        lines.append("```")
        lines.append("</details>")
        lines.append("")

    # 用神（单流派或多流派对比）
    school_list = schools or [config.yongshen_school]
    if len(school_list) == 1:
        ys = yongshen.compute_yongshen(chart, school_list[0])
        lines.append("### 用神（规则引擎输出）")
        lines.append("")
        lines.append("```")
        lines.append(str(ys))
        lines.append("```")
        lines.append("")
    else:
        lines.append("### 用神（多流派对比，规则引擎输出）")
        lines.append("")
        lines.append("> 各流派结论可能相互矛盾，均为经验规则，并列展示仅供对比参考。")
        lines.append("")
        for s in school_list:
            ys = yongshen.compute_yongshen(chart, s)
            text = str(ys)
            # 多流派时去掉每条结论自带的重复免责声明，统一在节末声明一次
            text = text.replace(f"  ⚠ {ys.caveat}\n", "")
            lines.append(f"**流派：{s}**")
            lines.append("")
            lines.append("```")
            lines.append(text)
            lines.append("```")
            lines.append("")
        lines.append("> ⚠ 用神推断为流派相关的经验规则，非确定性结论；不同流派结论可能相互矛盾，仅供参考研究。")
        lines.append("")

    # 何知章速览（《滴天髓》六亲论，规则映射；默认成对呈现，legacy 为旧逐句格式）
    hits = hz_mod.hezhi(chart, st, config.hezhi_thresholds)
    if config.hezhi_legacy:
        lines.append("### 何知章速览（《滴天髓》六亲论，规则映射）")
        lines.append("")
        lines.append("> 8 句原文逐字出自《滴天髓》何知章（本仓 epub 底本，与维基文库《滴天髓阐微》"
                     "互校；「财贫神反不真」两底本俱同，通行排印本多作「财神反不真」）。"
                     "规则映射为经验性简化（fortune/bazi/ditiansui.py），仅作速览参考。")
        lines.append("")
        matched = [h for h in hits if h.matched]
        for h in matched:
            lines.append(f"- 「{h.line}」——命中：{h.reason}")
        if not matched:
            lines.append("- 8 句无一命中（以规则映射为准，仅参考）。")
        lines.append("")
    else:
        lines.append("### 何知章条件核查（4 维成对呈现，非吉凶总断）")
        lines.append("")
        lines.append("> 8 句原文逐字出自《滴天髓》何知章（本仓 epub 底本，与维基文库《滴天髓阐微》"
                     "互校；「财贫神反不真」两底本俱同，通行排印本多作「财神反不真」）。"
                     "规则映射为经验性简化（fortune/bazi/ditiansui.py），仅作速览参考；"
                     "同维度两句为强弱两面，成对展示各自条件与依据，阈值见 research/hezhi_rules.md。")
        lines.append("")
        for pair in hz_mod.hezhi_pairs(hits):
            lines.append(f"**{pair['dim']}**")
            lines.append("")
            rows = [[f"{it['line']}（{'命中' if it['matched'] else '未命中'}）", it["reason"]]
                    for it in pair["items"]]
            lines.append(_table(["条件", "依据（得分/门槛）"], rows))
            lines.append("")

    # 何知章速览·大运流年（默认只报变化；legacy 输出全量表）
    lines.append("### 何知章·大运流年（规则映射，岁运干支并入原局计分）")
    lines.append("")
    lines.append("> 逐大运（及大运内逐年）把岁运干支并入原局、重算旺衰与 8 句命中"
                 "（同一规则引擎）；岁运十神按日主起算，计分沿用原局月令状态（经验简化）。"
                 "默认只列相对原局有变化者；全量数据见结构化输出。")
    lines.append("")
    dayun_rows, liunian_diffs = hz_mod.hezhi_suiyun(chart, st, config.hezhi_thresholds)
    if config.hezhi_legacy:
        lines.append(_table(["大运", "干支", "命中句", "相对原局"],
                            [[str(r["index"]), r["gan_zhi"],
                              "、".join(r["matched"]) or "—", r["delta"]]
                             for r in dayun_rows]))
        lines.append("")
    else:
        changed = [r for r in dayun_rows if r["delta"] != "同原局"]
        if changed:
            lines.append(_table(["大运", "干支", "命中句", "相对原局"],
                                [[str(r["index"]), r["gan_zhi"],
                                  "、".join(r["matched"]) or "—", r["delta"]]
                                 for r in changed]))
        else:
            lines.append("- 各步大运命中集与原局一致（无跨阈值变化）。")
        lines.append("")
    if liunian_diffs:
        lines.append(f"流年变例（相对该步大运新增命中，最多列 10 条，共 {len(liunian_diffs)} 条）：")
        for d in liunian_diffs[:10]:
            lines.append(f"- 第{d['dayun']}步大运内 {d['gan_zhi']}年（{d['year']}）："
                         f"新增{'、'.join(d['added'])}")
        if len(liunian_diffs) > 10:
            lines.append(f"- （其余 {len(liunian_diffs) - 10} 条从略）")
    else:
        lines.append("流年变例：各流年命中集均与该步大运相同。")
    lines.append("")

    # 大运流年速览（确定性关系事实，见 fortune/bazi/liunian.py）
    if config.liunian_years > 0:
        lines += liunian_section(chart, config)
    return "\n".join(lines)


def liunian_section(chart: BaziChart, config: FortuneConfig) -> list[str]:
    """大运流年速览：自锚年起 N 年，每年干支/十神/纳音 + 与原局、大运的确定性关系。

    锚年默认取排盘时刻当前年（与六爻占日同为时间敏感项）；测试可用
    config.liunian_anchor_year 固定锚年保证确定性。只输出关系事实，不断吉凶。
    """
    import datetime as _dt

    anchor = config.liunian_anchor_year or _dt.date.today().year
    rows = []
    for y in range(anchor, anchor + config.liunian_years):
        r = ln_mod.compute(chart, y)
        rows.append([str(r.year), r.gan_zhi, r.shi_shen, r.na_yin,
                     r.dayun or "—", "；".join(r.facts) or "—"])
    lines = [
        f"### 大运流年速览（自 {anchor} 年起 {config.liunian_years} 年；确定性关系事实，不断吉凶）",
        "",
    ]
    lines.append(_table(["年份", "干支", "流年干十神", "纳音", "所在大运", "与原局/大运关系"], rows))
    lines.append("")
    return lines


def full_report(birth: BirthInfo, config: FortuneConfig,
                chart: BaziChart,
                extra_sections: dict[str, str] | None = None,
                misc_sections: dict[str, str] | None = None,
                yongshen_schools: list[str] | None = None) -> str:
    """汇总报告。extra_sections: 紫微等追加小节（标题→markdown）。"""
    parts: list[str] = ["# 命盘报告", ""]
    parts.append("> 本报告由 fortune-assistant 生成。排盘数据由第三方历法/排盘库计算"
                 "（lunar_python 等，经交叉验证）；硬编码表经文献核验，出处见各小节与"
                 "research/ 目录；用神等解读为流派相关经验规则，仅供参考。")
    parts.append("")
    parts.append(bazi_markdown(chart, config, birth, schools=yongshen_schools))
    if extra_sections:
        for title, md in extra_sections.items():
            parts.append(f"## {title}")
            parts.append("")
            parts.append(md)
            parts.append("")
    if misc_sections:
        for title, md in misc_sections.items():
            parts.append(f"## {title}")
            parts.append("")
            parts.append(md)
            parts.append("")
    if config.show_sources:
        parts.append("## 附：主要文献与数据来源")
        parts.append("")
        parts.append("- 历法/八字主引擎：lunar-python（6tail，MIT），与 sxtwl 寿星天文历交叉验证，"
                     "见 research/bazi_golden_cases.md")
        parts.append("- 真太阳时：astral（太阳正午计算），EoT 与 NOAA/Meeus 对照，见 research/solar_time.md")
        parts.append("- 神煞表：《三命通会》《渊海子平》（维基文库）核验，见 research/shensha_tables.md")
        parts.append("- 紫微安星：《紫微斗数全书》+ iztro 系开源实现核验，见 research/ziwei_tables.md")
        parts.append("- 六爻：《增删卜易》《卜筮正宗》，见 research/liuyao_tables.md")
        parts.append("- 称骨/小六壬：通行本多源交叉核验，见 research/chenggu_table.md、research/xiaoliuren.md")
        parts.append("- 梅花易数：邵雍《梅花易数》通行本（64 卦名依通行《周易》）")
        parts.append("- 历法官方回归：香港天文台《公历与农历日期对照表》逐年逐日核对，见 tests/test_hko.py")
        parts.append("")
        parts.append("### 争议项与默认口径")
        parts.append("")
        parts.append("- 换日：默认 23:00 换日（传统主流；lunar_python sect=1）。部分现代软件用 0:00 换日（sect=2）。")
        parts.append("- 换年：八字以立春精确时刻为界（lunar_python），生肖/称骨以正月初一为界。")
        parts.append("- 起运：3 天折 1 年（lunar_python 内置）。")
        parts.append("- 天乙贵人：采用主流「甲戊庚牛羊」版；「庚辛逢虎马」别传未采。")
        parts.append("- 羊刃：主流阴干无刃。")
        parts.append("- 月德：取丙壬甲庚（《三命通会》小结「癸」为讹）。")
        parts.append("- 称骨：通行男命版；女命判词未收录。")
        parts.append("- 铜钱起卦：背=阳=3（主流），可在配置切换。")
        parts.append("")
    return "\n".join(parts)
