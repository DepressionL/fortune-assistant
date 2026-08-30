// dsh-fortune-client：Web 客户端插件（fortune_* 七工具按 wire tool name 注册
// toolview 行渲染）。v0.2 起全盘可交互：
// - 紫微：点宫位 → 星曜详情面板（亮度释义/四化/大限/长生），悬停高亮对宫；
// - 八字：页签（四柱/五行/大运/神煞/关系/用神），点四柱卡看藏干十神详情；
// - 六爻：点爻 → 六亲/六神释义面板，动爻脉冲；
// - 梅花：点卦卡 → 上下卦爻位/先天数/五行详情；
// - 小六壬：「逐步推演」重播月→日→时；称骨：「重播动效」。
// 设计约束不变：settled 数据源 = block.meta（presentationMeta 投影）；
// 零颜色字面量（--dsw-alias-* token，暗色自适应）；prefers-reduced-motion
// 全量降级；按钮/页签键盘可达（focus-visible + aria-pressed/expanded）。
(function () {
  "use strict";
  if (typeof window === "undefined") return;   // 仅浏览器装配

  window.__ModuleLoader__.load({
    id: "dsh-fortune-client",
    factory: (require) => {
      const module = { exports: {} };
      const exports = module.exports;
      Object.defineProperty(exports, Symbol.toStringTag, { value: "Module" });
      const react = require("react");
      const h = react.createElement;
      const { useState, useEffect, useRef } = react;

      // ------------------------------------------------------------------
      // 样式：语义 token + 入场/脉冲/描画/生长动效 + 交互态（页签/面板/悬停）
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
        // 页签（八字）
        ".ft-tabs{display:flex;gap:4px;flex-wrap:wrap;margin-top:8px}",
        ".ft-tab{font:inherit;font-size:11.5px;line-height:20px;padding:1px 10px;",
        "border-radius:8px;border:1px solid var(--dsw-alias-border-l2);",
        "color:var(--dsw-alias-label-secondary);background:var(--dsw-alias-bg-base);",
        "cursor:pointer;transition:background .15s ease}",
        ".ft-tab:hover{background:var(--dsw-alias-interactive-bg-hover)}",
        ".ft-tab[aria-selected=true]{color:var(--dsw-alias-brand-primary);",
        "border-color:var(--dsw-alias-brand-primary);",
        "background:var(--dsw-alias-interactive-bg-active)}",
        // 详情面板
        ".ft-panel{margin-top:8px;border:1px solid var(--dsw-alias-border-l2);",
        "border-radius:10px;padding:8px 10px;background:var(--dsw-alias-bg-base);",
        "animation:ft-rise .22s ease-out both}",
        ".ft-panel-h{font-size:12px;font-weight:600;color:var(--dsw-alias-brand-primary);",
        "display:flex;align-items:center;gap:6px;flex-wrap:wrap}",
        ".ft-panel-row{display:flex;gap:10px;flex-wrap:wrap;margin-top:5px;font-size:11.5px;",
        "color:var(--dsw-alias-label-secondary)}",
        ".ft-legend{font-size:10.5px;color:var(--dsw-alias-label-tertiary);margin-top:5px}",
        // 四柱
        ".ft-pillars{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:8px}",
        ".ft-pillar{border:1px solid var(--dsw-alias-border-l2);border-radius:10px;",
        "padding:8px 6px;text-align:center;background:var(--dsw-alias-bg-base);",
        "cursor:pointer;transition:transform .15s ease,border-color .15s ease;",
        "animation:ft-rise .3s cubic-bezier(.22,1,.36,1) both;",
        "animation-delay:calc(var(--n,0)*80ms + 60ms)}",
        ".ft-pillar:hover{transform:translateY(-2px)}",
        ".ft-pillar.ft-sel,.ft-pillar.ft-day{border-color:var(--dsw-alias-brand-primary);",
        "box-shadow:0 0 0 1px var(--dsw-alias-brand-primary)}",
        ".ft-pillar:focus-visible{outline:2px solid var(--dsw-alias-brand-primary);outline-offset:1px}",
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
        // 紫微盘（传统 4×4 宫格布局：外围 12 宫 + 中央摘要；正文排版，不溢出不糊）
        ".ft-zw-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));",
        "gap:5px;margin-top:8px}",
        ".ft-zw-cell{border:1px solid var(--dsw-alias-border-l2);border-radius:10px;",
        "padding:8px 8px;min-height:100px;background:var(--dsw-alias-bg-base);cursor:pointer;",
        "text-align:center;transition:border-color .15s ease,box-shadow .15s ease;",
        "animation:ft-rise .3s ease-out both;animation-delay:calc(var(--i,0)*55ms)}",
        ".ft-zw-cell:hover{border-color:var(--dsw-alias-state-warn-secondary)}",
        ".ft-zw-cell:focus-visible{outline:2px solid var(--dsw-alias-brand-primary);outline-offset:1px}",
        // 选中：品牌边框 + 光晕呼吸脉冲（与命宫的静态身份框区分）
        "@keyframes ft-glow-sel{0%,100%{box-shadow:0 0 0 2px var(--dsw-alias-brand-primary)}",
        "50%{box-shadow:0 0 0 2px var(--dsw-alias-brand-primary),",
        "0 0 12px 2px var(--dsw-alias-brand-primary)}}",
        ".ft-zw-cell.ft-sel{border-color:var(--dsw-alias-brand-primary);",
        "animation:ft-rise .3s ease-out both,ft-glow-sel 1.8s ease-in-out .4s infinite}",
        // 悬停对宫：琥珀虚线 + 边框色柔呼吸（不改文字亮度）
        "@keyframes ft-dash-h{0%,100%{border-color:var(--dsw-alias-state-warn-secondary)}",
        "50%{border-color:var(--dsw-alias-state-warn-primary)}}",
        ".ft-zw-cell.ft-opp-h{border-style:dashed;border-color:var(--dsw-alias-state-warn-secondary);",
        "animation:ft-rise .3s ease-out both,ft-dash-h 1.5s ease-in-out infinite}",
        // 点选对宫：品牌虚线 + 光晕脉冲（更强的确认态）
        ".ft-zw-cell.ft-opp-s{border-style:dashed;border-color:var(--dsw-alias-brand-primary);",
        "animation:ft-rise .3s ease-out both,ft-glow-sel 1.8s ease-in-out .4s infinite}",
        // 命宫：品牌边框 + 底色 + 宫名着色（静态身份，不参与动效竞争）
        ".ft-zw-cell.ft-ming{background:var(--dsw-alias-bg-layer-2)}",
        ".ft-zw-cell.ft-ming .ft-zw-name{color:var(--dsw-alias-brand-primary)}",
        ".ft-zw-head{display:flex;align-items:baseline;justify-content:center;gap:4px;flex-wrap:wrap}",
        ".ft-zw-name{font-size:12.5px;font-weight:600;color:var(--dsw-alias-label-primary)}",
        ".ft-zw-mingtag{font-size:9px;line-height:14px;padding:0 4px;border-radius:6px;",
        "border:1px solid var(--dsw-alias-brand-primary);color:var(--dsw-alias-brand-primary);",
        "animation:ft-breathe 2.4s ease-in-out infinite}",
        ".ft-zw-tag{font-size:9px;line-height:14px;padding:0 4px;border-radius:6px;",
        "border:1px solid var(--dsw-alias-border-l2);color:var(--dsw-alias-label-tertiary)}",
        ".ft-zw-gz{font-size:10px;color:var(--dsw-alias-label-tertiary)}",
        ".ft-zw-stars{margin-top:4px;display:flex;flex-direction:column;gap:2px}",
        ".ft-zw-star{font-size:11.5px;line-height:1.5;white-space:nowrap;overflow:hidden;",
        "text-overflow:ellipsis}",
        ".ft-zw-star.ft-main{font-weight:600}",
        ".ft-zw-b{font-size:9.5px;margin-left:2px}",
        ".ft-zb-miao{color:var(--dsw-alias-state-success-primary)}",
        ".ft-zb-wang{color:var(--dsw-alias-brand-primary)}",
        ".ft-zb-de{color:var(--dsw-alias-state-warn-primary)}",
        ".ft-zb-li{color:var(--dsw-alias-state-warn-primary)}",
        ".ft-zb-ping{color:var(--dsw-alias-label-tertiary)}",
        ".ft-zb-ruo{color:var(--dsw-alias-label-tertiary);opacity:.65}",
        ".ft-mut-lu{color:var(--dsw-alias-state-success-primary)}",
        ".ft-mut-quan{color:var(--dsw-alias-brand-primary)}",
        ".ft-mut-ke{color:var(--dsw-alias-state-warn-primary)}",
        ".ft-mut-ji{color:var(--dsw-alias-state-error-primary)}",
        ".ft-zw-minor{margin-top:3px;font-size:9.5px;line-height:1.55;",
        "color:var(--dsw-alias-label-tertiary);word-break:break-all}",
        ".ft-zw-foot{margin-top:4px;font-size:9.5px;color:var(--dsw-alias-label-tertiary)}",
        ".ft-zw-center{grid-area:2/2/4/4;border:1px dashed var(--dsw-alias-border-l2);",
        "border-radius:10px;padding:10px;background:var(--dsw-alias-bg-layer-2);",
        "display:flex;flex-direction:column;justify-content:center;gap:4px;text-align:center}",
        ".ft-zw-center-t{font-size:13px;font-weight:600;color:var(--dsw-alias-brand-primary)}",
        ".ft-zw-center-m{font-size:10.5px;color:var(--dsw-alias-label-secondary);line-height:1.6}",
        ".ft-zw-center-l{font-size:9.5px;color:var(--dsw-alias-label-tertiary);line-height:1.6}",
        // 六爻
        ".ft-yaos{margin-top:8px;border:1px solid var(--dsw-alias-border-l2);",
        "border-radius:10px;padding:6px 10px;background:var(--dsw-alias-bg-base)}",
        ".ft-yao{display:flex;align-items:center;gap:10px;padding:5px 6px;",
        "border-radius:8px;cursor:pointer;transition:background .15s ease;",
        "animation:ft-rise .25s ease-out both;animation-delay:calc(var(--n,0)*60ms)}",
        ".ft-yao:hover{background:var(--dsw-alias-interactive-bg-hover)}",
        ".ft-yao.ft-sel{background:var(--dsw-alias-interactive-bg-active);",
        "outline:1px solid var(--dsw-alias-brand-primary)}",
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
        "background:var(--dsw-alias-bg-base);cursor:pointer;",
        "transition:transform .15s ease,border-color .15s ease;",
        "animation:ft-rise .3s cubic-bezier(.22,1,.36,1) both;",
        "animation-delay:calc(var(--n,0)*90ms)}",
        ".ft-gua-card:hover{transform:translateY(-2px)}",
        ".ft-gua-card.ft-sel,.ft-ben{border-color:var(--dsw-alias-brand-primary)}",
        ".ft-gua-card:focus-visible{outline:2px solid var(--dsw-alias-brand-primary);outline-offset:1px}",
        ".ft-gua-sym{font-size:30px;line-height:1.15;letter-spacing:.06em}",
        ".ft-gua-name{font-size:12px;color:var(--dsw-alias-label-primary);margin-top:3px}",
        ".ft-gua-tag{font-size:10px;color:var(--dsw-alias-label-tertiary);margin-top:2px}",
        // 称骨
        ".ft-w-row{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}",
        ".ft-w-chip{flex:1;min-width:86px;text-align:center;border:1px solid var(--dsw-alias-border-l2);",
        "border-radius:10px;padding:7px 4px;background:var(--dsw-alias-bg-base);cursor:pointer;",
        "transition:border-color .15s ease;",
        "animation:ft-pop .2s cubic-bezier(.34,1.56,.64,1) both;",
        "animation-delay:calc(var(--n,0)*80ms)}",
        ".ft-w-chip.ft-sel,.ft-w-chip:hover{border-color:var(--dsw-alias-brand-primary)}",
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
        ".ft-step.ft-dim{opacity:.35}",
        ".ft-arrow{color:var(--dsw-alias-label-tertiary)}",
        ".ft-palace{margin-top:10px;text-align:center;border:1px solid var(--dsw-alias-brand-primary);",
        "border-radius:12px;padding:12px;background:var(--dsw-alias-bg-base);",
        "animation:ft-bloom .4s cubic-bezier(.22,1,.36,1) both}",
        ".ft-palace-n{font-size:24px;font-weight:700;color:var(--dsw-alias-brand-primary)}",
        // 按钮
        ".ft-btn{font:inherit;font-size:11.5px;line-height:20px;padding:1px 10px;",
        "border-radius:8px;border:1px solid var(--dsw-alias-border-l2);",
        "color:var(--dsw-alias-label-primary);background:var(--dsw-alias-bg-base);",
        "cursor:pointer;transition:background .15s ease}",
        ".ft-btn:hover{background:var(--dsw-alias-interactive-bg-hover)}",
        ".ft-btn:active{background:var(--dsw-alias-interactive-bg-active)}",
        ".ft-btn:focus-visible,.ft-tab:focus-visible{outline:2px solid var(--dsw-alias-brand-primary);",
        "outline-offset:1px}",
        // 文本回退
        ".ft-details{margin-top:6px}",
        ".ft-details>summary{font-size:11px;color:var(--dsw-alias-label-tertiary);cursor:pointer}",
        ".ft-out{font-family:inherit;font-size:12px;color:var(--dsw-alias-label-secondary);",
        "white-space:pre-wrap;word-break:break-word;max-height:220px;overflow:auto;",
        "margin:6px 0 0;padding:6px 8px;border-radius:6px;",
        "background:var(--dsw-alias-bg-layer-2)}",
        // 口径分段器
        ".ft-seg{display:inline-flex;border:1px solid var(--dsw-alias-border-l2);",
        "border-radius:8px;overflow:hidden;margin-top:6px}",
        ".ft-seg>button{font:inherit;font-size:11px;line-height:20px;padding:0 10px;border:0;",
        "background:var(--dsw-alias-bg-base);color:var(--dsw-alias-label-secondary);cursor:pointer}",
        ".ft-seg>button[aria-pressed=true]{background:var(--dsw-alias-interactive-bg-active);",
        "color:var(--dsw-alias-brand-primary)}",
        // 何知章成对条
        ".ft-pair{display:flex;gap:10px;flex-wrap:wrap;margin-top:8px}",
        ".ft-pair-side{flex:1;min-width:220px;border:1px solid var(--dsw-alias-border-l2);",
        "border-radius:10px;padding:8px 10px;background:var(--dsw-alias-bg-base);",
        "animation:ft-rise .25s ease-out both;animation-delay:calc(var(--n,0)*70ms)}",
        ".ft-pair-side.ft-pair-hit{border-color:var(--dsw-alias-state-warn-primary)}",
        ".ft-pair-line{font-size:11px;color:var(--dsw-alias-label-secondary)}",
        ".ft-pair-reason{font-size:10.5px;color:var(--dsw-alias-label-tertiary);",
        "margin-top:4px;line-height:1.6}",
        // 流年时间轴
        ".ft-tl{display:flex;gap:6px;overflow-x:auto;padding:8px 2px;margin-top:8px}",
        ".ft-tl-y{flex:none;min-width:76px;text-align:center;border:1px solid var(--dsw-alias-border-l2);",
        "border-radius:10px;padding:6px 4px;background:var(--dsw-alias-bg-base);cursor:pointer;",
        "transition:border-color .15s ease;animation:ft-pop .2s both;",
        "animation-delay:calc(var(--n,0)*45ms)}",
        ".ft-tl-y.ft-sel{border-color:var(--dsw-alias-brand-primary);",
        "box-shadow:0 0 0 1px var(--dsw-alias-brand-primary)}",
        ".ft-tl-y.ft-hit{border-color:var(--dsw-alias-state-warn-secondary)}",
        ".ft-tl-yr{font-size:9.5px;color:var(--dsw-alias-label-tertiary)}",
        ".ft-tl-gz{font-size:13px;font-weight:600;color:var(--dsw-alias-label-primary);margin-top:2px}",
        ".ft-tl-ss{font-size:10px;color:var(--dsw-alias-label-tertiary);margin-top:2px}",
        // 共识热力矩阵
        ".ft-heat{display:grid;grid-template-columns:minmax(64px,auto) repeat(5,1fr) minmax(64px,auto);",
        "gap:3px;margin-top:8px;font-size:11px}",
        ".ft-heat-c{position:relative;text-align:center;padding:6px 2px;border-radius:6px;",
        "background:var(--dsw-alias-bg-base);border:1px solid var(--dsw-alias-border-l2);",
        "color:var(--dsw-alias-label-secondary);overflow:hidden}",
        ".ft-heat-c.ft-heat-h{color:var(--dsw-alias-label-tertiary)}",
        ".ft-heat-bar{position:absolute;left:0;right:0;bottom:0;",
        "background:var(--dsw-alias-brand-primary);opacity:.18}",
        // 证据链条目卡（展开后结构化渲染 + 逐条错峰入场动效）
        ".ft-ev{margin-top:6px}",
        ".ft-ev-item{display:flex;flex-direction:column;gap:3px;border:1px solid var(--dsw-alias-border-l2);",
        "border-radius:8px;padding:6px 8px;margin:5px 0;background:var(--dsw-alias-bg-layer-1);",
        "animation:ft-rise .24s ease-out both;animation-delay:calc(var(--n,0)*60ms)}",
        ".ft-ev-head{display:flex;align-items:center;gap:6px;flex-wrap:wrap}",
        ".ft-ev-tool{font-size:10px;line-height:16px;padding:0 6px;border-radius:7px;",
        "border:1px solid var(--dsw-alias-brand-primary);color:var(--dsw-alias-brand-primary)}",
        ".ft-ev-tool.ft-ok{color:var(--dsw-alias-state-success-primary);",
        "border-color:var(--dsw-alias-state-success-secondary)}",
        ".ft-ev-tool.ft-warn{color:var(--dsw-alias-state-warn-primary);",
        "border-color:var(--dsw-alias-state-warn-secondary)}",
        ".ft-ev-field{font-size:11px;color:var(--dsw-alias-label-secondary)}",
        ".ft-ev-fact{font-size:11.5px;color:var(--dsw-alias-label-primary);line-height:1.6;white-space:pre-wrap}",
        ".ft-ev-src{font-size:10px;color:var(--dsw-alias-label-tertiary)}",
        "@media (prefers-reduced-motion: reduce){",
        ".ft-node,.ft-pillar,.ft-gua-card,.ft-yao,.ft-w-chip,.ft-step,.ft-palace,",
        ".ft-pill,.ft-chip,.ft-total-v,.ft-zw-cell,.ft-glyph-yang,.ft-glyph-yin>i,.ft-bar>i,",
        ".ft-panel,.ft-ev-item{animation:none}",
        ".ft-bar>i{transition:none}.ft-zw-cell{opacity:1}}",
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

      function TabBar({ tabs, active, onSelect }) {
        return h("div", { className: "ft-tabs", role: "tablist" },
          tabs.map((t) => h("button", {
            key: t.id, type: "button", className: "ft-tab",
            role: "tab", "aria-selected": String(active === t.id),
            onClick: () => onSelect(t.id),
          }, t.label)));
      }

      function DetailPanel({ title, children }) {
        return h("div", { className: "ft-panel", role: "region",
          "aria-label": title },
          h("div", { className: "ft-panel-h" }, title),
          children);
      }

      // ------------------------------------------------------------------
      // 八字视图（页签 + 四柱点选）
      // ------------------------------------------------------------------
      const SHI_SHEN_MEANING = {
        比肩: "同我·同性（兄弟朋友，帮扶竞争）", 劫财: "同我·异性（竞争分夺）",
        食神: "我生·同性（才华口福，温和输出）", 伤官: "我生·异性（锋芒才艺）",
        正财: "我克·异性（稳定钱财、妻）", 偏财: "我克·同性（流动之财、父）",
        正官: "克我·异性（职位、上司、夫）", 七杀: "克我·同性（压力、魄力）",
        正印: "生我·异性（学业、母亲、庇荫）", 偏印: "生我·同性（冷门学识）",
      };
      const WX_ORDER = ["木", "火", "土", "金", "水"];
      // 用神流派显示名（内部键为拼音，UI 一律中文）
      const SCHOOL_LABEL = { wangshuai: "旺衰", tiaohou: "调候", tongguan: "通关",
                             geju: "格局", bingyao: "病药" };
      // 证据链工具徽章色档（语义 token，无颜色字面量）
      const TOOL_PILL = { bazi: "ft-ok", ziwei: "ft-run", liuyao: "ft-warn",
                          meihua: "ft-run", xiaoliuren: "ft-warn", chenggu: "ft-ok",
                          comprehensive: "ft-run", context: "ft-ok" };
      // 证据链工具徽章中文显示名（悬停 title 保留原名）
      const TOOL_LABEL = { bazi: "八字", ziwei: "紫微", liuyao: "六爻", meihua: "梅花",
                           chenggu: "称骨", xiaoliuren: "小六壬",
                           comprehensive: "综合分析", context: "历法上下文" };
      function WuxingPanel({ st }) {
        const max = Math.max(0.01, ...Object.values(st.scores ?? {}));
        return h("div", { className: "ft-sec" },
          h("div", { className: "ft-sec-h" },
            `五行旺衰（月令${st.month_wx ?? "?"}·${st.level ?? "?"}）`),
          WX_ORDER.map((w, i) => h("div", {
            key: w, className: "ft-bar-row", style: { "--n": i },
          },
            h("span", { className: "ft-bar-l" }, w),
            h("div", { className: "ft-bar" },
              h("i", { style: {
                width: `${Math.max(3, ((st.scores?.[w] ?? 0) / max) * 100)}%`,
                opacity: `${1 - i * 0.12}`,
              } })),
            h("span", { className: "ft-bar-v" },
              `${(st.scores?.[w] ?? 0).toFixed(2)}`))),
          h("div", { className: "ft-legend" },
            `权重：月令旺相休囚死 × 藏干加权（经验参数，见 README）。`
            + `日主${st.day_wx ?? "?"}：同类 ${st.same_score?.toFixed?.(2) ?? "?"}`
            + ` / 异类 ${st.diff_score?.toFixed?.(2) ?? "?"}`));
      }
      // 多流派用神（yongshen_all 子页签：旺衰/调候/通关/格局/病药逐派渲染）
      function YongshenMulti({ d }) {
        const all = d && d.yongshen_all && typeof d.yongshen_all === "object"
          ? d.yongshen_all : null;
        const keys = all ? Object.keys(all) : [];
        const [s, setS] = useState(keys[0] ?? "");
        if (!keys.length) return null;
        const ys = all[s] ?? {};
        return h("div", { className: "ft-sec" },
          h("div", { className: "ft-sec-h" }, "用神（多流派对比，规则引擎参考）"),
          h("div", { className: "ft-tabs", role: "tablist" },
            keys.map((k) => h("button", {
              key: k, type: "button", className: "ft-tab", role: "tab",
              "aria-selected": String(s === k), onClick: () => setS(k),
            }, SCHOOL_LABEL[k] ?? k))),
          h("div", { className: "ft-chips" },
            h("span", { className: "ft-pill ft-ok" },
              `用 ${(ys.yong_wuxing ?? []).join("、") || "—"}`),
            ys.ji_wuxing && ys.ji_wuxing.length
              ? h("span", { className: "ft-pill ft-warn" },
                  `忌 ${ys.ji_wuxing.join("、")}`) : null),
          h("div", { className: "ft-legend" },
            (ys.conclusions ?? []).slice(0, 4).map((c2, i) =>
              h("div", { key: i }, c2))),
          h("div", { className: "ft-legend" },
            "各流派结论可能相互矛盾，均为经验规则，并列展示仅供参考。"));
      }

      // 何知章条件核查（4 维成对条：同维强弱两面并排）
      function HezhiPairs({ d }) {
        const pairs = d && d.hezhi_pairs ? d.hezhi_pairs : [];
        if (!pairs.length) return null;
        return h("div", { className: "ft-sec" },
          h("div", { className: "ft-sec-h" }, "何知章条件核查（4 维成对，非吉凶总断）"),
          pairs.map((p, i) => h("div", { key: p.dim, className: "ft-pair", style: { "--n": i } },
            (p.items ?? []).map((it) => h("div", {
              key: it.key,
              className: `ft-pair-side${it.matched ? " ft-pair-hit" : ""}`,
            },
              h("div", { className: "ft-pair-line" },
                `${it.line}（${it.matched ? "命中" : "未命中"}）`),
              h("div", { className: "ft-pair-reason" }, it.reason))))));
      }

      // 大运流年时间轴（点年份看确定性关系事实）
      function LiunianTimeline({ d }) {
        const rows = d && d.liunian ? d.liunian : [];
        const [sel, setSel] = useState(0);
        if (!rows.length) return null;
        const r = rows[Math.min(sel, rows.length - 1)];
        return h("div", { className: "ft-sec" },
          h("div", { className: "ft-sec-h" },
            `大运流年速览（自 ${d.liunian_anchor ?? ""} 年起；确定性关系事实，不断吉凶）`),
          h("div", { className: "ft-tl", role: "tablist" },
            rows.map((x, i) => h("button", {
              key: x.year, type: "button", role: "tab",
              className: `ft-tl-y${i === sel ? " ft-sel" : ""}`
                + `${x.facts && x.facts.length ? " ft-hit" : ""}`,
              style: { "--n": i }, onClick: () => setSel(i),
              "aria-selected": String(i === sel),
              title: x.facts ? x.facts.join("；") : "与原局及大运无冲合刑害",
            },
              h("div", { className: "ft-tl-yr" }, x.year),
              h("div", { className: "ft-tl-gz" }, x.gan_zhi),
              h("div", { className: "ft-tl-ss" },
                `${x.shi_shen}${x.dayun ? ` · ${x.dayun}` : ""}`)))),
          h("div", { className: "ft-panel" },
            h("div", { className: "ft-panel-h" },
              `${r.year} ${r.gan_zhi} · ${r.shi_shen} · 纳音${r.na_yin ?? ""}`
              + `${r.dayun ? ` · 大运${r.dayun}` : ""}`),
            h("div", { className: "ft-panel-row" },
              (r.facts ?? []).length ? r.facts.join("；")
                : "与原局及大运无冲合刑害。")));
      }

      function BaziView({ block }) {
        ensureStyle();
        const base = metaData(block);
        const [cal, setCal] = useState("solar");
        const [tab, setTab] = useState("pillars");
        const [sel, setSel] = useState(2);
        const alt = base && base.alternates ? base.alternates.clock : null;
        const d = cal === "clock" && alt ? alt : base;
        if (!base) return h(ToolRow, { block, title: "八字排盘" });
        const c = d.chart ?? {};
        const st = d.strength ?? {};
        const ys = d.yongshen ?? {};
        const pills = [];
        if (c.solar_used) pills.push(h("span", { className: "ft-pill" }, `排盘 ${c.solar_used}`));
        if (c.steps && c.steps.some((s) => String(s).includes("真太阳时"))) {
          pills.push(h("span", { className: "ft-pill" }, "真太阳时"));
        }
        if (c.dayun && c.dayun.length) {
          pills.push(h("span", { className: "ft-pill" },
            `大运${c.yun_forward ? "顺行" : "逆行"} · 起运 ${c.yun_start_solar}（虚岁${c.yun_start_age}）`));
        }
        const relCount = (d.relations ?? []).length;
        const ssHits = (d.shensha ?? []).filter((s) => s.positions && s.positions.length);
        const tabs = [
          { id: "pillars", label: "四柱" },
          { id: "wuxing", label: "五行" },
          { id: "dayun", label: `大运(${c.dayun?.length ?? 0})` },
          { id: "shensha", label: `神煞(${ssHits.length})` },
          { id: "relation", label: `关系(${relCount})` },
          { id: "yongshen", label: "用神" },
          { id: "hezhi", label: "何知章" },
          { id: "liunian", label: "流年" },
        ];
        const selP = (c.pillars ?? [])[sel] ?? null;
        return h("div", { className: "ft-node", style: { "--n": 0 } },
          h("div", { className: "ft-head" },
            h("span", { className: "ft-title" }, "八字排盘"),
            pills,
            !isSettled(block)
              ? h("span", { className: "ft-pill ft-run" }, "执行中…") : null),
          alt
            ? h("div", { className: "ft-seg", role: "group", "aria-label": "时辰口径切换" },
                h("button", { type: "button", "aria-pressed": String(cal === "solar"),
                  onClick: () => setCal("solar") }, "真太阳时"),
                h("button", { type: "button", "aria-pressed": String(cal === "clock"),
                  onClick: () => setCal("clock") }, "钟表时"))
            : null,
          h(TabBar, { tabs, active: tab, onSelect: setTab }),
          tab === "pillars"
            ? h("div", { className: "ft-pillars" },
                (c.pillars ?? []).map((p, i) => h("button", {
                  key: p.name, type: "button",
                  className: `ft-pillar${i === 2 ? " ft-day" : ""}${sel === i ? " ft-sel" : ""}`,
                  style: { "--n": i },
                  onClick: () => setSel(i),
                  "aria-pressed": String(sel === i),
                },
                  h("div", { className: "ft-pname" }, p.name + (i === 2 ? "（日主）" : "")),
                  h("div", { className: "ft-gz" }, p.gan_zhi),
                  h("div", { className: "ft-sub" },
                    `${p.wu_xing} · ${p.na_yin} · ${p.shi_shen_gan}`),
                  h("div", { className: "ft-hide" },
                    (p.hide_gan ?? []).map((g, k) => `${g}(${p.shi_shen_zhi?.[k] ?? ""})`).join(" ")),
                  h("div", { className: "ft-sub" }, `${p.di_shi} · 旬空${p.xun_kong}`))))
            : null,
          tab === "pillars" && selP
            ? h(DetailPanel, {
                title: `${selP.name} ${selP.gan_zhi} · ${selP.shi_shen_gan}`,
              },
                h("div", { className: "ft-panel-row" },
                  h("span", null, `五行 ${selP.wu_xing}`),
                  h("span", null, `纳音 ${selP.na_yin}`),
                  h("span", null, `地势 ${selP.di_shi}`),
                  h("span", null, `旬空 ${selP.xun_kong}`),
                  h("span", null, SHI_SHEN_MEANING[selP.shi_shen_gan] ?? "")),
                h("div", { className: "ft-legend" },
                  `藏干：${(selP.hide_gan ?? []).map((g, k) =>
                    `${g}→${selP.shi_shen_zhi?.[k] ?? ""}`).join("　")}`))
            : null,
          tab === "wuxing"
            ? h(WuxingPanel, { st })
            : null,
          tab === "dayun"
            ? h("div", { className: "ft-sec" },
                h("div", { className: "ft-sec-h" }, "大运（每步十年）"),
                h("div", { className: "ft-chips" },
                  c.dayun?.map((d2, i) => h("span", {
                    key: i, className: "ft-chip",
                    style: { animationDelay: `${i * 50}ms` },
                  }, `${d2.gan_zhi} ${d2.start_age}-${d2.end_age}岁`))))
            : null,
          tab === "shensha"
            ? h("div", { className: "ft-sec" },
                h("div", { className: "ft-sec-h" }, "神煞（点击「四柱」页签查看命中的柱）"),
                h("div", { className: "ft-chips" },
                  ssHits.slice(0, 16).map((s, i) => h("span", {
                    key: i, className: "ft-chip", title: s.note ?? "",
                  }, `${s.name}→${s.positions.join("/")}`))))
            : null,
          tab === "relation"
            ? h("div", { className: "ft-sec" },
                h("div", { className: "ft-sec-h" }, "合冲刑害"),
                h("div", { className: "ft-chips" },
                  (d.relations ?? []).map((r, i) => h("span", {
                    key: i, className: "ft-chip",
                  }, `${r.name} ${(r.positions ?? []).join("/")}`))))
            : null,
          tab === "yongshen"
            ? (d.yongshen_all
                ? h(YongshenMulti, { d })
                : h("div", { className: "ft-sec" },
                    h("div", { className: "ft-sec-h" }, `用神（${ys.school}，规则引擎参考）`),
                    h("div", { className: "ft-chips" },
                      h("span", { className: "ft-pill ft-ok" },
                        `用 ${(ys.yong_wuxing ?? []).join("、") || "—"}`),
                      ys.ji_wuxing && ys.ji_wuxing.length
                        ? h("span", { className: "ft-pill ft-warn" },
                            `忌 ${ys.ji_wuxing.join("、")}`) : null),
                    h("div", { className: "ft-legend" },
                      (ys.conclusions ?? []).slice(0, 3).join("；"))))
            : null,
          tab === "hezhi"
            ? h(HezhiPairs, { d })
            : null,
          tab === "liunian"
            ? h(LiunianTimeline, { d })
            : null,
          h(ContentText, { block }));
      }

      // ------------------------------------------------------------------
      // 紫微视图：十二宫盘（点宫看详情、悬停高亮对宫）
      // ------------------------------------------------------------------
      const BRIGHT_MEANING = {
        庙: "最吉，星力全显", 旺: "次吉", 得: "平吉", 利: "小吉",
        平: "中和", 不: "陷弱", 陷: "最弱",
      };
      function ZiweiView({ block }) {
        ensureStyle();
        const d = metaData(block);
        const [sel, setSel] = useState(-1);
        const [hover, setHover] = useState(-1);
        if (!d) return h(ToolRow, { block, title: "紫微斗数排盘" });
        const palaces = d.palaces ?? [];
        if (!palaces.length) return h(ToolRow, { block, title: "紫微斗数排盘" });
        // 传统 4×4 宫格：按地支定宫位（外围 12 格 + 中央 2×2 摘要）
        // 巳午未申 / 辰···酉 / 卯···戌 / 寅丑子亥（中央为摘要）
        const CELL = {
          子: [4, 3], 丑: [4, 2], 寅: [4, 1], 卯: [3, 1], 辰: [2, 1], 巳: [1, 1],
          午: [1, 2], 未: [1, 3], 申: [1, 4], 酉: [2, 4], 戌: [3, 4], 亥: [4, 4],
        };
        const MUT_CLS = { 禄: "ft-mut-lu", 权: "ft-mut-quan", 科: "ft-mut-ke", 忌: "ft-mut-ji" };
        const OPP = { 子: "午", 午: "子", 丑: "未", 未: "丑", 寅: "申", 申: "寅",
                     卯: "酉", 酉: "卯", 辰: "戌", 戌: "辰", 巳: "亥", 亥: "巳" };
        // 亮度传统配色：庙=绿、旺=蓝、得/利=黄、平=灰、不/陷=暗
        const BRIGHT_CLS = { 庙: "ft-zb-miao", 旺: "ft-zb-wang", 得: "ft-zb-de",
                             利: "ft-zb-li", 平: "ft-zb-ping", 不: "ft-zb-ruo", 陷: "ft-zb-ruo" };
        const zhiOf = (idx) => String(palaces[idx]?.gan_zhi ?? "").slice(-1);
        const selZhi = sel >= 0 ? zhiOf(sel) : null;
        const selOppZhi = selZhi ? OPP[selZhi] : null;
        const oppZhi = selOppZhi;
        const hoverZhi = hover >= 0 ? zhiOf(hover) : null;
        const cells = palaces.map((p, i) => {
          const zhi = String(p.gan_zhi ?? "").slice(-1);
          const [row, col] = CELL[zhi] ?? [4, 1];
          const isSel = sel === i;
          // 对宫联动：点选=品牌光晕虚线（确认态）；悬停=琥珀柔呼吸虚线（观察态）
          const isOppS = selOppZhi !== null && selOppZhi === zhi && !isSel;
          const isOppH = !isOppS && hoverZhi !== null && hoverZhi !== zhi && OPP[hoverZhi] === zhi;
          const tag = p.is_ming
            ? h("span", { className: "ft-zw-mingtag" }, "命")
            : p.is_shen
              ? h("span", { className: "ft-zw-tag" }, "身")
              : p.is_laiyin
                ? h("span", { className: "ft-zw-tag" }, "因")
                : null;
          return h("button", {
            key: `${p.name}-${i}`, type: "button", tabIndex: 0,
            className: `ft-zw-cell${p.is_ming ? " ft-ming" : ""}`
              + `${isSel ? " ft-sel" : ""}`
              + `${isOppS ? " ft-opp-s" : isOppH ? " ft-opp-h" : ""}`,
            style: { gridRow: row, gridColumn: col, "--i": i },
            onClick: () => setSel(isSel ? -1 : i),
            onMouseEnter: () => setHover(i),
            onMouseLeave: () => setHover(-1),
            onKeyDown: (e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                setSel(isSel ? -1 : i);
              }
            },
            "aria-pressed": String(isSel),
            "aria-label": `点击查看 ${p.name} 星曜详情`,
          },
            h("div", { className: "ft-zw-head" },
              h("span", { className: "ft-zw-name" }, p.name),
              tag,
              h("span", { className: "ft-zw-gz" }, p.gan_zhi)),
            h("div", { className: "ft-zw-stars" },
              (p.major ?? []).map(([n, b, mut]) => h("div", {
                key: n,
                className: `ft-zw-star ft-main${mut ? ` ${MUT_CLS[mut] ?? ""}` : ""}`,
                title: b ? `亮度「${b}」：${BRIGHT_MEANING[b] ?? ""}` : undefined,
              }, mut ? `${n}·${mut}` : n,
                b ? h("span", { className: `ft-zw-b ${BRIGHT_CLS[b] ?? ""}` }, `[${b}]`) : null)),
              h("div", { className: "ft-zw-minor" },
                [...(p.minor ?? []), ...(p.adjective ?? [])].slice(0, 8).join("　")
                + (p.minor.length + p.adjective.length > 8 ? "…" : ""))),
            h("div", { className: "ft-zw-foot" },
              p.da_xian ? `大限 ${p.da_xian} 岁` : "", " ",
              p.chang_sheng ? `长生「${p.chang_sheng}」` : ""));
        });
        const selP = sel >= 0 ? palaces[sel] : null;
        return h("div", { className: "ft-node", style: { "--n": 0 } },
          h("div", { className: "ft-head" },
            h("span", { className: "ft-title" }, "紫微斗数排盘"),
            h("span", { className: "ft-pill" }, d.five_elements_class ?? ""),
            h("span", { className: "ft-pill" }, `命主 ${d.ming_zhu ?? "?"}`),
            h("span", { className: "ft-pill" }, `身主 ${d.shen_zhu ?? "?"}`),
            !isSettled(block)
              ? h("span", { className: "ft-pill ft-run" }, "执行中…") : null),
          h("div", { className: "ft-zw-grid", role: "group",
            "aria-label": "紫微斗数十二宫盘（点击宫位查看星曜详情）" },
            cells,
            h("div", { className: "ft-zw-center" },
              h("div", { className: "ft-zw-center-t" }, "紫微斗数"),
              h("div", { className: "ft-zw-center-m" },
                `${d.solar_used ?? ""}${d.gender ? ` · ${d.gender}` : ""}`),
              h("div", { className: "ft-zw-center-l" },
                selP && oppZhi
                  ? `已选 ${selP.name}（${selZhi}），对宫 ${oppZhi}宫（品牌光晕虚线）；悬停任意宫会以琥珀虚线联动其六冲对宫。`
                  : "点选宫位看星曜详情（品牌光晕）；悬停宫位联动其六冲对宫（琥珀虚线）。",
                h("span", null, "配色：四化禄·权·科·忌；[庙]亮 [陷]暗；命宫=底色+品牌框。"))),
          selP            ? h(DetailPanel, {
                title: `${selP.name}${selP.is_ming ? "（命宫）" : selP.is_shen ? "（身宫）" : ""}${selP.is_laiyin ? "（来因宫）" : ""} · ${selP.gan_zhi} · 大限 ${selP.da_xian} 岁 · 长生「${selP.chang_sheng}」`,
              },
                h("div", { className: "ft-panel-row" },
                  (selP.major ?? []).map(([n, b, mut]) => h("span", {
                    key: n, className: `ft-chip${mut ? ` ${MUT_CLS[mut] ?? ""}` : ""}`,
                    title: `亮度「${b}」：${BRIGHT_MEANING[b] ?? ""}`,
                  }, `${n}${b ? `[${b}]` : ""}${mut ? `·${mut}` : ""}`))),
                (selP.minor ?? []).length + (selP.adjective ?? []).length
                  ? h("div", { className: "ft-legend" },
                      `辅星杂曜：${[...(selP.minor ?? []), ...(selP.adjective ?? [])].join("、")}`)
                  : null,
                h("div", { className: "ft-legend" },
                  `对宫：${oppZhi}宫。亮度：庙最吉＞旺＞得＞利＞平＞不＞陷。`))
            : null,
          d.patterns && d.patterns.length
            ? h("div", { className: "ft-sec" },
                h("div", { className: "ft-sec-h" }, "格局（iztro 64 格局库）"),
                h("div", { className: "ft-chips" },
                  d.patterns.map((p, i) => h("span", {
                    key: i, className: `ft-chip${String(p).includes("[破格]") ? " ft-warn" : ""}`,
                  }, p))))
            : null,
          d.pattern_review && d.pattern_review.length
            ? h("div", { className: "ft-sec" },
                h("div", { className: "ft-sec-h" }, "格局复核（展示性核对，判定以引擎为准）"),
                d.pattern_review.map((p, i) => h("div", {
                  key: `r${i}`, className: "ft-pair-reason",
                }, p)))
            : null,
          d.interpret_glance && d.interpret_glance.length
            ? h("div", { className: "ft-sec" },
                h("div", { className: "ft-sec-h" }, "解读速览（检索式，非推断）"),
                d.interpret_glance.map((p, i) => h("div", {
                  key: `g${i}`, className: "ft-pair-reason",
                }, p)))
            : null,
          h(ContentText, { block, max: 1500 })));
      }

      // ------------------------------------------------------------------
      // 六爻视图：点爻看六亲/六神释义
      // ------------------------------------------------------------------
      const LIUQIN_MEANING = {
        父母: "生我者——文书、长辈、房产、庇荫",
        兄弟: "同我者——同辈、朋友、竞争、分财",
        子孙: "我生者——晚辈、福神、财源、解忧",
        妻财: "我克者——钱财、妻妾、资源",
        官鬼: "克我者——官非、疾病、丈夫、压力",
      };
      const LIUSHEN_MEANING = {
        青龙: "吉庆喜事", 朱雀: "口舌文书", 勾陈: "田土牵连",
        螣蛇: "虚惊怪异", 白虎: "凶伤病丧", 玄武: "盗昧暗昧",
      };
      function LiuyaoView({ block }) {
        ensureStyle();
        const d = metaData(block);
        const [sel, setSel] = useState(-1);
        if (!d) return h(ToolRow, { block, title: "六爻起卦装卦" });
        const lines = d.lines ?? [];
        const selL = sel >= 0 ? lines[sel] : null;
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
            [...lines].reverse().map((l, i) => {
              const idx = lines.length - 1 - i;   // 原始列表索引（自下而上）
              return h("button", {
                key: l.no, type: "button",
                className: `ft-yao${sel === idx ? " ft-sel" : ""}`,
                style: { "--n": i },
                onClick: () => setSel(sel === idx ? -1 : idx),
                "aria-pressed": String(sel === idx),
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
                  h("span", { className: "ft-chip" }, l.liu_shen)));
            })),
          selL
            ? h(DetailPanel, {
                title: `${selL.no}爻 ${selL.gan_zhi}${selL.is_moving ? "（动爻）" : ""}${selL.no === d.shi ? " · 世爻" : selL.no === d.ying ? " · 应爻" : ""}`,
              },
                h("div", { className: "ft-panel-row" },
                  h("span", null, `六亲「${selL.liu_qin}」：${LIUQIN_MEANING[selL.liu_qin] ?? ""}`),
                  h("span", null, `六神「${selL.liu_shen}」：${LIUSHEN_MEANING[selL.liu_shen] ?? ""}`)),
                h("div", { className: "ft-legend" },
                  `${selL.is_moving
                    ? `动爻（${selL.value === 9 ? "老阳○" : "老阴×"}），变卦中此爻阴阳翻转。`
                    : "静爻，不变。"}`))
            : null,
          (d.topic && d.topic !== "综合" && d.topic_focus)
            ? h("div", { className: "ft-sec" },
                h("div", { className: "ft-sec-h" },
                  `占题：${d.topic}${d.question ? `「${d.question}」` : ""}`
                  + `${d.date ? `（起卦 ${d.date}，自动推导月建日辰）` : ""}`),
                h("pre", { className: "ft-out" }, d.topic_focus))
            : null,
          d.caliber
            ? h("div", { className: "ft-meta" },
                h("span", { className: "ft-caption" }, d.caliber))
            : null,
          h(ContentText, { block }));
      }

      // ------------------------------------------------------------------
      // 梅花视图：点卦卡看爻位/先天数/五行
      // ------------------------------------------------------------------
      const GUA_SYM = { 乾: "☰", 兑: "☱", 离: "☲", 震: "☳",
                       巽: "☴", 坎: "☵", 艮: "☶", 坤: "☷" };
      const GUA_INFO = {
        乾: { bits: "☰ 阳阳阳", num: 1, wx: "金", nature: "天·健" },
        兑: { bits: "☱ 阳阳阴", num: 2, wx: "金", nature: "泽·悦" },
        离: { bits: "☲ 阳阴阳", num: 3, wx: "火", nature: "火·丽" },
        震: { bits: "☳ 阳阴阴", num: 4, wx: "木", nature: "雷·动" },
        巽: { bits: "☴ 阴阳阳", num: 5, wx: "木", nature: "风·入" },
        坎: { bits: "☵ 阴阳阴", num: 6, wx: "水", nature: "水·险" },
        艮: { bits: "☶ 阴阴阳", num: 7, wx: "土", nature: "山·止" },
        坤: { bits: "☷ 阴阴阴", num: 8, wx: "土", nature: "地·顺" },
      };
      function MeihuaView({ block }) {
        ensureStyle();
        const d = metaData(block);
        const [sel, setSel] = useState("ben");
        if (!d) return h(ToolRow, { block, title: "梅花易数" });
        const sym = (up, lo) => `${GUA_SYM[up] ?? ""}${GUA_SYM[lo] ?? ""}`;
        const good = d.relation === "用生体" || d.relation === "比和";
        const bad = d.relation === "用克体";
        const cards = [
          { id: "ben", tag: "本卦 · 动爻第" + d.moving_line + "爻",
            up: d.upper, lo: d.lower, name: d.ben_gua, cls: "ft-ben" },
          { id: "hu", tag: "互卦", up: d.hu_upper, lo: d.hu_lower, name: d.hu_gua },
          { id: "bian", tag: "变卦", up: d.bian_upper, lo: d.bian_lower, name: d.bian_gua },
        ];
        const selC = cards.find((x) => x.id === sel);
        return h("div", { className: "ft-node", style: { "--n": 0 } },
          h("div", { className: "ft-head" },
            h("span", { className: "ft-title" }, "梅花易数"),
            h("span", { className: "ft-caption" }, d.method ?? ""),
            d.caliber
              ? h("span", { className: "ft-pill" }, d.caliber)
              : null,
            !isSettled(block)
              ? h("span", { className: "ft-pill ft-run" }, "执行中…") : null),
          h("div", { className: "ft-gua-row" },
            cards.map((c2, i) => h("button", {
              key: c2.id, type: "button",
              className: `ft-gua-card ${c2.cls ?? ""}${sel === c2.id ? " ft-sel" : ""}`,
              style: { "--n": i },
              onClick: () => setSel(c2.id),
              "aria-pressed": String(sel === c2.id),
            },
              h("div", { className: "ft-gua-sym" }, sym(c2.up, c2.lo)),
              h("div", { className: "ft-gua-name" }, c2.name),
              h("div", { className: "ft-gua-tag" }, c2.tag)))),
          selC
            ? h(DetailPanel, { title: `${selC.tag}：${selC.name}` },
                h("div", { className: "ft-panel-row" },
                  h("span", null, `上卦 ${selC.up ?? "?"}（${GUA_INFO[selC.up]?.nature ?? ""}，先天数 ${GUA_INFO[selC.up]?.num ?? "?"}，五行 ${GUA_INFO[selC.up]?.wx ?? "?"}）`),
                  h("span", null, `下卦 ${selC.lo ?? "?"}（${GUA_INFO[selC.lo]?.nature ?? ""}，先天数 ${GUA_INFO[selC.lo]?.num ?? "?"}，五行 ${GUA_INFO[selC.lo]?.wx ?? "?"}）`)),
                h("div", { className: "ft-legend" },
                  `卦符自下而上：${GUA_INFO[selC.up]?.bits ?? ""} / ${GUA_INFO[selC.lo]?.bits ?? ""}。`))
            : null,
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
      // 称骨视图：点卡看构成 + 重播动效
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
        const [sel, setSel] = useState(-1);
        const [play, setPlay] = useState(0);
        if (!d) return h(ToolRow, { block, title: "袁天罡称骨" });
        const items = [
          [`年（${d.year_gz}）`, d.year_qian],
          [`月（农历${d.lunar_month}月）`, d.month_qian],
          [`日（农历${d.lunar_day}）`, d.day_qian],
          [`时（${d.hour_zhi}时）`, d.hour_qian],
        ];
        const replay = () => setPlay((p) => p + 1);
        return h("div", { className: "ft-node", style: { "--n": 0 } },
          h("div", { className: "ft-head" },
            h("span", { className: "ft-title" }, "袁天罡称骨"),
            h("span", { className: "ft-caption" }, "通行男命版 · 仅作文化参考"),
            d.caliber
              ? h("span", { className: "ft-pill" }, d.caliber)
              : null,
            !isSettled(block)
              ? h("span", { className: "ft-pill ft-run" }, "执行中…") : null),
          h("div", { key: `w${play}`, className: "ft-w-row" },
            items.map(([k, v], i) => h("button", {
              key: k, type: "button",
              className: `ft-w-chip${sel === i ? " ft-sel" : ""}`,
              style: { "--n": i },
              onClick: () => setSel(sel === i ? -1 : i),
              "aria-pressed": String(sel === i),
            },
              h("div", { className: "ft-w-k" }, k),
              h("div", { className: "ft-w-v" }, qianStr(v))))),
          sel >= 0
            ? h(DetailPanel, { title: `${items[sel][0]} = ${qianStr(items[sel][1])}` },
                h("div", { className: "ft-legend" },
                  "骨重为通行本查表值（10 钱 = 1 两）；点其它卡片查看对应项。"))
            : null,
          d.total_qian != null
            ? h("div", { className: "ft-total" },
                h("span", {
                  key: `t${play}`,
                  className: "ft-total-v",
                }, qianStr(d.total_qian)),
                h("div", { className: "ft-caption" }, "总骨重"),
                h("button", { type: "button", className: "ft-btn",
                  onClick: replay }, "↻ 重播动效"))
            : null,
          d.verdict
            ? h("div", { className: "ft-verdict" }, d.verdict)
            : null,
          h(ContentText, { block, max: 1200 }));
      }

      // ------------------------------------------------------------------
      // 小六壬视图：「逐步推演」重播月→日→时
      // ------------------------------------------------------------------
      function XiaoliurenView({ block }) {
        ensureStyle();
        const d = metaData(block);
        const [step, setStep] = useState(3);   // 3 = 全部显示
        const timers = useRef([]);
        useEffect(() => () => {
          timers.current.forEach((t) => clearTimeout(t));
        }, []);
        const replay = () => {
          // 用户主动触发的推演始终执行（减少动效时用快进节奏，不跳过）
          timers.current.forEach((t) => clearTimeout(t));
          timers.current = [];
          const reduced = typeof window !== "undefined"
            && window.matchMedia
            && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
          const gap = reduced ? 140 : 450;
          setStep(0);
          timers.current.push(setTimeout(() => setStep(1), gap));
          timers.current.push(setTimeout(() => setStep(2), gap * 2));
          timers.current.push(setTimeout(() => setStep(3), gap * 3));
        };
        if (!d) return h(ToolRow, { block, title: "小六壬" });
        const info = d.info ?? {};
        const steps = [
          [`月 ${d.lunar_month}`, d.month_palace],
          [`日 ${d.lunar_day}`, d.day_palace],
          [`时 ${d.hour_zhi}`, d.palace],
        ];
        const good = String(info["吉凶"] ?? "").includes("吉") && !String(info["吉凶"] ?? "").includes("凶");
        const playing = step < 3 && step >= 0;
        return h("div", { className: "ft-node", style: { "--n": 0 } },
          h("div", { className: "ft-head" },
            h("span", { className: "ft-title" }, "小六壬"),
            h("span", { className: "ft-caption" },
              `农历${d.lunar_month}月${d.lunar_day}日 ${d.hour_zhi}时`),
            d.caliber
              ? h("span", { className: "ft-pill" }, d.caliber)
              : null,
            h("button", { type: "button", className: "ft-btn", onClick: replay,
              "aria-busy": String(playing) },
              playing ? "推演中…" : "▶ 逐步推演"),
            !isSettled(block)
              ? h("span", { className: "ft-pill ft-run" }, "执行中…") : null),
          h("div", { className: "ft-path" },
            steps.map(([k, v], i) => {
              if (step < i + 1) return null;   // 逐步显示（隐藏后续步骤，视觉不可忽略）
              return [
                i > 0 ? h("span", { key: `a${i}`, className: "ft-arrow" }, "→") : null,
                h("span", { key: `s${i}`, className: "ft-step", style: { "--n": i } },
                  h("span", { className: "ft-caption" }, `${k} 落`),
                  h("span", {
                    className: `ft-pill ${i === 2 ? (good ? "ft-ok" : "ft-warn") : ""}`,
                  }, v)),
              ];
            })),
          step === 3
            ? h("div", { className: "ft-palace" },
                h("div", { className: "ft-palace-n" }, d.palace),
                h("div", { className: "ft-meta", style: { justifyContent: "center" } },
                  h("span", { className: `ft-pill ${good ? "ft-ok" : "ft-warn"}` }, info["吉凶"] ?? ""),
                  info["五行"] ? h("span", { className: "ft-pill" }, `五行 ${info["五行"]}`) : null,
                  info["方位"] ? h("span", { className: "ft-pill" }, info["方位"]) : null,
                  info["神煞"] ? h("span", { className: "ft-pill" }, info["神煞"]) : null,
                  info["主数"] ? h("span", { className: "ft-pill" }, `主数 ${info["主数"]}`) : null))
            : null,
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

      // ------------------------------------------------------------------
      // 综合分析视图：共识热力矩阵 + 维度结论卡 + 证据链折叠 + 冲突清单
      // ------------------------------------------------------------------
      function ConsensusHeat({ d }) {
        const schools = d && d.matrix ? Object.keys(d.matrix) : [];
        if (!schools.length) return null;
        const WX = ["木", "火", "土", "金", "水"];
        const cell = (key, text, extra) =>
          h("div", { key, className: `ft-heat-c${extra ?? ""}` }, text);
        return h("div", { className: "ft-sec" },
          h("div", { className: "ft-sec-h" }, "用神共识矩阵（流派 × 五行投票）"),
          h("div", { className: "ft-heat" },
            cell("h0", "流派", " ft-heat-h"),
            WX.map((w) => cell(`h${w}`, w, " ft-heat-h")),
            cell("hc", "结论", " ft-heat-h"),
            schools.map((s) => [
              cell(`s${s}`, SCHOOL_LABEL[s] ?? s),
              ...WX.map((w) => {
                const hit = (d.matrix[s] ?? []).includes(w);
                return h("div", { key: `${s}${w}`, className: "ft-heat-c" },
                  hit ? h("div", { className: "ft-heat-bar", style: { height: "100%" } }) : null,
                  hit ? "✓" : "");
              }),
              cell(`c${s}`, (d.matrix[s] ?? []).join("、") || "—"),
            ])),
          h("div", { className: "ft-legend" },
            "五行加权得票：" + WX.map((w) =>
              `${w} ${((d.consensus ?? {})[w] ?? 0).toFixed(2)}`).join("；")
            + "（各流派等权/可配权重；调候用神取《穷通宝鉴》原文提炼映射）"));
      }

      function ComprehensiveView({ block }) {
        ensureStyle();
        const d = metaData(block);
        const [open, setOpen] = useState({});
        if (!d) return h(ToolRow, { block, title: "综合分析" });
        const concl = (d.conclusions ?? []).slice().sort((a, b) => (b.score ?? 0) - (a.score ?? 0));
        return h("div", { className: "ft-node", style: { "--n": 0 } },
          h("div", { className: "ft-head" },
            h("span", { className: "ft-title" }, "综合分析（无 LLM 聚合）"),
            !isSettled(block)
              ? h("span", { className: "ft-pill ft-run" }, "执行中…") : null),
          h(ConsensusHeat, { d }),
          concl.map((c, i) => {
            const band = c.score >= 0.6 ? "强" : c.score >= 0.3 ? "中" : "弱";
            const isOpen = !!open[c.dim];
            return h("div", { key: c.dim, className: "ft-sec" },
              h("div", { className: "ft-head" },
                h("span", { className: "ft-title" }, c.dim),
                h("span", {
                  className: `ft-pill ${band === "强" ? "ft-ok" : band === "中" ? "ft-run" : "ft-warn"}`,
                }, `共识度 ${(c.score ?? 0).toFixed(2)}（${band}共识）`),
                (c.evidence && c.evidence.length)
                  ? h("button", { type: "button", className: "ft-btn",
                      "aria-expanded": String(isOpen),
                      onClick: () => setOpen((o) => ({ ...o, [c.dim]: !o[c.dim] })) },
                      isOpen ? "收起证据链" : "展开证据链") : null),
              h("div", { className: "ft-pair-reason" }, c.text),
              c.scores
                ? h("div", { className: "ft-sec" },
                    WX_ORDER.map((w, i) => h("div", {
                      key: w, className: "ft-bar-row", style: { "--n": i },
                    },
                      h("span", { className: "ft-bar-l" }, w),
                      h("div", { className: "ft-bar" },
                        h("i", { style: {
                          width: `${Math.max(3, ((c.scores[w] ?? 0)
                            / Math.max(0.01, ...Object.values(c.scores))) * 100)}%`,
                          opacity: `${1 - i * 0.12}`,
                        } })),
                      h("span", { className: "ft-bar-v" },
                        `${(c.scores[w] ?? 0).toFixed(2)}`))))
                : null,
              isOpen && c.evidence
                ? h("div", { className: "ft-panel" },
                    c.evidence.map((e, k) => h("div", {
                      key: k, className: "ft-ev-item", style: { "--n": k },
                    },
                      h("div", { className: "ft-ev-head" },
                        h("span", {
                          className: `ft-ev-tool ${TOOL_PILL[e.tool] ?? ""}`,
                          title: e.tool ?? "",
                        }, TOOL_LABEL[e.tool] ?? e.tool ?? "—"),
                        h("span", { className: "ft-ev-field" },
                          (e.field ?? "").replace(
                            /wangshuai|tiaohou|tongguan|geju|bingyao/g,
                            (m) => SCHOOL_LABEL[m] ?? m))),
                      h("div", { className: "ft-ev-fact" }, e.fact ?? ""),
                      e.source
                        ? h("div", { className: "ft-ev-src" }, `出处：${e.source}`)
                        : null)))
                : null);
          }),
          d.conflicts && d.conflicts.length
            ? h("div", { className: "ft-sec" },
                h("div", { className: "ft-sec-h" }, "冲突清单（如实呈现，不调和）"),
                d.conflicts.map((c2, i) => h("div", {
                  key: i, className: "ft-pair-reason",
                }, `⚠ ${String(c2).replace(
                  /wangshuai|tiaohou|tongguan|geju|bingyao/g,
                  (m) => SCHOOL_LABEL[m] ?? m)}`)))
            : null,
          d.notes && d.notes.length
            ? h("div", { className: "ft-sec" },
                h("div", { className: "ft-sec-h" }, "备注"),
                d.notes.map((n2, i) => h("div", { key: i, className: "ft-pair-reason" }, n2)))
            : null,
          h(ContentText, { block, max: 3000 }));
      }

      // ------------------------------------------------------------------
      // BirthContext 视图：历法事实上下文（口径声明块）
      // ------------------------------------------------------------------
      function ContextView({ block }) {
        ensureStyle();
        const d = metaData(block);
        if (!d) return h(ToolRow, { block, title: "历法上下文" });
        return h("div", { className: "ft-node", style: { "--n": 0 } },
          h("div", { className: "ft-head" },
            h("span", { className: "ft-title" }, "历法上下文（BirthContext）"),
            h("span", { className: "ft-pill" }, `校正后 ${d.solar ?? ""}`),
            !isSettled(block)
              ? h("span", { className: "ft-pill ft-run" }, "执行中…") : null),
          h("div", { className: "ft-chips" },
            (d.eight_char ?? []).map((p, i) => h("span", {
              key: i, className: `ft-chip${i === 2 ? " ft-ok" : ""}`,
            }, p))),
          h("div", { className: "ft-meta" },
            h("span", { className: "ft-caption" },
              `钟表时支 ${d.time_zhi_clock ?? "—"} · 校正后时支 ${d.time_zhi_solar ?? "—"}`),
            d.true_solar_shift_min != null
              ? h("span", { className: "ft-caption" },
                  ` · 真太阳时校正 ${Number(d.true_solar_shift_min).toFixed(1)} 分`)
              : null),
          (d.steps ?? []).length
            ? h("div", { className: "ft-sec" },
                h("div", { className: "ft-sec-h" }, "归一化步骤"),
                d.steps.map((s2, i) => h("div", {
                  key: i, className: "ft-pair-reason",
                }, s2)))
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
        fortune_context: ContextView,
        fortune_comprehensive: ComprehensiveView,
      };

      const inject = ["slots"];

      function apply(ctx) {
        try {
          for (const [toolName, comp] of Object.entries(TOOLVIEWS)) {
            ctx.slots.inject("tool.call.toolview", () => ctx.slots.register({
              name: "tool.call.toolview",
              key: toolName,
            }, comp));
          }
        } catch (e) {
          console.error("[dsh-fortune-client] apply 失败:", e);
          throw e;
        }
      }

      exports.apply = apply;
      exports.inject = inject;
      exports.TOOLVIEWS = TOOLVIEWS;
      return module.exports;
    },
  });
})();
