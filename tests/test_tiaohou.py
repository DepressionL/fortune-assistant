"""《穷通宝鉴》调候表 回归测试。

- 结构：10 干 × 12 月 = 120 条、无空串；
- 忠实性：每条（去注记后缀、去标点/空白）必须是 t2s(原文去标记、去标点) 的子串
  —— 锁死「程序化提取、非杜撰」；
- 黄金用例：与原文逐字对照的锚点；
- yongshen 集成：tiaohou 流派输出含原文与出处。
"""
import pathlib
import re

import pytest

from fortune.bazi.tiaohou_text import TIAOHOU_TEXT

SRC = pathlib.Path(__file__).resolve().parents[1] / "research" / "fetched" / "qiongbao.txt"

try:
    from opencc import OpenCC
    T2S = OpenCC("t2s")
except ImportError:  # pragma: no cover
    T2S = None

PUNCT = "。，；、？！：（）()「」『』·—─…，?!\"'　 \n\t"


def strip_all(s: str) -> str:
    return "".join(c for c in s if c not in PUNCT and not c.isspace())


def clean_src(s: str) -> str:
    s = re.sub(r"\{\{.*?\}\}", "", s)
    s = s.replace("-{", "").replace("}-", "")
    s = re.sub(r"<[^>]+>", "", s)
    s = s.replace("'''", "")
    return s


def no_note(s: str) -> str:
    return re.sub(r"（注：[^）]*）$", "", s)


def test_structure():
    assert set(TIAOHOU_TEXT) == set("甲乙丙丁戊己庚辛壬癸")
    for stem in TIAOHOU_TEXT:
        assert len(TIAOHOU_TEXT[stem]) == 12, stem
        for mo in range(1, 13):
            assert TIAOHOU_TEXT[stem][mo].strip(), f"{stem}{mo} 为空"


@pytest.mark.skipif(T2S is None or not SRC.exists(), reason="opencc 或原文存档缺失")
def test_fidelity_each_entry_is_substring_of_source():
    src = strip_all(T2S.convert(clean_src(SRC.read_text(encoding="utf-8"))))
    bad = []
    for stem in TIAOHOU_TEXT:
        for mo in range(1, 13):
            entry = strip_all(no_note(TIAOHOU_TEXT[stem][mo]))
            if entry and entry not in src:
                bad.append((stem, mo, entry[:40]))
    assert not bad, f"以下条目不是原文子串（可能被改写/杜撰）：{bad}"


def test_golden_cases():
    assert "得丙癸逢" in TIAOHOU_TEXT["甲"][1]
    assert "先取庚金，次用壬水" in TIAOHOU_TEXT["甲"][3]
    assert "先庚后甲" in TIAOHOU_TEXT["丁"][2]
    assert "先用甲木" in TIAOHOU_TEXT["丁"][3]
    assert "耑用庚甲" in TIAOHOU_TEXT["丁"][12]      # 三冬丁火
    assert "不宜乱用甲木" in TIAOHOU_TEXT["丁"][5]
    assert TIAOHOU_TEXT["丁"][6].endswith("（注：该月原书无独立论，参考前月原文）")


def test_yongshen_tiaohou_uses_text():
    from fortune.bazi.chart import build as build_bazi
    from fortune.bazi.yongshen import compute_yongshen
    from fortune.config import FortuneConfig
    from fortune.core.calendar import normalize
    from fortune.core.model import BirthInfo

    birth = BirthInfo(calendar="solar", year=1990, month=6, day=15, hour=13,
                      minute=30, gender="男", longitude=120.0)
    cfg = FortuneConfig(use_true_solar_time=False)
    chart = build_bazi(normalize(birth, cfg), "男", cfg)
    r = compute_yongshen(chart, "tiaohou")
    out = str(r)
    assert r.school.startswith("tiaohou")
    assert "《穷通宝鉴》原文" in out
    assert "维基文库" in out
