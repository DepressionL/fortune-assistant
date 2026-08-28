# -*- coding: utf-8 -*-
"""Probe 2: clean zimaoyin case, meihua by_time impact, boundary inputs."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from fortune.bazi import relation
from fortune.misc import meihua
from fortune.config import FortuneConfig
from fortune.core.calendar import normalize
from fortune.core.model import BirthInfo

class FP:
    def __init__(self, name, gz): self.name, self._gz = name, gz
    @property
    def gan(self): return self._gz[0]
    @property
    def zhi(self): return self._gz[1]
    @property
    def gan_zhi(self): return self._gz
class FC:
    def __init__(self, gzs):
        self.pillars = [FP(n, gz) for n, gz in zip(("年柱","月柱","日柱","时柱"), gzs)]
    def gans(self): return [p.gan for p in self.pillars]
    def zhis(self): return [p.zhi for p in self.pillars]
    def pillar(self, name): return next(p for p in self.pillars if p.name == name)

print("=== clean 子卯 (each once) ===")
for gzs in [("甲子","乙卯","丙寅","丁午"), ("甲子","乙卯","丙午","丁未"),
            ("甲子","乙丑","丙卯","丁午")]:
    hits = relation.scan(FC(list(gzs)))
    print(f"  zhis={[g[1] for g in gzs]} -> 刑 hits:", [ (h.name,h.values) for h in hits if '刑' in h.name])

print()
print("=== meihua by_time with odd hour: does it differ from standard? ===")
# Compare meihua upper/lower for hour=1 vs a 'correct' 丑(2) branch
r = meihua.by_time(1984, 1, 1, 1)
print("  by_time(1984,1,1, hour=1): upper/lower/moving =", r.upper, r.lower, r.moving_line, " ben=", r.ben_gua)
# If hour=1 wer treated as 丑(2): s=1+1+1=3; up=3; down=(3+2)%8=5; mv=(3+2)%6=5
# => NUM_TO_IDX[3]=离 upper, NUM_TO_IDX[5]=坎 lower -> 火水未济, mv=5
print("  for comparison, correct 丑(2) branch would give 上离下坎 & mv=5")

print()
print("=== boundary / invalid inputs ===")
def probe(**kw):
    defaults = dict(year=1990, month=6, day=15, hour=12)
    defaults.update(kw)
    b = BirthInfo(calendar="solar", **defaults)
    try:
        normalize(b, FortuneConfig(use_true_solar_time=False))
        return "OK"
    except Exception as e:
        return f"{type(e).__name__}: {e}"

for label, kw in [
    ("hour=24", dict(hour=24)),
    ("minute=60", dict(minute=60)),
    ("month=2 day=30", dict(month=2, day=30)),
    ("month=13", dict(month=13)),
    ("day=0", dict(day=0)),
    ("longitude=181", dict(longitude=181)),
    ("longitude=-181", dict(longitude=-181)),
    ("timezone=-13", dict(timezone=-13)),
    ("timezone=15", dict(timezone=15)),
    ("year=1899", dict(year=1899)),
    ("year=2100", dict(year=2100)),
    ("year=1", dict(year=1)),
]:
    print(f"  {label}: {probe(**kw)}")

print()
print("=== lunar invalid leap ===")
for ly, lm in [(1990, -1), (1990, -13), (1990, 1), (1985, -4)]:
    b = BirthInfo(calendar="lunar", lunar_year=ly, lunar_month=lm, lunar_day=1)
    try:
        nb = normalize(b, FortuneConfig(use_true_solar_time=False))
        print(f"  lunar {ly} month={lm} day=1 -> OK (lunar {nb.lunar_year}年{('闰' if nb.lunar_month<0 else '')}{abs(nb.lunar_month)}月{nb.lunar_day}日)")
    except Exception as e:
        print(f"  lunar {ly} month={lm} day=1 -> {type(e).__name__}: {e}")

print()
print("=== lunar_python crosscheck for meihua lunar-year branch (1984=甲子->子=1) ===")
print("  by_time(1990,...) year branch number =", (1990-4)%12+1, " (1990庚午=午=7)")
