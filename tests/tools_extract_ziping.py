#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""从《子平真诠评注》（沈孝瞻原著、徐乐吾评注，GB18030→UTF-8 存档）提取
各章合刊文本，生成 fortune/bazi/ziping_text.py（程序化提取，非手工转写）。

数据源：research/fetched/ziping_pingzhu.txt（由 research/Book 评注 txt 转码）。
章节标题形如「八、论用神」「十二、 论用神格局高低」；原文与徐乐吾评注为
合刊混排，**本工具不做原文/评注分离**（分离需与《子平真诠》原本逐段对齐，
另立任务），引用时如实标注「沈孝瞻原著、徐乐吾评注合刊本」。
用法：python tests/tools_extract_ziping.py
"""
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

SRC = pathlib.Path(__file__).resolve().parents[1] / "research" / "fetched" / "ziping_pingzhu.txt"
OUT = pathlib.Path(__file__).resolve().parents[1] / "fortune" / "bazi" / "ziping_text.py"

# 章标题：中文数字 + 、/．/。 + 论…（允许数字后带空格）
HEAD = re.compile(r"^\s*([一二三四五六七八九十]+)[、．.]\s*(论[^\n]{1,20})\s*$", re.M)


def clean(s: str) -> str:
    s = re.sub(r"[\u3000\t ]+", "", s)
    return s.strip()


def extract() -> dict[str, str]:
    t = SRC.read_text(encoding="utf-8")
    chapters: dict[str, str] = {}
    pos = []  # (start, title)
    for m in HEAD.finditer(t):
        pos.append((m.start(), m.group(2).strip()))
    for i, (s, title) in enumerate(pos):
        e = pos[i + 1][0] if i + 1 < len(pos) else len(t)
        body = clean(t[s:e])
        # 去掉行首「N、论XXX」编号标题
        body = re.sub(r"^[一二三四五六七八九十]+[、．.]\s*" + re.escape(title) + r"\s*",
                      "", body, count=1)
        if body.strip():
            chapters[title] = body
    return chapters


def main() -> int:
    data = extract()
    if len(data) < 30:
        print("章节数不足：", len(data))
        return 1
    with OUT.open("w", encoding="utf-8") as f:
        f.write('"""《子平真诠评注》（清·沈孝瞻原著，民国·徐乐吾评注）各章合刊文本。\n\n')
        f.write("出处：research/Book《子平真诠评注》txt（GB18030）转码存档\n")
        f.write("research/fetched/ziping_pingzhu.txt，由 tests/tools_extract_ziping.py\n")
        f.write("程序化提取，非手工转写；一致性由 tests/test_ziping.py 回归锁定。\n")
        f.write("注意：原文与徐乐吾评注为合刊混排，未做逐段分离（引用时如实标注）；\n")
        f.write('个别传本文字与今排印本或有出入，以本书为准。\n"""\n\n')
        f.write("ZIPING: dict[str, str] = {\n")
        for title, body in data.items():
            f.write(f"    {json.dumps(title, ensure_ascii=False)}: "
                    f"{json.dumps(body, ensure_ascii=False)},\n")
        f.write("}\n")
    print(f"已生成 {OUT}（章节 {len(data)}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
