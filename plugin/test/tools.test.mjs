// dsh-fortune 插件工具测试（node:test，注入假 spawn，无需 Python 环境）
// 运行：node --test test/
import test from "node:test";
import assert from "node:assert/strict";
import { apply } from "../lib/index.js";

function makeCtx() {
  const registered = [];
  return {
    registered,
    tools: {
      register(t) {
        registered.push(t);
      },
    },
  };
}

function makeSpawn(calls) {
  return (bin, args, opts) => {
    calls.push({ bin, args, opts });
    return { status: 0, stdout: "ok", stderr: "" };
  };
}

const TWELVE_TOOLS = [
  "fortune_bazi",
  "fortune_ziwei",
  "fortune_chenggu",
  "fortune_xiaoliuren",
  "fortune_meihua",
  "fortune_liuyao",
  "fortune_liuren",
  "fortune_qimen",
  "fortune_qizheng",
  "fortune_solar_info",
  "fortune_context",
  "fortune_comprehensive",
];

test("注册 12 个工具且参数 schema 根为 object（DSH 方言要求）", () => {
  const ctx = makeCtx();
  apply(ctx, { projectDir: "D:/proj", pythonBin: "py" });
  assert.deepEqual(ctx.registered.map((t) => t.name), TWELVE_TOOLS);
  for (const t of ctx.registered) {
    assert.equal(t.parameters.type, "object");
    assert.ok(t.output.schema, `tool ${t.name} 缺 output.schema`);
    assert.equal(t.output.schema.type, "object");
    assert.equal(typeof t.execute, "function");
  }
});

test("fortune_bazi 转发出生参数与流派开关到 `python -m fortune.cli bazi`", async () => {
  const ctx = makeCtx();
  const calls = [];
  apply(ctx, { projectDir: "D:/proj", pythonBin: "py", spawn: makeSpawn(calls) });
  const t = ctx.registered.find((x) => x.name === "fortune_bazi");
  const res = await t.execute({
    year: 1990, month: 6, day: 15, hour: 13, minute: 30, gender: "男",
    lng: 116.4, trueSolar: false, dayChange: 0, school: "tiaohou",
    shenshaBase: "year",
  });
  assert.equal(res.ok, true);
  assert.equal(calls.length, 1);
  const { bin, args, opts } = calls[0];
  assert.equal(bin, "py");
  assert.deepEqual(args.slice(0, 3), ["-m", "fortune.cli", "bazi"]);
  assert.ok(args.includes("--no-true-solar"));
  assert.ok(args.includes("--school") && args[args.indexOf("--school") + 1] === "tiaohou");
  assert.ok(args.includes("--shensha-base") && args[args.indexOf("--shensha-base") + 1] === "year");
  assert.ok(args.includes("--day-change") && args[args.indexOf("--day-change") + 1] === "0");
  assert.ok(args.includes("--lng") && args[args.indexOf("--lng") + 1] === "116.4");
  assert.equal(opts.cwd, "D:/proj");
  assert.equal(opts.env.PYTHONIOENCODING, "utf-8");
});

test("execute 从输出中拆出内嵌 meta（标记后 JSON，模型面文本剔除标记）", async () => {
  const ctx = makeCtx();
  const raw = "# 命盘报告\n\n正文内容\n\n===DSH_META_JSON===\n{\"tool\":\"bazi\",\"chart\":{\"pillars\":[]}}";
  const calls = [];
  const spawn = (bin, args, opts) => {
    calls.push({ bin, args, opts });
    // 第二次调用（--no-true-solar 口径预计算）返回无 meta 输出，模拟 CLI 正常
    return calls.length === 1
      ? { status: 0, stdout: raw, stderr: "" }
      : { status: 0, stdout: "alt ok", stderr: "" };
  };
  apply(ctx, { projectDir: "D:/proj", pythonBin: "py", spawn });
  const t = ctx.registered.find((x) => x.name === "fortune_bazi");
  const res = await t.execute({ year: 1990, month: 6, day: 15, hour: 13 });
  assert.equal(res.ok, true);
  assert.equal(res.output, "# 命盘报告\n\n正文内容", "模型面文本应剔除标记与 JSON");
  assert.deepEqual(res.meta, { tool: "bazi", chart: { pillars: [] } });
  // 口径预计算：默认真太阳时 → 附带钟表时对照（无 meta 时安全跳过）
  assert.equal(calls.length, 2);
  assert.ok(calls[1].args.includes("--no-true-solar"));
  assert.equal(res.meta.alternates, undefined);
  // argv 不再带 --meta-json（meta 随身，不依赖临时文件）
  assert.ok(!calls[0].args.includes("--meta-json"));
});

test("presentationMeta 投影 value.meta（无 meta 时 {ok:false}）", () => {
  const ctx = makeCtx();
  apply(ctx, { projectDir: "D:/proj", pythonBin: "py", spawn: makeSpawn([]) });
  const t = ctx.registered.find((x) => x.name === "fortune_bazi");
  const good = t.output.presentationMeta({}, { ok: true, meta: { tool: "bazi", chart: { pillars: [] } } });
  assert.equal(good.ok, true);
  assert.equal(good.tool, "fortune_bazi");
  assert.deepEqual(good.data, { tool: "bazi", chart: { pillars: [] } });
  const bad = t.output.presentationMeta({}, { ok: true, meta: null });
  assert.equal(bad.ok, false);
  assert.equal(bad.data, null);
});

test("无标记输出时省略 meta 键（避免 null 触发 output schema 类型错误）", async () => {
  const ctx = makeCtx();
  apply(ctx, { projectDir: "D:/proj", pythonBin: "py",
               spawn: () => ({ status: 0, stdout: "纯文本", stderr: "" }) });
  const t = ctx.registered.find((x) => x.name === "fortune_liuyao");
  const res = await t.execute({ backs: [1, 1, 1, 1, 1, 1], monthZhi: "午", dayGanzhi: "甲子" });
  assert.equal(res.output, "纯文本");
  assert.equal(res.meta, undefined);
  assert.ok(!("meta" in res));
});

test("CLI 非零退出时错误正文前置可见（不再被 schema 吞掉）", async () => {
  const ctx = makeCtx();
  const exit2 = () => ({ status: 2, stdout: "", stderr: "bad args" });
  apply(ctx, { projectDir: "D:/proj", pythonBin: "py", spawn: exit2 });
  const t = ctx.registered.find((x) => x.name === "fortune_solar_info");
  const res = await t.execute({ year: 2024, month: 2, day: 10 });
  assert.equal(res.ok, false);
  assert.equal(res.exitCode, 2);
  assert.ok(res.output.includes("CLI 执行失败"), "应带失败标记");
  assert.ok(res.output.includes("bad args"), "应透出真实报错");
});

test("fortune_bazi --schools 多流派转发", async () => {
  const ctx = makeCtx();
  const calls = [];
  apply(ctx, { projectDir: "D:/proj", pythonBin: "py", spawn: makeSpawn(calls) });
  const t = ctx.registered.find((x) => x.name === "fortune_bazi");
  await t.execute({ year: 1990, month: 6, day: 15, hour: 13, schools: "tiaohou,tongguan" });
  const args = calls[0].args;
  assert.ok(args.includes("--schools") && args[args.indexOf("--schools") + 1] === "tiaohou,tongguan");
});

test("fortune_liuyao --random 随机起卦转发", async () => {
  const ctx = makeCtx();
  const calls = [];
  apply(ctx, { projectDir: "D:/proj", pythonBin: "py", spawn: makeSpawn(calls) });
  const t = ctx.registered.find((x) => x.name === "fortune_liuyao");
  const res = await t.execute({ monthZhi: "午", dayGanzhi: "甲子", random: true });
  assert.equal(res.ok, true);
  assert.ok(calls[0].args.includes("--random"));
  assert.ok(!calls[0].args.includes("--backs"));
});

test("fortune_liuyao 既无 backs 也无 random 时显式报错", async () => {
  const ctx = makeCtx();
  apply(ctx, { projectDir: "D:/proj", pythonBin: "py", spawn: makeSpawn([]) });
  const t = ctx.registered.find((x) => x.name === "fortune_liuyao");
  const res = await t.execute({ monthZhi: "午", dayGanzhi: "甲子" });
  assert.equal(res.ok, false);
  assert.ok(res.error.includes("random"));
});

test("fortune_ziwei 必带庚年四化/闰月开关", async () => {
  const ctx = makeCtx();
  const calls = [];
  apply(ctx, { projectDir: "D:/proj", pythonBin: "py", spawn: makeSpawn(calls) });
  const t = ctx.registered.find((x) => x.name === "fortune_ziwei");
  await t.execute({ year: 2000, month: 2, day: 5, hour: 9,
                    gengSihua: "tianxiang", leapMode: "mid_split", interpret: true });
  const args = calls[0].args;
  assert.ok(args.includes("--geng-sihua") && args[args.indexOf("--geng-sihua") + 1] === "tianxiang");
  assert.ok(args.includes("--leap-mode") && args[args.indexOf("--leap-mode") + 1] === "mid_split");
  assert.ok(args.includes("--interpret"));
});

test("fortune_bazi 口径预计算：默认真太阳时附带钟表时对照 meta", async () => {
  const ctx = makeCtx();
  const calls = [];
  const spawn = (bin, args, opts) => {
    calls.push({ bin, args, opts });
    const tag = args.includes("--no-true-solar") ? "clock" : "solar";
    return { status: 0, stdout: `===DSH_META_JSON===\n{"tool":"bazi","tag":"${tag}"}`, stderr: "" };
  };
  apply(ctx, { projectDir: "D:/proj", pythonBin: "py", spawn });
  const t = ctx.registered.find((x) => x.name === "fortune_bazi");
  const res = await t.execute({ year: 1990, month: 6, day: 15, hour: 13 });
  assert.equal(calls.length, 2);
  assert.equal(res.meta.tag, "solar");
  assert.deepEqual(res.meta.alternates, { clock: { tool: "bazi", tag: "clock" } });
  // trueSolar=false 时不再预计算（避免重复）
  const ctx2 = makeCtx();
  const calls2 = [];
  apply(ctx2, { projectDir: "D:/proj", pythonBin: "py",
                spawn: (bin, args) => { calls2.push(args); return { status: 0, stdout: "ok", stderr: "" }; } });
  const t2 = ctx2.registered.find((x) => x.name === "fortune_bazi");
  await t2.execute({ year: 1990, month: 6, day: 15, hour: 13, trueSolar: false });
  assert.equal(calls2.length, 1);
});

test("fortune_liuyao --date 自动推导月建日辰转发", async () => {
  const ctx = makeCtx();
  const calls = [];
  apply(ctx, { projectDir: "D:/proj", pythonBin: "py", spawn: makeSpawn(calls) });
  const t = ctx.registered.find((x) => x.name === "fortune_liuyao");
  const res = await t.execute({ backs: [2, 3, 1, 0, 3, 2], date: "2026-08-29",
                                topic: "求财", question: "近期财运" });
  assert.equal(res.ok, true);
  const args = calls[0].args;
  assert.ok(args.includes("--date") && args[args.indexOf("--date") + 1] === "2026-08-29");
  assert.ok(!args.includes("--month-zhi") && !args.includes("--day-ganzhi"));
  assert.ok(args.includes("--topic") && args[args.indexOf("--topic") + 1] === "求财");
  assert.ok(args.includes("--question") && args[args.indexOf("--question") + 1] === "近期财运");
});

test("fortune_liuyao 无 date 且无月建日辰时显式报错", async () => {
  const ctx = makeCtx();
  apply(ctx, { projectDir: "D:/proj", pythonBin: "py", spawn: makeSpawn([]) });
  const t = ctx.registered.find((x) => x.name === "fortune_liuyao");
  const res = await t.execute({ backs: [1, 1, 1, 1, 1, 1] });
  assert.equal(res.ok, false);
  assert.ok(res.error.includes("date"));
});

test("fortune_context 与 fortune_comprehensive 转发", async () => {
  const ctx = makeCtx();
  const calls = [];
  apply(ctx, { projectDir: "D:/proj", pythonBin: "py", spawn: makeSpawn(calls) });
  const tc = ctx.registered.find((x) => x.name === "fortune_context");
  await tc.execute({ year: 1990, month: 6, day: 15, hour: 13, lng: 112.5 });
  assert.equal(calls[0].args[2], "context");
  assert.ok(calls[0].args.includes("--lng") && calls[0].args[calls[0].args.indexOf("--lng") + 1] === "112.5");
  const tm = ctx.registered.find((x) => x.name === "fortune_comprehensive");
  await tm.execute({ year: 1990, month: 6, day: 15, hour: 13, anchorYear: 2026,
                     liuyaoBacks: [2, 3, 1, 0, 3, 2], liuyaoDate: "2026-08-29",
                     liuyaoTopic: "求财", coinBack: "yang" });
  const args = calls[1].args;
  assert.equal(args[2], "comprehensive");
  assert.ok(args.includes("--anchor-year") && args[args.indexOf("--anchor-year") + 1] === "2026");
  assert.ok(args.includes("--liuyao-backs") && args[args.indexOf("--liuyao-backs") + 1] === "2,3,1,0,3,2");
  assert.ok(args.includes("--liuyao-date") && args[args.indexOf("--liuyao-date") + 1] === "2026-08-29");
  assert.ok(args.includes("--liuyao-topic") && args[args.indexOf("--liuyao-topic") + 1] === "求财");
});

test("fortune_meihua 数字起卦（2 个数）", async () => {
  const ctx = makeCtx();
  const calls = [];
  apply(ctx, { projectDir: "D:/proj", pythonBin: "py", spawn: makeSpawn(calls) });
  const t = ctx.registered.find((x) => x.name === "fortune_meihua");
  await t.execute({ numbers: [12, 34] });
  const args = calls[0].args;
  assert.equal(args[2], "meihua");
  assert.deepEqual(args.slice(3, 5), ["12", "34"]);
  assert.ok(!args.includes("--meta-json"));
});

test("fortune_meihua 缺参数显式报错（不静默）", async () => {
  const ctx = makeCtx();
  apply(ctx, { projectDir: "D:/proj", pythonBin: "py", spawn: makeSpawn([]) });
  const t = ctx.registered.find((x) => x.name === "fortune_meihua");
  const res = await t.execute({});
  assert.equal(res.ok, false);
  assert.ok(res.error.includes("numbers"));
});

test("fortune_liuyao 六次掷币转发", async () => {
  const ctx = makeCtx();
  const calls = [];
  apply(ctx, { projectDir: "D:/proj", pythonBin: "py", spawn: makeSpawn(calls) });
  const t = ctx.registered.find((x) => x.name === "fortune_liuyao");
  await t.execute({ backs: [2, 3, 1, 0, 3, 2], monthZhi: "午",
                    dayGanzhi: "甲子", coinBack: "yin" });
  const args = calls[0].args;
  assert.ok(args.includes("--backs") && args[args.indexOf("--backs") + 1] === "2,3,1,0,3,2");
  assert.ok(args.includes("--coin-back") && args[args.indexOf("--coin-back") + 1] === "yin");
});

test("spawn 失败返回 ok=false 且带错误信息", async () => {
  const ctx = makeCtx();
  const failing = () => ({ status: null, stdout: "", stderr: "", error: new Error("boom") });
  apply(ctx, { projectDir: "D:/proj", pythonBin: "py", spawn: failing });
  const t = ctx.registered.find((x) => x.name === "fortune_bazi");
  const res = await t.execute({ year: 1990, month: 1, day: 1, hour: 12 });
  assert.equal(res.ok, false);
  assert.equal(res.exitCode, -1);
  assert.ok(res.error.includes("spawn 失败"));
});

test("非零退出码携带 exitCode 与 stderr 输出", async () => {
  const ctx = makeCtx();
  const exit2 = () => ({ status: 2, stdout: "", stderr: "bad args" });
  apply(ctx, { projectDir: "D:/proj", pythonBin: "py", spawn: exit2 });
  const t = ctx.registered.find((x) => x.name === "fortune_solar_info");
  const res = await t.execute({ year: 2024, month: 2, day: 10 });
  assert.equal(res.ok, false);
  assert.equal(res.exitCode, 2);
  assert.ok(res.output.includes("bad args"));
});
