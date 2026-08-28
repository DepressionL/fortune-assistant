// dsh-fortune-client 渲染冒烟测试（node 直跑，无需浏览器）：
// 注入假 window/__ModuleLoader__ 与假 react，用真实形状的 meta 数据
// 渲染 7 个工具视图，验证：不抛错、结构完整、交互回调（onClick/onSelect）存在。
// 运行：node test/smoke.mjs
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

// ---- 假 react ----
const h = (type, props, ...children) => {
  const el = { type, props: props ?? {}, children: children.flat(Infinity) };
  return el;
};
const react = {
  createElement: h,
  useState: (init) => [init, () => {}],
  useEffect: () => {},
  useRef: (v) => ({ current: v }),
};

// ---- 捕获客户端模块 ----
let factory = null;
globalThis.window = {
  __ModuleLoader__: {
    load({ id, factory: f }) {
      if (id === "dsh-fortune-client") factory = f;
    },
  },
};
await import("../lib/client.js");
assert.ok(factory, "未捕获 dsh-fortune-client factory");
const clientExports = factory((name) =>
  (name === "react" ? react
    : (() => { throw new Error(`unknown require ${name}`); })()));

// ---- 假 slots ctx ----
const registrations = [];
const ctx = {
  slots: {
    inject(_slot, fn) { fn(); },
    register(def, comp) { registrations.push([def.key, comp]); },
  },
};
clientExports.apply(ctx);
assert.equal(registrations.length, 7, "应注册 7 个 toolview");
const viewOf = (name) => registrations.find(([k]) => k === name)[1];

// ---- 真实形状的 meta 数据 ----
const FIXTURES = {
  fortune_bazi: {
    tool: "bazi",
    chart: {
      solar_used: "1990-06-15 13:29:44", gender: "男", yun_forward: true,
      yun_start_solar: "1997-11-04", yun_start_age: 8,
      steps: ["输入：公历 1990-06-15 13:30:00", "真太阳时校正（东经120°）：偏移 -0.3 分钟"],
      pillars: [
        { name: "年柱", gan_zhi: "庚午", gan: "庚", zhi: "午", hide_gan: ["丁", "己"], shi_shen_gan: "劫财", shi_shen_zhi: ["七杀", "偏印"], na_yin: "路旁土", wu_xing: "金", di_shi: "病", xun: "甲子", xun_kong: "戌亥" },
        { name: "月柱", gan_zhi: "壬午", gan: "壬", zhi: "午", hide_gan: ["丁", "己"], shi_shen_gan: "伤官", shi_shen_zhi: ["七杀", "偏印"], na_yin: "杨柳木", wu_xing: "水", di_shi: "病", xun: "甲申", xun_kong: "申酉" },
        { name: "日柱", gan_zhi: "辛亥", gan: "辛", zhi: "亥", hide_gan: ["壬", "甲"], shi_shen_gan: "日主", shi_shen_zhi: ["伤官", "正财"], na_yin: "钗钏金", wu_xing: "金", di_shi: "沐浴", xun: "甲辰", xun_kong: "寅卯" },
        { name: "时柱", gan_zhi: "乙未", gan: "乙", zhi: "未", hide_gan: ["己", "丁", "乙"], shi_shen_gan: "偏财", shi_shen_zhi: ["偏印", "七杀", "偏财"], na_yin: "沙中金", wu_xing: "木", di_shi: "衰", xun: "甲午", xun_kong: "辰巳" },
      ],
      dayun: [
        { gan_zhi: "癸未", start_year: 1997, end_year: 2006, start_age: 8, end_age: 17 },
        { gan_zhi: "甲申", start_year: 2007, end_year: 2016, start_age: 18, end_age: 27 },
      ],
    },
    strength: { month_wx: "火", level: "身弱", day_wx: "金",
      scores: { 木: 0.8, 火: 2.4, 土: 1.44, 金: 0.2, 水: 0.6 },
      same_score: 1.64, diff_score: 3.8 },
    shensha: [
      { name: "天乙贵人", basis: "日干辛", positions: ["年柱", "月柱"], values: ["午", "午"], note: "" },
      { name: "羊刃", basis: "日干辛（阴干）", positions: [], values: [], note: "主流阴干无刃" },
    ],
    relations: [
      { name: "天干五合", positions: ["年柱", "时柱"], values: ["庚", "乙"], detail: "化金" },
      { name: "自刑", positions: ["年柱", "月柱"], values: ["午", "午"], detail: "" },
    ],
    yongshen: { school: "wangshuai（旺衰平衡）", conclusions: ["日主金偏弱"],
      yong_wuxing: ["土", "金"], ji_wuxing: ["火", "水", "木"], caveat: "" },
  },
  fortune_ziwei: {
    tool: "ziwei", solar_used: "1976-07-28 05:35:34", gender: "男",
    five_elements_class: "水二局", ming_zhu: "武曲", shen_zhu: "文昌",
    palaces: Array.from({ length: 12 }, (_, i) => ({
      name: ["命宫", "兄弟", "夫妻", "子女", "财帛", "疾厄", "迁移", "仆役", "官禄", "田宅", "福德", "父母"][i],
      gan_zhi: ["癸巳", "壬辰", "辛卯", "庚寅", "辛丑", "庚子", "己亥", "戊戌", "丁酉", "丙申", "乙未", "甲午"][i],
      major: i === 0 ? [["巨门", "旺", ""]] : i === 3 ? [["紫微", "旺", ""], ["天府", "庙", ""]]
        : i === 8 ? [["天同", "平", "禄"]] : i === 11 ? [["廉贞", "平", "忌"], ["天相", "庙", ""]] : [],
      minor: i === 0 ? ["禄存", "火星"] : [], adjective: i === 0 ? ["天喜"] : [],
      da_xian: `${2 + i * 10}-${11 + i * 10}`, da_xian_ganzhi: "癸巳",
      chang_sheng: "绝", is_ming: i === 0, is_shen: i === 6, is_laiyin: i === 9,
    })),
    patterns: ["羊陀夹命（命宫）：禄存、陀罗、擎羊"],
  },
  fortune_liuyao: {
    tool: "liuyao", ben_gua: "水风井", bian_gua: "雷山小过", palace: "震", palace_wuxing: "木",
    shi: 5, ying: 2, month_zhi: "午", day_ganzhi: "甲子", xun_kong: ["戌", "亥"], coin_back: "yang",
    lines: [
      { no: 1, value: 8, gan_zhi: "辛丑", liu_qin: "妻财", liu_shen: "青龙", is_moving: false },
      { no: 2, value: 9, gan_zhi: "辛亥", liu_qin: "父母", liu_shen: "朱雀", is_moving: true },
      { no: 3, value: 7, gan_zhi: "辛酉", liu_qin: "官鬼", liu_shen: "勾陈", is_moving: false },
      { no: 4, value: 6, gan_zhi: "戊申", liu_qin: "官鬼", liu_shen: "螣蛇", is_moving: true },
      { no: 5, value: 9, gan_zhi: "戊戌", liu_qin: "妻财", liu_shen: "白虎", is_moving: true },
      { no: 6, value: 8, gan_zhi: "戊子", liu_qin: "父母", liu_shen: "玄武", is_moving: false },
    ],
  },
  fortune_meihua: {
    tool: "meihua", method: "数字起卦（12,34）", upper: "震", lower: "兑",
    moving_line: 4, ben_gua: "雷泽归妹", hu_gua: "水火既济", bian_gua: "地泽临",
    ti_gua: "兑", yong_gua: "震", relation: "体克用", verdict: "体克用，可成但费力（小吉）",
    hu_upper: "坎", hu_lower: "离", bian_upper: "坤", bian_lower: "兑",
    wuxing: { ti: "金", yong: "木" },
  },
  fortune_chenggu: {
    tool: "chenggu", year_gz: "庚午", lunar_month: 5, lunar_day: 23, hour_zhi: "午",
    year_qian: 9, month_qian: 5, day_qian: 8, hour_qian: 10, total_qian: 32,
    verdict: "初年运蹇事难谋，渐有财源如水流；到得中年衣食旺，那时名利一齐收。",
  },
  fortune_xiaoliuren: {
    tool: "xiaoliuren", lunar_month: 5, lunar_day: 23, hour_zhi: "未",
    month_palace: "小吉", day_palace: "速喜", palace: "赤口",
    info: { "吉凶": "凶（口舌官非）", "五行": "金", "方位": "西方", "神煞": "白虎", "主数": "四、七、十",
            "断语": "赤口主口舌，官非切要防。" },
    finger: ["无名指", "上节"],
  },
  fortune_solar_info: {
    tool: "solar_info", solar: "2024-02-10 12:00", lunarYear: 2024, lunarMonth: 1,
    lunarDay: 1, lunarLeap: false, yearGanzhi: "甲辰", shengxiao: "龙",
    pillars: ["甲辰", "丙寅", "甲辰", "庚午"],
    jieqi: [{ name: "立春", time: "2024-02-04 16:26:53" }],
  },
};

// ---- 渲染冒烟 ----
function walk(el, fn) {
  if (!el || typeof el !== "object") return;
  fn(el);
  if (el.children) el.children.forEach((c) => walk(c, fn));
}

let rendered = 0, interactive = 0;
for (const [name, data] of Object.entries(FIXTURES)) {
  const View = viewOf(name);
  const block = { kind: "tool-result", meta: { ok: true, tool: name, data }, content: [] };
  let tree;
  try {
    tree = View({ block });
  } catch (e) {
    assert.fail(`${name} 渲染抛错: ${e.message}`);
  }
  rendered++;
  walk(tree, (el) => {
    if (el.props && (typeof el.props.onClick === "function"
      || typeof el.props.onSelect === "function")) interactive++;
  });
  assert.ok(interactive > 0, `${name} 未发现交互回调`);
}

// 关键结构断言
const zw = viewOf("fortune_ziwei")({ block: { kind: "tool-result",
  meta: { ok: true, tool: "fortune_ziwei", data: FIXTURES.fortune_ziwei }, content: [] } });
let palCount = 0;
walk(zw, (el) => { if (el.type === "g" && String(el.props.className ?? "").includes("ft-pal")) palCount++; });
assert.equal(palCount, 12, "紫微盘应有 12 个可点宫位");
assert.ok(palCount === 12 && true);

// meta 缺失时回退不抛错
for (const [name] of Object.entries(FIXTURES)) {
  const View = viewOf(name);
  View({ block: { kind: "tool-result", meta: null, content: [] } });
}

console.log(`渲染冒烟通过：${rendered}/7 视图渲染成功，交互回调存在，12 宫盘结构正确，meta 缺失回退正常`);
