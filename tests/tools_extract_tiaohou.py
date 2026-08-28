#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""从维基文库《穷通宝鉴》全文提取十干逐月调候原文，
生成 fortune/bazi/tiaohou_text.py（程序化提取、繁转简，非手工转写）。

数据源：research/fetched/qiongbao.txt（zh.wikisource.org《窮通寶鑑》，
Public Domain，2026-08-29 抓取）。与抓取页的一致性由 tests/test_tiaohou.py 锁定。
用法：python tests/tools_extract_tiaohou.py
"""
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from opencc import OpenCC

SRC = pathlib.Path(__file__).resolve().parents[1] / "research" / "fetched" / "qiongbao.txt"
OUT = pathlib.Path(__file__).resolve().parents[1] / "fortune" / "bazi" / "tiaohou_text.py"

T2S = OpenCC("t2s")
STEM_ELEM = {"甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
             "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水"}
MONTH_NUM = {"正": 1, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6,
             "七": 7, "八": 8, "九": 9, "十": 10, "十一": 11, "十二": 12}
SEASON = {1: "三春", 2: "三春", 3: "三春", 4: "三夏", 5: "三夏", 6: "三夏",
          7: "三秋", 8: "三秋", 9: "三秋", 10: "三冬", 11: "三冬", 12: "三冬"}


def clean(s: str) -> str:
    s = re.sub(r"\{\{.*?\}\}", "", s)
    s = s.replace("-{", "").replace("}-", "")
    s = re.sub(r"<[^>]+>", "", s)
    s = s.replace("'''", "")
    s = re.sub(r"^[*#\s]+", "", s)
    s = re.sub(r"\s+", "", s)
    return s.strip("，。；、：！？")


def first_paragraph(text: str, start: int) -> str:
    """从 start 起取到空行（或下个 ''' / === 标题 / 维基表格）为止的第一段。"""
    end = len(text)
    for pat in ("\n\n", "'''", "\n===", "\n==", "\n{|", "{|"):
        j = text.find(pat, start)
        if j > start:
            end = min(end, j)
    return clean(text[start:end])


def parse_months(part: str) -> list[int]:
    """月数部分 → 月份列表（支持 正/一…九/十/十一/十二 及 五六 等合并写法）。"""
    s = part.replace("十一", "K").replace("十二", "L").replace("十", "J")
    nums = []
    for ch in s:
        if ch == "正":
            nums.append(1)
        elif ch in "一二三四五六七八九":
            nums.append("一二三四五六七八九".index(ch) + 1)
        elif ch == "J":
            nums.append(10)
        elif ch == "K":
            nums.append(11)
        elif ch == "L":
            nums.append(12)
    return nums


def extract() -> dict[str, dict[int, str]]:
    t = SRC.read_text(encoding="utf-8")
    out: dict[str, dict[int, str]] = {}
    month_pat = re.compile(r"'''((?:正|[一二三四五六七八九十]+)月[甲乙丙丁戊己庚辛壬癸][木火土金水])'''")
    season_pat = re.compile(r"^={2,5}\s*三[春夏秋冬][甲乙丙丁戊己庚辛壬癸][木火土金水]\s*={2,5}\s*$", re.M)

    for stem, elem in STEM_ELEM.items():
        # 收集该干的所有月标记位置（独立月优先保留，合并月只填空位）
        months: dict[int, str] = {}
        for m in month_pat.finditer(t):
            name = m.group(1)
            if not name.endswith(stem + elem):
                continue
            part = name[:name.index("月")]
            block = T2S.convert(first_paragraph(t, m.end()))
            for mo in parse_months(part):
                if mo not in months:
                    months[mo] = block
        # 季节段（回退用）
        season_starts = {}
        for sm in season_pat.finditer(t):
            head = sm.group(0).strip("= \t")
            if head.endswith(stem + elem):
                season_starts[head[:2]] = T2S.convert(first_paragraph(t, sm.end()))
        row: dict[int, str] = {}
        last_seen = ""
        for mo in range(1, 13):
            if mo in months:
                row[mo] = months[mo]
                last_seen = months[mo]
            else:
                season = SEASON[mo]
                s_txt = season_starts.get(season, "")
                if s_txt:
                    row[mo] = s_txt + f"（注：该月无独立论，取{season}段原文）"
                elif last_seen:
                    row[mo] = last_seen + "（注：该月原书无独立论，参考前月原文）"
                else:
                    row[mo] = "（注：该月原书无独立论，且本季无总述，见上下文）"
        out[stem] = row
    return out


def main() -> int:
    data = extract()
    missing = [k for k, v in data.items() if len(v) != 12 or any(not s for s in v.values())]
    if missing:
        print("提取不完整：", missing)
        return 1
    with OUT.open("w", encoding="utf-8") as f:
        f.write('"""《穷通宝鉴》（《栏江网》）十干逐月调候原文（简体）——逐字引文数据模块。\n\n')
        f.write("出处：维基文库《窮通寶鑑》全文（Public Domain，2026-08-29 抓取，\n")
        f.write("存档 research/fetched/qiongbao.txt），由 tests/tools_extract_tiaohou.py\n")
        f.write("程序化提取、OpenCC t2s 繁转简后生成，非手工转写；与抓取页的一致性由\n")
        f.write("tests/test_tiaohou.py 回归锁定。个别月份原书无独立论段时回退取该季节\n")
        f.write('段首段并注明。原文按底本保留异体字（如「溼」）。\n"""\n\n')
        f.write("TIAOHOU_TEXT: dict[str, dict[int, str]] = {\n")
        for stem in STEM_ELEM:
            f.write(f'    "{stem}": {{\n')
            for mo in range(1, 13):
                f.write(f"        {mo}: {json.dumps(data[stem][mo], ensure_ascii=False)},\n")
            f.write("    },\n")
        f.write("}\n")
    print(f"已生成 {OUT}（10 干 × 12 月）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
