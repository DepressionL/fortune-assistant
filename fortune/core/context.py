"""BirthContext —— 跨工具共享的历法事实上下文（工具联动层）。

定位：只共享「历法事实」（公历/农历/干支/节气边界/时支/真太阳时校正），
**绝不共享吉凶结论**——各术数独立计算，保持客观独立。

用法：
- 生成：fortune context -y 1990 -m 6 -d 15 -H 13 ... > ctx.json
- 消费：工具侧以 context 传入并做一致性校验（冲突即报错，防错配）。
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .calendar import NormalizedBirth, normalize
from ..config import FortuneConfig
from .model import BirthInfo

ZHI = "子丑寅卯辰巳午未申酉戌亥"


def _zhi_of_hour(hour: int) -> str:
    """钟点 → 时支（标准时辰口径）。"""
    return ZHI[((hour + 1) // 2) % 12]


@dataclass
class BirthContext:
    """归一化历法事实上下文（JSON 可序列化）。"""

    solar: str                      # 公历输入 YYYY-MM-DD HH:MM:SS
    gender: str
    longitude: float
    timezone: float
    is_dst: bool
    true_solar: bool
    day_change_hour: int
    lunar_year: int
    lunar_month: int                # 正数；闰月以 lunar_leap 标记
    lunar_leap: bool
    lunar_day: int
    lunar_year_ganzhi: str          # 农历年干支（正月初一换年）
    eight_char: list[str]           # [年, 月, 日, 时] 干支（按 day_change_hour 口径）
    time_zhi_clock: str             # 钟表时支（未校正）
    time_zhi_solar: str             # 校正后时支（未校正时同 clock）
    true_solar_shift_min: float | None
    steps: list[str] = field(default_factory=list)

    def asdict(self) -> dict:
        from dataclasses import asdict
        return asdict(self)


def build(birth: BirthInfo, config: FortuneConfig) -> BirthContext:
    """由 BirthInfo + config 生成上下文（复用 normalize，保证与排盘同一事实源）。"""
    nb: NormalizedBirth = normalize(birth, config)
    y, m, d, h, mi, s = nb.solar_ymdhms
    time_zhi_solar = _zhi_of_hour(h)
    return BirthContext(
        solar=f"{y}-{m:02d}-{d:02d} {h:02d}:{mi:02d}:{s:02d}",
        gender=birth.gender,
        longitude=birth.longitude,
        timezone=birth.timezone,
        is_dst=birth.is_dst,
        true_solar=config.use_true_solar_time,
        day_change_hour=config.day_change_hour,
        lunar_year=nb.lunar_year,
        lunar_month=abs(nb.lunar_month),
        lunar_leap=nb.lunar_month < 0,
        lunar_day=nb.lunar_day,
        lunar_year_ganzhi=nb.lunar_year_ganzhi,
        eight_char=[nb.eight_char.getYear(), nb.eight_char.getMonth(),
                    nb.eight_char.getDay(), nb.eight_char.getTime()],
        time_zhi_clock=_zhi_of_hour(birth.hour),
        time_zhi_solar=time_zhi_solar,
        true_solar_shift_min=nb.true_solar_shift_min,
        steps=list(nb.steps),
    )


def check(ctx: BirthContext | dict, *, year=None, month=None, day=None,
          hour=None, minute=None, gender=None, longitude=None,
          timezone=None, is_dst=None, day_change_hour=None) -> None:
    """一致性校验：工具参数与上下文冲突时抛 ValueError（防错配）。

    仅校验传入的非 None 项；历法事实以 normalize 重算为准（见 build）。
    """
    c = ctx if isinstance(ctx, BirthContext) else BirthContext(**ctx)
    checks = {
        "年": (year, int(c.solar[:4])),
        "月": (month, int(c.solar[5:7])),
        "日": (day, int(c.solar[8:10])),
        "时": (hour, int(c.solar[11:13])),
        "分": (minute, int(c.solar[14:16])),
        "性别": (gender, c.gender),
        "经度": (longitude, c.longitude),
        "时区": (timezone, c.timezone),
        "夏令时": (is_dst, c.is_dst),
        "换日时刻": (day_change_hour, c.day_change_hour),
    }
    for label, (given, expected) in checks.items():
        if given is not None and given != expected:
            raise ValueError(
                f"上下文校验失败：{label} 参数 {given!r} 与 BirthContext 的 "
                f"{expected!r} 不一致（防错配，请以同一出生信息生成上下文）")


__all__ = ["BirthContext", "build", "check"]
