# -*- coding: utf-8 -*-
"""Probe 3 (fixed): meihua tiyong shengke labels via trigrams."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from fortune.misc import meihua

W = {t: meihua.GUA_WUXING[t] for t in meihua.XIAN_TIAN}
# correct 生克 over trigram五行的直接 push
WU = meihua.GUA_WUXING
SHENG = {"木":"火","火":"土","土":"金","金":"水","水":"木"}
KE = {"木":"土","土":"水","水":"火","火":"金","金":"木"}

def truth_name(ti, yong):
    u, t = WU[yong], WU[ti]
    if u == t: return "比和"
    if SHENG[u] == t: return "用生体"
    if SHENG[t] == u: return "体生用"
    if KE[u] == t: return "用克体"
    return "体克用"

GUAS = ["乾","兑","离","震","巽","坎","艮","坤"]
bad = 0
for yong in GUAS:
    for ti in GUAS:
        rel, verdict = meihua._interact(yong, ti)
        correct = truth_name(ti, yong)
        if rel != correct:
            bad += 1
            print(f"  yong={yong} ti={ti}: code='{rel}'  correct='{correct}'  verdict='{verdict}'")
print(f"  mismatches: {bad} / 64")

print()
print("=== concrete case: 用=震(木), 体=艮(土) -> 用克体(凶) ===")
r = meihua._make("test", lower_idx=6, upper_idx=3, moving=5)  # 下艮(土) 上震(木), 动爻5(上)
print(f"  ti={r.ti_gua}({WU[r.ti_gua]}) yong={r.yong_gua}({WU[r.yong_gua]}) "
      f"relation='{r.relation}' verdict='{r.verdict}'")
print("  -> correct = 用克体 (凶): 木用 克 土体")
