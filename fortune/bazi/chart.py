"""八字排盘：四柱、藏干、十神、纳音、地势、旬空、胎元命宫身宫、大运。

数据全部来自 lunar_python（EightChar/Yun），本模块只做「取数 + 结构化」，
不自行推算干支（历法正确性由 lunar_python 负责，并经 sxtwl 交叉验证，
见 research/bazi_golden_cases.md）。
"""
from __future__ import annotations

from dataclasses import dataclass, field

from lunar_python import EightChar
from lunar_python.util import LunarUtil

from ..config import FortuneConfig
from ..core.calendar import NormalizedBirth
from ..core.model import WUXING

PILLAR_NAMES = ("年柱", "月柱", "日柱", "时柱")


@dataclass
class Pillar:
    name: str                 # 年柱/月柱/日柱/时柱
    gan_zhi: str              # 干支
    gan: str
    zhi: str
    hide_gan: list[str]       # 藏干（1-3 个）
    shi_shen_gan: str         # 天干十神（日柱为「日主」）
    shi_shen_zhi: list[str]   # 藏干十神
    na_yin: str               # 纳音
    wu_xing: str              # 干五行（本气）
    di_shi: str               # 十二长生（地势）
    xun: str                  # 所在旬
    xun_kong: str             # 旬空

    def __str__(self) -> str:  # pragma: no cover
        hide = " ".join(f"{g}({s})" for g, s in zip(self.hide_gan, self.shi_shen_zhi))
        return (f"{self.name} {self.gan_zhi}  五行{self.wu_xing}  纳音{self.na_yin}  "
                f"十神[{self.shi_shen_gan}]  藏干[{hide}]  地势{self.di_shi}  "
                f"旬空[{self.xun_kong}]")


@dataclass
class DayunStep:
    index: int                # 1 起（0=起运前，不放入列表）
    gan_zhi: str
    start_year: int
    end_year: int
    start_age: int            # 虚岁
    end_age: int

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.gan_zhi}（{self.start_year}-{self.end_year}，{self.start_age}-{self.end_age}岁）"


@dataclass
class BaziChart:
    gender: str
    pillars: list[Pillar]                     # 年月日时四柱
    solar_used: str                           # 排盘所用公历时刻
    true_solar_shift_min: float | None
    steps: list[str]                          # 归一化处理链
    tai_yuan: str
    ming_gong: str
    shen_gong: str
    yun_forward: bool
    yun_start_solar: str                      # 起运公历日期
    yun_start_age: int                        # 起运虚岁
    dayun: list[DayunStep]
    #: 五行统计（干支本气，不含藏干加权；加权版见 strength.py）
    wuxing_count: dict[str, int] = field(default_factory=dict)

    @property
    def day_master(self) -> str:
        return self.pillars[2].gan

    @property
    def day_zhi(self) -> str:
        return self.pillars[2].zhi

    def pillar(self, name: str) -> Pillar:
        return next(p for p in self.pillars if p.name == name)

    def gans(self) -> list[str]:
        return [p.gan for p in self.pillars]

    def zhis(self) -> list[str]:
        return [p.zhi for p in self.pillars]

    def __str__(self) -> str:  # pragma: no cover
        lines = [f"八字（{self.gender}）排盘时刻：{self.solar_used}"]
        lines += [f"  {s}" for s in self.steps]
        lines += [f"  {p}" for p in self.pillars]
        lines.append(f"  胎元 {self.tai_yuan}  命宫 {self.ming_gong}  身宫 {self.shen_gong}")
        lines.append(
            f"  大运：{'顺行' if self.yun_forward else '逆行'}，起运 {self.yun_start_solar}"
            f"（虚岁 {self.yun_start_age}）")
        lines.append("  " + "  ".join(str(d) for d in self.dayun))
        return "\n".join(lines)


def build(nb: NormalizedBirth, gender: str, config: FortuneConfig,
          dayun_steps: int = 8) -> BaziChart:
    """由归一化出生信息构建八字盘。"""
    ec: EightChar = nb.eight_char
    getters = [  # (柱名, 藏干, 十神干, 十神支, 纳音, 地势, 旬, 旬空)
        ("年柱", ec.getYear, ec.getYearHideGan, ec.getYearShiShenGan, ec.getYearShiShenZhi,
         ec.getYearNaYin, ec.getYearDiShi, ec.getYearXun, ec.getYearXunKong),
        ("月柱", ec.getMonth, ec.getMonthHideGan, ec.getMonthShiShenGan, ec.getMonthShiShenZhi,
         ec.getMonthNaYin, ec.getMonthDiShi, ec.getMonthXun, ec.getMonthXunKong),
        ("日柱", ec.getDay, ec.getDayHideGan, ec.getDayShiShenGan, ec.getDayShiShenZhi,
         ec.getDayNaYin, ec.getDayDiShi, ec.getDayXun, ec.getDayXunKong),
        ("时柱", ec.getTime, ec.getTimeHideGan, ec.getTimeShiShenGan, ec.getTimeShiShenZhi,
         ec.getTimeNaYin, ec.getTimeDiShi, ec.getTimeXun, ec.getTimeXunKong),
    ]
    pillars: list[Pillar] = []
    wuxing_count = {w: 0 for w in WUXING}
    for name, gz_f, hide_f, ssg_f, ssz_f, nayin_f, dishi_f, xun_f, xunkong_f in getters:
        gz = gz_f()
        gan, zhi = gz[0], gz[1]
        pillars.append(Pillar(
            name=name, gan_zhi=gz, gan=gan, zhi=zhi,
            hide_gan=list(hide_f()),
            shi_shen_gan=ssg_f(),
            shi_shen_zhi=list(ssz_f()),
            na_yin=nayin_f(),
            wu_xing=LunarUtil.WU_XING_GAN[gan],
            di_shi=dishi_f(),
            xun=xun_f(), xun_kong=xunkong_f(),
        ))
        wuxing_count[LunarUtil.WU_XING_GAN[gan]] += 1
        wuxing_count[LunarUtil.WU_XING_ZHI[zhi]] += 1

    # 大运
    if config.yun_days_per_year != 3:
        raise NotImplementedError(
            "lunar_python 仅内置「3 天折 1 年」起运算法；2/5 天折 1 年的流派变体"
            "请自行扩展（本工具为可靠性起见不硬造轮子）。")
    yun = ec.getYun(1 if gender == "男" else 0, 1)
    dayun: list[DayunStep] = []
    raw = yun.getDaYun(dayun_steps + 1)
    for i, d in enumerate(raw[1:], start=1):
        dayun.append(DayunStep(
            index=i, gan_zhi=d.getGanZhi(),
            start_year=d.getStartYear(), end_year=d.getEndYear(),
            start_age=d.getStartAge(), end_age=d.getEndAge(),
        ))

    y, m, d, h, mi, s = nb.solar_ymdhms
    return BaziChart(
        gender=gender,
        pillars=pillars,
        solar_used=f"{y}-{m:02d}-{d:02d} {h:02d}:{mi:02d}:{s:02d}",
        true_solar_shift_min=nb.true_solar_shift_min,
        steps=nb.steps,
        tai_yuan=ec.getTaiYuan(),
        ming_gong=ec.getMingGong(),
        shen_gong=ec.getShenGong(),
        yun_forward=yun.isForward(),
        yun_start_solar=yun.getStartSolar().toYmd(),
        yun_start_age=raw[1].getStartAge(),
        dayun=dayun,
        wuxing_count=wuxing_count,
    )
