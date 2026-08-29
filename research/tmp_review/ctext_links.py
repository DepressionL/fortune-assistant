# -*- coding: utf-8 -*-
"""临时脚本：解析 ctext 搜索结果页中的资源链接（不入库）。"""
import html
import re
import sys

raw = open(sys.argv[1], encoding="utf-8", errors="replace").read()
seen = set()
for m in re.finditer(r"href=\"([^\"]+)\"", raw):
    href = html.unescape(m.group(1))
    if ("wiki.pl" in href or ".pl?" in href) and href not in seen:
        seen.add(href)
        print(href)
