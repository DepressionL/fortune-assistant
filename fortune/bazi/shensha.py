"""八字神煞：核心神煞判定（干查/支查/月令查/旬空）。

表与口诀来源：research/shensha_tables.md —— 以《三命通会》（维基文库）、《渊海子平》
原文逐条核验；分歧处已标注。索引基准由 config.shensha_base 决定：
"day"（默认，子平法：以日干/日支查）| "year"（古法禄命：以年干/年支查）。
天德/月德始终按月令（节气月支）查，空亡按日柱旬查。

实现说明：本模块只做「判定是否存在」，不带吉凶断语；
神煞组合解读属经验范畴，报告层只作罗列。
"""
from __future__ import annotations

from dataclasses import dataclass

from .chart import BaziChart, PILLAR_NAMES

GAN_CHARS = "甲乙丙丁戊己庚辛壬癸"
ZHI_CHARS = "子丑寅卯辰巳午未申酉戌亥"

# ---------- 干查神煞（以 config.shensha_base 选日干或年干） ----------
# 天乙贵人（版本一，主流：《三命通会》卷三「甲戊庚牛羊…六辛逢马虎」）
TIANYI = {
    "甲": ("丑", "未"), "戊": ("丑", "未"), "庚": ("丑", "未"),
    "乙": ("子", "申"), "己": ("子", "申"),
    "丙": ("酉", "亥"), "丁": ("酉", "亥"),
    "壬": ("卯", "巳"), "癸": ("卯", "巳"),
    "辛": ("午", "寅"),
}
#: 版本二（庚→寅午，个别传本），默认不用
TIANYI_V2 = {**TIANYI, "庚": ("寅", "午")}

# 太极贵人（《三命通会》卷三）
TAIJI = {
    "甲": ("子", "午"), "乙": ("子", "午"),
    "丙": ("卯", "酉"), "丁": ("卯", "酉"),
    "戊": ("辰", "戌", "丑", "未"), "己": ("辰", "戌", "丑", "未"),
    "庚": ("寅", "亥"), "辛": ("寅", "亥"),
    "壬": ("巳", "申"), "癸": ("巳", "申"),
}

# 文昌贵人（主流口诀「甲乙巳午报君知…」，与《三命通会》卷三另一套不同，见研究文档 §3）
WENCHANG = {
    "甲": "巳", "乙": "午", "丙": "申", "丁": "酉", "戊": "申",
    "己": "酉", "庚": "亥", "辛": "子", "壬": "寅", "癸": "卯",
}

# 禄神（十干禄，《三命通会》卷三）
LU = {
    "甲": "寅", "乙": "卯", "丙": "巳", "丁": "午", "戊": "巳",
    "己": "午", "庚": "申", "辛": "酉", "壬": "亥", "癸": "子",
}

# 羊刃（阳干禄前一位；主流「阴干无刃」，《三命通会》卷三论羊刃）
YANGREN = {"甲": "卯", "丙": "午", "戊": "午", "庚": "酉", "壬": "子"}
#: 少数派阴刃（帝旺位），默认不用
YANGREN_YIN = {"乙": "寅", "丁": "巳", "己": "巳", "辛": "申", "癸": "亥"}

# 金舆（禄前二辰，《三命通会》卷三论金舆「金舆常居禄前二辰」）
JINYU = {"甲": "辰", "乙": "巳", "丙": "未", "丁": "申", "戊": "未",
         "己": "申", "庚": "戌", "辛": "亥", "壬": "丑", "癸": "寅"}

# 学堂/词馆（日干长生位=学堂、临官位=词馆；《三命通会》卷三论学堂词馆
# 原文以纳音长生/临官立论，通行另有日干派，此处采用日干派并标注）
XUETANG = {"甲": "亥", "乙": "午", "丙": "寅", "丁": "酉", "戊": "寅",
           "己": "酉", "庚": "巳", "辛": "子", "壬": "申", "癸": "卯"}
CIGUAN = {"甲": "寅", "乙": "卯", "丙": "巳", "丁": "午", "戊": "巳",
          "己": "午", "庚": "申", "辛": "酉", "壬": "亥", "癸": "子"}

# 三奇（《三命通会》卷三论三奇；顺布）
SANQI = (("天上三奇", "甲戊庚"), ("地下三奇", "乙丙丁"), ("人中三奇", "壬癸辛"))

# 十恶大败（十干禄入空亡之十日，《三命通会》卷三论十恶大败；
# 维基文库本「乙丑」为传本异文，按定义应为「己丑」，从通行）
SHI_E = {"甲辰", "乙巳", "丙申", "丁亥", "戊戌", "己丑",
         "庚辰", "辛巳", "壬申", "癸亥"}

# ---------- 支查神煞（以 config.shensha_base 选日支或年支） ----------
_YIMA = {"申": "寅", "子": "寅", "辰": "寅", "寅": "申", "午": "申", "戌": "申",
         "巳": "亥", "酉": "亥", "丑": "亥", "亥": "巳", "卯": "巳", "未": "巳"}
_TAOHUA = {"申": "酉", "子": "酉", "辰": "酉", "寅": "卯", "午": "卯", "戌": "卯",
           "巳": "午", "酉": "午", "丑": "午", "亥": "子", "卯": "子", "未": "子"}
_HUAGAI = {"申": "辰", "子": "辰", "辰": "辰", "寅": "戌", "午": "戌", "戌": "戌",
           "巳": "丑", "酉": "丑", "丑": "丑", "亥": "未", "卯": "未", "未": "未"}
_JIANGXING = {"申": "子", "子": "子", "辰": "子", "寅": "午", "午": "午", "戌": "午",
              "巳": "酉", "酉": "酉", "丑": "酉", "亥": "卯", "卯": "卯", "未": "卯"}
_JIESHA = {"申": "巳", "子": "巳", "辰": "巳", "寅": "亥", "午": "亥", "戌": "亥",
           "巳": "寅", "酉": "寅", "丑": "寅", "亥": "申", "卯": "申", "未": "申"}
_ZAISHA = {"申": "午", "子": "午", "辰": "午", "寅": "子", "午": "子", "戌": "子",
           "巳": "卯", "酉": "卯", "丑": "卯", "亥": "酉", "卯": "酉", "未": "酉"}
_GUCHEN = {"亥": "寅", "子": "寅", "丑": "寅", "寅": "巳", "卯": "巳", "辰": "巳",
           "巳": "申", "午": "申", "未": "申", "申": "亥", "酉": "亥", "戌": "亥"}
_GUASU = {"亥": "戌", "子": "戌", "丑": "戌", "寅": "丑", "卯": "丑", "辰": "丑",
          "巳": "辰", "午": "辰", "未": "辰", "申": "未", "酉": "未", "戌": "未"}
_HONGLUAN = {"子": "卯", "丑": "寅", "寅": "丑", "卯": "子", "辰": "亥", "巳": "戌",
             "午": "酉", "未": "申", "申": "未", "酉": "午", "戌": "巳", "亥": "辰"}
#: 天喜 = 红鸾对冲
_TIANXI = {k: ZHI_CHARS[(ZHI_CHARS.index(v) + 6) % 12] for k, v in _HONGLUAN.items()}

# 亡神（三合局泄位，《三命通会》卷三论劫煞亡神：申子辰→亥、寅午戌→巳、
# 巳酉丑→申、亥卯未→寅）
_WANGSHEN = {"申": "亥", "子": "亥", "辰": "亥", "寅": "巳", "午": "巳", "戌": "巳",
             "巳": "申", "酉": "申", "丑": "申", "亥": "寅", "卯": "寅", "未": "寅"}

# ---------- 月令查 ----------
# 天德（《三命通会》卷三：正丁二坤三壬四辛五乾六甲七癸八艮九丙十乙十一巽十二庚；
# 值可为干或支）
TIANDE = {"寅": "丁", "卯": "申", "辰": "壬", "巳": "辛", "午": "亥", "未": "甲",
          "申": "癸", "酉": "寅", "戌": "丙", "亥": "乙", "子": "巳", "丑": "庚"}
# 月德（《三命通会》卷三：寅午戌月在丙、申子辰月在壬、亥卯未月在甲、巳酉丑月在庚；
# 文本小结处「癸」为讹，主流取丙壬甲庚）
YUEDE = {"寅": "丙", "午": "丙", "戌": "丙", "申": "壬", "子": "壬", "辰": "壬",
         "亥": "甲", "卯": "甲", "未": "甲", "巳": "庚", "酉": "庚", "丑": "庚"}


@dataclass
class ShenShaHit:
    """一条神煞命中记录。"""
    name: str            # 神煞名
    basis: str           # 判定依据说明（如「日干甲」）
    positions: list[str]  # 命中的柱（如 ["月柱","时柱"]）
    values: list[str]     # 命中的干支
    note: str = ""        # 分歧/出处注记

    def __str__(self) -> str:  # pragma: no cover
        pos = "、".join(f"{p}({v})" for p, v in zip(self.positions, self.values))
        return f"{self.name}：{self.basis} → {pos}{'（' + self.note + '）' if self.note else ''}"


def compute(chart: BaziChart, base: str = "day") -> list[ShenShaHit]:
    """计算八字核心神煞。

    :param base: "day"（日干/日支，子平主流）| "year"（年干/年支，古法）。
    """
    assert base in ("day", "year")
    hits: list[ShenShaHit] = []
    gans, zhis = chart.gans(), chart.zhis()
    key_gan = chart.day_master if base == "day" else gans[0]
    key_zhi = chart.day_zhi if base == "day" else zhis[0]
    basis_label = "日干" if base == "day" else "年干"
    basis_label_zhi = "日支" if base == "day" else "年支"

    def zhi_hit(name, table, key, key_label, note=""):
        target = table[key]
        pos = [PILLAR_NAMES[i] for i, z in enumerate(zhis) if z == target]
        if pos:
            hits.append(ShenShaHit(name, f"{key_label}{key}", pos, [target] * len(pos), note))

    def gan_hit(name, table, key, note=""):
        targets = table[key]
        if isinstance(targets, str):
            targets = (targets,)
        pos, vals = [], []
        for i, z in enumerate(zhis):
            if z in targets:
                pos.append(PILLAR_NAMES[i]); vals.append(z)
        if pos:
            hits.append(ShenShaHit(name, f"{basis_label}{key}", pos, vals, note))

    # 干查
    gan_hit("天乙贵人", TIANYI, key_gan,
            note="版本一（主流，甲戊庚牛羊）；另有「庚辛逢虎马」别传未采")
    gan_hit("太极贵人", TAIJI, key_gan)
    gan_hit("文昌贵人", WENCHANG, key_gan,
            note="主流口诀「甲乙巳午报君知」；《三命通会》卷三另有异表")
    gan_hit("禄神", LU, key_gan)
    gan_hit("金舆", JINYU, key_gan,
            note="禄前二辰；《三命通会》卷三论金舆「金舆常居禄前二辰，如甲子人禄在寅，辰为金舆是也」")
    gan_hit("学堂", XUETANG, key_gan,
            note="日干长生位；《三命通会》卷三论学堂词馆「长生乃学堂之正位」（原文兼举纳音派，此处采日干派）")
    gan_hit("词馆", CIGUAN, key_gan,
            note="日干临官位；《三命通会》卷三论学堂词馆「临官乃词馆正位」（口径争议同学堂）")
    # 三奇（顺布）：三干同见于四柱且按年→时柱序顺布（倒乱不判）
    seq = "".join(gans)
    for sname, trio in SANQI:
        idx = [seq.find(c) for c in trio]
        if all(i >= 0 for i in idx) and idx == sorted(idx) and len(set(idx)) == len(trio):
            hits.append(ShenShaHit(
                f"三奇（{sname}）", f"四柱天干{''.join(gans)}", ["四柱"], [trio],
                note=f"{trio} 顺布；《三命通会》卷三论三奇（通行分类：天上甲戊庚/地下乙丙丁/"
                     "人中壬癸辛；三命通会引《珞琭子》以乙丙丁为天上三奇、甲戊庚亦以为天上三奇，"
                     "两说并列）"))
    if key_gan in YANGREN:
        gan_hit("羊刃", YANGREN, key_gan, note="阳干禄前一位；主流阴干无刃")
    else:
        hits.append(ShenShaHit("羊刃", f"{basis_label}{key_gan}（阴干）", [], [],
                               note="主流：阴干无刃（《三命通会》论羊刃），仅见伤官论"))

    # 支查
    zhi_hit("驿马", _YIMA, key_zhi, basis_label_zhi,
            note="三合局起马；《三命通会》卷三论驿马「驿马者，三命中发用，喜庆之神」")
    zhi_hit("桃花(咸池)", _TAOHUA, key_zhi, basis_label_zhi)
    zhi_hit("华盖", _HUAGAI, key_zhi, basis_label_zhi)
    zhi_hit("将星", _JIANGXING, key_zhi, basis_label_zhi)
    zhi_hit("劫煞", _JIESHA, key_zhi, basis_label_zhi)
    zhi_hit("灾煞", _ZAISHA, key_zhi, basis_label_zhi)
    zhi_hit("亡神", _WANGSHEN, key_zhi, basis_label_zhi,
            note="三合局泄位；《三命通会》卷三论劫煞亡神「申子辰以亥为亡神」等")
    zhi_hit("孤辰", _GUCHEN, key_zhi, basis_label_zhi)
    zhi_hit("寡宿", _GUASU, key_zhi, basis_label_zhi)
    # 红鸾/天喜：主流以年支查（择日体系），不受 shensha_base 影响
    yb = zhis[0]
    for name, tab in (("红鸾", _HONGLUAN), ("天喜", _TIANXI)):
        target = tab[yb]
        pos = [PILLAR_NAMES[i] for i, z in enumerate(zhis) if z == target]
        if pos:
            hits.append(ShenShaHit(name, f"年支{yb}", pos, [target] * len(pos),
                                   note="以年支查（择日通行；古籍正文出处待考，见研究文档 §15）"))

    # 天罗地网（《三命通会》卷三论天罗地网：戌亥=天罗、辰巳=地网；男怕天罗、女怕地网）
    tl = [PILLAR_NAMES[i] for i, z in enumerate(zhis) if z in ("戌", "亥")]
    dw = [PILLAR_NAMES[i] for i, z in enumerate(zhis) if z in ("辰", "巳")]
    if tl:
        hits.append(ShenShaHit("天罗", "四柱", tl, ["戌/亥"] * len(tl),
                               note=f"戌亥为天罗，{'男命忌' if chart.gender == '男' else '女命不妨'}；"
                                    "《三命通会》「天倾西北，戌亥者，六阴之终也」（纳音派火命天罗之说未采）"))
    if dw:
        hits.append(ShenShaHit("地网", "四柱", dw, ["辰/巳"] * len(dw),
                               note=f"辰巳为地网，{'女命忌' if chart.gender == '女' else '男命不妨'}；"
                                    "《三命通会》「地陷东南，辰巳者，六阳之终也」（纳音派水土命地网之说未采）"))

    # 十恶大败（十干禄入空亡之十日，仅看日柱）
    dgz = chart.pillar("日柱").gan_zhi
    if dgz in SHI_E:
        hits.append(ShenShaHit("十恶大败", f"日柱{dgz}", ["日柱"], [dgz],
                               note="十干禄入空亡；《三命通会》卷三论十恶大败。"
                                    "维基文库本作「乙丑」，按定义应为「己丑」，从通行"))

    # 月令查：天德（值可为干或支）、月德（干）
    mz = chart.pillar("月柱").zhi
    td = TIANDE[mz]
    if td in GAN_CHARS:
        pos = [PILLAR_NAMES[i] for i, g in enumerate(gans) if g == td]
    else:
        pos = [PILLAR_NAMES[i] for i, z in enumerate(zhis) if z == td]
    if pos:
        hits.append(ShenShaHit("天德贵人", f"月令{mz}", pos, [td] * len(pos)))
    yd = YUEDE[mz]
    pos = [PILLAR_NAMES[i] for i, g in enumerate(gans) if g == yd]
    if pos:
        hits.append(ShenShaHit("月德贵人", f"月令{mz}", pos, [yd] * len(pos),
                               note="月德取丙壬甲庚（《三命通会》小结「癸」为讹）"))

    # 旬空（日柱旬）
    dk = chart.pillar("日柱").xun_kong
    hits.append(ShenShaHit("空亡", f"日柱{chart.pillar('日柱').gan_zhi}（{chart.pillar('日柱').xun}旬）",
                           ["日柱"], [dk],
                           note="与六爻旬空同表"))

    return hits
