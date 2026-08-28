"""香港天文台（HKO）官方《公历与农历日期对照表》回归测试。

数据：research/hko/hko_1901.txt、hko_2024.txt（来源：
https://www.hko.gov.hk/tc/gts/time/calendar/text/files/T<year>c.txt，
香港天文台官网发布，1901–2100 均有）。这是历法换算最权威的公开测试集之一。

验证内容（逐年逐日）：
1. 公历 → 农历 月/日（含闰月、月界）与 HKO 完全一致；
2. 节气所在日期与 HKO 完全一致（lunar_python 有精确时刻，此处按日比对）；
3. 年干支与表头一致（正月初一换年口径，HKO 表头「2024(甲辰-肖龍)」）。
"""
import pathlib
import re

import pytest

from lunar_python import Solar

HKO_DIR = pathlib.Path(__file__).resolve().parent.parent / "research" / "hko"

# 中文数字 → 数值（农历日）
_CN_NUM = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
           "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
_MONTH_CN = {"正月": 1, "二月": 2, "三月": 3, "四月": 4, "五月": 5, "六月": 6,
             "七月": 7, "八月": 8, "九月": 9, "十月": 10, "十一月": 11,
             "十二月": 12, "腊月": 12, "冬月": 11}
# lunar_python 节气键 → 中文名（HKO 用中文）
_JQ_NAME = {"DONG_ZHI": "冬至", "XIAO_HAN": "小寒", "DA_HAN": "大寒", "LI_CHUN": "立春",
            "YU_SHUI": "雨水", "JING_ZHE": "惊蛰", "CHUN_FEN": "春分", "QING_MING": "清明",
            "GU_YU": "谷雨", "LI_XIA": "立夏", "XIAO_MAN": "小满", "MANG_ZHONG": "芒种",
            "XIA_ZHI": "夏至", "XIAO_SHU": "小暑", "DA_SHU": "大暑", "LI_QIU": "立秋",
            "CHU_SHU": "处暑", "BAI_LU": "白露", "QIU_FEN": "秋分", "HAN_LU": "寒露",
            "SHUANG_JIANG": "霜降", "LI_DONG": "立冬", "XIAO_XUE": "小雪", "DA_XUE": "大雪"}


def parse_day(s: str) -> int:
    """农历日中文 → int。如 初一→1、廿三→23、三十→30。"""
    s = s.strip().replace("廿", "二十").replace("廿", "二十")
    if s.startswith("初"):
        return _CN_NUM[s[1]]
    if s.startswith("十"):
        return 10 + (_CN_NUM[s[1]] if len(s) > 1 else 0)
    if s.startswith("二十"):
        return 20 + (_CN_NUM[s[2]] if len(s) > 2 else 0)
    if s.startswith("三十"):
        return 30
    return _CN_NUM[s]


def parse_hko(year: int) -> list[dict]:
    """解析 HKO 文本 → [{solar:(y,m,d), lunar:(m,d,leap), jieqi:名称|None}]。"""
    path = HKO_DIR / f"hko_{year}.txt"
    assert path.exists(), f"缺少 HKO 数据：{path}（research/hko/）"
    text = path.read_text(encoding="utf-8-sig")
    # 表头年干支（1901: 「辛丑-肖牛」；2024: 「甲辰 - 肖龍」——空格有无两种排版）
    m = re.search(r"^(\d{4})\((\S+?)\s*-\s*肖", text)
    year_gz = m.group(2)

    # 第一遍：逐行解析日期/农历单元格/节气
    raw = []
    for line in text.splitlines()[3:]:
        line = line.rstrip()
        if not line.strip():
            continue
        cols = re.split(r"\s{2,}", line)
        if len(cols) < 3:
            continue
        date_cell, lunar_cell = cols[0].strip(), cols[1].strip()
        jieqi = cols[3].strip() if len(cols) > 3 else ""
        dm = re.match(r"(\d+)年(\d+)月(\d+)日", date_cell)
        if not dm:
            continue
        y, mo, d = map(int, dm.groups())
        raw.append({"solar": (y, mo, d), "cell": lunar_cell, "jieqi": jieqi or None})

    # 月名行（每月初一的单元格是月名；闰月为「閏X月」）→ 由前向后推月序；
    # 首个月初之前的行属于上一农历月（文件从年中/年初月中开始）。
    rows = []
    cur_month = None
    cur_leap = False
    first_month_row = next((r for r in raw
                            if r["cell"].lstrip("閏闰") in _MONTH_CN), None)
    if first_month_row is not None:
        first_idx = raw.index(first_month_row)
        fm = first_month_row["cell"].lstrip("閏闰")
        prev = _MONTH_CN[fm] - 1 or 12
        for r in raw[:first_idx]:
            rows.append({
                "solar": r["solar"],
                "lunar": (prev, parse_day(r["cell"]), False),
                "jieqi": r["jieqi"],
            })
        for r in raw[first_idx:]:
            cell = r["cell"].lstrip("閏闰")
            if r["cell"].startswith(("閏", "闰")) or cell in _MONTH_CN:
                cur_leap = r["cell"].startswith(("閏", "闰"))
            if cell in _MONTH_CN:
                cur_month = _MONTH_CN[cell]
                day = 1
            else:
                assert cur_month is not None, f"{r['solar']} 之前未出现月名"
                day = parse_day(cell)
            rows.append({"solar": r["solar"], "lunar": (cur_month, day, cur_leap),
                         "jieqi": r["jieqi"]})
    assert len(rows) in (365, 366), f"{year}: 解析出 {len(rows)} 行"
    return rows, year_gz


# HKO 用繁体（驚蟄/穀雨/小滿/芒種/處暑），统一转简体再比对
_T2S = str.maketrans({"驚": "惊", "蟄": "蛰", "穀": "谷", "滿": "满",
                      "種": "种", "處": "处", "氣": "气"})


def _jieqi_of(solar: Solar) -> str | None:
    """该公历日是否有节气（按日，简体名）。"""
    lunar = solar.getLunar()
    jq = lunar.getJieQiTable()
    for k, dt in jq.items():
        if (dt.getYear(), dt.getMonth(), dt.getDay()) == (solar.getYear(), solar.getMonth(), solar.getDay()):
            return _JQ_NAME.get(k, k)
    return None


@pytest.mark.parametrize("year", [1901, 2000, 2024, 2050])
def test_hko_lunar_conversion(year):
    rows, year_gz = parse_hko(year)
    mismatches = []
    for r in rows:
        solar = Solar.fromYmd(*r["solar"])
        lunar = solar.getLunar()
        got_m = lunar.getMonth()
        got_d = lunar.getDay()
        exp_m, exp_d, exp_leap = r["lunar"]
        # lunar_python 负数月 = 闰月
        got_leap = got_m < 0
        got_m = abs(got_m)
        if (got_m, got_d, got_leap) != (exp_m, exp_d, exp_leap):
            mismatches.append(
                f"{r['solar']}: 期望 农历{('闰' if exp_leap else '')}{exp_m}月{exp_d}日，"
                f"得到 {('闰' if got_leap else '')}{got_m}月{got_d}日")
    assert not mismatches, f"{year} 年共 {len(mismatches)} 处不一致，前 10 处：\n" + "\n".join(mismatches[:10])


@pytest.mark.parametrize("year", [1901, 2000, 2024, 2050])
def test_hko_jieqi_dates(year):
    rows, _ = parse_hko(year)
    bad = []
    for r in rows:
        solar = Solar.fromYmd(*r["solar"])
        got = _jieqi_of(solar)
        exp = r["jieqi"].translate(_T2S) if r["jieqi"] else None
        if (got or None) != (exp or None):
            bad.append(f"{r['solar']}: HKO 节气={exp!r}，lunar_python={got!r}")
    assert not bad, f"{year} 年节气不一致 {len(bad)} 处，前 10 处：\n" + "\n".join(bad[:10])


@pytest.mark.parametrize("year", [1901, 2000, 2024, 2050])
def test_hko_year_ganzhi(year):
    rows, year_gz = parse_hko(year)
    # 取年中一天核对农历年干支（避开正月初一/立春边界）
    mid = rows[len(rows) // 2]
    lunar = Solar.fromYmd(*mid["solar"]).getLunar()
    assert lunar.getYearInGanZhi() == year_gz, \
        f"{year}: HKO 表头年干支 {year_gz}，lunar_python 给出 {lunar.getYearInGanZhi()}"
