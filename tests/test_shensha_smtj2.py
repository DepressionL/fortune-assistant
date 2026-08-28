"""《三命通会》卷三第二批新增神煞 黄金用例测试（元辰/暗金的煞/六厄/勾绞/德秀）。"""
from fortune.bazi import shensha as sh
from fortune.bazi.chart import build as build_bazi
from fortune.config import FortuneConfig
from fortune.core.calendar import normalize
from fortune.core.model import BirthInfo

ZHI = "子丑寅卯辰巳午未申酉戌亥"


def make(dt: str, gender: str = "男"):
    d, t = dt.split(" ")
    y, m, dd = d.split("-")
    h, mi = t.split(":")
    birth = BirthInfo(calendar="solar", year=int(y), month=int(m), day=int(dd),
                      hour=int(h), minute=int(mi), gender=gender, longitude=120.0)
    cfg = FortuneConfig(use_true_solar_time=False)
    return build_bazi(normalize(birth, cfg), gender, cfg)


def names(chart):
    return [h.name for h in sh.compute(chart)]


def hit(chart, name):
    return next((h for h in sh.compute(chart) if h.name == name), None)


def test_anjin_exhaustive():
    """暗金的煞：四仲(子午卯酉)→巳、四孟(寅申巳亥)→酉、四季(辰戌丑未)→丑。"""
    for z in "子午卯酉":
        assert sh._ANJIN[z] == "巳"
    for z in "寅申巳亥":
        assert sh._ANJIN[z] == "酉"
    for z in "辰戌丑未":
        assert sh._ANJIN[z] == "丑"


def test_liu_e_exhaustive():
    """六厄：三合局五行死位（申子辰→卯、寅午戌→酉、亥卯未→午、巳酉丑→子）。"""
    for z in "申子辰":
        assert sh._LIU_E[z] == "卯"
    for z in "寅午戌":
        assert sh._LIU_E[z] == "酉"
    for z in "亥卯未":
        assert sh._LIU_E[z] == "午"
    for z in "巳酉丑":
        assert sh._LIU_E[z] == "子"


def test_yang_ming_partition():
    assert sh._yang_ming("甲", "男") and sh._yang_ming("乙", "女")
    assert not sh._yang_ming("乙", "男") and not sh._yang_ming("甲", "女")


def test_yuanchen_forward():
    """1984-03-02 甲子年阳男 → 元辰在冲前一位=未（柱含未）。"""
    c = make("1984-03-02 12:00", "男")
    assert (c.gans()[0], c.zhis()[0]) == ("甲", "子") and "未" in c.zhis()
    h = hit(c, "元辰")
    assert h is not None and "未" in h.values and "冲前一位" in h.note


def test_yuanchen_backward():
    """1985-03-01 乙丑年阴男 → 元辰在冲后一位=午（柱含午）。"""
    c = make("1985-03-01 12:00", "男")
    assert (c.gans()[0], c.zhis()[0]) == ("乙", "丑") and "午" in c.zhis()
    h = hit(c, "元辰")
    assert h is not None and "午" in h.values and "冲后一位" in h.note


def test_goujiao():
    """1984-03-04 甲子年阳男 → 勾=卯、绞=酉；柱含酉 → 绞煞命中、勾煞不命中。"""
    c = make("1984-03-04 12:00", "男")
    assert "酉" in c.zhis() and "卯" not in c.zhis()
    assert hit(c, "绞煞") is not None
    assert hit(c, "勾煞") is None
    assert "论勾绞" in hit(c, "绞煞").note


def test_dexiu():
    """德秀按月令三合局：戌月（寅午戌）丙丁为德 → 1965-10-10（丙丁在干）命中德；
    卯月（亥卯未）丁壬为秀 → 1962-03-14（壬在干）命中秀。"""
    c1 = make("1965-10-10 12:00")
    assert c1.pillar("月柱").zhi == "戌"
    h1 = hit(c1, "德秀（德）")
    assert h1 is not None and "论德秀" in h1.note and "丙丁为德" in h1.note
    c2 = make("1962-03-14 12:00")
    assert c2.pillar("月柱").zhi == "卯"
    h2 = hit(c2, "德秀（秀）")
    assert h2 is not None and "丁壬为秀" in h2.note


def test_no_false_positive_anjin():
    """暗金的煞按日支查：1960-01-01 日支子 → 目标巳；柱无巳 → 不命中。"""
    c = make("1960-01-01 08:00")
    assert c.pillar("日柱").zhi == "子" and "巳" not in c.zhis()
    assert hit(c, "暗金的煞") is None
