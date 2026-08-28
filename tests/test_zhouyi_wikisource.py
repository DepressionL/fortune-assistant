"""《周易》表 × 维基文库权威数字版 比对回归测试。

数据源：research/fetched/zhouyi_pages/（zh.wikisource.org《周易》64 卦子页，
2026-08-29 抓取，Public Domain，Textquality 50%）。缺数据源或未装 opencc 时跳过。

断言：与维基文库本逐字比对（去句读/爻题/卦名引导，繁转简），差异必须恰好等于
已核实的经典异文集合——任何新差异都会失败，锁定本表与权威数字版的一致性。

已知异文（本表从阮刻《十三经注疏》本，文库本为现代排印本用字）：
- 中孚初九：它（注疏）/ 他（文库）
- 同人九五、旅上九：咷 / 啕
- 大有上六：祐 / 佑
- 革卦辞、六二：己 / 巳
- 困九二：享祀 / 亨祀；姤初六：蹢躅 / 踟躅；复初九：祗 / 袛
  （三者已在比对脚本 VARIANT_MAP 归一，不进入差异列表）
- 复初九「不远复」：文库本误作「不复远」（诸本皆作不远复，文库转录疑误）
"""
import pathlib

import pytest

PAGES = pathlib.Path(__file__).resolve().parents[1] / "research" / "fetched" / "zhouyi_pages"

pytestmark = pytest.mark.skipif(
    not PAGES.is_dir() or len(list(PAGES.glob("*.txt"))) < 64,
    reason="维基文库比对数据源不存在（research/fetched/zhouyi_pages/），跳过")

try:
    from opencc import OpenCC  # noqa: F401
except ImportError:  # pragma: no cover
    pytestmark = pytest.mark.skip(reason="未安装 opencc-python-reimplemented，跳过")

import verify_zhouyi_wikisource as _vw  # noqa: E402  (tests/ 目录同名脚本)


# 允许的差异：(卦本体, 位置, 我方含字, 文库含字)；位置 -1=卦辞，0..5=爻1..6
ALLOWED = {
    ("中孚", 0): ("它", "他"),
    ("同人", 4): ("咷", "啕"),
    ("大有", 5): ("祐", "佑"),
    ("革", -1): ("己", "巳"),
    ("革", 1): ("己", "巳"),
    ("复", 0): ("不远复", "不复远"),   # 文库转录疑误（诸本皆作「不远复」）
}


def test_wikisource_diff_is_exactly_known_variants():
    diffs, extras = _vw.compare_all()
    assert extras == [], f"用九/用六差异：{extras}"
    norm_actual = {(b, -1 if w == "卦辞" else int(w[1]) - 1, m, ws)
                   for b, w, m, ws in diffs}
    actual_keys = {(b, i) for b, i, _m, _w in norm_actual}
    assert actual_keys == set(ALLOWED.keys()), (
        f"差异集合与已知异文不一致：多出 {actual_keys - set(ALLOWED)}，"
        f"缺失 {set(ALLOWED) - actual_keys}")
    for (b, i, m, ws) in norm_actual:
        m_char, ws_char = ALLOWED[(b, i)]
        assert m_char in m, f"[{b} {i}] 我方应含 {m_char}：{m}"
        assert ws_char in ws, f"[{b} {i}] 文库应含 {ws_char}：{ws}"
