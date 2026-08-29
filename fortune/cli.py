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
import datetime as _dt
import json
import pathlib
import re
import secrets

import typer

from .bazi import ditiansui as ditiansui_mod
from .bazi import relation as relation_mod
from .bazi import shensha as shensha_mod
from .bazi import strength as strength_mod
from .bazi import yongshen as yongshen_mod
from .bazi.chart import build as build_bazi
from .config import FortuneConfig
from .core.calendar import normalize
from .core.model import BirthInfo
from .liuyao import ZHI, duanyu as liuyao_duanyu
from .misc import chenggu as chenggu_mod
from .misc import meihua as meihua_mod
from .misc import xiaoliuren as xlr_mod
from .misc import zhouyi as zhouyi_mod
from .report import markdown as md_report
from .report import svg as svg_report

app = typer.Typer(help="fortune-assistant —— 算命辅助工具（历法换算 + 排盘 + 规则引擎）",
                  no_args_is_help=True)

_VALID_SCHOOLS = ("wangshuai", "tiaohou", "tongguan", "geju", "bingyao")
_GAN = "甲乙丙丁戊己庚辛壬癸"


def _fail(msg: str) -> None:
    """统一的输入错误出口：stderr 说明 + 退出码 2（宿主插件据此透出可读报错）。"""
    typer.echo(f"输入错误：{msg}", err=True)
    raise typer.Exit(2)


def _validate_birth(year: int, month: int, day: int, hour: int, minute: int,
                    gender: str, longitude: float, timezone: float = 8.0) -> None:
    """出生参数统一边界校验（各排盘命令共用，保证口径一致）。"""
    if not (1600 <= year <= 2200):
        _fail(f"年份 {year} 超出支持范围（1600-2200）")
    if not (1 <= month <= 12):
        _fail(f"月份 {month} 须在 1-12")
    if not (1 <= day <= 31):
        _fail(f"日 {day} 须在 1-31")
    try:
        _dt.date(year, month, day)
    except ValueError:
        _fail(f"公历日期 {year}-{month:02d}-{day:02d} 不存在")
    if not (0 <= hour <= 23):
        _fail(f"时 {hour} 须在 0-23")
    if not (0 <= minute <= 59):
        _fail(f"分 {minute} 须在 0-59")
    if gender not in ("男", "女"):
        _fail(f"性别须为 男/女，得到 {gender!r}")
    if not (-180 <= longitude <= 180):
        _fail(f"经度 {longitude} 须在 -180~180（东为正）")
    if not (-12 <= timezone <= 14):
        _fail(f"时区 {timezone} 须在 -12~14（小时，东为正）")


def _validate_ganzhi(gz: str) -> None:
    """日辰干支校验：两字、天干地支各合法、阴阳相配（60 甲子配对规则）。"""
    if not re.fullmatch(r"[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]", gz or ""):
        _fail(f"日辰干支 {gz!r} 不合法（须如「甲子」）")
    if _GAN.index(gz[0]) % 2 != ZHI.index(gz[1]) % 2:
        _fail(f"干支 {gz} 不存在（天干与地支阴阳不相配）")


def _birth_from_solar(year: int, month: int, day: int, hour: int, minute: int,
                      gender: str, longitude: float, is_dst: bool,
                      timezone: float = 8.0, note: str = "") -> BirthInfo:
    return BirthInfo(calendar="solar", year=year, month=month, day=day, hour=hour,
                     minute=minute, gender=gender, longitude=longitude, is_dst=is_dst,
                     timezone=timezone, note=note)


def _resolve(year: int, month: int, day: int, hour: int, minute: int,
             gender: str, longitude: float, true_solar: bool, day_change_hour: int,
             is_dst: bool, timezone: float = 8.0):
    birth = _birth_from_solar(year, month, day, hour, minute, gender, longitude,
                              is_dst, timezone)
    config = FortuneConfig(use_true_solar_time=true_solar,
                           day_change_hour=day_change_hour)
    try:
        nb = normalize(birth, config)
    except ValueError as e:
        _fail(str(e))
    return birth, config, nb


#: DSH 宿主插件用它从子进程输出中拆出结构化数据
META_MARKER = "===DSH_META_JSON==="


def _dump_meta(path: str | None, obj) -> None:
    """把结构化结果落盘 + 内嵌回传（供 DSH 客户端插件渲染图形化盘面）。

    双通道：--meta-json <path> 时既写文件（CLI 用户兼容），又在 stdout
    末尾以 META_MARKER 行内嵌一层 JSON——宿主插件拆出后随规范值交给
    presentationMeta（无文件/无哈希/无时序依赖）。
    """
    text = json.dumps(obj, ensure_ascii=False, indent=1, default=str)
    if path:
        pathlib.Path(path).write_text(text, encoding="utf-8")
    typer.echo(f"\n{META_MARKER}\n{text}")


def _bazi_meta(chart, config, schools: list[str] | None = None) -> dict:
    """八字结构化结果（与 Markdown 报告同源）。"""
    school_list = schools or [config.yongshen_school]
    st = strength_mod.compute(chart)
    ys = yongshen_mod.compute_yongshen(chart, school_list[0])
    dayun_rows, liunian_diffs = ditiansui_mod.hezhi_suiyun(chart, st)
    return {
        "tool": "bazi",
        "chart": dataclasses.asdict(chart),
        "strength": dataclasses.asdict(st),
        "shensha": [dataclasses.asdict(h) for h in shensha_mod.compute(chart, config.shensha_base)],
        "relations": [dataclasses.asdict(r) for r in relation_mod.scan(chart)],
        "yongshen": dataclasses.asdict(ys),
        "yongshen_all": {s: dataclasses.asdict(yongshen_mod.compute_yongshen(chart, s))
                         for s in school_list},
        "hezhi": [dataclasses.asdict(h) for h in ditiansui_mod.hezhi(chart, st)],
        "hezhi_dayun": dayun_rows,
        "hezhi_liunian": liunian_diffs[:20],
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
    timezone: float = typer.Option(8.0, "--timezone",
                                   help="出生记录所用标准时区（小时，东为正；默认 8=北京时间 UTC+8）"),
    school: str = typer.Option("wangshuai", "--school",
                               help="用神流派 wangshuai|tiaohou|tongguan|geju|bingyao"),
    schools: str | None = typer.Option(None, "--schools",
                                       help="逗号分隔多流派对比，如 wangshuai,tiaohou（覆盖 --school）"),
    shensha_base: str = typer.Option("day", "--shensha-base", help="神煞基准 day|year"),
    as_json: bool = typer.Option(False, "--json", help="输出 JSON"),
    meta_json: str | None = typer.Option(None, "--meta-json", help="结构化结果落盘路径（供 DSH UI）"),
    out_md: str | None = typer.Option(None, "--md", help="Markdown 报告输出路径"),
    out_svg: str | None = typer.Option(None, "--svg", help="五行条 SVG 输出路径"),
):
    """八字排盘：四柱/藏干/十神/大运/神煞/旺衰/用神。"""
    _validate_birth(year, month, day, hour, minute, gender, longitude, timezone)
    school_list: list[str]
    if schools:
        school_list = [s.strip() for s in schools.split(",") if s.strip()]
        for s in school_list:
            if s not in _VALID_SCHOOLS:
                _fail(f"--schools 含非法流派 {s!r}（wangshuai|tiaohou|tongguan|geju|bingyao）")
    else:
        if school not in _VALID_SCHOOLS:
            _fail(f"--school 非法流派 {school!r}（wangshuai|tiaohou|tongguan|geju|bingyao）")
        school_list = [school]
    birth, config, nb = _resolve(year, month, day, hour, minute, gender, longitude,
                                 true_solar, day_change_hour, is_dst, timezone)
    config.yongshen_school = school_list[0]
    config.shensha_base = shensha_base
    chart = build_bazi(nb, gender, config)
    if as_json:
        typer.echo(json.dumps(_bazi_meta(chart, config, school_list),
                              ensure_ascii=False, indent=2))
        raise typer.Exit()
    text = md_report.full_report(birth, config, chart, yongshen_schools=school_list)
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
    _dump_meta(meta_json, _bazi_meta(chart, config, school_list))


@app.command()
def chenggu(
    year: int = typer.Option(..., "--year", "-y"),
    month: int = typer.Option(..., "--month", "-m"),
    day: int = typer.Option(..., "--day", "-d"),
    hour: int = typer.Option(..., "--hour", "-H"),
    minute: int = typer.Option(0, "--minute", "-M"),
    gender: str = typer.Option("男", "--gender", "-g"),
    longitude: float = typer.Option(120.0, "--lng"),
    timezone: float = typer.Option(8.0, "--timezone",
                                   help="出生记录所用标准时区（小时，东为正；默认 8=北京时间 UTC+8）"),
    meta_json: str | None = typer.Option(None, "--meta-json", help="结构化结果落盘路径"),
):
    """袁天罡称骨（通行男命版；年按农历正月初一换年，时辰按校正后钟点）。"""
    _validate_birth(year, month, day, hour, minute, gender, longitude, timezone)
    birth, config, nb = _resolve(year, month, day, hour, minute, gender, longitude,
                                 True, 23, False, timezone)
    res = chenggu_mod.calc(nb.lunar_year_ganzhi, abs(nb.lunar_month), nb.lunar_day,
                           nb.time_zhi)
    typer.echo(str(res))
    if gender == "女":
        typer.echo("⚠ 提示：通行女命版判词未收录，以上结果按男命版歌诀计算，仅供参考。")
    typer.echo("\n注：称骨为托名袁天罡的民间歌诀（通行男命版），仅作文化参考；"
               "女命版判词未收录。")
    _dump_meta(meta_json, {"tool": "chenggu", **dataclasses.asdict(res)})


@app.command()
def xiaoliuren(
    month: int = typer.Option(..., "--month", help="农历月（闰月按当月，流派分歧见 README）"),
    day: int = typer.Option(..., "--day", help="农历日"),
    hour_zhi: str = typer.Option(..., "--hour-zhi", help="时支：子丑寅卯辰巳午未申酉戌亥"),
    meta_json: str | None = typer.Option(None, "--meta-json", help="结构化结果落盘路径"),
):
    """小六壬（诸葛马前课）。"""
    if not (1 <= month <= 12):
        _fail(f"农历月 {month} 须在 1-12")
    if not (1 <= day <= 30):
        _fail(f"农历日 {day} 须在 1-30")
    if hour_zhi not in ZHI:
        _fail(f"时支 {hour_zhi!r} 非法（须为子丑寅卯辰巳午未申酉戌亥）")
    res = xlr_mod.calc(month, day, hour_zhi)
    typer.echo(str(res))
    _dump_meta(meta_json, {"tool": "xiaoliuren", **dataclasses.asdict(res),
                           "info": xlr_mod.PALACE_INFO[res.palace],
                           "finger": res.finger})


@app.command()
def meihua(
    numbers: list[int] | None = typer.Argument(None, help="数字起卦：a b 或 a b c"),
    lunar_year: int = typer.Option(0, "--lunar-year", help="时间起卦：农历年"),
    lunar_month: int = typer.Option(0, "--lunar-month"),
    lunar_day: int = typer.Option(0, "--lunar-day"),
    hour: int = typer.Option(0, "--hour", help="时（0-23，用于时间起卦取时支）"),
    meta_json: str | None = typer.Option(None, "--meta-json", help="结构化结果落盘路径"),
):
    """梅花易数起卦（数字起卦 / 农历时间起卦），附卦辞爻辞（通行本《周易》）。"""
    if numbers:
        if len(numbers) not in (2, 3):
            _fail(f"数字起卦需 2 或 3 个数，得到 {len(numbers)} 个")
        if any(n < 1 for n in numbers):
            _fail("数字起卦各数须为正整数")
        res = meihua_mod.by_numbers(numbers[0], numbers[1],
                                    numbers[2] if len(numbers) == 3 else None)
    elif lunar_year and lunar_month and lunar_day:
        if not (1600 <= lunar_year <= 2200):
            _fail(f"农历年 {lunar_year} 超出支持范围（1600-2200）")
        if not (1 <= lunar_month <= 12):
            _fail(f"农历月 {lunar_month} 须在 1-12")
        if not (1 <= lunar_day <= 30):
            _fail(f"农历日 {lunar_day} 须在 1-30")
        if not (0 <= hour <= 23):
            _fail(f"时 {hour} 须在 0-23")
        res = meihua_mod.by_time(lunar_year, lunar_month, lunar_day, hour)
    else:
        _fail("请提供数字（2-3 个）或农历年月日（--lunar-year/--lunar-month/--lunar-day）")
    typer.echo(str(res))
    typer.echo("")
    typer.echo("《梅花易数》体用总诀（题宋·邵雍撰，传系后人托名；通行排印本）："
               "「体克用，诸事吉；用克体，诸事凶。体生用，有耗失之患；用生体，"
               "有进益之喜。体用比和，则百事顺遂。」")
    _echo_zhouyi(res)
    _dump_meta(meta_json, {"tool": "meihua", **dataclasses.asdict(res),
                           "wuxing": {"ti": meihua_mod.GUA_WUXING[res.ti_gua],
                                      "yong": meihua_mod.GUA_WUXING[res.yong_gua]},
                           "zhouyi": _zhouyi_ref(res)})


def _zhouyi_ref(res) -> dict:
    """梅花结果 → 卦爻辞/彖传/大象传引用（通行本《周易》）。"""
    return {
        "ben_gua_ci": zhouyi_mod.gua_ci(res.ben_gua),
        "dong_yao_ci": zhouyi_mod.yao_ci(res.ben_gua, res.moving_line),
        "bian_gua_ci": zhouyi_mod.gua_ci(res.bian_gua),
        "ben_tuan": zhouyi_mod.tuan(res.ben_gua),
        "ben_daxiang": zhouyi_mod.daxiang(res.ben_gua),
        "ben_mean": zhouyi_mod.meaning(res.ben_gua),
        "bian_mean": zhouyi_mod.meaning(res.bian_gua),
        "source": "通行本《周易》（阮刻《十三经注疏》本文字；彖传/大象传为"
                  "维基文库本程序化提取原文）；卦义为通行传注概括",
    }


def _echo_zhouyi(res) -> None:
    """输出卦辞/爻辞/彖传/大象传文本参照（与体用断法并列，两法互参）。"""
    ref = _zhouyi_ref(res)
    typer.echo("")
    typer.echo("【卦爻辞（通行本《周易》，阮刻《十三经注疏》本文字）】")
    if ref["ben_gua_ci"]:
        typer.echo(f"本卦「{res.ben_gua}」卦辞：{ref['ben_gua_ci']}")
        if ref["ben_mean"]:
            typer.echo(f"  卦义（通行传注概括，参考）：{ref['ben_mean']}")
    if ref["ben_tuan"]:
        typer.echo(f"本卦「{res.ben_gua}」彖传（原文）：{ref['ben_tuan']}")
    if ref["ben_daxiang"]:
        typer.echo(f"本卦「{res.ben_gua}」大象传（原文）：{ref['ben_daxiang']}")
    if ref["dong_yao_ci"]:
        typer.echo(f"动爻（第{res.moving_line}爻）爻辞：{ref['dong_yao_ci']}")
    if res.bian_gua != res.ben_gua and ref["bian_gua_ci"]:
        typer.echo(f"变卦「{res.bian_gua}」卦辞：{ref['bian_gua_ci']}")
        if ref["bian_mean"]:
            typer.echo(f"  卦义（通行传注概括，参考）：{ref['bian_mean']}")
    typer.echo("注：卦爻辞、彖传、大象传均为原文引文；吉凶以体用生克断法为主（见上），两法可互参。")


@app.command()
def liuyao(
    backs: str | None = typer.Option(None, "--backs",
                                     help="六次掷币「背」的个数（0-3），自下而上，逗号分隔；--random 时可省"),
    month_zhi: str = typer.Option(..., "--month-zhi", help="月建地支"),
    day_ganzhi: str = typer.Option(..., "--day-ganzhi", help="日辰干支，如 甲子"),
    coin_back: str = typer.Option("yang", "--coin-back", help="背=阳(yang,主流)|背=阴(yin)"),
    random: bool = typer.Option(False, "--random",
                                help="随机模拟三枚铜钱掷六次（每枚独立 50% 出背，符合真实掷币分布）"),
    meta_json: str | None = typer.Option(None, "--meta-json", help="结构化结果落盘路径"),
):
    """六爻起卦装卦（附规则化断语，逐条出处见 fortune/liuyao/duanyu.py）。"""
    if month_zhi not in ZHI:
        _fail(f"月建地支 {month_zhi!r} 非法（须为子丑寅卯辰巳午未申酉戌亥）")
    _validate_ganzhi(day_ganzhi)
    if coin_back not in ("yang", "yin"):
        _fail(f"--coin-back 须为 yang/yin，得到 {coin_back!r}")
    if backs:
        try:
            vals = [int(x) for x in backs.split(",")]
        except ValueError:
            _fail("--backs 需为 6 个 0-3 的整数，逗号分隔（自下而上）")
    elif random:
        rng = secrets.SystemRandom()
        vals = [sum(rng.randrange(2) for _ in range(3)) for _ in range(6)]
        typer.echo(f"随机掷币（三枚铜钱 × 6 次，自下而上）：{','.join(map(str, vals))}")
    else:
        _fail("请提供 --backs（六次背数）或使用 --random 随机起卦")
    if len(vals) != 6 or any(not 0 <= v <= 3 for v in vals):
        _fail(f"--backs 需恰好 6 个 0-3 的整数，得到 {vals}")
    chart = __import__("fortune.liuyao", fromlist=[""]).from_coins(
        vals, month_zhi, day_ganzhi, coin_back)
    typer.echo(str(chart))
    duanyu_text = liuyao_duanyu.duanyu(chart)
    typer.echo("")
    typer.echo(duanyu_text)
    _dump_meta(meta_json, {"tool": "liuyao", **dataclasses.asdict(chart),
                           "backs": vals, "duanyu": duanyu_text})


@app.command()
def ziwei(
    year: int = typer.Option(..., "--year", "-y"),
    month: int = typer.Option(..., "--month", "-m"),
    day: int = typer.Option(..., "--day", "-d"),
    hour: int = typer.Option(..., "--hour", "-H"),
    minute: int = typer.Option(0, "--minute", "-M"),
    gender: str = typer.Option("男", "--gender", "-g"),
    longitude: float = typer.Option(120.0, "--lng"),
    true_solar: bool = typer.Option(True, "--true-solar/--no-true-solar",
                                    help="是否真太阳时校正"),
    day_change_hour: int = typer.Option(23, "--day-change", help="换日时刻 23（传统主流）| 0"),
    is_dst: bool = typer.Option(False, "--dst", help="钟面时间是否为中国夏令时（1986-1991）"),
    timezone: float = typer.Option(8.0, "--timezone",
                                   help="出生记录所用标准时区（小时，东为正；默认 8=北京时间 UTC+8）"),
    geng_sihua: str = typer.Option("tiantong", "--geng-sihua",
                                   help="庚年四化忌星 tiantong(主流)|tianxiang(古法)"),
    leap_mode: str = typer.Option("as_month", "--leap-mode",
                                  help="闰月口径 as_month(按当月)|mid_split(十五分界)"),
    meta_json: str | None = typer.Option(None, "--meta-json", help="结构化结果落盘路径"),
    out_svg: str | None = typer.Option(None, "--svg", help="紫微盘 SVG 输出路径"),
):
    """紫微斗数排盘（引擎：x_iztro，见 README）。"""
    _validate_birth(year, month, day, hour, minute, gender, longitude, timezone)
    birth, config, nb = _resolve(year, month, day, hour, minute, gender, longitude,
                                 true_solar, day_change_hour, is_dst, timezone)
    config.ziwei_geng_sihua = geng_sihua
    config.ziwei_leap_month = leap_mode
    try:
        from .ziwei import chart as ziwei_chart
        zc = ziwei_chart.build(nb, gender, config)
        typer.echo(zc.markdown())
        if out_svg:
            svg = svg_report.ziwei_palace_svg(zc.palaces_for_svg(), note=zc.svg_note())
            with open(out_svg, "w", encoding="utf-8") as f:
                f.write(svg)
            typer.echo(f"紫微盘已写入 {out_svg}")
        _dump_meta(meta_json, {"tool": "ziwei", **dataclasses.asdict(zc)})
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
    timezone: float = typer.Option(8.0, "--timezone",
                                   help="出生记录所用标准时区（小时，东为正；默认 8=北京时间 UTC+8）"),
    target_year: int = typer.Option(..., "--target-year", help="要看的流年年份"),
):
    """流年分析：流年干支与原局、当前大运的合冲刑害（确定性关系事实）。"""
    _validate_birth(year, month, day, hour, minute, gender, longitude, timezone)
    birth, config, nb = _resolve(year, month, day, hour, minute, gender, longitude,
                                 True, 23, False, timezone)
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
    _validate_birth(year, month, day, hour, minute, "男", 120.0)
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
    typer.echo(f"公历 {year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}")
    typer.echo(f"农历 {nb.lunar_year}年{leap}{abs(lm)}月{nb.lunar_day}日  "
               f"{nb.lunar_year_ganzhi}年 生肖{nb.lunar.getYearShengXiao()}")
    typer.echo(f"四柱：{nb.eight_char.getYear()} {nb.eight_char.getMonth()} "
               f"{nb.eight_char.getDay()} {nb.eight_char.getTime()}")
    typer.echo("注：以上四柱为钟表时辰口径（未做真太阳时校正）；如需校正排盘，"
               "请用 bazi/ziwei 并传 --lng（出生地东经）。")
    typer.echo("当年节气（前 12 个）：")
    for e in jq:
        typer.echo(f"  {e['name']} {e['time']}")
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


def main() -> None:  # pragma: no cover
    app()


if __name__ == "__main__":  # pragma: no cover
    app()
