#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""本地《周易》表 × 独立默写结果 逐字比对脚本（一次性核验工具，非测试）。

比对口径：
- 去掉全部标点（古籍无句读，各本句读互异，非实质差异）；
- 我方卦辞去掉开头卦名引导词（如「乾，」），子代理爻辞去掉爻题（如「初九：」）；
- 字符级全等即视为一致，逐条列出不一致处供人工裁定。
用法：python -m tests.diff_zhouyi  # 或直接 python tests/diff_zhouyi.py
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from fortune.misc import zhouyi  # noqa: E402

PUNCT = "。，；、？！：（）()「」『』·—─…，?!"


def strip_punct(s: str) -> str:
    return "".join(c for c in s if c not in PUNCT and not c.isspace())


def strip_yaoti(s: str) -> str:
    """去爻题：初九：/九二：/六三：/上九：/用九： 等前缀。"""
    if "：" in s:
        s = s.split("：", 1)[1]
    return s


def strip_lead(gua_body: str, s: str) -> str:
    """去卦辞开头的卦名引导词（乾，/坤，/否之匪人 不属此类，保留）。"""
    for lead in (gua_body + "，", gua_body + "，"):
        if s.startswith(lead):
            return s[len(lead):]
    return s


def main() -> int:
    fixture = pathlib.Path(__file__).resolve().parent / "fixtures" / \
        "zhouyi_subagent_recitation.json"
    ref = json.loads(fixture.read_text(encoding="utf-8"))

    diffs = []
    for body_name, (my_gua, my_yaos, _mean) in zhouyi.ZHOUYI.items():
        assert body_name in ref, f"fixture 缺 {body_name}"
        r_gua = strip_punct(ref[body_name]["卦辞"])
        m_gua = strip_punct(strip_lead(body_name, my_gua))
        if m_gua != r_gua:
            diffs.append((body_name, "卦辞", m_gua, r_gua))
        r_yaos = ref[body_name]["爻辞"]
        assert len(r_yaos) == 6, body_name
        for i in range(6):
            m_y = strip_punct(my_yaos[i])
            r_y = strip_punct(strip_yaoti(r_yaos[i]))
            if m_y != r_y:
                diffs.append((body_name, f"爻{i+1}", m_y, r_y))

    print(f"总差异条数：{len(diffs)}")
    for body_name, where, mine, theirs in diffs:
        print(f"[{body_name} {where}] 我方: {mine} | 对方: {theirs}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
