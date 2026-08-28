# dsh-fortune-client —— fortune 工具的图形化 Web UI（DSH 客户端插件）

为 `dsh-fortune` 的 7 个工具注册 `tool.call.toolview` 行渲染，把排盘结果画成
直观的**可交互**图形化盘面，带入场/脉冲/描画/生长动效：

| 工具 | 图形化呈现 | 交互 |
|---|---|---|
| `fortune_bazi` | 四柱卡片（日主高亮）+ 五行旺衰动画条 + 大运/神煞/合冲刑害/用神徽章 | **页签切换**（四柱/五行/大运/神煞/关系/用神）；**点四柱卡**看藏干十神与十神释义详情 |
| `fortune_ziwei` | **紫微十二宫盘 SVG**：逐宫绽放、命宫呼吸脉冲、四化着色（禄绿/权蓝/科黄/忌红）、大限标注、格局徽章 | **点宫位**弹星曜详情（亮度庙旺释义/四化/大限/长生/辅星杂曜/对宫）；**悬停高亮对宫**（虚线框）；键盘 Enter/Space 可点 |
| `fortune_liuyao` | 六爻卦象：爻线逐爻描画、动爻 ○/× 脉冲、世应标记、六亲/六神/纳甲徽章 | **点爻**看六亲/六神释义面板与动变说明 |
| `fortune_meihua` | 本卦/互卦/变卦三卡（卦符 + 卦名）、动爻、体用五行徽章、吉凶着色断语 | **点卦卡**看上下卦爻位（自下而上）、先天数、五行、卦德 |
| `fortune_chenggu` | 年月日时骨重卡 + 总骨重弹入 + 判词引用块 | **点骨重卡**看单项；**「↻ 重播动效」**按钮重放总骨重弹入 |
| `fortune_xiaoliuren` | 月→日→时三步推演路径 + 结果宫大卡（五行/方位/神煞/主数）+ 断语 | **「▶ 逐步推演」**按钮按 450ms 节奏重放月→日→时落宫动画（reduced-motion 时直接全显） |
| `fortune_solar_info` | 公历/农历/年干支/四柱徽章 + 节气时间徽章 | — |

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
