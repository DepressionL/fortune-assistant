"""修复与改进计划（docs/修复与改进计划.md）的回归测试。

全部使用合成测试日期（随机样例，无任何真实个人信息）。
"""
import datetime as _dt

import pytest

from fortune.bazi import ditiansui as hz_mod
from fortune.bazi.chart import build as build_bazi
from fortune.bazi.yongshen import compute_yongshen
from fortune.comprehensive import run as comp_run
from fortune.config import FortuneConfig
from fortune.core import context as ctx_mod
from fortune.core.calendar import normalize
from fortune.core.model import BirthInfo
from fortune.misc import chenggu as chenggu_mod
from fortune.misc import meihua as meihua_mod
from fortune.misc import xiaoliuren as xlr_mod


def chart(dt: str, hh: int = 12, mi: int = 30, ts: bool = False, lng: float = 120.0):
    y, m, d = dt.split("-")
    birth = BirthInfo(calendar="solar", year=int(y), month=int(m), day=int(d),
                      hour=hh, minute=mi, gender="男", longitude=lng)
    cfg = FortuneConfig(use_true_solar_time=ts)
    return birth, cfg, build_bazi(normalize(birth, cfg), "男", cfg)


# ---------- F1 调候字段与原文一致 ----------

def test_f1_tiaohou_yong_from_xtiquan():
    _, _, c = chart("1987-02-07")  # 丁日寅月
    r = compute_yongshen(c, "tiaohou")
    assert r.yong_wuxing == ["金"]          # 正月丁：原文「姑用庚金」
    assert "用神五行：金" in str(r)
    assert "校注：底本此处「噼」当为「劈」" in str(r)   # 底本原字保留 + 校注

    _, _, c2 = chart("1990-06-15", 13, 30)   # 辛日午月
    r2 = compute_yongshen(c2, "tiaohou")
    assert r2.yong_wuxing == ["土", "水"]     # 五月辛：己壬兼用

    # 引文按句截断（不硬切字符）
    out = str(r2)
    assert "（节选，全文见 fortune/bazi/tiaohou_text.py）" in out


def test_f1_tiaohou_fallback_annotated():
    # 丙日亥月：XTIQUAN 无提炼（gan 空）→ 退回月令寒暖并标注「非原文结论」
    from fortune.bazi.tiaohou_text import XTIQUAN
    if XTIQUAN["丙"][10]["gan"] == "":
        found = None
        for d in range(1, 29):
            try:
                b, cfg, c = chart(f"1985-11-{d:02d}", 12, 30)
            except Exception:
                continue
            if c.day_master == "丙" and c.pillar("月柱").zhi in ("亥", "子"):
                found = c
                break
        if found is not None:
            r = compute_yongshen(found, "tiaohou")
            assert "非原文结论" in str(r)


# ---------- F2 格局比肩/劫财三小类 ----------

def test_f2_geju_renjian():
    _, _, c = chart("1987-03-26")            # 甲日卯月 → 羊刃
    r = compute_yongshen(c, "geju")
    assert r.yong_wuxing == ["金"]
    assert "羊刃格" in str(r) and "论阳刃" in str(r)


def test_f2_geju_jianlu():
    _, _, c = chart("1987-03-27")            # 乙日卯月 → 建禄
    r = compute_yongshen(c, "geju")
    assert r.yong_wuxing == ["土", "金"]
    assert "建禄格" in str(r) and "论建禄月劫" in str(r)


def test_f2_geju_yuejie():
    _, _, c = chart("1987-02-07")            # 丁亥日寅月、午时丙透 → 月劫
    r = compute_yongshen(c, "geju")
    assert r.yong_wuxing == ["金", "水"]
    assert "月劫格" in str(r)


def test_f2_geju_zhengyin_unchanged():
    _, _, c = chart("1987-02-07", 13, 30)    # 未时无丙透 → 正印格（旧行为不变）
    r = compute_yongshen(c, "geju")
    assert r.yong_wuxing == ["水", "火"]
    assert "正印" in str(r)


# ---------- F3 何知章成对与阈值 ----------

def test_f3_hezhi_pairs_and_thresholds():
    _, _, c = chart("1990-06-15", 13, 30)
    from fortune.bazi.strength import compute as sc
    st = sc(c)
    pairs = hz_mod.hezhi_pairs(hz_mod.hezhi(c, st))
    assert [p["dim"] for p in pairs] == ["财", "官", "喜忌", "元神"]
    for p in pairs:
        assert len(p["items"]) == 2
    # 阈值集中可配：大幅放宽后命中集变化
    loose = hz_mod.hezhi(c, st, {"fu_cai_tou": 0.0, "fu_cai_menhu": 0.0,
                                 "gui_guan": 0.0, "pin_cai": 9.9})
    by = {h.key: h.matched for h in loose}
    assert by["富"] is True


# ---------- I1 口径统一与 BirthContext ----------

def test_i1_misc_caliber():
    # 经度 90°（时区东六区边缘）真太阳时校正明显：钟表未时 → 校正后午时
    b, cfg, c = chart("1990-06-15", 13, 30, ts=True, lng=90.0)
    nb = normalize(b, cfg)
    xlr = xlr_mod.calc_from_birth(b, nb, use_true_solar=True)
    assert xlr.hour_zhi == "午"
    assert "真太阳" in xlr.caliber
    xlr_clock = xlr_mod.calc_from_birth(b, nb, use_true_solar=False)
    assert xlr_clock.hour_zhi == "未"
    assert "钟表" in xlr_clock.caliber

    mh = meihua_mod.by_birth(b, nb, use_true_solar=True)
    assert mh.caliber.startswith("时辰口径：真太阳时")
    cg = chenggu_mod.calc_from_birth(b, nb)
    assert cg.caliber.startswith("时辰口径：真太阳时")


def test_i1_context_check():
    b, cfg, _ = chart("1990-06-15", 13, 30)
    ctx = ctx_mod.build(b, cfg)
    assert ctx.eight_char[1].endswith("午")
    ctx_mod.check(ctx, year=1990, month=6, day=15, hour=13, minute=30)
    with pytest.raises(ValueError):
        ctx_mod.check(ctx, year=1991)          # 防错配


# ---------- I2 六爻占问聚焦与自动月建日辰 ----------

def test_i2_liuyao_topic_focus():
    from fortune.liuyao import from_coins
    from fortune.liuyao.duanyu import TOPIC_YONGSHEN, topic_focus
    chart6 = from_coins([2, 3, 1, 0, 3, 2], "申", "乙亥", "yang")
    out = topic_focus(chart6, "求财", "近期财运")
    assert "占题：求财「近期财运」" in out
    assert "用神妻财" in out
    assert topic_focus(chart6, "综合") == ""
    assert set(TOPIC_YONGSHEN) >= {"求财", "婚恋", "健康", "综合"}


def test_i2_liuyao_cli_date_derive():
    from typer.testing import CliRunner
    from fortune.cli import app
    r = CliRunner().invoke(app, ["liuyao", "--backs", "2,3,1,0,3,2",
                                 "--date", "2026-08-29", "--topic", "求财"])
    assert r.exit_code == 0, r.output
    assert "月建 申" in r.output and "日辰 乙亥" in r.output
    assert "自动推导" in r.output
    assert "用神聚焦" in r.output


# ---------- M3 综合聚合（确定性） ----------

def test_m3_comprehensive_deterministic():
    b, cfg, _ = chart("1988-02-22", 12, 30)
    cfg.liunian_anchor_year = 2026
    r1 = comp_run(b, cfg, anchor_year=2026)
    r2 = comp_run(b, cfg, anchor_year=2026)
    assert r1.markdown() == r2.markdown()          # 同输入字节级同输出
    assert set(r1.matrix) == set("wangshuai tiaohou tongguan geju bingyao".split())
    assert abs(sum(r1.consensus.values()) - 1.0) < 1e-9
    assert r1.conclusions
    assert any("用神" in c.dim for c in r1.conclusions)


def test_m3_comprehensive_with_liuyao():
    b, cfg, _ = chart("1988-02-22", 12, 30)
    r = comp_run(b, cfg, anchor_year=2026,
                 liuyao={"backs": [2, 3, 1, 0, 3, 2], "coin_back": "yang",
                         "date": "2026-08-29", "topic": "求财"})
    assert any("近运" in c.dim for c in r.conclusions)
    assert all(c.score >= 0.0 for c in r.conclusions)


# ---------- I4 配置与输出细节 ----------

def test_i4_config_validation():
    with pytest.raises(AssertionError):
        FortuneConfig(chenggu_gender="女").validate()   # 女版判词未核验，显式拒绝
    with pytest.raises(AssertionError):
        FortuneConfig(liunian_years=-1).validate()


def test_i4_bazi_meta_fields():
    from typer.testing import CliRunner
    from fortune.cli import app
    r = CliRunner().invoke(app, ["bazi", "-y", "1990", "-m", "6", "-d", "15",
                                 "-H", "13", "--no-true-solar", "--json",
                                 "--anchor-year", "2026"])
    assert r.exit_code == 0, r.output
    import json
    data = json.loads(r.output)
    assert "hezhi_pairs" in data and "liunian" in data
    assert "hezhi_thresholds" in data and "liunian_anchor" in data
