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

test("execute 附带 --meta-json 落盘参数（路径按工具名+参数哈希确定）", async () => {
  const ctx = makeCtx();
  const calls = [];
  apply(ctx, { projectDir: "D:/proj", pythonBin: "py", spawn: makeSpawn(calls) });
  const t = ctx.registered.find((x) => x.name === "fortune_bazi");
  const a1 = { year: 1990, month: 6, day: 15, hour: 13 };
  await t.execute(a1);
  const args1 = calls[0].args;
  const i1 = args1.indexOf("--meta-json");
  assert.ok(i1 >= 0 && i1 === args1.length - 2, "--meta-json 应为倒数第二个参数");
  const path1 = args1[i1 + 1];
  assert.ok(path1.includes("dsh-fortune-fortune_bazi-"), path1);
  await t.execute(a1);
  const args2 = calls[1].args;
  assert.equal(args2[args2.indexOf("--meta-json") + 1], path1, "同参数两次调用路径应一致");
  await t.execute({ ...a1, hour: 14 });
  const args3 = calls[2].args;
  assert.notEqual(args3[args3.indexOf("--meta-json") + 1], path1, "不同参数路径应不同");
});

test("presentationMeta 投影 readMeta 读取的结构化 JSON", () => {
  const ctx = makeCtx();
  apply(ctx, { projectDir: "D:/proj", pythonBin: "py",
               spawn: makeSpawn([]),
               readMeta: () => JSON.stringify({ tool: "bazi", chart: { pillars: [] } }) });
  const t = ctx.registered.find((x) => x.name === "fortune_bazi");
  const meta = t.output.presentationMeta({ year: 1990, month: 6, day: 15, hour: 13 }, {});
  assert.equal(meta.ok, true);
  assert.equal(meta.tool, "fortune_bazi");
  assert.deepEqual(meta.data, { tool: "bazi", chart: { pillars: [] } });
});

test("presentationMeta 在 readMeta 抛错/文件缺失时返回 {ok:false} 且不抛错", () => {
  const ctx = makeCtx();
  apply(ctx, { projectDir: "D:/proj", pythonBin: "py",
               spawn: makeSpawn([]),
               readMeta: () => { throw new Error("ENOENT"); } });
  for (const name of ["fortune_bazi", "fortune_ziwei", "fortune_liuyao",
                      "fortune_meihua", "fortune_chenggu", "fortune_xiaoliuren",
                      "fortune_solar_info"]) {
    const t = ctx.registered.find((x) => x.name === name);
    const meta = t.output.presentationMeta({}, {});
    assert.equal(meta.ok, false, name);
    assert.equal(meta.data, null);
  }
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
  assert.ok(args.includes("--meta-json"));
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
