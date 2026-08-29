"""《滴天髓》文本模块与何知章规则映射回归测试。"""
import pathlib
import re

import pytest

from fortune.bazi import ditiansui as hz_mod
from fortune.bazi.chart import build as build_bazi
from fortune.bazi.ditiansui_text import DITIANSUI, HZ_LINES, QUOTES, VARIANTS
from fortune.bazi.strength import compute as strength_compute
from fortune.bazi.yongshen import compute_yongshen
from fortune.config import FortuneConfig
from fortune.core.calendar import normalize
from fortune.core.model import BirthInfo

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "research" / "fetched" / "ditiansui_liuji.txt"

TONG_SHEN = ["天道", "地道", "人道", "知命", "理气", "配合", "天干", "地支",
             "干支总论", "形象", "方局", "八格", "体用", "精神", "月令", "生时",
             "衰旺", "中和", "源流", "通关", "官杀", "伤官", "清气", "浊气",
             "真神", "假神", "刚柔", "顺逆", "寒暖", "燥湿", "隐显", "众寡",
             "震兑", "坎离"]


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


def test_chapters_complete():
    for t in TONG_SHEN + ["何知章", "夫妻", "子女", "父母", "兄弟", "女命章"]:
        assert t in DITIANSUI and DITIANSUI[t], t


@pytest.mark.skipif(not SRC.exists(), reason="存档缺失")
def test_chapters_and_quotes_verbatim():
    """章文与引句须逐字（去空白）存在于 epub 存档。"""
    text = _norm(SRC.read_text(encoding="utf-8"))
    for key, body in DITIANSUI.items():
        assert _norm(body) in text, f"{key} 不在存档中"
    for key, q in QUOTES.items():
        assert _norm(q) in _norm(DITIANSUI[key]), f"{key} :: {q}"


def test_hezhang_eight_lines_and_variants():
    assert len(HZ_LINES) == 8
    assert HZ_LINES[0] == "何知其人富？财气通门户。"
    assert HZ_LINES[2] == "何知其人贫?财贫神反不真。"      # 底本原字
    assert HZ_LINES[6] == "何知其人寿？性定元神厚"         # 底本此句无句号
    assert "财贫神反不真" in VARIANTS and "品泯" in VARIANTS["生成品泯"]
    assert "相邀入洞户" in VARIANTS


def test_hezhi_golden_weak():
    """1990-06-15 辛日身弱：财透（乙）、月支藏官（丁七杀）、
    用神土金有气、印旺 → 命中 富/贵/吉/寿，不中 贫/贱/凶/夭。"""
    c = make("1990-06-15 13:30")
    st = strength_compute(c)
    assert st.level == "身弱"
    hits = {h.key: h for h in hz_mod.hezhi(c, st)}
    assert set(hits) == {"富", "贵", "贫", "贱", "吉", "凶", "寿", "夭"}
    assert [hits[k].matched for k in ("富", "贵", "吉", "寿")] == [True] * 4
    assert [hits[k].matched for k in ("贫", "贱", "凶", "夭")] == [False] * 4
    for k in hits:
        assert hits[k].line == HZ_LINES[("富", "贵", "贫", "贱", "吉", "凶", "寿", "夭").index(k)]
        assert hits[k].reason


def test_hezhi_no_crash_strong():
    c = make("1984-03-02 12:00")
    st = strength_compute(c)
    assert st.level == "身强"
    hits = hz_mod.hezhi(c, st)
    assert len(hits) == 8 and any(h.matched for h in hits)


def test_hezhi_suiyun_golden():
    """1990-06-15 大运流年重算：大运4丙戌/5丁亥透火忌神 → 新增「凶」；
    大运1内 丁丑(1997)/丙戌(2006) 流年新增「凶」。"""
    c = make("1990-06-15 13:30")
    st = strength_compute(c)
    rows, diffs = hz_mod.hezhi_suiyun(c, st)
    assert len(rows) == 8
    by_index = {r["index"]: r for r in rows}
    base = {h.key for h in hz_mod.hezhi(c, st) if h.matched}
    assert by_index[1]["gan_zhi"] == "癸未"
    assert by_index[1]["delta"] == "同原局"
    assert by_index[4]["delta"] == "新增凶" and "凶" in by_index[4]["matched"]
    assert by_index[5]["delta"] == "新增凶"
    for r in rows:
        assert set(r["matched"]) <= set(base) | {"凶"}
    diffs_by = {(d["dayun"], d["gan_zhi"], d["year"]): d for d in diffs}
    assert diffs_by[(1, "丁丑", 1997)]["added"] == ["凶"]
    assert diffs_by[(1, "丙戌", 2006)]["added"] == ["凶"]
    assert all(d["added"] for d in diffs)


def test_hezhi_suiyun_strong_no_crash():
    c = make("1984-03-02 12:00")
    st = strength_compute(c)
    rows, diffs = hz_mod.hezhi_suiyun(c, st)
    assert len(rows) == 8 and all(len(r["matched"]) <= 8 for r in rows)


def test_yongshen_quotes_enriched():
    """wangshuai/tiaohou/tongguan 输出应含新增《滴天髓》引文。"""
    c = make("1990-06-15 13:30")
    st = strength_compute(c)
    out_w = str(compute_yongshen(c, "wangshuai"))
    assert "能知衰旺之真机" in out_w and "既识中和之正理" in out_w
    out_t = str(compute_yongshen(c, "tiaohou"))
    assert "天道有寒暖" in out_t and "地道有燥湿" in out_t and "品汇" in out_t
    c2 = make("1990-02-04 12:00")
    out_g = str(compute_yongshen(c2, "tongguan"))
    assert "相邀入洞户" in out_g


def test_cli_hezhang_section():
    from typer.testing import CliRunner
    from fortune.cli import app
    r = CliRunner().invoke(app, ["bazi", "-y", "1990", "-m", "6", "-d", "15",
                                 "-H", "13", "--no-true-solar",
                                 "--schools", "wangshuai,bingyao"])
    assert r.exit_code == 0, r.output
    assert "何知章速览" in r.output
    assert "何知其人富？财气通门户。" in r.output
    assert "何知其人寿？性定元神厚" in r.output
    assert "何知章速览·大运流年" in r.output
    assert "丙戌" in r.output and "新增凶" in r.output
