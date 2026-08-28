# -*- coding: utf-8 -*-
"""真太阳时·均时差(EoT) 验证脚本。依赖: python -m pip install astral"""
import math, sys
try:  # Windows GBK 控制台兜底：以 UTF-8 输出，避免中文/符号报错
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
from datetime import datetime, timezone
from astral import Observer
from astral.sun import sun

LAT, LON = 39.9042, 116.4074  # 北京（经度不影响 EoT，可任换）

def eot_noaa(date):
    """NOAA/Meeus 均时差（分钟）。EoT = 视太阳时 − 平太阳时。"""
    N = date.timetuple().tm_yday
    gamma = 2 * math.pi / 365.0 * (N - 1)          # 取该日正午
    eq = (0.000075 + 0.001868 * math.cos(gamma)
          - 0.032077 * math.sin(gamma)
          - 0.014615 * math.cos(2 * gamma)
          - 0.040849 * math.sin(2 * gamma))
    return 229.18 * eq

def eot_astral(date):
    """用 astral 太阳正午求 EoT = 12:00 − 当地平太阳时(正午)。"""
    obs = Observer(latitude=LAT, longitude=LON)
    noon = sun(obs, date)['noon'].astimezone(timezone.utc)
    t = noon.hour + noon.minute / 60.0 + noon.second / 3600.0 + noon.microsecond / 3600e6
    lm = (t + LON / 15.0) % 24.0
    h = 12.0 - lm
    if h > 12: h -= 24
    if h < -12: h += 24
    return h * 60.0

if __name__ == "__main__":
    cases = [(2024, 2, 14, '参考 -14'), (2024, 11, 3, '参考 +16'), (2024, 4, 15, '参考 ~0'),
             (2024, 6, 13, '参考 ~0'), (2024, 9, 1, '参考 ~0'), (2024, 1, 15, -9.0),
             (2024, 3, 15, -8.9), (2024, 5, 15, 3.6), (2024, 7, 15, -6.0),
             (2024, 8, 15, -4.5), (2024, 10, 15, 14.3), (2024, 12, 15, 4.9)]
    print(f"{'日期':<12}{'astral':>8}{'NOAA':>8}{'参考表':>9}")
    for y, m, d, ref in cases:
        dt = datetime(y, m, d)
        a = eot_astral(dt); n = eot_noaa(dt)
        r = f"{ref:>6}" if isinstance(ref, str) else f"{ref:>6.1f}"
        print(f"{y}-{m:02d}-{d:02d}  {a:8.2f}{n:8.2f}{r:>9}")
    # 断言锚点
    assert abs(eot_astral(datetime(2024, 2, 14)) + 14.2) < 0.5
    assert abs(eot_astral(datetime(2024, 11, 3)) - 16.4) < 0.5
    print("\n断言通过：2/14约-14.2、11/3约+16.4 均满足。")
