"""大六壬起课回归测试：九宗门黄金用例 + 引文逐字锁定 + 天将/遁干/六亲/行年。"""
import pathlib
import re

import pytest

from fortune.liuren import (CHONG, GAN_JI, GUI_REN, XING, YUE_JIANG,
                            dun_gan_bu, liu_qin, month_jiang, qike,
                            qike_full, tian_jiang_bu, xing_nian)
from fortune.liuren.duanyu import format_chart
from fortune.liuren.text import NOTES, QUOTES

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _norm(s):
    return re.sub(r"\s+", "", s)


# ============ 九宗门黄金用例（手算核验） ============

def test_jiugong_golden():
    cases = [
        # (日干支, 时支, 月将支, 三传, 课体)
        ("甲子", "子", "丑", ["辰", "巳", "午"], "重审课"),      # 一下贼上
        ("甲子", "子", "辰", ["辰", "申", "子"], "元首课"),      # 一上克下
        ("甲子", "子", "巳", ["子", "巳", "戌"], "知一课（比用）"),  # 下贼上多课取比
        ("甲子", "子", "寅", ["辰", "午", "申"], "涉害课"),      # 涉害复等
        ("丙寅", "子", "酉", ["亥", "申", "巳"], "蒿矢课"),      # 神遥克日
        ("戊辰", "子", "卯", ["亥", "寅", "巳"], "弹射课"),      # 日遥克神
        ("戊辰", "子", "丑", ["戌", "巳", "午"], "昴星课"),      # 阳仰酉上
        ("丁未", "子", "卯", ["申", "戌", "戌"], "八专课"),      # 两课无克
        ("甲子", "子", "子", ["寅", "巳", "申"], "伏吟课"),      # 刑传
        ("辛未", "子", "午", ["巳", "辰", "丑"], "返吟课（井栏射）"),  # 驿马初传
    ]
    for dz, shi, jiang, chuan, keti in cases:
        c = qike(dz, shi, jiang)
        assert c.ke_ti == keti, f"{dz} {shi}时 {jiang}将 → {c.ke_ti} != {keti}"
        assert c.san_chuan == chuan, f"{dz} {shi}时 {jiang}将 → {c.san_chuan} != {chuan}"


def test_qike_parts_consistent():
    """起课结构自洽：四课由天盘推出、三传中末由初传上神递推（贼克系）。"""
    c = qike("甲子", "卯", "亥")
    assert c.gan_shang == c.tian_pan[GAN_JI["甲"]]
    assert c.gan_yin == c.tian_pan[c.gan_shang]
    assert c.zhi_shang == c.tian_pan["子"]
    assert c.zhi_yin == c.tian_pan[c.zhi_shang]
    assert c.san_chuan[0] == "戌"          # 甲木下贼戌土 → 重审
    assert c.ke_ti == "重审课"


# ============ 天将/遁干/六亲/行年 ============

def test_guiren_day_night_and_order():
    c = qike("甲子", "子", "亥")           # 子时：昼贵起例（子时属夜，见下）
    tian_jiang_bu(c, "子")
    assert c.day_night == "夜"
    assert c.gui_ren_zhi == GUI_REN["甲"][1] == "未"
    # 夜贵未临地盘申（巳午未申酉戌）→ 逆布：贵人后一天后
    gui_lin = c.pan_tian["未"]
    assert gui_lin in "巳午未申酉戌" and not c.gui_shun
    assert c.tian_jiang[gui_lin] == "贵人"
    idx = "子丑寅卯辰巳午未申酉戌亥".index(gui_lin)
    assert c.tian_jiang["子丑寅卯辰巳午未申酉戌亥"[(idx + 1) % 12]] == "天后"
    c2 = qike("甲子", "午", "亥")          # 午时昼占
    tian_jiang_bu(c2, "午")
    assert c2.day_night == "昼"
    assert c2.gui_ren_zhi == GUI_REN["甲"][0] == "丑"
    gui_lin2 = c2.pan_tian["丑"]
    assert gui_lin2 in "巳午未申酉戌" and not c2.gui_shun   # 丑贵临午 → 逆布
    assert c2.tian_jiang[gui_lin2] == "贵人"


def test_dun_gan_and_xun_kong():
    c = qike("壬寅", "未", "亥")
    dun_gan_bu(c)
    assert c.xun_shou == "甲午"          # 壬寅在甲午旬
    assert c.xun_kong == ("辰", "巳")
    assert c.dun_gan["午"] == "甲" and c.dun_gan["寅"] == "壬"   # 旬遁十干轮布
    assert c.dun_gan["巳"] == "乙"


def test_liu_qin_rules():
    # 壬水日：金生水=父母、水生木=子孙、土克水=官鬼、水克火=妻财、水水=兄弟
    assert liu_qin("壬寅", "申") == "父母"
    assert liu_qin("壬寅", "卯") == "子孙"
    assert liu_qin("壬寅", "未") == "官鬼"
    assert liu_qin("壬寅", "午") == "妻财"
    assert liu_qin("壬寅", "亥") == "兄弟"


def test_xing_nian():
    assert xing_nian("寅", "男", 1) == "寅"
    assert xing_nian("寅", "男", 2) == "卯"
    assert xing_nian("寅", "女", 2) == "丑"


# ============ 月将（太阳过宫） ============

def test_month_jiang_boundaries():
    import datetime as dt
    # 1990-06-15：小满后夏至前 → 四月将传送申（小满后日躔实沈）
    jz, jname, jq = month_jiang(dt.datetime(1990, 6, 15, 12, 0))
    assert (jz, jname, jq) == ("申", "传送", "小满")
    # 1990-01-10：冬至后大寒前 → 大吉丑
    jz, jname, jq = month_jiang(dt.datetime(1990, 1, 10, 12, 0))
    assert (jz, jname, jq) == ("丑", "大吉", "冬至")
    # 1990-03-01：雨水后春分前 → 登明亥
    jz, jname, jq = month_jiang(dt.datetime(1990, 3, 1, 12, 0))
    assert (jz, jname, jq) == ("亥", "登明", "雨水")


def test_qike_full_smoke():
    c = qike_full(1990, 6, 15, 13, 30, gender="男", birth_zhi="丑", age=30)
    assert c.day_ganzhi == "辛亥"          # 公历 1990-06-15 = 辛亥日
    assert c.hour_zhi == "未"
    assert c.yue_jiang_name == "传送" and c.yue_jiang_zhi == "申"   # 小满后
    assert c.ke_ti == "元首课"             # 第四课上克下（丑土克子水）
    assert c.san_chuan == ["丑", "寅", "卯"]
    assert c.ben_ming == "丑"
    assert c.xing_nian == "午"     # 丑顺数 30 虚岁：ZHI[(1+29)%12]=午
    text = format_chart(c)
    assert "大六壬" in text and "三传" in text and "元首课" in text


# ============ 引文逐字锁定 ============

@pytest.mark.skipif(not (ROOT / "research" / "fetched" / "liurendaquan_1.txt").exists(),
                    reason="《六壬大全》存档缺失")
def test_quotes_verbatim_in_sources():
    s1 = _norm((ROOT / "research" / "fetched" / "liurendaquan_1.txt").read_text(encoding="utf-8"))
    s2 = _norm((ROOT / "research" / "fetched" / "liurendaquan_2.txt").read_text(encoding="utf-8"))
    juan1_keys = {"寄宫", "贼克", "比用", "涉害", "遥克", "昴星", "别责",
                  "八专", "八专2", "伏吟", "返吟"}
    for k in juan1_keys:
        assert _norm(QUOTES[k]) in s1, k
    for k in ("贵人顺逆", "贵人顺逆注", "贵人昼夜", "天将序", "天将吉凶",
              "月将亥", "月将子", "月将寅底本"):
        assert _norm(QUOTES[k]) in s2, k


def test_notes_mark_disputes():
    assert "大雪" in NOTES["月将寅"] and "小雪" in NOTES["月将寅"]
    assert "卯辰巳午未申酉" in NOTES["贵人昼夜分界"]


def test_basic_tables():
    assert YUE_JIANG["亥"] == "登明" and YUE_JIANG["子"] == "神后"
    assert GAN_JI["甲"] == "寅" and GAN_JI["癸"] == "丑"
    assert GUI_REN["庚"] == ("丑", "未") and GUI_REN["辛"] == ("午", "寅")
    assert XING["寅"] == "巳" and XING["子"] == "卯"
    assert CHONG["子"] == "午"
