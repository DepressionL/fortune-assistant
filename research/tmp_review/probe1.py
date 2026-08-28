# -*- coding: utf-8 -*-
"""Adversarial probes: relation zimaoyin, meihua hour branch, config switches, boundaries."""
import sys, os, traceback
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fortune.bazi import relation, shensha, strength
from fortune.bazi.chart import build as build_bazi
from fortune.config import FortuneConfig
from fortune.core.calendar import normalize
from fortune.core.model import BirthInfo
from fortune.misc import meihua
from fortune.liuyao import from_coins, find_gua, xun_kong

def make_chart(dt, gender="男", **kw):
    date_part, time_part = dt.split(" ")
    y, m, d = date_part.split("-")
    h, mi = time_part.split(":")
    birth = BirthInfo(calendar="solar", year=int(y), month=int(m), day=int(d),
                      hour=int(h), minute=int(mi), gender=gender, longitude=120.0)
    cfg = FortuneConfig(use_true_solar_time=False, **kw)
    nb = normalize(birth, cfg)
    return build_bazi(nb, gender, cfg), cfg

print("=== 1. 子卯刑 detection (子卯 present together) ===")
class FakePillar:
    def __init__(self, name, gz): self.name, self.gan_zhi = name, gz
    @property
    def gan(self): return self.gan_zhi[0]
    @property
    def zhi(self): return self.gan_zhi[1]
class FakeChart:
    def __init__(self, gzs):
        self.pillars = [FakePillar(n, gz) for n, gz in zip(("年柱","月柱","日柱","时柱"), gzs)]
    def gans(self): return [p.gan for p in self.pillars]
    def zhis(self): return [p.zhi for p in self.pillars]
    def pillar(self, name): return next(p for p in self.pillars if p.name == name)

# 子 卯 both present -> should trigger 子卯无礼之刑
fc = FakeChart(["甲子", "乙卯", "丙寅", "丁卯"])
hits = relation.scan(fc)
print("chart 子卯 present; relation hits:")
for h in hits:
    print("  ", h.name, h.values, h.positions)
print("  any '刑' hit? ", [h.name for h in hits if "刑" in h.name])

print()
print("=== 2. meihua by_time hour branch mapping (should match lunar_python 子=23-01) ===")
from lunar_python import Solar
for h in [0,1,2,3,22,23]:
    l = Solar.fromYmdHms(1990,6,15,h,30,0).getLunar()
    print(f"  hour={h}  lunar_python timeZhi={l.getTimeZhi()}  meihua nh={h//2+1} (子=1..亥=12)")

print()
print("=== 3. config switches actually take effect? ===")
# shensha_base
chart,_ = make_chart("2000-02-05 09:00")
d_hits = shensha.compute(chart, "day")
y_hits = shensha.compute(chart, "year")
print("  shensha day basis '天乙贵人':", [h.positions for h in d_hits if h.name=="天乙贵人"])
print("  shensha year basis '天乙贵人':", [h.positions for h in y_hits if h.name=="天乙贵人"])

# yongshen school
from fortune.bazi.yongshen import compute_yongshen
for school in ("wangshuai","tiaohou","tongguan","geju"):
    r = compute_yongshen(chart, school)
    print(f"  yongshen school={school}: school_prefix={r.school.split('（')[0]}")

# liuyao coin back
c1 = from_coins([3,1,1,1,1,1], "午", "甲子", "yang")
c2 = from_coins([3,1,1,1,1,1], "午", "甲子", "yin")
print("  liuyao coin_back yang line0 value:", c1.lines[0].value)
print("  liuyao coin_back yin line0 value:", c2.lines[0].value)

print()
print("=== 4. boundary / invalid inputs ===")
def probe_birth(**kw):
    b = BirthInfo(calendar="solar", year=1990, month=6, day=15, hour=12, **kw)
    try:
        nb = normalize(b, FortuneConfig(use_true_solar_time=False))
        return "OK"
    except Exception as e:
        return f"{type(e).__name__}: {e}"

for label, kw in [
    ("hour=24", dict(hour=24)),
    ("minute=60", dict(minute=60)),
    ("solar month=2 day=30", dict(month=2, day=30)),
    ("solar month=13", dict(month=13)),
    ("longitude=181", dict(longitude=181)),
    ("timezone=-13", dict(timezone=-13)),
    ("year=1899", dict(year=1899)),
    ("year=2100", dict(year=2100)),
    ("lunar invalid leap (month=-1, year=1990)", ),
]:
    if label.startswith("lunar"):
        b = BirthInfo(calendar="lunar", lunar_year=1990, lunar_month=-1, lunar_day=1)
        try:
            nb = normalize(b, FortuneConfig(use_true_solar_time=False))
            print(f"  lunar_month=-1 1990: OK -> {nb.lunar_year}年{abs(nb.lunar_month)}月")
        except Exception as e:
            print(f"  lunar_month=-1 1990: {type(e).__name__}: {e}")
    else:
        print(f"  {label}: {probe_birth(**kw)}")
