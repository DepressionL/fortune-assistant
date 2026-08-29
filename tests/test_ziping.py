"""《子平真诠评注》数据模块 回归测试。"""
import pathlib
import re

import pytest

from fortune.bazi.ziping_text import ZIPING

SRC = pathlib.Path(__file__).resolve().parents[1] / "research" / "fetched" / "ziping_pingzhu.txt"

PUNCT = "。，；、？！：（）()「」『』·—─…，?!\"'　 \n\t"


def strip_all(s: str) -> str:
    return "".join(c for c in s if c not in PUNCT)


def test_structure():
    assert len(ZIPING) >= 40
    for k, v in ZIPING.items():
        assert v.strip(), k


@pytest.mark.skipif(not SRC.exists(), reason="评注存档缺失")
def test_fidelity_each_chapter_is_substring():
    src = strip_all(SRC.read_text(encoding="utf-8"))
    bad = []
    for k, v in ZIPING.items():
        if strip_all(v) not in src:
            bad.append((k, v[:30]))
    assert not bad, f"以下章节不是原文子串：{bad}"


def test_golden_anchors():
    assert ZIPING["论用神"].startswith("八字用神，专求月令")
    assert "官以克身" in ZIPING["论正官"]
    assert "煞以攻身" in ZIPING["论偏官"]
    assert "财为我克" in ZIPING["论财"] or "财者，我所克" in ZIPING["论财"]
    assert ZIPING["论建禄月劫"]


def test_yongshen_geju_cites_ziping():
    from fortune.bazi.chart import build as build_bazi
    from fortune.bazi.yongshen import compute_yongshen
    from fortune.config import FortuneConfig
    from fortune.core.calendar import normalize
    from fortune.core.model import BirthInfo

    birth = BirthInfo(calendar="solar", year=1990, month=6, day=15, hour=13,
                      minute=30, gender="男", longitude=120.0)
    cfg = FortuneConfig(use_true_solar_time=False)
    chart = build_bazi(normalize(birth, cfg), "男", cfg)
    r = compute_yongshen(chart, "geju")
    out = str(r)
    assert r.school.startswith("geju")
    # 七杀格应引《论偏官》章（此前映射缺「七杀」键导致漏引——本断言防回归）
    assert "《子平真诠》论偏官" in out
    assert "徐乐吾评注" in out and "煞以攻身" in out
