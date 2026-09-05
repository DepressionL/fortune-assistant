# -*- coding: utf-8 -*-
"""从抓取页提取紫气行度/起算点相关内容。"""
import html
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
F = pathlib.Path(__file__).resolve().parents[1] / "research" / "fetched"

for tag in ("tmp_destiny_ziqi.html", "tmp_d5168_ziqi.html"):
    raw = (F / tag).read_text(encoding="utf-8", errors="replace")
    text = re.sub(r"<script.*?</script>", "", raw, flags=re.S)
    text = re.sub(r"<style.*?</style>", "", text, flags=re.S)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)
    print(f"\n===== {tag} =====")
    for kw in ["紫氣", "紫气", "起算", "1900", "行度", "一周天", "甲子"]:
        for m in re.finditer(kw, text):
            s = max(0, m.start() - 60)
            seg = text[s:m.start() + 90].strip()
            if any(x in seg for x in ("行度", "起", "度", "年")):
                print(" …" + seg + "…")
                break
