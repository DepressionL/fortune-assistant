# -*- coding: utf-8 -*-
"""检查 research/Book 各书籍格式与程序化可用性（临时脚本）。"""
import glob
import html
import os
import re
import zipfile

from pypdf import PdfReader

bookdir = r"D:\ai工作区\fortune-assistant\research\Book"
for p in sorted(glob.glob(bookdir + r"\*")):
    name = os.path.basename(p)
    size = os.path.getsize(p)
    ext = os.path.splitext(p)[1].lower()
    info = f"{name[:46]:<48} {size // 1024:>6}KB"
    try:
        if ext == ".txt":
            raw = open(p, "rb").read()
            for enc in ("utf-8", "gb18030"):
                try:
                    t = raw.decode(enc)
                    info += f" | {enc} {len(t)}字 开头:{t.strip()[:22]}"
                    break
                except Exception:
                    continue
        elif ext == ".epub":
            z = zipfile.ZipFile(p)
            htmls = [n for n in z.namelist() if n.lower().endswith((".htm", ".xhtml"))]
            t = "".join(z.read(n).decode("utf-8", errors="ignore") for n in htmls)
            t = html.unescape(re.sub(r"<[^>]+>", "", t))
            info += f" | epub {len(t)}字 开头:{t.strip()[:22]}"
        elif ext == ".pdf":
            r = PdfReader(p)
            txt = (r.pages[0].extract_text() or "").strip()
            info += f" | pdf {len(r.pages)}页 文本层:{'有' if txt else '无(图片版)'}"
    except Exception as e:  # noqa: BLE001
        info += f" | 解析失败 {e}"
    print(info)
