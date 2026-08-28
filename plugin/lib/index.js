// dsh-fortune：fortune-assistant 的 DSH 原生插件（八字/紫微/六爻/梅花/小六壬/称骨）。
//
// 薄工具层：每个工具内部调用 `python -m fortune.cli <子命令> <参数>`，
// 计算、排盘正确性与争议口径全部由 Python 侧（fortune 包 + 文献核验表 +
// 80 项测试）承载；本层只做参数转发、结构化输出与超时控制。
// 零依赖（不 import dsh 包，ToolDefinition 手工构造 + 本地 schema 转换），
// 可经 `dsh plugin --profile <name> add <本目录>` 装入任意 profile。
//
// 结构化数据（presentationMeta）：每个调用同时以 `--meta-json <tmp>` 让 CLI
// 落盘结构化 JSON，presentationMeta 同步读取并投影为持久化的展示元数据——
// dsh-fortune-client 客户端插件据此渲染图形化盘面（八字四柱卡/紫微十二宫盘/
// 六爻卦象等），canonical 文本输出仍供模型阅读。
//
// 模板：本机已验证的 dsh-stable-asr / dsh-subtrans 插件
//（$DSH_HOME\profiles\web 的 cordis.patch.yml 与 package.json 为注册范例）。
import { spawnSync } from "node:child_process";

export const name = "dsh-fortune";
export const inject = ["tools"];

const MAX_OUT = 20000;
const BAZI_TIMEOUT = 60000;   // 八字：lunar_python 冷导入
const ZIWEI_TIMEOUT = 120000; // 紫微：x_iztro 引擎冷加载
const SHORT_TIMEOUT = 30000;

function defaultSpawn(pythonBin, args, opts) {
  return spawnSync(pythonBin, args, opts);
}

// meta 随身通道：CLI 在文本输出末尾以标记行内嵌一层结构化 JSON，
// 插件在此拆出（模型面文本剔除标记），随规范值交给 presentationMeta。
// 不再依赖临时文件/参数哈希——单次 spawn、无时序问题、重放安全。
const META_MARKER = "===DSH_META_JSON===";

function splitMeta(output) {
  const idx = output.lastIndexOf(META_MARKER);
  if (idx < 0) return { text: output, meta: null };
  const jsonPart = output.slice(idx + META_MARKER.length).trim();
  let meta = null;
  try { meta = JSON.parse(jsonPart); } catch { meta = null; }
  return { text: output.slice(0, idx).trim(), meta };
}

function runCli(projectDir, pythonBin, args, timeoutMs, spawn = defaultSpawn) {
  const res = spawn(pythonBin, ["-m", "fortune.cli", ...args], {
    cwd: projectDir,
    encoding: "utf8",
    timeout: timeoutMs,
    maxBuffer: 16 * 1024 * 1024,
    windowsHide: true,
    // Python 管道输出强制 UTF-8，避免 Windows GBK 控制台编码导致乱码
    env: { ...process.env, PYTHONIOENCODING: "utf-8" },
  });
  const raw = ((res.stdout || "") + (res.stderr || "")).trim();
  const ok = !res.error && res.status === 0;
  const { text, meta } = splitMeta(raw);
  // CLI 失败时把失败标记与 stderr 正文前置，保证真实报错对用户/模型可见
  // （不再被 output schema 的 meta 类型校验吞掉——meta 为 null 时省略该键）。
  let output = text.slice(0, MAX_OUT);
  if (!ok && text) {
    output = `[CLI 执行失败（exit=${res.status === null ? -1 : res.status}）]\n${output}`;
  }
  const value = {
    ok,
    exitCode: res.status === null ? -1 : res.status,
    output,
    error: res.error ? `spawn 失败: ${res.error.message}`
      : (!ok && !text ? `exit=${res.status}` : ""),
  };
  if (meta !== null) value.meta = meta;   // meta 缺失时省略键（null 会触发 schema 类型错误）
  return value;
}

function textRender(_args, value) {
  return [{ type: "text",
            text: [value.output, value.error].filter(Boolean).join("\n")
              || "(无输出)" }];
}

// 输出值 schema：object 根 + 对象级 required（DSH output schema 方言）
// meta 字段 = CLI 内嵌的结构化结果（客户端 UI 的图形化盘面数据源）。
const OUTPUT_TEXT = {
  schema: {
    type: "object",
    additionalProperties: false,
    required: ["ok", "exitCode", "output"],
    properties: {
      ok: { type: "boolean" },
      exitCode: { type: "number" },
      output: { type: "string" },
      error: { type: "string" },
      meta: { type: "object" },
    },
  },
  render: textRender,
};

const STRING = (d, required = false) =>
  ({ type: "string", description: d, ...(required ? { required: true } : {}) });
const BOOL = (d) => ({ type: "boolean", description: d });
const INT = (d, required = false) =>
  ({ type: "integer", description: d, ...(required ? { required: true } : {}) });
const ENUM = (d, values, required = false) =>
  ({ type: "string", description: d, enum: values, ...(required ? { required: true } : {}) });
const ARR_INT = (d, required = false) =>
  ({ type: "array", items: { type: "integer" }, description: d,
     ...(required ? { required: true } : {}) });

// 与 @deepseek-ai/dsh-tools 的 parameterSchemaSpecToJsonSchema 等价的最小转换：
// 扁平参数规格 → 带根 type:"object" 的 JSON Schema。DSH 工具注册要求该形状，
// 否则 wire 上的 function schema 缺根 type，服务端报 INVALID_REQUEST。
function toParametersSchema(spec) {
  const properties = {};
  const required = [];
  for (const [k, v] of Object.entries(spec)) {
    const prop = { type: v.type };
    if (v.description) prop.description = v.description;
    if (v.enum) prop.enum = v.enum;
    if (v.items) prop.items = v.items;
    properties[k] = prop;
    if (v.required) required.push(k);
  }
  const schema = { type: "object", properties };
  if (required.length > 0) schema.required = required;
  return schema;
}

// ---- 结构化元数据（presentationMeta）----
// meta 从规范值 value.meta 取（CLI 单次执行的产物），不依赖文件/参数哈希。
function makePresentationMeta(toolName) {
  return (args, value) => {
    const data = value && value.meta;
    if (data && typeof data === "object") {
      return { ok: true, tool: toolName, data };
    }
    return { ok: false, tool: toolName, data: null };
  };
}

// 出生参数（八字/紫微/称骨共用）
const BIRTH_SPEC = {
  year: INT("公历年（公历输入）", true),
  month: INT("公历月（1-12）", true),
  day: INT("公历日（1-31）", true),
  hour: INT("时（0-23，出生地钟表时间）", true),
  minute: INT("分（0-59，默认 0）"),
  gender: ENUM("性别", ["男", "女"]),
  lng: { type: "number", description: "出生地东经度数（东为正，默认 120=不校正经度）" },
  tzHours: { type: "number", description: "出生记录所用标准时区（小时，东为正；默认 8=北京时间 UTC+8。海外出生按当地标准时填，如纽约 -5、东京 9；1949 年前中国五时区记录按原时区填：昆仑 5.5/新藏 6/陇蜀 7/中原 8/长白 8.5）" },
  trueSolar: BOOL("是否真太阳时校正（默认 true）"),
  dayChange: ENUM("换日时刻：23（夜子时算次日，传统主流，默认）| 0（库默认）", [23, 0]),
  dst: BOOL("钟面时间是否为中国夏令时（1986-1991，默认 false）"),
};

function pushBirth(argv, a) {
  argv.push("-y", String(a.year), "-m", String(a.month), "-d", String(a.day),
            "-H", String(a.hour));
  if (a.minute !== undefined && a.minute !== null) argv.push("-M", String(a.minute));
  if (a.gender) argv.push("-g", a.gender);
  if (a.lng !== undefined && a.lng !== null) argv.push("--lng", String(a.lng));
  if (a.tzHours !== undefined && a.tzHours !== null) argv.push("--timezone", String(a.tzHours));
  if (a.trueSolar === false) argv.push("--no-true-solar");
  if (a.dayChange !== undefined && a.dayChange !== null) argv.push("--day-change", String(a.dayChange));
  if (a.dst) argv.push("--dst");
}

export function apply(ctx, config = {}) {
  const projectDir = config.projectDir || process.cwd();
  const pythonBin = config.pythonBin || "python";
  // 可注入 spawn（测试用假实现断言 argv 构造与 meta 拆解；生产走同步原语）
  const spawn = config.spawn || defaultSpawn;
  const call = (args, timeoutMs) => runCli(projectDir, pythonBin, args, timeoutMs, spawn);

  ctx.tools.register({
    name: "fortune_bazi",
    description:
      "八字排盘（子平法）：四柱/藏干/十神/纳音/地势/旬空/胎元命宫身宫/大运起运/"
      + "合冲刑害/18 项神煞/五行旺衰打分/用神（流派可选）。历法由 lunar-python 计算"
      + "（与 sxtwl 交叉验证），硬编码表经《三命通会》《渊海子平》核验；争议口径可配"
      + "（换日时刻/神煞基准/用神流派）。输出 Markdown 报告。",
    parameters: toParametersSchema({
      ...BIRTH_SPEC,
      school: ENUM("用神流派：wangshuai(旺衰,默认)|tiaohou(调候)|tongguan(通关)|geju(格局)",
                   ["wangshuai", "tiaohou", "tongguan", "geju"]),
      schools: STRING("逗号分隔的多流派一次对比（覆盖 school），如 \"wangshuai,tiaohou\""),
      shenshaBase: ENUM("神煞索引基准：day(日干/日支,子平主流,默认)|year(年干/年支,古法)",
                        ["day", "year"]),
    }),
    output: { ...OUTPUT_TEXT, presentationMeta: makePresentationMeta("fortune_bazi") },
    timeoutMs: BAZI_TIMEOUT,
    async execute(args) {
      const argv = ["bazi"];
      pushBirth(argv, args);
      if (args.school) argv.push("--school", args.school);
      if (args.schools) argv.push("--schools", args.schools);
      if (args.shenshaBase) argv.push("--shensha-base", args.shenshaBase);
      return call(argv, BAZI_TIMEOUT);
    },
  });

  ctx.tools.register({
    name: "fortune_ziwei",
    description:
      "紫微斗数排盘：十二宫/十四主星/辅星杂曜/生年四化（表头按实际生年显示，"
      + "如丁年太阴禄/天同权/天机科/巨门忌；庚年两派为配置口径，见表头「配置口径」行）/"
      + "大限/命身宫/命主身主/五行局/64 格局检测。引擎为 x-iztro（iztro v2.5.8 移植，"
      + "716,314 条黄金用例回归）；庚年四化（天同忌主流/天相忌古法）与闰月口径可配。"
      + "输出 Markdown 十二宫表。",
    parameters: toParametersSchema({
      ...BIRTH_SPEC,
      gengSihua: ENUM("庚年四化忌星：tiantong(天同,主流,默认)|tianxiang(天相,《全书》古法)",
                      ["tiantong", "tianxiang"]),
      leapMode: ENUM("闰月口径：as_month(按当月,默认)|mid_split(十五分界,iztro 默认)",
                     ["as_month", "mid_split"]),
    }),
    output: { ...OUTPUT_TEXT, presentationMeta: makePresentationMeta("fortune_ziwei") },
    timeoutMs: ZIWEI_TIMEOUT,
    async execute(args) {
      const argv = ["ziwei"];
      pushBirth(argv, args);
      if (args.gengSihua) argv.push("--geng-sihua", args.gengSihua);
      if (args.leapMode) argv.push("--leap-mode", args.leapMode);
      return call(argv, ZIWEI_TIMEOUT);
    },
  });

  ctx.tools.register({
    name: "fortune_chenggu",
    description:
      "袁天罡称骨（通行男命版）：年/月/日/时骨重相加与判词。托名袁天罡的民间歌诀，"
      + "仅作文化参考；表经多源交叉核验。按农历正月初一换年、时辰按校正后钟点。",
    parameters: toParametersSchema({
      year: INT("公历年", true),
      month: INT("公历月（1-12）", true),
      day: INT("公历日（1-31）", true),
      hour: INT("时（0-23）", true),
      minute: INT("分（0-59，默认 0）"),
      gender: ENUM("性别", ["男", "女"]),
      lng: { type: "number", description: "出生地东经度数（默认 120）" },
    }),
    output: { ...OUTPUT_TEXT, presentationMeta: makePresentationMeta("fortune_chenggu") },
    timeoutMs: SHORT_TIMEOUT,
    async execute(args) {
      const argv = ["chenggu"];
      pushBirth(argv, args);
      return call(argv, SHORT_TIMEOUT);
    },
  });

  ctx.tools.register({
    name: "fortune_xiaoliuren",
    description:
      "小六壬（诸葛马前课）：农历月日时三数落宫，六宫断辞。通行本规则，"
      + "从 1 起数（大安起正月）。时辰按钟表时支（不做真太阳时校正）。",
    parameters: toParametersSchema({
      month: INT("农历月（1-12；闰月按当月，流派分歧见 README）", true),
      day: INT("农历日（1-30）", true),
      hourZhi: ENUM("时支：子丑寅卯辰巳午未申酉戌亥",
                    "子丑寅卯辰巳午未申酉戌亥".split(""), true),
    }),
    output: { ...OUTPUT_TEXT, presentationMeta: makePresentationMeta("fortune_xiaoliuren") },
    timeoutMs: SHORT_TIMEOUT,
    async execute(args) {
      const argv = ["xiaoliuren", "--month", String(args.month),
                    "--day", String(args.day), "--hour-zhi", args.hourZhi];
      return call(argv, SHORT_TIMEOUT);
    },
  });

  ctx.tools.register({
    name: "fortune_meihua",
    description:
      "梅花易数起卦：数字起卦（2-3 个数）或农历时间起卦。给出本卦/互卦/变卦/"
      + "动爻/体用生克与通行断语，附卦辞爻辞（通行本《周易》，阮刻十三经注疏本文字）。"
      + "64 卦名依通行《周易》（上象+下象规则）；时间起卦时辰按钟表时支。",
    parameters: toParametersSchema({
      numbers: ARR_INT("数字起卦：2 或 3 个整数（如 [12,34]）"),
      lunarYear: INT("时间起卦：农历年（如 1990）"),
      lunarMonth: INT("时间起卦：农历月（1-12）"),
      lunarDay: INT("时间起卦：农历日（1-30）"),
      hour: INT("时间起卦：时（0-23，取时支）"),
    }),
    output: { ...OUTPUT_TEXT, presentationMeta: makePresentationMeta("fortune_meihua") },
    timeoutMs: SHORT_TIMEOUT,
    async execute(args) {
      const argv = ["meihua"];
      if (Array.isArray(args.numbers) && args.numbers.length > 0) {
        argv.push(...args.numbers.map(String));
      } else if (args.lunarYear) {
        argv.push("--lunar-year", String(args.lunarYear),
                  "--lunar-month", String(args.lunarMonth),
                  "--lunar-day", String(args.lunarDay),
                  "--hour", String(args.hour || 0));
      } else {
        return { ok: false, exitCode: -1, output: "",
                 error: "请提供 numbers（2-3 个整数）或农历时间起卦参数" };
      }
      return call(argv, SHORT_TIMEOUT);
    },
  });

  ctx.tools.register({
    name: "fortune_liuyao",
    description:
      "六爻起卦装卦：三枚铜钱六次投掷（自下而上），装世应/纳甲/六亲/六神/旬空/"
      + "动变。表依《增删卜易》《卜筮正宗》核验；铜钱「背为阳/阴」约定可配。",
    parameters: toParametersSchema({
      backs: ARR_INT("六次投掷中「背」的个数（0-3），自下而上，如 [2,3,1,0,3,2]；random=true 时可省略"),
      monthZhi: STRING("月建地支（子丑寅卯辰巳午未申酉戌亥）", true),
      dayGanzhi: STRING("日辰干支（如 甲子）", true),
      coinBack: ENUM("铜钱约定：yang(背=阳=3,主流,默认)|yin(背=阴)", ["yang", "yin"]),
      random: BOOL("不提供 backs 时随机模拟三枚铜钱掷六次（每枚独立 50% 出背）"),
    }),
    output: { ...OUTPUT_TEXT, presentationMeta: makePresentationMeta("fortune_liuyao") },
    timeoutMs: SHORT_TIMEOUT,
    async execute(args) {
      const argv = ["liuyao", "--month-zhi", args.monthZhi, "--day-ganzhi", args.dayGanzhi];
      if (Array.isArray(args.backs) && args.backs.length > 0) {
        argv.push("--backs", args.backs.join(","));
      } else if (args.random) {
        argv.push("--random");
      } else {
        return { ok: false, exitCode: -1, output: "",
                 error: "请提供 backs（六次背数）或设 random=true 随机起卦" };
      }
      if (args.coinBack) argv.push("--coin-back", args.coinBack);
      return call(argv, SHORT_TIMEOUT);
    },
  });

  ctx.tools.register({
    name: "fortune_solar_info",
    description:
      "历法速查：公历↔农历、年干支/生肖、四柱、当年节气精确时刻。"
      + "注意：四柱为钟表时辰口径（未做真太阳时校正），与 bazi/ziwei 传 lng 后的"
      + "校正盘可能时柱不同；用于排盘前核对输入与节气边界（如立春换年）。",
    parameters: toParametersSchema({
      year: INT("公历年", true),
      month: INT("公历月（1-12）", true),
      day: INT("公历日（1-31）", true),
      hour: INT("时（0-23，默认 12）"),
      minute: INT("分（默认 0）"),
    }),
    output: { ...OUTPUT_TEXT, presentationMeta: makePresentationMeta("fortune_solar_info") },
    timeoutMs: SHORT_TIMEOUT,
    async execute(args) {
      const argv = ["solar-info", "-y", String(args.year),
                    "-m", String(args.month), "-d", String(args.day)];
      if (args.hour !== undefined && args.hour !== null) argv.push("-H", String(args.hour));
      if (args.minute !== undefined && args.minute !== null) argv.push("-M", String(args.minute));
      return call(argv, SHORT_TIMEOUT);
    },
  });
}
