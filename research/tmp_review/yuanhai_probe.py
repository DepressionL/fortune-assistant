# -*- coding: utf-8 -*-
"""临时核验脚本：检索《渊海子平》神煞关键词分布（不入库）。"""
import re

t = open(r"D:\ai工作区\fortune-assistant\research\fetched\yuanhai.txt",
         encoding="utf-8", errors="replace").read()
for kw in ("天乙", "驛馬", "驿马", "華蓋", "华盖", "咸池", "金輿", "金舆",
           "羊刃", "陽刃", "月德", "天德", "三奇", "太極", "太极"):
    hits = [m.start() for m in re.finditer(kw, t)]
    samples = [t[i:i + 36].replace("\n", " ") for i in hits[:2]]
    print(kw, len(hits), "处", samples)
