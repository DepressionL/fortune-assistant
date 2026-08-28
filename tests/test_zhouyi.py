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


def test_against_independent_recitation_only_known_variants():
    """与独立默写结果逐字比对：只允许 4 处已知经典异文（咷/啕×2、己/巳×2），
    其余必须字符级全同——锁定本表已核验状态，防未来改动悄悄引入偏差。"""
    import json
    import pathlib

    fixture = pathlib.Path(__file__).parent / "fixtures" / "zhouyi_subagent_recitation.json"
    ref = json.loads(fixture.read_text(encoding="utf-8"))
    PUNCT = "。，；、？！：（）()「」『』·—─…，?! "

    def strip(s):
        return "".join(c for c in s if c not in PUNCT)

    def no_yaoti(s):
        return s.split("：", 1)[1] if "：" in s else s

    allowed = {
        ("同人", 4, "咷", "啕"),
        ("革", -1, "己", "巳"),   # -1 = 卦辞
        ("革", 1, "己", "巳"),
        ("旅", 5, "咷", "啕"),
    }
    found = set()
    for body_name, (my_gua, my_yaos, _mean) in zhouyi.ZHOUYI.items():
        lead = body_name + "，"
        m_gua0 = my_gua[len(lead):] if my_gua.startswith(lead) else my_gua
        r_gua = strip(ref[body_name]["卦辞"])
        m_gua = strip(m_gua0)
        if m_gua != r_gua:
            found.add((body_name, -1))
        for i in range(6):
            m_y = strip(my_yaos[i])
            r_y = strip(no_yaoti(ref[body_name]["爻辞"][i]))
            if m_y != r_y:
                found.add((body_name, i))
    # 只允许已知异文；其他一切差异必须为空
    keys = {(b, i) for b, i, *_ in allowed}
    assert found == keys, f"出现未记录的差异：{found ^ keys}"
