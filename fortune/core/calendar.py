"""历法输入封装：把 BirthInfo 归一化为 lunar_python 的 Solar/Lunar/EightChar。

处理链（每一步都会记录到 steps 供报告展示）：
1. 农历/公历输入 → 公历钟面时刻；
2. 中国夏令时（1986–1991，钟面时间扣 1 小时，见 solar_time.china_dst_range）；
3. 时区 → UTC+8（北京时间，lunar_python Solar 的基准时区）；
4. 真太阳时校正（经度差 + 均时差，见 solar_time.correct_true_solar）；
5. Solar → Lunar → EightChar，按 config.day_change_hour 设置 sect
   （23 点换日=sect1 传统主流；0 点换日=sect2 库默认）。

依赖：lunar_python（历法/八字主引擎，纯 Python，经 sxtwl 交叉验证，
见 research/bazi_golden_cases.md）。
"""
from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field

from lunar_python import EightChar, Lunar, Solar

from ..config import FortuneConfig
from .model import BirthInfo
from .solar_time import correct_true_solar


@dataclass
class NormalizedBirth:
    """归一化后的出生时间与各对象句柄。"""
    solar: Solar                     # 校正后公历时刻
    lunar: Lunar                     # 对应农历
    eight_char: EightChar            # 八字对象（已按 config 设 sect）
    solar_ymdhms: tuple[int, int, int, int, int, int]  # 校正后 年月日时分秒
    true_solar_shift_min: float | None   # 真太阳时总偏移（分钟），未校正为 None
    steps: list[str] = field(default_factory=list)

    # ---- 供其他术数模块取用的快查 ----
    @property
    def lunar_year(self) -> int:
        """农历年（负月为闰月的约定不影响年）。"""
        return self.lunar.getYear()

    @property
    def lunar_month(self) -> int:
        """农历月（负数=闰月，lunar_python 约定）。"""
        return self.lunar.getMonth()

    @property
    def lunar_day(self) -> int:
        return self.lunar.getDay()

    @property
    def lunar_year_ganzhi(self) -> str:
        """农历年干支（正月初一换年，称骨/生肖用）。"""
        return self.lunar.getYearInGanZhi()

    @property
    def time_zhi(self) -> str:
        """时支（按校正后钟点）。"""
        return self.lunar.getTimeZhi()


def normalize(birth: BirthInfo, config: FortuneConfig) -> NormalizedBirth:
    """归一化出生信息。"""
    birth.validate()
    config.validate()
    if config.year_change != "lichun":
        raise NotImplementedError(
            "八字引擎（lunar_python）仅支持立春换年（术数界主流）；"
            "「正月初一换年」口径适用于生肖/称骨等（本工具中已固定按正月初一），"
            "八字年柱不支持切换。")
    steps: list[str] = []

    # 1) 农历/公历 → 公历钟面时刻
    if birth.calendar == "solar":
        y, m, d = birth.year, birth.month, birth.day
        steps.append(f"输入：公历 {birth.solar_str()}")
    else:
        lm = -birth.lunar_month if (birth.is_lunar_leap and birth.lunar_month > 0) else birth.lunar_month
        try:
            tmp = Lunar.fromYmd(birth.lunar_year, lm, birth.lunar_day)
        except Exception as e:  # lunar_python 对非法农历日期抛裸 Exception
            raise ValueError(
                f"非法农历日期：{birth.lunar_year}年{'闰' if lm < 0 else ''}{abs(lm)}月"
                f"{birth.lunar_day}日（{e}）。注意：闰月仅在真实存在时可用，"
                f"以负数月表示，如闰二月=-2。") from e
        sol = tmp.getSolar()
        y, m, d = sol.getYear(), sol.getMonth(), sol.getDay()
        steps.append(
            f"输入：农历 {birth.lunar_year}年{'闰' if lm < 0 else ''}{abs(lm)}月{birth.lunar_day}日"
            f" {birth.time_str()}（= 公历 {y}-{m:02d}-{d:02d}）"
        )
    dt = _dt.datetime(y, m, d, birth.hour, birth.minute, birth.second)

    # 2) 中国夏令时（1986–1991，[开始日 02:00, 结束日 02:00)）
    if birth.is_dst:
        from .solar_time import china_dst_range, is_china_dst
        rng = china_dst_range(dt.year)
        if not (rng and is_china_dst(dt.year, dt.month, dt.day,
                                     dt.hour, dt.minute, dt.second)):
            raise ValueError(
                f"is_dst=True 但钟面时间 {dt} 不在中国夏令时区间内"
                f"（{dt.year} 年夏令时：{rng[0]} 02:00 – {rng[1]} 02:00）"
                if rng else f"is_dst=True 但 {dt.year} 年无中国夏令时（仅 1986–1991 有）")
        dt -= _dt.timedelta(hours=1)
        steps.append("扣 1 小时夏令时（1986–1991 中国夏令时）")

    # 3) 时区 → UTC+8
    if birth.timezone != 8:
        dt += _dt.timedelta(hours=8 - birth.timezone)
        steps.append(f"时区 UTC+{birth.timezone:g} → UTC+8（北京时间）")

    # 4) 真太阳时校正
    shift = None
    if config.use_true_solar_time:
        y2, m2, d2, h2, mi2, s2, shift = correct_true_solar(
            dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, birth.longitude)
        dt = _dt.datetime(y2, m2, d2, h2, mi2, s2)
        steps.append(f"真太阳时校正（东经{birth.longitude:g}°）：偏移 {shift:+.1f} 分钟")

    y, m, d, h, mi, s = dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second

    # 5) lunar_python 对象
    solar = Solar.fromYmdHms(y, m, d, h, mi, s)
    lunar = solar.getLunar()
    ec = lunar.getEightChar()
    ec.setSect(1 if config.day_change_hour == 23 else 2)
    if config.day_change_hour == 23:
        steps.append("日柱流派：23:00 换日（夜子时算次日，传统主流，sect=1）")
    else:
        steps.append("日柱流派：0:00 换日（夜子时算当天，库默认，sect=2）")

    return NormalizedBirth(
        solar=solar, lunar=lunar, eight_char=ec,
        solar_ymdhms=(y, m, d, h, mi, s),
        true_solar_shift_min=shift, steps=steps,
    )
