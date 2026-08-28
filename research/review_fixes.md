# 第二轮审查 · 修复状态附录

> 本文件为 review_adversarial.md 的修复闭环记录（按发现顺序）。

| # | 发现 | 严重度 | 状态 | 修复/回归 |
|---|---|---|---|---|
| 1 | 梅花时支数公式错误（hour//2+1，奇数小时取错地支、23点误判亥） | 严重 | ✅ 已修 | `meihua.py` `nh=((hour+1)//2)%12+1`；回归 `test_meihua_hour_zhi_exhaustive`（24 小时穷举 + 23/0 点同卦断言） |
| 2 | 体用生克「体克用/用克体」判读反转（26/64 组颠倒） | 严重 | ✅ 已修 | `meihua.py` `_interact` 末两分支对调；回归 `test_meihua_tiyong_exhaustive`（8×8=64 组穷举对照独立生克表） |
| 3 | 6 个配置项静默失效（longitude/timezone/is_dst/canggan_sect/show_sources/ziwei_age_type） | 一般 | ✅ 已修 | 删去无法生效的 longitude/timezone/is_dst/canggan_sect/ziwei_age_type（经度等属出生信息，归 BirthInfo）；`show_sources` 已接入报告生成 |
| 4 | 子卯刑漏检 | 一般 | ✅ 已修（审查期间并发修复） | `relation.py` 两两扫描；回归 `test_zi_mao_xing_detected` |
| 5 | DST 边界按整日粒度（未建模 02:00 拨钟） | 一般 | ✅ 已修 | `is_china_dst` 改为时刻级 [开始日 02:00, 结束日 02:00)；回归 `test_china_dst` 边界断言 |
| 6 | 裸 assert 无消息 / 非法公历日期 ValueError | 一般 | ✅ 已修 | `BirthInfo.validate` 全部带消息 + 公历日期真实性校验；农历非法日期包成带提示的 ValueError |
| 7 | 农历非法闰月报错含糊 | 一般 | ✅ 已修 | `calendar.py` 捕获并转为带说明的 ValueError |
| 8 | 文档问题（meihua docstring、ziwei_tables §6.1 旧公式残留、README 计数过时） | 轻微 | ✅ 已修 | 均已更正；另据 x_iztro 实测修正 ziwei_tables §5/§6.2 的紫微系/天府系偏移表（原表误读口诀）并新增 `test_ziwei_tianfu_star_offsets` 锚点 |
| 9 | 测试未覆盖 meihua 两处严重 bug（恰好用了不触发的输入） | 测试质量 | ✅ 已修 | 新增上述穷举回归；另补 64 卦 King Wen 全量核对、八宫卦序独立推导、神煞公式穷举（test_exhaustive.py） |

**审查确认无误的部分**（无需改动）：全部硬编码表（神煞/称骨/64 卦名/八宫卦序/纳甲/六神/旬空/天德月德/禄刃）经独立清单核对 0 偏差；八字黄金用例、紫微命身宫公式、紫微-天府寅申对称、庚年四化开关、EoT 符号、立春边界、day_change_hour 切换均正常。

最终状态：`tests/` 80 项 + `plugin/test/` 8 项全部通过（含 HKO 官方历法数据 4 个年份逐年逐日回归）。
