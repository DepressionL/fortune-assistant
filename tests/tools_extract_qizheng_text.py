# -*- coding: utf-8 -*-
"""生成 fortune/qizheng/text.py（《张果星宗》《星学大成》歌诀逐字引文）。

数据源：
- research/fetched/张果星宗_clean.txt（图书集成文本版清洗，繁体/异体原字）；
- research/fetched/星学大成.txt（四库全书本 epub 抽取，简体）。
程序化校验引句逐字（去空白）存在于存档；一致性由 tests/test_qizheng.py 回归锁定。
"""
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

ROOT = pathlib.Path(__file__).resolve().parents[1]
S_ZG = ROOT / "research" / "fetched" / "张果星宗_clean.txt"
S_XD = ROOT / "research" / "fetched" / "星学大成.txt"
OUT = ROOT / "fortune" / "qizheng" / "text.py"

QUOTES = {
    "安命": (S_ZG, "以生時加太陽宮順數遇卯即是命宮也"),
    "安命例": (S_ZG, "如太陽在子宮酉時生人以酉時加在子宮順數到午遇卯即是命宮也"),
    "命度": (S_ZG, "以太陽之度對著命宮之度即是命度"),
    "化曜": (S_XD, "甲乙丙丁戊己庚辛壬癸专配火孛木金土月水气计罗"),
    "化曜歌": (S_XD, "甲火乙孛丙属木，丁是金星戊土求，己是太阴庚是水，辛气壬计癸罗是也"),
    "宫主": (S_ZG, "子丑宮土寅亥宮木卯戌宮火辰酉宮金巳申宮水午宮日未宮月"),
    "宫分": (S_ZG, "子土寶瓶齊青位丑土磨羯越揚州寅木人馬燕幽"),
    "罗计": (S_XD, "交初为罗，交中为计都"),
    "行度": (S_ZG, "紫氣二十九日行一度大約二十九月一宮二十九年一周天"),
    "行度2": (S_ZG, "月孛九日行一度九箇月一宮九年一周天"),
    "行度3": (S_ZG, "計都十八日行一度十八月一宮十八年一周天"),
    "太阳行度": (S_ZG, "冬至箕四逼小寒斗十連大寒牛二直"),
}

NOTES = {
    "宿度": "二十八宿度数用《张果星宗》通行度表（角十二亢九氐十六房五心六尾十八"
            "箕九半斗廿二七五牛七女十一虚九二五危十六室十八二五壁九二五奎十八娄十二"
            "胃十五昴十一毕十六半觜半参九半井三十二五鬼二半柳十三半星六七五张十七二五"
            "翼二十二五轸十八二五），以「立春太阳在虚一度」锚定（冬至箕四、大寒牛二"
            "等太阳行度歌为约数，与今测略差，属古法口径，如实标注）。",
    "罗计": "罗睺=交初（白道升交点）、计都=交中（降交点），《星学大成》「交初为罗，"
            "交中为计都」；本仓用瑞士星历真交点实测（古法平均行度十八日行一度为约数）。",
    "月孛": "月孛=太阴行至最疾（月球远地点），本仓用瑞士星历平远地点实测"
            "（古法九日行一度为约数）。",
    "紫气": "紫气为传统虚拟星（木之余），无天文实体；古籍仅记平均行度"
            "（《张果星宗》「二十九日行一度……二十九年一周天」、《星平会海》"
            "「二十八日行一度」、《星学大成》「一宫住二十八个月」）而无统一"
            "起算锚点。本仓按多套速率×起算点预设同时计算并列对照"
            "（默认「果老速率+1900白羊初度」为现代排盘软件最常用简化起算），"
            "各口径出处逐行标注；可在 config/CLI 自定义速率与起算点。",
    "岁差": "本仓用回归黄道（tropical）宫位与宿度（古法锚定立春=虚一度），"
            "恒星黄道/现代岁差修正口径未实现。",
}


def _norm(s: str) -> str:
    return re.sub(r"\s+", "", s)


def main() -> int:
    zg = _norm(S_ZG.read_text(encoding="utf-8"))
    xd = _norm(S_XD.read_text(encoding="utf-8"))
    for key, (src, q) in QUOTES.items():
        text = zg if src == S_ZG else xd
        if _norm(q) not in text:
            raise RuntimeError(f"引句不在存档中：{key} :: {q}")
    with OUT.open("w", encoding="utf-8") as f:
        f.write('"""《张果星宗》（图书集成文本版）与《星学大成》（四库全书本）\n')
        f.write("七政四余歌诀逐字引文（程序化提取，tests/test_qizheng.py 回归锁定）。\n")
        f.write('NOTES：古法口径与现代实测差异如实标注。\n"""\n\n')
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
