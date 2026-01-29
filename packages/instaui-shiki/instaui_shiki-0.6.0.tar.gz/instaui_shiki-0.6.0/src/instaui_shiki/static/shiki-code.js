import { defineComponent as b, ref as w, computed as n, normalizeClass as i, watch as T, createElementBlock as L, openBlock as $, normalizeStyle as x, createElementVNode as u, unref as c, toDisplayString as z } from "vue";
import { useBindingGetter as D, useLanguage as H } from "instaui";
import { highlighterTask as S, getTransformers as E, readyCopyButton as M } from "@/shiki-code-logic";
function R(o) {
  return o.replace(/^[\r\n\u2028\u2029]+|[\r\n\u2028\u2029]+$/g, "");
}
const G = { class: "lang" }, V = ["innerHTML"], F = /* @__PURE__ */ b({
  __name: "Shiki-Code",
  props: {
    code: {},
    language: {},
    theme: {},
    themes: {},
    transformers: {},
    lineNumbers: { type: Boolean },
    useDark: { type: Boolean },
    decorations: {}
  },
  setup(o) {
    const e = o, {
      transformers: g = [],
      themes: f = {
        light: "vitesse-light",
        dark: "vitesse-dark"
      },
      useDark: h
    } = e, { getRef: p } = D(), v = p(h), m = w(""), s = n(() => e.language || "python"), a = n(
      () => e.theme || (v.value ? "dark" : "light")
    ), k = n(() => e.lineNumbers ?? !0), y = n(() => i([
      `language-${s.value}`,
      `theme-${a.value}`,
      "shiki-code",
      { "line-numbers": k.value }
    ]));
    T(
      [() => e.code, a],
      async ([t, r]) => {
        if (!t)
          return;
        t = R(t);
        const l = await S, N = await E(g);
        m.value = await l.codeToHtml(t, {
          themes: f,
          lang: s.value,
          transformers: N,
          defaultColor: a.value,
          colorReplacements: {
            "#ffffff": "#f8f8f2"
          },
          decorations: e.decorations
        });
      },
      { immediate: !0 }
    );
    const { copyButtonClick: d, btnClasses: C } = M(e), _ = H(), B = n(() => `--shiki-code-copy-copied-text-content: '${_.value === "zh_CN" ? "已复制" : "Copied"}'`);
    return (t, r) => ($(), L("div", {
      class: i(y.value),
      style: x(B.value)
    }, [
      u("button", {
        class: i(c(C)),
        title: "Copy Code",
        onClick: r[0] || (r[0] = //@ts-ignore
        (...l) => c(d) && c(d)(...l))
      }, null, 2),
      u("span", G, z(s.value), 1),
      u("div", {
        innerHTML: m.value,
        style: { overflow: "hidden" }
      }, null, 8, V)
    ], 6));
  }
});
export {
  F as default
};
