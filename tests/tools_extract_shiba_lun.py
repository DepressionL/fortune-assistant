#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""生成 fortune/liuyao/shiba_lun_text.py（《卜筮正宗》十八论逐字文本）。

数据源（双源，按章标注来源）：
- A = research/fetched/bushizhengzong.txt（清校注排印本转码存档）：第 1–11、16–18 章，
  正文完整、字迹清楚；该本「四生逐位论」误刻为「第六」（目录作第八）；
- B = research/fetched/shidian_18lun_raw.txt（識典古籍《卜筮正宗》卷三影印
  OCR 文字层，页面 https://www.shidianguji.com/zh/book/HY0057/...）：第 12–15 章
  （A 本缺此四章），个别字词存 OCR 噪声（如「句空」当作「旬空」「田函」当作「田园」）。

程序化提取；一致性由 tests/test_shiba_lun.py 回归锁定（章文逐字存在于对应存档、
引用句逐字存在于章文）。
"""
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC_A = ROOT / "research" / "fetched" / "bushizhengzong.txt"
SRC_B = ROOT / "research" / "fetched" / "shidian_18lun_raw.txt"
OUT = ROOT / "fortune" / "liuyao" / "shiba_lun_text.py"

# (章名键, 底本标题) —— A 本
A_CHAPTERS = [
    ("用神分类定例第一", "用神分类定例第一"),
    ("世应论用神第二", "世应论用神第二"),
    ("用神问答第三", "用神问答第三"),
    ("原忌仇神论第四", "原忌仇神论第四"),
    ("飞神正论第五", "飞神正论第五"),
    ("伏神正传第六", "伏神正传第六"),
    ("六兽评论第七", "六兽评论第七"),
    ("四生逐位论第八", "四生逐位论第六"),  # 底本误刻「第六」，目录作第八
    ("月破论第九", "月破论第九"),
    ("旬空论第十", "旬空论第十"),
    ("反吟卦定例第十一", "反吟卦定例第十一"),
    ("绝处逄生克处逄生论第十六", "绝处逄生克处逄生论第十六"),
    ("变出进退神论第十七", "变出进退神论第十七"),
    ("卦有验不验论第十八", "卦有验不验论第十八"),
]

# (章名键, 底本标题含尾标点) —— B 本（識典古籍影印 OCR）
B_CHAPTERS = [
    ("伏吟卦定例第十二", "伏吟卦定例第十二。"),
    ("旺相休囚論第十三", "旺相休囚論第十三。"),
    ("合中帶剋論第十四", "合中帶剋論第十四。"),
    ("合處逢冲，冲中逢合論第十五", "合處逢冲，冲中逢合論第十五。"),
]

# 展示用引句（须逐字存在于对应章文中；生成器逐一校验，不满足则报错）
QUOTES = {
    "用神分类定例第一": [],
    "世应论用神第二": ["凡卦中世应二爻，世为自己，应作他人，世应相生相合是云宾主相投；"
                  "世应相克相冲可见两情不睦。"],
    "用神问答第三": [],
    "原忌仇神论第四": ["凡占卦要知原神，先看用神何爻，生用神之爻即是原神也"],
    "飞神正论第五": ["凡卦既有伏神，伏神之上者飞神一也"],
    "伏神正传第六": ["夫伏神者，谓卦之有缺用神，纔看用神伏于何爻之下"],
    "六兽评论第七": ["略举六神取用，莫将六兽推尊"],
    "四生逐位论第八": ["火生于寅也，金生于巳也，水土生于申也，木生于亥也"],
    "月破论第九": ["凡卦中月破之爻，乃关因之所现也。动者亦能生克他爻，变者亦能生克本爻，"
                "目下虽破出月不破矣！今日虽破，值日不破矣！"],
    "旬空论第十": ["凡卦中爻遇旬空，乃神机发现于此也"],
    "反吟卦定例第十一": ["卦有反吟，卦变相冲也．爻之反吟，爻变相冲也"],
    "伏吟卦定例第十二": ["伏吟卦有三：乾卦變震，震變乾，无妄變大壯，大壯變无妄。"
                    "此子寅辰復化子寅辰，午申戌復化午申戌，內外卦之伏吟一也。"],
    "旺相休囚論第十三": ["凡卦中旺相之爻，倘被日辰及動爻剋制，目下貪榮得令，"
                     "過時仍受其毒，此旺相者，暫時之用也。"],
    "合中帶剋論第十四": ["凡卦中子爻變丑，戌爻變卯，此子與丑合，卯與戌合，"
                     "合中帶剋，合三剋七之分。"],
    "合處逢冲，冲中逢合論第十五": ["合處逢冲，謀雖成而終散；冲中逢合，事已散而復成。"],
    "绝处逄生克处逄生论第十六": ["金绝于寅，木绝于申，水土绝于巳，火绝于亥"],
    "变出进退神论第十七": ["凡卦中亥变子，丑变辰，寅变卯，辰变未，巳变午，未变戌，"
                       "申变酉，戌变丑，乃进神也",
                       "凡卦中子变亥，戌变未，酉变申，未变辰，午变巳，辰变丑，"
                       "卯变寅，丑变戌，乃退神也"],
    "卦有验不验论第十八": ["凡人问卦，惟致诚可以感格神明",
                       "又或一事而今日占之，明日又占之，或一人连占四五卦，"
                       "是再三渎则不告，不验也"],
}


def _norm(s: str) -> str:
    return re.sub(r"\s+", "", s)


def extract_a(text: str) -> dict[str, str]:
    """A 本：从正文「十八论」标题行后起，按标题链切章。"""
    # 正文标题「十八论」独立成行（出现在最末一次）
    heads = [m for m in re.finditer(r"^\s*十八论\s*$", text, re.M)]
    if not heads:
        raise RuntimeError("A 本未找到正文「十八论」标题")
    start = heads[-1].end()
    body = text[start:]
    out: dict[str, str] = {}
    for i, (key, title) in enumerate(A_CHAPTERS):
        nxt = A_CHAPTERS[i + 1][1] if i + 1 < len(A_CHAPTERS) else None
        p = body.find(title)
        if p < 0:
            raise RuntimeError(f"A 本未找到章标题：{title}")
        q = body.find(nxt, p + 1) if nxt else len(body)
        seg = body[p + len(title):q]
        out[key] = _norm(seg)
    return out


def extract_b(text: str) -> dict[str, str]:
    """B 本（識典 OCR）：按标题（含尾标点）切章，行间无分隔拼接。"""
    out: dict[str, str] = {}
    for i, (key, title) in enumerate(B_CHAPTERS):
        nxt = B_CHAPTERS[i + 1][1] if i + 1 < len(B_CHAPTERS) else "絶處逢生，剋處逢生論第十六"
        p = text.find(title)
        if p < 0:
            raise RuntimeError(f"B 本未找到章标题：{title}")
        q = text.find(nxt, p + 1)
        seg = text[p + len(title):q if q > 0 else len(text)]
        out[key] = _norm(seg)
    return out


def main() -> int:
    ta = SRC_A.read_text(encoding="utf-8")
    tb = SRC_B.read_text(encoding="utf-8")
    chapters = extract_a(ta)
    chapters.update(extract_b(tb))
    assert len(chapters) == 18, f"章节数 {len(chapters)} != 18"
    # 引用句校验
    for key, qs in QUOTES.items():
        if key not in chapters:
            raise RuntimeError(f"QUOTES 引用未收录的章：{key}")
        for q in qs:
            if _norm(q) not in _norm(chapters[key]):
                raise RuntimeError(f"引用句不在章文内：{key} :: {q}")

    src_a = "research/fetched/bushizhengzong.txt（清校注排印本，GB18030 转码存档）"
    src_b = ("research/fetched/shidian_18lun_raw.txt（識典古籍《卜筮正宗》卷三影印 OCR 文字层，"
             "个别字词存 OCR 噪声，如「句空」当作「旬空」「田函」当作「田园」）")
    provenance = {k: src_a for k, _ in A_CHAPTERS}
    provenance.update({k: src_b for k, _ in B_CHAPTERS})
    notes = {
        "四生逐位论第八": "底本误刻「四生逐位论第六」，目录作第八，此处按目录命名。",
        "旺相休囚論第十三": "識典 OCR 底本；「句空」当作「旬空」。",
        "合中帶剋論第十四": "識典 OCR 底本。",
        "合處逢冲，冲中逢合論第十五": "識典 OCR 底本。",
        "伏吟卦定例第十二": "識典 OCR 底本。",
    }
    with OUT.open("w", encoding="utf-8") as f:
        f.write('"""《卜筮正宗》卷三「十八论」逐字文本（双源按章标注，程序化提取）。\n\n')
        f.write("出处：第 1–11、16–18 章 = " + src_a + "；\n")
        f.write("第 12–15 章（该本所缺）= " + src_b + "。\n")
        f.write("由 tests/tools_extract_shiba_lun.py 程序化提取，非手工转写；\n")
        f.write("一致性由 tests/test_shiba_lun.py 回归锁定（章文逐字存在于对应存档、\n")
        f.write("引用句逐字存在于章文）。《卜筮正宗》清·王洪绪撰，公版。\n")
        f.write("SHIBA_LUN：章文；PROVENANCE：按章来源；QUOTES：展示用引句；\n")
        f.write("NOTES：底本刊误/OCR 噪声如实标注。\n""" + '"""\n\n')
        # 按章号排序输出（1–18）
        ordered_keys = [k for k, _ in A_CHAPTERS[:11]] + \
                       [k for k, _ in B_CHAPTERS] + \
                       [k for k, _ in A_CHAPTERS[11:]]
        f.write("SHIBA_LUN: dict[str, str] = {\n")
        for k in ordered_keys:
            f.write(f"    {json.dumps(k, ensure_ascii=False)}: {json.dumps(chapters[k], ensure_ascii=False)},\n")
        f.write("}\n\nPROVENANCE: dict[str, str] = {\n")
        for k in ordered_keys:
            f.write(f"    {json.dumps(k, ensure_ascii=False)}: {json.dumps(provenance[k], ensure_ascii=False)},\n")
        f.write("}\n\nQUOTES: dict[str, list[str]] = {\n")
        for k in ordered_keys:
            f.write(f"    {json.dumps(k, ensure_ascii=False)}: {json.dumps(QUOTES[k], ensure_ascii=False)},\n")
        f.write("}\n\nNOTES: dict[str, str] = {\n")
        for k in ordered_keys:
            if k in notes:
                f.write(f"    {json.dumps(k, ensure_ascii=False)}: {json.dumps(notes[k], ensure_ascii=False)},\n")
        f.write("}\n")
    print(f"已生成 {OUT}（章 {len(chapters)}，引用句 {sum(len(v) for v in QUOTES.values())}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
