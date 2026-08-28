// 端到端冒烟：真实 spawnSync 调用 venv Python 跑 fortune_bazi / fortune_solar_info
import { apply } from "../lib/index.js";

const registered = [];
const ctx = { tools: { register(t) { registered.push(t); } } };
apply(ctx, {
  projectDir: "D:/ai工作区/fortune-assistant",
  pythonBin: "D:/ai工作区/fortune-assistant/.venv/Scripts/python.exe",
});

const t = registered.find((x) => x.name === "fortune_bazi");
const res = await t.execute({ year: 1990, month: 6, day: 15, hour: 13, minute: 30, gender: "男" });
console.log("ok =", res.ok, "exit =", res.exitCode);
console.log("output 前 400 字:");
console.log(res.output.slice(0, 400));

const info = registered.find((x) => x.name === "fortune_solar_info");
const r2 = await info.execute({ year: 2024, month: 2, day: 10, hour: 12 });
console.log("solar_info ok =", r2.ok);
console.log(r2.output.split("\n").slice(0, 4).join("\n"));

const err = registered.find((x) => x.name === "fortune_bazi");
const bad = await err.execute({ year: 1990, month: 13, day: 1, hour: 12 });
console.log("非法输入 ok =", bad.ok, "exit =", bad.exitCode, "| 提示:", (bad.output || bad.error).split("\n")[0].slice(0, 80));
