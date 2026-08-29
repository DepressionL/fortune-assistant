#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""生成 fortune/bazi/ditiansui_text.py（《滴天髓》通神论各章 + 何知章 逐字文本）。

数据源：research/fetched/ditiansui_liuji.txt（本仓《滴天髓原文（刘基注）》epub
经 tests/tools_extract_ditiansui.py 抽取；题宋·京图撰、明·刘基注，公版）。
与维基文库《滴天髓阐微》（research/fetched/ditiansui_wikisource.txt）互校：
关键异文在 VARIANTS 中如实标注（如「品泯」通行作「品汇」、「财贫神」通行作「财神」、
「相邀入洞户」通行排印本或作「相将入洞房」——两底本一致处按底本）。

程序化提取；一致性由 tests/test_ditiansui_text.py 回归锁定。
"""
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "research" / "fetched" / "ditiansui_liuji.txt"
OUT = ROOT / "fortune" / "bazi" / "ditiansui_text.py"

# 通神论 34 章 + 六亲论 6 章（何知章单列）
TITLES = ["天道", "地道", "人道", "知命", "理气", "配合", "天干", "地支",
          "干支总论", "形象", "方局", "八格", "体用", "精神", "月令", "生时",
          "衰旺", "中和", "源流", "通关", "官杀", "伤官", "清气", "浊气",
          "真神", "假神", "刚柔", "顺逆", "寒暖", "燥湿", "隐显", "众寡",
          "震兑", "坎离", "夫妻", "子女", "父母", "兄弟", "何知章", "女命章"]

# 流派引注用引句（须逐字存在于对应章文）
QUOTES = {
    "理气": "理承气行岂有常，进兮退兮宜抑扬。",
    "衰旺": "能知衰旺之真机，其于三命之奥，思过半矣。",
    "中和": "既识中和之正理，而于五行之妙，有全能焉。",
    "源流": "何处起根源？流到何方住？机括此中求，知来亦知去。",
    "通关": "关内有织女，关外有牛郎，此关若通也，相邀入洞户。",
    "顺逆": "顺逆不齐也，不可逆者，其气势而已矣。",
    "寒暖": "天道有寒暖，发育万物，人道行之，不可过也。",
    "燥湿": "地道有燥湿，生成品泯，人道得之，不可偏也。",
    "众寡": "强众而敌寡者，势在去其寡；强寡而敌众者，势在成乎众。",
    "震兑": "震兑主仁义之真机，势不两立，而有相成者存。",
    "坎离": "坎离宰天地之中气，成不独成，而有相持者在。",
}

VARIANTS = {
    "生成品泯": "「品泯」本仓 epub 与维基文库《滴天髓阐微》两底本俱同；通行排印本多作「品汇」。",
    "财贫神反不真": "「财贫神」两底本俱同；通行排印本多作「财神反不真」。",
    "相邀入洞户": "两底本俱作「相邀入洞户」；通行排印本或作「相将入洞房」。",
}


def _norm(s: str) -> str:
    return re.sub(r"\s+", "", s)


def extract(text: str) -> dict[str, str]:
    # 章标题行：中文数字 + 、 + 章名（排除 TOC 行首的 >）
    head = re.compile(r"^([一二三四五六七八九十]+)、([\u4e00-\u9fa5]{2,4})$", re.M)
    pos = []
    for m in head.finditer(text):
        if m.group(2) in TITLES and not text[:m.start()].rsplit("\n", 1)[-1].startswith(">"):
            pos.append((m.start(), m.group(2)))
    out: dict[str, str] = {}
    for i, (s, title) in enumerate(pos):
        e = pos[i + 1][0] if i + 1 < len(pos) else len(text)
        out[title] = _norm(text[s:e])
    return out


def main() -> int:
    text = SRC.read_text(encoding="utf-8")
    chapters = extract(text)
    missing = [t for t in TITLES if t not in chapters]
    if missing:
        raise RuntimeError(f"未提取到章节：{missing}")
    # 引句校验
    for key, q in QUOTES.items():
        if _norm(q) not in chapters[key]:
            raise RuntimeError(f"引句不在章文内：{key} :: {q}")
    # 何知章 8 句抽取：在原文（未去空白）上按行取，每句独立成行
    # （「寿」句底本无句号，按行取保持底本原字）
    m_hz = re.search(r"^五、何知章\s*$", text, re.M)
    m_nx = re.search(r"^六、女命章\s*$", text, re.M)
    if not m_hz or not m_nx:
        raise RuntimeError("何知章/女命章标题未找到")
    hz_raw = text[m_hz.end():m_nx.start()]
    hz_lines = [ln.strip() for ln in re.findall(r"^何知其人.+$", hz_raw, re.M)]
    if len(hz_lines) != 8:
        raise RuntimeError(f"何知章应 8 句，实际 {len(hz_lines)}：{hz_lines}")

    with OUT.open("w", encoding="utf-8") as f:
        f.write('"""《滴天髓》通神论各章 + 何知章 逐字文本。\n\n')
        f.write("出处：research/fetched/ditiansui_liuji.txt（本仓《滴天髓原文（刘基注）》epub\n")
        f.write("经 tests/tools_extract_ditiansui.py 抽取；题宋·京图撰、明·刘基注，公版），\n")
        f.write("与维基文库《滴天髓阐微》互校（research/fetched/ditiansui_wikisource.txt）。\n")
        f.write("由 tests/tools_extract_ditiansui_text.py 程序化提取；\n")
        f.write("一致性由 tests/test_ditiansui_text.py 回归锁定。\n")
        f.write("DITIANSUI：章文（原文+原注，按底本）；QUOTES：流派引注句；\n")
        f.write("HZ_LINES：何知章 8 句；VARIANTS：底本异文如实标注。\n")
        f.write('"""\n\n')
        f.write("DITIANSUI: dict[str, str] = {\n")
        for k, v in chapters.items():
            f.write(f"    {json.dumps(k, ensure_ascii=False)}: {json.dumps(v, ensure_ascii=False)},\n")
        f.write("}\n\nQUOTES: dict[str, str] = {\n")
        for k, v in QUOTES.items():
            f.write(f"    {json.dumps(k, ensure_ascii=False)}: {json.dumps(v, ensure_ascii=False)},\n")
        f.write("}\n\nHZ_LINES: list[str] = [\n")
        for v in hz_lines:
            f.write(f"    {json.dumps(v, ensure_ascii=False)},\n")
        f.write("]\n\nVARIANTS: dict[str, str] = {\n")
        for k, v in VARIANTS.items():
            f.write(f"    {json.dumps(k, ensure_ascii=False)}: {json.dumps(v, ensure_ascii=False)},\n")
        f.write("}\n")
    print(f"已生成 {OUT}（章 {len(chapters)}，何知章 {len(hz_lines)} 句）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
