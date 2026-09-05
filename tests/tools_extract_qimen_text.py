#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""生成 fortune/qimen/text.py（奇门起局歌诀逐字引文）。

数据源：
- research/fetched/奇门秘笈大全.txt（《奇门遁甲秘笈大全》epub 抽取，简体）；
- research/fetched/wikisource_yanbodiao sou.txt（《烟波钓叟歌》维基文库本，繁体）。
程序化校验引句逐字（去空白）存在于存档；一致性由 tests/test_qimen.py 回归锁定。
"""
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

ROOT = pathlib.Path(__file__).resolve().parents[1]
S_MJ = ROOT / "research" / "fetched" / "奇门秘笈大全.txt"
S_YB = ROOT / "research" / "fetched" / "wikisource_yanbodiao sou.txt"
OUT = ROOT / "fortune" / "qimen" / "text.py"

QUOTES = {
    "布仪": (S_MJ, "阳遁顺仪奇逆布，阴遁逆仪奇顺行"),
    "符使": (S_MJ, "符上之门为值使，十时一易堪凭据，值符常遣加时干，值使顺逆遁宫去"),
    "局数阳": (S_MJ, "冬至惊蛰一七四，小寒二八五同推，春分大寒三九六，立春八五二相随，"
               "榖雨小满五二八，雨水九六三为期，清明立夏四一七，芒种六三九为宜，"
               "十二节气时候定，上中下分是根基。"),
    "局数阴": (S_MJ, "夏至白露九三六，小暑八二五之间，大暑秋分七一四，立秋二五八循环，"
               "霜降小雪五八二，大雪四七一相关，处暑排来一四七，立冬寒露六九三，"
               "此是阴遁起例法，节气推宜仔细看。"),
    "天禽": (S_MJ, "惟天禽则无定位，寄西南而属中宫"),
    "值使例": (S_MJ, "休到二宫从二起"),
    "值使例注": (S_MJ, "如阳遁二局甲子日乙丑时，休门飞到坤二宫即住，便为值使门也"),
    "九星": (S_MJ, "如坎宫认天蓬为符，则天芮二、天冲三、天辅四、天禽五、天心六、"
             "天柱七、天任八、天英九也"),
    "八门": (S_MJ, "如干宫配开为使，则休门坎、生门艮、伤门震、杜门巽、景门离、"
             "死门坤、惊门兑也"),
    "八神阳": (S_MJ, "值符（火）、螣蛇（土）、太阴（金）、六合（木）、勾陈（土）、"
              "太常（五行化气）、朱雀（火）、九地（土）、九天（金），阳遁顺行"),
    "八神阴": (S_MJ, "值、螣、阴、六（白虎金）、常（玄武水）、陈、雀、地、天，阴遁逆布"),
    "八神替": (S_MJ, "阳遁朱雀即阴遁元武"),
    "八神替2": (S_MJ, "阳遁勾陈，阴遁白虎"),
    "烟波布仪": (S_YB, "陽遁順儀奇逆布，陰遁逆儀奇順行"),
    "烟波符使": (S_YB, "符上之門為直使，十時一易堪憑據"),
}

NOTES = {
    "三元": "三元按日干支符头（甲己+子午卯酉=上元、寅申巳亥=中元、辰戌丑未=下元）"
            "的拆补简化法；置闰、超神接气未实现，如实标注。",
    "中宫": "中五宫寄坤二宫（天禽寄坤、值使落中宫取死门），《秘笈大全》"
            "「惟天禽则无定位，寄西南而属中宫」。",
    "值使": "值使门加时支宫：按地支所在九宫（子坎一、丑寅艮八、卯震三、辰巳巽四、"
            "午离九、未申坤二、酉兑七、戌亥乾六），其余门按门序顺布——《秘笈大全》"
            "「休到二宫从二起……休门飞到坤二宫即住，便为值使门也」即此口径；"
            "另有「自旬首宫顺逆数地支」一说（六甲时门归本宫），本仓从《秘笈大全》"
            "九宫方位口径并如实标注分歧。",
    "八神": "阳遁值符螣蛇太阴六合勾陈朱雀九地九天顺布；阴遁以白虎玄武替勾陈朱雀、逆布"
            "（《秘笈大全》「阳遁朱雀即阴遁元武」「阳遁勾陈，阴遁白虎」）。",
    "换日": "日干支按 0:00 换日（lunar-python 口径；夜子时归次日）。",
}


def _norm(s: str) -> str:
    return re.sub(r"\s+", "", s)


def main() -> int:
    mj = _norm(S_MJ.read_text(encoding="utf-8"))
    yb = _norm(S_YB.read_text(encoding="utf-8"))
    for key, (src, q) in QUOTES.items():
        text = mj if src == S_MJ else yb
        if _norm(q) not in text:
            raise RuntimeError(f"引句不在存档中：{key} :: {q}")
    with OUT.open("w", encoding="utf-8") as f:
        f.write('"""奇门起局歌诀逐字引文（《奇门遁甲秘笈大全》简体本 + 《烟波钓叟歌》\n')
        f.write("维基文库本，程序化提取，tests/test_qimen.py 回归锁定）。\n")
        f.write("NOTES：口径分歧与简化如实标注。\n""" + '"""\n\n')
        f.write("QUOTES: dict[str, str] = {\n")
        for k, (_, q) in QUOTES.items():
            f.write(f"    {json.dumps(k, ensure_ascii=False)}: {json.dumps(q, ensure_ascii=False)},\n")
        f.write("}\n\nNOTES: dict[str, str] = {\n")
        for k, v in NOTES.items():
            f.write(f"    {json.dumps(k, ensure_ascii=False)}: {json.dumps(v, ensure_ascii=False)},\n")
        f.write("}\n")
    print(f"已生成 {OUT}（引句 {len(QUOTES)}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
