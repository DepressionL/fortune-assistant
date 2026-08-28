"""fortune-assistant —— 可靠的 Python 算命辅助工具。

设计原则：
1. 历法/干支换算一律依赖经第三方验证的库（lunar_python 为主，sxtwl 交叉验证），不自造天文轮子；
2. 必须硬编码的表（神煞、纳音、安星诀、称骨歌等）逐项标注古籍/文献出处；
3. 所有流派分歧集中在 fortune.config.FortuneConfig 做成可配置项；
4. 解读类输出（用神等）明确标注为「经验规则，仅供参考」。

模块：
- fortune.config        流派配置（争议开关）
- fortune.core          历法输入封装 / 真太阳时
- fortune.bazi          八字排盘、神煞、旺衰、用神
- fortune.ziwei         紫微斗数排盘
- fortune.liuyao        六爻起卦装卦
- fortune.misc          梅花易数 / 小六壬 / 称骨
- fortune.report        Markdown 报告与 SVG 盘面
- fortune.cli           命令行入口
"""
__version__ = "0.1.0"
