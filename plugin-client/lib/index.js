// dsh-fortune-client 宿主侧 stub：宿主无职责（浏览器面由
// dsh-client-modules 按 package.json 的 dsh.client + exports["./client"]
// 装配进 window.__DSH_BOOT__）。此文件仅让 loader roster 行合法加载。
export const name = "dsh-fortune-client";

export function apply() {
  // no-op：宿主侧无服务注册（结构化数据生产者是 dsh-fortune 宿主插件）
}
