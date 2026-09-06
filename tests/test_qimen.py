"""奇门遁甲排盘回归测试：局数歌诀、黄金用例、引文逐字锁定、多流派并算。"""
import pathlib
import re

import pytest

from fortune.qimen import (GONG_XING, JU_TABLE, bu_ju, day_yuan,
                           day_yuan_maoshan, day_yuan_zhirun, governing_jieqi,
                           men_pan_layout, zhengshou_anchor,
                           zhi_shi_gong_xunshou)
from fortune.qimen.duanyu import format_chart
from fortune.qimen.text import NOTES, QUOTES

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _norm(s):
    return re.sub(r"\s+", "", s)


def test_ju_table_against_song():
    """局数表与《秘笈大全》起例歌一致（抽查关键条目）。"""
    assert JU_TABLE["冬至"] == (1, 7, 4) and JU_TABLE["惊蛰"] == (1, 7, 4)
    assert JU_TABLE["小寒"] == (2, 8, 5) and JU_TABLE["大寒"] == (3, 9, 6)
    assert JU_TABLE["立春"] == (8, 5, 2) and JU_TABLE["雨水"] == (9, 6, 3)
    assert JU_TABLE["清明"] == (4, 1, 7) and JU_TABLE["谷雨"] == (5, 2, 8)
    assert JU_TABLE["芒种"] == (6, 3, 9)
    assert JU_TABLE["夏至"] == (9, 3, 6) and JU_TABLE["白露"] == (9, 3, 6)
    assert JU_TABLE["大暑"] == (7, 1, 4) and JU_TABLE["秋分"] == (7, 1, 4)
    assert JU_TABLE["大雪"] == (4, 7, 1) and JU_TABLE["寒露"] == (6, 9, 3)
    # 阳遁/阴遁分界
    assert bu_ju(1990, 12, 25, 12, 0).dun == "阳遁"    # 冬至后
    assert bu_ju(1990, 6, 25, 12, 0).dun == "阴遁"     # 夏至后


def test_mijidaquan_anchor_yang2():
    """《秘笈大全》金锚：阳遁二局甲子日乙丑时 → 值使死门加艮八，休门在坤二。"""
    c = bu_ju(1988, 1, 10, 1, 30)
    assert c.dun == "阳遁" and c.ju == 2 and c.yuan == "上元"
    assert c.jie_qi == "小寒"
    assert c.day_ganzhi == "甲子" and c.hour_ganzhi == "乙丑"
    assert c.zhi_fu_xing == "天芮" and c.zhi_shi_men == "死门"
    assert c.di_pan[2] == "戊" and c.di_pan[1] == "乙"   # 阳遁二局：戊起坤二…乙在坎一
    assert c.men_pan[2] == "休门"                        # 秘笈「休门飞到坤二宫」


def test_yang1_jiashi_fuyin():
    """阳遁一局甲子日甲子时 → 值符天蓬值使休门，全伏吟。"""
    c = bu_ju(1989, 1, 4, 0, 30)
    assert c.dun == "阳遁" and c.ju == 1 and c.yuan == "上元"
    assert c.jie_qi == "冬至"
    assert c.day_ganzhi == "甲子" and c.hour_ganzhi == "甲子"
    assert c.zhi_fu_xing == "天蓬" and c.zhi_shi_men == "休门"
    assert c.di_pan == {1: "戊", 2: "己", 3: "庚", 4: "辛", 5: "壬",
                        6: "癸", 7: "丁", 8: "丙", 9: "乙"}
    assert c.tian_pan == {g: GONG_XING[g] for g in range(1, 10)}
    assert c.fu_yin is True


def test_yin9_jiashi():
    """阴遁九局甲子日甲子时：值符天英值使景门；地盘戊起离九逆布。"""
    c = bu_ju(1985, 9, 22, 0, 30)
    assert c.dun == "阴遁" and c.ju == 9 and c.yuan == "上元"
    assert c.jie_qi == "白露"
    assert c.day_ganzhi == "甲子" and c.hour_ganzhi == "甲子"
    assert c.zhi_fu_xing == "天英" and c.zhi_shi_men == "景门"
    assert c.di_pan[9] == "戊" and c.di_pan[8] == "己" and c.di_pan[1] == "丁"
    assert c.tian_pan[9] == "天英"                       # 值符加时干（甲→旬首宫）
    assert c.men_pan[1] == "景门"                        # 值使景门加时支宫（子→坎一）


def test_di_pan_consistency_and_zhong_gong():
    """地盘九宫全排九仪奇；天禽在五宫（寄坤二）；门神不入中五。"""
    for dt in ((1990, 1, 15, 12, 0), (1990, 6, 25, 12, 0), (1990, 3, 1, 6, 0)):
        c = bu_ju(*dt)
        assert set(c.di_pan.values()) == set("戊己庚辛壬癸丁丙乙")
        assert len(c.di_pan) == 9
        assert c.tian_pan.get(5) is not None
        assert 5 not in c.men_pan and 5 not in c.shen_pan


def test_governing_jieqi():
    import datetime as dt
    assert governing_jieqi(dt.datetime(1990, 6, 15, 12, 0)) == "芒种"
    assert governing_jieqi(dt.datetime(1990, 12, 25, 12, 0)) == "冬至"
    assert governing_jieqi(dt.datetime(1990, 1, 10, 12, 0)) == "小寒"


def test_day_yuan():
    assert day_yuan("甲子") == "上元" and day_yuan("己卯") == "上元"
    assert day_yuan("甲寅") == "中元" and day_yuan("己亥") == "中元"
    assert day_yuan("甲辰") == "下元" and day_yuan("戊戌") == "下元"


# ---------- 多流派并算 ----------

def test_men_schools_both_computed():
    """门法两派并算：秘笈大全金锚（阳遁二局甲子日乙丑时）。
    门法①时支本位宫 → 休门在坤二（与「休门飞到坤二宫」互证）；
    门法②自旬首宫顺逆数地支 → 旬首宫(坤二)起子顺数一步至寅时支丑 → 值使落震三。"""
    c = bu_ju(1988, 1, 10, 1, 30)
    assert c.men_pan[2] == "休门"                       # 门法①（金锚）
    keys = [s["key"] for s in c.men_schools]
    assert keys == ["zhigong", "xunshou"]
    alt = c.men_schools[1]
    assert alt["zhi_shi_gong"] == 3                     # 坤二起子 → 顺数一步至丑 → 震三
    assert alt["men_pan"][3] == "死门" and alt["men_pan"][7] == "休门"
    assert c.men_pan_alt == alt["men_pan"]


def test_men_school_xunshou_jiashi_returns_ben_gong():
    """门法②六甲时（时支=旬首支）零步 → 门归本宫（与门法①同宫）。"""
    c = bu_ju(1989, 1, 4, 0, 30)                        # 阳一局甲子时
    assert c.men_schools[1]["zhi_shi_gong"] == c.zhi_fu_gong == 1
    assert c.men_pan_alt[1] == "休门"


def test_men_school_xunshou_yindun():
    """门法②阴遁逆数：阴九局甲子日壬申时（申时），旬首甲子，值符宫离九；
    八宫序逆排 [9,8,7,6,4,3,2,1]，自离九逆数八步（子…申）仍落离九；
    门法①时支申本位宫 = 坤二。"""
    c = bu_ju(1985, 9, 22, 15, 30)
    assert c.dun == "阴遁" and c.ju == 9
    assert c.hour_ganzhi == "壬申" and c.xun_shou == "甲子"
    assert c.men_schools[0]["zhi_shi_gong"] == 2        # 门法① 申 → 坤二
    assert c.men_schools[1]["zhi_shi_gong"] == 9        # 门法② 逆数八步 → 离九（值符宫）
    assert c.men_pan_alt[9] == "景门" and c.men_pan[2] == "景门"


def test_ju_schools_chaibu_maoshan():
    """三元定局两派并算：1988-01-11（小寒后第 5 日，乙丑日）。
    拆补法按日干支符头（丑 → 下元）→ 5 局；茅山法按交节日起五日一元 → 中元 8 局。"""
    c = bu_ju(1988, 1, 11, 12, 0)
    assert c.jie_qi == "小寒"
    keys = [s["key"] for s in c.ju_schools]
    assert keys == ["chaibu", "maoshan", "zhirun"]
    cb = c.ju_schools[0]
    ms = c.ju_schools[1]
    assert (cb["yuan"], cb["ju"]) == ("下元", 5)
    assert (ms["yuan"], ms["ju"]) == ("中元", 8)
    assert c.school == "chaibu" and c.ju == 5
    # 茅山法局不同 → 地盘不同（戊起艮八 / 拆补戊起中五）
    assert ms["di_pan"][8] == "戊" and cb["di_pan"][5] == "戊"
    # 每派都带两套门盘
    assert ms["men_pan_alt"] and cb["men_pan_alt"]


def test_day_yuan_maoshan():
    import datetime as dt
    from fortune.qimen import governing_jieqi_dt
    _, jq = governing_jieqi_dt(dt.datetime(1988, 1, 11, 12, 0))
    assert day_yuan_maoshan(dt.datetime(1988, 1, 11, 12, 0), jq) == "中元"


# ---------- 置闰/超神接气 ----------

def test_zhirun_chaoshen_1988_01_07():
    """置闰法·超神：1988-01-07（丙寅日），小寒 01-06；节前符头己未(01-05) → 超神。
    元 = 己未下元（base_days=2）→ 下元 5 局；与拆补（丙寅中元 8 局）不同。"""
    import datetime as dt
    from fortune.qimen import governing_jieqi_dt
    jq, jq_dt = governing_jieqi_dt(dt.datetime(1988, 1, 7, 12, 0))
    assert jq == "小寒"
    r = day_yuan_zhirun(dt.datetime(1988, 1, 7, 12, 0), jq, jq_dt)
    assert r["relation"] == "超神" and r["yuan"] == "下元"


def test_zhirun_jieqi_1988_01_10():
    """置闰法·接气：1988-01-10（甲子日，小寒 01-06 后）→ 节后遇符为接气；
    自节前符头己未(01-05)顺延 base_days=5 → 上元（金锚 2 局一致）。"""
    import datetime as dt
    from fortune.qimen import governing_jieqi_dt
    jq, jq_dt = governing_jieqi_dt(dt.datetime(1988, 1, 10, 12, 0))
    r = day_yuan_zhirun(dt.datetime(1988, 1, 10, 12, 0), jq, jq_dt)
    assert r["relation"] == "接气" and r["yuan"] == "上元"


def test_zhengshou_anchor_is_valid():
    """正授锚点：找到的日期必须是甲/己日且恰逢交节日。"""
    import datetime as dt
    from lunar_python import Lunar, Solar
    a = zhengshou_anchor(dt.datetime(2020, 6, 1, 12, 0))
    assert a is not None
    gz = Solar.fromYmd(a.year, a.month, a.day).getLunar().getDayInGanZhi()
    assert gz[0] in "甲己"
    # 该日应为某个节气交节日（逐表核验）
    from fortune.qimen import JU_TABLE
    hit = False
    for yy in (a.year - 1, a.year, a.year + 1):
        table = Lunar.fromYmdHms(yy, 6, 15, 12, 0, 0).getJieQiTable()
        for name, t in table.items():
            if name not in JU_TABLE or t is None:
                continue
            td = dt.datetime(t.getYear(), t.getMonth(), t.getDay(),
                              t.getHour(), t.getMinute(), t.getSecond())
            if td.date() == a.date():
                hit = True
    assert hit


def test_zhirun_variant_in_buju():
    """置闰法作为第三种三元派并入 bu_ju 的 ju_schools。"""
    c = bu_ju(1988, 1, 7, 12, 0)
    keys = [s["key"] for s in c.ju_schools]
    assert keys == ["chaibu", "maoshan", "zhirun"]
    zr = c.ju_schools[2]
    assert zr["yuan"] == "下元" and zr["ju"] == 5
    assert "超神" in zr["note"]


def test_men_layout_helper():
    """men_pan_layout：阳遁值使死门落三宫 → 死三、惊四、开六、休七…"""
    mp = men_pan_layout(True, 2, "死门", 3)
    assert mp == {3: "死门", 4: "惊门", 6: "开门", 7: "休门",
                  8: "生门", 9: "伤门", 1: "杜门", 2: "景门"}


@pytest.mark.skipif(not (ROOT / "research" / "fetched" / "奇门秘笈大全.txt").exists(),
                    reason="《奇门遁甲秘笈大全》存档缺失")
def test_quotes_verbatim_in_sources():
    mj = _norm((ROOT / "research" / "fetched" / "奇门秘笈大全.txt").read_text(encoding="utf-8"))
    yb = _norm((ROOT / "research" / "fetched" / "wikisource_yanbodiao sou.txt")
               .read_text(encoding="utf-8"))
    mj_keys = {"布仪", "符使", "局数阳", "局数阴", "天禽", "值使例", "值使例注",
               "值使数支", "置闰诀", "置闰过九", "正授", "九星", "八门", "八神阳",
               "八神阴", "八神替", "八神替2"}
    for k in mj_keys:
        assert _norm(QUOTES[k]) in mj, k
    for k in ("烟波布仪", "烟波符使"):
        assert _norm(QUOTES[k]) in yb, k


def test_notes_mark_disputes():
    assert "拆补" in NOTES["三元"] and "置闰" in NOTES["三元"] and "茅山" in NOTES["三元"]
    assert "九宫方位" in NOTES["值使"] and "顺逆数地支" in NOTES["值使"]


def test_cli_qimen():
    from typer.testing import CliRunner
    from fortune.cli import app
    r = CliRunner().invoke(app, ["qimen", "-y", "1989", "-m", "1", "-d", "4",
                                 "-H", "0", "-M", "30"])
    assert r.exit_code == 0, r.output
    assert "奇门遁甲" in r.output and "阳遁 1 局" in r.output
    assert "伏吟" in r.output


def test_report_smoke():
    c = bu_ju(1988, 1, 10, 1, 30)
    text = format_chart(c)
    assert "奇门遁甲" in text and "值符" in text and "死门" in text
