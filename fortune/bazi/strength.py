"""五行旺衰打分与日主强弱（经验规则引擎，非确定性结论）。

方法：月令旺相休囚死 + 藏干加权，是通行「打分法」的一种。
- 月令状态：当令者旺、令生者相、生令者休、克令者囚、令克者死；
- 权重（经验参数，各排盘软件略有差异，可调）：
    天干 1.0 / 支本气 1.0 / 藏干中气 0.4 / 藏干余气 0.2，再乘月令状态系数：
    旺 1.0、相 0.8、休 0.5、囚 0.3、死 0.1。
- 身强身弱：同类（日主五行+生日主之印）得分与异类（食伤财官杀）得分比较，
  差幅 ≤10% 判「中和」。

出处：月令旺相休囚死——《三命通会》《渊海子平》通行论法；权重系数为现代
排盘软件通行经验参数（非古籍定值）。本模块输出过程数据，供人工复核。
"""
from __future__ import annotations

from dataclasses import dataclass, field

from lunar_python.util import LunarUtil

from .chart import BaziChart

SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
KE = {a: b for a, b in (("木", "土"), ("土", "水"), ("水", "火"), ("火", "金"), ("金", "木"))}

#: 月令状态系数（经验参数）
STATE_FACTOR = {"旺": 1.0, "相": 0.8, "休": 0.5, "囚": 0.3, "死": 0.1}
#: 干/支本气/中气/余气权重（经验参数）
WEIGHT_GAN = 1.0
WEIGHT_QI = 1.0
WEIGHT_ZHONG = 0.4
WEIGHT_YU = 0.2

WUXING_ORDER = ("木", "火", "土", "金", "水")


def month_states(month_wx: str) -> dict[str, str]:
    """月令五行 → 各五行旺相休囚死。"""
    return {
        month_wx: "旺",
        SHENG[month_wx]: "相",
        KE[month_wx]: "死",
        next(w for w in WUXING_ORDER if SHENG[w] == month_wx): "休",
        next(w for w in WUXING_ORDER if KE[w] == month_wx): "囚",
    }


@dataclass
class StrengthResult:
    month_wx: str                       # 月令五行
    states: dict[str, str]              # 五行 → 旺相休囚死
    scores: dict[str, float]            # 五行加权得分
    detail: list[str] = field(default_factory=list)   # 计分明细
    day_wx: str = ""                    # 日主五行
    same_score: float = 0.0             # 同类（日主+印）得分
    diff_score: float = 0.0             # 异类得分
    level: str = ""                     # 身强/身弱/中和

    def __str__(self) -> str:  # pragma: no cover
        s = "  ".join(f"{w}{self.scores[w]:.2f}" for w in WUXING_ORDER)
        return (f"月令{self.month_wx}（{self.states}）\n  得分：{s}\n"
                f"  日主{self.day_wx} 同类{self.same_score:.2f} 异类{self.diff_score:.2f} "
                f"→ {self.level}")


def compute(chart: BaziChart) -> StrengthResult:
    month_zhi = chart.pillar("月柱").zhi
    month_wx = LunarUtil.WU_XING_ZHI[month_zhi]
    states = month_states(month_wx)
    scores = {w: 0.0 for w in WUXING_ORDER}
    detail: list[str] = []

    for p in chart.pillars:
        # 天干
        wx = LunarUtil.WU_XING_GAN[p.gan]
        st = states[wx]
        scores[wx] += WEIGHT_GAN * STATE_FACTOR[st]
        detail.append(f"{p.name}{p.gan_zhi} 干{p.gan}({wx},{st}) "
                      f"+{WEIGHT_GAN * STATE_FACTOR[st]:.2f}")
        # 地支本气 + 藏干
        qis = p.hide_gan
        for k, g in enumerate(qis):
            gwx = LunarUtil.WU_XING_GAN[g]
            w = WEIGHT_QI if k == 0 else (WEIGHT_ZHONG if k == 1 else WEIGHT_YU)
            scores[gwx] += w * STATE_FACTOR[states[gwx]]
            detail.append(f"  {p.name}支{p.zhi}藏{g}({gwx},{states[gwx]}) "
                          f"+{w * STATE_FACTOR[states[gwx]]:.2f}")

    day_wx = LunarUtil.WU_XING_GAN[chart.day_master]
    yin = next(w for w in WUXING_ORDER if SHENG[w] == day_wx)  # 生日主者=印
    same = scores[day_wx] + scores[yin]
    diff = sum(v for k, v in scores.items() if k not in (day_wx, yin))
    total = same + diff
    ratio = (same - diff) / total if total else 0.0
    if ratio > 0.10:
        level = "身强"
    elif ratio < -0.10:
        level = "身弱"
    else:
        level = "中和"

    return StrengthResult(month_wx=month_wx, states=states, scores=scores,
                          detail=detail, day_wx=day_wx,
                          same_score=same, diff_score=diff, level=level)
