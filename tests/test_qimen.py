"""奇门遁甲排盘回归测试：局数歌诀、黄金用例、引文逐字锁定。"""
import pathlib
import re

import pytest

from fortune.qimen import (GONG_XING, JU_TABLE, bu_ju, day_yuan,
                           governing_jieqi)
from fortune.qimen.duanyu import format_chart
from fortune.qimen.text import NOTES, QUOTES

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _norm(s):
    return re.sub(r"\s+", "", s)


def test_ju_table_against_song():
    """局数表与《秘笈大全》起例歌一致（抽查关键条目）。"""
    assert JU_TABLE["冬至"] == (1, 7, 4) and JU_TABLE["惊蛰"] == (1, 7, 4)
    assert JU_TABLE["小寒"] == (2, 8, 5) and JU_TABLE["大寒"] == (3, 9, 6)
    assert JU_TABLE["立春"] == (8, 5, 2) and JU_TABLE["雨水"] == (9, 6, 3)
    assert JU_TABLE["清明"] == (4, 1, 7) and JU_TABLE["谷雨"] == (5, 2, 8)
    assert JU_TABLE["芒种"] == (6, 3, 9)
    assert JU_TABLE["夏至"] == (9, 3, 6) and JU_TABLE["白露"] == (9, 3, 6)
    assert JU_TABLE["大暑"] == (7, 1, 4) and JU_TABLE["秋分"] == (7, 1, 4)
    assert JU_TABLE["大雪"] == (4, 7, 1) and JU_TABLE["寒露"] == (6, 9, 3)
    # 阳遁/阴遁分界
    assert bu_ju(1990, 12, 25, 12, 0).dun == "阳遁"    # 冬至后
    assert bu_ju(1990, 6, 25, 12, 0).dun == "阴遁"     # 夏至后


def test_mijidaquan_anchor_yang2():
    """《秘笈大全》金锚：阳遁二局甲子日乙丑时 → 值使死门加艮八，休门在坤二。"""
    c = bu_ju(1988, 1, 10, 1, 30)
    assert c.dun == "阳遁" and c.ju == 2 and c.yuan == "上元"
    assert c.jie_qi == "小寒"
    assert c.day_ganzhi == "甲子" and c.hour_ganzhi == "乙丑"
    assert c.zhi_fu_xing == "天芮" and c.zhi_shi_men == "死门"
    assert c.di_pan[2] == "戊" and c.di_pan[1] == "乙"   # 阳遁二局：戊起坤二…乙在坎一
    assert c.men_pan[2] == "休门"                        # 秘笈「休门飞到坤二宫」


def test_yang1_jiashi_fuyin():
    """阳遁一局甲子日甲子时 → 值符天蓬值使休门，全伏吟。"""
    c = bu_ju(1989, 1, 4, 0, 30)
    assert c.dun == "阳遁" and c.ju == 1 and c.yuan == "上元"
    assert c.jie_qi == "冬至"
    assert c.day_ganzhi == "甲子" and c.hour_ganzhi == "甲子"
    assert c.zhi_fu_xing == "天蓬" and c.zhi_shi_men == "休门"
    assert c.di_pan == {1: "戊", 2: "己", 3: "庚", 4: "辛", 5: "壬",
                        6: "癸", 7: "丁", 8: "丙", 9: "乙"}
    assert c.tian_pan == {g: GONG_XING[g] for g in range(1, 10)}
    assert c.fu_yin is True


def test_yin9_jiashi():
    """阴遁九局甲子日甲子时：值符天英值使景门；地盘戊起离九逆布。"""
    c = bu_ju(1985, 9, 22, 0, 30)
    assert c.dun == "阴遁" and c.ju == 9 and c.yuan == "上元"
    assert c.jie_qi == "白露"
    assert c.day_ganzhi == "甲子" and c.hour_ganzhi == "甲子"
    assert c.zhi_fu_xing == "天英" and c.zhi_shi_men == "景门"
    assert c.di_pan[9] == "戊" and c.di_pan[8] == "己" and c.di_pan[1] == "丁"
    assert c.tian_pan[9] == "天英"                       # 值符加时干（甲→旬首宫）
    assert c.men_pan[1] == "景门"                        # 值使景门加时支宫（子→坎一）


def test_di_pan_consistency_and_zhong_gong():
    """地盘九宫全排九仪奇；天禽在五宫（寄坤二）；门神不入中五。"""
    for dt in ((1990, 1, 15, 12, 0), (1990, 6, 25, 12, 0), (1990, 3, 1, 6, 0)):
        c = bu_ju(*dt)
        assert set(c.di_pan.values()) == set("戊己庚辛壬癸丁丙乙")
        assert len(c.di_pan) == 9
        assert c.tian_pan.get(5) is not None
        assert 5 not in c.men_pan and 5 not in c.shen_pan


def test_governing_jieqi():
    import datetime as dt
    assert governing_jieqi(dt.datetime(1990, 6, 15, 12, 0)) == "芒种"
    assert governing_jieqi(dt.datetime(1990, 12, 25, 12, 0)) == "冬至"
    assert governing_jieqi(dt.datetime(1990, 1, 10, 12, 0)) == "小寒"


def test_day_yuan():
    assert day_yuan("甲子") == "上元" and day_yuan("己卯") == "上元"
    assert day_yuan("甲寅") == "中元" and day_yuan("己亥") == "中元"
    assert day_yuan("甲辰") == "下元" and day_yuan("戊戌") == "下元"


@pytest.mark.skipif(not (ROOT / "research" / "fetched" / "奇门秘笈大全.txt").exists(),
                    reason="《奇门遁甲秘笈大全》存档缺失")
def test_quotes_verbatim_in_sources():
    mj = _norm((ROOT / "research" / "fetched" / "奇门秘笈大全.txt").read_text(encoding="utf-8"))
    yb = _norm((ROOT / "research" / "fetched" / "wikisource_yanbodiao sou.txt")
               .read_text(encoding="utf-8"))
    mj_keys = {"布仪", "符使", "局数阳", "局数阴", "天禽", "值使例", "值使例注",
               "九星", "八门", "八神阳", "八神阴", "八神替", "八神替2"}
    for k in mj_keys:
        assert _norm(QUOTES[k]) in mj, k
    for k in ("烟波布仪", "烟波符使"):
        assert _norm(QUOTES[k]) in yb, k


def test_notes_mark_disputes():
    assert "拆补" in NOTES["三元"] and "置闰" in NOTES["三元"]
    assert "九宫方位" in NOTES["值使"] and "顺逆数地支" in NOTES["值使"]


def test_cli_qimen():
    from typer.testing import CliRunner
    from fortune.cli import app
    r = CliRunner().invoke(app, ["qimen", "-y", "1989", "-m", "1", "-d", "4",
                                 "-H", "0", "-M", "30"])
    assert r.exit_code == 0, r.output
    assert "奇门遁甲" in r.output and "阳遁 1 局" in r.output
    assert "伏吟" in r.output


def test_report_smoke():
    c = bu_ju(1988, 1, 10, 1, 30)
    text = format_chart(c)
    assert "奇门遁甲" in text and "值符" in text and "死门" in text
