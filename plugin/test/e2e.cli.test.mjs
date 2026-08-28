// dsh-fortune 端到端契约测试：真跑 `python -m fortune.cli`，
// 断言「工具参数 schema 广告的每个参数」都能被 CLI 接受（exit 0 + 结构化 meta）。
//
// 这是 argv 转发层与 Python CLI 之间的契约防线——此前的 ziwei --day-change
// 崩溃（CLI 未定义该选项 → meta=null → output schema 校验失败）即属此类契约
// 破裂，而 tools.test.mjs 用假 spawn 只断言 argv 组装、从不真跑 CLI，测不到。
//
// 无 Python 环境时整体跳过（node --test test/ 仍可在纯 Node 环境跑）。
import test from "node:test";
import assert from "node:assert/strict";
import path from "node:path";
import fs from "node:fs";
import { fileURLToPath } from "node:url";
import { apply } from "../lib/index.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PROJECT_DIR = path.resolve(__dirname, "..", "..");
const VENV_PY = path.join(PROJECT_DIR, ".venv", "Scripts", "python.exe");
const PYTHON = fs.existsSync(VENV_PY) ? VENV_PY : null;
const SKIP = PYTHON ? false : "未找到 venv Python（.venv/Scripts/python.exe），跳过 e2e 契约测试";

function makeCtx() {
  const registered = [];
  return {
    registered,
    tools: { register(t) { registered.push(t); } },
  };
}

function tools(ctx) {
  return Object.fromEntries(ctx.registered.map((t) => [t.name, t]));
}

test("e2e：全部工具 × 全部广告参数 真跑 CLI（契约）", { timeout: 300000, skip: SKIP }, async () => {
  const ctx = makeCtx();
  apply(ctx, { projectDir: PROJECT_DIR, pythonBin: PYTHON });
  const t = tools(ctx);
  const BIRTH = { year: 1991, month: 1, day: 11, hour: 1, minute: 1, gender: "男" };

  // 1) 八字：完整 BIRTH_SPEC（含 dayChange/trueSolar=false 开关）+ 流派 + 神煞基准
  let r = await t.fortune_bazi.execute({
    ...BIRTH, lng: 116.4, trueSolar: false, dayChange: 0, dst: false,
    tzHours: 8, school: "tiaohou", shenshaBase: "year",
  });
  assert.equal(r.ok, true, `bazi 失败: ${r.output}`);
  assert.equal(r.meta && r.meta.tool, "bazi");

  // 1b) 八字：dst 开关正例（1990 年在中国夏令时区间内）
  r = await t.fortune_bazi.execute({
    year: 1990, month: 6, day: 15, hour: 13, minute: 30, gender: "男", dst: true,
  });
  assert.equal(r.ok, true, `bazi dst 正例失败: ${r.output}`);

  // 2) 八字：--schools 多流派一次对比
  r = await t.fortune_bazi.execute({
    ...BIRTH, lng: 116.4, trueSolar: true, dayChange: 23,
    schools: "wangshuai,tiaohou,tongguan,geju",
  });
  assert.equal(r.ok, true, `bazi schools 失败: ${r.output}`);
  assert.deepEqual(Object.keys(r.meta.yongshen_all).sort(),
                   ["geju", "tiaohou", "tongguan", "wangshuai"]);

  // 3) 紫微：完整 BIRTH_SPEC + 庚年/闰月开关（此路径此前崩溃）
  r = await t.fortune_ziwei.execute({
    ...BIRTH, lng: 116.4, trueSolar: true, dayChange: 23, dst: false,
    gengSihua: "tianxiang", leapMode: "mid_split",
  });
  assert.equal(r.ok, true, `ziwei 失败: ${r.output}`);
  assert.equal(r.meta.tool, "ziwei");
  assert.equal(r.meta.sihua.length, 4, "生年四化应恰 4 项");
  assert.match(r.meta.year_pillar, /^[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]$/);

  // 4) 紫微：默认口径（主流庚年/闰月按当月）+ 时区参数（UTC+9 记录）
  r = await t.fortune_ziwei.execute({ ...BIRTH, lng: 116.4, tzHours: 9 });
  assert.equal(r.ok, true, `ziwei 默认口径失败: ${r.output}`);
  assert.ok(r.output.includes("时区 UTC+9 → UTC+8"), "紫微报告应显示时区换算步骤");

  // 5) 称骨
  r = await t.fortune_chenggu.execute({ ...BIRTH, lng: 116.4 });
  assert.equal(r.ok, true, `chenggu 失败: ${r.output}`);
  assert.equal(r.meta.tool, "chenggu");

  // 6) 历法速查
  r = await t.fortune_solar_info.execute({ year: 1991, month: 1, day: 11, hour: 11, minute: 1 });
  assert.equal(r.ok, true, `solar_info 失败: ${r.output}`);
  assert.equal(r.meta.tool, "solar_info");

  // 7) 小六壬
  r = await t.fortune_xiaoliuren.execute({ month: 5, day: 23, hourZhi: "酉" });
  assert.equal(r.ok, true, `xiaoliuren 失败: ${r.output}`);
  assert.equal(r.meta.tool, "xiaoliuren");

  // 8) 梅花：数字起卦（附卦爻辞）
  r = await t.fortune_meihua.execute({ numbers: [12, 34] });
  assert.equal(r.ok, true, `meihua 数字失败: ${r.output}`);
  assert.ok(r.meta.zhouyi && r.meta.zhouyi.ben_gua_ci, "梅花应附卦辞");

  // 9) 梅花：时间起卦
  r = await t.fortune_meihua.execute({ lunarYear: 1990, lunarMonth: 3, lunarDay: 12, hour: 10 });
  assert.equal(r.ok, true, `meihua 时间失败: ${r.output}`);

  // 10) 六爻：手动掷币（附规则化断语）
  r = await t.fortune_liuyao.execute({
    backs: [1, 1, 1, 1, 1, 1], monthZhi: "午", dayGanzhi: "甲子",
  });
  assert.equal(r.ok, true, `liuyao 失败: ${r.output}`);
  assert.ok(r.meta.duanyu && r.meta.duanyu.includes("断语"), "六爻应附规则化断语");

  // 11) 六爻：随机起卦
  r = await t.fortune_liuyao.execute({ monthZhi: "午", dayGanzhi: "甲子", random: true });
  assert.equal(r.ok, true, `liuyao random 失败: ${r.output}`);
  assert.deepEqual(r.meta.backs.length, 6);

  // 12) 六爻：背=阴约定
  r = await t.fortune_liuyao.execute({
    backs: [1, 1, 1, 1, 1, 1], monthZhi: "午", dayGanzhi: "甲子", coinBack: "yin",
  });
  assert.equal(r.ok, true, `liuyao yin 失败: ${r.output}`);
});

test("e2e：非法输入返回可读报错（不崩溃、不静默）", { timeout: 120000, skip: SKIP }, async () => {
  const ctx = makeCtx();
  apply(ctx, { projectDir: PROJECT_DIR, pythonBin: PYTHON });
  const t = tools(ctx);

  // 非法月建
  let r = await t.fortune_liuyao.execute({
    backs: [1, 1, 1, 1, 1, 1], monthZhi: "猫", dayGanzhi: "甲子",
  });
  assert.equal(r.ok, false);
  assert.ok(r.output.includes("输入错误"), `应透出输入错误：${r.output}`);

  // 不存在的干支（甲丑：阴阳不配）
  r = await t.fortune_liuyao.execute({
    backs: [1, 1, 1, 1, 1, 1], monthZhi: "午", dayGanzhi: "甲丑",
  });
  assert.equal(r.ok, false);
  assert.ok(r.output.includes("输入错误"));

  // 不存在的公历日期
  r = await t.fortune_bazi.execute({ year: 1991, month: 2, day: 31, hour: 8 });
  assert.equal(r.ok, false);
  assert.ok(r.output.includes("输入错误"));

  // dst 误用（1991 年无中国夏令时）→ 应报可读输入错误而非裸 traceback
  r = await t.fortune_bazi.execute({ year: 1991, month: 1, day: 11, hour: 0, dst: true });
  assert.equal(r.ok, false);
  assert.ok(r.output.includes("输入错误"), `dst 误用应报输入错误：${r.output}`);
  assert.ok(r.output.includes("夏令时"));

  // 数字起卦个数/取值非法
  r = await t.fortune_meihua.execute({ numbers: [0, 34] });
  assert.equal(r.ok, false);
  assert.ok(r.output.includes("输入错误"));
});
