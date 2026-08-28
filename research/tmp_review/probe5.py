# -*- coding: utf-8 -*-
"""Probe 5: year range, DST 02:00 boundary, lunar leap, chenggu/section checks."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from fortune.config import FortuneConfig
from fortune.core.calendar import normalize
from fortune.core.model import BirthInfo
from fortune.core import solar_time as st
from fortune.misc import chenggu
import datetime as _dt

print("=== year range via lunar_python ===")
for y in [1900, 1899, 1850, 1950, 2000, 2024, 1]:
    b = BirthInfo(calendar="solar", year=y, month=6, day=15, hour=12)
    try:
        nb = normalize(b, FortuneConfig(use_true_solar_time=False))
        print(f"  year={y} -> OK 年柱={nb.eight_char.getYear()}")
    except Exception as e:
        print(f"  year={y} -> {type(e).__name__}: {e}")

print("\n=== DST date-granularity (02:00 jump not modeled) ===")
print("  is_china_dst(1986,5,4)=", st.is_china_dst(1986,5,4), "(whole day marked)")
print("  A birth 1986-05-04 01:30 is actually BEFORE the 02:00 spring-forward")
# normalize a birth at 1986-05-04 01:30 with is_dst=True
b = BirthInfo(calendar="solar", year=1986, month=5, day=4, hour=1, minute=30, is_dst=True)
nb = normalize(b, FortuneConfig(use_true_solar_time=False))
print("  normalize(1986-05-04 01:30, is_dst=True) ->", nb.solar_ymdhms, "(expect 00:30 if 02:00 boundary honored)")

print("\n=== validate() boundary messages are bare asserts ===")
try:
    FortuneConfig(day_change_hour=12).validate()
except AssertionError as e:
    print("  day_change_hour=12 -> AssertionError:", repr(str(e)))

print("\n=== chenggu max total / verdict reachability ===")
mx = max(chenggu.YEAR_WEIGHT.values()) + max(chenggu.MONTH_WEIGHT) + max(chenggu.DAY_WEIGHT) + max(chenggu.HOUR_WEIGHT)
print("  max reachable total =", mx)
print("  verdict keys count =", len(chenggu.VERDICT), "range=", min(chenggu.VERDICT), "-", max(chenggu.VERDICT))
print("  72 in VERDICT?", 72 in chenggu.VERDICT, "(unreachable since max=", mx, ")")

print("\n=== ziwei time_index 23 (晚间子) works end to end ===")
from fortune.ziwei import chart as zc
b = BirthInfo(calendar="solar", year=2000, month=2, day=29, hour=23, minute=30)
nb = normalize(b, FortuneConfig(use_true_solar_time=False))
try:
    z = zc.build(nb, "男", FortuneConfig(use_true_solar_time=False))
    print("  ziwei 2000-02-29 23:30 OK, ming=", z.palaces[z.ming_index].name)
except Exception as e:
    print("  ziwei 23:30 err:", type(e).__name__, e)

print("\n=== x_iztro leap note: lunar month for 2023 (leap) ===")
for dt in ["2023-03-25 12:00", "2023-04-20 12:00"]:
    date_part, time_part = dt.split(" "); y,m,d = date_part.split("-"); h = time_part.split(":")[0]
    b = BirthInfo(calendar="solar", year=int(y), month=int(m), day=int(d), hour=int(h))
    nb = normalize(b, FortuneConfig(use_true_solar_time=False))
    print(f"  solar {dt} -> lunar {nb.lunar_year}年{('闰' if nb.lunar_month<0 else '')}{abs(nb.lunar_month)}月{nb.lunar_day}日")
