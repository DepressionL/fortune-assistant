# -*- coding: utf-8 -*-
"""双库八字排盘对照 —— 权威参考实现 (lunar_python 1.4.8 + sxtwl 2.0.7)

运行: .venv\\Scripts\\python.exe bazi_crosscheck.py
输出: 9 个基准日期的双库四柱 + lunar_python 大运/起运
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from lunar_python import Solar
from lunar_python.util import LunarUtil
import sxtwl

GAN = ["", "甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
ZHI = ["", "子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]


def gzstr(gz):
    """sxtwl 的 GZ 对象 (tg/dz 为 0 基索引) -> 干支字符串"""
    return GAN[gz.tg + 1] + ZHI[gz.dz + 1]


def lunar_chart(y, m, d, hh, mm, ss=0, gender=1, sect=2):
    """lunar_python 完整八字 + 大运"""
    solar = Solar.fromYmdHms(y, m, d, hh, mm, ss)          # 公历
    lunar = solar.getLunar()                               # 公历 -> 农历
    ec = lunar.getEightChar()                              # 八字对象
    ec.setSect(sect)                                       # 流派 1/2
    pillars = [ec.getYear(), ec.getMonth(), ec.getDay(), ec.getTime()]
    hide = [LunarUtil.ZHI_HIDE_GAN.get(p[1:]) for p in pillars]
    nayin = [LunarUtil.NAYIN.get(p) for p in pillars]
    yun = ec.getYun(gender, 1)                             # 运, sect1=3天折1年
    dy = [yun.getDaYun(10)[i] for i in range(1, 5)]        # 前4步大运
    return {
        "pillars": pillars, "hide": hide, "nayin": nayin,
        "forward": yun.isForward(),
        "start": (yun.getStartYear(), yun.getStartMonth(), yun.getStartDay(), yun.getStartHour()),
        "start_solar": yun.getStartSolar().toYmd() + " " + yun.getStartSolar().toYmdHms()[11:16],
        "start_age_xu": yun.getDaYun(10)[1].getStartAge(),
        "dayuns": [(x.getGanZhi(), x.getStartYear(), x.getEndYear(), x.getStartAge(), x.getEndAge()) for x in dy],
    }


def sxtwl_chart(y, m, d, hh):
    """sxtwl 四柱 (历法层)"""
    day = sxtwl.fromSolar(y, m, d)                         # 公历 -> 日(历法)
    return {
        "year": gzstr(day.getYearGZ(False)),   # 立春(按日)为年界
        "year_cny": gzstr(day.getYearGZ(True)),  # 正月初一为年界
        "month": gzstr(day.getMonthGZ()),
        "day": gzstr(day.getDayGZ()),
        "hour_zw": gzstr(day.getHourGZ(hh, True)),   # 早晚子时开
        "hour_nzw": gzstr(day.getHourGZ(hh, False)),  # 早晚子时关
    }


CASE = [
    ("2000-01-01 12:00 立春前", 2000, 1, 1, 12, 0),
    ("2000-02-04 18:00 立春当日20:40前", 2000, 2, 4, 18, 0),
    ("2000-02-05 09:00 立春后", 2000, 2, 5, 9, 0),
    ("1984-02-02 12:00", 1984, 2, 2, 12, 0),
    ("1990-06-15 13:30", 1990, 6, 15, 13, 30),
    ("2024-02-10 00:30 春节+早晚子时", 2024, 2, 10, 0, 30),
    ("1976-07-28 03:42", 1976, 7, 28, 3, 42),
    ("1949-10-01 15:00", 1949, 10, 1, 15, 0),
    ("2000-02-29 23:30 晚子时", 2000, 2, 29, 23, 30),
]

if __name__ == "__main__":
    for label, y, m, d, hh, mm in CASE:
        L = lunar_chart(y, m, d, hh, mm)
        S = sxtwl_chart(y, m, d, hh)
        print(f"\n### {label}")
        print(f"  lunar(近式) {L['pillars']}  藏干{L['hide']}  纳音{L['nayin']}")
        print(f"  sxtwl       年{S['year']} 月{S['month']} 日{S['day']} 时{S['hour_zw']}")
        print(f"  起运 {'顺' if L['forward'] else '逆'} {L['start']} -> {L['start_solar']}  虚岁{L['start_age_xu']}")
        print("  大运", L["dayuns"])
