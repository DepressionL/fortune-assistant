"""报告生成：Markdown 文本 + SVG 盘面。

所有解读类内容都在报告中标注「经验规则/流派相关」；
硬编码表的数据出处集中在各模块 docstring 与 research/*.md。
"""
from __future__ import annotations

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
                  birth: BirthInfo | None = None) -> str:
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

    # 用神
    ys = yongshen.compute_yongshen(chart, config.yongshen_school)
    lines.append("### 用神（规则引擎输出）")
    lines.append("")
    lines.append("```")
    lines.append(str(ys))
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def full_report(birth: BirthInfo, config: FortuneConfig,
                chart: BaziChart,
                extra_sections: dict[str, str] | None = None,
                misc_sections: dict[str, str] | None = None) -> str:
    """汇总报告。extra_sections: 紫微等追加小节（标题→markdown）。"""
    parts: list[str] = ["# 命盘报告", ""]
    parts.append("> 本报告由 fortune-assistant 生成。排盘数据由第三方历法/排盘库计算"
                 "（lunar_python 等，经交叉验证）；硬编码表经文献核验，出处见各小节与"
                 "research/ 目录；用神等解读为流派相关经验规则，仅供参考。")
    parts.append("")
    parts.append(bazi_markdown(chart, config, birth))
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
