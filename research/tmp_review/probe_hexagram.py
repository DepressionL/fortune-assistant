# -*- coding: utf-8 -*-
"""Independent verification of 64 hexagram names (King Wen) + eight-palace derivation."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import fortune.liuyao as ly
import fortune.misc.meihua as mh

# Trigram indices in the code's XIAN_TIAN order (先天八卦数: 乾1兑2离3震4巽5坎6艮7坤8)
XIAN = ("乾","兑","离","震","巽","坎","艮","坤")
IDX = {t:i for i,t in enumerate(XIAN)}

# --- King Wen order: (upper_trigram, lower_trigram) -> full name ---
# Hand-derived from the canonical 64 hexagram sequence.
KW = [
("乾","乾","乾为天"),("坤","坤","坤为地"),("坎","震","水雷屯"),("艮","坎","山水蒙"),
("坎","乾","水天需"),("乾","坎","天水讼"),("坤","坎","地水师"),("坎","坤","水地比"),
("巽","乾","风天小畜"),("乾","兑","天泽履"),("坤","乾","地天泰"),("乾","坤","天地否"),
("乾","离","天火同人"),("离","乾","火天大有"),("坤","艮","地山谦"),("震","坤","雷地豫"),
("兑","震","泽雷随"),("艮","巽","山风蛊"),("坤","兑","地泽临"),("巽","坤","风地观"),
("离","震","火雷噬嗑"),("艮","离","山火贲"),("艮","坤","山地剥"),("坤","震","地雷复"),
("乾","震","天雷无妄"),("艮","乾","山天大畜"),("艮","震","山雷颐"),("兑","巽","泽风大过"),
("坎","坎","坎为水"),("离","离","离为火"),("兑","艮","泽山咸"),("震","巽","雷风恒"),
("乾","艮","天山遁"),("震","乾","雷天大壮"),("离","坤","火地晋"),("坤","离","地火明夷"),
("巽","离","风火家人"),("离","兑","火泽睽"),("坎","艮","水山蹇"),("震","坎","雷水解"),
("艮","兑","山泽损"),("巽","震","风雷益"),("兑","乾","泽天夬"),("乾","巽","天风姤"),
("兑","坤","泽地萃"),("坤","巽","地风升"),("兑","坎","泽水困"),("坎","巽","水风井"),
("兑","离","泽火革"),("离","巽","火风鼎"),("震","震","震为雷"),("艮","艮","艮为山"),
("巽","艮","风山渐"),("震","兑","雷泽归妹"),("震","离","雷火丰"),("离","艮","火山旅"),
("巽","巽","巽为风"),("兑","兑","兑为泽"),("巽","坎","风水涣"),("坎","兑","水泽节"),
("巽","兑","风泽中孚"),("震","艮","雷山小过"),("坎","离","水火既济"),("离","坎","火水未济"),
]
assert len(KW) == 64, len(KW)

# Build name-by-(lower_idx, upper_idx)
name_by_pos = {}
for up, lo, name in KW:
    key = (IDX[lo], IDX[up])
    if key in name_by_pos:
        print("  !! duplicate", key, name, name_by_pos[key])
    name_by_pos[key] = name

print("=== A. meihua.GUA64 vs King Wen reference ===")
bad = 0
for (lo, up), expected_name in sorted(name_by_pos.items()):
    got = mh.GUA64[lo*8 + up]
    if got != expected_name:
        print(f"  MISMATCH lower={XIAN[lo]} upper={XIAN[up]} (idx {lo*8+up}): code='{got}' kw='{expected_name}'")
        bad += 1
print(f"  total mismatches: {bad} / 64")

# Check the '上象+下象' rule reconstructs the name
IMAGE = {"乾":"天","兑":"泽","离":"火","震":"雷","巽":"风","坎":"水","艮":"山","坤":"地"}
print("\n=== B. reconstruct code names by 上象+下象 rule ===")
rulebad = 0
for (lo, up) in name_by_pos:
    got = mh.GUA64[lo*8 + up]
    if lo == up:
        rule = XIAN[lo] + "为" + IMAGE[XIAN[lo]]
    else:
        rule = IMAGE[XIAN[up]] + IMAGE[XIAN[lo]]
    if got != rule:
        print(f"  rule-mismatch lower={XIAN[lo]} upper={XIAN[up]}: code='{got}' rule='{rule}'")
        rulebad += 1
print(f"  rule mismatches: {rulebad} / 64")

print("\n=== C. eight-palace derivation (本宫逐爻变) ===")
# PALACE_GUA entries: (name, upper, lower, shi, ying)
BITS = {  # bottom-up
 "乾":(1,1,1),"兑":(1,1,0),"离":(1,0,1),"震":(1,0,0),
 "巽":(0,1,1),"坎":(0,1,0),"艮":(0,0,1),"坤":(0,0,0),
}
BITS2GUA = {v:k for k,v in BITS.items()}
def pair_name(lo, up):
    if lo == up:
        return XIAN[IDX[lo]] + "为" + IMAGE[lo]
    return IMAGE[up] + IMAGE[lo]

EXPECT = {  # stage -> (lines toggled from 本宫, shi, ying)
 0: ((), 6, 3),   # 本宫
 1: ((0,), 1, 4),
 2: ((0,1), 2, 5),
 3: ((0,1,2), 3, 6),
 4: ((0,1,2,3), 4, 1),
 5: ((0,1,2,3,4), 5, 2),
 6: ((0,1,2,4), 4, 1),   # 游魂: revert line3 (index 3), keep lines 0,1,2,4 toggled
 7: ((0,1,2,4,5,6), 3, 6), # 归魂: lower(0,1,2) revert to 本宫; upper=游魂(3,4,5)... handled below
}

def gen(palace):
    base = BITS[palace]*2  # lower then upper, bottom-up, length 6
    out = []
    # 本宫
    out.append((base[:], 6, 3))
    # 1世..5世
    for k in range(1, 6):
        b = list(base)
        for i in range(k):
            b[i] = 1 - b[i]
        out.append((b[:], {1:1,2:2,3:3,4:4,5:5}[k], {1:4,2:5,3:6,4:1,5:2}[k]))
    # 游魂: 五世 lines then revert 4th (index3)
    b5 = list(base)
    for i in range(5):
        b5[i] = 1 - b5[i]
    you = list(b5); you[3] = 1 - you[3]   # revert 4th ya0
    out.append((you[:], 4, 1))
    # 归魂: lower revert to base, upper keep 游魂 upper
    gui = list(you)
    gui[0:3] = base[0:3]
    out.append((gui[:], 3, 6))
    return out

pal_bad = 0
for palace, guas in ly.PALACE_GUA.items():
    derived = gen(palace)
    # derived entries: [(bits, shi, ying)] in order; map bits -> (lower, upper)
    for i, (name, up, lo, shi, ying) in enumerate(guas):
        dbits, dshi, dying = derived[i]
        dlo = BITS2GUA[tuple(dbits[0:3])]
        dup = BITS2GUA[tuple(dbits[3:6])]
        dname = pair_name(dlo, dup)
        okname = (dname == name)
        okpos = (dshi == shi and dying == ying)
        if not (okname and okpos):
            pal_bad += 1
            print(f"  {palace}宫 stage{i}: code=({name},{up},{lo},shi{shi},ying{ying}) "
                  f"derived=({dname},{dup},{dlo},shi{dshi},ying{dying}) "
                  f"nameOK={okname} posOK={okpos}")
print(f"  palace mismatches: {pal_bad}")

print("\n=== D. PALACE_GUA all 64 names are valid King Wen names ===")
kw_names = set(n for _,_,n in KW)
all_names = set()
for p, gas in ly.PALACE_GUA.items():
    for g in gas: all_names.add(g[0])
print(f"  64 names unique? {len(all_names)==64}")
print(f"  every palace name in King Wen set? {all_names <= kw_names}")
print(f"  names not in King Wen: {all_names - kw_names}")

print("\n=== E. meihua GUA64 == meihua names distinct, all valid KW? ===")
print(f"  meihua GUA64 set == King Wen set? {set(mh.GUA64)==kw_names}")
