"""真太阳时 / 称骨 / 小六壬 / 梅花 / 六爻 / 配置 测试。"""
import datetime as _dt

import pytest

from fortune.core import solar_time as st
from fortune.misc import chenggu, meihua, xiaoliuren
from fortune.liuyao import from_coins, find_gua, xun_kong


# ---------- 真太阳时 ----------
def test_eot_february():
    """2 月 15 日均时差约 −14.2 分钟（NOAA/Meeus/astral 三源一致）。"""
    e = st.equation_of_time(120.0, 2024, 2, 15)
    assert -15.0 < e < -13.4, e


def test_eot_november():
    """11 月 3 日均时差约 +16.4 分钟。"""
    e = st.equation_of_time(120.0, 2024, 11, 3)
    assert 15.4 < e < 17.4, e


def test_correct_true_solar_longitude_only():
    """经度差部分：东经 105°（比 120° 慢 60 分钟）+ EoT。"""
    # 只验证总偏移 = 4*(105-120) + EoT
    e = st.equation_of_time(105.0, 2024, 6, 15)
    *_, shift = st.correct_true_solar(2024, 6, 15, 12, 0, 0, 105.0)
    assert abs(shift - (4 * (105 - 120) + e)) < 1e-9


def test_china_dst():
    """夏令时区间 [开始日 02:00, 结束日 02:00)。"""
    # 开始日：01:59 未拨快，02:00 起为夏令时
    assert not st.is_china_dst(1986, 5, 4, 1, 59)
    assert st.is_china_dst(1986, 5, 4, 2, 0)
    # 结束日：01:59 仍是夏令时，02:00 拨回
    assert st.is_china_dst(1986, 9, 14, 1, 59)
    assert not st.is_china_dst(1986, 9, 14, 2, 0)
    # 区间中段与非夏令时年份
    assert st.is_china_dst(1986, 6, 1, 12, 0)
    assert not st.is_china_dst(1986, 5, 3, 12, 0)
    assert not st.is_china_dst(1986, 9, 15, 12, 0)
    assert st.china_dst_range(1992) is None
    assert not st.is_china_dst(1992, 6, 1, 12, 0)
    assert st.china_dst_range(1988) == (_dt.date(1988, 4, 17), _dt.date(1988, 9, 11))
    assert st.apply_dst(_dt.datetime(1990, 6, 1, 12, 0), True) == _dt.datetime(1990, 6, 1, 11, 0)


# ---------- 梅花：第二轮审查回归（时支数 + 体用生克） ----------
def test_meihua_hour_zhi_exhaustive():
    """时支数按标准时辰口径：子=23/0点，丑=1/2点，…，亥=21/22点。"""
    # hour → 时支数（子=1 … 亥=12）的权威对照表
    TABLE = {0: 1, 1: 2, 2: 2, 3: 3, 4: 3, 5: 4, 6: 4, 7: 5, 8: 5, 9: 6, 10: 6,
             11: 7, 12: 7, 13: 8, 14: 8, 15: 9, 16: 9, 17: 10, 18: 10, 19: 11,
             20: 11, 21: 12, 22: 12, 23: 1}
    for h, want in TABLE.items():
        got = ((h + 1) // 2) % 12 + 1
        assert got == want, f"hour={h}: 期望时支数 {want}，得到 {got}"
    # by_time 端到端：23 点与 0 点同为子时 → 起卦结果应完全一致；1 点为丑时 → 不同
    r23 = meihua.by_time(1984, 1, 1, 23)
    r0 = meihua.by_time(1984, 1, 1, 0)
    r1 = meihua.by_time(1984, 1, 1, 1)
    assert (r23.ben_gua, r23.moving_line) == (r0.ben_gua, r0.moving_line)
    assert (r1.ben_gua, r1.moving_line) != (r0.ben_gua, r0.moving_line)


def test_meihua_tiyong_exhaustive():
    """体用生克穷举 8×8=64 组，与独立五行生克表对照（回归「体克用/用克体反转」）。"""
    wx = meihua.GUA_WUXING
    KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
    SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
    for u in meihua.XIAN_TIAN:
        for t in meihua.XIAN_TIAN:
            ux, tx = wx[u], wx[t]
            if ux == tx:
                exp = "比和"
            elif SHENG[ux] == tx:
                exp = "用生体"
            elif SHENG[tx] == ux:
                exp = "体生用"
            elif KE[ux] == tx:
                exp = "用克体"
            else:
                exp = "体克用"
            got, _ = meihua._interact(u, t)
            assert got == exp, f"用{u}({ux}) 体{t}({tx})：期望 {exp}，得到 {got}"


# ---------- 称骨 ----------
def test_chenggu_basic():
    """甲子年 正月 初一 子时 = 12+6+5+16 = 39 钱 = 三两九。"""
    r = chenggu.calc("甲子", 1, 1, "子")
    assert r.total_qian == 39
    assert r.total_str == "三两九钱"
    assert r.verdict.startswith("此命终身运不通")


def test_chenggu_tables_integrity():
    assert len(chenggu.YEAR_WEIGHT) == 60
    assert len(chenggu.MONTH_WEIGHT) == 12
    assert len(chenggu.DAY_WEIGHT) == 30
    assert len(chenggu.HOUR_WEIGHT) == 12
    # 全部 60 甲子都在表内
    from fortune.core.model import GAN, ZHI
    for i in range(60):
        gz = GAN[i % 10] + ZHI[i % 12]
        assert gz in chenggu.YEAR_WEIGHT, gz
    # 判词表覆盖 2两1 ~ 7两2 的 52 档
    assert set(chenggu.VERDICT) == set(range(21, 73))
    # 通行表可达到的最大总骨重 = 19+18+18+16 = 71（七两一）
    assert max(chenggu.YEAR_WEIGHT.values()) + max(chenggu.MONTH_WEIGHT) + \
        max(chenggu.DAY_WEIGHT) + max(chenggu.HOUR_WEIGHT) == 71


def test_chenggu_liang_str():
    assert chenggu._qian_to_str(6) == "六钱"
    assert chenggu._qian_to_str(10) == "一两"
    assert chenggu._qian_to_str(39) == "三两九钱"


# ---------- 小六壬 ----------
def test_xiaoliuren_anchor():
    """正月初一子时 → 大安。"""
    r = xiaoliuren.calc(1, 1, "子")
    assert r.palace == "大安" and r.month_palace == "大安" and r.day_palace == "大安"


def test_xiaoliuren_rotation():
    """三月初七午时：月落速喜、日落速喜、时落速喜。"""
    r = xiaoliuren.calc(3, 7, "午")
    assert (r.month_palace, r.day_palace, r.palace) == ("速喜", "速喜", "速喜")


def test_xiaoliuren_tables():
    assert xiaoliuren.PALACES == ("大安", "留连", "速喜", "赤口", "小吉", "空亡")
    assert set(xiaoliuren.PALACE_INFO) == set(xiaoliuren.PALACES)
    # 十二时辰都能算
    for z in "子丑寅卯辰巳午未申酉戌亥":
        assert xiaoliuren.calc(1, 1, z).palace in xiaoliuren.PALACES


# ---------- 梅花易数 ----------
def test_meihua_64_names_unique():
    assert len(meihua.GUA64) == 64
    assert len(set(meihua.GUA64)) == 64


def test_meihua_known_gua():
    """卦名 = 上卦象+下卦象：(下乾,上坤)=地天泰；(下坤,上乾)=天地否；
    (下坎,上坎)=坎为水；(下坎,上艮)=山水蒙；(下乾,上巽)=天风姤；(下震,上坎)=雷水解。"""
    idx = lambda lo, up: meihua.XIAN_TIAN.index(lo) * 8 + meihua.XIAN_TIAN.index(up)
    assert meihua.GUA64[idx("乾", "坤")] == "地天泰"
    assert meihua.GUA64[idx("坤", "乾")] == "天地否"
    assert meihua.GUA64[idx("坎", "坎")] == "坎为水"
    assert meihua.GUA64[idx("坎", "艮")] == "山水蒙"
    assert meihua.GUA64[idx("乾", "巽")] == "风天小畜"    # 小畜：上巽下乾
    assert meihua.GUA64[idx("巽", "乾")] == "天风姤"      # 姤：上乾下巽
    assert meihua.GUA64[idx("震", "坎")] == "水雷屯"      # 屯：上坎下震
    assert meihua.GUA64[idx("坎", "震")] == "雷水解"      # 解：上震下坎
    # 抽查 King Wen 名实（上象+下象 规则）
    assert meihua.GUA64[idx("兑", "乾")] == "天泽履"    # 履：上乾下兑
    assert meihua.GUA64[idx("震", "兑")] == "泽雷随"    # 随：上兑下震
    assert meihua.GUA64[idx("兑", "震")] == "雷泽归妹"  # 归妹：上震下兑
    assert meihua.GUA64[idx("坤", "兑")] == "泽地萃"    # 萃：上兑下坤
    assert meihua.GUA64[idx("兑", "坤")] == "地泽临"    # 临：上坤下兑


def test_meihua_numbers():
    """1,1 起卦：乾为天，动爻 (1+1)%6=2，体用比和。"""
    r = meihua.by_numbers(1, 1)
    assert r.ben_gua == "乾为天"
    assert r.moving_line == 2
    assert r.bian_gua == "天火同人"   # 第2爻动：下乾(111)→(101)=离 → 上乾下离
    assert r.ti_gua == "乾" and r.yong_gua == "乾"
    assert r.relation == "比和"


def test_meihua_time():
    """农历 1984 年（甲子，年支数 1）正月初一 子时(0 点)：
    (1+1+1)%8=3→离 上卦；(1+1+1+1)%8=4→震 下卦；(1+1+1+1)%6=4 动爻。"""
    r = meihua.by_time(1984, 1, 1, 0)
    assert (r.upper, r.lower) == ("离", "震")
    assert r.ben_gua == "火雷噬嗑"
    assert r.moving_line == 4


# ---------- 六爻 ----------
def test_liuyao_qian_wei_tian():
    """六爻全少阳（三背两字各一? 用全 7 值）→ 乾为天，世6应3。"""
    c = from_coins([1, 1, 1, 1, 1, 1], "午", "甲子")
    assert c.ben_gua == "乾为天" and c.palace == "乾" and c.palace_wuxing == "金"
    assert c.shi == 6 and c.ying == 3
    # 纳甲
    assert [l.gan_zhi for l in c.lines] == ["甲子", "甲寅", "甲辰", "壬午", "壬申", "壬戌"]
    # 六亲：金宫：子水=子孙(金生水)、寅木=妻财(金克木)、辰土=父母(土生金)、
    #        午火=官鬼(火克金)、申金=兄弟、戌土=父母
    assert [l.liu_qin for l in c.lines] == ["子孙", "妻财", "父母", "官鬼", "兄弟", "父母"]
    # 六神：甲日 → 青龙起
    assert [l.liu_shen for l in c.lines] == ["青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武"]
    # 旬空：甲子日 → 戌亥
    assert c.xun_kong == ("戌", "亥")


def test_liuyao_moving():
    """初爻老阳（三背）→ 变卦天风姤；本卦仍为乾为天（世6应3）。"""
    c = from_coins([3, 1, 1, 1, 1, 1], "午", "甲子")
    assert c.ben_gua == "乾为天" and c.bian_gua == "天风姤"
    assert c.shi == 6 and c.ying == 3
    assert c.lines[0].is_moving and not c.lines[1].is_moving


def test_liuyao_coin_yin():
    """背=阴约定：三背=老阴(6)。"""
    c = from_coins([3, 1, 1, 1, 1, 1], "午", "甲子", coin_back="yin")
    assert c.lines[0].value == 6
    c2 = from_coins([3, 1, 1, 1, 1, 1], "午", "甲子", coin_back="yang")
    assert c2.lines[0].value == 9


def test_liuyao_tables_integrity():
    """八宫 64 卦无重名、世应 1-6、上下卦合法。"""
    from fortune.liuyao import PALACE_GUA, TRIGRAM_BITS
    names = []
    for palace, guas in PALACE_GUA.items():
        assert len(guas) == 8
        for name, up, low, shi, ying in guas:
            names.append(name)
            assert 1 <= shi <= 6 and 1 <= ying <= 6
            assert up in TRIGRAM_BITS and low in TRIGRAM_BITS
    assert len(set(names)) == 64
    assert len(set(PALACE_GUA)) == 8


def test_xun_kong_table():
    assert xun_kong("甲子") == ("戌", "亥")
    assert xun_kong("癸酉") == ("戌", "亥")
    assert xun_kong("甲戌") == ("申", "酉")
    assert xun_kong("癸巳") == ("午", "未")
    assert xun_kong("甲寅") == ("子", "丑")
    assert xun_kong("癸亥") == ("子", "丑")


def test_find_gua_all64():
    """find_gua 对全部 64 卦都能定位（含世应一致性抽查）。"""
    from fortune.liuyao import PALACE_GUA
    for palace, guas in PALACE_GUA.items():
        for name, up, low, shi, ying in guas:
            p2, n2, s2, y2 = find_gua(low, up)
            assert (p2, n2, s2, y2) == (palace, name, shi, ying)
