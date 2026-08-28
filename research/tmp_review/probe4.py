# -*- coding: utf-8 -*-
"""Probe 4: config effects (true solar, day_change, timezone) + ziwei engine."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from fortune.config import FortuneConfig
from fortune.core.calendar import normalize
from fortune.core.model import BirthInfo
from fortune.ziwei import chart as zc

def nb_for(dt, **cfg_kw):
    date_part, time_part = dt.split(" ")
    y, m, d = date_part.split("-")
    h, mi = time_part.split(":")
    b = BirthInfo(calendar="solar", year=int(y), month=int(m), day=int(d),
                  hour=int(h), minute=int(mi), gender="男", longitude=120.0)
    cfg = FortuneConfig(**cfg_kw)
    return normalize(b, cfg)

print("=== use_true_solar_time effect (longitude 120 => no lon shift, only EoT) ===")
nb_off = nb_for("1990-06-15 13:30", use_true_solar_time=False, longitude=120.0)
nb_on  = nb_for("1990-06-15 13:30", use_true_solar_time=True,  longitude=120.0)
print("  false solar_used:", nb_off.solar_ymdhms)
print("  true  solar_used:", nb_on.solar_ymdhms, "shift=", nb_on.true_solar_shift_min)

print("\n=== use_true_solar_time effect (longitude 105, ~ -60min lon) ===")
nb_105 = nb_for("1990-06-15 13:30", use_true_solar_time=True, longitude=105.0)
print("  lon104? 105:", nb_105.solar_ymdhms, "shift=", nb_105.true_solar_shift_min)

print("\n=== day_change_hour effect on 23:00 birth ===")
nb23 = nb_for("2000-02-29 23:30", use_true_solar_time=False, day_change_hour=23)
nb0  = nb_for("2000-02-29 23:30", use_true_solar_time=False, day_change_hour=0)
print("  day_change=23 day pillar:", nb23.eight_char.getDay())
print("  day_change=0  day pillar:", nb0.eight_char.getDay())

print("\n=== timezone field handling ===")
# config.timezone default 8; birth.timezone used in normalize. Check a non-8 birth.timezone.
def nb_tz(tz):
    b = BirthInfo(calendar="solar", year=1990, month=6, day=15, hour=13, minute=30,
                  gender="男", longitude=120.0, timezone=tz)
    return normalize(b, FortuneConfig(use_true_solar_time=False, timezone=tz))
print("  birth.timezone=8  ->", nb_tz(8).solar_ymdhms)
print("  birth.timezone=9  ->", nb_tz(9).solar_ymdhms, "(expect 12:30 local Beijing)")
print("  config.timezone is used by normalize? -> inspect")

print("\n=== ziwei end-to-end + geng_sihua switch + leap ===")
def zw(dt, **kw):
    date_part, time_part = dt.split(" ")
    y, m, d = date_part.split("-")
    h, mi = time_part.split(":")
    b = BirthInfo(calendar="solar", year=int(y), month=int(m), day=int(d),
                  hour=int(h), minute=int(mi), gender="男", longitude=120.0)
    cfg = FortuneConfig(use_true_solar_time=False, **kw)
    nb = normalize(b, cfg)
    return zc.build(nb, "男", cfg)

try:
    z = zw("2000-02-05 09:00")
    found = {}
    for p in z.palaces:
        for name, bright, m in p.major:
            if m: found[m] = name
    print("  2000-02-05 (庚辰) 忌星:", found.get("忌"))
    z2 = zw("2000-02-05 09:00", ziwei_geng_sihua="tianxiang")
    found2 = {}
    for p in z2.palaces:
        for name, bright, m in p.major:
            if m: found2[m] = name
    print("  庚辰 tianxiang 忌星:", found2.get("忌"))
except Exception as e:
    print("  ziwei err:", type(e).__name__, e)

# 闰月: 2023 闰二月? test mid_split vs as_month
try:
    z_a = zw("2023-03-25 12:00", ziwei_leap_month="as_month")
    z_m = zw("2023-03-25 12:00", ziwei_leap_month="mid_split")
    print("  as_month ming:", z_a.palaces[z_a.ming_index].name,
          " mid_split ming:", z_m.palaces[z_m.ming_index].name)
except Exception as e:
    print("  ziwei leap err:", type(e).__name__, e)

# 晚子时 23:00
try:
    z = zw("2000-02-29 23:30")
    print("  23:30 ziwei ok, ming:", z.palaces[z.ming_index].name, "shen:", z.palaces[z.shen_index].name)
except Exception as e:
    print("  23:30 ziwei err:", type(e).__name__, e)
