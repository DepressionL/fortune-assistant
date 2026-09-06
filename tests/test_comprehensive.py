"""综合分析：多术数合参（大六壬/奇门遁甲/七政四余）测试。"""
from fortune.comprehensive import run
from fortune.config import FortuneConfig
from fortune.core.model import BirthInfo


def _birth():
    return BirthInfo(calendar="solar", year=1990, month=6, day=15, hour=13,
                     minute=30, gender="男", longitude=120.0)


def test_hepai_default_all():
    r = run(_birth(), FortuneConfig(), anchor_year=2025)
    tools = [hp["tool"] for hp in r.hepai]
    assert tools == ["liuren", "qimen", "qizheng"]
    for hp in r.hepai:
        assert hp.get("ok", True), hp.get("note", "")
        assert hp["markers"], hp["tool"]
        assert hp["schools"], hp["tool"]


def test_hepai_include_filter():
    r = run(_birth(), FortuneConfig(), include=["qimen"])
    assert [hp["tool"] for hp in r.hepai] == ["qimen"]
    r2 = run(_birth(), FortuneConfig(), include=[])
    assert r2.hepai == []


def test_hepai_qimen_schools():
    r = run(_birth(), FortuneConfig(), include=["qimen"])
    qm = r.hepai[0]
    san_yuan = next(s for s in qm["schools"] if s["name"] == "三元定局")
    assert len(san_yuan["items"]) == 3          # 拆补/茅山/置闰
    zhi_shi = next(s for s in qm["schools"] if s["name"] == "值使起法")
    assert len(zhi_shi["items"]) == 2


def test_hepai_qizheng_schools():
    r = run(_birth(), FortuneConfig(), include=["qizheng"])
    qz = r.hepai[0]
    names = [s["name"] for s in qz["schools"]]
    assert "黄道基准" in names and "紫气口径" in names
    assert qz["markers"][0]["key"] == "命宫命度"


def test_hepai_liuren_markers():
    r = run(_birth(), FortuneConfig(), include=["liuren"])
    lr = r.hepai[0]
    keys = [m["key"] for m in lr["markers"]]
    assert "课体" in keys and "三传" in keys


def test_hepai_markdown_section():
    r = run(_birth(), FortuneConfig(), include=["liuren"])
    md = r.markdown()
    assert "多术数合参" in md and "大六壬" in md
