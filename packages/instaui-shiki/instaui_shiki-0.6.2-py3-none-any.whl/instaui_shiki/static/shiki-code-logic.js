import { shallowRef as m, shallowReadonly as j, toValue as v, getCurrentScope as k, onScopeDispose as O, watch as x, computed as y, getCurrentInstance as B, onMounted as G, unref as q, toRaw as I, normalizeClass as N } from "vue";
function A(e) {
  return k() ? (O(e), !0) : !1;
}
const w = typeof window < "u" && typeof document < "u";
typeof WorkerGlobalScope < "u" && globalThis instanceof WorkerGlobalScope;
const _ = Object.prototype.toString, $ = (e) => _.call(e) === "[object Object]";
function z(e) {
  let t;
  function n() {
    return t || (t = e()), t;
  }
  return n.reset = async () => {
    const c = t;
    t = void 0, c && await c;
  }, n;
}
function S(e) {
  return Array.isArray(e) ? e : [e];
}
function D(e, t, n = {}) {
  const {
    immediate: c = !0,
    immediateCallback: f = !1
  } = n, i = m(!1);
  let s;
  function o() {
    s && (clearTimeout(s), s = void 0);
  }
  function r() {
    i.value = !1, o();
  }
  function u(...a) {
    f && e(), o(), i.value = !0, s = setTimeout(() => {
      i.value = !1, s = void 0, e(...a);
    }, v(t));
  }
  return c && (i.value = !0, w && u()), A(r), {
    isPending: j(i),
    start: u,
    stop: r
  };
}
function F(e, t, n) {
  return x(
    e,
    t,
    {
      ...n,
      immediate: !0
    }
  );
}
const U = w ? window : void 0, E = w ? window.navigator : void 0;
function V(e) {
  var t;
  const n = v(e);
  return (t = n == null ? void 0 : n.$el) != null ? t : n;
}
function L(...e) {
  const t = [], n = () => {
    t.forEach((o) => o()), t.length = 0;
  }, c = (o, r, u, a) => (o.addEventListener(r, u, a), () => o.removeEventListener(r, u, a)), f = y(() => {
    const o = S(v(e[0])).filter((r) => r != null);
    return o.every((r) => typeof r != "string") ? o : void 0;
  }), i = F(
    () => {
      var o, r;
      return [
        (r = (o = f.value) == null ? void 0 : o.map((u) => V(u))) != null ? r : [U].filter((u) => u != null),
        S(v(f.value ? e[1] : e[0])),
        S(q(f.value ? e[2] : e[1])),
        // @ts-expect-error - TypeScript gets the correct types, but somehow still complains
        v(f.value ? e[3] : e[2])
      ];
    },
    ([o, r, u, a]) => {
      if (n(), !(o != null && o.length) || !(r != null && r.length) || !(u != null && u.length))
        return;
      const p = $(a) ? { ...a } : a;
      t.push(
        ...o.flatMap(
          (g) => r.flatMap(
            (b) => u.map((h) => c(g, b, h, p))
          )
        )
      );
    },
    { flush: "post" }
  ), s = () => {
    i(), n();
  };
  return A(n), s;
}
function H() {
  const e = m(!1), t = B();
  return t && G(() => {
    e.value = !0;
  }, t), e;
}
function P(e) {
  const t = H();
  return y(() => (t.value, !!e()));
}
function M(e, t = {}) {
  const {
    controls: n = !1,
    navigator: c = E
  } = t, f = P(() => c && "permissions" in c), i = m(), s = typeof e == "string" ? { name: e } : e, o = m(), r = () => {
    var a, p;
    o.value = (p = (a = i.value) == null ? void 0 : a.state) != null ? p : "prompt";
  };
  L(i, "change", r, { passive: !0 });
  const u = z(async () => {
    if (f.value) {
      if (!i.value)
        try {
          i.value = await c.permissions.query(s);
        } catch {
          i.value = void 0;
        } finally {
          r();
        }
      if (n)
        return I(i.value);
    }
  });
  return u(), n ? {
    state: o,
    isSupported: f,
    query: u
  } : o;
}
function J(e = {}) {
  const {
    navigator: t = E,
    read: n = !1,
    source: c,
    copiedDuring: f = 1500,
    legacy: i = !1
  } = e, s = P(() => t && "clipboard" in t), o = M("clipboard-read"), r = M("clipboard-write"), u = y(() => s.value || i), a = m(""), p = m(!1), g = D(() => p.value = !1, f, { immediate: !1 });
  async function b() {
    let l = !(s.value && T(o.value));
    if (!l)
      try {
        a.value = await t.clipboard.readText();
      } catch {
        l = !0;
      }
    l && (a.value = W());
  }
  u.value && n && L(["copy", "cut"], b, { passive: !0 });
  async function h(l = v(c)) {
    if (u.value && l != null) {
      let d = !(s.value && T(r.value));
      if (!d)
        try {
          await t.clipboard.writeText(l);
        } catch {
          d = !0;
        }
      d && R(l), a.value = l, p.value = !0, g.start();
    }
  }
  function R(l) {
    const d = document.createElement("textarea");
    d.value = l ?? "", d.style.position = "absolute", d.style.opacity = "0", document.body.appendChild(d), d.select(), document.execCommand("copy"), d.remove();
  }
  function W() {
    var l, d, C;
    return (C = (d = (l = document == null ? void 0 : document.getSelection) == null ? void 0 : l.call(document)) == null ? void 0 : d.toString()) != null ? C : "";
  }
  function T(l) {
    return l === "granted" || l === "prompt";
  }
  return {
    isSupported: u,
    text: a,
    copied: p,
    copy: h
  };
}
function K() {
  let e = null;
  return async () => (e || (e = await import("@shiki/transformers")), e);
}
const Q = K();
async function Y(e) {
  if (e.length === 0)
    return [];
  const t = await Q();
  return e.map((n) => {
    const c = `transformer${n.charAt(0).toUpperCase() + n.slice(1)}`;
    return t[c]();
  });
}
function Z(e) {
  const { copy: t, copied: n } = J({ source: e.code, legacy: !0 }), c = y(() => N(["copy", { copied: n.value }]));
  function f(i) {
    t(e.code), x(
      n,
      (s) => {
        s || i.target.blur();
      },
      { once: !0 }
    );
  }
  return {
    copyButtonClick: f,
    btnClasses: c
  };
}
export {
  Y as getTransformers,
  Q as getTransformersModule,
  Z as readyCopyButton
};
