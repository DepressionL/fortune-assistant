"""真太阳时校正：经度差 + 均时差（Equation of Time）。

- 平太阳时是「平均太阳」的钟表时间（如北京时间即 120°E 的平太阳时）；
- 真太阳时 = 平太阳时 + 4×(经度−120°) 分钟 + 均时差 EoT（分钟）。

EoT 通过 astral（纯 Python、有测试覆盖）计算太阳正午求得：
    EoT = mean_noon_utc − solar_noon_utc
其中 mean_noon_utc = 12:00 UTC − 4×经度 分钟（平均太阳在本地正午的 UTC 时刻）。
符号约定（视太阳时 − 平太阳时）：11 月初 EoT ≈ +16.4 分钟、2 月中 ≈ −14.2 分钟，
用 Meeus《Astronomical Algorithms》/NOAA 发布的均时差表核验（见 tests/test_solar_time.py）。

中国历史夏令时（1986–1991）：钟面时间在每年 4 月第 2 个周日 02:00 至
9 月第 2 个周日 02:00 拨快 1 小时；该时段出生的钟面时间须先扣 1 小时。
（出处：国务院办公厅 1986–1991 年夏令时通知；见 research/solar_time.md）
"""
from __future__ import annotations

import datetime as _dt

from astral import Observer
from astral.sun import noon

__all__ = [
    "china_dst_range", "is_china_dst", "equation_of_time",
    "correct_true_solar", "apply_dst",
]

# 1986–1991 中国夏令时起止（当年 4 月第 2 个周日 / 9 月第 2 个周日）
_CHINA_DST = {
    1986: (_dt.date(1986, 5, 4), _dt.date(1986, 9, 14)),
    1987: (_dt.date(1987, 4, 12), _dt.date(1987, 9, 13)),
    1988: (_dt.date(1988, 4, 17), _dt.date(1988, 9, 11)),
    1989: (_dt.date(1989, 4, 16), _dt.date(1989, 9, 17)),
    1990: (_dt.date(1990, 4, 15), _dt.date(1990, 9, 16)),
    1991: (_dt.date(1991, 4, 14), _dt.date(1991, 9, 15)),
}


def china_dst_range(year: int) -> tuple[_dt.date, _dt.date] | None:
    """某年中国夏令时 (开始日, 结束日)，非夏令时年份返回 None。

    起止日均为「拨钟日」：开始日 02:00 起拨快，结束日 02:00 拨回。
    因此钟面时间落在 [开始日 02:00, 结束日 02:00) 内才是夏令时。"""
    return _CHINA_DST.get(year)


def is_china_dst(year: int, month: int, day: int,
                 hour: int = 0, minute: int = 0, second: int = 0) -> bool:
    """该公历时刻（钟面时间）是否处于中国夏令时（1986–1991）。

    夏令时区间为 [开始日 02:00, 结束日 02:00)：开始日 00:00–01:59 尚未拨快，
    结束日 00:00–01:59 仍未拨回。
    """
    rng = _CHINA_DST.get(year)
    if rng is None:
        return False
    t = _dt.datetime(year, month, day, hour, minute, second)
    start = _dt.datetime.combine(rng[0], _dt.time(2, 0))
    end = _dt.datetime.combine(rng[1], _dt.time(2, 0))
    return start <= t < end


def apply_dst(dt_: _dt.datetime, was_dst: bool) -> _dt.datetime:
    """钟面时间 → 标准时间。was_dst=True 表示钟面时间是夏令时，扣 1 小时。"""
    return dt_ - _dt.timedelta(hours=1) if was_dst else dt_


def equation_of_time(longitude_east: float, year: int, month: int, day: int) -> float:
    """均时差 EoT（分钟），符号约定 = 视太阳时 − 平太阳时。

    :param longitude_east: 东经度数（东为正）。
    """
    observer = Observer(latitude=0.0, longitude=longitude_east, elevation=0.0)
    date_ = _dt.date(year, month, day)
    t = noon(observer, date_)
    if t.tzinfo is None:
        t = t.replace(tzinfo=_dt.timezone.utc)
    else:
        t = t.astimezone(_dt.timezone.utc)
    mean_noon_utc = _dt.datetime(year, month, day, 12, 0, 0,
                                 tzinfo=_dt.timezone.utc) - _dt.timedelta(minutes=4 * longitude_east)
    return (mean_noon_utc - t).total_seconds() / 60.0


def true_solar_shift_parts(longitude_east: float, year: int, month: int,
                           day: int) -> tuple[float, float]:
    """真太阳时总偏移的两个分量：(经度差分钟, 均时差分钟)。

    经度差 = 4×(经度−120) 分钟（把北京时间 UTC+8 换算为地方平太阳时的差值，
    经度=120 时为 0）；均时差 EoT = 视太阳时 − 平太阳时。
    总偏移 = 经度差 + 均时差。供报告分项展示与断言用。"""
    lon_shift = 4.0 * (longitude_east - 120.0)
    eot = equation_of_time(longitude_east, year, month, day)
    return lon_shift, eot


def correct_true_solar(year: int, month: int, day: int,
                       hour: int, minute: int, second: int,
                       longitude_east: float) -> tuple[int, int, int, int, int, int, float]:
    """把标准时间钟面（如北京时间）校正为真太阳时。

    返回 (校正后 年,月,日,时,分,秒, 总偏移分钟数)。
    总偏移 = 4×(经度−120°) + EoT（分钟）。
    """
    base = _dt.datetime(year, month, day, hour, minute, second)
    lon_shift, eot = true_solar_shift_parts(longitude_east, year, month, day)
    shift = lon_shift + eot
    corrected = base + _dt.timedelta(minutes=shift)
    return (corrected.year, corrected.month, corrected.day,
            corrected.hour, corrected.minute, corrected.second, shift)
