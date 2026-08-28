# -*- coding: utf-8 -*-
"""临时核验脚本：穷举六十甲子验证「十恶大败=禄入空亡」集合（不入库）。"""
GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"
LU = {"甲": "寅", "乙": "卯", "丙": "巳", "丁": "午", "戊": "巳",
      "己": "午", "庚": "申", "辛": "酉", "壬": "亥", "癸": "子"}
XUN_KONG = {"甲子": ("戌", "亥"), "甲戌": ("申", "酉"), "甲申": ("午", "未"),
            "甲午": ("辰", "巳"), "甲辰": ("寅", "卯"), "甲寅": ("子", "丑")}

found = []
for gi in range(10):
    for zi in range(12):
        if gi % 2 != zi % 2:
            continue
        gz = GAN[gi] + ZHI[zi]
        # 该干支所在旬首
        offset = (zi - gi) % 12
        xun_shou = "甲" + ZHI[offset]
        kong = XUN_KONG[xun_shou]
        if LU[gz[0]] in kong:
            found.append(gz)
print("禄入空亡之日：", "、".join(found))
print("共", len(found), "个")
