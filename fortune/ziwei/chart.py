"""紫微斗数排盘 —— 基于 x_iztro（iztro v2.5.8 的 Rust+Python 移植，
716,314 条黄金用例回归，与 iztro 逐字段对齐）。

为什么用引擎而不是自建安星表：
- 紫微定位表（生日×五行局）等逐格数值存在传本差异，research/ziwei_tables.md
  核验结论明确建议「以 iztro 输出为权威基准」，不自造未经逐格比对的表；
- 本模块只做「取数 + 结构化 + 争议开关」，安星正确性由 x_iztro 负责。

争议开关（config.ziwei_*）：
- ziwei_geng_sihua："tiantong"（庚年天同化忌，iztro/中州派主流，默认）
  | "tianxiang"（庚年天相化忌，《紫微斗数全书》古法）——通过引擎的
  ChartConfig.mutagens 覆盖实现，两种都是引擎原生表；
- ziwei_leap_month："as_month"（闰月全按当月，fix_leap=False，默认）
  | "mid_split"（闰月十五日后按下月，fix_leap=True，iztro 默认）；
  "as_next" 引擎不支持，会给出明确报错。

参考：research/ziwei_tables.md（安星诀核验清单，含全部口诀出处与分歧标注）。
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..config import FortuneConfig
from ..core.calendar import NormalizedBirth

_STEM_KEYS = {"甲": "jiaHeavenly", "乙": "yiHeavenly", "丙": "bingHeavenly",
              "丁": "dingHeavenly", "戊": "wuHeavenly", "己": "jiHeavenly",
              "庚": "gengHeavenly", "辛": "xinHeavenly", "壬": "renHeavenly",
              "癸": "guiHeavenly"}
#: 庚年两派四化（化忌星不同）
_GENG_MUTAGENS = {
    "tiantong": ["taiyangMaj", "wuquMaj", "taiyinMaj", "tiantongMaj"],
    "tianxiang": ["taiyangMaj", "wuquMaj", "taiyinMaj", "tianxiangMaj"],
}

PALACE_ORDER = ("命宫", "兄弟", "夫妻", "子女", "财帛", "疾厄",
                "迁移", "仆役", "官禄", "田宅", "福德", "父母")


@dataclass
class ZiweiPalace:
    name: str                       # 宫名
    gan_zhi: str                    # 宫干支
    major: list[tuple[str, str, str]]   # (星名, 亮度, 四化|"")
    minor: list[str]                # 辅星名
    adjective: list[str]            # 杂曜名
    da_xian: str                    # 大限 "起-止岁"
    da_xian_ganzhi: str
    chang_sheng: str                # 十二长生
    is_ming: bool
    is_shen: bool
    is_laiyin: bool                 # 来因宫（宫干 = 生年干，四化飞星派用）

    def star_list(self) -> list[str]:
        out = []
        for name, bright, mut in self.major:
            s = name + (f"[{bright}]" if bright else "")
            if mut:
                s += f"·{mut}"
            out.append(s)
        out += self.minor
        out += self.adjective
        return out


@dataclass
class ZiweiChart:
    solar_used: str
    gender: str
    year_pillar: str                 # 生年干支（引擎口径）
    sihua: list[tuple[str, str]]     # 生年四化 [(星名, 禄/权/科/忌)]，按禄权科忌序
    five_elements_class: str        # 五行局（如「土五局」）
    ming_index: int                 # 命宫在 palaces 中的索引
    shen_index: int                 # 身宫索引
    ming_zhu: str                   # 命主星
    shen_zhu: str                   # 身主星
    palaces: list[ZiweiPalace]      # 12 宫（命宫起，顺排）
    geng_sihua: str
    leap_month_mode: str
    patterns: list[str] = field(default_factory=list)   # 格局（iztro 64 格局库）
    notes: list[str] = field(default_factory=list)

    def markdown(self) -> str:
        sihua_txt = "、".join(f"{n}化{m}" for n, m in self.sihua)
        lines = [
            f"- 排盘时刻：{self.solar_used}（{self.gender}）",
            f"- 生年四化（{self.year_pillar}年）：{sihua_txt}",
            f"- 五行局：{self.five_elements_class}　命主 {self.ming_zhu}　身主 {self.shen_zhu}",
            f"- 配置口径：庚年化忌={'天同（主流）' if self.geng_sihua == 'tiantong' else '天相（《全书》古法）'}；"
            f"闰月={'按当月' if self.leap_month_mode == 'as_month' else '十五分界' if self.leap_month_mode == 'mid_split' else self.leap_month_mode}",
            "",
            "| 宫 | 干支 | 大限 | 主星 | 辅星杂曜 | 十二长生 |",
            "|---|---|---|---|---|---|",
        ]
        for p in self.palaces:
            tag = ""
            if p.is_ming:
                tag = "（命）"
            if p.is_shen:
                tag += "（身）"
            if p.is_laiyin:
                tag += "（来因）"
            major = " ".join(
                f"{n}{'·' + m if m else ''}" + (f"[{b}]" if b else "")
                for n, b, m in p.major)
            lines.append(
                f"| {p.name}{tag} | {p.gan_zhi} | {p.da_xian}({p.da_xian_ganzhi}) "
                f"| {major} | {' '.join(p.minor + p.adjective) or '—'} | {p.chang_sheng} |")
        lines.append("")
        lines.append("- 亮度符号：庙旺得利平不陷（iztro 标准）。四化标注：禄权科忌。")
        if self.patterns:
            lines.append(f"- 格局（iztro 64 格局库，[破格]=被化忌/煞曜破坏）：{'；'.join(self.patterns)}")
        for n in self.notes:
            lines.append(f"- {n}")
        return "\n".join(lines)

    def palaces_for_svg(self) -> list[dict]:
        out = []
        for i, p in enumerate(self.palaces):
            sihua = {}
            stars = []
            for name, bright, mut in p.major:
                stars.append(name)
                if mut:
                    sihua[name] = mut
            stars += p.minor
            stars += p.adjective
            out.append({
                "name": p.name,
                "gan_zhi": p.gan_zhi,
                "stars": stars,
                "sihua": sihua,
                "da_xian": p.da_xian,
                "chang_sheng": p.chang_sheng,
                "shen_gong": p.is_shen,
            })
        return out

    def svg_note(self) -> str:
        sihua_txt = " ".join(f"{n}化{m}" for n, m in self.sihua)
        return (f"{self.solar_used} {self.gender} 五行局{self.five_elements_class} "
                f"{self.year_pillar}年 {sihua_txt}"
                "｜引擎 x_iztro（iztro 移植）")


def _time_index(hour: int) -> int:
    """小时 → iztro 时辰索引：0=早子, 1=丑 … 11=亥, 12=晚子。"""
    if hour == 23:
        return 12
    return (hour + 1) // 2


def build(nb: NormalizedBirth, gender: str, config: FortuneConfig) -> ZiweiChart:
    from x_iztro.astro import Astro, ChartConfig  # 延迟导入：未装引擎时给出清晰错误

    if config.ziwei_leap_month == "as_next":
        raise NotImplementedError(
            "x_iztro 引擎不支持「闰月全按下月」（as_next）口径；"
            "支持 as_month（按当月，默认）与 mid_split（十五分界，iztro 默认）。")
    y, m, d, h, mi, s = nb.solar_ymdhms
    fix_leap = (config.ziwei_leap_month == "mid_split")
    kwargs = dict(
        gender="male" if gender == "男" else "female",
        fix_leap=fix_leap,
        language="zh-CN",
    )
    if config.ziwei_geng_sihua == "tianxiang":
        kwargs["config"] = ChartConfig(
            mutagens={"gengHeavenly": _GENG_MUTAGENS["tianxiang"]})

    r = Astro().by_solar(f"{y}-{m}-{d}", _time_index(h), **kwargs)

    # x_iztro 的 palaces 按地支序排（索引 0 = 寅宫），命宫以宫名定位；
    # 十二宫自命宫起逆时针（地支序递减）排布 —— 与《紫微斗数全书》一致。
    ming_raw = next(i for i, p in enumerate(r.palaces) if p.name == "命宫")
    order = [(ming_raw - i) % 12 for i in range(12)]

    palaces: list[ZiweiPalace] = []
    shen_idx = -1
    for pos, i in enumerate(order):
        p = r.palaces[i]
        major = [(s.name, (s.brightness or ""), (s.mutagen or ""))
                 for s in p.major_stars]
        is_shen = p.is_body_palace
        if is_shen:
            shen_idx = pos
        palaces.append(ZiweiPalace(
            name=p.name,
            gan_zhi=p.heavenly_stem + p.earthly_branch,
            major=major,
            minor=[s.name for s in p.minor_stars],
            adjective=[s.name for s in p.adjective_stars],
            da_xian=f"{p.decadal.range[0]}-{p.decadal.range[1]}",
            da_xian_ganzhi=p.decadal.heavenly_stem + p.decadal.earthly_branch,
            chang_sheng=p.changsheng12,
            is_ming=(pos == 0),
            is_shen=is_shen,
            is_laiyin=p.is_original_palace,
        ))

    notes = [
        "引擎：x_iztro 0.4.x（iztro v2.5.8 移植，716,314 条黄金用例；安星口径以 iztro 为准）",
        "星曜亮度按 iztro 标准（庙/旺/得/利/平/不/陷）；四化为生年干四化（含宫干自化见引擎原始输出）",
        "争议：庚年四化、闰月口径见 config.ziwei_geng_sihua / ziwei_leap_month 与 research/ziwei_tables.md §11",
    ]

    # 生年干支与四化：直接取自引擎盘面（与安星同一事实源，不另建表）
    yearly = getattr(getattr(r, "raw_dates", None), "chinese_date", None)
    year_pillar = "".join(yearly.yearly) if yearly is not None else ""
    seen: dict[str, str] = {}
    for p in r.palaces:
        for st in p.major_stars:   # 注意：勿用 s 作循环变量（遮蔽上面的秒数 s）
            if st.mutagen and st.name not in seen:
                seen[st.name] = st.mutagen
    sihua = sorted(seen.items(), key=lambda kv: "禄权科忌".index(kv[1]))

    # 格局（iztro 64 格局库；[破格] = 格局被化忌/煞曜破坏）
    patterns: list[str] = []
    for ph in r.patterns():
        stars = "、".join(st.name for st in ph.stars)
        mark = "[破格]" if ph.broken else ""
        patterns.append(f"{ph.name}（{ph.palace_name}）{mark}：{stars}")

    return ZiweiChart(
        solar_used=f"{y}-{m:02d}-{d:02d} {h:02d}:{mi:02d}:{s:02d}",
        gender=gender,
        year_pillar=year_pillar,
        sihua=sihua,
        five_elements_class=r.five_elements_class,
        ming_index=0, shen_index=shen_idx,
        ming_zhu=r.soul, shen_zhu=r.body,
        palaces=palaces,
        geng_sihua=config.ziwei_geng_sihua,
        leap_month_mode=config.ziwei_leap_month,
        patterns=patterns,
        notes=notes,
    )
