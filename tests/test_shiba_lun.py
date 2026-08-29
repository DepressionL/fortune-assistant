"""《卜筮正宗》十八论 文本模块回归测试（双源逐字锁定）。"""
import pathlib
import re

import pytest

from fortune.liuyao import from_coins
from fortune.liuyao.duanyu import duanyu
from fortune.liuyao.shiba_lun_text import NOTES, PROVENANCE, QUOTES, SHIBA_LUN

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC_A = ROOT / "research" / "fetched" / "bushizhengzong.txt"
SRC_B = ROOT / "research" / "fetched" / "shidian_18lun_raw.txt"

EXPECTED = ["用神分类定例第一", "世应论用神第二", "用神问答第三", "原忌仇神论第四",
            "飞神正论第五", "伏神正传第六", "六兽评论第七", "四生逐位论第八",
            "月破论第九", "旬空论第十", "反吟卦定例第十一", "伏吟卦定例第十二",
            "旺相休囚論第十三", "合中帶剋論第十四", "合處逢冲，冲中逢合論第十五",
            "绝处逄生克处逄生论第十六", "变出进退神论第十七", "卦有验不验论第十八"]

# 識典古籍 OCR 底本的章（第 12–15 章）
OCR_KEYS = {"伏吟卦定例第十二", "旺相休囚論第十三",
            "合中帶剋論第十四", "合處逢冲，冲中逢合論第十五"}


def _norm(s):
    return re.sub(r"\s+", "", s)


def test_eighteen_chapters_present():
    assert list(SHIBA_LUN.keys()) == EXPECTED


@pytest.mark.skipif(not SRC_A.exists() or not SRC_B.exists(), reason="存档缺失")
def test_chapters_verbatim_in_sources():
    """章文须逐字（去空白）存在于对应来源存档：A=校注本，B=識典古籍 OCR。"""
    ta = _norm(SRC_A.read_text(encoding="utf-8"))
    tb = _norm(SRC_B.read_text(encoding="utf-8"))
    for key, text in SHIBA_LUN.items():
        src = tb if key in OCR_KEYS else ta
        assert _norm(text) in src, f"{key} 不在对应存档中"


def test_provenance_marks_ocr_chapters():
    for key in OCR_KEYS:
        assert "shidian_18lun_raw" in PROVENANCE[key] or "識典" in PROVENANCE[key]
    assert "bushizhengzong" in PROVENANCE["旬空论第十"]


def test_quotes_verbatim_in_chapters():
    """引用句须逐字存在于对应章文中。"""
    for key, qs in QUOTES.items():
        for q in qs:
            assert _norm(q) in _norm(SHIBA_LUN[key]), f"{key} :: {q}"


def test_misprint_and_ocr_notes():
    assert "第六" in NOTES["四生逐位论第八"]          # 底本误刻如实标注
    assert "句空" in NOTES["旺相休囚論第十三"]        # OCR 噪声如实标注


def test_duanyu_triggers_quotes():
    """随卦五爻动（酉化申退神）：月建午冲子=月破、辰巳旬空、化退神——
    应触发 月破论/旬空论/进退神论 引注。"""
    c = from_coins([1, 2, 2, 1, 3, 2], "午", "甲午")  # 泽雷随 五爻动 → 震为雷
    assert c.ben_gua == "泽雷随" and c.bian_gua == "震为雷"
    assert c.lines[4].gan_zhi[1] == "酉" and c.lines[4].bian_gan_zhi[1] == "申"
    text = duanyu(c)
    assert "十八论引注" in text
    assert "月破论第九" in text and "乃关因之所现也" in text
    assert "旬空论第十" in text and "乃神机发现于此也" in text
    assert "变出进退神论第十七" in text and "乃退神也" in text


def test_duanyu_fanyin_trigger():
    """巽为风初四爻动 → 乾为天：巽乾为方位对冲（卦变相冲）= 反吟卦，
    应触发反吟引注。"""
    c = from_coins([0, 1, 1, 0, 1, 1], "午", "甲午")
    assert c.ben_gua == "巽为风" and c.bian_gua == "乾为天"
    text = duanyu(c)
    assert "反吟卦定例第十一" in text and "卦变相冲也" in text


def test_duanyu_fuyin_trigger():
    """无妄二三五六爻动 → 大壮：六爻地支伏吟，应触发伏吟引注（識典 OCR 底本标注）。"""
    c = from_coins([1, 0, 0, 1, 3, 3], "午", "甲午")
    assert c.ben_gua == "天雷无妄" and c.bian_gua == "雷天大壮"
    text = duanyu(c)
    assert "伏吟卦定例第十二" in text and "伏吟卦有三" in text
    assert "識典" in text


def test_duanyu_wangxiang_trigger():
    """火山旅（静卦）：初爻辰、五爻未旺相（月建午生/合）而被日辰寅克
    → 应触发旺相休囚论「旺相者，暫時之用也」。"""
    c = from_coins([2, 2, 1, 1, 2, 1], "午", "甲寅")
    assert c.ben_gua == "火山旅"
    text = duanyu(c)
    assert "旺相休囚論第十三" in text
    assert "暫時之用也" in text


def test_duanyu_xiuqiu_trigger():
    """乾为天（静卦）：五爻申休囚（月建午克）而得日辰辰生
    → 应触发旺相休囚论「休囚者，待時之用也」。"""
    c = from_coins([1, 1, 1, 1, 1, 1], "午", "甲辰")
    text = duanyu(c)
    assert "旺相休囚論第十三" in text
    assert "待時之用也" in text


def test_duanyu_hezhongdaike_trigger():
    """乾为天初爻动 → 天风姤：子变丑（子丑合，克合）→ 应触发合中带克论。"""
    c = from_coins([3, 1, 1, 1, 1, 1], "午", "甲午")
    assert c.ben_gua == "乾为天" and c.bian_gua == "天风姤"
    text = duanyu(c)
    assert "合中帶剋論第十四" in text
    assert "合三剋七之分" in text


def test_duanyu_hezhongdaike_zuohe_trigger():
    """乾为天初爻动（子化丑），月建申/日辰申生扶旺相 → 应附「是作合論也」。"""
    c = from_coins([3, 1, 1, 1, 1, 1], "申", "甲申")
    text = duanyu(c)
    assert "合中帶剋論第十四" in text
    assert "是作合論也" in text


def test_duanyu_hezhongdaike_zuoke_trigger():
    """乾为天初爻动（子化丑），月建未/日辰己未克之休囚 → 应附「是作剋論也」。"""
    c = from_coins([3, 1, 1, 1, 1, 1], "未", "己未")
    text = duanyu(c)
    assert "合中帶剋論第十四" in text
    assert "是作剋論也" in text
