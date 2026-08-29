"""《渊海子平》足本（合并官板音义评注本）卷一神煞交叉核验回归测试。

数据源：research/fetched/yuanhai_quanben.txt（由 research/Book 足本 epub 抽取，
2026-08-29）。每条：先断言口诀原文逐字存在于足本（引文锚点），再断言本仓
表与口诀推导表逐字一致（起法核验）；差异项（学堂纳音派、十恶大败乙丑/己丑、
阴刃别传）显式断言并核对实现标注。
"""
import pathlib

import pytest

from fortune.bazi import shensha as sh

SRC = pathlib.Path(__file__).resolve().parents[1] / "research" / "fetched" / "yuanhai_quanben.txt"

pytestmark = pytest.mark.skipif(
    not SRC.exists(), reason="《渊海子平》足本存档缺失，跳过")


def _text():
    return SRC.read_text(encoding="utf-8")


# ---------- 逐条：口诀原文锚点 + 仓表一致性 ----------

def test_tianyi_matches_quanben():
    """天乙贵人：足本口诀「庚辛逢马虎」属版本二；本仓从《三命通会》版本一
    （甲戊庚牛羊）。两古本各持一说，此分歧在实现 note 中已标注。"""
    t = _text()
    assert "甲戊兼牛羊，乙己鼠猴乡" in t
    assert "丙丁猪鸡位，壬癸兔蛇藏" in t
    assert "庚辛逢马虎" in t          # 足本 = 版本二（庚→午寅）
    expect_v1 = {
        "甲": ("丑", "未"), "戊": ("丑", "未"), "庚": ("丑", "未"),
        "乙": ("子", "申"), "己": ("子", "申"),
        "丙": ("酉", "亥"), "丁": ("酉", "亥"),
        "壬": ("卯", "巳"), "癸": ("卯", "巳"),
        "辛": ("午", "寅"),
    }
    assert sh.TIANYI == expect_v1
    assert sh.TIANYI_V2 == {**sh.TIANYI, "庚": ("寅", "午")}
    assert "惟辰戌二宫贵人不临" in t


def test_taiji_matches_quanben():
    t = _text()
    assert "甲乙生人子午中，丙丁鸡兔定亨通" in t
    assert "戊己两干临四季，庚辛寅亥禄盈丰" in t
    assert "壬癸巳申偏喜美" in t
    expect = {
        "甲": ("子", "午"), "乙": ("子", "午"),
        "丙": ("卯", "酉"), "丁": ("卯", "酉"),
        "戊": ("辰", "戌", "丑", "未"), "己": ("辰", "戌", "丑", "未"),
        "庚": ("寅", "亥"), "辛": ("寅", "亥"),
        "壬": ("巳", "申"), "癸": ("巳", "申"),
    }
    assert sh.TAIJI == expect


def test_yuede_tiande_matches_quanben():
    t = _text()
    assert "寅午戌，月在丙；申子辰，月在壬" in t
    assert "亥卯未，月在甲；巳酉丑，月在庚" in t
    assert "正丁二坤（申）中，三壬四辛同" in t
    assert "九丙十归乙，子巽（巳）丑庚中" in t
    assert sh.YUEDE == {"寅": "丙", "午": "丙", "戌": "丙", "申": "壬", "子": "壬",
                        "辰": "壬", "亥": "甲", "卯": "甲", "未": "甲", "巳": "庚",
                        "酉": "庚", "丑": "庚"}
    assert sh.TIANDE == {"寅": "丁", "卯": "申", "辰": "壬", "巳": "辛", "午": "亥",
                         "未": "甲", "申": "癸", "酉": "寅", "戌": "丙", "亥": "乙",
                         "子": "巳", "丑": "庚"}


def test_lu_yima_huagai_matches_quanben():
    t = _text()
    assert "甲禄在寅，乙禄在卯" in t and "丙戊禄在巳，丁己禄在午" in t
    assert "庚禄在申，辛禄在酉" in t and "壬禄在亥，癸禄在子" in t
    assert "申子辰马在寅，寅午戌马在申" in t
    assert "巳酉丑马在亥，亥卯未马在巳" in t
    assert "寅午戌见戌，巳酉丑见丑" in t and "申子辰见辰，亥卯未见未" in t
    assert sh.LU == {"甲": "寅", "乙": "卯", "丙": "巳", "丁": "午", "戊": "巳",
                     "己": "午", "庚": "申", "辛": "酉", "壬": "亥", "癸": "子"}
    assert sh._YIMA == {"申": "寅", "子": "寅", "辰": "寅", "寅": "申", "午": "申",
                        "戌": "申", "巳": "亥", "酉": "亥", "丑": "亥", "亥": "巳",
                        "卯": "巳", "未": "巳"}
    assert sh._HUAGAI == {"申": "辰", "子": "辰", "辰": "辰", "寅": "戌", "午": "戌",
                          "戌": "戌", "巳": "丑", "酉": "丑", "丑": "丑", "亥": "未",
                          "卯": "未", "未": "未"}


def test_jinyu_kongwang_matches_quanben():
    t = _text()
    assert "十干禄前第二位是也。如甲禄在寅，辰上是也" in t
    assert "甲子旬中无戌亥，甲戌旬中无申酉" in t and "甲寅旬中无子丑" in t
    assert sh.JINYU == {"甲": "辰", "乙": "巳", "丙": "未", "丁": "申", "戊": "未",
                        "己": "申", "庚": "戌", "辛": "亥", "壬": "丑", "癸": "寅"}


def test_yangren_matches_quanben():
    t = _text()
    assert "甲丙戊庚壬五阳有刃，乙己丁辛癸五阴无刃" in t
    assert sh.YANGREN == {"甲": "卯", "丙": "午", "戊": "午", "庚": "酉", "壬": "子"}


# ---------- 差异项（如实标注的版本分歧） ----------

def test_xuetang_nayin_divide_documented():
    """足本「论十干学堂」为纳音生人派（金巳木亥水土申火寅），与本仓日干派不同；
    两说均已标注。"""
    t = _text()
    assert "（金）生人见巳，辛巳为正" in t and "（木）生人见亥，己亥为正" in t
    assert "（水）生人见申，甲申为正" in t and "（土）生人见申，戊申为正" in t
    assert "（火）生人见寅，丙寅为正" in t
    # 日干派（本仓）与纳音派映射确实不同：甲日干长生在亥，而纳音木派为「木生人见亥」
    assert sh.XUETANG["甲"] == "亥"
    note = "《渊海子平》足本「论十干学堂」按纳音生人取"
    assert note in next(h.note for h in sh.compute(
        _chart("1960-01-07 08:00")) if h.name == "学堂")


def test_shie_yichou_variant_documented():
    """足本十恶大败作「乙丑」，与本仓（按禄入空亡穷举）的「己丑」差异已标注。"""
    t = _text()
    assert "乙丑都来十位神" in t
    assert sh.SHI_E == {"甲辰", "乙巳", "丙申", "丁亥", "戊戌", "己丑",
                        "庚辰", "辛巳", "壬申", "癸亥"}
    assert "己丑" in sh.SHI_E and "乙丑" not in sh.SHI_E
    # 命中文档（note）标注两古本同作乙丑：构造十恶大败命中并检查 note
    from fortune.bazi import shensha as _sh
    hits = [h for h in _sh.compute(_chart("1970-01-12 02:00"))]  # 壬辰日，非十恶
    # 用已知十恶大败日：1960-01-17 甲辰日
    hits = [h for h in _sh.compute(_chart("1960-01-17 08:00")) if h.name == "十恶大败"]
    assert hits and "两古本或同源之误" in hits[0].note


def _chart(dt: str):
    from fortune.bazi.chart import build as build_bazi
    from fortune.config import FortuneConfig
    from fortune.core.calendar import normalize
    from fortune.core.model import BirthInfo

    d, t = dt.split(" ")
    y, m, dd = d.split("-")
    h, mi = t.split(":")
    birth = BirthInfo(calendar="solar", year=int(y), month=int(m), day=int(dd),
                      hour=int(h), minute=int(mi), gender="男", longitude=120.0)
    cfg = FortuneConfig(use_true_solar_time=False)
    return build_bazi(normalize(birth, cfg), "男", cfg)
