# -*- coding: utf-8 -*-
"""临时核验脚本：为魁罡/金神/日贵扫黄金日期（不入库）。"""
import datetime as dt

from fortune.bazi.chart import build as build_bazi
from fortune.config import FortuneConfig
from fortune.core.calendar import normalize
from fortune.core.model import BirthInfo

need = {"魁罡(庚辰/庚戌/壬辰/戊戌)": None, "金神(时柱乙丑)": None,
        "金神(时柱己巳)": None, "金神(时柱癸酉)": None,
        "日贵(丁酉/丁亥/癸巳/癸卯)": None}

d = dt.date(1970, 1, 1)
while d < dt.date(1990, 1, 1) and not all(need.values()):
    for h in (2, 10, 18):   # 丑时/巳时/酉时
        birth = BirthInfo(calendar="solar", year=d.year, month=d.month, day=d.day,
                          hour=h, minute=0, gender="男", longitude=120.0)
        cfg = FortuneConfig(use_true_solar_time=False)
        c = build_bazi(normalize(birth, cfg), "男", cfg)
        day = c.pillar("日柱").gan_zhi
        hour_zhi = c.pillar("时柱").gan_zhi
        if need["魁罡(庚辰/庚戌/壬辰/戊戌)"] is None and day in ("庚辰", "庚戌", "壬辰", "戊戌"):
            need["魁罡(庚辰/庚戌/壬辰/戊戌)"] = (str(d), h, c.gans(), c.zhis())
        if need["金神(时柱乙丑)"] is None and hour_zhi == "乙丑":
            need["金神(时柱乙丑)"] = (str(d), h, c.gans(), c.zhis())
        if need["金神(时柱己巳)"] is None and hour_zhi == "己巳":
            need["金神(时柱己巳)"] = (str(d), h, c.gans(), c.zhis())
        if need["金神(时柱癸酉)"] is None and hour_zhi == "癸酉":
            need["金神(时柱癸酉)"] = (str(d), h, c.gans(), c.zhis())
        if need["日贵(丁酉/丁亥/癸巳/癸卯)"] is None and day in ("丁酉", "丁亥", "癸巳", "癸卯"):
            need["日贵(丁酉/丁亥/癸巳/癸卯)"] = (str(d), h, c.gans(), c.zhis())
    d += dt.timedelta(days=1)

for k, v in need.items():
    print(k, "=>", v)
