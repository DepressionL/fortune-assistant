"""七政四余排盘回归测试：星躔黄金用例、命宫安命法、宿度闭合、引文逐字锁定。"""
import pathlib
import re

import pytest

from fortune.qizheng import (GONG_CN, GONG_ZHU, HUA_YAO, SU_BOUNDS, SU_DU,
                             ZIQI_PRESETS, _lon_to_su, _ming_gong, qizheng,
                             ziqi_positions)
from fortune.qizheng.duanyu import format_chart
from fortune.qizheng.text import NOTES, QUOTES

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _norm(s):
    return re.sub(r"\s+", "", s)


def test_star_positions_golden():
    """1990-06-15 13:30 北京时间：日月木土实测锚点（瑞士星历）。"""
    c = qizheng(1990, 6, 15, 13, 30)
    ri = c.stars["日"]
    assert abs(ri["lon"] - 83.87) < 0.2 and ri["gong"] == "申" and ri["su"] == "参"
    yue = c.stars["月"]
    assert yue["gong"] == "亥" and yue["gong_cn"] == "双鱼" and yue["su"] == "室"
    mu = c.stars["木"]
    assert mu["gong"] == "未" and mu["gong_cn"] == "巨蟹"   # 1990 木星巨蟹
    tu = c.stars["土"]
    assert tu["gong"] == "丑" and tu["gong_cn"] == "磨羯"   # 1990 土星摩羯


def test_luo_ji_duigong():
    c = qizheng(1990, 6, 15, 13, 30)
    assert abs((c.stars["罗"]["lon"] + 180.0) % 360 - c.stars["计"]["lon"]) < 1e-6


def test_ming_gong_rule():
    """安命法：太阳子宫酉时生 → 命宫午（《张果星宗》歌例）。"""
    assert _ming_gong(10, "酉") == 4      # 子宫 → 午宫
    assert GONG_CN[4] == ("午", "狮子")
    c = qizheng(1990, 6, 15, 13, 30)      # 太阳申宫未时 → 命宫辰
    assert c.ming_gong == "辰"
    assert c.ming_du.startswith("角")


def test_su_bounds_closed():
    """宿界闭合：28 界、角宿起 198°（辰宫，合「角亢氐初总在辰」）。"""
    assert len(SU_BOUNDS) == 28 and len(SU_DU) == 28
    names = [n for n, _ in SU_BOUNDS]
    assert len(set(names)) == 28
    jiao = dict(SU_BOUNDS)["角"]
    assert 180 <= jiao < 210
    # 总度数 ≈ 360（古度表换算后闭合）
    total = sum(d + f / 100.0 for _, d, f in SU_DU)
    assert abs(total - 360.0) < 1.5


def test_hua_yao_and_gong_zhu():
    assert HUA_YAO["甲"] == "火" and HUA_YAO["乙"] == "孛"
    assert HUA_YAO["辛"] == "气" and HUA_YAO["壬"] == "计" and HUA_YAO["癸"] == "罗"
    assert GONG_ZHU["子"] == "土" and GONG_ZHU["午"] == "日" and GONG_ZHU["未"] == "月"


@pytest.mark.skipif(not (ROOT / "research" / "fetched" / "张果星宗_clean.txt").exists(),
                    reason="《张果星宗》清洗存档缺失")
def test_quotes_verbatim_in_sources():
    zg = _norm((ROOT / "research" / "fetched" / "张果星宗_clean.txt").read_text(encoding="utf-8"))
    xd = _norm((ROOT / "research" / "fetched" / "星学大成.txt").read_text(encoding="utf-8"))
    for k in ("安命", "安命例", "命度", "宫主", "宫分", "行度", "行度2", "行度3", "太阳行度"):
        assert _norm(QUOTES[k]) in zg, k
    for k in ("化曜", "化曜歌", "罗计"):
        assert _norm(QUOTES[k]) in xd, k


def test_notes_mark_disputes():
    assert "紫气" in NOTES["紫气"] and "多套" in NOTES["紫气"]
    assert "回归黄道" in NOTES["岁差"] and "恒星黄道" in NOTES["岁差"]


def test_ziqi_presets_golden():
    """紫气多口径黄金用例：
    - 果老·立成1910：1910-01-05 恰在辰宫二十二度（202°，立成表锚点）；
    - 民国星历口径：1912-04-29 应为丑宫二十五度五十三分左右（295.88°，论坛比对值）；
    - 果老·1900：1900-01-01 恰在白羊初度（0°）。"""
    import swisseph as swe
    sel, rows = ziqi_positions(swe.julday(1910, 1, 5, 0.0))
    by_key = {r["key"]: r for r in rows}
    assert abs(by_key["guolao1910"]["lon"] - 202.0) < 0.01
    # 1900-01-01 → 1910-01-05 = 3656 日（1904/1908 闰）
    assert abs(by_key["guolao1900"]["lon"] - (3656 / 29) % 360) < 0.01
    sel2, rows2 = ziqi_positions(swe.julday(1912, 4, 29, 0.0))
    by_key2 = {r["key"]: r for r in rows2}
    assert abs(by_key2["minguo1910"]["lon"] - 295.883) < 0.05   # 丑宫25°53′
    # 1900-01-01 果老·1900 = 0°
    sel3, rows3 = ziqi_positions(swe.julday(1900, 1, 1, 0.0))
    by_key3 = {r["key"]: r for r in rows3}
    assert by_key3["guolao1900"]["lon"] == 0.0
    assert by_key3["xingping1900"]["lon"] == 0.0


def test_ziqi_custom_and_presets_meta():
    """自定义口径追加行；每个口径行带速率与起算点出处（可追溯）。"""
    import swisseph as swe
    jd = swe.julday(1990, 6, 15, 0.0)
    sel, rows = ziqi_positions(jd, custom=(1 / 29.0, swe.julday(1900, 1, 1, 0.0), 5.0))
    assert rows[-1]["key"] == "custom"
    assert abs(rows[-1]["lon"] - ((jd - swe.julday(1900, 1, 1, 0.0)) / 29.0 + 5.0) % 360) < 0.01
    for r in rows:
        assert r["rate_src"] and r["epoch_src"] and r["note"]
    assert len(ZIQI_PRESETS) == 6
    # 默认口径标注「最常用」
    assert any("最常用" in p["epoch_src"] for p in ZIQI_PRESETS)


def test_qizheng_ziqi_in_chart():
    c = qizheng(1990, 6, 15, 13, 30)
    assert "气" in c.stars and c.stars["气"]["preset"].startswith("果老")
    assert len(c.ziqi_rows) == 6
    text = format_chart(c)
    assert "紫气多口径对照" in text and "最常用" in text


def test_cli_qizheng():
    from typer.testing import CliRunner
    from fortune.cli import app
    r = CliRunner().invoke(app, ["qizheng", "-y", "1990", "-m", "6", "-d", "15",
                                 "-H", "13", "-M", "30"])
    assert r.exit_code == 0, r.output
    assert "七政四余" in r.output and "命宫" in r.output and "罗睺" in r.output
    assert "紫气多口径对照" in r.output


def test_cli_qizheng_ziqi_custom():
    from typer.testing import CliRunner
    from fortune.cli import app
    r = CliRunner().invoke(app, ["qizheng", "-y", "1990", "-m", "6", "-d", "15",
                                 "-H", "13", "--ziqi-preset", "guolao1910",
                                 "--ziqi-rate", "0.03448", "--ziqi-epoch",
                                 "1900-01-01", "--ziqi-epoch-lon", "3"])
    assert r.exit_code == 0, r.output
    assert "自定义" in r.output and "紫气多口径对照" in r.output


def test_report_smoke():
    c = qizheng(1990, 6, 15, 13, 30)
    text = format_chart(c)
    assert "七政四余" in text and "辰宫" in text and "化曜" in text
