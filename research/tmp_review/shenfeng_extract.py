# -*- coding: utf-8 -*-
"""临时脚本：抽取《神峰通考》PDF 全文 → UTF-8 文本（一次性归档）。"""
import glob

from pypdf import PdfReader

p = glob.glob(r"D:\ai工作区\fortune-assistant\research\Book\神峰通考*.pdf")[0]
r = PdfReader(p)
parts = [pg.extract_text() or "" for pg in r.pages]
full = "\n".join(parts)
out = r"D:\ai工作区\fortune-assistant\research\fetched\shenfeng.txt"
with open(out, "w", encoding="utf-8") as f:
    f.write(full)
print("已写", out, "字数", len(full), "页数", len(r.pages))
