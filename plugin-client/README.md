# dsh-fortune-client —— fortune 工具的图形化 Web UI（DSH 客户端插件）

为 `dsh-fortune` 的 7 个工具注册 `tool.call.toolview` 行渲染，把排盘结果画成
直观的**可交互**图形化盘面，带入场/脉冲/描画/生长动效：

| 工具 | 图形化呈现 | 交互 |
|---|---|---|
| `fortune_bazi` | 四柱卡片（日主高亮）+ 五行旺衰动画条 + 大运/神煞/合冲刑害徽章 + **用神多流派子页签**（旺衰/调候/通关/格局/病药）+ **何知章 4 维成对条** + **大运流年时间轴**（冲突年描边、点年看事实）+ **口径分段器**（真太阳时/钟表时，后端预计算切换） | **页签切换**；点四柱卡看藏干十神；点流年年份看关系事实；切换时辰口径 |
| `fortune_ziwei` | **紫微十二宫盘 SVG**：逐宫绽放、命宫呼吸脉冲、四化着色、大限标注、格局徽章 + **格局复核**（星曜实际落宫/破格提示）+ **解读速览**（--interpret，检索式） | 点宫位弹星曜详情；悬停高亮对宫；键盘 Enter/Space |
| `fortune_liuyao` | 六爻卦象：爻线描画、动爻脉冲、世应标记、纳甲徽章 + **占题用神聚焦卡**（topic/date 徽章） | 点爻看六亲/六神释义 |
| `fortune_meihua` | 本卦/互卦/变卦三卡 + 体用五行徽章 + 吉凶着色断语 + 口径徽章 | 点卦卡看爻位/先天数/五行 |
| `fortune_chenggu` | 年月日时骨重卡 + 总骨重弹入 + 判词 + 口径徽章 | 点骨重卡；↻ 重播动效 |
| `fortune_xiaoliuren` | 月→日→时三步推演路径 + 结果宫大卡 + 断语 + 口径徽章 | ▶ 逐步推演重放 |
| `fortune_solar_info` | 公历/农历/年干支/四柱徽章 + 节气时间徽章 | — |
| `fortune_context` | BirthContext：四柱徽章 + 钟表/校正时支双口径 + 归一化步骤 | — |
| `fortune_comprehensive` | **用神共识热力矩阵**（流派×五行投票）+ **分维度结论卡**（共识度分档徽章）+ **证据链折叠**（工具→字段→事实→出处）+ **冲突清单** | 证据链展开/收起按钮 |

## 数据链路

```
dsh-fortune（宿主）--execute--> python -m fortune.cli ... --meta-json <tmp>
        │（同步 spawn）
        └--presentationMeta--> 读取 <tmp> JSON → 持久化 block.meta
dsh-fortune-client（浏览器）--tool.call.toolview 槽位--> 读 block.meta 渲染
```

- 结构化数据的单一事实源仍是 Python 侧（fortune.cli `--meta-json`）；
- canonical 文本输出照常供模型阅读，UI 只消费 meta 投影；
- meta 缺失（旧日志重放）时优雅回退纯文本。

## 设计约束

- 零颜色字面量：全部 `--dsw-alias-*` 语义 token，暗色主题自动适配；
- `prefers-reduced-motion` 时全量关闭动效（推演按钮直接全显）；
- 键盘可达：页签/宫位/爻/卦卡均可用 Tab 聚焦、Enter/Space 激活，
  `aria-pressed`/`aria-selected`/`role=tablist|button|img` 标注；
- 交互状态（选中宫/爻/页签）为纯前端 React state，不改动会话数据。

## 测试

```powershell
node test\smoke.mjs   # 渲染冒烟：注入假 react/window，7 视图渲染 + 交互回调
                      # + 12 宫盘结构 + meta 缺失回退
```

## 安装

```powershell
dsh plugin --profile web add link:path-to-fortune-assistant/plugin-client
# 无需 cordis.patch.yml 配置（无 config 项）；重启 DSH + 刷新页面生效
```

`dsh.client.immediately=true`：客户端模块随页面启动即加载（toolview 槽位注册不依赖
惰性触发）；宿主侧 bundle 有 watcher 时改动会自动重建（rev 变化），刷新页面即可。
