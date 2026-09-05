# -*- coding: utf-8 -*-
"""大六壬起课（排盘）：月将加时 → 天盘 → 四课 → 三传（九宗门）→ 十二天将 →
遁干、旬空、六亲、年命行年。

规则逐字依据《六壬大全》（明·郭载騋校，四库全书本，维基文库
research/fetched/liurendaquan_*.txt）：卷一「入手法」九宗门歌诀、卷二
「十二将释」贵神月将；歌诀引文见 fortune/liuren/text.py（程序化提取，
回归测试锁定逐字存在）。月将取太阳过宫（中气）口径，与《大全》卷二
「雨水后日躔娵訾，正月将（登明亥）」一致；底本「大雪后日躔析木，十月将」
之「大雪」与通法「小雪后功曹寅」不符，按通法并从俗（如实标注见 NOTES）。

⚠ 起课为确定性排盘规则；断语为经验规则，见 duanyu.py。
"""
from __future__ import annotations

from dataclasses import dataclass, field

from lunar_python import Lunar
from lunar_python.util import LunarUtil

#: 十二地支
ZHI = "子丑寅卯辰巳午未申酉戌亥"
#: 地支五行（六壬用，与四柱同）
ZHI_WUXING = {z: LunarUtil.WU_XING_ZHI[z] for z in ZHI}
GAN_WUXING = {g: LunarUtil.WU_XING_GAN[g] for g in "甲乙丙丁戊己庚辛壬癸"}
SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
KE = {a: b for a, b in (("木", "土"), ("土", "水"), ("水", "火"), ("火", "金"), ("金", "木"))}

#: 十干寄宫（《六壬大全》卷一入手法）：
#: 「甲课寅兮乙课辰，丙戊课巳不须论。丁己课未庚申上，辛戌壬亥是其真。癸课原来丑宫坐，分明不用四正神。」
GAN_JI = {"甲": "寅", "乙": "辰", "丙": "巳", "丁": "未", "戊": "巳",
          "己": "未", "庚": "申", "辛": "戌", "壬": "亥", "癸": "丑"}

#: 月将（太阳过宫中气 → 将支与将名），《六壬大全》卷二
#: 雨水后登明亥（正月将）……大寒后神后子（十二月将）。
#: 注：lunar-python getJieQiTable 中文本键为当年节气（自上年冬至起），英文键为次年
#: 同气，此处统一用中文键名并跨三年取值以覆盖年界。
JIE_QI_KEYS = ["雨水", "春分", "谷雨", "小满", "夏至", "大暑", "处暑", "秋分",
               "霜降", "小雪", "冬至", "大寒"]
YUE_JIANG = {"亥": "登明", "戌": "河魁", "酉": "从魁", "申": "传送",
             "未": "小吉", "午": "胜光", "巳": "太乙", "辰": "天罡",
             "卯": "太冲", "寅": "功曹", "丑": "大吉", "子": "神后"}
#: 中气 → 将支（太阳过宫）
JIE_QI_JIANG = dict(zip(JIE_QI_KEYS,
                         ["亥", "戌", "酉", "申", "未", "午", "巳", "辰",
                          "卯", "寅", "丑", "子"]))

#: 天乙贵人（十干 → 昼贵/夜贵），通行贵人歌
#: 「甲戊庚牛羊，乙己鼠猴乡，丙丁猪鸡位，壬癸蛇兔藏，六辛逢马虎，此是贵人方」
GUI_REN = {"甲": ("丑", "未"), "戊": ("丑", "未"), "庚": ("丑", "未"),
           "乙": ("子", "申"), "己": ("子", "申"),
           "丙": ("亥", "酉"), "丁": ("亥", "酉"),
           "壬": ("巳", "卯"), "癸": ("巳", "卯"),
           "辛": ("午", "寅")}

#: 十二天将顺布序（贵人起，顺布；逆行反序）。《六壬大全》卷二：
#: 「前有五位：一蛇、二雀、三合、四勾、五龙……后有五位：一后、二阴、三元、四常、五虎」
TIAN_JIANG = ["贵人", "螣蛇", "朱雀", "六合", "勾陈", "青龙",
              "天空", "白虎", "太常", "玄武", "太阴", "天后"]
#: 天将五行（天将本位五行，乘神以神论）
TIAN_JIANG_WUXING = {"贵人": "土", "螣蛇": "火", "朱雀": "火", "六合": "木",
                     "勾陈": "土", "青龙": "木", "天空": "土", "白虎": "金",
                     "太常": "土", "玄武": "水", "太阴": "金", "天后": "水"}

#: 三刑（六壬用，子卯相刑与四柱同表；自刑辰午酉亥）
XING = {"寅": "巳", "巳": "申", "申": "寅", "丑": "戌", "戌": "未", "未": "丑",
        "子": "卯", "卯": "子", "辰": "辰", "午": "午", "酉": "酉", "亥": "亥"}
CHONG = {"子": "午", "午": "子", "丑": "未", "未": "丑", "寅": "申", "申": "寅",
         "卯": "酉", "酉": "卯", "辰": "戌", "戌": "辰", "巳": "亥", "亥": "巳"}
#: 驿马（三合首冲）
YI_MA = {"申": "寅", "子": "寅", "辰": "寅", "寅": "申", "午": "申", "戌": "申",
         "巳": "亥", "酉": "亥", "丑": "亥", "亥": "巳", "卯": "巳", "未": "巳"}
#: 三合局（别责柔日用支前三合）
SAN_HE = {"申": "辰", "子": "申", "辰": "子", "寅": "戌", "午": "寅", "戌": "午",
          "巳": "酉", "酉": "丑", "丑": "巳", "亥": "卯", "卯": "未", "未": "亥"}
#: 干合（别责刚日用干合干之寄宫）
GAN_HE = {"甲": "己", "己": "甲", "乙": "庚", "庚": "乙", "丙": "辛", "辛": "丙",
          "丁": "壬", "壬": "丁", "戊": "癸", "癸": "戊"}

#: 八专日（两课无克之课日）：甲寅 丁未 己未 庚申 癸丑
BA_ZHUAN = {"甲寅", "丁未", "己未", "庚申", "癸丑"}

NOTES = {
    "小雪功曹": "《六壬大全》卷二底本作「大雪后日躔析木，十月将」，按太阳过宫通法当作"
                "「小雪后」（大雪为十一月节），本仓按通法从小雪后取功曹寅，如实标注。",
    "贵人昼夜": "昼贵/夜贵按占时定：卯辰巳午未申酉为昼用昼贵，戌亥子丑寅为夜用夜贵"
                "（通行法）；《大全》卷二「贵人从十干分书治、暮治」即昼夜两治。",
}


@dataclass
class LiuRenChart:
    year: int = 0
    month: int = 0
    day: int = 0
    hour: int = 0
    minute: int = 0
    day_ganzhi: str = ""          # 日干支
    hour_zhi: str = ""            # 占时支
    yue_jiang_zhi: str = ""       # 月将支
    yue_jiang_name: str = ""      # 月将名
    jie_qi: str = ""              # 过宫中气
    day_night: str = ""           # 昼/夜
    tian_pan: dict[str, str] = field(default_factory=dict)   # 地盘支 → 天盘神
    pan_tian: dict[str, str] = field(default_factory=dict)   # 天盘神 → 地盘支（酉下神用）
    gan_shang: str = ""           # 第一课（干上神）
    gan_yin: str = ""             # 第二课
    zhi_shang: str = ""           # 第三课（支上神）
    zhi_yin: str = ""             # 第四课
    san_chuan: list[str] = field(default_factory=list)   # 三传天盘神
    ke_ti: str = ""               # 课体名
    ke_ti_note: str = ""          # 课体说明（宗门/克名）
    gui_ren_zhi: str = ""         # 所用贵人支
    gui_shun: bool = True         # 贵人顺逆
    tian_jiang: dict[str, str] = field(default_factory=dict)  # 地盘支 → 天将
    dun_gan: dict[str, str] = field(default_factory=dict)     # 地盘支 → 遁干
    xun_shou: str = ""            # 旬首
    xun_kong: tuple[str, str] = ("", "")   # 旬空两支
    ben_ming: str = ""            # 本命（生年支）——需要生日时由 CLI 注入
    xing_nian: str = ""           # 行年支


def _solar_dt(solar) -> "datetime.datetime":
    import datetime as _dt
    return _dt.datetime(solar.getYear(), solar.getMonth(), solar.getDay(),
                        solar.getHour(), solar.getMinute(), solar.getSecond())


def month_jiang(solar_dt) -> tuple[str, str, str]:
    """按太阳过宫（中气）取月将：返回 (将支, 将名, 中气名)。"""
    y = solar_dt.year
    seen: set = set()
    cands = []  # (datetime, jieqi_key)
    for yy in (y - 1, y, y + 1):
        lunar = Lunar.fromYmdHms(yy, 6, 15, 12, 0, 0)  # 年中任取，取当年节气表
        table = lunar.getJieQiTable()
        for k in JIE_QI_KEYS:
            t = table.get(k)
            if t is not None:
                dt = _solar_dt(t)
                if dt in seen:
                    continue
                seen.add(dt)
                cands.append((dt, k))
    past = [c for c in cands if c[0] <= solar_dt]
    if not past:
        return YUE_JIANG["子"], "神后", "大寒"
    latest = max(past, key=lambda c: c[0])
    zhi = JIE_QI_JIANG[latest[1]]
    return zhi, YUE_JIANG[zhi], latest[1]


def _wuxing_rel(a_wx: str, b_wx: str) -> str:
    """a 对 b：生/克/比。"""
    if a_wx == b_wx:
        return "比"
    if SHENG[a_wx] == b_wx:
        return "生"
    if KE[a_wx] == b_wx:
        return "克"
    return "耗"


def qike(day_ganzhi: str, hour_zhi: str, yue_jiang_zhi: str) -> LiuRenChart:
    """起课主流程。"""
    c = LiuRenChart()
    c.day_ganzhi = day_ganzhi
    c.hour_zhi = hour_zhi
    c.yue_jiang_zhi = yue_jiang_zhi
    c.yue_jiang_name = YUE_JIANG[yue_jiang_zhi]
    day_gan = day_ganzhi[0]
    day_zhi = day_ganzhi[1]
    day_wx = GAN_WUXING[day_gan]

    # 1. 天盘：月将加时，顺布十二神
    tp = {}
    for i in range(12):
        tp[ZHI[(ZHI.index(hour_zhi) + i) % 12]] = ZHI[(ZHI.index(yue_jiang_zhi) + i) % 12]
    c.tian_pan = tp
    c.pan_tian = {v: k for k, v in tp.items()}

    # 2. 四课
    gan_ji = GAN_JI[day_gan]
    c.gan_shang = tp[gan_ji]
    c.gan_yin = tp[c.gan_shang]
    c.zhi_shang = tp[day_zhi]
    c.zhi_yin = tp[c.zhi_shang]

    # 3. 三传九宗门（《六壬大全》卷一入手法歌诀）
    si_ke = [c.gan_shang, c.gan_yin, c.zhi_shang, c.zhi_yin]
    # 四课上下五行：第一课下神以日干五行论（贼克「下」为日干），余以地支论
    xia_wx = [day_wx, ZHI_WUXING[c.gan_shang], ZHI_WUXING[day_zhi], ZHI_WUXING[c.zhi_shang]]
    shang_wx = [ZHI_WUXING[s] for s in si_ke]
    up_ke = [i for i in range(4) if KE[shang_wx[i]] == xia_wx[i]]    # 上克下
    down_ke = [i for i in range(4) if KE[xia_wx[i]] == shang_wx[i]]  # 下贼上

    chu = zhong = mo = None
    ke_ti = ke_ti_note = ""

    def _chuan(chu_shen: str):
        return chu_shen, tp[chu_shen], tp[tp[chu_shen]]

    if down_ke or up_ke:
        # 一 贼克法：先下贼后上克
        pool = down_ke if down_ke else up_ke
        if len(pool) == 1:
            chu, zhong, mo = _chuan(si_ke[pool[0]])
            ke_ti = "重审课" if down_ke else "元首课"
            ke_ti_note = "一下贼上" if down_ke else "一上克下"
        else:
            # 二 比用法：与日干阴阳比者
            bi = [i for i in pool
                  if (si_ke[i] in "子寅辰午申戌") == (day_gan in "甲丙戊庚壬")]
            if len(bi) == 1:
                chu, zhong, mo = _chuan(si_ke[bi[0]])
                ke_ti = "知一课（比用）"
                ke_ti_note = f"{'下贼上' if down_ke else '上克下'}多课，取与日干比者"
            else:
                # 三 涉害法：路逢多克为用；孟深仲浅季当休；复等柔辰刚日宜
                cands = bi or pool
                depths = []
                for i in cands:
                    shang = si_ke[i]
                    d = 0
                    # 上神自所临地盘宫顺行回本家，途中克地盘之数
                    cur = c.pan_tian[shang]
                    for _ in range(12):
                        if KE[ZHI_WUXING[shang]] == ZHI_WUXING[cur]:
                            d += 1
                        if cur == shang:
                            break
                        cur = ZHI[(ZHI.index(cur) + 1) % 12]
                    depths.append(d)
                mx = max(depths)
                top = [cands[j] for j, d in enumerate(depths) if d == mx]
                if len(top) == 1:
                    chu, zhong, mo = _chuan(si_ke[top[0]])
                    ke_ti = "涉害课"
                    ke_ti_note = f"涉害最深（{mx} 克）"
                else:
                    # 孟深仲浅季当休；复等柔辰刚日宜
                    meng = [i for i in top if si_ke[i] in "寅申巳亥"]
                    zhong2 = [i for i in top if si_ke[i] in "子午卯酉"]
                    chosen = meng or zhong2 or top
                    if len(chosen) > 1:
                        # 复等：刚日取干上、柔日取支上
                        chosen = [top[1]] if day_gan in "乙丁己辛癸" else [top[0]]
                    chu, zhong, mo = _chuan(si_ke[chosen[0]])
                    ke_ti = "涉害课"
                    ke_ti_note = "涉害复等，取孟深仲浅（复等柔辰刚日）"
    elif yue_jiang_zhi == hour_zhi:
        # 八 伏吟：无克刚干柔取辰
        if day_gan in "甲丙戊庚壬":
            chu = c.gan_shang
        else:
            chu = c.zhi_shang
        if XING[chu] == chu:
            # 初传自刑：中末颠倒日辰并（中=支上神，末=干上神）
            zhong = c.zhi_shang
            mo = c.gan_shang
            if XING[zhong] == zhong:
                mo = CHONG[zhong]
        else:
            zhong = XING[chu]
            if XING[zhong] == zhong:
                mo = CHONG[zhong]
            else:
                mo = XING[zhong]
        ke_ti = "伏吟课"
        ke_ti_note = "天地盘同位，无克按刑冲取传"
    elif yue_jiang_zhi == CHONG[hour_zhi]:
        # 九 返吟：有克亦为用（已在前面处理）；无克井栏射
        if day_zhi in ("丑", "未") and day_gan in "丁己辛":
            chu = YI_MA[day_zhi]
            if day_gan in "甲丙戊庚壬":
                zhong, mo = c.zhi_shang, c.gan_shang
            else:
                zhong, mo = c.gan_shang, c.zhi_shang
            ke_ti = "返吟课（井栏射）"
            ke_ti_note = "返吟无克，丑未日取驿马为初传"
        else:
            # 返吟无克、非井栏六日（九宗门中此况归井栏射，其余日子按通法仍以贼克论；
            # 此处保守回退并如实标注）
            chu, zhong, mo = c.gan_shang, c.zhi_shang, c.gan_shang
            ke_ti = "返吟课"
            ke_ti_note = "返吟无克（非井栏六日，回退取干上神）"
    else:
        # 四课无克且非伏吟返吟 → 遥克
        yao_ke_ri = [i for i in range(4) if KE[ZHI_WUXING[si_ke[i]]] == day_wx]  # 神遥克日
        ri_yao = [i for i in range(4) if KE[day_wx] == ZHI_WUXING[si_ke[i]]]      # 日遥克神
        if yao_ke_ri or ri_yao:
            pool = yao_ke_ri if yao_ke_ri else ri_yao
            yang = day_gan in "甲丙戊庚壬"
            if len(pool) == 1:
                chu, zhong, mo = _chuan(si_ke[pool[0]])
            else:
                bi = [i for i in pool if (si_ke[i] in "子寅辰午申戌") == yang]
                chu, zhong, mo = _chuan(si_ke[(bi or pool)[0]])
            ke_ti = "蒿矢课" if yao_ke_ri else "弹射课"
            ke_ti_note = "四课无克，神遥克日" if yao_ke_ri else "四课无克，日遥克神"
        elif day_ganzhi in BA_ZHUAN and c.gan_shang == c.zhi_shang \
                and c.gan_yin == c.zhi_yin:
            # 七 八专：两课无克
            if day_gan in "甲丙戊庚壬":
                chu = ZHI[(ZHI.index(c.gan_shang) + 2) % 12]  # 阳日干上神顺行三（连本位数）
            else:
                chu = ZHI[(ZHI.index(c.zhi_shang) - 2) % 12]  # 阴日支上神逆行三
            zhong = mo = c.gan_shang
            ke_ti = "八专课"
            ke_ti_note = "两课无克，阳日干上顺三、阴日支上逆三，中末总向日上"
        elif c.gan_shang != c.gan_yin and c.zhi_shang != c.zhi_yin:
            # 五 昴星：四课备、无遥无克
            if day_gan in "甲丙戊庚壬":
                chu = tp["酉"]              # 阳仰：酉上神
                zhong, mo = c.zhi_shang, c.gan_shang
            else:
                chu = tp[c.pan_tian["酉"]]  # 阴俯：酉下神（天盘酉所临宫之上神）
                zhong, mo = c.gan_shang, c.zhi_shang
            ke_ti = "昴星课"
            ke_ti_note = "四课备、无遥无克，阳仰阴俯酉位中"
        else:
            # 六 别责：四课不全三课备、无遥无克
            if day_gan in "甲丙戊庚壬":
                he_gan = GAN_HE[day_gan]
                chu = tp[GAN_JI[he_gan]]
            else:
                chu = tp[SAN_HE[day_zhi]]
            zhong = mo = c.gan_shang
            ke_ti = "别责课"
            ke_ti_note = "四课不全三课备，刚日干合上头神，柔日支前三合取，中末干中寄"
    c.san_chuan = [chu, zhong, mo]
    c.ke_ti = ke_ti
    c.ke_ti_note = ke_ti_note
    return c


def tian_jiang_bu(c: LiuRenChart, hour_zhi: str) -> None:
    """十二天将：昼夜贵 + 顺逆布将。"""
    day_gan = c.day_ganzhi[0]
    day_night = "昼" if hour_zhi in "卯辰巳午未申酉" else "夜"
    c.day_night = day_night
    gui = GUI_REN[day_gan][0] if day_night == "昼" else GUI_REN[day_gan][1]
    c.gui_ren_zhi = gui
    # 顺逆：贵人临地盘 亥子丑寅卯辰 → 顺布；巳午未申酉戌 → 逆布
    gui_lin = c.pan_tian[gui]
    shun = gui_lin in "亥子丑寅卯辰"
    c.gui_shun = shun
    # 贵人落宫后，顺布接螣蛇…天后；逆布接天后…螣蛇
    seq = TIAN_JIANG[1:] if shun else list(reversed(TIAN_JIANG))[:-1]
    start = ZHI.index(gui_lin)
    c.tian_jiang[gui_lin] = "贵人"
    for i, jiang in enumerate(seq, start=1):
        c.tian_jiang[ZHI[(start + i) % 12]] = jiang


def dun_gan_bu(c: LiuRenChart) -> None:
    """旬遁：以旬首甲加旬首支顺布十干；旬空为旬首支前两位（十干所不配）。"""
    dz = c.day_ganzhi
    idx = ZHI.index(dz[1])
    gan_idx = "甲乙丙丁戊己庚辛壬癸".index(dz[0])
    xun_idx = (idx - gan_idx) % 12            # 旬首支位
    c.xun_shou = "甲" + ZHI[xun_idx]
    c.xun_kong = (ZHI[(xun_idx - 2) % 12], ZHI[(xun_idx - 1) % 12])  # 旬首支前两位
    for i in range(12):
        c.dun_gan[ZHI[(xun_idx + i) % 12]] = "甲乙丙丁戊己庚辛壬癸"[i % 10]


def liu_qin(day_ganzhi: str, shen: str) -> str:
    """神（地支）对日干的六亲。"""
    day_wx = GAN_WUXING[day_ganzhi[0]]
    wx = ZHI_WUXING[shen]
    if wx == day_wx:
        return "兄弟"
    if SHENG[wx] == day_wx:
        return "父母"
    if SHENG[day_wx] == wx:
        return "子孙"
    if KE[wx] == day_wx:
        return "官鬼"
    return "妻财"


def xing_nian(birth_zhi: str, gender: str, age: int) -> str:
    """行年：男从本命顺数、女从本命逆数至虚岁（通法，一岁起本命）。"""
    step = (age - 1) % 12
    return ZHI[(ZHI.index(birth_zhi) + step) % 12] if gender == "男" \
        else ZHI[(ZHI.index(birth_zhi) - step) % 12]


def qike_full(year: int, month: int, day: int, hour: int, minute: int = 0,
              gender: str | None = None, birth_zhi: str | None = None,
              age: int | None = None) -> LiuRenChart:
    """完整起课：日干支、月将、天盘、四课、三传、天将、遁干、年命行年。

    输入为公历（占时钟表时间）；日干支按 0:00 换日（lunar-python sect=2 口径，
    夜子时归次日，与部分六壬传本 23:00 换日略有出入，如实标注）。
    """
    from lunar_python import Solar

    solar = Solar.fromYmdHms(year, month, day, hour, minute, 0)
    lunar = solar.getLunar()
    dz = lunar.getDayInGanZhi()
    hz = ZHI[((hour + 1) // 2) % 12]  # 占时支（钟表时辰，未做真太阳时校正）
    jzhi, jname, jq = month_jiang(_solar_dt(solar))
    c = qike(dz, hz, jzhi)
    c.year, c.month, c.day, c.hour, c.minute = year, month, day, hour, minute
    c.jie_qi = jq
    tian_jiang_bu(c, hz)
    dun_gan_bu(c)
    if birth_zhi:
        c.ben_ming = birth_zhi
        if gender and age:
            c.xing_nian = xing_nian(birth_zhi, gender, age)
    return c


__all__ = ["LiuRenChart", "qike", "qike_full", "tian_jiang_bu", "dun_gan_bu",
           "liu_qin", "month_jiang", "xing_nian", "ZHI", "ZHI_WUXING",
           "GAN_JI", "YUE_JIANG", "GUI_REN", "TIAN_JIANG", "XING", "CHONG",
           "YI_MA", "SAN_HE", "GAN_HE", "NOTES"]
