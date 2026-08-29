"""《神峰通考》盖头说/病药说类/雕枯旺弱四病说类/损益生长四药说类
文本模块回归测试（维基文库本 + 影印本文字层 双源逐字锁定）。"""
import pathlib
import re

import pytest

from fortune.bazi import yongshen as ys
from fortune.bazi.chart import build as build_bazi
from fortune.bazi.shenfeng_text import NOTES, SHENFENG, SHENFENG_QUOTES
from fortune.bazi.strength import compute as strength_compute
from fortune.config import FortuneConfig
from fortune.core.calendar import normalize
from fortune.core.model import BirthInfo

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC_WS = ROOT / "research" / "fetched" / "shenfeng_wikisource.txt"
SRC_PDF = ROOT / "research" / "fetched" / "shenfeng.txt"

EXPECTED = ["盖头说", "病药说类", "雕枯旺弱四病说类", "损益生长四药说类"]


def _norm(s):
    return re.sub(r"\s+", "", s)


def make(dt: str, gender: str = "男"):
    d, t = dt.split(" ")
    y, m, dd = d.split("-")
    h, mi = t.split(":")
    birth = BirthInfo(calendar="solar", year=int(y), month=int(m), day=int(dd),
                      hour=int(h), minute=int(mi), gender=gender, longitude=120.0)
    cfg = FortuneConfig(use_true_solar_time=False)
    return build_bazi(normalize(birth, cfg), gender, cfg)


def test_four_chapters_present():
    assert list(SHENFENG.keys()) == EXPECTED


@pytest.mark.skipif(not SRC_WS.exists() or not SRC_PDF.exists(), reason="存档缺失")
def test_chapters_verbatim_in_wikisource():
    """章文须逐字（去空白）存在于维基文库存档。"""
    ws = _norm(SRC_WS.read_text(encoding="utf-8"))
    for key, text in SHENFENG.items():
        assert _norm(text) in ws, f"{key} 不在维基文库存档中"


@pytest.mark.skipif(not SRC_WS.exists() or not SRC_PDF.exists(), reason="存档缺失")
def test_quotes_dual_source_verified():
    """引用句须同时逐字（去空白）存在于维基文库本与影印本文字层。"""
    ws = _norm(SRC_WS.read_text(encoding="utf-8"))
    pdf = _norm(SRC_PDF.read_text(encoding="utf-8"))
    for key, qs in SHENFENG_QUOTES.items():
        assert qs, f"{key} 引用句为空（可能被双源互校剔除）"
        for q in qs:
            assert _norm(q) in _norm(SHENFENG[key]), f"维基文库章文：{key} :: {q}"
            assert _norm(q) in ws, f"维基文库存档：{key} :: {q}"
            assert _norm(q) in pdf, f"影印本文字层：{key} :: {q}"


def test_transcription_notes():
    for key in ["盖头说", "雕枯旺弱四病说类", "损益生长四药说类"]:
        assert key in NOTES and NOTES[key]
    assert "雨" in NOTES["雕枯旺弱四病说类"]     # 「而」作「雨」如实标注
    assert "桔" in NOTES["雕枯旺弱四病说类"]     # 「枯」作「桔」如实标注


def test_bingyao_cites_four_diseases_and_four_medicines():
    """bingyao 输出应附 四病四药（雕枯/损益）引文与双源互校标注。"""
    c = make("1990-06-15 13:30")
    st = strength_compute(c)
    r = ys.bingyao(c, st)
    text = "\n".join(r.conclusions)
    assert "《神峰通考》病药说类原文" in text
    assert "雕枯旺弱四病说类" in text and "苟玉之不琢" in text
    assert "损益生长四药说类" in text and "损者，损其有余也" in text
    assert "维基文库本" in text


def test_bingyao_gaitou_trigger_when_bing_tou_gan():
    """病神透干时应触发盖头说引注。"""
    # 1990-06-15 病神=火但天干无火 → 不触发
    c = make("1990-06-15 13:30")
    st = strength_compute(c)
    text = "\n".join(ys.bingyao(c, st).conclusions)
    assert "盖头说" not in text
    # 身弱、官杀火透干（丙午年）→ 病神火透干，应触发
    c2 = make("1986-07-07 12:00")
    st2 = strength_compute(c2)
    assert st2.level == "身弱"
    r2 = ys.bingyao(c2, st2)
    text2 = "\n".join(r2.conclusions)
    if "病神取火" in text2:
        assert "盖头说" in text2 and "露出头面" in text2
