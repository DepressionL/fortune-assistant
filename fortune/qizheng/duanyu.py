"""七政四余排盘报告 —— 排盘事实 + 歌诀逐字引文，不做吉凶总断。"""
from __future__ import annotations

from . import GONG_CN, GONG_ZHU, HUA_YAO, QiZhengChart, _lon_to_gong, _lon_to_su
from .text import NOTES, QUOTES

XING_MING = {"日": "太阳", "月": "太阴", "水": "水星", "金": "金星",
             "火": "火星", "木": "木星", "土": "土星", "罗": "罗睺",
             "计": "计都", "孛": "月孛", "气": "紫气"}


def _gong_su(lon: float) -> dict:
    gong = _lon_to_gong(lon)
    su, su_du = _lon_to_su(lon)
    return {"gong": GONG_CN[gong][0], "gong_cn": GONG_CN[gong][1],
            "su": su, "su_du": su_du}


def format_chart(c: QiZhengChart, with_sources: bool = True) -> str:
    L: list[str] = []
    L.append("## 七政四余（果老星宗式排盘）")
    L.append("")
    L.append(f"- 出生时刻：{c.year}-{c.month:02d}-{c.day:02d} "
             f"{c.hour:02d}:{c.minute:02d}（北京时间），时支 {c.hour_zhi}")
    L.append(f"- 命宫：{c.ming_gong}宫（{GONG_CN[[i for i, (z, _) in GONG_CN.items() if z == c.ming_gong][0]][1]}），"
             f"命度：{c.ming_du}（《张果星宗》「以生时加太阳宫，顺数遇卯即是命宫」）")
    L.append("")

    L.append("| 星曜 | 黄经 | 入宫 | 入宿 |")
    L.append("| --- | --- | --- | --- |")
    order = ["日", "月", "水", "金", "火", "木", "土", "罗", "计", "孛", "气"]
    for x in order:
        v = c.stars[x]
        extra = f"（{v.get('preset', '')}）" if x == "气" else ""
        L.append(f"| {XING_MING.get(x, x)}（{x}） | {v['lon']:.4f}° | "
                 f"{v['gong']}宫{v['gong_cn']} | {v['su']}宿 {v['su_du']:g} 度{extra} |")
    L.append("")
    # 紫气多口径对照
    L.append("### 紫气多口径对照（虚拟星，多套速率×起算点同时计算）")
    L.append("")
    L.append("| 口径 | 速率（出处） | 起算点（出处） | 黄经 | 入宫 | 入宿 |")
    L.append("| --- | --- | --- | --- | --- | --- |")
    for r in c.ziqi_rows:
        g = _gong_su(r["lon"])
        mark = "（默认/最常用）" if r["key"] == c.ziqi_sel.get("key") else ""
        L.append(f"| {r['name']}{mark} | {r['rate_src']} | "
                 f"{r['epoch']} 黄经 {r['epoch_lon']:g}°（{r['epoch_src']}） | "
                 f"{r['lon']:.4f}° | {g['gong']}宫{g['gong_cn']} | "
                 f"{g['su']}宿 {g['su_du']:g} 度 |")
    L.append("")
    L.append("> 紫气无天文实体、古籍仅记平均行度而无统一起算锚点，故多口径并列展示；"
             "各口径的速率与起算点出处逐行标注（可追溯），默认口径为现代排盘软件"
             "最常用的「果老速率 + 1900 白羊初度」，可在 config/CLI 自定义"
             "（--ziqi-rate/--ziqi-epoch/--ziqi-epoch-lon）。")
    if c.hua_yao:
        yao = next(iter(c.hua_yao))
        L.append(f"- 化曜（日干{c.hua_yao[yao]}）：禄曜为{yao}"
                 f"（《星学大成》十干变曜「{QUOTES['化曜歌'][:24]}……」）。")
    L.append("- 宫主：" + "；".join(
        f"{z}宫（{GONG_CN[i][1]}）主{XING_MING.get(GONG_ZHU[z], GONG_ZHU[z])}"
        for z, i in sorted((z, i) for i, (z, _) in GONG_CN.items()))
        + "。")
    L.append("")

    L.append("### 口径与出处")
    L.append("")
    L.append(f"- {NOTES['宿度']}")
    L.append(f"- {NOTES['罗计']}（引文：「{QUOTES['罗计']}」）")
    L.append(f"- {NOTES['月孛']}")
    L.append(f"- {NOTES['紫气']}")
    L.append(f"- {NOTES['岁差']}")
    L.append("")
    L.append("> 本报告只陈述排盘事实（星躔宫宿、命宫命度、化曜宫主）；庙旺喜忌、"
             "星格与大小限断法为经验规则，需另按《果老星宗》《星学大成》参详，不做总断。")
    return "\n".join(L)


__all__ = ["format_chart"]
