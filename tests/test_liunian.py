"""流年模块测试。"""
from fortune.bazi.chart import build
from fortune.bazi.liunian import compute, liunian_ganzhi
from fortune.config import FortuneConfig
from fortune.core.calendar import normalize
from fortune.core.model import BirthInfo


def make_chart():
    birth = BirthInfo(calendar="solar", year=1990, month=6, day=15, hour=13,
                      minute=30, gender="男", longitude=120.0)
    nb = normalize(birth, FortuneConfig(use_true_solar_time=False))
    return build(nb, "男", FortuneConfig(use_true_solar_time=False))


def test_liunian_ganzhi():
    # 2024 甲辰、2025 乙巳（立春换年）
    assert liunian_ganzhi(2024) == "甲辰"
    assert liunian_ganzhi(2025) == "乙巳"


def test_liunian_2000():
    """1990-06-15 男（庚午 壬午 辛亥 乙未）：2000 年流年庚辰。
    - 日主辛，庚=劫财；
    - 流年干庚与时干乙五合；
    - 大运癸未（1997-2006）。
    """
    r = compute(make_chart(), 2000)
    assert r.gan_zhi == "庚辰"
    assert r.shi_shen == "劫财"
    assert r.dayun == "癸未"
    assert any("庚" in f and "乙" in f and "五合" in f for f in r.facts)


def test_liunian_suiyun_binglin():
    """岁运并临：找一个大运干支==流年干支的年份。
    1990-06-15 男：大运 癸未(1997-2006)、甲申(2007-2016)…
    2003 年流年癸未 == 大运癸未 → 岁运并临。"""
    r = compute(make_chart(), 2003)
    assert r.gan_zhi == "癸未"
    assert r.dayun == "癸未"
    assert any("岁运并临" in f for f in r.facts)


def test_liunian_tian_ke_di_chong():
    """天克地冲：1990-06-15 男，大运甲申(2007-2016)。
    流年庚寅（2010）：庚克甲（阳干克）且寅冲申 → 天克地冲。"""
    r = compute(make_chart(), 2010)
    assert r.gan_zhi == "庚寅"
    assert r.dayun == "甲申"
    assert any("天克地冲" in f for f in r.facts)
    assert any("寅冲大运支申" in f for f in r.facts)
