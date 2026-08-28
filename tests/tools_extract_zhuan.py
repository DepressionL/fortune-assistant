#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""从维基文库抓取的 64 卦页面提取《彖传》《大象传》原文，
生成 fortune/misc/zhouyi_zhuan.py（纯简体数据模块，无第三方依赖）。

数据源：research/fetched/zhouyi_pages/*.txt（zh.wikisource.org《周易》，
Public Domain，2026-08-29 抓取）。生成后与抓取页的回归测试见
tests/test_zhouyi_zhuan.py。
用法：python tests/tools_extract_zhuan.py
"""
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from opencc import OpenCC

from tests.verify_zhouyi_wikisource import NAME_MAP, norm  # noqa: E402

PAGES = pathlib.Path(__file__).resolve().parents[1] / "research" / "fetched" / "zhouyi_pages"
OUT = pathlib.Path(__file__).resolve().parents[1] / "fortune" / "misc" / "zhouyi_zhuan.py"

T2S = OpenCC("t2s")


def clean_zhuan(s: str) -> str:
    s = re.sub(r"\{\{.*?\}\}", "", s)          # 去 {{*|一作…}} 等模板
    s = re.sub(r"-{", "", s)
    s = re.sub(r"}-", "", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = s.replace("'''", "")
    s = re.sub(r"^[*#\s]+", "", s)
    return s.strip()


def extract(text: str) -> tuple[str, str]:
    """→ (彖传, 大象传)。"""
    lines = text.splitlines()
    tuan_lines: list[str] = []
    xiang_line = ""
    mode = None
    for ln in lines:
        s = ln.strip()
        if re.match(r"\*'''", s):
            if "彖曰" in s:
                mode = "tuan"
            elif "象曰" in s:
                mode = "xiang"
            else:
                mode = None
            continue
        if mode == "tuan":
            c = clean_zhuan(ln)
            if c:
                tuan_lines.append(c)
        elif mode == "xiang":
            c = clean_zhuan(ln)
            if c and not xiang_line and not ln.strip().startswith("*#") and not ln.strip().startswith("**"):
                pass  # 无标记行不取（大象传在各页以 ** 开头）
            if c and not xiang_line and ln.strip().startswith("**"):
                xiang_line = c
    tuan = "".join(tuan_lines)
    if not xiang_line:
        # 兜底：象曰后第一条非 *# 行
        mode = None
        for ln in lines:
            s = ln.strip()
            if re.match(r"\*'''", s):
                mode = "xiang" if "象曰" in s else None
                continue
            if mode == "xiang":
                c = clean_zhuan(ln)
                if c and not ln.strip().startswith("*#"):
                    xiang_line = c
                    break
    return tuan, xiang_line


def main() -> int:
    tuan_map: dict[str, str] = {}
    xiang_map: dict[str, str] = {}
    missing_tuan, missing_xiang = [], []
    for f in sorted(PAGES.glob("*.txt")):
        raw = f.read_text(encoding="utf-8")
        body = NAME_MAP.get(T2S.convert(f.stem), T2S.convert(f.stem))
        tuan, xiang = extract(raw)
        if not tuan:
            missing_tuan.append(body)
        if not xiang:
            missing_xiang.append(body)
        tuan_map[body] = norm(tuan)
        xiang_map[body] = norm(xiang)

    if missing_tuan or missing_xiang:
        print(f"缺彖传：{missing_tuan}；缺大象传：{missing_xiang}")
        return 1

    with OUT.open("w", encoding="utf-8") as f:
        f.write('"""《周易》彖传、大象传原文（简体）—— 逐字引文数据模块。\n\n')
        f.write('出处：通行本《周易》（维基文库 zh.wikisource.org 64 卦子页，\n')
        f.write('Public Domain，2026-08-29 抓取存档 research/fetched/zhouyi_pages/），\n')
        f.write('由 tests/tools_extract_zhuan.py 程序化提取、繁转简（OpenCC t2s）后生成，\n')
        f.write('非手工转写；与抓取页的一致性由 tests/test_zhouyi_zhuan.py 回归锁定。\n')
        f.write('彖传为全篇（卦辞后之彖辞）；大象传为「君子以…」一句（象曰首条）。\n"""\n\n')
        f.write("TUAN: dict[str, str] = {\n")
        for body, t in tuan_map.items():
            f.write(f'    "{body}": "{t}",\n')
        f.write("}\n\n\n")
        f.write("XIANG: dict[str, str] = {\n")
        for body, x in xiang_map.items():
            f.write(f'    "{body}": "{x}",\n')
        f.write("}\n")
    print(f"已生成 {OUT}（彖传 {len(tuan_map)}、大象传 {len(xiang_map)}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
