"""紫微斗数测试：用 research/ziwei_tables.md 核验过的经典安星锚点
反验 x_iztro 引擎输出（不自建表，以引擎为权威基准）。"""
import pytest

from fortune.bazi.chart import build as build_bazi
from fortune.config import FortuneConfig
from fortune.core.calendar import normalize
from fortune.core.model import BirthInfo
from fortune.report import svg as svg_report
from fortune.ziwei import chart as zc

BR = "子丑寅卯辰巳午未申酉戌亥"


def make(dt: str, gender: str = "男", **cfg_kw) -> zc.ZiweiChart:
    date_part, time_part = dt.split(" ")
    y, m, d = date_part.split("-")
    h, mi = time_part.split(":")
    birth = BirthInfo(calendar="solar", year=int(y), month=int(m), day=int(d),
                      hour=int(h), minute=int(mi), gender=gender, longitude=120.0)
    config = FortuneConfig(use_true_solar_time=False, **cfg_kw)
    nb = normalize(birth, config)
    return zc.build(nb, gender, config)


def test_time_index():
    assert zc._time_index(0) == 0 and zc._time_index(23) == 12
    assert zc._time_index(1) == 1 and zc._time_index(13) == 7
    assert zc._time_index(22) == 11


def test_ming_shen_gong_formula():
    """命宫 = 寅起顺数生月→月宫，再起子时逆数生时；身宫 = 顺数生时。
    （《紫微斗数全书》安身命诀；仅对非闰月、fix_leap 无修正的日期有效）"""
    for dt in ("1990-06-15 13:30", "2000-02-05 09:00", "1984-02-02 12:00"):
        z = make(dt)
        # 用农历月/时支独立推命宫
        date_part, time_part = dt.split(" ")
        y, m, d = date_part.split("-")
        h = int(time_part.split(":")[0])
        birth = BirthInfo(calendar="solar", year=int(y), month=int(m), day=int(d),
                          hour=h, minute=0, gender="男", longitude=120.0)
        nb = normalize(birth, FortuneConfig(use_true_solar_time=False))
        lm = abs(nb.lunar_month)
        h_idx = zc._time_index(h)  # 0=子 … 11=亥（23 点=晚子 12 不适用此公式，测试时间避开）
        yue = (2 + (lm - 1)) % 12          # 寅=2 起正月顺数
        ming = (yue - h_idx) % 12          # 月宫起子时逆数
        shen = (yue + h_idx) % 12
        got_ming = BR.index(z.palaces[z.ming_index].gan_zhi[1])
        got_shen = BR.index(z.palaces[z.shen_index].gan_zhi[1])
        assert got_ming == ming, (dt, z.palaces[z.ming_index].gan_zhi)
        assert got_shen == shen, dt


def test_palace_order():
    z = make("1990-06-15 13:30")
    assert [p.name for p in z.palaces] == list(zc.PALACE_ORDER)
    assert z.palaces[z.ming_index].is_ming
    assert z.palaces[z.shen_index].is_shen


def test_ziwei_tianfu_axis_symmetry():
    """紫微与天府关于寅申线镜面对称：天府 = (4 − 紫微索引) mod 12
    （索引和 ≡ 4；紫微在寅/申时紫府同宫——「紫府同宫」格）。
    该规则以 x_iztro（iztro 移植）实测为权威基准；
    注意 research/ziwei_tables.md §6.1 原列「寅↔申」为对宫映射（有误，
    已在文档内加修正附注）。"""
    for dt in ("1990-06-15 13:30", "2000-02-05 09:00", "1976-07-28 03:42",
               "2024-02-10 00:30", "1949-10-01 15:00"):
        z = make(dt)
        zw = tf = None
        for p in z.palaces:
            for name, bright, mut in p.major:
                if name == "紫微":
                    zw = BR.index(p.gan_zhi[1])
                if name == "天府":
                    tf = BR.index(p.gan_zhi[1])
        assert zw is not None and tf is not None, dt
        assert (zw + tf) % 12 == 4, (dt, zw, tf)
        assert tf == (4 - zw) % 12, (dt, zw, tf)
    # 紫府同宫格：1990-06-15 未时（土五局五月廿三）→ 紫微天府同在申
    z = make("1990-06-15 13:30")
    assert any(p.gan_zhi.endswith("申") and "紫微" in [n for n, _, _ in p.major]
               and "天府" in [n for n, _, _ in p.major] for p in z.palaces)


def test_geng_sihua_switch():
    """庚年：默认天同化忌（主流）；tianxiang 配置 → 天相化忌。"""
    z = make("2000-02-05 09:00")  # 庚辰年
    found = {}
    for p in z.palaces:
        for name, bright, m in p.major:
            if m:
                found[m] = name
    assert found.get("忌") == "天同"
    z2 = make("2000-02-05 09:00", ziwei_geng_sihua="tianxiang")
    found2 = {}
    for p in z2.palaces:
        for name, bright, m in p.major:
            if m:
                found2[m] = name
    assert found2.get("忌") == "天相"


def test_five_elements_class_matches_ming_gong_nayin():
    """五行局 = 命宫干支纳音 → 局数（水二木三金四土五火六）。"""
    from lunar_python.util import LunarUtil
    z = make("1990-06-15 13:30")
    mgz = z.palaces[z.ming_index].gan_zhi
    nayin = LunarUtil.NAYIN[mgz]
    wx = nayin[-1]  # 纳音末字为五行（如「海中金」→金）
    expect = {"金": "金四局", "木": "木三局", "水": "水二局",
              "火": "火六局", "土": "土五局"}[wx]
    assert z.five_elements_class == expect, (mgz, nayin, z.five_elements_class)


def test_ziwei_tianfu_star_offsets():
    """十四主星相对位置与安星口诀逐字核对（引擎行为回归锚点）。
    口诀：《紫微斗数全书》——紫微逆去天机星，隔一阳武天同临，又隔二位廉贞地，
    空三复见紫微星；天府太阴顺贪狼，巨门天相与天梁，七杀空三破军位。
    实测锚点：1976-07-28 卯时（水二局）紫微在寅、天府同宫在寅。"""
    from x_iztro.astro import Astro
    r = Astro().by_solar("1976-7-28", 3, "male")
    pos = {}
    for p in r.palaces:
        for s in p.major_stars:
            pos[s.name] = BR.index(p.earthly_branch)
    assert pos["紫微"] == 2  # 寅
    ZW_OFF = {"紫微": 0, "天机": 1, "太阳": 3, "武曲": 4, "天同": 5, "廉贞": 8}
    TF_OFF = {"天府": 0, "太阴": 1, "贪狼": 2, "巨门": 3, "天相": 4, "天梁": 5,
              "七杀": 6, "破军": 10}
    for s, off in ZW_OFF.items():
        assert pos[s] == (pos["紫微"] - off) % 12, f"紫微系 {s} 偏移不符"
    for s, off in TF_OFF.items():
        assert pos[s] == (pos["天府"] + off) % 12, f"天府系 {s} 偏移不符"


def test_dayun_direction():
    """大限方向：阳男顺行/阴男逆行。宫列表为命宫起逆时针排，
    阳男顺行（地支序方向）→ 列表内大限首岁每步 −10（mod 120）；
    阴男逆行 → 每步 +10。"""
    z_yang = make("2000-02-05 09:00")          # 庚辰（阳）年，男
    starts = [int(p.da_xian.split("-")[0]) for p in z_yang.palaces]
    assert starts[0] in (2, 3, 4, 5, 6)         # 命宫起于五行局数
    for i in range(12):
        assert (starts[i] - starts[(i + 1) % 12]) % 120 == 10, (i, starts)

    z_yin = make("2000-01-01 12:00")           # 己卯（阴）年，男
    starts2 = [int(p.da_xian.split("-")[0]) for p in z_yin.palaces]
    for i in range(12):
        assert (starts2[(i + 1) % 12] - starts2[i]) % 120 == 10, (i, starts2)


def test_svg_output():
    z = make("1990-06-15 13:30")
    svg = svg_report.ziwei_palace_svg(z.palaces_for_svg(), note=z.svg_note())
    assert svg.startswith("<svg")
    assert "紫微" not in svg or "命宫" in svg
    assert "</svg>" in svg


def test_leap_mode_as_next_rejected():
    with pytest.raises(NotImplementedError):
        make("1990-06-15 13:30", ziwei_leap_month="as_next")
