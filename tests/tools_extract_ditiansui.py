#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""从 research/Book《滴天髓原文（刘基注）》epub 抽取全文文本，存档为
research/fetched/ditiansui_liuji.txt（纯标准库 zipfile+html 解析，无第三方依赖）。
仅存档与探测用；后续引用模块由专门的生成脚本产出。"""
import html
import pathlib
import re
import sys
import zipfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

ROOT = pathlib.Path(__file__).resolve().parents[1]
BOOK = next((ROOT / "research" / "Book").glob("滴天髓*.epub"), None)
OUT = ROOT / "research" / "fetched" / "ditiansui_liuji.txt"

TAG = re.compile(r"<[^>]+>")
BR = re.compile(r"</(p|div|h[1-6]|br|li|tr)>", re.I)


def epub_texts(path: pathlib.Path) -> list[tuple[str, str]]:
    with zipfile.ZipFile(path) as z:
        names = [n for n in z.namelist() if n.lower().endswith((".xhtml", ".html", ".htm"))]
        out = []
        for n in names:
            try:
                raw = z.read(n).decode("utf-8")
            except UnicodeDecodeError:
                continue
            txt = BR.sub("\n", raw)
            txt = TAG.sub("", txt)
            txt = html.unescape(txt)
            txt = re.sub(r"[ \t\u3000]+", "", txt)
            txt = re.sub(r"\n{3,}", "\n\n", txt)
            out.append((n, txt.strip()))
        return out


def main() -> int:
    if BOOK is None:
        print("未找到《滴天髓》epub")
        return 1
    parts = epub_texts(BOOK)
    with OUT.open("w", encoding="utf-8") as f:
        for n, t in parts:
            f.write(f"===== {n} =====\n{t}\n\n")
    total = sum(len(t) for _, t in parts)
    print(f"{BOOK.name} → {OUT}（{len(parts)} 篇，共 {total} 字）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
