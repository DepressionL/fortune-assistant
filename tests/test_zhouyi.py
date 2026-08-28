"""《周易》表完整性测试：64 卦、每卦 6 爻辞、卦名本体覆盖梅花/六爻全部复合名。"""
from fortune.misc import meihua
from fortune.misc import zhouyi


def test_64_gua_complete():
    assert len(zhouyi.ZHOUYI) == 64
    for body_name, (gua_ci, yaos, mean) in zhouyi.ZHOUYI.items():
        assert gua_ci and gua_ci.endswith("。"), f"{body_name} 卦辞为空"
        assert len(yaos) == 6, f"{body_name} 爻辞应为 6 条"
        assert all(y and y.endswith("。") for y in yaos), f"{body_name} 有空洞爻辞"
        assert mean, f"{body_name} 缺卦名释义"


def test_body_covers_meihua_names():
    bodies = {zhouyi.body(n) for n in meihua.GUA64}
    assert len(bodies) == 64, "64 复合卦名应映射到 64 个不同本体"
    assert bodies == set(zhouyi.ZHOUYI.keys())


def test_body_covers_liuyao_names():
    from fortune.liuyao import PALACE_GUA
    names = {n for guas in PALACE_GUA.values() for (n, *_rest) in guas}
    assert len(names) == 64
    for n in names:
        assert zhouyi.body(n) in zhouyi.ZHOUYI, f"六爻卦名 {n} 未覆盖"


def test_yong_yao():
    assert zhouyi.yong_yao("乾为天") == "见群龙无首，吉。"
    assert zhouyi.yong_yao("坤为地") == "利永贞。"
    assert zhouyi.yong_yao("火山旅") is None


def test_spot_checks():
    assert zhouyi.gua_ci("火山旅") == "旅，小亨。旅贞吉。"
    assert zhouyi.yao_ci("火山旅", 6) == "鸟焚其巢，旅人先笑后号咷。丧牛于易，凶。"
    assert zhouyi.gua_ci("天水讼") == "讼，有孚窒惕，中吉，终凶。利见大人，不利涉大川。"
    assert zhouyi.yao_ci("乾为天", 1) == "潜龙勿用。"
    assert zhouyi.yao_ci("坤为地", 6) == "龙战于野，其血玄黄。"
    assert zhouyi.yao_ci("火山旅", 0) is None
    assert zhouyi.yao_ci("火山旅", 7) is None
    assert zhouyi.gua_ci("不存在的卦") is None
