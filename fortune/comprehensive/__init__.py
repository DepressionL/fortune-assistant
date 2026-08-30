"""fortune_comprehensive —— 无 LLM 的综合聚合工具。

定位（docs/修复与改进计划.md §4）：确定性聚合引擎 + 已核验内容检索。
- 无采样、无生成：同一输入字节级同一输出；
- 每条结论可回溯到（工具, 字段, 规则/词条, 出处）；
- 冲突结论并列呈现，不调和；只陈述「条件→证据」，不做断言式吉凶预测。

工具权重（默认，config.comprehensive_weights 可覆盖）：
bazi 0.35 / ziwei 0.25 / meihua 0.12 / xiaoliuren 0.10 / liuyao 0.10 / chenggu 0.08。
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field

from ..bazi import ditiansui as hz_mod
from ..bazi import shensha as shensha_mod
from ..bazi import strength as strength_mod
from ..bazi import yongshen as yongshen_mod
from ..bazi.chart import build as build_bazi
from ..bazi.liunian import compute as liunian_compute
from ..config import FortuneConfig
from ..core.calendar import NormalizedBirth, normalize
from ..core.model import BirthInfo
from ..misc import chenggu as chenggu_mod
from ..misc import meihua as meihua_mod
from ..misc import xiaoliuren as xlr_mod

SCHOOLS = ("wangshuai", "tiaohou", "tongguan", "geju", "bingyao")
#: 流派中文显示名（内部键保持拼音，报告与 UI 一律中文）
SCHOOLS_CN = {"wangshuai": "旺衰", "tiaohou": "调候", "tongguan": "通关",
              "geju": "格局", "bingyao": "病药"}
#: 证据链工具中文显示名（出处路径保留原样，仅徽章名中文化）
TOOLS_CN = {"bazi": "八字", "ziwei": "紫微", "liuyao": "六爻", "meihua": "梅花",
            "chenggu": "称骨", "xiaoliuren": "小六壬",
            "comprehensive": "综合分析", "context": "历法上下文"}
DEFAULT_WEIGHTS = {"bazi": 0.35, "ziwei": 0.25, "meihua": 0.12,
                   "xiaoliuren": 0.10, "liuyao": 0.10, "chenggu": 0.08}
WUXING = ("木", "火", "土", "金", "水")


@dataclass
class Evidence:
    tool: str
    field: str
    fact: str
    source: str = ""


@dataclass
class Conclusion:
    dim: str
    text: str
    evidence: list[Evidence] = field(default_factory=list)
    score: float = 0.0      # 共识度：证据权重 / 可参与工具权重（0-1）
    scores: dict | None = None   # 可选结构化数值（如旺衰五行得分，供图形渲染）


def _cn_field(field: str) -> str:
    """证据链字段名中的流派拼音 → 中文显示名。"""
    import re as _re
    return _re.sub("|".join(SCHOOLS), lambda m: SCHOOLS_CN.get(m.group(0), m.group(0)), field)


@dataclass
class ComprehensiveResult:
    context: dict
    matrix: dict                       # 流派 → 用神五行列表
    consensus: dict                    # 五行 → 加权票数（0-1 归一）
    conclusions: list[Conclusion]
    conflicts: list[str]
    notes: list[str] = field(default_factory=list)

    def markdown(self) -> str:
        L = ["# 综合分析报告（无 LLM 聚合，确定性规则引擎）", ""]
        L.append("> 本报告由确定性聚合生成：各工具独立计算后按固定权重汇总证据；"
                 "结论只陈述「条件→证据→出处」链，冲突并列呈现、不调和。"
                 "全部内容为传统命理文化参考，不构成任何现实决策建议。")
        L.append("")
        L.append("## 口径声明")
        L.append("")
        L.append("```")
        L += self.context.get("steps", [])
        L.append("```")
        L.append("")
        L.append("## 用神共识矩阵（流派 × 五行投票）")
        L.append("")
        rows = [["流派"] + list(WUXING) + ["结论"]]
        for s in SCHOOLS:
            yw = self.matrix.get(s)
            if yw is None:
                continue
            rows.append([SCHOOLS_CN.get(s, s)] + ["✓" if w in yw else "" for w in WUXING]
                        + ["、".join(yw)])
        L.append(_table(rows[0], rows[1:]))
        L.append("")
        L.append("五行加权得票：" + "；".join(
            f"{w} {self.consensus.get(w, 0.0):.2f}" for w in WUXING)
            + "（各流派等权/可配权重；调候用神取《穷通宝鉴》原文提炼映射）")
        L.append("")
        L.append("## 分维度结论（按共识度排序）")
        L.append("")
        for c in sorted(self.conclusions, key=lambda x: -x.score):
            band = "强" if c.score >= 0.6 else ("中" if c.score >= 0.3 else "弱")
            L.append(f"### {c.dim}（共识度 {c.score:.2f}，{band}共识）")
            L.append("")
            L.append(c.text)
            L.append("")
            if c.evidence:
                L.append("<details><summary>证据链（工具 → 字段 → 事实）</summary>")
                L.append("")
                L.append("\n".join(
                    f"- **{TOOLS_CN.get(e.tool, e.tool)}**｜{_cn_field(e.field)}｜{e.fact}"
                    + (f"｜出处：{e.source}" if e.source else "")
                    for e in c.evidence))
                L.append("</details>")
                L.append("")
        if self.conflicts:
            L.append("## 冲突清单（如实呈现，不调和）")
            L.append("")
            L += [f"- {x}" for x in self.conflicts]
            L.append("")
        L.append("> 未覆盖声明：本报告不输出任何生成式文本；未命中维度无结论。"
                 "各工具原始输出可用对应工具单独查看。")
        return "\n".join(L)


def _table(headers: list[str], rows: list[list[str]]) -> str:
    head = "| " + " | ".join(headers) + " |\n"
    sep = "| " + " | ".join("---" for _ in headers) + " |\n"
    body = "".join("| " + " | ".join(str(r) for r in row) + " |\n" for row in rows)
    return head + sep + body


def _weights(config: FortuneConfig) -> dict:
    w = dict(DEFAULT_WEIGHTS)
    for k, v in (config.comprehensive_weights or {}).items():
        if k in w:
            w[k] = float(v)
    return w


def run(birth: BirthInfo, config: FortuneConfig, *,
        liuyao: dict | None = None,
        anchor_year: int | None = None) -> ComprehensiveResult:
    """执行综合聚合。liuyao: {"backs":[…],"coin_back":"yang","date":"YYYY-MM-DD"}。"""
    import datetime as _dt

    nb: NormalizedBirth = normalize(birth, config)
    gender = birth.gender
    chart = build_bazi(nb, gender, config)
    st = strength_mod.compute(chart)
    weights = _weights(config)
    notes: list[str] = []

    # ---- 1) 用神共识矩阵 ----
    matrix: dict[str, list[str]] = {}
    votes = {w: 0.0 for w in WUXING}
    for s in SCHOOLS:
        try:
            ys = yongshen_mod.compute_yongshen(chart, s)
        except Exception:
            continue
        matrix[s] = ys.yong_wuxing
        for w in ys.yong_wuxing:
            votes[w] += weights.get("bazi", 0.35) / max(len(ys.yong_wuxing), 1)
    total = sum(votes.values()) or 1.0
    consensus = {w: votes[w] / total for w in WUXING}   # 全精度（展示时再格式化）
    top_wx = sorted(WUXING, key=lambda w: -consensus[w])
    conflicts: list[str] = []

    # ---- 2) 事实集 ----
    hits = hz_mod.hezhi(chart, st, config.hezhi_thresholds)
    hit_map = {h.key: h for h in hits}
    shensha = shensha_mod.compute(chart, config.shensha_base)
    shensha_hit = [h for h in shensha if h.positions]
    anchor = anchor_year or _dt.date.today().year
    ln = liunian_compute(chart, anchor)
    ln2 = liunian_compute(chart, anchor + 1)

    chenggu = chenggu_mod.calc_from_birth(birth, nb)
    meihua_r = meihua_mod.by_birth(birth, nb, use_true_solar=config.use_true_solar_time)
    xlr_r = xlr_mod.calc_from_birth(birth, nb, use_true_solar=config.use_true_solar_time)

    ziwei = None
    try:
        from ..ziwei import chart as ziwei_chart
        ziwei = ziwei_chart.build(nb, gender, config)
    except Exception as e:  # 引擎缺失等情况：如实跳过并注明
        notes.append(f"紫微模块不可用（{e}），相关维度证据空缺，共识度按可参与工具计算。")

    liuyao_chart = None
    liuyao_topic = None
    if liuyao:
        from ..liuyao import from_coins
        from ..liuyao import duanyu as ly_duanyu
        date = liuyao.get("date") or ""
        backs = liuyao.get("backs")
        coin_back = liuyao.get("coin_back", "yang")
        liuyao_topic = liuyao.get("topic", "综合")
        if date:
            dy, dm, dd = (int(x) for x in date.split("-"))
            b2 = BirthInfo(calendar="solar", year=dy, month=dm, day=dd, hour=12,
                           minute=0, gender=gender, longitude=120.0)
            nb2 = normalize(b2, FortuneConfig(use_true_solar_time=False))
            month_zhi = nb2.eight_char.getMonth()[-1]
            day_ganzhi = nb2.eight_char.getDay()
        else:
            month_zhi = liuyao.get("month_zhi", "子")
            day_ganzhi = liuyao.get("day_ganzhi", "甲子")
        liuyao_chart = from_coins(list(backs), month_zhi, day_ganzhi, coin_back)

    # ---- 3) 维度结论（证据链式，无自由文本） ----
    concl: list[Conclusion] = []

    # 用神共识
    ev = [Evidence("bazi", f"{s} 流派用神", "、".join(matrix[s]),
                   "fortune/bazi/yongshen.py") for s in matrix]
    concl.append(Conclusion(
        "用神共识",
        f"五行加权得票：{'；'.join(f'{w} {consensus[w]:.2f}' for w in top_wx)}。"
        f"多流派共识指向 {'、'.join(top_wx[:2])}（各流派逐条结论见证据链）。",
        ev, score=1.0))

    # 旺衰（附结构化五行得分，供图形渲染；不再用 dict 字符串展示）
    wx_max = max(st.scores, key=st.scores.get)
    wx_min = min(st.scores, key=st.scores.get)
    score_txt = " / ".join(f"{w} {st.scores[w]:.2f}" for w in WUXING)
    concl.append(Conclusion(
        "旺衰",
        f"日主{st.day_wx}{st.level}（同类 {st.same_score:.2f} / 异类 {st.diff_score:.2f}；"
        f"最旺 {wx_max} {st.scores[wx_max]:.2f}，最弱 {wx_min} {st.scores[wx_min]:.2f}）",
        [Evidence("bazi", "strength",
                  f"{score_txt}（月令旺相休囚死 × 藏干加权）",
                  "fortune/bazi/strength.py")],
        score=weights["bazi"] / weights["bazi"],
        scores={w: round(st.scores[w], 4) for w in WUXING}))

    # 财
    cai_hits = [hit_map[k] for k in ("富", "贫")]
    ev = [Evidence("bazi", "何知章·财维", h.reason, "《滴天髓》何知章规则映射")
          for h in cai_hits]
    ev.append(Evidence("chenggu", "判词",
                       f"{chenggu.total_str}——{chenggu.verdict or ''}",
                       "research/chenggu_table.md"))
    if liuyao_chart:
        shi = liuyao_chart.lines[liuyao_chart.shi - 1]
        ev.append(Evidence("liuyao", "世爻六亲", f"{shi.liu_qin}持世（{shi.gan_zhi}）",
                           "《卜筮正宗》诸爻持世诀"))
    concl.append(Conclusion("财", "见证据链（各工具财维事实并列，不做综合断言）。",
                            ev,
                            score=round((weights["bazi"] + weights["chenggu"]
                                         + (weights["liuyao"] if liuyao_chart else 0))
                                        / (weights["bazi"] + weights["chenggu"]
                                           + (weights["liuyao"] if liuyao else 0)), 4)))

    # 事业
    guan_hits = [hit_map[k] for k in ("贵", "贱")]
    ev = [Evidence("bazi", "何知章·官维", h.reason, "《滴天髓》何知章规则映射")
          for h in guan_hits]
    ev.append(Evidence("bazi", f"流年{anchor}{ln.gan_zhi}", f"流年干十神：{ln.shi_shen}；"
                       + ("；".join(ln.facts) or "与原局及大运无冲合刑害"),
                       "fortune/bazi/liunian.py"))
    if ziwei:
        g = next(p for p in ziwei.palaces if p.name == "官禄")
        ev.append(Evidence("ziwei", "官禄宫",
                           f"{g.gan_zhi} 主星 {'、'.join(g.star_list()) or '空宫'}（大限 {g.da_xian}）",
                           "x_iztro 引擎输出"))
    concl.append(Conclusion("事业", "见证据链（官杀状态/流年十神/官禄宫事实并列）。", ev,
                            score=round((weights["bazi"] + (weights["ziwei"] if ziwei else 0))
                                        / (weights["bazi"] + (weights["ziwei"] if ziwei else 0)), 4)))

    # 婚恋（男命以财为妻、女命以官为夫 —— 取用说明，见 research 口径）
    if gender == "男":
        ev = [Evidence("bazi", "妻星", hit_map["富"].reason, "财为妻（子平通行取用）")]
    else:
        ev = [Evidence("bazi", "夫星", hit_map["贵"].reason, "官为夫（子平通行取用）")]
    if ziwei:
        g = next(p for p in ziwei.palaces if p.name == "夫妻")
        ev.append(Evidence("ziwei", "夫妻宫",
                           f"{g.gan_zhi} 主星 {'、'.join(g.star_list()) or '空宫'}（大限 {g.da_xian}）",
                           "x_iztro 引擎输出"))
    concl.append(Conclusion("婚恋", "见证据链（妻/夫星状态与夫妻宫事实并列）。", ev,
                            score=round(weights["bazi"] / weights["bazi"], 4)))

    # 性格（仅盘面事实：日主/神煞/命宫主星）
    ev = [Evidence("bazi", "日主与旺衰", f"{st.day_wx}日主·{st.level}", "fortune/bazi/strength.py")]
    for h in shensha_hit[:6]:
        ev.append(Evidence("bazi", "神煞", str(h), "《三命通会》/《渊海子平》核验表"))
    if ziwei:
        ming = ziwei.palaces[ziwei.ming_index]
        ev.append(Evidence("ziwei", "命宫",
                           f"{ming.gan_zhi} 主星 {'、'.join(ming.star_list()) or '空宫'}（借对宫）",
                           "x_iztro 引擎输出"))
    concl.append(Conclusion("性格", "见证据链（日主/神煞/命宫盘面事实并列，无性格断言）。",
                            ev, score=1.0))

    # 健康
    ev = [Evidence("bazi", "五行强弱", f"最旺 {max(st.scores, key=st.scores.get)}、"
                   f"最弱 {min(st.scores, key=st.scores.get)}（五行偏枯之盘面事实，"
                   "对应脏腑属通行象意，本报告不展开）", "fortune/bazi/strength.py")]
    if ziwei:
        g = next(p for p in ziwei.palaces if p.name == "疾厄")
        ev.append(Evidence("ziwei", "疾厄宫",
                           f"{g.gan_zhi} 主星 {'、'.join(g.star_list()) or '空宫'}",
                           "x_iztro 引擎输出"))
    concl.append(Conclusion("健康", "见证据链（盘面五行强弱与疾厄宫事实并列）。", ev,
                            score=round(weights["bazi"] / weights["bazi"], 4)))

    # 近运（流年 + 梅花 + 小六壬 + 六爻）
    ev = [Evidence("bazi", f"流年{anchor}{ln.gan_zhi}", f"十神：{ln.shi_shen}；"
                   + ("；".join(ln.facts) or "与原局及大运无冲合刑害"), "fortune/bazi/liunian.py"),
          Evidence("bazi", f"流年{anchor + 1}{ln2.gan_zhi}", f"十神：{ln2.shi_shen}；"
                   + ("；".join(ln2.facts) or "与原局及大运无冲合刑害"), "fortune/bazi/liunian.py"),
          Evidence("meihua", "体用", f"{meihua_r.ben_gua} 动{meihua_r.moving_line}爻，"
                   f"体{meihua_r.ti_gua}用{meihua_r.yong_gua}：{meihua_r.relation}（{meihua_r.verdict}）",
                   "《梅花易数》体用总诀"),
          Evidence("xiaoliuren", "落宫", f"{xlr_r.path()} → {xlr_r.palace}（{xlr_r.info['吉凶']}）；"
                   f"断语：{xlr_r.info['断语']}", "research/xiaoliuren.md"),
          Evidence("meihua", "口径", meihua_r.caliber, ""),
          Evidence("xiaoliuren", "口径", xlr_r.caliber, "")]
    if liuyao_chart:
        ev.append(Evidence("liuyao", "世爻", f"{liuyao_chart.lines[liuyao_chart.shi - 1].liu_qin}持世",
                           "《卜筮正宗》"))
    score = round((weights["bazi"] + weights["meihua"] + weights["xiaoliuren"]
                   + (weights["liuyao"] if liuyao_chart else 0))
                  / (weights["bazi"] + weights["meihua"] + weights["xiaoliuren"]
                     + (weights["liuyao"] if liuyao else 0)), 4)
    concl.append(Conclusion("近运", "见证据链（流年关系事实/梅花体用/小六壬落宫并列）。",
                            ev, score=score))

    # ---- 4) 冲突清单 ----
    if hit_map["富"].matched and hit_map["贫"].matched:
        conflicts.append("何知章·财维：富、贫两条件同时命中（成对条件各自成立，"
                         "不代表综合吉凶，详见各条件依据）。")
    if hit_map["吉"].matched and hit_map["凶"].matched:
        conflicts.append("何知章·喜忌维：吉、凶两条件同时命中（成对条件各自成立）。")
    if matrix:
        agree = {s for s in matrix if any(w in matrix[s] for w in top_wx[:1])}
        if len(agree) < len(matrix):
            conflicts.append(
                f"用神流派分歧：{'、'.join(SCHOOLS_CN.get(s, s) for s in sorted(set(matrix) - agree))}"
                f" 的用神不含最高得票五行 {top_wx[0]}（各流派结论并列展示，不调和）。")
    if xlr_r.palace == "空亡" and meihua_r.relation in ("比和", "用生体"):
        conflicts.append("小六壬落空亡（凶）与梅花体用比和/用生体（吉）方向不一致"
                         "（两术独立计算，如实并列）。")

    return ComprehensiveResult(
        context=ctx_mod_build_context(birth, config),
        matrix=matrix,
        consensus=consensus,
        conclusions=concl,
        conflicts=conflicts,
        notes=notes,
    )


def ctx_mod_build_context(birth: BirthInfo, config: FortuneConfig) -> dict:
    from ..core import context as ctx_mod
    return ctx_mod.build(birth, config).asdict()


__all__ = ["run", "ComprehensiveResult", "Conclusion", "Evidence",
           "SCHOOLS", "DEFAULT_WEIGHTS"]
