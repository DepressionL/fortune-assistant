// 括号配对检查（跳过字符串/模板/注释）
const fs = require("fs");
const src = fs.readFileSync("D:/ai工作区/fortune-assistant/plugin-client/lib/client.js", "utf8");
const stack = [];
let i = 0, line = 1;
const lines = src.split("\n");
const at = () => lines[line - 1];
while (i < src.length) {
  const ch = src[i];
  if (ch === "\n") { line++; i++; continue; }
  if (ch === "/" && src[i + 1] === "/") { while (i < src.length && src[i] !== "\n") i++; continue; }
  if (ch === "/" && src[i + 1] === "*") {
    i += 2;
    while (i < src.length && !(src[i] === "*" && src[i + 1] === "/")) { if (src[i] === "\n") line++; i++; }
    i += 2; continue;
  }
  if (ch === '"' || ch === "'" || ch === "`") {
    const q = ch; i++;
    if (q !== "`") {
      while (i < src.length && src[i] !== q) { if (src[i] === "\n") line++; if (src[i] === "\\") i++; i++; }
      i++; continue;
    }
    while (i < src.length) {
      if (src[i] === "\\") { i += 2; continue; }
      if (src[i] === "`") { i++; break; }
      if (src[i] === "\n") line++;
      if (src[i] === "$" && src[i + 1] === "{") { stack.push({ c: "{", l: line }); i += 2; continue; }
      if (src[i] === "}") {
        const t = stack.pop();
        if (!t || t.c !== "{") { console.log("line", line, "unexpected } in template"); process.exit(1); }
        i++; continue;
      }
      i++;
    }
    continue;
  }
  if (ch === "(" || ch === "{" || ch === "[") { stack.push({ c: ch, l: line }); i++; continue; }
  if (ch === ")" || ch === "}" || ch === "]") {
    const t = stack.pop();
    const want = ch === ")" ? "(" : ch === "}" ? "{" : "[";
    if (!t) { console.log("line", line, "unmatched close", ch); console.log(at().slice(0, 120)); process.exit(1); }
    if (t.c !== want) {
      console.log("line", line, "mismatch: want close of", t.c, "opened at line", t.l, "got", ch);
      console.log(at().slice(0, 120)); process.exit(1);
    }
    i++; continue;
  }
  i++;
}
if (stack.length) {
  const t = stack[stack.length - 1];
  console.log("EOF: unclosed", t.c, "opened at line", t.l);
  for (const s of stack.slice(-8)) console.log("  open", s.c, "line", s.l);
} else {
  console.log("括号平衡 OK");
}
