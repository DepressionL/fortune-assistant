#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""本地《周易》表 × 维基文库《周易》逐字比对（权威数字版核验工具）。

数据源：zh.wikisource.org《周易》64 卦子页（research/fetched/zhouyi_pages/*.txt，
Textquality 50%，通行本经文），与本地 fortune/misc/zhouyi.py 比对。

比对口径：
- 去除全部标点（古籍无句读，各本句读互异）；
- 去除 MediaWiki 标记（-{ }-、'''、<span>…）、卦名引导词、爻题；
- 维基文库繁体 → OpenCC t2s 转简体后与本地表字符级比对。
用法：python tests/verify_zhouyi_wikisource.py
"""
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from opencc import OpenCC  # noqa: E402

from fortune.misc import zhouyi  # noqa: E402

PAGES = pathlib.Path(__file__).resolve().parents[1] / "research" / "fetched" / "zhouyi_pages"
PUNCT = "。，；、？！：（）()「」『』·—─…，?!\"'　 "
T2S = OpenCC("t2s")
# 子页名（繁体）→ 本体（简体），个别异体直接映射（注意 t2s 会把「乾」误转「干」）
NAME_MAP = {"无妄": "无妄", "遯": "遁", "恆": "恒", "干": "乾"}
# 同一汉字的扩展区码位 → 常用码位（维基文库部分页用了 CJK 扩展区异体码位）
CHAR_MAP = {"𬙊": "纆", "𦈡": "繻", "㧑": "撝", "𫗧": "餗"}
# 文言异体（t2s 未覆盖）→ 简体通行字（均为已核实的经典异文，见 zhouyi.py YIWEN）
VARIANT_MAP = {"遯": "遁", "袛": "祗", "踟躅": "蹢躅", "亨祀": "享祀"}


def norm(s: str) -> str:
    s = s.replace("乾乾", "<QQ>")          # 保护「终日乾乾」不被 t2s 误转「干干」
    s = T2S.convert(s)
    s = s.replace("<QQ>", "乾乾")
    for a, b in {**CHAR_MAP, **VARIANT_MAP}.items():
        s = s.replace(a, b)
    return s


def strip_all(s: str) -> str:
    return "".join(c for c in s if c not in PUNCT and not c.isspace())


def clean(s: str) -> str:
    s = re.sub(r"-{", "", s)
    s = re.sub(r"}-", "", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = s.replace("'''", "")
    s = re.sub(r"^[*#\s]+", "", s)          # 剥 list 标记 *#
    return s.strip()


def parse_page(text: str) -> tuple[str, list[str], list[tuple[str, str]]]:
    """→ (卦辞(带卦名引导), [6 条爻辞], [(用九/用六, 文本)])."""
    lines = text.splitlines()
    start = end = -1
    for i, ln in enumerate(lines):
        if "'''易經" in ln and start < 0:
            start = i
        elif start >= 0 and re.match(r"\*'''", ln.strip()):
            end = i
            break
    block = lines[start:end if end > start else None]
    gua_ci = ""
    yaos: list[str] = []
    extra: list[tuple[str, str]] = []
    for ln in block:
        raw = clean(ln)
        if ln.strip().startswith("**"):
            gua_ci += raw               # 部分卦的卦辞跨多行，拼接
        elif ln.strip().startswith("*#"):
            m = re.match(r"^(初[六九]|[六九][二三四五]|上[六九]|用[九六])[：:]?", raw)
            if m:
                yaoti, body_txt = m.group(1), raw[m.end():]
                if yaoti in ("用九", "用六"):
                    extra.append((yaoti, body_txt))
                else:
                    yaos.append(body_txt)
            else:
                yaos.append(raw)
    return gua_ci, yaos, extra


def compare_all() -> tuple[list[tuple[str, str, str, str]], list[str]]:
    """全量比对 → (差异列表, 用九/用六差异列表)。供命令行与回归测试共用。"""
    diffs: list[tuple[str, str, str, str]] = []
    extras_diff: list[str] = []
    for f in sorted(PAGES.glob("*.txt")):
        raw = f.read_text(encoding="utf-8")
        gua_ci, yaos, extra = parse_page(raw)
        if len(yaos) != 6:
            print(f"[{f.stem}] 解析出的爻辞非 6 条：{len(yaos)}")
            continue
        # 卦名本体：从子页名（繁体）→ 简体
        body = T2S.convert(f.stem)
        body = NAME_MAP.get(body, body)
        if body not in zhouyi.ZHOUYI:
            print(f"[{f.stem}] 无法映射到本地表（{body}）")
            continue
        my_gua, my_yaos, _ = zhouyi.ZHOUYI[body]

        # 卦辞：去卦名引导（“乾：”；坎卦引导为“习坎”）
        ws_gua = strip_all(norm(gua_ci.split("：", 1)[1] if "：" in gua_ci else gua_ci))
        lead = body + "，"
        if body == "坎":
            lead = "习坎，"
        m_gua = strip_all(my_gua[len(lead):] if my_gua.startswith(lead) else my_gua)
        if m_gua != ws_gua:
            diffs.append((body, "卦辞", m_gua, ws_gua))

        # 爻辞：爻题已在 parse_page 中剥除
        for i in range(6):
            ws_y = strip_all(norm(yaos[i]))
            m_y = strip_all(my_yaos[i])
            if m_y != ws_y:
                diffs.append((body, f"爻{i+1}", m_y, ws_y))

        # 用九/用六
        for key, txt in extra:
            val = strip_all(norm(txt))
            mine = strip_all(zhouyi.YONG_YAO.get(body, "") or "")
            if mine != val:
                extras_diff.append(f"[{body} {key}] 我方: {mine} | 文库: {val}")
    return diffs, extras_diff


def main() -> int:
    diffs, extras_diff = compare_all()
    print(f"差异条数：{len(diffs)}；用九/用六差异：{len(extras_diff)}")
    for b, w, mine, ws in diffs:
        print(f"[{b} {w}] 我方: {mine} | 文库: {ws}")
    for e in extras_diff:
        print(e)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
