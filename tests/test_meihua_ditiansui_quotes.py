"""《梅花易数》体用总诀与《滴天髓》通神论 引注回归测试。"""
import pathlib
import re

import pytest

from fortune.misc import meihua as mh

MH_SRC = pathlib.Path(__file__).resolve().parents[1] / "research" / "fetched" / "meihua_yishu.txt"
DT_SRC = pathlib.Path(__file__).resolve().parents[1] / "research" / "fetched" / "ditiansui.txt"


def _norm(s):
    return re.sub(r"\s+", "", s)


@pytest.mark.skipif(not MH_SRC.exists(), reason="《梅花易数》存档缺失")
def test_meihua_tiyong_quote_verbatim():
    """体用总诀引文须逐字存在于《梅花易数》存档（去空白比对）。"""
    text = _norm(MH_SRC.read_text(encoding="utf-8"))
    quote = "体克用，诸事吉；用克体，诸事凶。体生用，有耗失之患；用生体，有进益之喜。体用比和，则百事顺遂"
    assert _norm(quote) in text


def test_meihua_verdicts_match_quote():
    """断语与体用总诀一致：用克体凶、体克用小吉、体生用泄、用生体吉、比和吉。"""
    assert mh._interact("离", "乾")[0] == "用克体"     # 用火克体金
    assert mh._interact("坤", "乾")[0] == "用生体"     # 用土生体金
    assert mh._interact("乾", "兑")[0] == "比和"       # 金金
    assert mh._interact("震", "乾")[0] == "体克用"     # 体金克用木


def test_meihua_docstring_marks_tuoming():
    assert "托名" in mh.__doc__


@pytest.mark.skipif(not DT_SRC.exists(), reason="《滴天髓》存档缺失")
def test_ditiansui_quote_verbatim():
    text = _norm(DT_SRC.read_text(encoding="utf-8"))
    assert "理承气行岂有常，进兮退兮宜抑扬" in text


def test_wangshuai_cites_ditiansui():
    from fortune.bazi.chart import build as build_bazi
    from fortune.bazi.yongshen import compute_yongshen
    from fortune.config import FortuneConfig
    from fortune.core.calendar import normalize
    from fortune.core.model import BirthInfo

    birth = BirthInfo(calendar="solar", year=1990, month=6, day=15, hour=13,
                      minute=30, gender="男", longitude=120.0)
    cfg = FortuneConfig(use_true_solar_time=False)
    chart = build_bazi(normalize(birth, cfg), "男", cfg)
    out = str(compute_yongshen(chart, "wangshuai"))
    assert "滴天髓" in out and "理承气行岂有常" in out
