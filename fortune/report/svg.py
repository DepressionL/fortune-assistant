"""SVG 盘面：紫微十二宫盘、八字五行条。

紫微盘输入为通用结构，与具体排盘引擎解耦：
    palaces: 12 个宫，自命宫起逆时针排列，每项
        {"name": 宫名, "gan_zhi": 宫干支, "stars": [星曜...],
         "sihua": {星: "禄|权|科|忌"}, "da_xian": "2-11", "shen_gong": bool}
"""
from __future__ import annotations

import html

BR = ("子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥")


def ziwei_palace_svg(palaces: list[dict], title: str = "紫微斗数命盘",
                     note: str = "") -> str:
    """生成紫微十二宫盘 SVG（自命宫起逆时针排列，命宫在下方位置）。"""
    assert len(palaces) == 12
    cx, cy = 300, 300
    r_out, r_mid, r_in = 210, 150, 90

    def point(i: int, r: float) -> tuple[float, float]:
        # 第 i 宫中心角度：命宫(i=0)放正下方，逆时针
        import math
        ang = math.radians(270 - i * 30)
        return cx + r * math.cos(ang), cy - r * math.sin(ang)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {cx * 2} {cy * 2}">',
        '<defs><style>text{font-family:"Microsoft YaHei",sans-serif}'
        '.t{font-size:18px;fill:#1a1a1a}.s{font-size:12px;fill:#333}'
        '.h4{font-size:13px;fill:#b30000;font-weight:bold}'
        '.ds{font-size:13px;fill:#0d47a1}'
        '.x{stroke:#999;fill:none;stroke-width:1.2}'
        '.tk{font-size:13px;fill:#4a148c}</style></defs>',
        f'<rect width="{cx * 2}" height="{cy * 2}" fill="#fdfcf7"/>',
        f'<text x="{cx}" y="28" text-anchor="middle" class="t" font-size="20">{html.escape(title)}</text>',
        f'<circle cx="{cx}" cy="{cy}" r="{r_out}" class="x"/>',
        f'<circle cx="{cx}" cy="{cy}" r="{r_mid}" class="x"/>',
        f'<circle cx="{cx}" cy="{cy}" r="{r_in}" class="x"/>',
    ]
    for i in range(12):
        import math
        a1 = math.radians(270 - i * 30 + 15)
        a2 = math.radians(270 - i * 30 - 15)
        parts.append(f'<line x1="{cx + r_in * math.cos(a1):.1f}" y1="{cy - r_in * math.sin(a1):.1f}" '
                     f'x2="{cx + r_out * math.cos(a1):.1f}" y2="{cy - r_out * math.sin(a1):.1f}" class="x"/>')
        parts.append(f'<line x1="{cx + r_in * math.cos(a2):.1f}" y1="{cy - r_in * math.sin(a2):.1f}" '
                     f'x2="{cx + r_out * math.cos(a2):.1f}" y2="{cy - r_out * math.sin(a2):.1f}" class="x"/>')

    for i, p in enumerate(palaces):
        mx, my = point(i, (r_in + r_mid) / 2)
        # 宫名 + 干支
        gz = p.get("gan_zhi", "")
        name = p["name"]
        tag = "命宫" if i == 0 else ""
        if p.get("shen_gong"):
            tag = "身宫" if not tag else "命身"
        label = name + (f"({tag})" if tag else "")
        parts.append(f'<text x="{mx:.1f}" y="{my - 14:.1f}" text-anchor="middle" class="t">{html.escape(label)}</text>')
        parts.append(f'<text x="{mx:.1f}" y="{my + 2:.1f}" text-anchor="middle" class="tk">{html.escape(gz)}</text>')
        if p.get("da_xian"):
            parts.append(f'<text x="{mx:.1f}" y="{my + 17:.1f}" text-anchor="middle" class="ds">'
                         f'{html.escape(p["da_xian"])}</text>')
        # 星曜（外环）
        sx, sy = point(i, (r_mid + r_out) / 2)
        stars = []
        for s in p.get("stars", []):
            h4 = p.get("sihua", {}).get(s)
            if h4:
                stars.append(f'<tspan class="h4">{html.escape(s)}·{html.escape(h4)}</tspan>')
            else:
                stars.append(f'<tspan class="s">{html.escape(s)}</tspan>')
        if stars:
            parts.append(f'<text x="{sx:.1f}" y="{sy - 10:.1f}" text-anchor="middle">'
                         + "　".join(stars) + "</text>")
        # 十二长生（可选，内环）
        if p.get("chang_sheng"):
            ix, iy = point(i, (r_in + 0) / 2 + 18)
            parts.append(f'<text x="{ix:.1f}" y="{iy:.1f}" text-anchor="middle" class="s">'
                         f'{html.escape(p["chang_sheng"])}</text>')
    if note:
        parts.append(f'<text x="{cx}" y="{cy * 2 - 12}" text-anchor="middle" '
                     f'font-size="11" fill="#666">{html.escape(note)}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def wuxing_bar_svg(scores: dict[str, float], title: str = "五行分布") -> str:
    """五行得分条形图。"""
    w = 420
    h = 220
    order = ("木", "火", "土", "金", "水")
    colors = {"木": "#2e7d32", "火": "#c62828", "土": "#8d6e63",
              "金": "#b8860b", "水": "#1565c0"}
    mx = max(scores.values()) or 1.0
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}">',
        f'<rect width="{w}" height="{h}" fill="#fdfcf7"/>',
        f'<text x="{w / 2}" y="22" text-anchor="middle" font-size="15" fill="#1a1a1a">'
        f'<tspan>{html.escape(title)}</tspan></text>',
    ]
    for k, wx in enumerate(order):
        v = scores.get(wx, 0.0)
        bw = 46
        bx = 40 + k * 80
        bh = 120 * v / mx
        by = 150 - bh
        parts.append(f'<rect x="{bx}" y="{by:.1f}" width="{bw}" height="{bh:.1f}" '
                     f'fill="{colors[wx]}" rx="3"/>')
        parts.append(f'<text x="{bx + bw / 2}" y="170" text-anchor="middle" font-size="14">'
                     f'{wx} {v:.2f}</text>')
    parts.append("</svg>")
    return "\n".join(parts)
