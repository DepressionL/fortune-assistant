# dsh-fortune —— fortune-assistant 的 DSH 原生插件

把 [fortune-assistant](../README.md)（八字/紫微/六爻/梅花/小六壬/称骨/历法）注册为
DSH 原生工具集。薄工具层：每个工具调用 `python -m fortune.cli <子命令>`，
**计算与校验的单一事实源在 Python 侧**（lunar-python / x-iztro 引擎 + 文献核验表
+ 71 项 pytest）。本插件零 npm 依赖，结构照搬本机已验证的
`dsh-stable-asr` / `dsh-subtrans` 模板。

## 工具清单

| 工具 | 说明 | 超时 |
|---|---|---|
| `fortune_bazi` | 八字排盘：四柱/藏干/十神/大运/神煞/旺衰/用神（流派可配） | 60s |
| `fortune_ziwei` | 紫微斗数：十二宫/主星辅星/四化/大限（x-iztro 引擎，庚年四化与闰月口径可配） | 120s |
| `fortune_liuyao` | 六爻起卦装卦：世应/纳甲/六亲/六神/旬空/动变 | 30s |
| `fortune_meihua` | 梅花易数：数字/时间起卦，本卦互卦变卦体用 | 30s |
| `fortune_xiaoliuren` | 小六壬：农历月日时落宫 + 断辞 | 30s |
| `fortune_chenggu` | 袁天罡称骨（通行男命版） | 30s |
| `fortune_solar_info` | 历法速查：公历/农历/干支/四柱/节气精确时刻 | 30s |

## 安装

```powershell
# 1. 先确保 Python 依赖已装（清华镜像）：
cd path-to-fortune-assistant
.venv\Scripts\python -m pip install -e . -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn

# 2. 装入目标 profile（web 为例）：
dsh plugin --profile web add link:D:/ai工作区/fortune-assistant/plugin

# 3. 在该 profile 的 cordis.patch.yml 追加配置（路径按实际修改）：
#    - id: dsh-fortune
#      config:
#        projectDir: 'D:\ai工作区\fortune-assistant'
#        pythonBin: 'D:\ai工作区\fortune-assistant\.venv\Scripts\python.exe'
```

`dsh plugin add` 会把本目录 link 进 profile 的依赖并因 `dsh.bundle` 声明自动加入
bundles 列表（与 dsh-stable-asr 同一机制）。重启 DSH 后即可在会话中调用上述工具。

## 配置

| 键 | 默认 | 说明 |
|---|---|---|
| `projectDir` | 进程 cwd | fortune 项目根（`python -m fortune.cli` 的 cwd，需含 fortune 包） |
| `pythonBin` | `python` | 解释器路径（建议 venv 内 Python） |

## 测试

```powershell
cd path-to-fortune-assistant\plugin
node --test --experimental-test-isolation=none test\tools.test.mjs
# 8 项：注册完整性、schema 根 object、各工具 argv 构造、spawn 失败/非零退出码路径
# （用假 spawn 断言协议，不依赖 Python 环境；沙箱内无法跑真 spawn 时同样适用）
```

## 注意事项

- 工具输出为 Markdown 文本（与 stable-asr 相同风格），模型直接可读；
- 每个 spawn 都注入 `PYTHONIOENCODING=utf-8`，避免 Windows 控制台 GBK 乱码；
- 争议口径（夜子时换日、庚年四化、闰月等）由 Python 侧 config 承载，
  插件只透传参数，不在 JS 侧重复实现规则；
- `fortune_liuyao` 的铜钱「背为阳/阴」、`fortune_bazi` 的用神流派等均可通过参数切换。
