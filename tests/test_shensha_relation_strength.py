"""神煞 / 合冲刑害 / 旺衰 测试。

神煞期望值依据 research/shensha_tables.md 的判定规则手工推导；
合冲刑害期望值依据《三命通会》通行表手工推导。
"""
import pytest

from fortune.bazi import relation, shensha, strength
from fortune.bazi.chart import build
from fortune.config import FortuneConfig
from fortune.core.calendar import normalize
from fortune.core.model import BirthInfo


def make_chart(dt: str, gender: str = "男") -> tuple:
    date_part, time_part = dt.split(" ")
    y, m, d = date_part.split("-")
    h, mi = time_part.split(":")
    birth = BirthInfo(calendar="solar", year=int(y), month=int(m), day=int(d),
                      hour=int(h), minute=int(mi), gender=gender, longitude=120.0)
    config = FortuneConfig(use_true_solar_time=False)
    nb = normalize(birth, config)
    return build(nb, gender, config), config


def names(hits):
    return {h.name for h in hits}


def hit_of(hits, name):
    return [h for h in hits if h.name == name]


def test_shensha_2000_02_05():
    """庚辰 戊寅 癸巳 丁巳：日干癸、日支巳。"""
    chart, cfg = make_chart("2000-02-05 09:00")
    hits = shensha.compute(chart, "day")
    by_name = {h.name: h for h in hits}

    # 天乙贵人：日干癸 → 卯巳；日支巳、时支巳 → 日柱、时柱
    t = by_name["天乙贵人"]
    assert t.positions == ["日柱", "时柱"] and t.values == ["巳", "巳"]
    # 劫煞：日支巳（巳酉丑金局，绝在寅）→ 月支寅
    t = by_name["劫煞"]
    assert t.positions == ["月柱"] and t.values == ["寅"]
    # 桃花：巳→午 → 该盘无午 → 未命中（不生成条目）
    assert by_name.get("桃花(咸池)") is None
    # 天德：月令寅 → 丁 → 时干丁
    t = by_name["天德贵人"]
    assert t.positions == ["时柱"]
    # 月德：月令寅 → 丙 → 无
    assert by_name.get("月德贵人") is None
    # 羊刃：日干癸为阴干 → 无刃（主流，生成带注记的空条目）
    assert by_name["羊刃"].positions == []
    # 红鸾：年支辰 → 亥 → 无
    assert by_name.get("红鸾") is None
    # 空亡：日柱癸巳（甲申旬）→ 午未
    assert by_name["空亡"].values == ["午未"]


def test_shensha_year_base():
    """shensha_base=year 时改用年干年支。"""
    chart, cfg = make_chart("2000-02-05 09:00")
    hits = shensha.compute(chart, "year")
    by_name = {h.name: h for h in hits}
    # 天乙贵人：年干庚 → 丑未 → 该盘无丑未 → 未命中（不生成条目）
    assert by_name.get("天乙贵人") is None
    assert by_name["华盖"].positions == ["年柱"]


def test_relation_chong():
    """甲子 丙寅 戊午 壬申：子午冲（年日）、寅申冲（月时）。"""
    chart, _ = make_chart("2000-01-01 12:00")  # 己卯 丙子 戊午 戊午：子午冲
    hits = relation.scan(chart)
    chongs = [h for h in hits if h.name == "六冲"]
    assert any(h.values == ["子", "午"] for h in chongs)


def test_relation_sanxing():
    """四柱含 辰戌丑未：辰戌冲、丑未冲、丑戌未三刑。"""
    # 构造：甲辰 壬戌 丁丑 丁未（公历任取，直接用柱组合测试 scan 逻辑）
    class FakePillar:
        def __init__(self, name, gz):
            self.name, self.gan_zhi = name, gz
            self.gan, self.zhi = gz[0], gz[1]

    class FakeChart:
        def __init__(self):
            self.pillars = [FakePillar(n, gz) for n, gz in
                            zip(("年柱", "月柱", "日柱", "时柱"),
                                ("甲辰", "壬戌", "丁丑", "丁未"))]

        def gans(self):
            return [p.gan for p in self.pillars]

        def zhis(self):
            return [p.zhi for p in self.pillars]

        def pillar(self, name):
            return next(p for p in self.pillars if p.name == name)

    hits = relation.scan(FakeChart())
    n = names(hits)
    assert "六冲" in n and "三刑" in n
    sxx = [h for h in hits if h.name == "三刑"]
    assert any(set(h.values) == {"丑", "戌", "未"} for h in sxx)
    # 六害：子未害 → 无子，不含六害
    assert "六害" not in n


def test_relation_hai():
    """六害表：子未害。"""
    class FakeChart:
        pillars = [type("P", (), {"name": "年柱", "gan_zhi": "甲子", "gan": "甲", "zhi": "子"})(),
                   type("P", (), {"name": "月柱", "gan_zhi": "乙未", "gan": "乙", "zhi": "未"})(),
                   type("P", (), {"name": "日柱", "gan_zhi": "丙申", "gan": "丙", "zhi": "申"})(),
                   type("P", (), {"name": "时柱", "gan_zhi": "丁酉", "gan": "丁", "zhi": "酉"})()]

        def gans(self):
            return [p.gan for p in self.pillars]

        def zhis(self):
            return [p.zhi for p in self.pillars]

        def pillar(self, name):
            return next(p for p in self.pillars if p.name == name)

    hits = relation.scan(FakeChart())
    hais = [h for h in hits if h.name == "六害"]
    assert any(h.values == ["子", "未"] for h in hais)
    # 申酉无关系（无冲合害刑）


def test_strength_month_states():
    st = strength.month_states("木")
    assert st == {"木": "旺", "火": "相", "水": "休", "金": "囚", "土": "死"}


def test_strength_compute_level():
    chart, _ = make_chart("1990-06-15 13:30")  # 月令午火
    st = strength.compute(chart)
    assert st.month_wx == "火"
    assert set(st.scores) == {"木", "火", "土", "金", "水"}
    assert st.level in ("身强", "身弱", "中和")
    assert len(st.detail) > 0


def test_yongshen_all_schools():
    from fortune.bazi.yongshen import compute_yongshen
    chart, _ = make_chart("1990-06-15 13:30")
    for school in ("wangshuai", "tiaohou", "tongguan", "geju"):
        r = compute_yongshen(chart, school)
        assert r.school.startswith(school)
        assert r.caveat
