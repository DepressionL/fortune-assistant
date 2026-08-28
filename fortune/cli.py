"""命令行入口。

示例：
    fortune bazi -y 1990 -m 6 -d 15 -H 13 -M 30 -g 男
    fortune bazi -y 1990 -m 6 -d 15 -H 13 -M 30 -g 男 --school tiaohou --json
    fortune chenggu -y 1990 -m 6 -d 15 -H 13
    fortune xiaoliuren --month 5 --day 20 --hour-zhi 酉
    fortune meihua --numbers 12 34
    fortune liuyao --backs 2,3,1,0,3,2 --month-zhi 午 --day-ganzhi 甲子
    fortune ziwei -y 1990 -m 6 -d 15 -H 13 -M 30 -g 男 --svg ziwei.svg

--meta-json PATH：每个排盘命令都支持——正常文本输出的同时，把结构化结果
（JSON）写到 PATH，供 DSH 宿主插件的 presentationMeta 使用（客户端插件据此
渲染图形化盘面）。
"""
from __future__ import annotations

import dataclasses
import json
import pathlib

import typer

from .bazi import relation as relation_mod
from .bazi import shensha as shensha_mod
from .bazi import strength as strength_mod
from .bazi import yongshen as yongshen_mod
from .bazi.chart import build as build_bazi
from .config import FortuneConfig
from .core.calendar import normalize
from .core.model import BirthInfo
from .misc import chenggu as chenggu_mod
from .misc import meihua as meihua_mod
from .misc import xiaoliuren as xlr_mod
from .report import markdown as md_report
from .report import svg as svg_report

app = typer.Typer(help="fortune-assistant —— 算命辅助工具（历法换算 + 排盘 + 规则引擎）",
                  no_args_is_help=True)


def _birth_from_solar(year: int, month: int, day: int, hour: int, minute: int,
                      gender: str, longitude: float, is_dst: bool, note: str = "") -> BirthInfo:
    return BirthInfo(calendar="solar", year=year, month=month, day=day, hour=hour,
                     minute=minute, gender=gender, longitude=longitude, is_dst=is_dst,
                     note=note)


def _resolve(year: int, month: int, day: int, hour: int, minute: int,
             gender: str, longitude: float, true_solar: bool, day_change_hour: int,
             is_dst: bool):
    birth = _birth_from_solar(year, month, day, hour, minute, gender, longitude, is_dst)
    config = FortuneConfig(use_true_solar_time=true_solar,
                           day_change_hour=day_change_hour)
    nb = normalize(birth, config)
    return birth, config, nb


def _dump_meta(path: str | None, obj) -> None:
    """把结构化结果写为 JSON（供 DSH 客户端插件渲染图形化盘面）。"""
    if not path:
        return
    pathlib.Path(path).write_text(
        json.dumps(obj, ensure_ascii=False, indent=1, default=str), encoding="utf-8")


def _bazi_meta(chart, config) -> dict:
    """八字结构化结果（与 Markdown 报告同源）。"""
    st = strength_mod.compute(chart)
    ys = yongshen_mod.compute_yongshen(chart, config.yongshen_school)
    return {
        "tool": "bazi",
        "chart": dataclasses.asdict(chart),
        "strength": dataclasses.asdict(st),
        "shensha": [dataclasses.asdict(h) for h in shensha_mod.compute(chart, config.shensha_base)],
        "relations": [dataclasses.asdict(r) for r in relation_mod.scan(chart)],
        "yongshen": dataclasses.asdict(ys),
    }


@app.command()
def bazi(
    year: int = typer.Option(..., "--year", "-y", help="公历年"),
    month: int = typer.Option(..., "--month", "-m", help="公历月"),
    day: int = typer.Option(..., "--day", "-d", help="公历日"),
    hour: int = typer.Option(..., "--hour", "-H", help="时（0-23，钟表时间）"),
    minute: int = typer.Option(0, "--minute", "-M", help="分"),
    gender: str = typer.Option("男", "--gender", "-g", help="男/女"),
    longitude: float = typer.Option(120.0, "--lng", help="出生地东经（度，东为正）"),
    true_solar: bool = typer.Option(True, "--true-solar/--no-true-solar", help="是否真太阳时校正"),
    day_change_hour: int = typer.Option(23, "--day-change", help="换日时刻 23（传统主流）| 0"),
    is_dst: bool = typer.Option(False, "--dst", help="钟面时间是否为中国夏令时（1986-1991）"),
    school: str = typer.Option("wangshuai", "--school",
                               help="用神流派 wangshuai|tiaohou|tongguan|geju"),
    shensha_base: str = typer.Option("day", "--shensha-base", help="神煞基准 day|year"),
    as_json: bool = typer.Option(False, "--json", help="输出 JSON"),
    meta_json: str | None = typer.Option(None, "--meta-json", help="结构化结果落盘路径（供 DSH UI）"),
    out_md: str | None = typer.Option(None, "--md", help="Markdown 报告输出路径"),
    out_svg: str | None = typer.Option(None, "--svg", help="五行条 SVG 输出路径"),
):
    """八字排盘：四柱/藏干/十神/大运/神煞/旺衰/用神。"""
    birth, config, nb = _resolve(year, month, day, hour, minute, gender, longitude,
                                 true_solar, day_change_hour, is_dst)
    config.yongshen_school = school
    config.shensha_base = shensha_base
    chart = build_bazi(nb, gender, config)
    if as_json:
        typer.echo(json.dumps(_bazi_meta(chart, config), ensure_ascii=False, indent=2))
        raise typer.Exit()
    _dump_meta(meta_json, _bazi_meta(chart, config))
    text = md_report.full_report(birth, config, chart)
    if out_md:
        with open(out_md, "w", encoding="utf-8") as f:
            f.write(text)
        typer.echo(f"报告已写入 {out_md}")
    else:
        typer.echo(text)
    if out_svg:
        svg = svg_report.wuxing_bar_svg(strength_mod.compute(chart).scores)
        with open(out_svg, "w", encoding="utf-8") as f:
            f.write(svg)
        typer.echo(f"五行图已写入 {out_svg}")


@app.command()
def chenggu(
    year: int = typer.Option(..., "--year", "-y"),
    month: int = typer.Option(..., "--month", "-m"),
    day: int = typer.Option(..., "--day", "-d"),
    hour: int = typer.Option(..., "--hour", "-H"),
    minute: int = typer.Option(0, "--minute", "-M"),
    gender: str = typer.Option("男", "--gender", "-g"),
    longitude: float = typer.Option(120.0, "--lng"),
    meta_json: str | None = typer.Option(None, "--meta-json", help="结构化结果落盘路径"),
):
    """袁天罡称骨（通行男命版；年按农历正月初一换年，时辰按校正后钟点）。"""
    birth, config, nb = _resolve(year, month, day, hour, minute, gender, longitude,
                                 True, 23, False)
    res = chenggu_mod.calc(nb.lunar_year_ganzhi, abs(nb.lunar_month), nb.lunar_day,
                           nb.time_zhi)
    _dump_meta(meta_json, {"tool": "chenggu", **dataclasses.asdict(res)})
    typer.echo(str(res))
    typer.echo("\n注：称骨为托名袁天罡的民间歌诀（通行男命版），仅作文化参考；"
               "女命版判词未收录。")


@app.command()
def xiaoliuren(
    month: int = typer.Option(..., "--month", help="农历月（闰月按当月，流派分歧见 README）"),
    day: int = typer.Option(..., "--day", help="农历日"),
    hour_zhi: str = typer.Option(..., "--hour-zhi", help="时支：子丑寅卯辰巳午未申酉戌亥"),
    meta_json: str | None = typer.Option(None, "--meta-json", help="结构化结果落盘路径"),
):
    """小六壬（诸葛马前课）。"""
    res = xlr_mod.calc(month, day, hour_zhi)
    _dump_meta(meta_json, {"tool": "xiaoliuren", **dataclasses.asdict(res),
                           "info": xlr_mod.PALACE_INFO[res.palace],
                           "finger": res.finger})
    typer.echo(str(res))


@app.command()
def meihua(
    numbers: list[int] | None = typer.Argument(None, help="数字起卦：a b 或 a b c"),
    lunar_year: int = typer.Option(0, "--lunar-year", help="时间起卦：农历年"),
    lunar_month: int = typer.Option(0, "--lunar-month"),
    lunar_day: int = typer.Option(0, "--lunar-day"),
    hour: int = typer.Option(0, "--hour", help="时（0-23，用于时间起卦取时支）"),
    meta_json: str | None = typer.Option(None, "--meta-json", help="结构化结果落盘路径"),
):
    """梅花易数起卦（数字起卦 / 农历时间起卦）。"""
    if numbers:
        if len(numbers) == 2:
            res = meihua_mod.by_numbers(numbers[0], numbers[1])
        elif len(numbers) == 3:
            res = meihua_mod.by_numbers(numbers[0], numbers[1], numbers[2])
        else:
            typer.echo("数字起卦需 2 或 3 个数", err=True)
            raise typer.Exit(1)
    elif lunar_year and lunar_month and lunar_day:
        res = meihua_mod.by_time(lunar_year, lunar_month, lunar_day, hour)
    else:
        typer.echo("请提供数字（2-3 个）或农历年月日时", err=True)
        raise typer.Exit(1)
    _dump_meta(meta_json, {"tool": "meihua", **dataclasses.asdict(res),
                           "wuxing": {"ti": meihua_mod.GUA_WUXING[res.ti_gua],
                                      "yong": meihua_mod.GUA_WUXING[res.yong_gua]}})
    typer.echo(str(res))


@app.command()
def liuyao(
    backs: str = typer.Option(..., "--backs", help="六次掷币「背」的个数（0-3），自下而上，逗号分隔"),
    month_zhi: str = typer.Option(..., "--month-zhi", help="月建地支"),
    day_ganzhi: str = typer.Option(..., "--day-ganzhi", help="日辰干支，如 甲子"),
    coin_back: str = typer.Option("yang", "--coin-back", help="背=阳(yang,主流)|背=阴(yin)"),
    meta_json: str | None = typer.Option(None, "--meta-json", help="结构化结果落盘路径"),
):
    """六爻起卦装卦。"""
    try:
        vals = [int(x) for x in backs.split(",")]
    except ValueError:
        typer.echo("--backs 需为 6 个 0-3 的整数", err=True)
        raise typer.Exit(1)
    chart = __import__("fortune.liuyao", fromlist=[""]).from_coins(
        vals, month_zhi, day_ganzhi, coin_back)
    _dump_meta(meta_json, {"tool": "liuyao", **dataclasses.asdict(chart)})
    typer.echo(str(chart))


@app.command()
def ziwei(
    year: int = typer.Option(..., "--year", "-y"),
    month: int = typer.Option(..., "--month", "-m"),
    day: int = typer.Option(..., "--day", "-d"),
    hour: int = typer.Option(..., "--hour", "-H"),
    minute: int = typer.Option(0, "--minute", "-M"),
    gender: str = typer.Option("男", "--gender", "-g"),
    longitude: float = typer.Option(120.0, "--lng"),
    geng_sihua: str = typer.Option("tiantong", "--geng-sihua",
                                   help="庚年四化忌星 tiantong(主流)|tianxiang(古法)"),
    leap_mode: str = typer.Option("as_month", "--leap-mode",
                                  help="闰月口径 as_month(按当月)|mid_split(十五分界)"),
    meta_json: str | None = typer.Option(None, "--meta-json", help="结构化结果落盘路径"),
    out_svg: str | None = typer.Option(None, "--svg", help="紫微盘 SVG 输出路径"),
):
    """紫微斗数排盘（引擎：x_iztro，见 README）。"""
    birth, config, nb = _resolve(year, month, day, hour, minute, gender, longitude,
                                 True, 23, False)
    config.ziwei_geng_sihua = geng_sihua
    config.ziwei_leap_month = leap_mode
    try:
        from .ziwei import chart as ziwei_chart
        zc = ziwei_chart.build(nb, gender, config)
        _dump_meta(meta_json, {"tool": "ziwei", **dataclasses.asdict(zc)})
        typer.echo(zc.markdown())
        if out_svg:
            svg = svg_report.ziwei_palace_svg(zc.palaces_for_svg(), note=zc.svg_note())
            with open(out_svg, "w", encoding="utf-8") as f:
                f.write(svg)
            typer.echo(f"紫微盘已写入 {out_svg}")
    except ImportError as e:
        typer.echo(f"紫微模块不可用：{e}", err=True)
        raise typer.Exit(1)


@app.command()
def liunian(
    year: int = typer.Option(..., "--year", "-y", help="公历年（出生年）"),
    month: int = typer.Option(..., "--month", "-m"),
    day: int = typer.Option(..., "--day", "-d"),
    hour: int = typer.Option(..., "--hour", "-H"),
    minute: int = typer.Option(0, "--minute", "-M"),
    gender: str = typer.Option("男", "--gender", "-g"),
    longitude: float = typer.Option(120.0, "--lng"),
    target_year: int = typer.Option(..., "--target-year", help="要看的流年年份"),
):
    """流年分析：流年干支与原局、当前大运的合冲刑害（确定性关系事实）。"""
    birth, config, nb = _resolve(year, month, day, hour, minute, gender, longitude,
                                 True, 23, False)
    chart = build_bazi(nb, gender, config)
    from .bazi.liunian import compute
    typer.echo(str(compute(chart, target_year)))


@app.command()
def solar_info(
    year: int = typer.Option(..., "--year", "-y"),
    month: int = typer.Option(..., "--month", "-m"),
    day: int = typer.Option(..., "--day", "-d"),
    hour: int = typer.Option(12, "--hour", "-H"),
    minute: int = typer.Option(0, "--minute", "-M"),
    meta_json: str | None = typer.Option(None, "--meta-json", help="结构化结果落盘路径"),
):
    """历法信息速查：公历/农历/干支/节气。"""
    birth, config, nb = _resolve(year, month, day, hour, minute, "男", 120.0, False, 23, False)
    lm = nb.lunar_month
    leap = "闰" if lm < 0 else ""
    _jq_name = {"DONG_ZHI": "冬至", "XIAO_HAN": "小寒", "DA_HAN": "大寒",
                "LI_CHUN": "立春", "YU_SHUI": "雨水", "JING_ZHE": "惊蛰",
                "CHUN_FEN": "春分", "QING_MING": "清明", "GU_YU": "谷雨",
                "LI_XIA": "立夏", "XIAO_MAN": "小满", "MANG_ZHONG": "芒种",
                "XIA_ZHI": "夏至", "XIAO_SHU": "小暑", "DA_SHU": "大暑",
                "LI_QIU": "立秋", "CHU_SHU": "处暑", "BAI_LU": "白露",
                "QIU_FEN": "秋分", "HAN_LU": "寒露", "SHUANG_JIANG": "霜降",
                "LI_DONG": "立冬", "XIAO_XUE": "小雪", "DA_XUE": "大雪"}
    jq = [{"name": _jq_name.get(k, k), "time": dt.toYmdHms()}
          for k, dt in list(nb.lunar.getJieQiTable().items())[:12]]
    _dump_meta(meta_json, {
        "tool": "solar_info",
        "solar": f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}",
        "lunarYear": nb.lunar_year, "lunarMonth": abs(lm), "lunarDay": nb.lunar_day,
        "lunarLeap": lm < 0, "yearGanzhi": nb.lunar_year_ganzhi,
        "shengxiao": nb.lunar.getYearShengXiao(),
        "pillars": [nb.eight_char.getYear(), nb.eight_char.getMonth(),
                    nb.eight_char.getDay(), nb.eight_char.getTime()],
        "jieqi": jq,
    })
    typer.echo(f"公历 {year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}")
    typer.echo(f"农历 {nb.lunar_year}年{leap}{abs(lm)}月{nb.lunar_day}日  "
               f"{nb.lunar_year_ganzhi}年 生肖{nb.lunar.getYearShengXiao()}")
    typer.echo(f"四柱：{nb.eight_char.getYear()} {nb.eight_char.getMonth()} "
               f"{nb.eight_char.getDay()} {nb.eight_char.getTime()}")
    typer.echo("当年节气（前 12 个）：")
    for e in jq:
        typer.echo(f"  {e['name']} {e['time']}")


def main() -> None:  # pragma: no cover
    app()


if __name__ == "__main__":  # pragma: no cover
    app()
