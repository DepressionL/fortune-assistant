"""全局流派配置 —— 所有「争议/分歧」都集中在这里做成可配置项。

每个字段的 docstring 都注明：争议内容、主流做法、本项目默认值、文献出处。
对应 research/*.md 的核验结论（出处详见 README.md 与 research 目录）。

注意：出生地经度/时区/夏令时是「出生信息」而非流派口径，统一放在
core.model.BirthInfo；本类只保留流派层面的开关（第二轮审查后清理，
删除过原本无法生效的 longitude/timezone/is_dst/canggan_sect/ziwei_age_type）。
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FortuneConfig:
    """算命引擎全局配置。

    用法::

        cfg = FortuneConfig()                 # 全部取主流默认
        cfg = FortuneConfig(use_true_solar_time=False, ...)  # 自定义流派
    """

    # ---------- 时间与历法 ----------
    #: 是否使用真太阳时校正（按出生地经度 + 均时差）。
    #: 争议：一派坚持真太阳时（主流排盘软件默认），一派坚持用钟表时间（地方习惯）。
    #: 默认 True。出处：research/solar_time.md。
    use_true_solar_time: bool = True

    # ---------- 八字流派分歧 ----------
    #: 换日时刻（子时归属）：23 = 23:00 后算次日（夜子时换日，传统子平主流，
    #: 如邵伟华《四柱预测学》；对应 lunar_python sect=1）；
    #: 0 = 0:00 换日（夜子时算当天；对应 lunar_python sect=2，lunar_python/sxtwl
    #: 的库默认值，部分现代软件采用）。两派对夜子时(23:00-23:59)出生者的日柱不同，
    #: 分歧依据见 research/bazi_golden_cases.md 案例 9。
    day_change_hour: int = 23

    #: 换年规则："lichun"（立春换年，术数界主流，八字引擎固定此口径）
    #: | "lunar_new_year"（正月初一；生肖/称骨等口径固定按此，八字不支持切换，
    #: 传入会得到明确报错）。
    year_change: str = "lichun"

    #: 起大运折算法：出生到上/下一节气的天数 ÷ N = 起运岁数。
    #: 3（主流「三天折一年」）| 2 | 5。lunar_python 仅内置 3 天折 1 年，
    #: 其余取值会得到明确报错（见 research/bazi_golden_cases.md）。
    yun_days_per_year: int = 3

    #: 神煞索引基准："day"（以日干/日支查，子平法主流）| "year"（以年干/年支查，
    #: 古法禄命习惯）。神煞模块据此选择索引。
    shensha_base: str = "day"

    #: 用神流派："wangshuai"（旺衰平衡，默认）| "tiaohou"（调候，《穷通宝鉴》）
    #: | "tongguan"（通关）| "geju"（格局，《子平真诠》）| "bingyao"（病药，《神峰通考》）。
    #: 注意：用神推断本质是经验规则而非确定性算法，本工具只做「透明的打分+规则」，
    #: 结果标注为参考。分歧详见 README。
    yongshen_school: str = "wangshuai"

    # ---------- 紫微斗数流派分歧 ----------
    #: 闰月生人安盘："as_month"（按当月，主流）| "as_next"（按下月，引擎不支持，
    #: 会明确报错）| "mid_split"（十五分界，iztro 默认）。
    ziwei_leap_month: str = "as_month"

    #: 庚年四化忌星："tiantong"（天同化忌，主流/iztro 默认）| "tianxiang"（天相化忌，
    #: 《紫微斗数全书》古法）。出处：research/ziwei_tables.md §9。
    ziwei_geng_sihua: str = "tiantong"

    # ---------- 六爻分歧 ----------
    #: 铜钱「背」的阴阳约定："yang"（背=3=老阳，多数教材）| "yin"（背=2=老阴）。
    #: 两派对老阴老阳恰好互换，务必在报告中注明所用约定。
    liuyao_coin_back: str = "yang"

    # ---------- 七政四余·紫气（多口径） ----------
    #: 紫气预设（虚拟星，多套速率×起算点同时计算，报告附对照表）：
    #: "guolao1900"（默认，果老星宗 29 日行一度 + 1900-01-01 白羊初度，
    #: 现代排盘软件最常用简化起算）| "guolao1984"（果老速率 + 甲子年立春）
    #: | "guolao1910"（果老速率 + 1910-01-05 辰宫二十二度，早期星历立成表锚点）
    #: | "xingping1900"（《星平会海》28 日行一度 + 1900 白羊初度）
    #: | "xingxue1900"（《星学大成》二十八个月一宫换算 + 1900 白羊初度）
    #: | "minguo1910"（民国星历比对口径：1910 锚 + 日行六分四十秒，疑月孛速率，
    #: 如实标注）。详见 fortune/qizheng/__init__.py 与 research/qizheng_tables.md。
    ziqi_preset: str = "guolao1900"

    #: 紫气自定义起法：速率（度/日）、起算点（ISO 日期）、起算点黄经（度）。
    #: 三者同时给定时在对照表中追加「自定义」行（不改默认行）。
    ziqi_rate: float | None = None
    ziqi_epoch: str | None = None
    ziqi_epoch_lon: float | None = None

    # ---------- 何知章（《滴天髓》规则映射） ----------
    #: 规则阈值覆盖（键见 bazi/ditiansui.HEZHI_DEFAULTS；推导与样本统计见
    #: research/hezhi_rules.md。默认值已收紧，避免多数盘全命中）。
    hezhi_thresholds: dict = field(default_factory=dict)

    #: 是否输出旧版「逐句列表 + 全量岁运表」格式（默认 False=成对呈现 + 只报变化）。
    hezhi_legacy: bool = False

    # ---------- 输出细节 ----------
    #: 报告中是否附旺衰计分明细（逐柱逐藏干得分，供人工复核；默认开）。
    show_strength_detail: bool = True

    #: 流年速览年数（自锚年起；0=关闭。该节随排盘时刻变化，
    #: 测试可用 liunian_anchor_year 固定锚年以保持确定性）。
    liunian_years: int = 10

    #: 流年速览锚年（None=排盘时刻当前年）。
    liunian_anchor_year: int | None = None

    #: 紫微检索式解读速览（默认关；开启后追加「参考条目（检索式，非推断）」节）。
    ziwei_interpret: bool = False

    #: 称骨性别（女命判词未完成多源核验前仅支持 男，见 docs/修复与改进计划.md I4-e）。
    chenggu_gender: str = "男"

    #: 综合工具（comprehensive）流派投票权重（流派名→权重；缺省等权）。
    comprehensive_weights: dict = field(default_factory=dict)

    # ---------- 输出 ----------
    #: 报告中是否附文献出处注记（默认开，便于核对硬编码表）。
    show_sources: bool = True

    def validate(self) -> None:
        assert self.day_change_hour in (0, 23), "day_change_hour 只能为 0 或 23"
        assert self.year_change in ("lichun", "lunar_new_year"), \
            'year_change 只能为 "lichun" 或 "lunar_new_year"'
        assert self.yun_days_per_year in (2, 3, 5), "yun_days_per_year 只能为 2/3/5"
        assert self.shensha_base in ("day", "year"), 'shensha_base 只能为 "day" 或 "year"'
        assert self.yongshen_school in ("wangshuai", "tiaohou", "tongguan", "geju", "bingyao"), \
            "yongshen_school 取值非法"
        assert self.ziwei_leap_month in ("as_month", "as_next", "mid_split"), \
            "ziwei_leap_month 取值非法"
        assert self.ziwei_geng_sihua in ("tiantong", "tianxiang"), \
            "ziwei_geng_sihua 取值非法"
        assert self.liuyao_coin_back in ("yang", "yin"), 'liuyao_coin_back 只能为 "yang"/"yin"'
        assert self.ziqi_preset in ("guolao1900", "guolao1984", "guolao1910",
                                    "xingping1900", "xingxue1900", "minguo1910"), \
            "ziqi_preset 取值非法"
        assert isinstance(self.hezhi_thresholds, dict), "hezhi_thresholds 须为字典"
        assert isinstance(self.comprehensive_weights, dict), "comprehensive_weights 须为字典"
        assert self.liunian_years >= 0, "liunian_years 须 ≥0"
        assert self.liunian_anchor_year is None or 1600 <= self.liunian_anchor_year <= 2200, \
            "liunian_anchor_year 须在 1600-2200 或为 None"
        assert self.chenggu_gender == "男", \
            "称骨女命判词尚未完成多源核验（docs/修复与改进计划.md I4-e），暂仅支持 男"


DEFAULT_CONFIG = FortuneConfig()
