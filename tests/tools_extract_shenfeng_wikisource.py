#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""生成 fortune/bazi/shenfeng_text.py（《神峰通考》盖头说/病药说类/
雕枯旺弱四病说类/损益生长四药说类 逐字文本）。

数据源：research/fetched/shenfeng_wikisource.txt（维基文库《神峰通考》全文，
https://zh.wikisource.org/wiki/神峰通考，公版；由 tmp_wikisource_shenfeng.html
程序化抽段而成）。与影印本文字层（research/fetched/shenfeng.txt）双源互校：
引用句须同时逐字（去空白）存在于两源中，不满足者生成时报错剔除。

维基文库本个别字词仍有转录讹误（如「而」作「雨」、「至」作「全」、「未」作「夫」、
「口」作「中」、「干」作「下」），NOTES 如实标注；引用句均取两源一致的干净句。
"""
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC_WS = ROOT / "research" / "fetched" / "shenfeng_wikisource.txt"
SRC_PDF = ROOT / "research" / "fetched" / "shenfeng.txt"
OUT = ROOT / "fortune" / "bazi" / "shenfeng_text.py"

# (章名键, 起始标题段落, 结束标题段落或正文锚点)
CHAPTERS = [
    ("盖头说", "盖头说", "六亲说"),
    ("病药说类", "病药说类", "雕枯旺弱四病说类"),
    ("雕枯旺弱四病说类", "雕枯旺弱四病说类", "损益生长四药说类"),
    ("损益生长四药说类", "损益生长四药说类", "正官格"),
]

# 展示用引句候选（须在维基文库章文中逐字存在，且去空白后逐字存在于影印本文字层）
QUOTES_CANDIDATES = {
    "盖头说": [
        "大抵人之八字，类如此。八字中上四个字是头也，下地支四字是肚腹四肢也。",
        "凡有所害之物，露出头面，便是动物，就能作害。",
        "看八字以此盖头望见了，就识得人一生好歹，此是真传秘诀也。",
    ],
    "病药说类": [
        "何以为之病？原八字中原所害之神也；何以为之药？如八字原有所害之字，而得一字以去之",
        "有病方为贵，无伤不是奇；格中如去病，财禄两相随。",
        "从重者论",
    ],
    "雕枯旺弱四病说类": [
        "苟玉之不琢，虽曰荆山之美，则为无用之玉也",
        "若木不木而金不金，旺不旺而弱不弱，则五行之质有亏矣。",
        "是以八字贵有雕也。",
    ],
    "损益生长四药说类": [
        "何以谓之损？损者，损其有余也。",
        "何以谓之益？益者，益其不及也。",
        "何以谓之生也？六阳生处，真为生也。",
        "何以谓之长也？春蚕作茧，木气方敷。",
    ],
}

NOTES = {
    "盖头说": ("维基文库本转录自影印，个别字或讹：如「独有头为一身为端也」当为「…一身之端也」、"
              "「耳目中鼻」当为「耳目口鼻」、「如天下透此伤官」当为「如天干透…」、「盖球了头」当为「盖了头」；"
              "引用句均取与影印本文字层一致的干净句。"),
    "雕枯旺弱四病说类": ("维基文库本个别字或讹：如「雨贵有雕琢之功」当为「而贵…」、「金虽全宝也」当为"
                    "「金虽至宝也」、「夫曾见印绶」当为「未曾见印绶」、「桔」当为「枯」；引用句均取两源一致的干净句。"),
    "损益生长四药说类": ("维基文库本个别字或讹：如「金产竞宫」当为「金产兑宫」、「壁如」当为「譬如」；"
                    "引用句均取两源一致的干净句。"),
    "病药说类": "与影印本文字层互校一致。",
}

# 雕枯旺弱逐十神细分引句：key=十神类，(引句, 病类标签)；
# 须双源（维基文库+影印本）逐字互证，不满足者生成时剔除。
RULE_QUOTES_CANDIDATES: dict[str, list[tuple[str, str]]] = {
    "官杀": [
        ("见官星未曾有伤官", "雕：官星无伤官则太纯"),
        ("苟若官星无根，官从何出？", "枯：官星无根"),
        ("官星之气有余，则损其官星", "损：官有余则损之"),
        ("若官星太弱，宜行官旺之乡", "弱：官弱宜行官旺地"),
    ],
    "财": [
        ("见财星未曾有比劫", "雕：财星无比劫则太纯"),
        ("财星无根，财从何生？", "枯：财星无根"),
        ("财星之气有余，则损其财星", "损：财有余则损之"),
        ("财星太弱，宜行财旺之地", "弱：财弱宜行财旺地"),
    ],
    "印": [
        ("见印绶未曾有财星", "雕：印绶无财星则太纯"),
    ],
    "日主": [
        ("日干太旺者，宜行官杀运以制其日主", "旺：日主旺宜官杀制"),
        ("日主太弱，宜行身旺之地", "弱：日主弱宜行身旺地"),
    ],
    "比劫": [
        ("宜行比劫动以去财星", "旺：财旺宜行比劫（底本「比劫动」疑当作「比劫运」）"),
    ],
    "食伤": [],
}


def _norm(s: str) -> str:
    return re.sub(r"\s+", "", s)


def extract(ws: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for key, start_title, end_title in CHAPTERS:
        m = re.search(rf"^{re.escape(start_title)}$", ws, re.M)
        if not m:
            raise RuntimeError(f"维基文库本未找到章标题：{start_title}")
        e = re.search(rf"^{re.escape(end_title)}$", ws[m.end():], re.M)
        seg = ws[m.end():m.end() + e.start()] if e else ws[m.end():]
        out[key] = _norm(seg)
    return out


def main() -> int:
    ws = SRC_WS.read_text(encoding="utf-8")
    pdf = _norm(SRC_PDF.read_text(encoding="utf-8"))
    chapters = extract(ws)
    quotes: dict[str, list[str]] = {}
    dropped: list[str] = []
    for key, cands in QUOTES_CANDIDATES.items():
        keep = []
        for q in cands:
            nq = _norm(q)
            in_ws = nq in _norm(chapters[key])
            in_pdf = nq in pdf
            if in_ws and in_pdf:
                keep.append(q)
            else:
                dropped.append(f"{key} :: {q} (ws={in_ws}, pdf={in_pdf})")
        quotes[key] = keep
    if dropped:
        print("以下候选引句未通过双源互校，已剔除：")
        for d in dropped:
            print("  -", d)

    # 雕枯旺弱逐十神细分引句：对四章合文 + 影印本双源互证
    all4 = _norm("".join(chapters.values()))
    rule_quotes: dict[str, list[list[str]]] = {}
    for key, cands in RULE_QUOTES_CANDIDATES.items():
        keep = []
        for q, label in cands:
            nq = _norm(q)
            if nq in all4 and nq in pdf:
                keep.append([q, label])
            else:
                print(f"  RULE 剔除：{key} :: {q} (ws={nq in all4}, pdf={nq in pdf})")
        rule_quotes[key] = keep

    with OUT.open("w", encoding="utf-8") as f:
        f.write('"""《神峰通考》（明·张楠撰，公版）盖头说/病药说类/雕枯旺弱四病说类/\n')
        f.write("损益生长四药说类 逐字文本。\n\n")
        f.write("出处：research/fetched/shenfeng_wikisource.txt（维基文库全文，\n")
        f.write("https://zh.wikisource.org/wiki/神峰通考），与影印本文字层\n")
        f.write("research/fetched/shenfeng.txt 双源互校；由 tests/tools_extract_shenfeng_wikisource.py\n")
        f.write("程序化提取，一致性由 tests/test_shenfeng_text.py 回归锁定。\n")
        f.write("SHENFENG：章文；SHENFENG_QUOTES：双源互证引用句；NOTES：转录讹误如实标注；\n")
        f.write("RULE_QUOTES：雕枯旺弱逐十神细分引句（引句, 病类标签），同样双源互证。\n")
        f.write('"""\n\n')
        f.write("SHENFENG: dict[str, str] = {\n")
        for k, v in chapters.items():
            f.write(f"    {json.dumps(k, ensure_ascii=False)}: {json.dumps(v, ensure_ascii=False)},\n")
        f.write("}\n\nSHENFENG_QUOTES: dict[str, list[str]] = {\n")
        for k, v in quotes.items():
            f.write(f"    {json.dumps(k, ensure_ascii=False)}: {json.dumps(v, ensure_ascii=False)},\n")
        f.write("}\n\nNOTES: dict[str, str] = {\n")
        for k, v in NOTES.items():
            f.write(f"    {json.dumps(k, ensure_ascii=False)}: {json.dumps(v, ensure_ascii=False)},\n")
        f.write("}\n\nRULE_QUOTES: dict[str, list[list[str]]] = {\n")
        for k, v in rule_quotes.items():
            f.write(f"    {json.dumps(k, ensure_ascii=False)}: {json.dumps(v, ensure_ascii=False)},\n")
        f.write("}\n")
    print(f"已生成 {OUT}（章 {len(chapters)}，双源互证引用句 "
          f"{sum(len(v) for v in quotes.values())}，细分引句 "
          f"{sum(len(v) for v in rule_quotes.values())}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
