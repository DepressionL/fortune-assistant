# -*- coding: utf-8 -*-
"""临时脚本：抽取《子平真诠》原本 epub → UTF-8 文本（一次性归档）。"""
import glob
import html
import re
import zipfile

p = glob.glob(r"D:\ai工作区\fortune-assistant\research\Book\子平真诠原本*.epub")[0]
z = zipfile.ZipFile(p)
names = [n for n in z.namelist() if n.lower().endswith((".htm", ".html", ".xhtml"))]
full = "".join(z.read(n).decode("utf-8", errors="ignore") for n in names)
full = html.unescape(re.sub(r"<[^>]+>", "", full))
out = r"D:\ai工作区\fortune-assistant\research\fetched\ziping_yuanben.txt"
with open(out, "w", encoding="utf-8") as f:
    f.write(full)
print("已写", out, "字数", len(full))
