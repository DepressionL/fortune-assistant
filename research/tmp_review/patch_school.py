# -*- coding: utf-8 -*-
"""临时脚本：更新插件 index.js 的 school 枚举（一次性）。"""
import re

p = r"D:\ai工作区\fortune-assistant\plugin\lib\index.js"
t = open(p, encoding="utf-8").read()
t = t.replace(
    'wangshuai(旺衰,默认)|tiaohou(调候,《穷通宝鉴》逐月原文)|tongguan(通关)|geju(格局)',
    'wangshuai(旺衰,默认)|tiaohou(调候,《穷通宝鉴》逐月原文)|tongguan(通关)|geju(格局,《子平真诠》)|bingyao(病药,《神峰通考》)')
t = t.replace(
    '["wangshuai", "tiaohou", "tongguan", "geju"]',
    '["wangshuai", "tiaohou", "tongguan", "geju", "bingyao"]')
open(p, "w", encoding="utf-8").write(t)
print("已更新插件 school 枚举")
