// dsh-fortune-client：Web 客户端插件（fortune_* 七工具按 wire tool name 注册
// toolview 行渲染：八字四柱卡 + 五行条 + 紫微十二宫盘 + 六爻卦象 + 梅花体用 +
// 称骨 + 小六壬 + 历法速查）。v0.1 设计要点：
// - D1：settled 数据源 = block.meta（宿主插件 presentationMeta 投影——
//   canonical value 不上 UI）；
// - D2：样式零颜色字面量，全部走 --dsw-alias-* 语义 token（暗色主题自适应）；
// - D3：动效：卡片入场 stagger、紫微十二宫逐宫绽放、六爻爻线逐爻描画、
//   命宫/动爻呼吸脉冲、五行条生长、称骨总骨重弹入；prefers-reduced-motion
//   全量降级；键盘焦点与 aria 标注无障碍；
// - D4：meta 缺失（旧日志重放）时优雅回退到纯文本 details。
(function () {
  "use strict";
  if (typeof window === "undefined") return;   // 仅浏览器装配；node 测试注入后直接驱动

  window.__ModuleLoader__.load({
    id: "dsh-fortune-client",
    factory: (require) => {
      const module = { exports: {} };
      const exports = module.exports;
      Object.defineProperty(exports, Symbol.toStringTag, { value: "Module" });
      const react = require("react");
      const h = react.createElement;
      const useState = react.useState;

      // ------------------------------------------------------------------
      // 样式（D2/D3）：零颜色字面量；入场/脉冲/描画/生长动效；动效降级。
      // ------------------------------------------------------------------
      const STYLE_TEXT = [
        ".ft-node{font-family:inherit;border:1px solid var(--dsw-alias-border-l2);",
        "border-radius:12px;padding:12px 14px;margin:6px 0;max-width:720px;",
        "background:var(--dsw-alias-bg-layer-1);color:var(--dsw-alias-label-primary);",
        "animation:ft-rise .28s cubic-bezier(.22,1,.36,1) both;",
        "animation-delay:calc(var(--n,0)*70ms)}",
        "@keyframes ft-rise{0%{opacity:0;transform:translateY(8px)}100%{opacity:1;transform:none}}",
        ".ft-head{display:flex;align-items:center;gap:8px;flex-wrap:wrap}",
        ".ft-title{font-size:13.5px;font-weight:600;color:var(--dsw-alias-label-primary)}",
        ".ft-meta{font-size:12px;color:var(--dsw-alias-label-secondary);",
        "display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-top:6px}",
        ".ft-caption{font-size:11px;color:var(--dsw-alias-label-tertiary)}",
        ".ft-pill{font-size:11px;line-height:18px;padding:0 8px;border-radius:9px;",
        "border:1px solid var(--dsw-alias-border-l2);color:var(--dsw-alias-label-secondary);",
        "animation:ft-pop .18s cubic-bezier(.34,1.56,.64,1) both}",
        ".ft-pill.ft-ok{color:var(--dsw-alias-state-success-primary);",
        "border-color:var(--dsw-alias-state-success-secondary)}",
        ".ft-pill.ft-run{color:var(--dsw-alias-brand-primary);",
        "border-color:var(--dsw-alias-brand-primary);animation:ft-breathe 1.2s ease-in-out infinite}",
        ".ft-pill.ft-warn{color:var(--dsw-alias-state-warn-primary);",
        "border-color:var(--dsw-alias-state-warn-secondary)}",
        ".ft-pill.ft-fail{color:var(--dsw-alias-state-error-primary);",
        "border-color:var(--dsw-alias-state-error-secondary)}",
        "@keyframes ft-pop{0%{transform:scale(.85);opacity:0}100%{transform:scale(1);opacity:1}}",
        "@keyframes ft-breathe{0%,100%{opacity:1}50%{opacity:.55}}",
        ".ft-sec{margin-top:10px}",
        ".ft-sec-h{font-size:11px;color:var(--dsw-alias-label-tertiary);",
        "letter-spacing:.04em;margin-bottom:5px}",
        ".ft-chips{display:flex;flex-wrap:wrap;gap:5px;margin-top:5px}",
        ".ft-chip{font-size:11px;line-height:18px;padding:0 7px;border-radius:8px;",
        "border:1px solid var(--dsw-alias-border-l2);color:var(--dsw-alias-label-secondary);",
        "animation:ft-pop .18s cubic-bezier(.34,1.56,.64,1) both}",
        // 八字四柱
        ".ft-pillars{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:8px}",
        ".ft-pillar{border:1px solid var(--dsw-alias-border-l2);border-radius:10px;",
        "padding:8px 6px;text-align:center;background:var(--dsw-alias-bg-base);",
        "animation:ft-rise .3s cubic-bezier(.22,1,.36,1) both;",
        "animation-delay:calc(var(--n,0)*80ms + 60ms)}",
        ".ft-pillar.ft-day{border-color:var(--dsw-alias-brand-primary);",
        "box-shadow:0 0 0 1px var(--dsw-alias-brand-primary)}",
        ".ft-pname{font-size:11px;color:var(--dsw-alias-label-tertiary)}",
        ".ft-gz{font-size:22px;font-weight:600;line-height:1.25;letter-spacing:.04em}",
        ".ft-day .ft-gz{color:var(--dsw-alias-brand-primary)}",
        ".ft-sub{font-size:10.5px;color:var(--dsw-alias-label-secondary);",
        "margin-top:2px;word-break:break-all}",
        ".ft-hide{font-size:10px;color:var(--dsw-alias-label-tertiary);margin-top:3px}",
        // 五行条
        ".ft-bar-row{display:flex;align-items:center;gap:8px;margin-top:4px}",
        ".ft-bar-l{width:14px;font-size:12px;color:var(--dsw-alias-label-secondary);",
        "text-align:center;flex:none}",
        ".ft-bar{flex:1;height:8px;border-radius:4px;background:var(--dsw-alias-bg-layer-3);",
        "overflow:hidden}",
        ".ft-bar>i{display:block;height:100%;border-radius:4px;",
        "background:var(--dsw-alias-brand-primary);",
        "animation:ft-grow .7s cubic-bezier(.22,1,.36,1) both;",
        "animation-delay:calc(var(--n,0)*90ms + 120ms);transform-origin:left}",
        "@keyframes ft-grow{0%{transform:scaleX(0)}100%{transform:scaleX(1)}}",
        ".ft-bar-v{width:52px;font-size:11px;color:var(--dsw-alias-label-tertiary);",
        "text-align:right;flex:none}",
        // 紫微盘
        ".ft-zw{display:flex;justify-content:center;margin-top:8px}",
        ".ft-zw svg{max-width:100%;height:auto}",
        ".ft-pal{opacity:0;transform-box:fill-box;transform-origin:center;",
        "animation:ft-bloom .45s cubic-bezier(.22,1,.36,1) forwards;",
        "animation-delay:calc(var(--i,0)*70ms)}",
        "@keyframes ft-bloom{0%{opacity:0;transform:scale(.6)}",
        "60%{transform:scale(1.05)}100%{opacity:1;transform:scale(1)}}",
        ".ft-pal:hover{filter:brightness(1.08)}",
        ".ft-zw-ming{animation:ft-breathe 2.4s ease-in-out infinite}",
        ".ft-ring{fill:none;stroke:var(--dsw-alias-border-l2);stroke-width:1.2}",
        ".ft-sep{stroke:var(--dsw-alias-border-l2);stroke-width:1}",
        ".ft-star{font-size:10px}",
        ".ft-star4{font-weight:600}",
        // 六爻
        ".ft-yaos{margin-top:8px;border:1px solid var(--dsw-alias-border-l2);",
        "border-radius:10px;padding:6px 10px;background:var(--dsw-alias-bg-base)}",
        ".ft-yao{display:flex;align-items:center;gap:10px;padding:5px 0;",
        "animation:ft-rise .25s ease-out both;animation-delay:calc(var(--n,0)*60ms)}",
        ".ft-yao-idx{width:34px;font-size:11px;color:var(--dsw-alias-label-tertiary);flex:none}",
        ".ft-yao-mark{width:14px;font-size:13px;flex:none;text-align:center}",
        ".ft-yao-mark.ft-mov{color:var(--dsw-alias-state-warn-primary);",
        "animation:ft-breathe 1s ease-in-out infinite}",
        ".ft-yao-glyph{flex:1;display:flex;flex-direction:column;gap:3px}",
        ".ft-glyph-yang{height:6px;border-radius:3px;",
        "background:var(--dsw-alias-label-primary);",
        "animation:ft-draw .4s ease-out both;animation-delay:calc(var(--n,0)*60ms)}",
        ".ft-glyph-yin{display:flex;gap:22%;height:6px}",
        ".ft-glyph-yin>i{flex:1;height:6px;border-radius:3px;",
        "background:var(--dsw-alias-label-primary);",
        "animation:ft-draw .4s ease-out both;animation-delay:calc(var(--n,0)*60ms)}",
        "@keyframes ft-draw{0%{transform:scaleX(0)}100%{transform:scaleX(1)}}",
        ".ft-yao-chips{display:flex;gap:5px;flex-wrap:wrap;min-width:150px;justify-content:flex-end}",
        ".ft-tag{font-size:10px;line-height:16px;padding:0 5px;border-radius:7px;",
        "border:1px solid var(--dsw-alias-brand-primary);",
        "color:var(--dsw-alias-brand-primary)}",
        // 梅花
        ".ft-gua-row{display:flex;gap:10px;align-items:stretch;margin-top:8px;flex-wrap:wrap}",
        ".ft-gua-card{flex:1;min-width:120px;border:1px solid var(--dsw-alias-border-l2);",
        "border-radius:10px;padding:10px 8px;text-align:center;",
        "background:var(--dsw-alias-bg-base);",
        "animation:ft-rise .3s cubic-bezier(.22,1,.36,1) both;",
        "animation-delay:calc(var(--n,0)*90ms)}",
        ".ft-gua-sym{font-size:30px;line-height:1.15;letter-spacing:.06em}",
        ".ft-gua-name{font-size:12px;color:var(--dsw-alias-label-primary);margin-top:3px}",
        ".ft-gua-tag{font-size:10px;color:var(--dsw-alias-label-tertiary);margin-top:2px}",
        ".ft-ben{border-color:var(--dsw-alias-brand-primary)}",
        // 称骨
        ".ft-w-row{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}",
        ".ft-w-chip{flex:1;min-width:86px;text-align:center;border:1px solid var(--dsw-alias-border-l2);",
        "border-radius:10px;padding:7px 4px;background:var(--dsw-alias-bg-base);",
        "animation:ft-pop .2s cubic-bezier(.34,1.56,.64,1) both;",
        "animation-delay:calc(var(--n,0)*80ms)}",
        ".ft-w-k{font-size:10.5px;color:var(--dsw-alias-label-tertiary)}",
        ".ft-w-v{font-size:13px;color:var(--dsw-alias-label-primary);margin-top:2px}",
        ".ft-total{text-align:center;margin-top:12px}",
        ".ft-total-v{font-size:30px;font-weight:700;color:var(--dsw-alias-brand-primary);",
        "display:inline-block;animation:ft-total .45s cubic-bezier(.34,1.56,.64,1) both}",
        "@keyframes ft-total{0%{transform:scale(.5);opacity:0}100%{transform:scale(1);opacity:1}}",
        ".ft-verdict{margin-top:10px;border-left:3px solid var(--dsw-alias-brand-primary);",
        "padding:6px 10px;background:var(--dsw-alias-bg-layer-2);border-radius:0 8px 8px 0;",
        "font-size:12px;color:var(--dsw-alias-label-secondary);line-height:1.7}",
        // 小六壬
        ".ft-path{display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-top:8px;font-size:12px}",
        ".ft-step{display:flex;align-items:center;gap:6px;animation:ft-pop .2s both;",
        "animation-delay:calc(var(--n,0)*80ms)}",
        ".ft-arrow{color:var(--dsw-alias-label-tertiary)}",
        ".ft-palace{margin-top:10px;text-align:center;border:1px solid var(--dsw-alias-brand-primary);",
        "border-radius:12px;padding:12px;background:var(--dsw-alias-bg-base);",
        "animation:ft-bloom .4s cubic-bezier(.22,1,.36,1) both}",
        ".ft-palace-n{font-size:24px;font-weight:700;color:var(--dsw-alias-brand-primary)}",
        // 文本回退
        ".ft-details{margin-top:6px}",
        ".ft-details>summary{font-size:11px;color:var(--dsw-alias-label-tertiary);cursor:pointer}",
        ".ft-out{font-family:inherit;font-size:12px;color:var(--dsw-alias-label-secondary);",
        "white-space:pre-wrap;word-break:break-word;max-height:220px;overflow:auto;",
        "margin:6px 0 0;padding:6px 8px;border-radius:6px;",
        "background:var(--dsw-alias-bg-layer-2)}",
        "@media (prefers-reduced-motion: reduce){",
        ".ft-node,.ft-pillar,.ft-gua-card,.ft-yao,.ft-w-chip,.ft-step,.ft-palace,",
        ".ft-pill,.ft-chip,.ft-total-v,.ft-pal,.ft-glyph-yang,.ft-glyph-yin>i,.ft-bar>i{animation:none}",
        ".ft-bar>i{transition:none}.ft-pal{opacity:1}}",
      ].join("");

      let styleInjected = false;
      function ensureStyle() {
        if (styleInjected || typeof document === "undefined") return;
        styleInjected = true;
        const el = document.createElement("style");
        el.textContent = STYLE_TEXT;
        document.head.appendChild(el);
      }

      // ------------------------------------------------------------------
      // 公共件
      // ------------------------------------------------------------------
      const settledMeta = (block) =>
        (block && block.kind === "tool-result" && block.meta) ? block.meta : null;
      const isSettled = (block) => !!block && block.kind === "tool-result";

      function ContentText({ block, max = 4000 }) {
        const text = (block?.content ?? [])
          .filter((b) => b && b.type === "text")
          .map((b) => b.text ?? "")
          .join("");
        if (!text) return null;
        const shown = text.length > max ? `${text.slice(0, max)}\n…（已截断）` : text;
        return h("details", { className: "ft-details", open: text.length < 500 },
          h("summary", null, `输出（${text.length} 字符）`),
          h("pre", { className: "ft-out" }, shown));
      }

      function ToolRow({ block, title, pill, children }) {
        ensureStyle();
        return h("div", { className: "ft-node", style: { "--n": 0 } },
          h("div", { className: "ft-head" },
            h("span", { className: "ft-title" }, title),
            pill,
            !isSettled(block)
              ? h("span", { className: "ft-pill ft-run" }, "执行中…") : null),
          children,
          h(ContentText, { block }));
      }

      const metaData = (block) => {
        const m = settledMeta(block);
        return m && m.ok ? m.data : null;
      };

      // ------------------------------------------------------------------
      // 八字视图
      // ------------------------------------------------------------------
      function BaziView({ block }) {
        ensureStyle();
        const d = metaData(block);
        if (!d) return h(ToolRow, { block, title: "八字排盘" });
        const c = d.chart ?? {};
        const st = d.strength ?? {};
        const ys = d.yongshen ?? {};
        const wxMax = Math.max(0.01, ...Object.values(st.scores ?? {}));
        const WX = ["木", "火", "土", "金", "水"];
        const pills = [];
        if (c.solar_used) pills.push(h("span", { className: "ft-pill" }, `排盘 ${c.solar_used}`));
        if (c.steps && c.steps.some((s) => String(s).includes("真太阳时"))) {
          pills.push(h("span", { className: "ft-pill" }, "真太阳时"));
        }
        if (c.dayun && c.dayun.length) {
          pills.push(h("span", { className: "ft-pill" },
            `大运${c.yun_forward ? "顺行" : "逆行"} · 起运 ${c.yun_start_solar}（虚岁${c.yun_start_age}）`));
        }
        const relations = (d.relations ?? []).map((r) => r.name);
        const relText = relations.length
          ? `${relations.length} 项：${[...new Set(relations)].join("、")}` : "无";
        const shenshaHits = (d.shensha ?? []).filter((s) => s.positions && s.positions.length);
        return h("div", { className: "ft-node", style: { "--n": 0 } },
          h("div", { className: "ft-head" },
            h("span", { className: "ft-title" }, "八字排盘"),
            pills,
            !isSettled(block)
              ? h("span", { className: "ft-pill ft-run" }, "执行中…") : null),
          h("div", { className: "ft-pillars" },
            (c.pillars ?? []).map((p, i) => h("div", {
              key: p.name, className: `ft-pillar${i === 2 ? " ft-day" : ""}`,
              style: { "--n": i },
            },
              h("div", { className: "ft-pname" }, p.name + (i === 2 ? "（日主）" : "")),
              h("div", { className: "ft-gz" }, p.gan_zhi),
              h("div", { className: "ft-sub" },
                `${p.wu_xing} · ${p.na_yin} · ${p.shi_shen_gan}`),
              h("div", { className: "ft-hide" },
                (p.hide_gan ?? []).map((g, k) => `${g}(${p.shi_shen_zhi?.[k] ?? ""})`).join(" ")),
              h("div", { className: "ft-sub" }, `${p.di_shi} · 旬空${p.xun_kong}`)))),
          h("div", { className: "ft-sec" },
            h("div", { className: "ft-sec-h" },
              `五行旺衰（月令${st.month_wx ?? "?"}·${st.level ?? "?"}）`),
            WX.map((w, i) => h("div", { key: w, className: "ft-bar-row", style: { "--n": i } },
              h("span", { className: "ft-bar-l" }, w),
              h("div", { className: "ft-bar" },
                h("i", { style: { width: `${Math.max(3, ((st.scores?.[w] ?? 0) / wxMax) * 100)}%`,
                                 opacity: `${1 - i * 0.12}` } })),
              h("span", { className: "ft-bar-v" }, `${(st.scores?.[w] ?? 0).toFixed(2)}`)))),
          c.dayun && c.dayun.length
            ? h("div", { className: "ft-sec" },
                h("div", { className: "ft-sec-h" }, "大运"),
                h("div", { className: "ft-chips" },
                  c.dayun.map((d2, i) => h("span", {
                    key: i, className: "ft-chip",
                    style: { animationDelay: `${i * 50}ms` },
                  }, `${d2.gan_zhi} ${d2.start_age}-${d2.end_age}岁`))))
            : null,
          h("div", { className: "ft-sec" },
            h("div", { className: "ft-sec-h" }, `合冲刑害：${relText}`),
            h("div", { className: "ft-chips" },
              (d.relations ?? []).map((r, i) => h("span", {
                key: i, className: "ft-chip",
              }, `${r.name} ${(r.positions ?? []).join("/")}`)))),
          shenshaHits.length
            ? h("div", { className: "ft-sec" },
                h("div", { className: "ft-sec-h" }, "神煞"),
                h("div", { className: "ft-chips" },
                  shenshaHits.slice(0, 14).map((s, i) => h("span", {
                    key: i, className: "ft-chip",
                    title: s.note ?? "",
                  }, `${s.name}→${s.positions.join("/")}`))))
            : null,
          ys.school
            ? h("div", { className: "ft-sec" },
                h("div", { className: "ft-sec-h" }, `用神（${ys.school}）`),
                h("div", { className: "ft-chips" },
                  h("span", { className: "ft-pill ft-ok" },
                    `用 ${(ys.yong_wuxing ?? []).join("、") || "—"}`),
                  ys.ji_wuxing && ys.ji_wuxing.length
                    ? h("span", { className: "ft-pill ft-warn" },
                        `忌 ${ys.ji_wuxing.join("、")}`) : null))
            : null,
          h(ContentText, { block }));
      }

      // ------------------------------------------------------------------
      // 紫微视图：十二宫盘（SVG，逐宫绽放）
      // ------------------------------------------------------------------
      const BR = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"];
      function ZiweiView({ block }) {
        ensureStyle();
        const d = metaData(block);
        if (!d) return h(ToolRow, { block, title: "紫微斗数排盘" });
        const palaces = d.palaces ?? [];
        if (!palaces.length) return h(ToolRow, { block, title: "紫微斗数排盘" });
        const cx = 250, cy = 250;
        const R1 = 108, R2 = 152, R3 = 196;
        const pt = (i, r) => {
          const a = Math.PI * (270 - i * 30) / 180;
          return [cx + r * Math.cos(a), cy - r * Math.sin(a)];
        };
        const a1 = (i, off) => Math.PI * (270 - i * 30 + off) / 180;
        const line = (i, off) => {
          const a = a1(i, off);
          return `${cx + R1 * Math.cos(a)},${cy - R1 * Math.sin(a)} ${cx + R3 * Math.cos(a)},${cy - R3 * Math.sin(a)}`;
        };
        return h("div", { className: "ft-node", style: { "--n": 0 } },
          h("div", { className: "ft-head" },
            h("span", { className: "ft-title" }, "紫微斗数排盘"),
            h("span", { className: "ft-pill" }, d.five_elements_class ?? ""),
            h("span", { className: "ft-pill" }, `命主 ${d.ming_zhu ?? "?"}`),
            h("span", { className: "ft-pill" }, `身主 ${d.shen_zhu ?? "?"}`),
            h("span", { className: "ft-caption" }, d.solar_used ?? ""),
            !isSettled(block)
              ? h("span", { className: "ft-pill ft-run" }, "执行中…") : null),
          h("div", { className: "ft-zw" },
            h("svg", { viewBox: "0 0 500 500", width: 460, role: "img",
              "aria-label": "紫微斗数十二宫盘" },
              h("circle", { cx, cy, r: R1, className: "ft-ring" }),
              h("circle", { cx, cy, r: R2, className: "ft-ring" }),
              h("circle", { cx, cy, r: R3, className: "ft-ring" }),
              Array.from({ length: 12 }, (_, i) => {
                const x1y1 = line(i, 15).split(" ");
                return h("line", {
                  key: `sep${i}`,
                  x1: x1y1[0].split(",")[0], y1: x1y1[0].split(",")[1],
                  x2: x1y1[1].split(",")[0], y2: x1y1[1].split(",")[1],
                  className: "ft-sep",
                });
              }),
              palaces.map((p, i) => {
                const [mx, my] = pt(i, (R1 + R2) / 2);
                const [sx, sy] = pt(i, (R2 + R3) / 2);
                const tag = p.is_ming ? "命" : p.is_shen ? "身"
                  : p.is_laiyin ? "因" : "";
                const starSpans = [];
                const seen = {};
                (p.major ?? []).forEach(([n, b, mut]) => {
                  seen[n] = true;
                  starSpans.push(h("tspan", {
                    key: n, className: `ft-star ${mut ? "ft-star4 ft-mut" : ""}`,
                    fill: mut
                      ? (mut === "忌" ? "var(--dsw-alias-state-error-primary)"
                         : mut === "禄" ? "var(--dsw-alias-state-success-primary)"
                         : mut === "科" ? "var(--dsw-alias-state-warn-primary)"
                         : "var(--dsw-alias-brand-primary)")
                      : "var(--dsw-alias-label-primary)",
                  }, mut ? `${n}·${mut}` : n, " "));
                });
                [...(p.minor ?? []), ...(p.adjective ?? [])].slice(0, 5)
                  .forEach((n) => starSpans.push(h("tspan", {
                    key: `x${n}`, className: "ft-star",
                    fill: "var(--dsw-alias-label-secondary)",
                  }, n, " ")));
                return h("g", {
                  key: p.name, className: `ft-pal${p.is_ming ? " ft-zw-ming" : ""}`,
                  style: { "--i": i },
                },
                  h("text", {
                    x: mx, y: my - 12, textAnchor: "middle",
                    fill: "var(--dsw-alias-label-primary)", fontSize: 13,
                    fontWeight: p.is_ming ? 700 : 400,
                  }, `${p.name}${tag ? `(${tag})` : ""}`),
                  h("text", {
                    x: mx, y: my + 4, textAnchor: "middle",
                    fill: "var(--dsw-alias-brand-primary)", fontSize: 10.5,
                  }, p.gan_zhi ?? ""),
                  h("text", {
                    x: mx, y: my + 17, textAnchor: "middle",
                    fill: "var(--dsw-alias-label-tertiary)", fontSize: 9,
                  }, p.da_xian ? `${p.da_xian}岁` : ""),
                  h("text", {
                    x: sx, y: sy + 3, textAnchor: "middle", fontSize: 10,
                  }, starSpans));
              }))),
          d.patterns && d.patterns.length
            ? h("div", { className: "ft-sec" },
                h("div", { className: "ft-sec-h" }, "格局（iztro 64 格局库）"),
                h("div", { className: "ft-chips" },
                  d.patterns.map((p, i) => h("span", {
                    key: i, className: `ft-chip${String(p).includes("[破格]") ? " ft-warn" : ""}`,
                  }, p))))
            : null,
          h(ContentText, { block, max: 1500 }));
      }

      // ------------------------------------------------------------------
      // 六爻视图：爻线逐爻描画
      // ------------------------------------------------------------------
      function LiuyaoView({ block }) {
        ensureStyle();
        const d = metaData(block);
        if (!d) return h(ToolRow, { block, title: "六爻起卦装卦" });
        const lines = d.lines ?? [];
        return h("div", { className: "ft-node", style: { "--n": 0 } },
          h("div", { className: "ft-head" },
            h("span", { className: "ft-title" }, "六爻起卦"),
            h("span", { className: "ft-pill ft-ok" }, `本卦 ${d.ben_gua}`),
            h("span", { className: "ft-pill" }, `变卦 ${d.bian_gua}`),
            h("span", { className: "ft-pill" }, `${d.palace}宫${d.palace_wuxing}`),
            h("span", { className: "ft-pill" }, `世${d.shi} 应${d.ying}`),
            h("span", { className: "ft-pill" },
              `月建${d.month_zhi} 日辰${d.day_ganzhi} 旬空${(d.xun_kong ?? []).join("")}`),
            !isSettled(block)
              ? h("span", { className: "ft-pill ft-run" }, "执行中…") : null),
          h("div", { className: "ft-yaos" },
            [...lines].reverse().map((l, i) => h("div", {
              key: l.no, className: "ft-yao", style: { "--n": i },
            },
              h("span", { className: "ft-yao-idx" }, `${l.no}爻`),
              h("span", {
                className: `ft-yao-mark${l.is_moving ? " ft-mov" : ""}`,
                "aria-label": l.is_moving ? "动爻" : "",
              }, l.is_moving ? (l.value === 9 ? "○" : "×") : ""),
              h("div", { className: "ft-yao-glyph", style: { "--n": i } },
                (l.value === 7 || l.value === 9)
                  ? h("div", { className: "ft-glyph-yang" })
                  : h("div", { className: "ft-glyph-yin" },
                      h("i", null), h("i", null))),
              h("div", { className: "ft-yao-chips" },
                (l.no === d.shi ? h("span", { className: "ft-tag" }, "世") : null),
                (l.no === d.ying ? h("span", { className: "ft-tag" }, "应") : null),
                h("span", { className: "ft-chip" }, l.gan_zhi),
                h("span", { className: "ft-chip" }, l.liu_qin),
                h("span", { className: "ft-chip" }, l.liu_shen))))),
          h(ContentText, { block }));
      }

      // ------------------------------------------------------------------
      // 梅花视图
      // ------------------------------------------------------------------
      const GUA_SYM = { 乾: "☰", 兑: "☱", 离: "☲", 震: "☳",
                       巽: "☴", 坎: "☵", 艮: "☶", 坤: "☷" };
      function MeihuaView({ block }) {
        ensureStyle();
        const d = metaData(block);
        if (!d) return h(ToolRow, { block, title: "梅花易数" });
        const sym = (up, lo) => `${GUA_SYM[up] ?? ""}${GUA_SYM[lo] ?? ""}`;
        const good = d.relation === "用生体" || d.relation === "比和";
        const bad = d.relation === "用克体";
        return h("div", { className: "ft-node", style: { "--n": 0 } },
          h("div", { className: "ft-head" },
            h("span", { className: "ft-title" }, "梅花易数"),
            h("span", { className: "ft-caption" }, d.method ?? ""),
            !isSettled(block)
              ? h("span", { className: "ft-pill ft-run" }, "执行中…") : null),
          h("div", { className: "ft-gua-row" },
            h("div", { className: "ft-gua-card ft-ben", style: { "--n": 0 } },
              h("div", { className: "ft-gua-sym" }, sym(d.upper, d.lower)),
              h("div", { className: "ft-gua-name" }, d.ben_gua),
              h("div", { className: "ft-gua-tag" }, `动爻 第${d.moving_line}爻`)),
            h("div", { className: "ft-gua-card", style: { "--n": 1 } },
              h("div", { className: "ft-gua-sym" },
                sym(d.hu_upper, d.hu_lower)),
              h("div", { className: "ft-gua-name" }, d.hu_gua),
              h("div", { className: "ft-gua-tag" }, "互卦")),
            h("div", { className: "ft-gua-card", style: { "--n": 2 } },
              h("div", { className: "ft-gua-sym" },
                sym(d.bian_upper, d.bian_lower)),
              h("div", { className: "ft-gua-name" }, d.bian_gua),
              h("div", { className: "ft-gua-tag" }, "变卦"))),
          h("div", { className: "ft-chips" },
            h("span", { className: "ft-pill" },
              `体卦 ${d.ti_gua}${d.wuxing ? `（${d.wuxing.ti}）` : ""}`),
            h("span", { className: "ft-pill" },
              `用卦 ${d.yong_gua}${d.wuxing ? `（${d.wuxing.yong}）` : ""}`),
            h("span", {
              className: `ft-pill ${good ? "ft-ok" : bad ? "ft-fail" : "ft-warn"}`,
            }, d.relation)),
          d.verdict
            ? h("div", { className: "ft-verdict" }, d.verdict)
            : null,
          h(ContentText, { block, max: 1200 }));
      }

      // ------------------------------------------------------------------
      // 称骨视图
      // ------------------------------------------------------------------
      const CN = "零一二三四五六七八九";
      const qianStr = (q) => {
        const l = Math.floor(q / 10), r = q % 10;
        if (!l) return `${CN[r]}钱`;
        if (!r) return `${CN[l]}两`;
        return `${CN[l]}两${CN[r]}钱`;
      };
      function ChengguView({ block }) {
        ensureStyle();
        const d = metaData(block);
        if (!d) return h(ToolRow, { block, title: "袁天罡称骨" });
        const items = [
          [`年（${d.year_gz}）`, d.year_qian],
          [`月（农历${d.lunar_month}月）`, d.month_qian],
          [`日（农历${d.lunar_day}）`, d.day_qian],
          [`时（${d.hour_zhi}时）`, d.hour_qian],
        ];
        return h("div", { className: "ft-node", style: { "--n": 0 } },
          h("div", { className: "ft-head" },
            h("span", { className: "ft-title" }, "袁天罡称骨"),
            h("span", { className: "ft-caption" }, "通行男命版 · 仅作文化参考"),
            !isSettled(block)
              ? h("span", { className: "ft-pill ft-run" }, "执行中…") : null),
          h("div", { className: "ft-w-row" },
            items.map(([k, v], i) => h("div", {
              key: k, className: "ft-w-chip", style: { "--n": i },
            },
              h("div", { className: "ft-w-k" }, k),
              h("div", { className: "ft-w-v" }, qianStr(v))))),
          d.total_qian != null
            ? h("div", { className: "ft-total" },
                h("span", { className: "ft-total-v" }, qianStr(d.total_qian)),
                h("div", { className: "ft-caption" }, "总骨重"))
            : null,
          d.verdict
            ? h("div", { className: "ft-verdict" }, d.verdict)
            : null,
          h(ContentText, { block, max: 1200 }));
      }

      // ------------------------------------------------------------------
      // 小六壬视图
      // ------------------------------------------------------------------
      function XiaoliurenView({ block }) {
        ensureStyle();
        const d = metaData(block);
        if (!d) return h(ToolRow, { block, title: "小六壬" });
        const info = d.info ?? {};
        const steps = [
          `月 ${d.lunar_month}`, d.month_palace,
          `日 ${d.lunar_day}`, d.day_palace,
          `时 ${d.hour_zhi}`, d.palace,
        ];
        const good = String(info["吉凶"] ?? "").includes("吉") && !String(info["吉凶"] ?? "").includes("凶");
        return h("div", { className: "ft-node", style: { "--n": 0 } },
          h("div", { className: "ft-head" },
            h("span", { className: "ft-title" }, "小六壬"),
            h("span", { className: "ft-caption" },
              `农历${d.lunar_month}月${d.lunar_day}日 ${d.hour_zhi}时`),
            !isSettled(block)
              ? h("span", { className: "ft-pill ft-run" }, "执行中…") : null),
          h("div", { className: "ft-path" },
            steps.map((s, i) => (i % 2 === 1)
              ? h("span", {
                  key: i, className: `ft-step ft-pill ${i === 5
                    ? (good ? "ft-ok" : "ft-warn") : ""}`,
                  style: { "--n": i },
                }, s)
              : h("span", { key: i, className: "ft-step", style: { "--n": i } },
                  h("span", { className: "ft-caption" }, s)))),
          h("div", { className: "ft-palace" },
            h("div", { className: "ft-palace-n" }, d.palace),
            h("div", { className: "ft-meta", style: { justifyContent: "center" } },
              h("span", { className: `ft-pill ${good ? "ft-ok" : "ft-warn"}` }, info["吉凶"] ?? ""),
              info["五行"] ? h("span", { className: "ft-pill" }, `五行 ${info["五行"]}`) : null,
              info["方位"] ? h("span", { className: "ft-pill" }, info["方位"]) : null,
              info["神煞"] ? h("span", { className: "ft-pill" }, info["神煞"]) : null,
              info["主数"] ? h("span", { className: "ft-pill" }, `主数 ${info["主数"]}`) : null)),
          info["断语"]
            ? h("div", { className: "ft-verdict" }, info["断语"])
            : null,
          h(ContentText, { block, max: 1200 }));
      }

      // ------------------------------------------------------------------
      // 历法速查视图
      // ------------------------------------------------------------------
      function SolarInfoView({ block }) {
        ensureStyle();
        const d = metaData(block);
        if (!d) return h(ToolRow, { block, title: "历法速查" });
        const rows = [
          ["公历", d.solar],
          ["农历", `${d.lunarYear}年${d.lunarLeap ? "闰" : ""}${d.lunarMonth}月${d.lunarDay}日`],
          ["年干支", `${d.yearGanzhi}年 · 生肖${d.shengxiao}`],
        ];
        return h("div", { className: "ft-node", style: { "--n": 0 } },
          h("div", { className: "ft-head" },
            h("span", { className: "ft-title" }, "历法速查"),
            !isSettled(block)
              ? h("span", { className: "ft-pill ft-run" }, "执行中…") : null),
          rows.map(([k, v], i) => h("div", { key: k, className: "ft-meta" },
            h("span", { className: "ft-caption", style: { width: 44, flex: "none" } }, k),
            h("span", { className: "ft-pill" }, v))),
          h("div", { className: "ft-chips" },
            (d.pillars ?? []).map((p, i) => h("span", {
              key: i, className: `ft-chip${i === 2 ? " ft-ok" : ""}`,
            }, p))),
          d.jieqi && d.jieqi.length
            ? h("div", { className: "ft-sec" },
                h("div", { className: "ft-sec-h" }, "节气（前 8 个）"),
                h("div", { className: "ft-chips" },
                  d.jieqi.slice(0, 8).map((j, i) => h("span", {
                    key: i, className: "ft-chip",
                  }, `${j.name} ${j.time}`))))
            : null,
          h(ContentText, { block, max: 800 }));
      }

      const TOOLVIEWS = {
        fortune_bazi: BaziView,
        fortune_ziwei: ZiweiView,
        fortune_liuyao: LiuyaoView,
        fortune_meihua: MeihuaView,
        fortune_chenggu: ChengguView,
        fortune_xiaoliuren: XiaoliurenView,
        fortune_solar_info: SolarInfoView,
      };

      const inject = ["slots"];

      function apply(ctx) {
        for (const [toolName, comp] of Object.entries(TOOLVIEWS)) {
          ctx.slots.inject("tool.call.toolview", () => ctx.slots.register({
            name: "tool.call.toolview",
            key: toolName,
          }, comp));
        }
      }

      exports.apply = apply;
      exports.inject = inject;
      exports.TOOLVIEWS = TOOLVIEWS;
      return module.exports;
    },
  });
})();
