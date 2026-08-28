"""六爻变爻纳甲口径与规则化断语测试。"""
from fortune.liuyao import from_coins
from fortune.liuyao.duanyu import duanyu


def test_bian_najia_uses_bian_gua_branches():
    """火山旅（下艮上离）三爻动 → 天水讼（下坎上乾）：
    变爻地支按变卦纳甲取支（初爻辰→寅、二爻午→辰、三爻申→午），
    六亲仍按本宫（离火）论。此为本轮修复的口径（《增删卜易》装卦法）。"""
    c = from_coins([2, 0, 3, 1, 0, 1], "申", "乙亥")  # 初少阴 二老阴 三老阳 四少阳 五老阴 上少阳
    assert c.ben_gua == "火山旅" and c.bian_gua == "天水讼"
    moving = [ln for ln in c.lines if ln.is_moving]
    assert [ln.no for ln in moving] == [2, 3, 5]
    # 变爻纳甲：二爻 丙午→戊辰；三爻 丙申→戊午；五爻 己未→壬申
    by_no = {ln.no: ln for ln in c.lines}
    assert by_no[2].bian_gan_zhi == "戊辰" and by_no[2].bian_liu_qin == "子孙"
    assert by_no[3].bian_gan_zhi == "戊午" and by_no[3].bian_liu_qin == "兄弟"
    assert by_no[5].bian_gan_zhi == "壬申" and by_no[5].bian_liu_qin == "妻财"
    # 非动爻变支仍按变卦纳甲记录（仅不展示）
    assert by_no[1].bian_gan_zhi == "戊寅"


def test_duanyu_smoke():
    c = from_coins([2, 0, 3, 1, 0, 1], "申", "乙亥")
    text = duanyu(c)
    assert "断语（规则化生成" in text
    assert "世爻" in text and "应爻" in text
    assert "回头克" in text            # 三爻申金动化午火回头克
    assert "旬空" in text              # 应爻酉金逢空（乙亥日旬空申酉）
    assert "月建" in text and "日辰" in text
    assert "旅为行旅" in text          # 卦名释义引用


def test_duanyu_static_gua():
    """六爻安静（无动爻）→ 静卦断法提示。"""
    c = from_coins([1, 1, 1, 1, 1, 1], "午", "甲子")  # 全少阳 → 乾为天，无动
    text = duanyu(c)
    assert "六爻安静" in text
