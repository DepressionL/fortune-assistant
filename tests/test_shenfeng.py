"""《神峰通考》病药流派（bingyao）回归测试。"""
import pathlib
import re

import pytest

from fortune.bazi import yongshen as ys
from fortune.bazi.chart import build as build_bazi
from fortune.bazi.strength import compute as strength_compute
from fortune.config import FortuneConfig
from fortune.core.calendar import normalize
from fortune.core.model import BirthInfo

SRC = pathlib.Path(__file__).resolve().parents[1] / "research" / "fetched" / "shenfeng.txt"


def make(dt: str, gender: str = "男"):
    d, t = dt.split(" ")
    y, m, dd = d.split("-")
    h, mi = t.split(":")
    birth = BirthInfo(calendar="solar", year=int(y), month=int(m), day=int(dd),
                      hour=int(h), minute=int(mi), gender=gender, longitude=120.0)
    cfg = FortuneConfig(use_true_solar_time=False)
    return build_bazi(normalize(birth, cfg), gender, cfg)


@pytest.mark.skipif(not SRC.exists(), reason="《神峰通考》存档缺失")
def test_quotes_verbatim_in_source():
    """病药说引文（去空白后）必须逐字存在于《神峰通考》文本层中。"""
    text = re.sub(r"\s+", "", SRC.read_text(encoding="utf-8"))
    for q in ("何以为之病？原八字中原所害之神也；何以为之药？如八字原有所害之字，而得一字以去之",
              "有病方为贵，无伤不是奇；格中如去病，财禄两相随"):
        assert re.sub(r"\s+", "", q) in text, q


def test_bingyao_shen_ruo():
    """1990-06-15 辛日身弱：病=官杀火（2.40 最旺忌神）、药=水。"""
    c = make("1990-06-15 13:30")
    st = strength_compute(c)
    assert st.level == "身弱"
    r = ys.bingyao(c, st)
    assert r.school.startswith("bingyao")
    assert "病神取火" in "\n".join(r.conclusions)
    assert "药神取水" in "\n".join(r.conclusions)
    assert r.yong_wuxing == ["水"]


def test_bingyao_shen_qiang():
    """1984-03-02 甲日身强：病=比劫/印中得分最高者、药=克病之五行。"""
    c = make("1984-03-02 12:00")
    st = strength_compute(c)
    assert st.level == "身强"
    r = ys.bingyao(c, st)
    assert r.yong_wuxing and r.yong_wuxing[0] in "金火土水木"
    assert "《神峰通考》病药说类原文" in "\n".join(r.conclusions)


def test_compute_yongshen_bingyao_and_config():
    c = make("1990-06-15 13:30")
    r = ys.compute_yongshen(c, "bingyao")
    assert r.school.startswith("bingyao")
    cfg = FortuneConfig(yongshen_school="bingyao")
    cfg.validate()   # 枚举校验应接受 bingyao


def test_cli_school_bingyao():
    from typer.testing import CliRunner
    from fortune.cli import app
    r = CliRunner().invoke(app, ["bazi", "-y", "1990", "-m", "6", "-d", "15",
                                 "-H", "13", "--school", "bingyao"])
    assert r.exit_code == 0, r.output
    assert "病药" in r.output and "神峰通考" in r.output
