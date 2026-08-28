"""彖传/大象传引文模块 × 维基文库抓取页 回归测试。

- 结构：64 卦各有一条彖传与大象传；
- 一致性：用同一提取器重新解析 research/fetched/zhouyi_pages 并与模块逐条相等
  （锁定「程序化提取、非手工转写」），数据源缺省时跳过；
- 抽查名句防整体错位。
"""
import pathlib

import pytest

from fortune.misc import zhouyi_zhuan as zz

PAGES = pathlib.Path(__file__).resolve().parents[1] / "research" / "fetched" / "zhouyi_pages"

skip_missing = pytest.mark.skipif(
    not PAGES.is_dir() or len(list(PAGES.glob("*.txt"))) < 64,
    reason="维基文库数据源不存在，跳过与抓取页的一致性比对")


def test_structure():
    assert len(zz.TUAN) == 64 and len(zz.XIANG) == 64
    assert set(zz.TUAN) == set(zz.XIANG)
    for k in zz.TUAN:
        assert zz.TUAN[k], f"{k} 彖传为空"
        assert zz.XIANG[k], f"{k} 大象传为空"


def test_spot_checks():
    assert zz.XIANG["乾"] == "天行健，君子以自强不息。"
    assert zz.XIANG["坤"] == "地势坤，君子以厚德载物。"
    assert zz.TUAN["乾"].startswith("大哉乾元，万物资始，乃统天。")
    assert zz.TUAN["坤"].startswith("至哉坤元，万物资生，乃顺承天。")
    assert zz.TUAN["蛊"].endswith("终则有始，天行也。")


@skip_missing
def test_matches_fetched_pages():
    """模块内容必须与抓取页的提取结果逐字相等（防生成后人工改动引入偏差）。"""
    from opencc import OpenCC
    import tools_extract_zhuan as ext

    T2S = OpenCC("t2s")
    from tests.verify_zhouyi_wikisource import NAME_MAP, norm

    for f in sorted(PAGES.glob("*.txt")):
        body = NAME_MAP.get(T2S.convert(f.stem), T2S.convert(f.stem))
        tuan, xiang = ext.extract(f.read_text(encoding="utf-8"))
        assert zz.TUAN[body] == norm(tuan), f"{body} 彖传与抓取页不一致"
        assert zz.XIANG[body] == norm(xiang), f"{body} 大象传与抓取页不一致"
