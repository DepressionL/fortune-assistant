"""《渊海子平》交叉核验与新增神煞（魁罡/日贵/金神）黄金用例测试。"""
import pathlib

from fortune.bazi import shensha as sh
from fortune.bazi.chart import build as build_bazi
from fortune.config import FortuneConfig
from fortune.core.calendar import normalize
from fortune.core.model import BirthInfo


def make(dt: str, gender: str = "男"):
    d, t = dt.split(" ")
    y, m, dd = d.split("-")
    h, mi = t.split(":")
    birth = BirthInfo(calendar="solar", year=int(y), month=int(m), day=int(dd),
                      hour=int(h), minute=int(mi), gender=gender, longitude=120.0)
    cfg = FortuneConfig(use_true_solar_time=False)
    return build_bazi(normalize(birth, cfg), gender, cfg)


def hit(chart, name):
    return next((h for h in sh.compute(chart) if h.name == name), None)


def test_yangren_matches_yuanhai():
    """交叉核验：《渊海子平·论阳刃》「以禄前一位是也……甲丙戊庚壬五阳有刃，
    乙丁己辛癸五阴无刃」——与本仓 YANGREN 表一致。"""
    assert sh.YANGREN == {"甲": "卯", "丙": "午", "戊": "午", "庚": "酉", "壬": "子"}
    # 阳干禄前一位规则穷举
    LU = {"甲": "寅", "丙": "巳", "戊": "巳", "庚": "申", "壬": "亥"}
    ZHI = "子丑寅卯辰巳午未申酉戌亥"
    for gan, ren in sh.YANGREN.items():
        assert ren == ZHI[(ZHI.index(LU[gan]) + 1) % 12], gan


def test_kuigang():
    """1970-01-12 丑时 → 日柱壬辰（四魁罡之一）。"""
    c = make("1970-01-12 02:00")
    assert c.pillar("日柱").gan_zhi == "壬辰"
    h = hit(c, "魁罡")
    assert h is not None and "论魁罡" in h.note


def test_kuigang_negative():
    c = make("1970-01-07 02:00")  # 日柱丁亥，非魁罡
    assert hit(c, "魁罡") is None


def test_rigui():
    """1970-01-07 丑时 → 日柱丁亥（四日贵之一）。"""
    c = make("1970-01-07 02:00")
    assert c.pillar("日柱").gan_zhi == "丁亥"
    h = hit(c, "日贵")
    assert h is not None and "丁亥" in h.values and "论日贵" in h.note


def test_jinshen_three_hours():
    """1970-01-04：丑时→乙丑、巳时→己巳、酉时→癸酉 三时皆金神。"""
    for h, gz in ((2, "乙丑"), (10, "己巳"), (18, "癸酉")):
        c = make(f"1970-01-04 {h:02d}:00")
        assert c.pillar("时柱").gan_zhi == gz
        hh = hit(c, "金神")
        assert hh is not None and gz in hh.values and "入火乡为胜" in hh.note


def test_source_file_present():
    """《渊海子平》存档存在（维基文库赋文编本，无卷一神煞起法篇，如实记录）。"""
    src = pathlib.Path(__file__).resolve().parents[1] / "research" / "fetched" / "yuanhai.txt"
    assert src.exists()
