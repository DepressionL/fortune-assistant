"""八字黄金用例测试。

期望值来自 research/bazi_golden_cases.md（lunar_python 与 sxtwl 双引擎实测对照，
并经在线排盘实例核验）。排盘均关闭真太阳时（经度 120°，即不校正），与报告一致。
"""
import pytest

from fortune.bazi.chart import build
from fortune.config import FortuneConfig
from fortune.core.calendar import normalize
from fortune.core.model import BirthInfo

# (公历时间, 期望四柱, 顺逆, 起运日期, 第一步大运干支, 起运虚岁)
GOLDEN = [
    ("2000-01-01 12:00", ("己卯", "丙子", "戊午", "戊午"), False, "2008-03-11", "乙亥", 9),
    ("2000-02-05 09:00", ("庚辰", "戊寅", "癸巳", "丁巳"), True, "2009-10-25", "己卯", 10),
    ("1984-02-02 12:00", ("癸亥", "乙丑", "丙寅", "甲午"), False, "1993-02-02", "甲子", 10),
    ("1990-06-15 13:30", ("庚午", "壬午", "辛亥", "乙未"), True, "1997-11-04", "癸未", 8),
    ("2024-02-10 00:30", ("甲辰", "丙寅", "甲辰", "甲子"), True, "2032-03-30", "丁卯", 9),
    ("1976-07-28 03:42", ("丙辰", "乙未", "辛巳", "庚寅"), True, "1980-02-07", "丙申", 5),
    ("1949-10-01 15:00", ("己丑", "癸酉", "甲子", "壬申"), False, "1957-07-11", "壬申", 9),
]


def make_chart(dt: str, gender: str = "男", day_change: int = 23) -> tuple:
    date_part, time_part = dt.split(" ")
    y, m, d = date_part.split("-")
    h, mi = time_part.split(":")
    birth = BirthInfo(calendar="solar", year=int(y), month=int(m), day=int(d),
                      hour=int(h), minute=int(mi), gender=gender,
                      longitude=120.0, is_dst=False)
    config = FortuneConfig(use_true_solar_time=False, day_change_hour=day_change)
    nb = normalize(birth, config)
    return build(nb, gender, config), nb


@pytest.mark.parametrize("dt,expect_pillars,forward,start,dayun1,age", GOLDEN)
def test_golden_pillars_dayun(dt, expect_pillars, forward, start, dayun1, age):
    chart, _ = make_chart(dt)
    got = tuple(p.gan_zhi for p in chart.pillars)
    assert got == expect_pillars, f"{dt}: 四柱 {got} != {expect_pillars}"
    assert chart.yun_forward == forward
    assert chart.yun_start_solar == start
    assert chart.dayun[0].gan_zhi == dayun1
    assert chart.yun_start_age == age


def test_zaowan_zishi_sect():
    """夜子时（23:30）换日流派差异：23点换日=戊午，0点换日=丁巳。"""
    c23, _ = make_chart("2000-02-29 23:30", day_change=23)
    c0, _ = make_chart("2000-02-29 23:30", day_change=0)
    assert c23.pillar("日柱").gan_zhi == "戊午"
    assert c0.pillar("日柱").gan_zhi == "丁巳"
    # 时柱两派一致（壬子）
    assert c23.pillar("时柱").gan_zhi == "壬子" == c0.pillar("时柱").gan_zhi


def test_lichun_boundary():
    """立春精确时刻边界：2000-02-04 18:00（立春 20:40 前）年柱己卯、月柱丁丑。"""
    chart, _ = make_chart("2000-02-04 18:00")
    assert chart.pillar("年柱").gan_zhi == "己卯"
    assert chart.pillar("月柱").gan_zhi == "丁丑"


def test_canggan_nayin_1990():
    chart, _ = make_chart("1990-06-15 13:30")
    expect_hide = {"年柱": ["丁", "己"], "月柱": ["丁", "己"],
                   "日柱": ["壬", "甲"], "时柱": ["己", "丁", "乙"]}
    expect_nayin = {"年柱": "路旁土", "月柱": "杨柳木", "日柱": "钗钏金", "时柱": "沙中金"}
    for p in chart.pillars:
        assert p.hide_gan == expect_hide[p.name], p.name
        assert p.na_yin == expect_nayin[p.name], p.name


def test_wuxing_count():
    chart, _ = make_chart("1990-06-15 13:30")
    # 庚(金)午(火) 壬(水)午(火) 辛(金)亥(水) 乙(木)未(土) → 金2 火2 水2 木1 土1
    assert chart.wuxing_count == {"木": 1, "火": 2, "土": 1, "金": 2, "水": 2}


def test_taiyuan_minggong_shengong_present():
    chart, _ = make_chart("1990-06-15 13:30")
    assert len(chart.tai_yuan) == 2 and len(chart.ming_gong) == 2 and len(chart.shen_gong) == 2


def test_yin_nan_ni_xing():
    """阴年男命逆行：2000-01-01（己卯阴年）男 → 逆行。"""
    chart, _ = make_chart("2000-01-01 12:00")
    assert chart.yun_forward is False
    # 阴年女命 → 顺行
    chart_f, _ = make_chart("2000-01-01 12:00", gender="女")
    assert chart_f.yun_forward is True


def test_sxtwl_crosscheck():
    """与 sxtwl（寿星天文历，独立实现）交叉验证四柱干支（非边界日）。"""
    sxtwl = pytest.importorskip("sxtwl")
    GAN = ["", "甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    ZHI = ["", "子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

    def gz(g):
        return GAN[g.tg + 1] + ZHI[g.dz + 1]

    for dt, expect, *_ in GOLDEN:
        date_part, time_part = dt.split(" ")
        y, m, d = date_part.split("-")
        h, mi = time_part.split(":")
        day = sxtwl.fromSolar(int(y), int(m), int(d))
        got = (gz(day.getYearGZ(False)), gz(day.getMonthGZ()), gz(day.getDayGZ()),
               gz(day.getHourGZ(int(h), True)))
        assert got == expect, f"{dt}: sxtwl {got} != lunar_python {expect}"


def test_config_validation():
    from fortune.config import FortuneConfig
    with pytest.raises(AssertionError):
        FortuneConfig(day_change_hour=12).validate()
    with pytest.raises(AssertionError):
        FortuneConfig(year_change="bad").validate()
    FortuneConfig().validate()
