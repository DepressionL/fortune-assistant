# -*- coding: utf-8 -*-
"""临时核验脚本：提取《穷通宝鉴》各日主逐月标记与首句（人工核对用，不入库）。"""
import re
import sys

path = r"D:\ai工作区\fortune-assistant\research\fetched\qiongbao.txt"
t = open(path, encoding="utf-8").read()

ELEM = {"甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
        "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水"}


def clean(s):
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"\{\{.*?\}\}", "", s)
    s = s.replace("-{", "").replace("}-", "")
    s = re.sub(r"^[*#\s]+", "", s)
    return s.strip()


stem = sys.argv[1] if len(sys.argv) > 1 else "丁"
elem = ELEM[stem]
pat = re.compile(r"'''((?:正|[一二三四五六七八九十]+)月" + stem + elem + r")'''")
for m in pat.finditer(t):
    nxt = t.find("'''", m.end())
    block = clean(t[m.end():nxt if nxt > 0 else m.end() + 200])
    print(f"【{m.group(1)}】{block[:110]}")
