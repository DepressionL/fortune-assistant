"""六爻变爻纳甲口径与规则化断语测试。"""
from fortune.liuyao import from_coins
from fortune.liuyao.duanyu import duanyu


def test_bian_najia_uses_bian_gua_branches():
    """乾为天（下乾上乾）二三五爻动 → 火雷噬嗑（下震上离）：
    变爻地支按变卦纳甲取支（二爻寅→寅、三爻辰→辰、五爻申→未），
    六亲仍按本宫（乾金）论。此为本轮修复的口径（《增删卜易》装卦法）。"""
    c = from_coins([1, 3, 3, 1, 3, 1], "午", "甲午")  # 初少阳 二老阳 三老阳 四少阳 五老阳 上少阳
    assert c.ben_gua == "乾为天" and c.bian_gua == "火雷噬嗑"
    moving = [ln for ln in c.lines if ln.is_moving]
    assert [ln.no for ln in moving] == [2, 3, 5]
    # 变爻纳甲：二爻 甲寅→庚寅；三爻 甲辰→庚辰；五爻 壬申→己未
    by_no = {ln.no: ln for ln in c.lines}
    assert by_no[2].bian_gan_zhi == "庚寅" and by_no[2].bian_liu_qin == "妻财"
    assert by_no[3].bian_gan_zhi == "庚辰" and by_no[3].bian_liu_qin == "父母"
    assert by_no[5].bian_gan_zhi == "己未" and by_no[5].bian_liu_qin == "父母"
    # 非动爻变支仍按变卦纳甲记录（仅不展示）
    assert by_no[1].bian_gan_zhi == "庚子"


def test_duanyu_smoke():
    c = from_coins([1, 3, 3, 1, 3, 1], "午", "甲午")
    text = duanyu(c)
    assert "断语（规则化生成" in text
    assert "世爻" in text and "应爻" in text
    assert "应爻逢旬空" in text        # 应爻甲辰逢空（甲午日旬空辰巳）
    assert "回头生" in text            # 五爻壬申金动化己未土回头生
    assert "月建" in text and "日辰" in text
    assert "乾为健" in text            # 卦名释义引用


def test_duanyu_static_gua():
    """六爻安静（无动爻）→ 静卦断法提示。"""
    c = from_coins([1, 1, 1, 1, 1, 1], "午", "甲子")  # 全少阳 → 乾为天，无动
    text = duanyu(c)
    assert "六爻安静" in text


def test_shichi_quotes_verbatim_in_source():
    """六亲持世的原文引文必须逐字存在于《卜筮正宗》原文存档中（防引文漂移）。"""
    import pathlib
    import re

    import pytest

    from fortune.liuyao.duanyu import SHI_CHI

    src = pathlib.Path(__file__).resolve().parents[1] / "research" / "fetched" / "bushizhengzong.txt"
    if not src.exists():
        pytest.skip("《卜筮正宗》原文存档缺失，跳过")
    text = src.read_text(encoding="utf-8")
    text = re.sub(r"\s+", "", text)      # 诗体排版有换行，去空白后比对
    for qin, (_gloss, quotes) in SHI_CHI.items():
        for q in re.findall(r"「([^」]+)」", quotes):
            assert re.sub(r"\s+", "", q) in text, f"{qin} 引文不在原文存档中：{q}"
