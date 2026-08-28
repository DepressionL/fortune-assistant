# -*- coding: utf-8 -*-
"""临时核验脚本：扫描日期为新神煞找黄金用例（不入库）。"""
import datetime as _dt

from fortune.bazi.chart import build as build_bazi
from fortune.config import FortuneConfig
from fortune.core.calendar import normalize
from fortune.core.model import BirthInfo

found = {
    "甲辰日(十恶大败)": None, "甲日+亥(学堂)": None, "甲日+寅(词馆)": None,
    "申子辰日支+寅(驿马)": None, "戌亥在柱(天罗)": None, "甲戊庚顺布": None,
    "乙丙丁顺布": None, "壬癸辛顺布": None,
}

d = _dt.date(1960, 1, 1)
while d < _dt.date(1980, 1, 1) and not all(found.values()):
    birth = BirthInfo(calendar="solar", year=d.year, month=d.month, day=d.day,
                      hour=8, minute=0, gender="男", longitude=120.0)
    cfg = FortuneConfig(use_true_solar_time=False)
    chart = build_bazi(normalize(birth, cfg), "男", cfg)
    gans, zhis = chart.gans(), chart.zhis()
    gz = chart.day_gan_zhi if hasattr(chart, "day_gan_zhi") else None
    if gz is None:
        gz = chart.pillar("日柱").gan_zhi
    s = "".join(gans)
    def order_ok(seq):
        idx = [s.find(c) for c in seq]
        return all(i >= 0 for i in idx) and idx == sorted(idx)
    if found["甲辰日(十恶大败)"] is None and gz == "甲辰":
        found["甲辰日(十恶大败)"] = (str(d), gans, zhis)
    if found["甲日+亥(学堂)"] is None and gans[2] == "甲" and "亥" in zhis:
        found["甲日+亥(学堂)"] = (str(d), gans, zhis)
    if found["甲日+寅(词馆)"] is None and gans[2] == "甲" and "寅" in zhis:
        found["甲日+寅(词馆)"] = (str(d), gans, zhis)
    if found["申子辰日支+寅(驿马)"] is None and zhis[2] in "申子辰" and "寅" in zhis:
        found["申子辰日支+寅(驿马)"] = (str(d), gans, zhis)
    if found["戌亥在柱(天罗)"] is None and ("戌" in zhis or "亥" in zhis):
        found["戌亥在柱(天罗)"] = (str(d), gans, zhis)
    if found["甲戊庚顺布"] is None and order_ok("甲戊庚"):
        found["甲戊庚顺布"] = (str(d), gans, zhis)
    if found["乙丙丁顺布"] is None and order_ok("乙丙丁"):
        found["乙丙丁顺布"] = (str(d), gans, zhis)
    if found["壬癸辛顺布"] is None and order_ok("壬癸辛"):
        found["壬癸辛顺布"] = (str(d), gans, zhis)
    d += _dt.timedelta(days=1)

for k, v in found.items():
    print(k, "=>", v if v else "未找到（扫描区间内）")
