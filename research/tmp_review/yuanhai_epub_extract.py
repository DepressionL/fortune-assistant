# -*- coding: utf-8 -*-
"""临时脚本：抽取《渊海子平》足本 epub 全文 → UTF-8 文本（一次性归档，不入库）。"""
import glob
import html
import re
import zipfile

p = glob.glob(r"D:\ai工作区\fortune-assistant\research\Book\渊海子平*.epub")[0]
z = zipfile.ZipFile(p)
names = sorted([n for n in z.namelist() if "_split_" in n],
               key=lambda s: int(re.search(r"(\d+)", s).group(1)))
full = "".join(z.read(n).decode("utf-8", errors="ignore") for n in names)
full = html.unescape(re.sub(r"<[^>]+>", "", full))
out = r"D:\ai工作区\fortune-assistant\research\fetched\yuanhai_quanben.txt"
with open(out, "w", encoding="utf-8") as f:
    f.write(full)
print("已写", out, "字数", len(full))
