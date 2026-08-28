"""输入模型：出生信息标准化。

支持公历/农历两种输入，统一转成公历后交给排盘引擎。
"""
from __future__ import annotations

from dataclasses import dataclass, field

# 五行
WUXING = ("木", "火", "土", "金", "水")
# 十天干/十二地支（用于校验与显示）
GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"


@dataclass
class BirthInfo:
    """出生信息（农历/公历其一）。

    - 公历输入：calendar="solar"，填 year/month/day/hour/minute/second。
    - 农历输入：calendar="lunar"，填 lunar_year/lunar_month/lunar_day（month 支持负数闰月，
      即 -N 表示闰 N 月，与 lunar_python 约定一致）。
    - gender：男/女。
    - longitude：出生地经度（东经为正），用于真太阳时校正。
    - timezone：时区（东为正，小时），默认 8。
    - is_dst：时间是否为夏令时钟面时间（中国 1986–1991）。
    """
    calendar: str = "solar"          # "solar" | "lunar"
    year: int = 1990                 # 公历年
    month: int = 1                   # 公历月
    day: int = 1                     # 公历日
    hour: int = 12                   # 时（0-23）
    minute: int = 0
    second: int = 0
    lunar_year: int = 0              # 农历年（calendar="lunar" 时用）
    lunar_month: int = 1             # 农历月，负数=闰月
    lunar_day: int = 1               # 农历日
    is_lunar_leap: bool = False      # 该农历月是否为闰月（与 lunar_month<0 二选一）
    gender: str = "男"               # "男" | "女"
    longitude: float = 120.0         # 东经为正
    timezone: float = 8.0
    is_dst: bool = False
    #: 附加说明（姓名等，仅用于报告抬头）
    note: str = ""

    def validate(self) -> None:
        """校验输入；非法值抛 AssertionError/ValueError 并带清晰信息。"""
        assert self.calendar in ("solar", "lunar"), \
            f"calendar 必须为 solar/lunar，得到 {self.calendar!r}"
        assert self.gender in ("男", "女"), f"gender 必须为 男/女，得到 {self.gender!r}"
        assert 0 <= self.hour <= 23 and 0 <= self.minute <= 59 and 0 <= self.second <= 59, \
            f"时间非法：{self.hour:02d}:{self.minute:02d}:{self.second:02d}"
        assert -180 <= self.longitude <= 180, f"经度须在 [-180,180]，得到 {self.longitude}"
        assert -12 <= self.timezone <= 14, f"时区须在 [-12,14]，得到 {self.timezone}"
        if self.calendar == "solar":
            assert 1 <= self.month <= 12 and 1 <= self.day <= 31, \
                f"公历月/日非法：{self.year}-{self.month}-{self.day}"
            import datetime as _dt
            try:
                _dt.date(self.year, self.month, self.day)
            except ValueError as e:
                raise ValueError(
                    f"非法公历日期：{self.year}-{self.month}-{self.day}（{e}）") from e
        else:
            assert 1 <= abs(self.lunar_month) <= 12 and 1 <= self.lunar_day <= 30, \
                f"农历月/日非法：{self.lunar_year}年{self.lunar_month}月{self.lunar_day}日"

    def time_str(self) -> str:
        return f"{self.hour:02d}:{self.minute:02d}:{self.second:02d}"

    def solar_str(self) -> str:
        return f"{self.year:04d}-{self.month:02d}-{self.day:02d} {self.time_str()}"


def is_yang_gan(gan: str) -> bool:
    """天干是否阳干。"""
    return GAN.index(gan) % 2 == 0


def is_yang_zhi(zhi: str) -> bool:
    """地支是否阳支。"""
    return ZHI.index(zhi) % 2 == 0
