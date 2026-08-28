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

const SEVEN_TOOLS = [
  "fortune_bazi",
  "fortune_ziwei",
  "fortune_chenggu",
  "fortune_xiaoliuren",
  "fortune_meihua",
  "fortune_liuyao",
  "fortune_solar_info",
];

test("注册 7 个工具且参数 schema 根为 object（DSH 方言要求）", () => {
  const ctx = makeCtx();
  apply(ctx, { projectDir: "D:/proj", pythonBin: "py" });
  assert.deepEqual(ctx.registered.map((t) => t.name), SEVEN_TOOLS);
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
    return { status: 0, stdout: raw, stderr: "" };
  };
  apply(ctx, { projectDir: "D:/proj", pythonBin: "py", spawn });
  const t = ctx.registered.find((x) => x.name === "fortune_bazi");
  const res = await t.execute({ year: 1990, month: 6, day: 15, hour: 13 });
  assert.equal(res.ok, true);
  assert.equal(res.output, "# 命盘报告\n\n正文内容", "模型面文本应剔除标记与 JSON");
  assert.deepEqual(res.meta, { tool: "bazi", chart: { pillars: [] } });
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

test("无标记输出时 meta 为 null 且不影响文本", async () => {
  const ctx = makeCtx();
  apply(ctx, { projectDir: "D:/proj", pythonBin: "py",
               spawn: () => ({ status: 0, stdout: "纯文本", stderr: "" }) });
  const t = ctx.registered.find((x) => x.name === "fortune_liuyao");
  const res = await t.execute({ backs: [1, 1, 1, 1, 1, 1], monthZhi: "午", dayGanzhi: "甲子" });
  assert.equal(res.output, "纯文本");
  assert.equal(res.meta, null);
});

test("fortune_ziwei 必带庚年四化/闰月开关", async () => {
  const ctx = makeCtx();
  const calls = [];
  apply(ctx, { projectDir: "D:/proj", pythonBin: "py", spawn: makeSpawn(calls) });
  const t = ctx.registered.find((x) => x.name === "fortune_ziwei");
  await t.execute({ year: 2000, month: 2, day: 5, hour: 9,
                    gengSihua: "tianxiang", leapMode: "mid_split" });
  const args = calls[0].args;
  assert.ok(args.includes("--geng-sihua") && args[args.indexOf("--geng-sihua") + 1] === "tianxiang");
  assert.ok(args.includes("--leap-mode") && args[args.indexOf("--leap-mode") + 1] === "mid_split");
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
