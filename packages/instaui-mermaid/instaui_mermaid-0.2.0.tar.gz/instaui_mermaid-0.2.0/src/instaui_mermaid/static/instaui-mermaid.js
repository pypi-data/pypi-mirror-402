import { defineComponent as M, ref as k, watch as C, onBeforeUnmount as w, createElementBlock as I, openBlock as $ } from "vue";
import _ from "mermaid";
import { useBindingGetter as L } from "instaui";
const x = "instaui-mermaid_svg-";
let y = 0;
function E() {
  return `${x}${y++}`;
}
function R() {
  return `mm_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}
function H(s, n) {
  return s.trimEnd() + `

%% auto generated click handlers
` + n.join(`
`) + `
`;
}
function N(s) {
  const n = window, t = R(), e = `__MERMAID_CLICK_DISPATCHER__${t}`, c = /* @__PURE__ */ new Map();
  n[e] = (a) => {
    const l = c.get(a);
    l && l(a, a);
  };
  function u(a, l) {
    c.clear();
    const g = [];
    for (const d of l) {
      const h = d.arg ?? d.node;
      c.set(d.node, (i) => s(i, h)), g.push(`click ${d.node} ${e}`);
    }
    return H(a, g);
  }
  function p() {
    c.clear();
    try {
      delete n[e];
    } catch {
      n[e] = void 0;
    }
  }
  return {
    enhance: u,
    dispose: p,
    namespace: t
  };
}
function B(s) {
  if (!s) return "";
  let n = s.split(`
`);
  const t = n.findIndex((e) => e.trim() !== "");
  if (t === -1) return "";
  if (n = n.slice(t), n[0].trim() === "---") {
    const e = n.findIndex(
      (c, u) => u > 0 && c.trim() === "---"
    );
    if (e !== -1) {
      const c = n.slice(0, e + 1), p = n.slice(e + 1).join(`
`).replace(/^\s*\n+/, "").replace(/\n+$/, "");
      return [...c, p].join(`
`);
    }
  }
  return n.join(`
`).replace(/^\s*\n+/, "").replace(/\n+$/, "");
}
const G = /* @__PURE__ */ M({
  __name: "Mermaid",
  props: {
    graph: {},
    initConfig: {},
    clickConfigs: {},
    errorRefName: {}
  },
  emits: ["update:graph", "node:click", "render:error", "render:success"],
  setup(s, { emit: n }) {
    const t = s, e = n, { initConfig: c, clickConfigs: u } = t, p = {
      ...c,
      startOnLoad: !1,
      ...u && { securityLevel: "loose" }
    };
    _.initialize(p);
    const a = k(), l = E(), g = N((i, o) => {
      e("node:click", {
        node: i,
        arg: o
      });
    }), d = t.errorRefName ? L().getRef(t.errorRefName) : null, h = k("");
    return C(
      [() => t.graph, a, () => t.clickConfigs],
      async ([i, o, v]) => {
        if (!o) return;
        i = B(i);
        const f = v ? g.enhance(i, v) : i;
        if (!!d)
          try {
            const { svg: r, bindFunctions: m } = await _.render(
              l,
              f,
              o
            );
            o.innerHTML = r, m == null || m(o), h.value = r, e("update:graph", f), e("render:success", f), d.value = "";
          } catch (r) {
            o.innerHTML = h.value, d.value = (r == null ? void 0 : r.message) || String(r), e("render:error", r);
          }
        else
          try {
            const { svg: r, bindFunctions: m } = await _.render(
              l,
              f,
              o
            );
            o.innerHTML = r, m == null || m(o), e("update:graph", f), e("render:success", f);
          } catch (r) {
            throw console.warn("Mermaid render error (default mode):", r, f), e("render:error", r), r;
          }
      }
    ), w(() => g.dispose()), (i, o) => ($(), I("div", {
      ref_key: "container",
      ref: a
    }, null, 512));
  }
});
export {
  G as default
};
