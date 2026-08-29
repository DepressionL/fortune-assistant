# -*- coding: utf-8 -*-
"""排查 epub 0 字问题（临时脚本）。"""
import glob
import os
import zipfile

bookdir = r"D:\ai工作区\fortune-assistant\research\Book"
for key in ("滴天髓", "子平真诠原本"):
    p = glob.glob(bookdir + f"\\{key}*.epub")[0]
    z = zipfile.ZipFile(p)
    print("=" * 20, os.path.basename(p)[:30], "=" * 20)
    for n in z.namelist():
        print(" ", n)
