"""小六壬（诸葛马前课）—— 农历月日时三数落宫。

表与规则来源：research/xiaoliuren.md（多源交叉核验的通行本）。
- 六宫顺序：大安→留连（异体「流连」）→速喜→赤口→小吉→空亡；
- 从 1 起数：大安起正月顺数月→落宫起初一顺数日→落宫起子时顺数时辰；
- 时用十二地支序（子=1 … 亥=12）；
- 小吉五行通行多作「水」，个别作「木」，属异文存疑，本模块标注为「水（存疑）」。
"""
from __future__ import annotations

from dataclasses import dataclass

PALACES = ("大安", "留连", "速喜", "赤口", "小吉", "空亡")

# 六宫断辞简表。来源：research/xiaoliuren.md §3（通行口诀）
PALACE_INFO = {
    "大安": {
        "吉凶": "吉",
        "五行": "木",
        "方位": "东方",
        "神煞": "青龙",
        "主数": "一、五、七",
        "断语": "大安事事昌，求谋在东方，失物去不远，宅舍保安康；行人身未动，病者主无妨，将军回田野，仔细好推详。",
    },
    "留连": {
        "吉凶": "凶（迟滞）",
        "五行": "水",
        "方位": "北方",
        "神煞": "玄武",
        "主数": "二、八、十",
        "断语": "留连事难成，求谋日未明，官事只宜缓，去者未回程；失物南方见，急讨方称心，更须防口舌，人口且平平。",
    },
    "速喜": {
        "吉凶": "吉",
        "五行": "火",
        "方位": "南方",
        "神煞": "朱雀",
        "主数": "三、六、九",
        "断语": "速喜喜来临，求财向南行，失物申午见，逢人路上寻；官事有福德，病者无祸侵，田宅六畜吉，行人有信音。",
    },
    "赤口": {
        "吉凶": "凶（口舌官非）",
        "五行": "金",
        "方位": "西方",
        "神煞": "白虎",
        "主数": "四、七、十",
        "断语": "赤口主口舌，官非切要防，失物急去寻，行人有惊慌；鸡犬多作怪，病者出西方，更须防诅咒，恐怕染瘟疫。",
    },
    "小吉": {
        "吉凶": "大吉",
        "五行": "水（异文存疑，另有作木）",
        "方位": "南方",
        "神煞": "六合",
        "主数": "一、五、七",
        "断语": "小吉最吉昌，路上好商量，阴人来报喜，失物在坤方；行人立便至，交关甚是强，凡事皆和合，病者叩穹苍。",
    },
    "空亡": {
        "吉凶": "凶",
        "五行": "土",
        "方位": "中央",
        "神煞": "勾陈",
        "主数": "三、六、九",
        "断语": "空亡事不长，阴人多乖张，求财无利益，行人有灾殃；失物寻不见，官事主刑伤，病人逢暗鬼，禳解保安康。",
    },
}

# 掌诀位置（通行左手）：宫名 → (手指, 节位)
FINGER_POS = {
    "大安": ("食指", "下节"),
    "留连": ("食指", "上节"),
    "速喜": ("中指", "上节"),
    "赤口": ("无名指", "上节"),
    "小吉": ("无名指", "下节"),
    "空亡": ("中指", "下节"),
}


def _count(start_idx: int, n: int) -> int:
    """从 start_idx 宫起数 1，数 n 步（从 1 起）。"""
    return (start_idx + n - 1) % 6


@dataclass
class XiaoLiuRenResult:
    lunar_month: int
    lunar_day: int
    hour_zhi: str       # 时支
    month_palace: str   # 月宫
    day_palace: str     # 日宫
    palace: str         # 结果宫
    caliber: str = ""   # 时辰口径声明（出生信息推算时填写）

    @property
    def info(self) -> dict:
        return PALACE_INFO[self.palace]

    @property
    def finger(self) -> tuple[str, str]:
        return FINGER_POS[self.palace]

    def path(self) -> str:
        return f"月落{self.month_palace} → 日落{self.day_palace} → 时落{self.palace}"

    def __str__(self) -> str:  # pragma: no cover - 展示用
        i = self.info
        f, pos = self.finger
        body = (
            f"小六壬（农历{self.lunar_month}月{self.lunar_day}日 {self.hour_zhi}时）\n"
            f"  推演：{self.path()}\n"
            f"  结果宫：{self.palace}（{f}{pos}）  {i['吉凶']}\n"
            f"  五行{i['五行']} · {i['方位']} · {i['神煞']} · 主数{i['主数']}\n"
            f"  断语：{i['断语']}"
        )
        if self.caliber:
            body += f"\n  {self.caliber}"
        return body


def calc(lunar_month: int, lunar_day: int, hour_zhi: str) -> XiaoLiuRenResult:
    """小六壬推算。

    :param lunar_month: 农历月 1-12（闰月按当月，属流派分歧，见 README）。
    :param lunar_day: 农历日 1-30。
    :param hour_zhi: 时支（子丑寅卯辰巳午未申酉戌亥），子=1。
    """
    assert 1 <= lunar_month <= 12
    assert 1 <= lunar_day <= 30
    assert hour_zhi in "子丑寅卯辰巳午未申酉戌亥"
    hour = "子丑寅卯辰巳午未申酉戌亥".index(hour_zhi) + 1
    m = _count(0, lunar_month)
    d = _count(m, lunar_day)
    t = _count(d, hour)
    return XiaoLiuRenResult(
        lunar_month=lunar_month, lunar_day=lunar_day, hour_zhi=hour_zhi,
        month_palace=PALACES[m], day_palace=PALACES[d], palace=PALACES[t],
    )


def calc_from_birth(birth: "BirthInfo", nb: "NormalizedBirth",
                    use_true_solar: bool = True) -> XiaoLiuRenResult:
    """出生信息推算小六壬（农历月日 + 时支），并标注时辰口径。

    注意：小六壬通行按钟表时支起数（本工具标准口径）；本入口提供
    use_true_solar 选项以便与八字/紫微口径对齐比较，两口径结论均如实输出。
    """
    if use_true_solar and nb.true_solar_shift_min is not None:
        hour = nb.solar_ymdhms[3]
        caliber = f"时辰口径：真太阳时支（校正 {nb.true_solar_shift_min:+.1f} 分，与八字/紫微一致）"
    else:
        hour = birth.hour
        caliber = "时辰口径：钟表时支（小六壬工具标准口径，未做真太阳时校正）"
    hour_zhi = "子丑寅卯辰巳午未申酉戌亥"[((hour + 1) // 2) % 12]
    res = calc(abs(nb.lunar_month), nb.lunar_day, hour_zhi)
    res.caliber = caliber
    return res
