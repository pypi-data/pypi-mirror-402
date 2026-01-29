var _n = Object.defineProperty;
var bn = (n, e, t) => e in n ? _n(n, e, { enumerable: !0, configurable: !0, writable: !0, value: t }) : n[e] = t;
var f = (n, e, t) => bn(n, typeof e != "symbol" ? e + "" : e, t);
import { shallowRef as Y, shallowReadonly as Sn, toValue as H, getCurrentScope as Cn, onScopeDispose as vn, watch as It, computed as xe, getCurrentInstance as wn, onMounted as kn, unref as Rn, toRaw as xn, normalizeClass as An } from "vue";
import { getAppInfo as Nn } from "instaui";
function Et(n) {
  return Cn() ? (vn(n), !0) : !1;
}
const Xe = typeof window < "u" && typeof document < "u";
typeof WorkerGlobalScope < "u" && globalThis instanceof WorkerGlobalScope;
const Tn = Object.prototype.toString, Pn = (n) => Tn.call(n) === "[object Object]";
function In(n) {
  let e;
  function t() {
    return e || (e = n()), e;
  }
  return t.reset = async () => {
    const r = e;
    e = void 0, r && await r;
  }, t;
}
function Ie(n) {
  return Array.isArray(n) ? n : [n];
}
function En(n, e, t = {}) {
  const {
    immediate: r = !0,
    immediateCallback: s = !1
  } = t, o = Y(!1);
  let i;
  function a() {
    i && (clearTimeout(i), i = void 0);
  }
  function l() {
    o.value = !1, a();
  }
  function c(...u) {
    s && n(), a(), o.value = !0, i = setTimeout(() => {
      o.value = !1, i = void 0, n(...u);
    }, H(e));
  }
  return r && (o.value = !0, Xe && c()), Et(l), {
    isPending: Sn(o),
    start: c,
    stop: l
  };
}
function Ln(n, e, t) {
  return It(
    n,
    e,
    {
      ...t,
      immediate: !0
    }
  );
}
const On = Xe ? window : void 0, Lt = Xe ? window.navigator : void 0;
function Mn(n) {
  var e;
  const t = H(n);
  return (e = t == null ? void 0 : t.$el) != null ? e : t;
}
function Ot(...n) {
  const e = [], t = () => {
    e.forEach((a) => a()), e.length = 0;
  }, r = (a, l, c, u) => (a.addEventListener(l, c, u), () => a.removeEventListener(l, c, u)), s = xe(() => {
    const a = Ie(H(n[0])).filter((l) => l != null);
    return a.every((l) => typeof l != "string") ? a : void 0;
  }), o = Ln(
    () => {
      var a, l;
      return [
        (l = (a = s.value) == null ? void 0 : a.map((c) => Mn(c))) != null ? l : [On].filter((c) => c != null),
        Ie(H(s.value ? n[1] : n[0])),
        Ie(Rn(s.value ? n[2] : n[1])),
        // @ts-expect-error - TypeScript gets the correct types, but somehow still complains
        H(s.value ? n[3] : n[2])
      ];
    },
    ([a, l, c, u]) => {
      if (t(), !(a != null && a.length) || !(l != null && l.length) || !(c != null && c.length))
        return;
      const h = Pn(u) ? { ...u } : u;
      e.push(
        ...a.flatMap(
          (d) => l.flatMap(
            (p) => c.map((g) => r(d, p, g, h))
          )
        )
      );
    },
    { flush: "post" }
  ), i = () => {
    o(), t();
  };
  return Et(t), i;
}
function Gn() {
  const n = Y(!1), e = wn();
  return e && kn(() => {
    n.value = !0;
  }, e), n;
}
function Mt(n) {
  const e = Gn();
  return xe(() => (e.value, !!n()));
}
function at(n, e = {}) {
  const {
    controls: t = !1,
    navigator: r = Lt
  } = e, s = Mt(() => r && "permissions" in r), o = Y(), i = typeof n == "string" ? { name: n } : n, a = Y(), l = () => {
    var u, h;
    a.value = (h = (u = o.value) == null ? void 0 : u.state) != null ? h : "prompt";
  };
  Ot(o, "change", l, { passive: !0 });
  const c = In(async () => {
    if (s.value) {
      if (!o.value)
        try {
          o.value = await r.permissions.query(i);
        } catch {
          o.value = void 0;
        } finally {
          l();
        }
      if (t)
        return xn(o.value);
    }
  });
  return c(), t ? {
    state: a,
    isSupported: s,
    query: c
  } : a;
}
function Bn(n = {}) {
  const {
    navigator: e = Lt,
    read: t = !1,
    source: r,
    copiedDuring: s = 1500,
    legacy: o = !1
  } = n, i = Mt(() => e && "clipboard" in e), a = at("clipboard-read"), l = at("clipboard-write"), c = xe(() => i.value || o), u = Y(""), h = Y(!1), d = En(() => h.value = !1, s, { immediate: !1 });
  async function p() {
    let y = !(i.value && _(a.value));
    if (!y)
      try {
        u.value = await e.clipboard.readText();
      } catch {
        y = !0;
      }
    y && (u.value = S());
  }
  c.value && t && Ot(["copy", "cut"], p, { passive: !0 });
  async function g(y = H(r)) {
    if (c.value && y != null) {
      let b = !(i.value && _(l.value));
      if (!b)
        try {
          await e.clipboard.writeText(y);
        } catch {
          b = !0;
        }
      b && C(y), u.value = y, h.value = !0, d.start();
    }
  }
  function C(y) {
    const b = document.createElement("textarea");
    b.value = y ?? "", b.style.position = "absolute", b.style.opacity = "0", document.body.appendChild(b), b.select(), document.execCommand("copy"), b.remove();
  }
  function S() {
    var y, b, w;
    return (w = (b = (y = document == null ? void 0 : document.getSelection) == null ? void 0 : y.call(document)) == null ? void 0 : b.toString()) != null ? w : "";
  }
  function _(y) {
    return y === "granted" || y === "prompt";
  }
  return {
    isSupported: c,
    text: u,
    copied: h,
    copy: g
  };
}
let T = class extends Error {
  constructor(e) {
    super(e), this.name = "ShikiError";
  }
};
function Dn(n) {
  return Je(n);
}
function Je(n) {
  return Array.isArray(n) ? $n(n) : n instanceof RegExp ? n : typeof n == "object" ? jn(n) : n;
}
function $n(n) {
  let e = [];
  for (let t = 0, r = n.length; t < r; t++)
    e[t] = Je(n[t]);
  return e;
}
function jn(n) {
  let e = {};
  for (let t in n)
    e[t] = Je(n[t]);
  return e;
}
function Gt(n, ...e) {
  return e.forEach((t) => {
    for (let r in t)
      n[r] = t[r];
  }), n;
}
function Bt(n) {
  const e = ~n.lastIndexOf("/") || ~n.lastIndexOf("\\");
  return e === 0 ? n : ~e === n.length - 1 ? Bt(n.substring(0, n.length - 1)) : n.substr(~e + 1);
}
var Ee = /\$(\d+)|\${(\d+):\/(downcase|upcase)}/g, ue = class {
  static hasCaptures(n) {
    return n === null ? !1 : (Ee.lastIndex = 0, Ee.test(n));
  }
  static replaceCaptures(n, e, t) {
    return n.replace(Ee, (r, s, o, i) => {
      let a = t[parseInt(s || o, 10)];
      if (a) {
        let l = e.substring(a.start, a.end);
        for (; l[0] === "."; )
          l = l.substring(1);
        switch (i) {
          case "downcase":
            return l.toLowerCase();
          case "upcase":
            return l.toUpperCase();
          default:
            return l;
        }
      } else
        return r;
    });
  }
};
function Dt(n, e) {
  return n < e ? -1 : n > e ? 1 : 0;
}
function $t(n, e) {
  if (n === null && e === null)
    return 0;
  if (!n)
    return -1;
  if (!e)
    return 1;
  let t = n.length, r = e.length;
  if (t === r) {
    for (let s = 0; s < t; s++) {
      let o = Dt(n[s], e[s]);
      if (o !== 0)
        return o;
    }
    return 0;
  }
  return t - r;
}
function ct(n) {
  return !!(/^#[0-9a-f]{6}$/i.test(n) || /^#[0-9a-f]{8}$/i.test(n) || /^#[0-9a-f]{3}$/i.test(n) || /^#[0-9a-f]{4}$/i.test(n));
}
function jt(n) {
  return n.replace(/[\-\\\{\}\*\+\?\|\^\$\.\,\[\]\(\)\#\s]/g, "\\$&");
}
var Ft = class {
  constructor(n) {
    f(this, "cache", /* @__PURE__ */ new Map());
    this.fn = n;
  }
  get(n) {
    if (this.cache.has(n))
      return this.cache.get(n);
    const e = this.fn(n);
    return this.cache.set(n, e), e;
  }
}, ge = class {
  constructor(n, e, t) {
    f(this, "_cachedMatchRoot", new Ft(
      (n) => this._root.match(n)
    ));
    this._colorMap = n, this._defaults = e, this._root = t;
  }
  static createFromRawTheme(n, e) {
    return this.createFromParsedTheme(zn(n), e);
  }
  static createFromParsedTheme(n, e) {
    return qn(n, e);
  }
  getColorMap() {
    return this._colorMap.getColorMap();
  }
  getDefaults() {
    return this._defaults;
  }
  match(n) {
    if (n === null)
      return this._defaults;
    const e = n.scopeName, r = this._cachedMatchRoot.get(e).find(
      (s) => Fn(n.parent, s.parentScopes)
    );
    return r ? new Wt(
      r.fontStyle,
      r.foreground,
      r.background
    ) : null;
  }
}, Le = class fe {
  constructor(e, t) {
    this.parent = e, this.scopeName = t;
  }
  static push(e, t) {
    for (const r of t)
      e = new fe(e, r);
    return e;
  }
  static from(...e) {
    let t = null;
    for (let r = 0; r < e.length; r++)
      t = new fe(t, e[r]);
    return t;
  }
  push(e) {
    return new fe(this, e);
  }
  getSegments() {
    let e = this;
    const t = [];
    for (; e; )
      t.push(e.scopeName), e = e.parent;
    return t.reverse(), t;
  }
  toString() {
    return this.getSegments().join(" ");
  }
  extends(e) {
    return this === e ? !0 : this.parent === null ? !1 : this.parent.extends(e);
  }
  getExtensionIfDefined(e) {
    const t = [];
    let r = this;
    for (; r && r !== e; )
      t.push(r.scopeName), r = r.parent;
    return r === e ? t.reverse() : void 0;
  }
};
function Fn(n, e) {
  if (e.length === 0)
    return !0;
  for (let t = 0; t < e.length; t++) {
    let r = e[t], s = !1;
    if (r === ">") {
      if (t === e.length - 1)
        return !1;
      r = e[++t], s = !0;
    }
    for (; n && !Wn(n.scopeName, r); ) {
      if (s)
        return !1;
      n = n.parent;
    }
    if (!n)
      return !1;
    n = n.parent;
  }
  return !0;
}
function Wn(n, e) {
  return e === n || n.startsWith(e) && n[e.length] === ".";
}
var Wt = class {
  constructor(n, e, t) {
    this.fontStyle = n, this.foregroundId = e, this.backgroundId = t;
  }
};
function zn(n) {
  if (!n)
    return [];
  if (!n.settings || !Array.isArray(n.settings))
    return [];
  let e = n.settings, t = [], r = 0;
  for (let s = 0, o = e.length; s < o; s++) {
    let i = e[s];
    if (!i.settings)
      continue;
    let a;
    if (typeof i.scope == "string") {
      let h = i.scope;
      h = h.replace(/^[,]+/, ""), h = h.replace(/[,]+$/, ""), a = h.split(",");
    } else Array.isArray(i.scope) ? a = i.scope : a = [""];
    let l = -1;
    if (typeof i.settings.fontStyle == "string") {
      l = 0;
      let h = i.settings.fontStyle.split(" ");
      for (let d = 0, p = h.length; d < p; d++)
        switch (h[d]) {
          case "italic":
            l = l | 1;
            break;
          case "bold":
            l = l | 2;
            break;
          case "underline":
            l = l | 4;
            break;
          case "strikethrough":
            l = l | 8;
            break;
        }
    }
    let c = null;
    typeof i.settings.foreground == "string" && ct(i.settings.foreground) && (c = i.settings.foreground);
    let u = null;
    typeof i.settings.background == "string" && ct(i.settings.background) && (u = i.settings.background);
    for (let h = 0, d = a.length; h < d; h++) {
      let g = a[h].trim().split(" "), C = g[g.length - 1], S = null;
      g.length > 1 && (S = g.slice(0, g.length - 1), S.reverse()), t[r++] = new Un(
        C,
        S,
        s,
        l,
        c,
        u
      );
    }
  }
  return t;
}
var Un = class {
  constructor(n, e, t, r, s, o) {
    this.scope = n, this.parentScopes = e, this.index = t, this.fontStyle = r, this.foreground = s, this.background = o;
  }
}, I = /* @__PURE__ */ ((n) => (n[n.NotSet = -1] = "NotSet", n[n.None = 0] = "None", n[n.Italic = 1] = "Italic", n[n.Bold = 2] = "Bold", n[n.Underline = 4] = "Underline", n[n.Strikethrough = 8] = "Strikethrough", n))(I || {});
function qn(n, e) {
  n.sort((l, c) => {
    let u = Dt(l.scope, c.scope);
    return u !== 0 || (u = $t(l.parentScopes, c.parentScopes), u !== 0) ? u : l.index - c.index;
  });
  let t = 0, r = "#000000", s = "#ffffff";
  for (; n.length >= 1 && n[0].scope === ""; ) {
    let l = n.shift();
    l.fontStyle !== -1 && (t = l.fontStyle), l.foreground !== null && (r = l.foreground), l.background !== null && (s = l.background);
  }
  let o = new Hn(e), i = new Wt(t, o.getId(r), o.getId(s)), a = new Kn(new $e(0, null, -1, 0, 0), []);
  for (let l = 0, c = n.length; l < c; l++) {
    let u = n[l];
    a.insert(0, u.scope, u.parentScopes, u.fontStyle, o.getId(u.foreground), o.getId(u.background));
  }
  return new ge(o, i, a);
}
var Hn = class {
  constructor(n) {
    f(this, "_isFrozen");
    f(this, "_lastColorId");
    f(this, "_id2color");
    f(this, "_color2id");
    if (this._lastColorId = 0, this._id2color = [], this._color2id = /* @__PURE__ */ Object.create(null), Array.isArray(n)) {
      this._isFrozen = !0;
      for (let e = 0, t = n.length; e < t; e++)
        this._color2id[n[e]] = e, this._id2color[e] = n[e];
    } else
      this._isFrozen = !1;
  }
  getId(n) {
    if (n === null)
      return 0;
    n = n.toUpperCase();
    let e = this._color2id[n];
    if (e)
      return e;
    if (this._isFrozen)
      throw new Error(`Missing color in color map - ${n}`);
    return e = ++this._lastColorId, this._color2id[n] = e, this._id2color[e] = n, e;
  }
  getColorMap() {
    return this._id2color.slice(0);
  }
}, Vn = Object.freeze([]), $e = class zt {
  constructor(e, t, r, s, o) {
    f(this, "scopeDepth");
    f(this, "parentScopes");
    f(this, "fontStyle");
    f(this, "foreground");
    f(this, "background");
    this.scopeDepth = e, this.parentScopes = t || Vn, this.fontStyle = r, this.foreground = s, this.background = o;
  }
  clone() {
    return new zt(this.scopeDepth, this.parentScopes, this.fontStyle, this.foreground, this.background);
  }
  static cloneArr(e) {
    let t = [];
    for (let r = 0, s = e.length; r < s; r++)
      t[r] = e[r].clone();
    return t;
  }
  acceptOverwrite(e, t, r, s) {
    this.scopeDepth > e ? console.log("how did this happen?") : this.scopeDepth = e, t !== -1 && (this.fontStyle = t), r !== 0 && (this.foreground = r), s !== 0 && (this.background = s);
  }
}, Kn = class je {
  constructor(e, t = [], r = {}) {
    f(this, "_rulesWithParentScopes");
    this._mainRule = e, this._children = r, this._rulesWithParentScopes = t;
  }
  static _cmpBySpecificity(e, t) {
    if (e.scopeDepth !== t.scopeDepth)
      return t.scopeDepth - e.scopeDepth;
    let r = 0, s = 0;
    for (; e.parentScopes[r] === ">" && r++, t.parentScopes[s] === ">" && s++, !(r >= e.parentScopes.length || s >= t.parentScopes.length); ) {
      const o = t.parentScopes[s].length - e.parentScopes[r].length;
      if (o !== 0)
        return o;
      r++, s++;
    }
    return t.parentScopes.length - e.parentScopes.length;
  }
  match(e) {
    if (e !== "") {
      let r = e.indexOf("."), s, o;
      if (r === -1 ? (s = e, o = "") : (s = e.substring(0, r), o = e.substring(r + 1)), this._children.hasOwnProperty(s))
        return this._children[s].match(o);
    }
    const t = this._rulesWithParentScopes.concat(this._mainRule);
    return t.sort(je._cmpBySpecificity), t;
  }
  insert(e, t, r, s, o, i) {
    if (t === "") {
      this._doInsertHere(e, r, s, o, i);
      return;
    }
    let a = t.indexOf("."), l, c;
    a === -1 ? (l = t, c = "") : (l = t.substring(0, a), c = t.substring(a + 1));
    let u;
    this._children.hasOwnProperty(l) ? u = this._children[l] : (u = new je(this._mainRule.clone(), $e.cloneArr(this._rulesWithParentScopes)), this._children[l] = u), u.insert(e + 1, c, r, s, o, i);
  }
  _doInsertHere(e, t, r, s, o) {
    if (t === null) {
      this._mainRule.acceptOverwrite(e, r, s, o);
      return;
    }
    for (let i = 0, a = this._rulesWithParentScopes.length; i < a; i++) {
      let l = this._rulesWithParentScopes[i];
      if ($t(l.parentScopes, t) === 0) {
        l.acceptOverwrite(e, r, s, o);
        return;
      }
    }
    r === -1 && (r = this._mainRule.fontStyle), s === 0 && (s = this._mainRule.foreground), o === 0 && (o = this._mainRule.background), this._rulesWithParentScopes.push(new $e(e, t, r, s, o));
  }
}, X = class O {
  static toBinaryStr(e) {
    return e.toString(2).padStart(32, "0");
  }
  static print(e) {
    const t = O.getLanguageId(e), r = O.getTokenType(e), s = O.getFontStyle(e), o = O.getForeground(e), i = O.getBackground(e);
    console.log({
      languageId: t,
      tokenType: r,
      fontStyle: s,
      foreground: o,
      background: i
    });
  }
  static getLanguageId(e) {
    return (e & 255) >>> 0;
  }
  static getTokenType(e) {
    return (e & 768) >>> 8;
  }
  static containsBalancedBrackets(e) {
    return (e & 1024) !== 0;
  }
  static getFontStyle(e) {
    return (e & 30720) >>> 11;
  }
  static getForeground(e) {
    return (e & 16744448) >>> 15;
  }
  static getBackground(e) {
    return (e & 4278190080) >>> 24;
  }
  /**
   * Updates the fields in `metadata`.
   * A value of `0`, `NotSet` or `null` indicates that the corresponding field should be left as is.
   */
  static set(e, t, r, s, o, i, a) {
    let l = O.getLanguageId(e), c = O.getTokenType(e), u = O.containsBalancedBrackets(e) ? 1 : 0, h = O.getFontStyle(e), d = O.getForeground(e), p = O.getBackground(e);
    return t !== 0 && (l = t), r !== 8 && (c = r), s !== null && (u = s ? 1 : 0), o !== -1 && (h = o), i !== 0 && (d = i), a !== 0 && (p = a), (l << 0 | c << 8 | u << 10 | h << 11 | d << 15 | p << 24) >>> 0;
  }
};
function me(n, e) {
  const t = [], r = Yn(n);
  let s = r.next();
  for (; s !== null; ) {
    let l = 0;
    if (s.length === 2 && s.charAt(1) === ":") {
      switch (s.charAt(0)) {
        case "R":
          l = 1;
          break;
        case "L":
          l = -1;
          break;
        default:
          console.log(`Unknown priority ${s} in scope selector`);
      }
      s = r.next();
    }
    let c = i();
    if (t.push({ matcher: c, priority: l }), s !== ",")
      break;
    s = r.next();
  }
  return t;
  function o() {
    if (s === "-") {
      s = r.next();
      const l = o();
      return (c) => !!l && !l(c);
    }
    if (s === "(") {
      s = r.next();
      const l = a();
      return s === ")" && (s = r.next()), l;
    }
    if (ut(s)) {
      const l = [];
      do
        l.push(s), s = r.next();
      while (ut(s));
      return (c) => e(l, c);
    }
    return null;
  }
  function i() {
    const l = [];
    let c = o();
    for (; c; )
      l.push(c), c = o();
    return (u) => l.every((h) => h(u));
  }
  function a() {
    const l = [];
    let c = i();
    for (; c && (l.push(c), s === "|" || s === ","); ) {
      do
        s = r.next();
      while (s === "|" || s === ",");
      c = i();
    }
    return (u) => l.some((h) => h(u));
  }
}
function ut(n) {
  return !!n && !!n.match(/[\w\.:]+/);
}
function Yn(n) {
  let e = /([LR]:|[\w\.:][\w\.:\-]*|[\,\|\-\(\)])/g, t = e.exec(n);
  return {
    next: () => {
      if (!t)
        return null;
      const r = t[0];
      return t = e.exec(n), r;
    }
  };
}
function Ut(n) {
  typeof n.dispose == "function" && n.dispose();
}
var re = class {
  constructor(n) {
    this.scopeName = n;
  }
  toKey() {
    return this.scopeName;
  }
}, Xn = class {
  constructor(n, e) {
    this.scopeName = n, this.ruleName = e;
  }
  toKey() {
    return `${this.scopeName}#${this.ruleName}`;
  }
}, Jn = class {
  constructor() {
    f(this, "_references", []);
    f(this, "_seenReferenceKeys", /* @__PURE__ */ new Set());
    f(this, "visitedRule", /* @__PURE__ */ new Set());
  }
  get references() {
    return this._references;
  }
  add(n) {
    const e = n.toKey();
    this._seenReferenceKeys.has(e) || (this._seenReferenceKeys.add(e), this._references.push(n));
  }
}, Qn = class {
  constructor(n, e) {
    f(this, "seenFullScopeRequests", /* @__PURE__ */ new Set());
    f(this, "seenPartialScopeRequests", /* @__PURE__ */ new Set());
    f(this, "Q");
    this.repo = n, this.initialScopeName = e, this.seenFullScopeRequests.add(this.initialScopeName), this.Q = [new re(this.initialScopeName)];
  }
  processQueue() {
    const n = this.Q;
    this.Q = [];
    const e = new Jn();
    for (const t of n)
      Zn(t, this.initialScopeName, this.repo, e);
    for (const t of e.references)
      if (t instanceof re) {
        if (this.seenFullScopeRequests.has(t.scopeName))
          continue;
        this.seenFullScopeRequests.add(t.scopeName), this.Q.push(t);
      } else {
        if (this.seenFullScopeRequests.has(t.scopeName) || this.seenPartialScopeRequests.has(t.toKey()))
          continue;
        this.seenPartialScopeRequests.add(t.toKey()), this.Q.push(t);
      }
  }
};
function Zn(n, e, t, r) {
  const s = t.lookup(n.scopeName);
  if (!s) {
    if (n.scopeName === e)
      throw new Error(`No grammar provided for <${e}>`);
    return;
  }
  const o = t.lookup(e);
  n instanceof re ? pe({ baseGrammar: o, selfGrammar: s }, r) : Fe(
    n.ruleName,
    { baseGrammar: o, selfGrammar: s, repository: s.repository },
    r
  );
  const i = t.injections(n.scopeName);
  if (i)
    for (const a of i)
      r.add(new re(a));
}
function Fe(n, e, t) {
  if (e.repository && e.repository[n]) {
    const r = e.repository[n];
    ye([r], e, t);
  }
}
function pe(n, e) {
  n.selfGrammar.patterns && Array.isArray(n.selfGrammar.patterns) && ye(
    n.selfGrammar.patterns,
    { ...n, repository: n.selfGrammar.repository },
    e
  ), n.selfGrammar.injections && ye(
    Object.values(n.selfGrammar.injections),
    { ...n, repository: n.selfGrammar.repository },
    e
  );
}
function ye(n, e, t) {
  for (const r of n) {
    if (t.visitedRule.has(r))
      continue;
    t.visitedRule.add(r);
    const s = r.repository ? Gt({}, e.repository, r.repository) : e.repository;
    Array.isArray(r.patterns) && ye(r.patterns, { ...e, repository: s }, t);
    const o = r.include;
    if (!o)
      continue;
    const i = qt(o);
    switch (i.kind) {
      case 0:
        pe({ ...e, selfGrammar: e.baseGrammar }, t);
        break;
      case 1:
        pe(e, t);
        break;
      case 2:
        Fe(i.ruleName, { ...e, repository: s }, t);
        break;
      case 3:
      case 4:
        const a = i.scopeName === e.selfGrammar.scopeName ? e.selfGrammar : i.scopeName === e.baseGrammar.scopeName ? e.baseGrammar : void 0;
        if (a) {
          const l = { baseGrammar: e.baseGrammar, selfGrammar: a, repository: s };
          i.kind === 4 ? Fe(i.ruleName, l, t) : pe(l, t);
        } else
          i.kind === 4 ? t.add(new Xn(i.scopeName, i.ruleName)) : t.add(new re(i.scopeName));
        break;
    }
  }
}
var er = class {
  constructor() {
    f(this, "kind", 0);
  }
}, tr = class {
  constructor() {
    f(this, "kind", 1);
  }
}, nr = class {
  constructor(n) {
    f(this, "kind", 2);
    this.ruleName = n;
  }
}, rr = class {
  constructor(n) {
    f(this, "kind", 3);
    this.scopeName = n;
  }
}, sr = class {
  constructor(n, e) {
    f(this, "kind", 4);
    this.scopeName = n, this.ruleName = e;
  }
};
function qt(n) {
  if (n === "$base")
    return new er();
  if (n === "$self")
    return new tr();
  const e = n.indexOf("#");
  if (e === -1)
    return new rr(n);
  if (e === 0)
    return new nr(n.substring(1));
  {
    const t = n.substring(0, e), r = n.substring(e + 1);
    return new sr(t, r);
  }
}
var or = /\\(\d+)/, ht = /\\(\d+)/g, ir = -1, Ht = -2;
var le = class {
  constructor(n, e, t, r) {
    f(this, "$location");
    f(this, "id");
    f(this, "_nameIsCapturing");
    f(this, "_name");
    f(this, "_contentNameIsCapturing");
    f(this, "_contentName");
    this.$location = n, this.id = e, this._name = t || null, this._nameIsCapturing = ue.hasCaptures(this._name), this._contentName = r || null, this._contentNameIsCapturing = ue.hasCaptures(this._contentName);
  }
  get debugName() {
    const n = this.$location ? `${Bt(this.$location.filename)}:${this.$location.line}` : "unknown";
    return `${this.constructor.name}#${this.id} @ ${n}`;
  }
  getName(n, e) {
    return !this._nameIsCapturing || this._name === null || n === null || e === null ? this._name : ue.replaceCaptures(this._name, n, e);
  }
  getContentName(n, e) {
    return !this._contentNameIsCapturing || this._contentName === null ? this._contentName : ue.replaceCaptures(this._contentName, n, e);
  }
}, lr = class extends le {
  constructor(e, t, r, s, o) {
    super(e, t, r, s);
    f(this, "retokenizeCapturedWithRuleId");
    this.retokenizeCapturedWithRuleId = o;
  }
  dispose() {
  }
  collectPatterns(e, t) {
    throw new Error("Not supported!");
  }
  compile(e, t) {
    throw new Error("Not supported!");
  }
  compileAG(e, t, r, s) {
    throw new Error("Not supported!");
  }
}, ar = class extends le {
  constructor(e, t, r, s, o) {
    super(e, t, r, null);
    f(this, "_match");
    f(this, "captures");
    f(this, "_cachedCompiledPatterns");
    this._match = new se(s, this.id), this.captures = o, this._cachedCompiledPatterns = null;
  }
  dispose() {
    this._cachedCompiledPatterns && (this._cachedCompiledPatterns.dispose(), this._cachedCompiledPatterns = null);
  }
  get debugMatchRegExp() {
    return `${this._match.source}`;
  }
  collectPatterns(e, t) {
    t.push(this._match);
  }
  compile(e, t) {
    return this._getCachedCompiledPatterns(e).compile(e);
  }
  compileAG(e, t, r, s) {
    return this._getCachedCompiledPatterns(e).compileAG(e, r, s);
  }
  _getCachedCompiledPatterns(e) {
    return this._cachedCompiledPatterns || (this._cachedCompiledPatterns = new oe(), this.collectPatterns(e, this._cachedCompiledPatterns)), this._cachedCompiledPatterns;
  }
}, dt = class extends le {
  constructor(e, t, r, s, o) {
    super(e, t, r, s);
    f(this, "hasMissingPatterns");
    f(this, "patterns");
    f(this, "_cachedCompiledPatterns");
    this.patterns = o.patterns, this.hasMissingPatterns = o.hasMissingPatterns, this._cachedCompiledPatterns = null;
  }
  dispose() {
    this._cachedCompiledPatterns && (this._cachedCompiledPatterns.dispose(), this._cachedCompiledPatterns = null);
  }
  collectPatterns(e, t) {
    for (const r of this.patterns)
      e.getRule(r).collectPatterns(e, t);
  }
  compile(e, t) {
    return this._getCachedCompiledPatterns(e).compile(e);
  }
  compileAG(e, t, r, s) {
    return this._getCachedCompiledPatterns(e).compileAG(e, r, s);
  }
  _getCachedCompiledPatterns(e) {
    return this._cachedCompiledPatterns || (this._cachedCompiledPatterns = new oe(), this.collectPatterns(e, this._cachedCompiledPatterns)), this._cachedCompiledPatterns;
  }
}, We = class extends le {
  constructor(e, t, r, s, o, i, a, l, c, u) {
    super(e, t, r, s);
    f(this, "_begin");
    f(this, "beginCaptures");
    f(this, "_end");
    f(this, "endHasBackReferences");
    f(this, "endCaptures");
    f(this, "applyEndPatternLast");
    f(this, "hasMissingPatterns");
    f(this, "patterns");
    f(this, "_cachedCompiledPatterns");
    this._begin = new se(o, this.id), this.beginCaptures = i, this._end = new se(a || "￿", -1), this.endHasBackReferences = this._end.hasBackReferences, this.endCaptures = l, this.applyEndPatternLast = c || !1, this.patterns = u.patterns, this.hasMissingPatterns = u.hasMissingPatterns, this._cachedCompiledPatterns = null;
  }
  dispose() {
    this._cachedCompiledPatterns && (this._cachedCompiledPatterns.dispose(), this._cachedCompiledPatterns = null);
  }
  get debugBeginRegExp() {
    return `${this._begin.source}`;
  }
  get debugEndRegExp() {
    return `${this._end.source}`;
  }
  getEndWithResolvedBackReferences(e, t) {
    return this._end.resolveBackReferences(e, t);
  }
  collectPatterns(e, t) {
    t.push(this._begin);
  }
  compile(e, t) {
    return this._getCachedCompiledPatterns(e, t).compile(e);
  }
  compileAG(e, t, r, s) {
    return this._getCachedCompiledPatterns(e, t).compileAG(e, r, s);
  }
  _getCachedCompiledPatterns(e, t) {
    if (!this._cachedCompiledPatterns) {
      this._cachedCompiledPatterns = new oe();
      for (const r of this.patterns)
        e.getRule(r).collectPatterns(e, this._cachedCompiledPatterns);
      this.applyEndPatternLast ? this._cachedCompiledPatterns.push(this._end.hasBackReferences ? this._end.clone() : this._end) : this._cachedCompiledPatterns.unshift(this._end.hasBackReferences ? this._end.clone() : this._end);
    }
    return this._end.hasBackReferences && (this.applyEndPatternLast ? this._cachedCompiledPatterns.setSource(this._cachedCompiledPatterns.length() - 1, t) : this._cachedCompiledPatterns.setSource(0, t)), this._cachedCompiledPatterns;
  }
}, _e = class extends le {
  constructor(e, t, r, s, o, i, a, l, c) {
    super(e, t, r, s);
    f(this, "_begin");
    f(this, "beginCaptures");
    f(this, "whileCaptures");
    f(this, "_while");
    f(this, "whileHasBackReferences");
    f(this, "hasMissingPatterns");
    f(this, "patterns");
    f(this, "_cachedCompiledPatterns");
    f(this, "_cachedCompiledWhilePatterns");
    this._begin = new se(o, this.id), this.beginCaptures = i, this.whileCaptures = l, this._while = new se(a, Ht), this.whileHasBackReferences = this._while.hasBackReferences, this.patterns = c.patterns, this.hasMissingPatterns = c.hasMissingPatterns, this._cachedCompiledPatterns = null, this._cachedCompiledWhilePatterns = null;
  }
  dispose() {
    this._cachedCompiledPatterns && (this._cachedCompiledPatterns.dispose(), this._cachedCompiledPatterns = null), this._cachedCompiledWhilePatterns && (this._cachedCompiledWhilePatterns.dispose(), this._cachedCompiledWhilePatterns = null);
  }
  get debugBeginRegExp() {
    return `${this._begin.source}`;
  }
  get debugWhileRegExp() {
    return `${this._while.source}`;
  }
  getWhileWithResolvedBackReferences(e, t) {
    return this._while.resolveBackReferences(e, t);
  }
  collectPatterns(e, t) {
    t.push(this._begin);
  }
  compile(e, t) {
    return this._getCachedCompiledPatterns(e).compile(e);
  }
  compileAG(e, t, r, s) {
    return this._getCachedCompiledPatterns(e).compileAG(e, r, s);
  }
  _getCachedCompiledPatterns(e) {
    if (!this._cachedCompiledPatterns) {
      this._cachedCompiledPatterns = new oe();
      for (const t of this.patterns)
        e.getRule(t).collectPatterns(e, this._cachedCompiledPatterns);
    }
    return this._cachedCompiledPatterns;
  }
  compileWhile(e, t) {
    return this._getCachedCompiledWhilePatterns(e, t).compile(e);
  }
  compileWhileAG(e, t, r, s) {
    return this._getCachedCompiledWhilePatterns(e, t).compileAG(e, r, s);
  }
  _getCachedCompiledWhilePatterns(e, t) {
    return this._cachedCompiledWhilePatterns || (this._cachedCompiledWhilePatterns = new oe(), this._cachedCompiledWhilePatterns.push(this._while.hasBackReferences ? this._while.clone() : this._while)), this._while.hasBackReferences && this._cachedCompiledWhilePatterns.setSource(0, t || "￿"), this._cachedCompiledWhilePatterns;
  }
}, Vt = class P {
  static createCaptureRule(e, t, r, s, o) {
    return e.registerRule((i) => new lr(t, i, r, s, o));
  }
  static getCompiledRuleId(e, t, r) {
    return e.id || t.registerRule((s) => {
      if (e.id = s, e.match)
        return new ar(
          e.$vscodeTextmateLocation,
          e.id,
          e.name,
          e.match,
          P._compileCaptures(e.captures, t, r)
        );
      if (typeof e.begin > "u") {
        e.repository && (r = Gt({}, r, e.repository));
        let o = e.patterns;
        return typeof o > "u" && e.include && (o = [{ include: e.include }]), new dt(
          e.$vscodeTextmateLocation,
          e.id,
          e.name,
          e.contentName,
          P._compilePatterns(o, t, r)
        );
      }
      return e.while ? new _e(
        e.$vscodeTextmateLocation,
        e.id,
        e.name,
        e.contentName,
        e.begin,
        P._compileCaptures(e.beginCaptures || e.captures, t, r),
        e.while,
        P._compileCaptures(e.whileCaptures || e.captures, t, r),
        P._compilePatterns(e.patterns, t, r)
      ) : new We(
        e.$vscodeTextmateLocation,
        e.id,
        e.name,
        e.contentName,
        e.begin,
        P._compileCaptures(e.beginCaptures || e.captures, t, r),
        e.end,
        P._compileCaptures(e.endCaptures || e.captures, t, r),
        e.applyEndPatternLast,
        P._compilePatterns(e.patterns, t, r)
      );
    }), e.id;
  }
  static _compileCaptures(e, t, r) {
    let s = [];
    if (e) {
      let o = 0;
      for (const i in e) {
        if (i === "$vscodeTextmateLocation")
          continue;
        const a = parseInt(i, 10);
        a > o && (o = a);
      }
      for (let i = 0; i <= o; i++)
        s[i] = null;
      for (const i in e) {
        if (i === "$vscodeTextmateLocation")
          continue;
        const a = parseInt(i, 10);
        let l = 0;
        e[i].patterns && (l = P.getCompiledRuleId(e[i], t, r)), s[a] = P.createCaptureRule(t, e[i].$vscodeTextmateLocation, e[i].name, e[i].contentName, l);
      }
    }
    return s;
  }
  static _compilePatterns(e, t, r) {
    let s = [];
    if (e)
      for (let o = 0, i = e.length; o < i; o++) {
        const a = e[o];
        let l = -1;
        if (a.include) {
          const c = qt(a.include);
          switch (c.kind) {
            case 0:
            case 1:
              l = P.getCompiledRuleId(r[a.include], t, r);
              break;
            case 2:
              let u = r[c.ruleName];
              u && (l = P.getCompiledRuleId(u, t, r));
              break;
            case 3:
            case 4:
              const h = c.scopeName, d = c.kind === 4 ? c.ruleName : null, p = t.getExternalGrammar(h, r);
              if (p)
                if (d) {
                  let g = p.repository[d];
                  g && (l = P.getCompiledRuleId(g, t, p.repository));
                } else
                  l = P.getCompiledRuleId(p.repository.$self, t, p.repository);
              break;
          }
        } else
          l = P.getCompiledRuleId(a, t, r);
        if (l !== -1) {
          const c = t.getRule(l);
          let u = !1;
          if ((c instanceof dt || c instanceof We || c instanceof _e) && c.hasMissingPatterns && c.patterns.length === 0 && (u = !0), u)
            continue;
          s.push(l);
        }
      }
    return {
      patterns: s,
      hasMissingPatterns: (e ? e.length : 0) !== s.length
    };
  }
}, se = class Kt {
  constructor(e, t) {
    f(this, "source");
    f(this, "ruleId");
    f(this, "hasAnchor");
    f(this, "hasBackReferences");
    f(this, "_anchorCache");
    if (e && typeof e == "string") {
      const r = e.length;
      let s = 0, o = [], i = !1;
      for (let a = 0; a < r; a++)
        if (e.charAt(a) === "\\" && a + 1 < r) {
          const c = e.charAt(a + 1);
          c === "z" ? (o.push(e.substring(s, a)), o.push("$(?!\\n)(?<!\\n)"), s = a + 2) : (c === "A" || c === "G") && (i = !0), a++;
        }
      this.hasAnchor = i, s === 0 ? this.source = e : (o.push(e.substring(s, r)), this.source = o.join(""));
    } else
      this.hasAnchor = !1, this.source = e;
    this.hasAnchor ? this._anchorCache = this._buildAnchorCache() : this._anchorCache = null, this.ruleId = t, typeof this.source == "string" ? this.hasBackReferences = or.test(this.source) : this.hasBackReferences = !1;
  }
  clone() {
    return new Kt(this.source, this.ruleId);
  }
  setSource(e) {
    this.source !== e && (this.source = e, this.hasAnchor && (this._anchorCache = this._buildAnchorCache()));
  }
  resolveBackReferences(e, t) {
    if (typeof this.source != "string")
      throw new Error("This method should only be called if the source is a string");
    let r = t.map((s) => e.substring(s.start, s.end));
    return ht.lastIndex = 0, this.source.replace(ht, (s, o) => jt(r[parseInt(o, 10)] || ""));
  }
  _buildAnchorCache() {
    if (typeof this.source != "string")
      throw new Error("This method should only be called if the source is a string");
    let e = [], t = [], r = [], s = [], o, i, a, l;
    for (o = 0, i = this.source.length; o < i; o++)
      a = this.source.charAt(o), e[o] = a, t[o] = a, r[o] = a, s[o] = a, a === "\\" && o + 1 < i && (l = this.source.charAt(o + 1), l === "A" ? (e[o + 1] = "￿", t[o + 1] = "￿", r[o + 1] = "A", s[o + 1] = "A") : l === "G" ? (e[o + 1] = "￿", t[o + 1] = "G", r[o + 1] = "￿", s[o + 1] = "G") : (e[o + 1] = l, t[o + 1] = l, r[o + 1] = l, s[o + 1] = l), o++);
    return {
      A0_G0: e.join(""),
      A0_G1: t.join(""),
      A1_G0: r.join(""),
      A1_G1: s.join("")
    };
  }
  resolveAnchors(e, t) {
    return !this.hasAnchor || !this._anchorCache || typeof this.source != "string" ? this.source : e ? t ? this._anchorCache.A1_G1 : this._anchorCache.A1_G0 : t ? this._anchorCache.A0_G1 : this._anchorCache.A0_G0;
  }
}, oe = class {
  constructor() {
    f(this, "_items");
    f(this, "_hasAnchors");
    f(this, "_cached");
    f(this, "_anchorCache");
    this._items = [], this._hasAnchors = !1, this._cached = null, this._anchorCache = {
      A0_G0: null,
      A0_G1: null,
      A1_G0: null,
      A1_G1: null
    };
  }
  dispose() {
    this._disposeCaches();
  }
  _disposeCaches() {
    this._cached && (this._cached.dispose(), this._cached = null), this._anchorCache.A0_G0 && (this._anchorCache.A0_G0.dispose(), this._anchorCache.A0_G0 = null), this._anchorCache.A0_G1 && (this._anchorCache.A0_G1.dispose(), this._anchorCache.A0_G1 = null), this._anchorCache.A1_G0 && (this._anchorCache.A1_G0.dispose(), this._anchorCache.A1_G0 = null), this._anchorCache.A1_G1 && (this._anchorCache.A1_G1.dispose(), this._anchorCache.A1_G1 = null);
  }
  push(n) {
    this._items.push(n), this._hasAnchors = this._hasAnchors || n.hasAnchor;
  }
  unshift(n) {
    this._items.unshift(n), this._hasAnchors = this._hasAnchors || n.hasAnchor;
  }
  length() {
    return this._items.length;
  }
  setSource(n, e) {
    this._items[n].source !== e && (this._disposeCaches(), this._items[n].setSource(e));
  }
  compile(n) {
    if (!this._cached) {
      let e = this._items.map((t) => t.source);
      this._cached = new ft(n, e, this._items.map((t) => t.ruleId));
    }
    return this._cached;
  }
  compileAG(n, e, t) {
    return this._hasAnchors ? e ? t ? (this._anchorCache.A1_G1 || (this._anchorCache.A1_G1 = this._resolveAnchors(n, e, t)), this._anchorCache.A1_G1) : (this._anchorCache.A1_G0 || (this._anchorCache.A1_G0 = this._resolveAnchors(n, e, t)), this._anchorCache.A1_G0) : t ? (this._anchorCache.A0_G1 || (this._anchorCache.A0_G1 = this._resolveAnchors(n, e, t)), this._anchorCache.A0_G1) : (this._anchorCache.A0_G0 || (this._anchorCache.A0_G0 = this._resolveAnchors(n, e, t)), this._anchorCache.A0_G0) : this.compile(n);
  }
  _resolveAnchors(n, e, t) {
    let r = this._items.map((s) => s.resolveAnchors(e, t));
    return new ft(n, r, this._items.map((s) => s.ruleId));
  }
}, ft = class {
  constructor(n, e, t) {
    f(this, "scanner");
    this.regExps = e, this.rules = t, this.scanner = n.createOnigScanner(e);
  }
  dispose() {
    typeof this.scanner.dispose == "function" && this.scanner.dispose();
  }
  toString() {
    const n = [];
    for (let e = 0, t = this.rules.length; e < t; e++)
      n.push("   - " + this.rules[e] + ": " + this.regExps[e]);
    return n.join(`
`);
  }
  findNextMatchSync(n, e, t) {
    const r = this.scanner.findNextMatchSync(n, e, t);
    return r ? {
      ruleId: this.rules[r.index],
      captureIndices: r.captureIndices
    } : null;
  }
}, Oe = class {
  constructor(n, e) {
    this.languageId = n, this.tokenType = e;
  }
}, j, cr = (j = class {
  constructor(e, t) {
    f(this, "_defaultAttributes");
    f(this, "_embeddedLanguagesMatcher");
    f(this, "_getBasicScopeAttributes", new Ft((e) => {
      const t = this._scopeToLanguage(e), r = this._toStandardTokenType(e);
      return new Oe(t, r);
    }));
    this._defaultAttributes = new Oe(
      e,
      8
      /* NotSet */
    ), this._embeddedLanguagesMatcher = new ur(Object.entries(t || {}));
  }
  getDefaultAttributes() {
    return this._defaultAttributes;
  }
  getBasicScopeAttributes(e) {
    return e === null ? j._NULL_SCOPE_METADATA : this._getBasicScopeAttributes.get(e);
  }
  /**
   * Given a produced TM scope, return the language that token describes or null if unknown.
   * e.g. source.html => html, source.css.embedded.html => css, punctuation.definition.tag.html => null
   */
  _scopeToLanguage(e) {
    return this._embeddedLanguagesMatcher.match(e) || 0;
  }
  _toStandardTokenType(e) {
    const t = e.match(j.STANDARD_TOKEN_TYPE_REGEXP);
    if (!t)
      return 8;
    switch (t[1]) {
      case "comment":
        return 1;
      case "string":
        return 2;
      case "regex":
        return 3;
      case "meta.embedded":
        return 0;
    }
    throw new Error("Unexpected match for standard token type!");
  }
}, f(j, "_NULL_SCOPE_METADATA", new Oe(0, 0)), f(j, "STANDARD_TOKEN_TYPE_REGEXP", /\b(comment|string|regex|meta\.embedded)\b/), j), ur = class {
  constructor(n) {
    f(this, "values");
    f(this, "scopesRegExp");
    if (n.length === 0)
      this.values = null, this.scopesRegExp = null;
    else {
      this.values = new Map(n);
      const e = n.map(
        ([t, r]) => jt(t)
      );
      e.sort(), e.reverse(), this.scopesRegExp = new RegExp(
        `^((${e.join(")|(")}))($|\\.)`,
        ""
      );
    }
  }
  match(n) {
    if (!this.scopesRegExp)
      return;
    const e = n.match(this.scopesRegExp);
    if (e)
      return this.values.get(e[1]);
  }
};
typeof process < "u" && process.env.VSCODE_TEXTMATE_DEBUG;
var pt = class {
  constructor(n, e) {
    this.stack = n, this.stoppedEarly = e;
  }
};
function Yt(n, e, t, r, s, o, i, a) {
  const l = e.content.length;
  let c = !1, u = -1;
  if (i) {
    const p = hr(
      n,
      e,
      t,
      r,
      s,
      o
    );
    s = p.stack, r = p.linePos, t = p.isFirstLine, u = p.anchorPosition;
  }
  const h = Date.now();
  for (; !c; ) {
    if (a !== 0 && Date.now() - h > a)
      return new pt(s, !0);
    d();
  }
  return new pt(s, !1);
  function d() {
    const p = dr(
      n,
      e,
      t,
      r,
      s,
      u
    );
    if (!p) {
      o.produce(s, l), c = !0;
      return;
    }
    const g = p.captureIndices, C = p.matchedRuleId, S = g && g.length > 0 ? g[0].end > r : !1;
    if (C === ir) {
      const _ = s.getRule(n);
      o.produce(s, g[0].start), s = s.withContentNameScopesList(s.nameScopesList), te(
        n,
        e,
        t,
        s,
        o,
        _.endCaptures,
        g
      ), o.produce(s, g[0].end);
      const y = s;
      if (s = s.parent, u = y.getAnchorPos(), !S && y.getEnterPos() === r) {
        s = y, o.produce(s, l), c = !0;
        return;
      }
    } else {
      const _ = n.getRule(C);
      o.produce(s, g[0].start);
      const y = s, b = _.getName(e.content, g), w = s.contentNameScopesList.pushAttributed(
        b,
        n
      );
      if (s = s.push(
        C,
        r,
        u,
        g[0].end === l,
        null,
        w,
        w
      ), _ instanceof We) {
        const R = _;
        te(
          n,
          e,
          t,
          s,
          o,
          R.beginCaptures,
          g
        ), o.produce(s, g[0].end), u = g[0].end;
        const G = R.getContentName(
          e.content,
          g
        ), N = w.pushAttributed(
          G,
          n
        );
        if (s = s.withContentNameScopesList(N), R.endHasBackReferences && (s = s.withEndRule(
          R.getEndWithResolvedBackReferences(
            e.content,
            g
          )
        )), !S && y.hasSameRuleAs(s)) {
          s = s.pop(), o.produce(s, l), c = !0;
          return;
        }
      } else if (_ instanceof _e) {
        const R = _;
        te(
          n,
          e,
          t,
          s,
          o,
          R.beginCaptures,
          g
        ), o.produce(s, g[0].end), u = g[0].end;
        const G = R.getContentName(
          e.content,
          g
        ), N = w.pushAttributed(
          G,
          n
        );
        if (s = s.withContentNameScopesList(N), R.whileHasBackReferences && (s = s.withEndRule(
          R.getWhileWithResolvedBackReferences(
            e.content,
            g
          )
        )), !S && y.hasSameRuleAs(s)) {
          s = s.pop(), o.produce(s, l), c = !0;
          return;
        }
      } else if (te(
        n,
        e,
        t,
        s,
        o,
        _.captures,
        g
      ), o.produce(s, g[0].end), s = s.pop(), !S) {
        s = s.safePop(), o.produce(s, l), c = !0;
        return;
      }
    }
    g[0].end > r && (r = g[0].end, t = !1);
  }
}
function hr(n, e, t, r, s, o) {
  let i = s.beginRuleCapturedEOL ? 0 : -1;
  const a = [];
  for (let l = s; l; l = l.pop()) {
    const c = l.getRule(n);
    c instanceof _e && a.push({
      rule: c,
      stack: l
    });
  }
  for (let l = a.pop(); l; l = a.pop()) {
    const { ruleScanner: c, findOptions: u } = gr(l.rule, n, l.stack.endRule, t, r === i), h = c.findNextMatchSync(e, r, u);
    if (h) {
      if (h.ruleId !== Ht) {
        s = l.stack.pop();
        break;
      }
      h.captureIndices && h.captureIndices.length && (o.produce(l.stack, h.captureIndices[0].start), te(n, e, t, l.stack, o, l.rule.whileCaptures, h.captureIndices), o.produce(l.stack, h.captureIndices[0].end), i = h.captureIndices[0].end, h.captureIndices[0].end > r && (r = h.captureIndices[0].end, t = !1));
    } else {
      s = l.stack.pop();
      break;
    }
  }
  return { stack: s, linePos: r, anchorPosition: i, isFirstLine: t };
}
function dr(n, e, t, r, s, o) {
  const i = fr(n, e, t, r, s, o), a = n.getInjections();
  if (a.length === 0)
    return i;
  const l = pr(a, n, e, t, r, s, o);
  if (!l)
    return i;
  if (!i)
    return l;
  const c = i.captureIndices[0].start, u = l.captureIndices[0].start;
  return u < c || l.priorityMatch && u === c ? l : i;
}
function fr(n, e, t, r, s, o) {
  const i = s.getRule(n), { ruleScanner: a, findOptions: l } = Xt(i, n, s.endRule, t, r === o), c = a.findNextMatchSync(e, r, l);
  return c ? {
    captureIndices: c.captureIndices,
    matchedRuleId: c.ruleId
  } : null;
}
function pr(n, e, t, r, s, o, i) {
  let a = Number.MAX_VALUE, l = null, c, u = 0;
  const h = o.contentNameScopesList.getScopeNames();
  for (let d = 0, p = n.length; d < p; d++) {
    const g = n[d];
    if (!g.matcher(h))
      continue;
    const C = e.getRule(g.ruleId), { ruleScanner: S, findOptions: _ } = Xt(C, e, null, r, s === i), y = S.findNextMatchSync(t, s, _);
    if (!y)
      continue;
    const b = y.captureIndices[0].start;
    if (!(b >= a) && (a = b, l = y.captureIndices, c = y.ruleId, u = g.priority, a === s))
      break;
  }
  return l ? {
    priorityMatch: u === -1,
    captureIndices: l,
    matchedRuleId: c
  } : null;
}
function Xt(n, e, t, r, s) {
  return {
    ruleScanner: n.compileAG(e, t, r, s),
    findOptions: 0
    /* None */
  };
}
function gr(n, e, t, r, s) {
  return {
    ruleScanner: n.compileWhileAG(e, t, r, s),
    findOptions: 0
    /* None */
  };
}
function te(n, e, t, r, s, o, i) {
  if (o.length === 0)
    return;
  const a = e.content, l = Math.min(o.length, i.length), c = [], u = i[0].end;
  for (let h = 0; h < l; h++) {
    const d = o[h];
    if (d === null)
      continue;
    const p = i[h];
    if (p.length === 0)
      continue;
    if (p.start > u)
      break;
    for (; c.length > 0 && c[c.length - 1].endPos <= p.start; )
      s.produceFromScopes(c[c.length - 1].scopes, c[c.length - 1].endPos), c.pop();
    if (c.length > 0 ? s.produceFromScopes(c[c.length - 1].scopes, p.start) : s.produce(r, p.start), d.retokenizeCapturedWithRuleId) {
      const C = d.getName(a, i), S = r.contentNameScopesList.pushAttributed(C, n), _ = d.getContentName(a, i), y = S.pushAttributed(_, n), b = r.push(d.retokenizeCapturedWithRuleId, p.start, -1, !1, null, S, y), w = n.createOnigString(a.substring(0, p.end));
      Yt(
        n,
        w,
        t && p.start === 0,
        p.start,
        b,
        s,
        !1,
        /* no time limit */
        0
      ), Ut(w);
      continue;
    }
    const g = d.getName(a, i);
    if (g !== null) {
      const S = (c.length > 0 ? c[c.length - 1].scopes : r.contentNameScopesList).pushAttributed(g, n);
      c.push(new mr(S, p.end));
    }
  }
  for (; c.length > 0; )
    s.produceFromScopes(c[c.length - 1].scopes, c[c.length - 1].endPos), c.pop();
}
var mr = class {
  constructor(n, e) {
    f(this, "scopes");
    f(this, "endPos");
    this.scopes = n, this.endPos = e;
  }
};
function yr(n, e, t, r, s, o, i, a) {
  return new br(
    n,
    e,
    t,
    r,
    s,
    o,
    i,
    a
  );
}
function gt(n, e, t, r, s) {
  const o = me(e, be), i = Vt.getCompiledRuleId(t, r, s.repository);
  for (const a of o)
    n.push({
      debugSelector: e,
      matcher: a.matcher,
      ruleId: i,
      grammar: s,
      priority: a.priority
    });
}
function be(n, e) {
  if (e.length < n.length)
    return !1;
  let t = 0;
  return n.every((r) => {
    for (let s = t; s < e.length; s++)
      if (_r(e[s], r))
        return t = s + 1, !0;
    return !1;
  });
}
function _r(n, e) {
  if (!n)
    return !1;
  if (n === e)
    return !0;
  const t = e.length;
  return n.length > t && n.substr(0, t) === e && n[t] === ".";
}
var br = class {
  constructor(n, e, t, r, s, o, i, a) {
    f(this, "_rootId");
    f(this, "_lastRuleId");
    f(this, "_ruleId2desc");
    f(this, "_includedGrammars");
    f(this, "_grammarRepository");
    f(this, "_grammar");
    f(this, "_injections");
    f(this, "_basicScopeAttributesProvider");
    f(this, "_tokenTypeMatchers");
    if (this._rootScopeName = n, this.balancedBracketSelectors = o, this._onigLib = a, this._basicScopeAttributesProvider = new cr(
      t,
      r
    ), this._rootId = -1, this._lastRuleId = 0, this._ruleId2desc = [null], this._includedGrammars = {}, this._grammarRepository = i, this._grammar = mt(e, null), this._injections = null, this._tokenTypeMatchers = [], s)
      for (const l of Object.keys(s)) {
        const c = me(l, be);
        for (const u of c)
          this._tokenTypeMatchers.push({
            matcher: u.matcher,
            type: s[l]
          });
      }
  }
  get themeProvider() {
    return this._grammarRepository;
  }
  dispose() {
    for (const n of this._ruleId2desc)
      n && n.dispose();
  }
  createOnigScanner(n) {
    return this._onigLib.createOnigScanner(n);
  }
  createOnigString(n) {
    return this._onigLib.createOnigString(n);
  }
  getMetadataForScope(n) {
    return this._basicScopeAttributesProvider.getBasicScopeAttributes(n);
  }
  _collectInjections() {
    const n = {
      lookup: (s) => s === this._rootScopeName ? this._grammar : this.getExternalGrammar(s),
      injections: (s) => this._grammarRepository.injections(s)
    }, e = [], t = this._rootScopeName, r = n.lookup(t);
    if (r) {
      const s = r.injections;
      if (s)
        for (let i in s)
          gt(
            e,
            i,
            s[i],
            this,
            r
          );
      const o = this._grammarRepository.injections(t);
      o && o.forEach((i) => {
        const a = this.getExternalGrammar(i);
        if (a) {
          const l = a.injectionSelector;
          l && gt(
            e,
            l,
            a,
            this,
            a
          );
        }
      });
    }
    return e.sort((s, o) => s.priority - o.priority), e;
  }
  getInjections() {
    return this._injections === null && (this._injections = this._collectInjections()), this._injections;
  }
  registerRule(n) {
    const e = ++this._lastRuleId, t = n(e);
    return this._ruleId2desc[e] = t, t;
  }
  getRule(n) {
    return this._ruleId2desc[n];
  }
  getExternalGrammar(n, e) {
    if (this._includedGrammars[n])
      return this._includedGrammars[n];
    if (this._grammarRepository) {
      const t = this._grammarRepository.lookup(n);
      if (t)
        return this._includedGrammars[n] = mt(
          t,
          e && e.$base
        ), this._includedGrammars[n];
    }
  }
  tokenizeLine(n, e, t = 0) {
    const r = this._tokenize(n, e, !1, t);
    return {
      tokens: r.lineTokens.getResult(r.ruleStack, r.lineLength),
      ruleStack: r.ruleStack,
      stoppedEarly: r.stoppedEarly
    };
  }
  tokenizeLine2(n, e, t = 0) {
    const r = this._tokenize(n, e, !0, t);
    return {
      tokens: r.lineTokens.getBinaryResult(r.ruleStack, r.lineLength),
      ruleStack: r.ruleStack,
      stoppedEarly: r.stoppedEarly
    };
  }
  _tokenize(n, e, t, r) {
    this._rootId === -1 && (this._rootId = Vt.getCompiledRuleId(
      this._grammar.repository.$self,
      this,
      this._grammar.repository
    ), this.getInjections());
    let s;
    if (!e || e === ze.NULL) {
      s = !0;
      const c = this._basicScopeAttributesProvider.getDefaultAttributes(), u = this.themeProvider.getDefaults(), h = X.set(
        0,
        c.languageId,
        c.tokenType,
        null,
        u.fontStyle,
        u.foregroundId,
        u.backgroundId
      ), d = this.getRule(this._rootId).getName(
        null,
        null
      );
      let p;
      d ? p = ne.createRootAndLookUpScopeName(
        d,
        h,
        this
      ) : p = ne.createRoot(
        "unknown",
        h
      ), e = new ze(
        null,
        this._rootId,
        -1,
        -1,
        !1,
        null,
        p,
        p
      );
    } else
      s = !1, e.reset();
    n = n + `
`;
    const o = this.createOnigString(n), i = o.content.length, a = new Cr(
      t,
      n,
      this._tokenTypeMatchers,
      this.balancedBracketSelectors
    ), l = Yt(
      this,
      o,
      s,
      0,
      e,
      a,
      !0,
      r
    );
    return Ut(o), {
      lineLength: i,
      lineTokens: a,
      ruleStack: l.stack,
      stoppedEarly: l.stoppedEarly
    };
  }
};
function mt(n, e) {
  return n = Dn(n), n.repository = n.repository || {}, n.repository.$self = {
    $vscodeTextmateLocation: n.$vscodeTextmateLocation,
    patterns: n.patterns,
    name: n.scopeName
  }, n.repository.$base = e || n.repository.$self, n;
}
var ne = class B {
  /**
   * Invariant:
   * ```
   * if (parent && !scopePath.extends(parent.scopePath)) {
   * 	throw new Error();
   * }
   * ```
   */
  constructor(e, t, r) {
    this.parent = e, this.scopePath = t, this.tokenAttributes = r;
  }
  static fromExtension(e, t) {
    let r = e, s = (e == null ? void 0 : e.scopePath) ?? null;
    for (const o of t)
      s = Le.push(s, o.scopeNames), r = new B(r, s, o.encodedTokenAttributes);
    return r;
  }
  static createRoot(e, t) {
    return new B(null, new Le(null, e), t);
  }
  static createRootAndLookUpScopeName(e, t, r) {
    const s = r.getMetadataForScope(e), o = new Le(null, e), i = r.themeProvider.themeMatch(o), a = B.mergeAttributes(
      t,
      s,
      i
    );
    return new B(null, o, a);
  }
  get scopeName() {
    return this.scopePath.scopeName;
  }
  toString() {
    return this.getScopeNames().join(" ");
  }
  equals(e) {
    return B.equals(this, e);
  }
  static equals(e, t) {
    do {
      if (e === t || !e && !t)
        return !0;
      if (!e || !t || e.scopeName !== t.scopeName || e.tokenAttributes !== t.tokenAttributes)
        return !1;
      e = e.parent, t = t.parent;
    } while (!0);
  }
  static mergeAttributes(e, t, r) {
    let s = -1, o = 0, i = 0;
    return r !== null && (s = r.fontStyle, o = r.foregroundId, i = r.backgroundId), X.set(
      e,
      t.languageId,
      t.tokenType,
      null,
      s,
      o,
      i
    );
  }
  pushAttributed(e, t) {
    if (e === null)
      return this;
    if (e.indexOf(" ") === -1)
      return B._pushAttributed(this, e, t);
    const r = e.split(/ /g);
    let s = this;
    for (const o of r)
      s = B._pushAttributed(s, o, t);
    return s;
  }
  static _pushAttributed(e, t, r) {
    const s = r.getMetadataForScope(t), o = e.scopePath.push(t), i = r.themeProvider.themeMatch(o), a = B.mergeAttributes(
      e.tokenAttributes,
      s,
      i
    );
    return new B(e, o, a);
  }
  getScopeNames() {
    return this.scopePath.getSegments();
  }
  getExtensionIfDefined(e) {
    var s;
    const t = [];
    let r = this;
    for (; r && r !== e; )
      t.push({
        encodedTokenAttributes: r.tokenAttributes,
        scopeNames: r.scopePath.getExtensionIfDefined(((s = r.parent) == null ? void 0 : s.scopePath) ?? null)
      }), r = r.parent;
    return r === e ? t.reverse() : void 0;
  }
}, M, ze = (M = class {
  /**
   * Invariant:
   * ```
   * if (contentNameScopesList !== nameScopesList && contentNameScopesList?.parent !== nameScopesList) {
   * 	throw new Error();
   * }
   * if (this.parent && !nameScopesList.extends(this.parent.contentNameScopesList)) {
   * 	throw new Error();
   * }
   * ```
   */
  constructor(e, t, r, s, o, i, a, l) {
    f(this, "_stackElementBrand");
    /**
     * The position on the current line where this state was pushed.
     * This is relevant only while tokenizing a line, to detect endless loops.
     * Its value is meaningless across lines.
     */
    f(this, "_enterPos");
    /**
     * The captured anchor position when this stack element was pushed.
     * This is relevant only while tokenizing a line, to restore the anchor position when popping.
     * Its value is meaningless across lines.
     */
    f(this, "_anchorPos");
    /**
     * The depth of the stack.
     */
    f(this, "depth");
    this.parent = e, this.ruleId = t, this.beginRuleCapturedEOL = o, this.endRule = i, this.nameScopesList = a, this.contentNameScopesList = l, this.depth = this.parent ? this.parent.depth + 1 : 1, this._enterPos = r, this._anchorPos = s;
  }
  equals(e) {
    return e === null ? !1 : M._equals(this, e);
  }
  static _equals(e, t) {
    return e === t ? !0 : this._structuralEquals(e, t) ? ne.equals(e.contentNameScopesList, t.contentNameScopesList) : !1;
  }
  /**
   * A structural equals check. Does not take into account `scopes`.
   */
  static _structuralEquals(e, t) {
    do {
      if (e === t || !e && !t)
        return !0;
      if (!e || !t || e.depth !== t.depth || e.ruleId !== t.ruleId || e.endRule !== t.endRule)
        return !1;
      e = e.parent, t = t.parent;
    } while (!0);
  }
  clone() {
    return this;
  }
  static _reset(e) {
    for (; e; )
      e._enterPos = -1, e._anchorPos = -1, e = e.parent;
  }
  reset() {
    M._reset(this);
  }
  pop() {
    return this.parent;
  }
  safePop() {
    return this.parent ? this.parent : this;
  }
  push(e, t, r, s, o, i, a) {
    return new M(
      this,
      e,
      t,
      r,
      s,
      o,
      i,
      a
    );
  }
  getEnterPos() {
    return this._enterPos;
  }
  getAnchorPos() {
    return this._anchorPos;
  }
  getRule(e) {
    return e.getRule(this.ruleId);
  }
  toString() {
    const e = [];
    return this._writeString(e, 0), "[" + e.join(",") + "]";
  }
  _writeString(e, t) {
    var r, s;
    return this.parent && (t = this.parent._writeString(e, t)), e[t++] = `(${this.ruleId}, ${(r = this.nameScopesList) == null ? void 0 : r.toString()}, ${(s = this.contentNameScopesList) == null ? void 0 : s.toString()})`, t;
  }
  withContentNameScopesList(e) {
    return this.contentNameScopesList === e ? this : this.parent.push(
      this.ruleId,
      this._enterPos,
      this._anchorPos,
      this.beginRuleCapturedEOL,
      this.endRule,
      this.nameScopesList,
      e
    );
  }
  withEndRule(e) {
    return this.endRule === e ? this : new M(
      this.parent,
      this.ruleId,
      this._enterPos,
      this._anchorPos,
      this.beginRuleCapturedEOL,
      e,
      this.nameScopesList,
      this.contentNameScopesList
    );
  }
  // Used to warn of endless loops
  hasSameRuleAs(e) {
    let t = this;
    for (; t && t._enterPos === e._enterPos; ) {
      if (t.ruleId === e.ruleId)
        return !0;
      t = t.parent;
    }
    return !1;
  }
  toStateStackFrame() {
    var e, t, r;
    return {
      ruleId: this.ruleId,
      beginRuleCapturedEOL: this.beginRuleCapturedEOL,
      endRule: this.endRule,
      nameScopesList: ((t = this.nameScopesList) == null ? void 0 : t.getExtensionIfDefined(((e = this.parent) == null ? void 0 : e.nameScopesList) ?? null)) ?? [],
      contentNameScopesList: ((r = this.contentNameScopesList) == null ? void 0 : r.getExtensionIfDefined(this.nameScopesList)) ?? []
    };
  }
  static pushFrame(e, t) {
    const r = ne.fromExtension((e == null ? void 0 : e.nameScopesList) ?? null, t.nameScopesList);
    return new M(
      e,
      t.ruleId,
      t.enterPos ?? -1,
      t.anchorPos ?? -1,
      t.beginRuleCapturedEOL,
      t.endRule,
      r,
      ne.fromExtension(r, t.contentNameScopesList)
    );
  }
}, // TODO remove me
f(M, "NULL", new M(
  null,
  0,
  0,
  0,
  !1,
  null,
  null,
  null
)), M), Sr = class {
  constructor(n, e) {
    f(this, "balancedBracketScopes");
    f(this, "unbalancedBracketScopes");
    f(this, "allowAny", !1);
    this.balancedBracketScopes = n.flatMap(
      (t) => t === "*" ? (this.allowAny = !0, []) : me(t, be).map((r) => r.matcher)
    ), this.unbalancedBracketScopes = e.flatMap(
      (t) => me(t, be).map((r) => r.matcher)
    );
  }
  get matchesAlways() {
    return this.allowAny && this.unbalancedBracketScopes.length === 0;
  }
  get matchesNever() {
    return this.balancedBracketScopes.length === 0 && !this.allowAny;
  }
  match(n) {
    for (const e of this.unbalancedBracketScopes)
      if (e(n))
        return !1;
    for (const e of this.balancedBracketScopes)
      if (e(n))
        return !0;
    return this.allowAny;
  }
}, Cr = class {
  constructor(n, e, t, r) {
    f(this, "_emitBinaryTokens");
    /**
     * defined only if `false`.
     */
    f(this, "_lineText");
    /**
     * used only if `_emitBinaryTokens` is false.
     */
    f(this, "_tokens");
    /**
     * used only if `_emitBinaryTokens` is true.
     */
    f(this, "_binaryTokens");
    f(this, "_lastTokenEndIndex");
    f(this, "_tokenTypeOverrides");
    this.balancedBracketSelectors = r, this._emitBinaryTokens = n, this._tokenTypeOverrides = t, this._lineText = null, this._tokens = [], this._binaryTokens = [], this._lastTokenEndIndex = 0;
  }
  produce(n, e) {
    this.produceFromScopes(n.contentNameScopesList, e);
  }
  produceFromScopes(n, e) {
    var r;
    if (this._lastTokenEndIndex >= e)
      return;
    if (this._emitBinaryTokens) {
      let s = (n == null ? void 0 : n.tokenAttributes) ?? 0, o = !1;
      if ((r = this.balancedBracketSelectors) != null && r.matchesAlways && (o = !0), this._tokenTypeOverrides.length > 0 || this.balancedBracketSelectors && !this.balancedBracketSelectors.matchesAlways && !this.balancedBracketSelectors.matchesNever) {
        const i = (n == null ? void 0 : n.getScopeNames()) ?? [];
        for (const a of this._tokenTypeOverrides)
          a.matcher(i) && (s = X.set(
            s,
            0,
            a.type,
            null,
            -1,
            0,
            0
          ));
        this.balancedBracketSelectors && (o = this.balancedBracketSelectors.match(i));
      }
      if (o && (s = X.set(
        s,
        0,
        8,
        o,
        -1,
        0,
        0
      )), this._binaryTokens.length > 0 && this._binaryTokens[this._binaryTokens.length - 1] === s) {
        this._lastTokenEndIndex = e;
        return;
      }
      this._binaryTokens.push(this._lastTokenEndIndex), this._binaryTokens.push(s), this._lastTokenEndIndex = e;
      return;
    }
    const t = (n == null ? void 0 : n.getScopeNames()) ?? [];
    this._tokens.push({
      startIndex: this._lastTokenEndIndex,
      endIndex: e,
      // value: lineText.substring(lastTokenEndIndex, endIndex),
      scopes: t
    }), this._lastTokenEndIndex = e;
  }
  getResult(n, e) {
    return this._tokens.length > 0 && this._tokens[this._tokens.length - 1].startIndex === e - 1 && this._tokens.pop(), this._tokens.length === 0 && (this._lastTokenEndIndex = -1, this.produce(n, e), this._tokens[this._tokens.length - 1].startIndex = 0), this._tokens;
  }
  getBinaryResult(n, e) {
    this._binaryTokens.length > 0 && this._binaryTokens[this._binaryTokens.length - 2] === e - 1 && (this._binaryTokens.pop(), this._binaryTokens.pop()), this._binaryTokens.length === 0 && (this._lastTokenEndIndex = -1, this.produce(n, e), this._binaryTokens[this._binaryTokens.length - 2] = 0);
    const t = new Uint32Array(this._binaryTokens.length);
    for (let r = 0, s = this._binaryTokens.length; r < s; r++)
      t[r] = this._binaryTokens[r];
    return t;
  }
}, vr = class {
  constructor(n, e) {
    f(this, "_grammars", /* @__PURE__ */ new Map());
    f(this, "_rawGrammars", /* @__PURE__ */ new Map());
    f(this, "_injectionGrammars", /* @__PURE__ */ new Map());
    f(this, "_theme");
    this._onigLib = e, this._theme = n;
  }
  dispose() {
    for (const n of this._grammars.values())
      n.dispose();
  }
  setTheme(n) {
    this._theme = n;
  }
  getColorMap() {
    return this._theme.getColorMap();
  }
  /**
   * Add `grammar` to registry and return a list of referenced scope names
   */
  addGrammar(n, e) {
    this._rawGrammars.set(n.scopeName, n), e && this._injectionGrammars.set(n.scopeName, e);
  }
  /**
   * Lookup a raw grammar.
   */
  lookup(n) {
    return this._rawGrammars.get(n);
  }
  /**
   * Returns the injections for the given grammar
   */
  injections(n) {
    return this._injectionGrammars.get(n);
  }
  /**
   * Get the default theme settings
   */
  getDefaults() {
    return this._theme.getDefaults();
  }
  /**
   * Match a scope in the theme.
   */
  themeMatch(n) {
    return this._theme.match(n);
  }
  /**
   * Lookup a grammar.
   */
  grammarForScopeName(n, e, t, r, s) {
    if (!this._grammars.has(n)) {
      let o = this._rawGrammars.get(n);
      if (!o)
        return null;
      this._grammars.set(n, yr(
        n,
        o,
        e,
        t,
        r,
        s,
        this,
        this._onigLib
      ));
    }
    return this._grammars.get(n);
  }
}, wr = class {
  constructor(e) {
    f(this, "_options");
    f(this, "_syncRegistry");
    f(this, "_ensureGrammarCache");
    this._options = e, this._syncRegistry = new vr(
      ge.createFromRawTheme(e.theme, e.colorMap),
      e.onigLib
    ), this._ensureGrammarCache = /* @__PURE__ */ new Map();
  }
  dispose() {
    this._syncRegistry.dispose();
  }
  /**
   * Change the theme. Once called, no previous `ruleStack` should be used anymore.
   */
  setTheme(e, t) {
    this._syncRegistry.setTheme(ge.createFromRawTheme(e, t));
  }
  /**
   * Returns a lookup array for color ids.
   */
  getColorMap() {
    return this._syncRegistry.getColorMap();
  }
  /**
   * Load the grammar for `scopeName` and all referenced included grammars asynchronously.
   * Please do not use language id 0.
   */
  loadGrammarWithEmbeddedLanguages(e, t, r) {
    return this.loadGrammarWithConfiguration(e, t, { embeddedLanguages: r });
  }
  /**
   * Load the grammar for `scopeName` and all referenced included grammars asynchronously.
   * Please do not use language id 0.
   */
  loadGrammarWithConfiguration(e, t, r) {
    return this._loadGrammar(
      e,
      t,
      r.embeddedLanguages,
      r.tokenTypes,
      new Sr(
        r.balancedBracketSelectors || [],
        r.unbalancedBracketSelectors || []
      )
    );
  }
  /**
   * Load the grammar for `scopeName` and all referenced included grammars asynchronously.
   */
  loadGrammar(e) {
    return this._loadGrammar(e, 0, null, null, null);
  }
  _loadGrammar(e, t, r, s, o) {
    const i = new Qn(this._syncRegistry, e);
    for (; i.Q.length > 0; )
      i.Q.map((a) => this._loadSingleGrammar(a.scopeName)), i.processQueue();
    return this._grammarForScopeName(
      e,
      t,
      r,
      s,
      o
    );
  }
  _loadSingleGrammar(e) {
    this._ensureGrammarCache.has(e) || (this._doLoadSingleGrammar(e), this._ensureGrammarCache.set(e, !0));
  }
  _doLoadSingleGrammar(e) {
    const t = this._options.loadGrammar(e);
    if (t) {
      const r = typeof this._options.getInjections == "function" ? this._options.getInjections(e) : void 0;
      this._syncRegistry.addGrammar(t, r);
    }
  }
  /**
   * Adds a rawGrammar.
   */
  addGrammar(e, t = [], r = 0, s = null) {
    return this._syncRegistry.addGrammar(e, t), this._grammarForScopeName(e.scopeName, r, s);
  }
  /**
   * Get the grammar for `scopeName`. The grammar must first be created via `loadGrammar` or `addGrammar`.
   */
  _grammarForScopeName(e, t = 0, r = null, s = null, o = null) {
    return this._syncRegistry.grammarForScopeName(
      e,
      t,
      r,
      s,
      o
    );
  }
}, Ue = ze.NULL;
const kr = [
  "area",
  "base",
  "basefont",
  "bgsound",
  "br",
  "col",
  "command",
  "embed",
  "frame",
  "hr",
  "image",
  "img",
  "input",
  "keygen",
  "link",
  "meta",
  "param",
  "source",
  "track",
  "wbr"
];
class ae {
  /**
   * @param {SchemaType['property']} property
   *   Property.
   * @param {SchemaType['normal']} normal
   *   Normal.
   * @param {Space | undefined} [space]
   *   Space.
   * @returns
   *   Schema.
   */
  constructor(e, t, r) {
    this.normal = t, this.property = e, r && (this.space = r);
  }
}
ae.prototype.normal = {};
ae.prototype.property = {};
ae.prototype.space = void 0;
function Jt(n, e) {
  const t = {}, r = {};
  for (const s of n)
    Object.assign(t, s.property), Object.assign(r, s.normal);
  return new ae(t, r, e);
}
function qe(n) {
  return n.toLowerCase();
}
class E {
  /**
   * @param {string} property
   *   Property.
   * @param {string} attribute
   *   Attribute.
   * @returns
   *   Info.
   */
  constructor(e, t) {
    this.attribute = t, this.property = e;
  }
}
E.prototype.attribute = "";
E.prototype.booleanish = !1;
E.prototype.boolean = !1;
E.prototype.commaOrSpaceSeparated = !1;
E.prototype.commaSeparated = !1;
E.prototype.defined = !1;
E.prototype.mustUseProperty = !1;
E.prototype.number = !1;
E.prototype.overloadedBoolean = !1;
E.prototype.property = "";
E.prototype.spaceSeparated = !1;
E.prototype.space = void 0;
let Rr = 0;
const v = z(), x = z(), He = z(), m = z(), k = z(), V = z(), L = z();
function z() {
  return 2 ** ++Rr;
}
const Ve = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  boolean: v,
  booleanish: x,
  commaOrSpaceSeparated: L,
  commaSeparated: V,
  number: m,
  overloadedBoolean: He,
  spaceSeparated: k
}, Symbol.toStringTag, { value: "Module" })), Me = (
  /** @type {ReadonlyArray<keyof typeof types>} */
  Object.keys(Ve)
);
class Qe extends E {
  /**
   * @constructor
   * @param {string} property
   *   Property.
   * @param {string} attribute
   *   Attribute.
   * @param {number | null | undefined} [mask]
   *   Mask.
   * @param {Space | undefined} [space]
   *   Space.
   * @returns
   *   Info.
   */
  constructor(e, t, r, s) {
    let o = -1;
    if (super(e, t), yt(this, "space", s), typeof r == "number")
      for (; ++o < Me.length; ) {
        const i = Me[o];
        yt(this, Me[o], (r & Ve[i]) === Ve[i]);
      }
  }
}
Qe.prototype.defined = !0;
function yt(n, e, t) {
  t && (n[e] = t);
}
function J(n) {
  const e = {}, t = {};
  for (const [r, s] of Object.entries(n.properties)) {
    const o = new Qe(
      r,
      n.transform(n.attributes || {}, r),
      s,
      n.space
    );
    n.mustUseProperty && n.mustUseProperty.includes(r) && (o.mustUseProperty = !0), e[r] = o, t[qe(r)] = r, t[qe(o.attribute)] = r;
  }
  return new ae(e, t, n.space);
}
const Qt = J({
  properties: {
    ariaActiveDescendant: null,
    ariaAtomic: x,
    ariaAutoComplete: null,
    ariaBusy: x,
    ariaChecked: x,
    ariaColCount: m,
    ariaColIndex: m,
    ariaColSpan: m,
    ariaControls: k,
    ariaCurrent: null,
    ariaDescribedBy: k,
    ariaDetails: null,
    ariaDisabled: x,
    ariaDropEffect: k,
    ariaErrorMessage: null,
    ariaExpanded: x,
    ariaFlowTo: k,
    ariaGrabbed: x,
    ariaHasPopup: null,
    ariaHidden: x,
    ariaInvalid: null,
    ariaKeyShortcuts: null,
    ariaLabel: null,
    ariaLabelledBy: k,
    ariaLevel: m,
    ariaLive: null,
    ariaModal: x,
    ariaMultiLine: x,
    ariaMultiSelectable: x,
    ariaOrientation: null,
    ariaOwns: k,
    ariaPlaceholder: null,
    ariaPosInSet: m,
    ariaPressed: x,
    ariaReadOnly: x,
    ariaRelevant: null,
    ariaRequired: x,
    ariaRoleDescription: k,
    ariaRowCount: m,
    ariaRowIndex: m,
    ariaRowSpan: m,
    ariaSelected: x,
    ariaSetSize: m,
    ariaSort: null,
    ariaValueMax: m,
    ariaValueMin: m,
    ariaValueNow: m,
    ariaValueText: null,
    role: null
  },
  transform(n, e) {
    return e === "role" ? e : "aria-" + e.slice(4).toLowerCase();
  }
});
function Zt(n, e) {
  return e in n ? n[e] : e;
}
function en(n, e) {
  return Zt(n, e.toLowerCase());
}
const xr = J({
  attributes: {
    acceptcharset: "accept-charset",
    classname: "class",
    htmlfor: "for",
    httpequiv: "http-equiv"
  },
  mustUseProperty: ["checked", "multiple", "muted", "selected"],
  properties: {
    // Standard Properties.
    abbr: null,
    accept: V,
    acceptCharset: k,
    accessKey: k,
    action: null,
    allow: null,
    allowFullScreen: v,
    allowPaymentRequest: v,
    allowUserMedia: v,
    alt: null,
    as: null,
    async: v,
    autoCapitalize: null,
    autoComplete: k,
    autoFocus: v,
    autoPlay: v,
    blocking: k,
    capture: null,
    charSet: null,
    checked: v,
    cite: null,
    className: k,
    cols: m,
    colSpan: null,
    content: null,
    contentEditable: x,
    controls: v,
    controlsList: k,
    coords: m | V,
    crossOrigin: null,
    data: null,
    dateTime: null,
    decoding: null,
    default: v,
    defer: v,
    dir: null,
    dirName: null,
    disabled: v,
    download: He,
    draggable: x,
    encType: null,
    enterKeyHint: null,
    fetchPriority: null,
    form: null,
    formAction: null,
    formEncType: null,
    formMethod: null,
    formNoValidate: v,
    formTarget: null,
    headers: k,
    height: m,
    hidden: He,
    high: m,
    href: null,
    hrefLang: null,
    htmlFor: k,
    httpEquiv: k,
    id: null,
    imageSizes: null,
    imageSrcSet: null,
    inert: v,
    inputMode: null,
    integrity: null,
    is: null,
    isMap: v,
    itemId: null,
    itemProp: k,
    itemRef: k,
    itemScope: v,
    itemType: k,
    kind: null,
    label: null,
    lang: null,
    language: null,
    list: null,
    loading: null,
    loop: v,
    low: m,
    manifest: null,
    max: null,
    maxLength: m,
    media: null,
    method: null,
    min: null,
    minLength: m,
    multiple: v,
    muted: v,
    name: null,
    nonce: null,
    noModule: v,
    noValidate: v,
    onAbort: null,
    onAfterPrint: null,
    onAuxClick: null,
    onBeforeMatch: null,
    onBeforePrint: null,
    onBeforeToggle: null,
    onBeforeUnload: null,
    onBlur: null,
    onCancel: null,
    onCanPlay: null,
    onCanPlayThrough: null,
    onChange: null,
    onClick: null,
    onClose: null,
    onContextLost: null,
    onContextMenu: null,
    onContextRestored: null,
    onCopy: null,
    onCueChange: null,
    onCut: null,
    onDblClick: null,
    onDrag: null,
    onDragEnd: null,
    onDragEnter: null,
    onDragExit: null,
    onDragLeave: null,
    onDragOver: null,
    onDragStart: null,
    onDrop: null,
    onDurationChange: null,
    onEmptied: null,
    onEnded: null,
    onError: null,
    onFocus: null,
    onFormData: null,
    onHashChange: null,
    onInput: null,
    onInvalid: null,
    onKeyDown: null,
    onKeyPress: null,
    onKeyUp: null,
    onLanguageChange: null,
    onLoad: null,
    onLoadedData: null,
    onLoadedMetadata: null,
    onLoadEnd: null,
    onLoadStart: null,
    onMessage: null,
    onMessageError: null,
    onMouseDown: null,
    onMouseEnter: null,
    onMouseLeave: null,
    onMouseMove: null,
    onMouseOut: null,
    onMouseOver: null,
    onMouseUp: null,
    onOffline: null,
    onOnline: null,
    onPageHide: null,
    onPageShow: null,
    onPaste: null,
    onPause: null,
    onPlay: null,
    onPlaying: null,
    onPopState: null,
    onProgress: null,
    onRateChange: null,
    onRejectionHandled: null,
    onReset: null,
    onResize: null,
    onScroll: null,
    onScrollEnd: null,
    onSecurityPolicyViolation: null,
    onSeeked: null,
    onSeeking: null,
    onSelect: null,
    onSlotChange: null,
    onStalled: null,
    onStorage: null,
    onSubmit: null,
    onSuspend: null,
    onTimeUpdate: null,
    onToggle: null,
    onUnhandledRejection: null,
    onUnload: null,
    onVolumeChange: null,
    onWaiting: null,
    onWheel: null,
    open: v,
    optimum: m,
    pattern: null,
    ping: k,
    placeholder: null,
    playsInline: v,
    popover: null,
    popoverTarget: null,
    popoverTargetAction: null,
    poster: null,
    preload: null,
    readOnly: v,
    referrerPolicy: null,
    rel: k,
    required: v,
    reversed: v,
    rows: m,
    rowSpan: m,
    sandbox: k,
    scope: null,
    scoped: v,
    seamless: v,
    selected: v,
    shadowRootClonable: v,
    shadowRootDelegatesFocus: v,
    shadowRootMode: null,
    shape: null,
    size: m,
    sizes: null,
    slot: null,
    span: m,
    spellCheck: x,
    src: null,
    srcDoc: null,
    srcLang: null,
    srcSet: null,
    start: m,
    step: null,
    style: null,
    tabIndex: m,
    target: null,
    title: null,
    translate: null,
    type: null,
    typeMustMatch: v,
    useMap: null,
    value: x,
    width: m,
    wrap: null,
    writingSuggestions: null,
    // Legacy.
    // See: https://html.spec.whatwg.org/#other-elements,-attributes-and-apis
    align: null,
    // Several. Use CSS `text-align` instead,
    aLink: null,
    // `<body>`. Use CSS `a:active {color}` instead
    archive: k,
    // `<object>`. List of URIs to archives
    axis: null,
    // `<td>` and `<th>`. Use `scope` on `<th>`
    background: null,
    // `<body>`. Use CSS `background-image` instead
    bgColor: null,
    // `<body>` and table elements. Use CSS `background-color` instead
    border: m,
    // `<table>`. Use CSS `border-width` instead,
    borderColor: null,
    // `<table>`. Use CSS `border-color` instead,
    bottomMargin: m,
    // `<body>`
    cellPadding: null,
    // `<table>`
    cellSpacing: null,
    // `<table>`
    char: null,
    // Several table elements. When `align=char`, sets the character to align on
    charOff: null,
    // Several table elements. When `char`, offsets the alignment
    classId: null,
    // `<object>`
    clear: null,
    // `<br>`. Use CSS `clear` instead
    code: null,
    // `<object>`
    codeBase: null,
    // `<object>`
    codeType: null,
    // `<object>`
    color: null,
    // `<font>` and `<hr>`. Use CSS instead
    compact: v,
    // Lists. Use CSS to reduce space between items instead
    declare: v,
    // `<object>`
    event: null,
    // `<script>`
    face: null,
    // `<font>`. Use CSS instead
    frame: null,
    // `<table>`
    frameBorder: null,
    // `<iframe>`. Use CSS `border` instead
    hSpace: m,
    // `<img>` and `<object>`
    leftMargin: m,
    // `<body>`
    link: null,
    // `<body>`. Use CSS `a:link {color: *}` instead
    longDesc: null,
    // `<frame>`, `<iframe>`, and `<img>`. Use an `<a>`
    lowSrc: null,
    // `<img>`. Use a `<picture>`
    marginHeight: m,
    // `<body>`
    marginWidth: m,
    // `<body>`
    noResize: v,
    // `<frame>`
    noHref: v,
    // `<area>`. Use no href instead of an explicit `nohref`
    noShade: v,
    // `<hr>`. Use background-color and height instead of borders
    noWrap: v,
    // `<td>` and `<th>`
    object: null,
    // `<applet>`
    profile: null,
    // `<head>`
    prompt: null,
    // `<isindex>`
    rev: null,
    // `<link>`
    rightMargin: m,
    // `<body>`
    rules: null,
    // `<table>`
    scheme: null,
    // `<meta>`
    scrolling: x,
    // `<frame>`. Use overflow in the child context
    standby: null,
    // `<object>`
    summary: null,
    // `<table>`
    text: null,
    // `<body>`. Use CSS `color` instead
    topMargin: m,
    // `<body>`
    valueType: null,
    // `<param>`
    version: null,
    // `<html>`. Use a doctype.
    vAlign: null,
    // Several. Use CSS `vertical-align` instead
    vLink: null,
    // `<body>`. Use CSS `a:visited {color}` instead
    vSpace: m,
    // `<img>` and `<object>`
    // Non-standard Properties.
    allowTransparency: null,
    autoCorrect: null,
    autoSave: null,
    disablePictureInPicture: v,
    disableRemotePlayback: v,
    prefix: null,
    property: null,
    results: m,
    security: null,
    unselectable: null
  },
  space: "html",
  transform: en
}), Ar = J({
  attributes: {
    accentHeight: "accent-height",
    alignmentBaseline: "alignment-baseline",
    arabicForm: "arabic-form",
    baselineShift: "baseline-shift",
    capHeight: "cap-height",
    className: "class",
    clipPath: "clip-path",
    clipRule: "clip-rule",
    colorInterpolation: "color-interpolation",
    colorInterpolationFilters: "color-interpolation-filters",
    colorProfile: "color-profile",
    colorRendering: "color-rendering",
    crossOrigin: "crossorigin",
    dataType: "datatype",
    dominantBaseline: "dominant-baseline",
    enableBackground: "enable-background",
    fillOpacity: "fill-opacity",
    fillRule: "fill-rule",
    floodColor: "flood-color",
    floodOpacity: "flood-opacity",
    fontFamily: "font-family",
    fontSize: "font-size",
    fontSizeAdjust: "font-size-adjust",
    fontStretch: "font-stretch",
    fontStyle: "font-style",
    fontVariant: "font-variant",
    fontWeight: "font-weight",
    glyphName: "glyph-name",
    glyphOrientationHorizontal: "glyph-orientation-horizontal",
    glyphOrientationVertical: "glyph-orientation-vertical",
    hrefLang: "hreflang",
    horizAdvX: "horiz-adv-x",
    horizOriginX: "horiz-origin-x",
    horizOriginY: "horiz-origin-y",
    imageRendering: "image-rendering",
    letterSpacing: "letter-spacing",
    lightingColor: "lighting-color",
    markerEnd: "marker-end",
    markerMid: "marker-mid",
    markerStart: "marker-start",
    navDown: "nav-down",
    navDownLeft: "nav-down-left",
    navDownRight: "nav-down-right",
    navLeft: "nav-left",
    navNext: "nav-next",
    navPrev: "nav-prev",
    navRight: "nav-right",
    navUp: "nav-up",
    navUpLeft: "nav-up-left",
    navUpRight: "nav-up-right",
    onAbort: "onabort",
    onActivate: "onactivate",
    onAfterPrint: "onafterprint",
    onBeforePrint: "onbeforeprint",
    onBegin: "onbegin",
    onCancel: "oncancel",
    onCanPlay: "oncanplay",
    onCanPlayThrough: "oncanplaythrough",
    onChange: "onchange",
    onClick: "onclick",
    onClose: "onclose",
    onCopy: "oncopy",
    onCueChange: "oncuechange",
    onCut: "oncut",
    onDblClick: "ondblclick",
    onDrag: "ondrag",
    onDragEnd: "ondragend",
    onDragEnter: "ondragenter",
    onDragExit: "ondragexit",
    onDragLeave: "ondragleave",
    onDragOver: "ondragover",
    onDragStart: "ondragstart",
    onDrop: "ondrop",
    onDurationChange: "ondurationchange",
    onEmptied: "onemptied",
    onEnd: "onend",
    onEnded: "onended",
    onError: "onerror",
    onFocus: "onfocus",
    onFocusIn: "onfocusin",
    onFocusOut: "onfocusout",
    onHashChange: "onhashchange",
    onInput: "oninput",
    onInvalid: "oninvalid",
    onKeyDown: "onkeydown",
    onKeyPress: "onkeypress",
    onKeyUp: "onkeyup",
    onLoad: "onload",
    onLoadedData: "onloadeddata",
    onLoadedMetadata: "onloadedmetadata",
    onLoadStart: "onloadstart",
    onMessage: "onmessage",
    onMouseDown: "onmousedown",
    onMouseEnter: "onmouseenter",
    onMouseLeave: "onmouseleave",
    onMouseMove: "onmousemove",
    onMouseOut: "onmouseout",
    onMouseOver: "onmouseover",
    onMouseUp: "onmouseup",
    onMouseWheel: "onmousewheel",
    onOffline: "onoffline",
    onOnline: "ononline",
    onPageHide: "onpagehide",
    onPageShow: "onpageshow",
    onPaste: "onpaste",
    onPause: "onpause",
    onPlay: "onplay",
    onPlaying: "onplaying",
    onPopState: "onpopstate",
    onProgress: "onprogress",
    onRateChange: "onratechange",
    onRepeat: "onrepeat",
    onReset: "onreset",
    onResize: "onresize",
    onScroll: "onscroll",
    onSeeked: "onseeked",
    onSeeking: "onseeking",
    onSelect: "onselect",
    onShow: "onshow",
    onStalled: "onstalled",
    onStorage: "onstorage",
    onSubmit: "onsubmit",
    onSuspend: "onsuspend",
    onTimeUpdate: "ontimeupdate",
    onToggle: "ontoggle",
    onUnload: "onunload",
    onVolumeChange: "onvolumechange",
    onWaiting: "onwaiting",
    onZoom: "onzoom",
    overlinePosition: "overline-position",
    overlineThickness: "overline-thickness",
    paintOrder: "paint-order",
    panose1: "panose-1",
    pointerEvents: "pointer-events",
    referrerPolicy: "referrerpolicy",
    renderingIntent: "rendering-intent",
    shapeRendering: "shape-rendering",
    stopColor: "stop-color",
    stopOpacity: "stop-opacity",
    strikethroughPosition: "strikethrough-position",
    strikethroughThickness: "strikethrough-thickness",
    strokeDashArray: "stroke-dasharray",
    strokeDashOffset: "stroke-dashoffset",
    strokeLineCap: "stroke-linecap",
    strokeLineJoin: "stroke-linejoin",
    strokeMiterLimit: "stroke-miterlimit",
    strokeOpacity: "stroke-opacity",
    strokeWidth: "stroke-width",
    tabIndex: "tabindex",
    textAnchor: "text-anchor",
    textDecoration: "text-decoration",
    textRendering: "text-rendering",
    transformOrigin: "transform-origin",
    typeOf: "typeof",
    underlinePosition: "underline-position",
    underlineThickness: "underline-thickness",
    unicodeBidi: "unicode-bidi",
    unicodeRange: "unicode-range",
    unitsPerEm: "units-per-em",
    vAlphabetic: "v-alphabetic",
    vHanging: "v-hanging",
    vIdeographic: "v-ideographic",
    vMathematical: "v-mathematical",
    vectorEffect: "vector-effect",
    vertAdvY: "vert-adv-y",
    vertOriginX: "vert-origin-x",
    vertOriginY: "vert-origin-y",
    wordSpacing: "word-spacing",
    writingMode: "writing-mode",
    xHeight: "x-height",
    // These were camelcased in Tiny. Now lowercased in SVG 2
    playbackOrder: "playbackorder",
    timelineBegin: "timelinebegin"
  },
  properties: {
    about: L,
    accentHeight: m,
    accumulate: null,
    additive: null,
    alignmentBaseline: null,
    alphabetic: m,
    amplitude: m,
    arabicForm: null,
    ascent: m,
    attributeName: null,
    attributeType: null,
    azimuth: m,
    bandwidth: null,
    baselineShift: null,
    baseFrequency: null,
    baseProfile: null,
    bbox: null,
    begin: null,
    bias: m,
    by: null,
    calcMode: null,
    capHeight: m,
    className: k,
    clip: null,
    clipPath: null,
    clipPathUnits: null,
    clipRule: null,
    color: null,
    colorInterpolation: null,
    colorInterpolationFilters: null,
    colorProfile: null,
    colorRendering: null,
    content: null,
    contentScriptType: null,
    contentStyleType: null,
    crossOrigin: null,
    cursor: null,
    cx: null,
    cy: null,
    d: null,
    dataType: null,
    defaultAction: null,
    descent: m,
    diffuseConstant: m,
    direction: null,
    display: null,
    dur: null,
    divisor: m,
    dominantBaseline: null,
    download: v,
    dx: null,
    dy: null,
    edgeMode: null,
    editable: null,
    elevation: m,
    enableBackground: null,
    end: null,
    event: null,
    exponent: m,
    externalResourcesRequired: null,
    fill: null,
    fillOpacity: m,
    fillRule: null,
    filter: null,
    filterRes: null,
    filterUnits: null,
    floodColor: null,
    floodOpacity: null,
    focusable: null,
    focusHighlight: null,
    fontFamily: null,
    fontSize: null,
    fontSizeAdjust: null,
    fontStretch: null,
    fontStyle: null,
    fontVariant: null,
    fontWeight: null,
    format: null,
    fr: null,
    from: null,
    fx: null,
    fy: null,
    g1: V,
    g2: V,
    glyphName: V,
    glyphOrientationHorizontal: null,
    glyphOrientationVertical: null,
    glyphRef: null,
    gradientTransform: null,
    gradientUnits: null,
    handler: null,
    hanging: m,
    hatchContentUnits: null,
    hatchUnits: null,
    height: null,
    href: null,
    hrefLang: null,
    horizAdvX: m,
    horizOriginX: m,
    horizOriginY: m,
    id: null,
    ideographic: m,
    imageRendering: null,
    initialVisibility: null,
    in: null,
    in2: null,
    intercept: m,
    k: m,
    k1: m,
    k2: m,
    k3: m,
    k4: m,
    kernelMatrix: L,
    kernelUnitLength: null,
    keyPoints: null,
    // SEMI_COLON_SEPARATED
    keySplines: null,
    // SEMI_COLON_SEPARATED
    keyTimes: null,
    // SEMI_COLON_SEPARATED
    kerning: null,
    lang: null,
    lengthAdjust: null,
    letterSpacing: null,
    lightingColor: null,
    limitingConeAngle: m,
    local: null,
    markerEnd: null,
    markerMid: null,
    markerStart: null,
    markerHeight: null,
    markerUnits: null,
    markerWidth: null,
    mask: null,
    maskContentUnits: null,
    maskUnits: null,
    mathematical: null,
    max: null,
    media: null,
    mediaCharacterEncoding: null,
    mediaContentEncodings: null,
    mediaSize: m,
    mediaTime: null,
    method: null,
    min: null,
    mode: null,
    name: null,
    navDown: null,
    navDownLeft: null,
    navDownRight: null,
    navLeft: null,
    navNext: null,
    navPrev: null,
    navRight: null,
    navUp: null,
    navUpLeft: null,
    navUpRight: null,
    numOctaves: null,
    observer: null,
    offset: null,
    onAbort: null,
    onActivate: null,
    onAfterPrint: null,
    onBeforePrint: null,
    onBegin: null,
    onCancel: null,
    onCanPlay: null,
    onCanPlayThrough: null,
    onChange: null,
    onClick: null,
    onClose: null,
    onCopy: null,
    onCueChange: null,
    onCut: null,
    onDblClick: null,
    onDrag: null,
    onDragEnd: null,
    onDragEnter: null,
    onDragExit: null,
    onDragLeave: null,
    onDragOver: null,
    onDragStart: null,
    onDrop: null,
    onDurationChange: null,
    onEmptied: null,
    onEnd: null,
    onEnded: null,
    onError: null,
    onFocus: null,
    onFocusIn: null,
    onFocusOut: null,
    onHashChange: null,
    onInput: null,
    onInvalid: null,
    onKeyDown: null,
    onKeyPress: null,
    onKeyUp: null,
    onLoad: null,
    onLoadedData: null,
    onLoadedMetadata: null,
    onLoadStart: null,
    onMessage: null,
    onMouseDown: null,
    onMouseEnter: null,
    onMouseLeave: null,
    onMouseMove: null,
    onMouseOut: null,
    onMouseOver: null,
    onMouseUp: null,
    onMouseWheel: null,
    onOffline: null,
    onOnline: null,
    onPageHide: null,
    onPageShow: null,
    onPaste: null,
    onPause: null,
    onPlay: null,
    onPlaying: null,
    onPopState: null,
    onProgress: null,
    onRateChange: null,
    onRepeat: null,
    onReset: null,
    onResize: null,
    onScroll: null,
    onSeeked: null,
    onSeeking: null,
    onSelect: null,
    onShow: null,
    onStalled: null,
    onStorage: null,
    onSubmit: null,
    onSuspend: null,
    onTimeUpdate: null,
    onToggle: null,
    onUnload: null,
    onVolumeChange: null,
    onWaiting: null,
    onZoom: null,
    opacity: null,
    operator: null,
    order: null,
    orient: null,
    orientation: null,
    origin: null,
    overflow: null,
    overlay: null,
    overlinePosition: m,
    overlineThickness: m,
    paintOrder: null,
    panose1: null,
    path: null,
    pathLength: m,
    patternContentUnits: null,
    patternTransform: null,
    patternUnits: null,
    phase: null,
    ping: k,
    pitch: null,
    playbackOrder: null,
    pointerEvents: null,
    points: null,
    pointsAtX: m,
    pointsAtY: m,
    pointsAtZ: m,
    preserveAlpha: null,
    preserveAspectRatio: null,
    primitiveUnits: null,
    propagate: null,
    property: L,
    r: null,
    radius: null,
    referrerPolicy: null,
    refX: null,
    refY: null,
    rel: L,
    rev: L,
    renderingIntent: null,
    repeatCount: null,
    repeatDur: null,
    requiredExtensions: L,
    requiredFeatures: L,
    requiredFonts: L,
    requiredFormats: L,
    resource: null,
    restart: null,
    result: null,
    rotate: null,
    rx: null,
    ry: null,
    scale: null,
    seed: null,
    shapeRendering: null,
    side: null,
    slope: null,
    snapshotTime: null,
    specularConstant: m,
    specularExponent: m,
    spreadMethod: null,
    spacing: null,
    startOffset: null,
    stdDeviation: null,
    stemh: null,
    stemv: null,
    stitchTiles: null,
    stopColor: null,
    stopOpacity: null,
    strikethroughPosition: m,
    strikethroughThickness: m,
    string: null,
    stroke: null,
    strokeDashArray: L,
    strokeDashOffset: null,
    strokeLineCap: null,
    strokeLineJoin: null,
    strokeMiterLimit: m,
    strokeOpacity: m,
    strokeWidth: null,
    style: null,
    surfaceScale: m,
    syncBehavior: null,
    syncBehaviorDefault: null,
    syncMaster: null,
    syncTolerance: null,
    syncToleranceDefault: null,
    systemLanguage: L,
    tabIndex: m,
    tableValues: null,
    target: null,
    targetX: m,
    targetY: m,
    textAnchor: null,
    textDecoration: null,
    textRendering: null,
    textLength: null,
    timelineBegin: null,
    title: null,
    transformBehavior: null,
    type: null,
    typeOf: L,
    to: null,
    transform: null,
    transformOrigin: null,
    u1: null,
    u2: null,
    underlinePosition: m,
    underlineThickness: m,
    unicode: null,
    unicodeBidi: null,
    unicodeRange: null,
    unitsPerEm: m,
    values: null,
    vAlphabetic: m,
    vMathematical: m,
    vectorEffect: null,
    vHanging: m,
    vIdeographic: m,
    version: null,
    vertAdvY: m,
    vertOriginX: m,
    vertOriginY: m,
    viewBox: null,
    viewTarget: null,
    visibility: null,
    width: null,
    widths: null,
    wordSpacing: null,
    writingMode: null,
    x: null,
    x1: null,
    x2: null,
    xChannelSelector: null,
    xHeight: m,
    y: null,
    y1: null,
    y2: null,
    yChannelSelector: null,
    z: null,
    zoomAndPan: null
  },
  space: "svg",
  transform: Zt
}), tn = J({
  properties: {
    xLinkActuate: null,
    xLinkArcRole: null,
    xLinkHref: null,
    xLinkRole: null,
    xLinkShow: null,
    xLinkTitle: null,
    xLinkType: null
  },
  space: "xlink",
  transform(n, e) {
    return "xlink:" + e.slice(5).toLowerCase();
  }
}), nn = J({
  attributes: { xmlnsxlink: "xmlns:xlink" },
  properties: { xmlnsXLink: null, xmlns: null },
  space: "xmlns",
  transform: en
}), rn = J({
  properties: { xmlBase: null, xmlLang: null, xmlSpace: null },
  space: "xml",
  transform(n, e) {
    return "xml:" + e.slice(3).toLowerCase();
  }
}), Nr = /[A-Z]/g, _t = /-[a-z]/g, Tr = /^data[-\w.:]+$/i;
function Pr(n, e) {
  const t = qe(e);
  let r = e, s = E;
  if (t in n.normal)
    return n.property[n.normal[t]];
  if (t.length > 4 && t.slice(0, 4) === "data" && Tr.test(e)) {
    if (e.charAt(4) === "-") {
      const o = e.slice(5).replace(_t, Er);
      r = "data" + o.charAt(0).toUpperCase() + o.slice(1);
    } else {
      const o = e.slice(4);
      if (!_t.test(o)) {
        let i = o.replace(Nr, Ir);
        i.charAt(0) !== "-" && (i = "-" + i), e = "data" + i;
      }
    }
    s = Qe;
  }
  return new s(r, e);
}
function Ir(n) {
  return "-" + n.toLowerCase();
}
function Er(n) {
  return n.charAt(1).toUpperCase();
}
const Lr = Jt([Qt, xr, tn, nn, rn], "html"), sn = Jt([Qt, Ar, tn, nn, rn], "svg"), bt = {}.hasOwnProperty;
function Or(n, e) {
  const t = e || {};
  function r(s, ...o) {
    let i = r.invalid;
    const a = r.handlers;
    if (s && bt.call(s, n)) {
      const l = String(s[n]);
      i = bt.call(a, l) ? a[l] : r.unknown;
    }
    if (i)
      return i.call(this, s, ...o);
  }
  return r.handlers = t.handlers || {}, r.invalid = t.invalid, r.unknown = t.unknown, r;
}
const Mr = /["&'<>`]/g, Gr = /[\uD800-\uDBFF][\uDC00-\uDFFF]/g, Br = (
  // eslint-disable-next-line no-control-regex, unicorn/no-hex-escape
  /[\x01-\t\v\f\x0E-\x1F\x7F\x81\x8D\x8F\x90\x9D\xA0-\uFFFF]/g
), Dr = /[|\\{}()[\]^$+*?.]/g, St = /* @__PURE__ */ new WeakMap();
function $r(n, e) {
  if (n = n.replace(
    e.subset ? jr(e.subset) : Mr,
    r
  ), e.subset || e.escapeOnly)
    return n;
  return n.replace(Gr, t).replace(Br, r);
  function t(s, o, i) {
    return e.format(
      (s.charCodeAt(0) - 55296) * 1024 + s.charCodeAt(1) - 56320 + 65536,
      i.charCodeAt(o + 2),
      e
    );
  }
  function r(s, o, i) {
    return e.format(
      s.charCodeAt(0),
      i.charCodeAt(o + 1),
      e
    );
  }
}
function jr(n) {
  let e = St.get(n);
  return e || (e = Fr(n), St.set(n, e)), e;
}
function Fr(n) {
  const e = [];
  let t = -1;
  for (; ++t < n.length; )
    e.push(n[t].replace(Dr, "\\$&"));
  return new RegExp("(?:" + e.join("|") + ")", "g");
}
const Wr = /[\dA-Fa-f]/;
function zr(n, e, t) {
  const r = "&#x" + n.toString(16).toUpperCase();
  return t && e && !Wr.test(String.fromCharCode(e)) ? r : r + ";";
}
const Ur = /\d/;
function qr(n, e, t) {
  const r = "&#" + String(n);
  return t && e && !Ur.test(String.fromCharCode(e)) ? r : r + ";";
}
const Hr = [
  "AElig",
  "AMP",
  "Aacute",
  "Acirc",
  "Agrave",
  "Aring",
  "Atilde",
  "Auml",
  "COPY",
  "Ccedil",
  "ETH",
  "Eacute",
  "Ecirc",
  "Egrave",
  "Euml",
  "GT",
  "Iacute",
  "Icirc",
  "Igrave",
  "Iuml",
  "LT",
  "Ntilde",
  "Oacute",
  "Ocirc",
  "Ograve",
  "Oslash",
  "Otilde",
  "Ouml",
  "QUOT",
  "REG",
  "THORN",
  "Uacute",
  "Ucirc",
  "Ugrave",
  "Uuml",
  "Yacute",
  "aacute",
  "acirc",
  "acute",
  "aelig",
  "agrave",
  "amp",
  "aring",
  "atilde",
  "auml",
  "brvbar",
  "ccedil",
  "cedil",
  "cent",
  "copy",
  "curren",
  "deg",
  "divide",
  "eacute",
  "ecirc",
  "egrave",
  "eth",
  "euml",
  "frac12",
  "frac14",
  "frac34",
  "gt",
  "iacute",
  "icirc",
  "iexcl",
  "igrave",
  "iquest",
  "iuml",
  "laquo",
  "lt",
  "macr",
  "micro",
  "middot",
  "nbsp",
  "not",
  "ntilde",
  "oacute",
  "ocirc",
  "ograve",
  "ordf",
  "ordm",
  "oslash",
  "otilde",
  "ouml",
  "para",
  "plusmn",
  "pound",
  "quot",
  "raquo",
  "reg",
  "sect",
  "shy",
  "sup1",
  "sup2",
  "sup3",
  "szlig",
  "thorn",
  "times",
  "uacute",
  "ucirc",
  "ugrave",
  "uml",
  "uuml",
  "yacute",
  "yen",
  "yuml"
], Ge = {
  nbsp: " ",
  iexcl: "¡",
  cent: "¢",
  pound: "£",
  curren: "¤",
  yen: "¥",
  brvbar: "¦",
  sect: "§",
  uml: "¨",
  copy: "©",
  ordf: "ª",
  laquo: "«",
  not: "¬",
  shy: "­",
  reg: "®",
  macr: "¯",
  deg: "°",
  plusmn: "±",
  sup2: "²",
  sup3: "³",
  acute: "´",
  micro: "µ",
  para: "¶",
  middot: "·",
  cedil: "¸",
  sup1: "¹",
  ordm: "º",
  raquo: "»",
  frac14: "¼",
  frac12: "½",
  frac34: "¾",
  iquest: "¿",
  Agrave: "À",
  Aacute: "Á",
  Acirc: "Â",
  Atilde: "Ã",
  Auml: "Ä",
  Aring: "Å",
  AElig: "Æ",
  Ccedil: "Ç",
  Egrave: "È",
  Eacute: "É",
  Ecirc: "Ê",
  Euml: "Ë",
  Igrave: "Ì",
  Iacute: "Í",
  Icirc: "Î",
  Iuml: "Ï",
  ETH: "Ð",
  Ntilde: "Ñ",
  Ograve: "Ò",
  Oacute: "Ó",
  Ocirc: "Ô",
  Otilde: "Õ",
  Ouml: "Ö",
  times: "×",
  Oslash: "Ø",
  Ugrave: "Ù",
  Uacute: "Ú",
  Ucirc: "Û",
  Uuml: "Ü",
  Yacute: "Ý",
  THORN: "Þ",
  szlig: "ß",
  agrave: "à",
  aacute: "á",
  acirc: "â",
  atilde: "ã",
  auml: "ä",
  aring: "å",
  aelig: "æ",
  ccedil: "ç",
  egrave: "è",
  eacute: "é",
  ecirc: "ê",
  euml: "ë",
  igrave: "ì",
  iacute: "í",
  icirc: "î",
  iuml: "ï",
  eth: "ð",
  ntilde: "ñ",
  ograve: "ò",
  oacute: "ó",
  ocirc: "ô",
  otilde: "õ",
  ouml: "ö",
  divide: "÷",
  oslash: "ø",
  ugrave: "ù",
  uacute: "ú",
  ucirc: "û",
  uuml: "ü",
  yacute: "ý",
  thorn: "þ",
  yuml: "ÿ",
  fnof: "ƒ",
  Alpha: "Α",
  Beta: "Β",
  Gamma: "Γ",
  Delta: "Δ",
  Epsilon: "Ε",
  Zeta: "Ζ",
  Eta: "Η",
  Theta: "Θ",
  Iota: "Ι",
  Kappa: "Κ",
  Lambda: "Λ",
  Mu: "Μ",
  Nu: "Ν",
  Xi: "Ξ",
  Omicron: "Ο",
  Pi: "Π",
  Rho: "Ρ",
  Sigma: "Σ",
  Tau: "Τ",
  Upsilon: "Υ",
  Phi: "Φ",
  Chi: "Χ",
  Psi: "Ψ",
  Omega: "Ω",
  alpha: "α",
  beta: "β",
  gamma: "γ",
  delta: "δ",
  epsilon: "ε",
  zeta: "ζ",
  eta: "η",
  theta: "θ",
  iota: "ι",
  kappa: "κ",
  lambda: "λ",
  mu: "μ",
  nu: "ν",
  xi: "ξ",
  omicron: "ο",
  pi: "π",
  rho: "ρ",
  sigmaf: "ς",
  sigma: "σ",
  tau: "τ",
  upsilon: "υ",
  phi: "φ",
  chi: "χ",
  psi: "ψ",
  omega: "ω",
  thetasym: "ϑ",
  upsih: "ϒ",
  piv: "ϖ",
  bull: "•",
  hellip: "…",
  prime: "′",
  Prime: "″",
  oline: "‾",
  frasl: "⁄",
  weierp: "℘",
  image: "ℑ",
  real: "ℜ",
  trade: "™",
  alefsym: "ℵ",
  larr: "←",
  uarr: "↑",
  rarr: "→",
  darr: "↓",
  harr: "↔",
  crarr: "↵",
  lArr: "⇐",
  uArr: "⇑",
  rArr: "⇒",
  dArr: "⇓",
  hArr: "⇔",
  forall: "∀",
  part: "∂",
  exist: "∃",
  empty: "∅",
  nabla: "∇",
  isin: "∈",
  notin: "∉",
  ni: "∋",
  prod: "∏",
  sum: "∑",
  minus: "−",
  lowast: "∗",
  radic: "√",
  prop: "∝",
  infin: "∞",
  ang: "∠",
  and: "∧",
  or: "∨",
  cap: "∩",
  cup: "∪",
  int: "∫",
  there4: "∴",
  sim: "∼",
  cong: "≅",
  asymp: "≈",
  ne: "≠",
  equiv: "≡",
  le: "≤",
  ge: "≥",
  sub: "⊂",
  sup: "⊃",
  nsub: "⊄",
  sube: "⊆",
  supe: "⊇",
  oplus: "⊕",
  otimes: "⊗",
  perp: "⊥",
  sdot: "⋅",
  lceil: "⌈",
  rceil: "⌉",
  lfloor: "⌊",
  rfloor: "⌋",
  lang: "〈",
  rang: "〉",
  loz: "◊",
  spades: "♠",
  clubs: "♣",
  hearts: "♥",
  diams: "♦",
  quot: '"',
  amp: "&",
  lt: "<",
  gt: ">",
  OElig: "Œ",
  oelig: "œ",
  Scaron: "Š",
  scaron: "š",
  Yuml: "Ÿ",
  circ: "ˆ",
  tilde: "˜",
  ensp: " ",
  emsp: " ",
  thinsp: " ",
  zwnj: "‌",
  zwj: "‍",
  lrm: "‎",
  rlm: "‏",
  ndash: "–",
  mdash: "—",
  lsquo: "‘",
  rsquo: "’",
  sbquo: "‚",
  ldquo: "“",
  rdquo: "”",
  bdquo: "„",
  dagger: "†",
  Dagger: "‡",
  permil: "‰",
  lsaquo: "‹",
  rsaquo: "›",
  euro: "€"
}, Vr = [
  "cent",
  "copy",
  "divide",
  "gt",
  "lt",
  "not",
  "para",
  "times"
], on = {}.hasOwnProperty, Ke = {};
let he;
for (he in Ge)
  on.call(Ge, he) && (Ke[Ge[he]] = he);
const Kr = /[^\dA-Za-z]/;
function Yr(n, e, t, r) {
  const s = String.fromCharCode(n);
  if (on.call(Ke, s)) {
    const o = Ke[s], i = "&" + o;
    return t && Hr.includes(o) && !Vr.includes(o) && (!r || e && e !== 61 && Kr.test(String.fromCharCode(e))) ? i : i + ";";
  }
  return "";
}
function Xr(n, e, t) {
  let r = zr(n, e, t.omitOptionalSemicolons), s;
  if ((t.useNamedReferences || t.useShortestReferences) && (s = Yr(
    n,
    e,
    t.omitOptionalSemicolons,
    t.attribute
  )), (t.useShortestReferences || !s) && t.useShortestReferences) {
    const o = qr(n, e, t.omitOptionalSemicolons);
    o.length < r.length && (r = o);
  }
  return s && (!t.useShortestReferences || s.length < r.length) ? s : r;
}
function K(n, e) {
  return $r(n, Object.assign({ format: Xr }, e));
}
const Jr = /^>|^->|<!--|-->|--!>|<!-$/g, Qr = [">"], Zr = ["<", ">"];
function es(n, e, t, r) {
  return r.settings.bogusComments ? "<?" + K(
    n.value,
    Object.assign({}, r.settings.characterReferences, {
      subset: Qr
    })
  ) + ">" : "<!--" + n.value.replace(Jr, s) + "-->";
  function s(o) {
    return K(
      o,
      Object.assign({}, r.settings.characterReferences, {
        subset: Zr
      })
    );
  }
}
function ts(n, e, t, r) {
  return "<!" + (r.settings.upperDoctype ? "DOCTYPE" : "doctype") + (r.settings.tightDoctype ? "" : " ") + "html>";
}
function Ct(n, e) {
  const t = String(n);
  if (typeof e != "string")
    throw new TypeError("Expected character");
  let r = 0, s = t.indexOf(e);
  for (; s !== -1; )
    r++, s = t.indexOf(e, s + e.length);
  return r;
}
function ns(n, e) {
  const t = e || {};
  return (n[n.length - 1] === "" ? [...n, ""] : n).join(
    (t.padRight ? " " : "") + "," + (t.padLeft === !1 ? "" : " ")
  ).trim();
}
function rs(n) {
  return n.join(" ").trim();
}
const ss = /[ \t\n\f\r]/g;
function Ze(n) {
  return typeof n == "object" ? n.type === "text" ? vt(n.value) : !1 : vt(n);
}
function vt(n) {
  return n.replace(ss, "") === "";
}
const A = an(1), ln = an(-1), os = [];
function an(n) {
  return e;
  function e(t, r, s) {
    const o = t ? t.children : os;
    let i = (r || 0) + n, a = o[i];
    if (!s)
      for (; a && Ze(a); )
        i += n, a = o[i];
    return a;
  }
}
const is = {}.hasOwnProperty;
function cn(n) {
  return e;
  function e(t, r, s) {
    return is.call(n, t.tagName) && n[t.tagName](t, r, s);
  }
}
const et = cn({
  body: as,
  caption: Be,
  colgroup: Be,
  dd: ds,
  dt: hs,
  head: Be,
  html: ls,
  li: us,
  optgroup: fs,
  option: ps,
  p: cs,
  rp: wt,
  rt: wt,
  tbody: ms,
  td: kt,
  tfoot: ys,
  th: kt,
  thead: gs,
  tr: _s
});
function Be(n, e, t) {
  const r = A(t, e, !0);
  return !r || r.type !== "comment" && !(r.type === "text" && Ze(r.value.charAt(0)));
}
function ls(n, e, t) {
  const r = A(t, e);
  return !r || r.type !== "comment";
}
function as(n, e, t) {
  const r = A(t, e);
  return !r || r.type !== "comment";
}
function cs(n, e, t) {
  const r = A(t, e);
  return r ? r.type === "element" && (r.tagName === "address" || r.tagName === "article" || r.tagName === "aside" || r.tagName === "blockquote" || r.tagName === "details" || r.tagName === "div" || r.tagName === "dl" || r.tagName === "fieldset" || r.tagName === "figcaption" || r.tagName === "figure" || r.tagName === "footer" || r.tagName === "form" || r.tagName === "h1" || r.tagName === "h2" || r.tagName === "h3" || r.tagName === "h4" || r.tagName === "h5" || r.tagName === "h6" || r.tagName === "header" || r.tagName === "hgroup" || r.tagName === "hr" || r.tagName === "main" || r.tagName === "menu" || r.tagName === "nav" || r.tagName === "ol" || r.tagName === "p" || r.tagName === "pre" || r.tagName === "section" || r.tagName === "table" || r.tagName === "ul") : !t || // Confusing parent.
  !(t.type === "element" && (t.tagName === "a" || t.tagName === "audio" || t.tagName === "del" || t.tagName === "ins" || t.tagName === "map" || t.tagName === "noscript" || t.tagName === "video"));
}
function us(n, e, t) {
  const r = A(t, e);
  return !r || r.type === "element" && r.tagName === "li";
}
function hs(n, e, t) {
  const r = A(t, e);
  return !!(r && r.type === "element" && (r.tagName === "dt" || r.tagName === "dd"));
}
function ds(n, e, t) {
  const r = A(t, e);
  return !r || r.type === "element" && (r.tagName === "dt" || r.tagName === "dd");
}
function wt(n, e, t) {
  const r = A(t, e);
  return !r || r.type === "element" && (r.tagName === "rp" || r.tagName === "rt");
}
function fs(n, e, t) {
  const r = A(t, e);
  return !r || r.type === "element" && r.tagName === "optgroup";
}
function ps(n, e, t) {
  const r = A(t, e);
  return !r || r.type === "element" && (r.tagName === "option" || r.tagName === "optgroup");
}
function gs(n, e, t) {
  const r = A(t, e);
  return !!(r && r.type === "element" && (r.tagName === "tbody" || r.tagName === "tfoot"));
}
function ms(n, e, t) {
  const r = A(t, e);
  return !r || r.type === "element" && (r.tagName === "tbody" || r.tagName === "tfoot");
}
function ys(n, e, t) {
  return !A(t, e);
}
function _s(n, e, t) {
  const r = A(t, e);
  return !r || r.type === "element" && r.tagName === "tr";
}
function kt(n, e, t) {
  const r = A(t, e);
  return !r || r.type === "element" && (r.tagName === "td" || r.tagName === "th");
}
const bs = cn({
  body: vs,
  colgroup: ws,
  head: Cs,
  html: Ss,
  tbody: ks
});
function Ss(n) {
  const e = A(n, -1);
  return !e || e.type !== "comment";
}
function Cs(n) {
  const e = /* @__PURE__ */ new Set();
  for (const r of n.children)
    if (r.type === "element" && (r.tagName === "base" || r.tagName === "title")) {
      if (e.has(r.tagName)) return !1;
      e.add(r.tagName);
    }
  const t = n.children[0];
  return !t || t.type === "element";
}
function vs(n) {
  const e = A(n, -1, !0);
  return !e || e.type !== "comment" && !(e.type === "text" && Ze(e.value.charAt(0))) && !(e.type === "element" && (e.tagName === "meta" || e.tagName === "link" || e.tagName === "script" || e.tagName === "style" || e.tagName === "template"));
}
function ws(n, e, t) {
  const r = ln(t, e), s = A(n, -1, !0);
  return t && r && r.type === "element" && r.tagName === "colgroup" && et(r, t.children.indexOf(r), t) ? !1 : !!(s && s.type === "element" && s.tagName === "col");
}
function ks(n, e, t) {
  const r = ln(t, e), s = A(n, -1);
  return t && r && r.type === "element" && (r.tagName === "thead" || r.tagName === "tbody") && et(r, t.children.indexOf(r), t) ? !1 : !!(s && s.type === "element" && s.tagName === "tr");
}
const de = {
  // See: <https://html.spec.whatwg.org/#attribute-name-state>.
  name: [
    [`	
\f\r &/=>`.split(""), `	
\f\r "&'/=>\``.split("")],
    [`\0	
\f\r "&'/<=>`.split(""), `\0	
\f\r "&'/<=>\``.split("")]
  ],
  // See: <https://html.spec.whatwg.org/#attribute-value-(unquoted)-state>.
  unquoted: [
    [`	
\f\r &>`.split(""), `\0	
\f\r "&'<=>\``.split("")],
    [`\0	
\f\r "&'<=>\``.split(""), `\0	
\f\r "&'<=>\``.split("")]
  ],
  // See: <https://html.spec.whatwg.org/#attribute-value-(single-quoted)-state>.
  single: [
    ["&'".split(""), "\"&'`".split("")],
    ["\0&'".split(""), "\0\"&'`".split("")]
  ],
  // See: <https://html.spec.whatwg.org/#attribute-value-(double-quoted)-state>.
  double: [
    ['"&'.split(""), "\"&'`".split("")],
    ['\0"&'.split(""), "\0\"&'`".split("")]
  ]
};
function Rs(n, e, t, r) {
  const s = r.schema, o = s.space === "svg" ? !1 : r.settings.omitOptionalTags;
  let i = s.space === "svg" ? r.settings.closeEmptyElements : r.settings.voids.includes(n.tagName.toLowerCase());
  const a = [];
  let l;
  s.space === "html" && n.tagName === "svg" && (r.schema = sn);
  const c = xs(r, n.properties), u = r.all(
    s.space === "html" && n.tagName === "template" ? n.content : n
  );
  return r.schema = s, u && (i = !1), (c || !o || !bs(n, e, t)) && (a.push("<", n.tagName, c ? " " + c : ""), i && (s.space === "svg" || r.settings.closeSelfClosing) && (l = c.charAt(c.length - 1), (!r.settings.tightSelfClosing || l === "/" || l && l !== '"' && l !== "'") && a.push(" "), a.push("/")), a.push(">")), a.push(u), !i && (!o || !et(n, e, t)) && a.push("</" + n.tagName + ">"), a.join("");
}
function xs(n, e) {
  const t = [];
  let r = -1, s;
  if (e) {
    for (s in e)
      if (e[s] !== null && e[s] !== void 0) {
        const o = As(n, s, e[s]);
        o && t.push(o);
      }
  }
  for (; ++r < t.length; ) {
    const o = n.settings.tightAttributes ? t[r].charAt(t[r].length - 1) : void 0;
    r !== t.length - 1 && o !== '"' && o !== "'" && (t[r] += " ");
  }
  return t.join("");
}
function As(n, e, t) {
  const r = Pr(n.schema, e), s = n.settings.allowParseErrors && n.schema.space === "html" ? 0 : 1, o = n.settings.allowDangerousCharacters ? 0 : 1;
  let i = n.quote, a;
  if (r.overloadedBoolean && (t === r.attribute || t === "") ? t = !0 : (r.boolean || r.overloadedBoolean) && (typeof t != "string" || t === r.attribute || t === "") && (t = !!t), t == null || t === !1 || typeof t == "number" && Number.isNaN(t))
    return "";
  const l = K(
    r.attribute,
    Object.assign({}, n.settings.characterReferences, {
      // Always encode without parse errors in non-HTML.
      subset: de.name[s][o]
    })
  );
  return t === !0 || (t = Array.isArray(t) ? (r.commaSeparated ? ns : rs)(t, {
    padLeft: !n.settings.tightCommaSeparatedLists
  }) : String(t), n.settings.collapseEmptyAttributes && !t) ? l : (n.settings.preferUnquoted && (a = K(
    t,
    Object.assign({}, n.settings.characterReferences, {
      attribute: !0,
      subset: de.unquoted[s][o]
    })
  )), a !== t && (n.settings.quoteSmart && Ct(t, i) > Ct(t, n.alternative) && (i = n.alternative), a = i + K(
    t,
    Object.assign({}, n.settings.characterReferences, {
      // Always encode without parse errors in non-HTML.
      subset: (i === "'" ? de.single : de.double)[s][o],
      attribute: !0
    })
  ) + i), l + (a && "=" + a));
}
const Ns = ["<", "&"];
function un(n, e, t, r) {
  return t && t.type === "element" && (t.tagName === "script" || t.tagName === "style") ? n.value : K(
    n.value,
    Object.assign({}, r.settings.characterReferences, {
      subset: Ns
    })
  );
}
function Ts(n, e, t, r) {
  return r.settings.allowDangerousHtml ? n.value : un(n, e, t, r);
}
function Ps(n, e, t, r) {
  return r.all(n);
}
const Is = Or("type", {
  invalid: Es,
  unknown: Ls,
  handlers: { comment: es, doctype: ts, element: Rs, raw: Ts, root: Ps, text: un }
});
function Es(n) {
  throw new Error("Expected node, not `" + n + "`");
}
function Ls(n) {
  const e = (
    /** @type {Nodes} */
    n
  );
  throw new Error("Cannot compile unknown node `" + e.type + "`");
}
const Os = {}, Ms = {}, Gs = [];
function Bs(n, e) {
  const t = e || Os, r = t.quote || '"', s = r === '"' ? "'" : '"';
  if (r !== '"' && r !== "'")
    throw new Error("Invalid quote `" + r + "`, expected `'` or `\"`");
  return {
    one: Ds,
    all: $s,
    settings: {
      omitOptionalTags: t.omitOptionalTags || !1,
      allowParseErrors: t.allowParseErrors || !1,
      allowDangerousCharacters: t.allowDangerousCharacters || !1,
      quoteSmart: t.quoteSmart || !1,
      preferUnquoted: t.preferUnquoted || !1,
      tightAttributes: t.tightAttributes || !1,
      upperDoctype: t.upperDoctype || !1,
      tightDoctype: t.tightDoctype || !1,
      bogusComments: t.bogusComments || !1,
      tightCommaSeparatedLists: t.tightCommaSeparatedLists || !1,
      tightSelfClosing: t.tightSelfClosing || !1,
      collapseEmptyAttributes: t.collapseEmptyAttributes || !1,
      allowDangerousHtml: t.allowDangerousHtml || !1,
      voids: t.voids || kr,
      characterReferences: t.characterReferences || Ms,
      closeSelfClosing: t.closeSelfClosing || !1,
      closeEmptyElements: t.closeEmptyElements || !1
    },
    schema: t.space === "svg" ? sn : Lr,
    quote: r,
    alternative: s
  }.one(
    Array.isArray(n) ? { type: "root", children: n } : n,
    void 0,
    void 0
  );
}
function Ds(n, e, t) {
  return Is(n, e, t, this);
}
function $s(n) {
  const e = [], t = n && n.children || Gs;
  let r = -1;
  for (; ++r < t.length; )
    e[r] = this.one(t[r], r, n);
  return e.join("");
}
function Se(n, e) {
  const t = typeof n == "string" ? {} : { ...n.colorReplacements }, r = typeof n == "string" ? n : n.name;
  for (const [s, o] of Object.entries((e == null ? void 0 : e.colorReplacements) || {}))
    typeof o == "string" ? t[s] = o : s === r && Object.assign(t, o);
  return t;
}
function F(n, e) {
  return n && ((e == null ? void 0 : e[n == null ? void 0 : n.toLowerCase()]) || n);
}
function js(n) {
  return Array.isArray(n) ? n : [n];
}
async function hn(n) {
  return Promise.resolve(typeof n == "function" ? n() : n).then((e) => e.default || e);
}
function tt(n) {
  return !n || ["plaintext", "txt", "text", "plain"].includes(n);
}
function Fs(n) {
  return n === "ansi" || tt(n);
}
function nt(n) {
  return n === "none";
}
function Ws(n) {
  return nt(n);
}
function dn(n, e) {
  var r;
  if (!e)
    return n;
  n.properties || (n.properties = {}), (r = n.properties).class || (r.class = []), typeof n.properties.class == "string" && (n.properties.class = n.properties.class.split(/\s+/g)), Array.isArray(n.properties.class) || (n.properties.class = []);
  const t = Array.isArray(e) ? e : e.split(/\s+/g);
  for (const s of t)
    s && !n.properties.class.includes(s) && n.properties.class.push(s);
  return n;
}
function Ae(n, e = !1) {
  var o;
  const t = n.split(/(\r?\n)/g);
  let r = 0;
  const s = [];
  for (let i = 0; i < t.length; i += 2) {
    const a = e ? t[i] + (t[i + 1] || "") : t[i];
    s.push([a, r]), r += t[i].length, r += ((o = t[i + 1]) == null ? void 0 : o.length) || 0;
  }
  return s;
}
function zs(n) {
  const e = Ae(n, !0).map(([s]) => s);
  function t(s) {
    if (s === n.length)
      return {
        line: e.length - 1,
        character: e[e.length - 1].length
      };
    let o = s, i = 0;
    for (const a of e) {
      if (o < a.length)
        break;
      o -= a.length, i++;
    }
    return { line: i, character: o };
  }
  function r(s, o) {
    let i = 0;
    for (let a = 0; a < s; a++)
      i += e[a].length;
    return i += o, i;
  }
  return {
    lines: e,
    indexToPos: t,
    posToIndex: r
  };
}
const rt = "light-dark()", Us = ["color", "background-color"];
function qs(n, e) {
  let t = 0;
  const r = [];
  for (const s of e)
    s > t && r.push({
      ...n,
      content: n.content.slice(t, s),
      offset: n.offset + t
    }), t = s;
  return t < n.content.length && r.push({
    ...n,
    content: n.content.slice(t),
    offset: n.offset + t
  }), r;
}
function Hs(n, e) {
  const t = Array.from(e instanceof Set ? e : new Set(e)).sort((r, s) => r - s);
  return t.length ? n.map((r) => r.flatMap((s) => {
    const o = t.filter((i) => s.offset < i && i < s.offset + s.content.length).map((i) => i - s.offset).sort((i, a) => i - a);
    return o.length ? qs(s, o) : s;
  })) : n;
}
function Vs(n, e, t, r, s = "css-vars") {
  const o = {
    content: n.content,
    explanation: n.explanation,
    offset: n.offset
  }, i = e.map((u) => Ce(n.variants[u])), a = new Set(i.flatMap((u) => Object.keys(u))), l = {}, c = (u, h) => {
    const d = h === "color" ? "" : h === "background-color" ? "-bg" : `-${h}`;
    return t + e[u] + (h === "color" ? "" : d);
  };
  return i.forEach((u, h) => {
    for (const d of a) {
      const p = u[d] || "inherit";
      if (h === 0 && r && Us.includes(d))
        if (r === rt && i.length > 1) {
          const g = e.findIndex((y) => y === "light"), C = e.findIndex((y) => y === "dark");
          if (g === -1 || C === -1)
            throw new T('When using `defaultColor: "light-dark()"`, you must provide both `light` and `dark` themes');
          const S = i[g][d] || "inherit", _ = i[C][d] || "inherit";
          l[d] = `light-dark(${S}, ${_})`, s === "css-vars" && (l[c(h, d)] = p);
        } else
          l[d] = p;
      else
        s === "css-vars" && (l[c(h, d)] = p);
    }
  }), o.htmlStyle = l, o;
}
function Ce(n) {
  const e = {};
  if (n.color && (e.color = n.color), n.bgColor && (e["background-color"] = n.bgColor), n.fontStyle) {
    n.fontStyle & I.Italic && (e["font-style"] = "italic"), n.fontStyle & I.Bold && (e["font-weight"] = "bold");
    const t = [];
    n.fontStyle & I.Underline && t.push("underline"), n.fontStyle & I.Strikethrough && t.push("line-through"), t.length && (e["text-decoration"] = t.join(" "));
  }
  return e;
}
function Ye(n) {
  return typeof n == "string" ? n : Object.entries(n).map(([e, t]) => `${e}:${t}`).join(";");
}
const fn = /* @__PURE__ */ new WeakMap();
function Ne(n, e) {
  fn.set(n, e);
}
function ie(n) {
  return fn.get(n);
}
class Q {
  constructor(...e) {
    /**
     * Theme to Stack mapping
     */
    f(this, "_stacks", {});
    f(this, "lang");
    if (e.length === 2) {
      const [t, r] = e;
      this.lang = r, this._stacks = t;
    } else {
      const [t, r, s] = e;
      this.lang = r, this._stacks = { [s]: t };
    }
  }
  get themes() {
    return Object.keys(this._stacks);
  }
  get theme() {
    return this.themes[0];
  }
  get _stack() {
    return this._stacks[this.theme];
  }
  /**
   * Static method to create a initial grammar state.
   */
  static initial(e, t) {
    return new Q(
      Object.fromEntries(js(t).map((r) => [r, Ue])),
      e
    );
  }
  /**
   * Get the internal stack object.
   * @internal
   */
  getInternalStack(e = this.theme) {
    return this._stacks[e];
  }
  getScopes(e = this.theme) {
    return Ks(this._stacks[e]);
  }
  toJSON() {
    return {
      lang: this.lang,
      theme: this.theme,
      themes: this.themes,
      scopes: this.getScopes()
    };
  }
}
function Ks(n) {
  const e = [], t = /* @__PURE__ */ new Set();
  function r(s) {
    var i;
    if (t.has(s))
      return;
    t.add(s);
    const o = (i = s == null ? void 0 : s.nameScopesList) == null ? void 0 : i.scopeName;
    o && e.push(o), s.parent && r(s.parent);
  }
  return r(n), e;
}
function Ys(n, e) {
  if (!(n instanceof Q))
    throw new T("Invalid grammar state");
  return n.getInternalStack(e);
}
function Xs() {
  const n = /* @__PURE__ */ new WeakMap();
  function e(t) {
    if (!n.has(t.meta)) {
      let r = function(i) {
        if (typeof i == "number") {
          if (i < 0 || i > t.source.length)
            throw new T(`Invalid decoration offset: ${i}. Code length: ${t.source.length}`);
          return {
            ...s.indexToPos(i),
            offset: i
          };
        } else {
          const a = s.lines[i.line];
          if (a === void 0)
            throw new T(`Invalid decoration position ${JSON.stringify(i)}. Lines length: ${s.lines.length}`);
          let l = i.character;
          if (l < 0 && (l = a.length + l), l < 0 || l > a.length)
            throw new T(`Invalid decoration position ${JSON.stringify(i)}. Line ${i.line} length: ${a.length}`);
          return {
            ...i,
            character: l,
            offset: s.posToIndex(i.line, l)
          };
        }
      };
      const s = zs(t.source), o = (t.options.decorations || []).map((i) => ({
        ...i,
        start: r(i.start),
        end: r(i.end)
      }));
      Js(o), n.set(t.meta, {
        decorations: o,
        converter: s,
        source: t.source
      });
    }
    return n.get(t.meta);
  }
  return {
    name: "shiki:decorations",
    tokens(t) {
      var i;
      if (!((i = this.options.decorations) != null && i.length))
        return;
      const s = e(this).decorations.flatMap((a) => [a.start.offset, a.end.offset]);
      return Hs(t, s);
    },
    code(t) {
      var u;
      if (!((u = this.options.decorations) != null && u.length))
        return;
      const r = e(this), s = Array.from(t.children).filter((h) => h.type === "element" && h.tagName === "span");
      if (s.length !== r.converter.lines.length)
        throw new T(`Number of lines in code element (${s.length}) does not match the number of lines in the source (${r.converter.lines.length}). Failed to apply decorations.`);
      function o(h, d, p, g) {
        const C = s[h];
        let S = "", _ = -1, y = -1;
        if (d === 0 && (_ = 0), p === 0 && (y = 0), p === Number.POSITIVE_INFINITY && (y = C.children.length), _ === -1 || y === -1)
          for (let w = 0; w < C.children.length; w++)
            S += pn(C.children[w]), _ === -1 && S.length === d && (_ = w + 1), y === -1 && S.length === p && (y = w + 1);
        if (_ === -1)
          throw new T(`Failed to find start index for decoration ${JSON.stringify(g.start)}`);
        if (y === -1)
          throw new T(`Failed to find end index for decoration ${JSON.stringify(g.end)}`);
        const b = C.children.slice(_, y);
        if (!g.alwaysWrap && b.length === C.children.length)
          a(C, g, "line");
        else if (!g.alwaysWrap && b.length === 1 && b[0].type === "element")
          a(b[0], g, "token");
        else {
          const w = {
            type: "element",
            tagName: "span",
            properties: {},
            children: b
          };
          a(w, g, "wrapper"), C.children.splice(_, b.length, w);
        }
      }
      function i(h, d) {
        s[h] = a(s[h], d, "line");
      }
      function a(h, d, p) {
        var S;
        const g = d.properties || {}, C = d.transform || ((_) => _);
        return h.tagName = d.tagName || "span", h.properties = {
          ...h.properties,
          ...g,
          class: h.properties.class
        }, (S = d.properties) != null && S.class && dn(h, d.properties.class), h = C(h, p) || h, h;
      }
      const l = [], c = r.decorations.sort((h, d) => d.start.offset - h.start.offset || h.end.offset - d.end.offset);
      for (const h of c) {
        const { start: d, end: p } = h;
        if (d.line === p.line)
          o(d.line, d.character, p.character, h);
        else if (d.line < p.line) {
          o(d.line, d.character, Number.POSITIVE_INFINITY, h);
          for (let g = d.line + 1; g < p.line; g++)
            l.unshift(() => i(g, h));
          o(p.line, 0, p.character, h);
        }
      }
      l.forEach((h) => h());
    }
  };
}
function Js(n) {
  for (let e = 0; e < n.length; e++) {
    const t = n[e];
    if (t.start.offset > t.end.offset)
      throw new T(`Invalid decoration range: ${JSON.stringify(t.start)} - ${JSON.stringify(t.end)}`);
    for (let r = e + 1; r < n.length; r++) {
      const s = n[r], o = t.start.offset <= s.start.offset && s.start.offset < t.end.offset, i = t.start.offset < s.end.offset && s.end.offset <= t.end.offset, a = s.start.offset <= t.start.offset && t.start.offset < s.end.offset, l = s.start.offset < t.end.offset && t.end.offset <= s.end.offset;
      if (o || i || a || l) {
        if (o && i || a && l || a && t.start.offset === t.end.offset || i && s.start.offset === s.end.offset)
          continue;
        throw new T(`Decorations ${JSON.stringify(t.start)} and ${JSON.stringify(s.start)} intersect.`);
      }
    }
  }
}
function pn(n) {
  return n.type === "text" ? n.value : n.type === "element" ? n.children.map(pn).join("") : "";
}
const Qs = [
  /* @__PURE__ */ Xs()
];
function ve(n) {
  const e = Zs(n.transformers || []);
  return [
    ...e.pre,
    ...e.normal,
    ...e.post,
    ...Qs
  ];
}
function Zs(n) {
  const e = [], t = [], r = [];
  for (const s of n)
    switch (s.enforce) {
      case "pre":
        e.push(s);
        break;
      case "post":
        t.push(s);
        break;
      default:
        r.push(s);
    }
  return { pre: e, post: t, normal: r };
}
var W = [
  "black",
  "red",
  "green",
  "yellow",
  "blue",
  "magenta",
  "cyan",
  "white",
  "brightBlack",
  "brightRed",
  "brightGreen",
  "brightYellow",
  "brightBlue",
  "brightMagenta",
  "brightCyan",
  "brightWhite"
], De = {
  1: "bold",
  2: "dim",
  3: "italic",
  4: "underline",
  7: "reverse",
  8: "hidden",
  9: "strikethrough"
};
function eo(n, e) {
  const t = n.indexOf("\x1B", e);
  if (t !== -1 && n[t + 1] === "[") {
    const r = n.indexOf("m", t);
    if (r !== -1)
      return {
        sequence: n.substring(t + 2, r).split(";"),
        startPosition: t,
        position: r + 1
      };
  }
  return {
    position: n.length
  };
}
function Rt(n) {
  const e = n.shift();
  if (e === "2") {
    const t = n.splice(0, 3).map((r) => Number.parseInt(r));
    return t.length !== 3 || t.some((r) => Number.isNaN(r)) ? void 0 : {
      type: "rgb",
      rgb: t
    };
  } else if (e === "5") {
    const t = n.shift();
    if (t)
      return { type: "table", index: Number(t) };
  }
}
function to(n) {
  const e = [];
  for (; n.length > 0; ) {
    const t = n.shift();
    if (!t)
      continue;
    const r = Number.parseInt(t);
    if (!Number.isNaN(r))
      if (r === 0)
        e.push({ type: "resetAll" });
      else if (r <= 9)
        De[r] && e.push({
          type: "setDecoration",
          value: De[r]
        });
      else if (r <= 29) {
        const s = De[r - 20];
        s && (e.push({
          type: "resetDecoration",
          value: s
        }), s === "dim" && e.push({
          type: "resetDecoration",
          value: "bold"
        }));
      } else if (r <= 37)
        e.push({
          type: "setForegroundColor",
          value: { type: "named", name: W[r - 30] }
        });
      else if (r === 38) {
        const s = Rt(n);
        s && e.push({
          type: "setForegroundColor",
          value: s
        });
      } else if (r === 39)
        e.push({
          type: "resetForegroundColor"
        });
      else if (r <= 47)
        e.push({
          type: "setBackgroundColor",
          value: { type: "named", name: W[r - 40] }
        });
      else if (r === 48) {
        const s = Rt(n);
        s && e.push({
          type: "setBackgroundColor",
          value: s
        });
      } else r === 49 ? e.push({
        type: "resetBackgroundColor"
      }) : r === 53 ? e.push({
        type: "setDecoration",
        value: "overline"
      }) : r === 55 ? e.push({
        type: "resetDecoration",
        value: "overline"
      }) : r >= 90 && r <= 97 ? e.push({
        type: "setForegroundColor",
        value: { type: "named", name: W[r - 90 + 8] }
      }) : r >= 100 && r <= 107 && e.push({
        type: "setBackgroundColor",
        value: { type: "named", name: W[r - 100 + 8] }
      });
  }
  return e;
}
function no() {
  let n = null, e = null, t = /* @__PURE__ */ new Set();
  return {
    parse(r) {
      const s = [];
      let o = 0;
      do {
        const i = eo(r, o), a = i.sequence ? r.substring(o, i.startPosition) : r.substring(o);
        if (a.length > 0 && s.push({
          value: a,
          foreground: n,
          background: e,
          decorations: new Set(t)
        }), i.sequence) {
          const l = to(i.sequence);
          for (const c of l)
            c.type === "resetAll" ? (n = null, e = null, t.clear()) : c.type === "resetForegroundColor" ? n = null : c.type === "resetBackgroundColor" ? e = null : c.type === "resetDecoration" && t.delete(c.value);
          for (const c of l)
            c.type === "setForegroundColor" ? n = c.value : c.type === "setBackgroundColor" ? e = c.value : c.type === "setDecoration" && t.add(c.value);
        }
        o = i.position;
      } while (o < r.length);
      return s;
    }
  };
}
var ro = {
  black: "#000000",
  red: "#bb0000",
  green: "#00bb00",
  yellow: "#bbbb00",
  blue: "#0000bb",
  magenta: "#ff00ff",
  cyan: "#00bbbb",
  white: "#eeeeee",
  brightBlack: "#555555",
  brightRed: "#ff5555",
  brightGreen: "#00ff00",
  brightYellow: "#ffff55",
  brightBlue: "#5555ff",
  brightMagenta: "#ff55ff",
  brightCyan: "#55ffff",
  brightWhite: "#ffffff"
};
function so(n = ro) {
  function e(a) {
    return n[a];
  }
  function t(a) {
    return `#${a.map((l) => Math.max(0, Math.min(l, 255)).toString(16).padStart(2, "0")).join("")}`;
  }
  let r;
  function s() {
    if (r)
      return r;
    r = [];
    for (let c = 0; c < W.length; c++)
      r.push(e(W[c]));
    let a = [0, 95, 135, 175, 215, 255];
    for (let c = 0; c < 6; c++)
      for (let u = 0; u < 6; u++)
        for (let h = 0; h < 6; h++)
          r.push(t([a[c], a[u], a[h]]));
    let l = 8;
    for (let c = 0; c < 24; c++, l += 10)
      r.push(t([l, l, l]));
    return r;
  }
  function o(a) {
    return s()[a];
  }
  function i(a) {
    switch (a.type) {
      case "named":
        return e(a.name);
      case "rgb":
        return t(a.rgb);
      case "table":
        return o(a.index);
    }
  }
  return {
    value: i
  };
}
function oo(n, e, t) {
  const r = Se(n, t), s = Ae(e), o = so(
    Object.fromEntries(
      W.map((a) => {
        var l;
        return [
          a,
          (l = n.colors) == null ? void 0 : l[`terminal.ansi${a[0].toUpperCase()}${a.substring(1)}`]
        ];
      })
    )
  ), i = no();
  return s.map(
    (a) => i.parse(a[0]).map((l) => {
      let c, u;
      l.decorations.has("reverse") ? (c = l.background ? o.value(l.background) : n.bg, u = l.foreground ? o.value(l.foreground) : n.fg) : (c = l.foreground ? o.value(l.foreground) : n.fg, u = l.background ? o.value(l.background) : void 0), c = F(c, r), u = F(u, r), l.decorations.has("dim") && (c = io(c));
      let h = I.None;
      return l.decorations.has("bold") && (h |= I.Bold), l.decorations.has("italic") && (h |= I.Italic), l.decorations.has("underline") && (h |= I.Underline), l.decorations.has("strikethrough") && (h |= I.Strikethrough), {
        content: l.value,
        offset: a[1],
        // TODO: more accurate offset? might need to fork ansi-sequence-parser
        color: c,
        bgColor: u,
        fontStyle: h
      };
    })
  );
}
function io(n) {
  const e = n.match(/#([0-9a-f]{3})([0-9a-f]{3})?([0-9a-f]{2})?/);
  if (e)
    if (e[3]) {
      const r = Math.round(Number.parseInt(e[3], 16) / 2).toString(16).padStart(2, "0");
      return `#${e[1]}${e[2]}${r}`;
    } else return e[2] ? `#${e[1]}${e[2]}80` : `#${Array.from(e[1]).map((r) => `${r}${r}`).join("")}80`;
  const t = n.match(/var\((--[\w-]+-ansi-[\w-]+)\)/);
  return t ? `var(${t[1]}-dim)` : n;
}
function st(n, e, t = {}) {
  const {
    lang: r = "text",
    theme: s = n.getLoadedThemes()[0]
  } = t;
  if (tt(r) || nt(s))
    return Ae(e).map((l) => [{ content: l[0], offset: l[1] }]);
  const { theme: o, colorMap: i } = n.setTheme(s);
  if (r === "ansi")
    return oo(o, e, t);
  const a = n.getLanguage(r);
  if (t.grammarState) {
    if (t.grammarState.lang !== a.name)
      throw new T(`Grammar state language "${t.grammarState.lang}" does not match highlight language "${a.name}"`);
    if (!t.grammarState.themes.includes(o.name))
      throw new T(`Grammar state themes "${t.grammarState.themes}" do not contain highlight theme "${o.name}"`);
  }
  return ao(e, a, o, i, t);
}
function lo(...n) {
  if (n.length === 2)
    return ie(n[1]);
  const [e, t, r = {}] = n, {
    lang: s = "text",
    theme: o = e.getLoadedThemes()[0]
  } = r;
  if (tt(s) || nt(o))
    throw new T("Plain language does not have grammar state");
  if (s === "ansi")
    throw new T("ANSI language does not have grammar state");
  const { theme: i, colorMap: a } = e.setTheme(o), l = e.getLanguage(s);
  return new Q(
    we(t, l, i, a, r).stateStack,
    l.name,
    i.name
  );
}
function ao(n, e, t, r, s) {
  const o = we(n, e, t, r, s), i = new Q(
    we(n, e, t, r, s).stateStack,
    e.name,
    t.name
  );
  return Ne(o.tokens, i), o.tokens;
}
function we(n, e, t, r, s) {
  const o = Se(t, s), {
    tokenizeMaxLineLength: i = 0,
    tokenizeTimeLimit: a = 500
  } = s, l = Ae(n);
  let c = s.grammarState ? Ys(s.grammarState, t.name) ?? Ue : s.grammarContextCode != null ? we(
    s.grammarContextCode,
    e,
    t,
    r,
    {
      ...s,
      grammarState: void 0,
      grammarContextCode: void 0
    }
  ).stateStack : Ue, u = [];
  const h = [];
  for (let d = 0, p = l.length; d < p; d++) {
    const [g, C] = l[d];
    if (g === "") {
      u = [], h.push([]);
      continue;
    }
    if (i > 0 && g.length >= i) {
      u = [], h.push([{
        content: g,
        offset: C,
        color: "",
        fontStyle: 0
      }]);
      continue;
    }
    let S, _, y;
    s.includeExplanation && (S = e.tokenizeLine(g, c, a), _ = S.tokens, y = 0);
    const b = e.tokenizeLine2(g, c, a), w = b.tokens.length / 2;
    for (let R = 0; R < w; R++) {
      const G = b.tokens[2 * R], N = R + 1 < w ? b.tokens[2 * R + 2] : g.length;
      if (G === N)
        continue;
      const D = b.tokens[2 * R + 1], ce = F(
        r[X.getForeground(D)],
        o
      ), Z = X.getFontStyle(D), Te = {
        content: g.substring(G, N),
        offset: C + G,
        color: ce,
        fontStyle: Z
      };
      if (s.includeExplanation) {
        const it = [];
        if (s.includeExplanation !== "scopeName")
          for (const $ of t.settings) {
            let U;
            switch (typeof $.scope) {
              case "string":
                U = $.scope.split(/,/).map((Pe) => Pe.trim());
                break;
              case "object":
                U = $.scope;
                break;
              default:
                continue;
            }
            it.push({
              settings: $,
              selectors: U.map((Pe) => Pe.split(/ /))
            });
          }
        Te.explanation = [];
        let lt = 0;
        for (; G + lt < N; ) {
          const $ = _[y], U = g.substring(
            $.startIndex,
            $.endIndex
          );
          lt += U.length, Te.explanation.push({
            content: U,
            scopes: s.includeExplanation === "scopeName" ? co(
              $.scopes
            ) : uo(
              it,
              $.scopes
            )
          }), y += 1;
        }
      }
      u.push(Te);
    }
    h.push(u), u = [], c = b.ruleStack;
  }
  return {
    tokens: h,
    stateStack: c
  };
}
function co(n) {
  return n.map((e) => ({ scopeName: e }));
}
function uo(n, e) {
  const t = [];
  for (let r = 0, s = e.length; r < s; r++) {
    const o = e[r];
    t[r] = {
      scopeName: o,
      themeMatches: fo(n, o, e.slice(0, r))
    };
  }
  return t;
}
function xt(n, e) {
  return n === e || e.substring(0, n.length) === n && e[n.length] === ".";
}
function ho(n, e, t) {
  if (!xt(n[n.length - 1], e))
    return !1;
  let r = n.length - 2, s = t.length - 1;
  for (; r >= 0 && s >= 0; )
    xt(n[r], t[s]) && (r -= 1), s -= 1;
  return r === -1;
}
function fo(n, e, t) {
  const r = [];
  for (const { selectors: s, settings: o } of n)
    for (const i of s)
      if (ho(i, e, t)) {
        r.push(o);
        break;
      }
  return r;
}
function gn(n, e, t) {
  const r = Object.entries(t.themes).filter((l) => l[1]).map((l) => ({ color: l[0], theme: l[1] })), s = r.map((l) => {
    const c = st(n, e, {
      ...t,
      theme: l.theme
    }), u = ie(c), h = typeof l.theme == "string" ? l.theme : l.theme.name;
    return {
      tokens: c,
      state: u,
      theme: h
    };
  }), o = po(
    ...s.map((l) => l.tokens)
  ), i = o[0].map(
    (l, c) => l.map((u, h) => {
      const d = {
        content: u.content,
        variants: {},
        offset: u.offset
      };
      return "includeExplanation" in t && t.includeExplanation && (d.explanation = u.explanation), o.forEach((p, g) => {
        const {
          content: C,
          explanation: S,
          offset: _,
          ...y
        } = p[c][h];
        d.variants[r[g].color] = y;
      }), d;
    })
  ), a = s[0].state ? new Q(
    Object.fromEntries(s.map((l) => {
      var c;
      return [l.theme, (c = l.state) == null ? void 0 : c.getInternalStack(l.theme)];
    })),
    s[0].state.lang
  ) : void 0;
  return a && Ne(i, a), i;
}
function po(...n) {
  const e = n.map(() => []), t = n.length;
  for (let r = 0; r < n[0].length; r++) {
    const s = n.map((l) => l[r]), o = e.map(() => []);
    e.forEach((l, c) => l.push(o[c]));
    const i = s.map(() => 0), a = s.map((l) => l[0]);
    for (; a.every((l) => l); ) {
      const l = Math.min(...a.map((c) => c.content.length));
      for (let c = 0; c < t; c++) {
        const u = a[c];
        u.content.length === l ? (o[c].push(u), i[c] += 1, a[c] = s[c][i[c]]) : (o[c].push({
          ...u,
          content: u.content.slice(0, l)
        }), a[c] = {
          ...u,
          content: u.content.slice(l),
          offset: u.offset + l
        });
      }
    }
  }
  return e;
}
function ke(n, e, t) {
  let r, s, o, i, a, l;
  if ("themes" in t) {
    const {
      defaultColor: c = "light",
      cssVariablePrefix: u = "--shiki-",
      colorsRendering: h = "css-vars"
    } = t, d = Object.entries(t.themes).filter((_) => _[1]).map((_) => ({ color: _[0], theme: _[1] })).sort((_, y) => _.color === c ? -1 : y.color === c ? 1 : 0);
    if (d.length === 0)
      throw new T("`themes` option must not be empty");
    const p = gn(
      n,
      e,
      t
    );
    if (l = ie(p), c && rt !== c && !d.find((_) => _.color === c))
      throw new T(`\`themes\` option must contain the defaultColor key \`${c}\``);
    const g = d.map((_) => n.getTheme(_.theme)), C = d.map((_) => _.color);
    o = p.map((_) => _.map((y) => Vs(y, C, u, c, h))), l && Ne(o, l);
    const S = d.map((_) => Se(_.theme, t));
    s = At(d, g, S, u, c, "fg", h), r = At(d, g, S, u, c, "bg", h), i = `shiki-themes ${g.map((_) => _.name).join(" ")}`, a = c ? void 0 : [s, r].join(";");
  } else if ("theme" in t) {
    const c = Se(t.theme, t);
    o = st(
      n,
      e,
      t
    );
    const u = n.getTheme(t.theme);
    r = F(u.bg, c), s = F(u.fg, c), i = u.name, l = ie(o);
  } else
    throw new T("Invalid options, either `theme` or `themes` must be provided");
  return {
    tokens: o,
    fg: s,
    bg: r,
    themeName: i,
    rootStyle: a,
    grammarState: l
  };
}
function At(n, e, t, r, s, o, i) {
  return n.map((a, l) => {
    const c = F(e[l][o], t[l]) || "inherit", u = `${r + a.color}${o === "bg" ? "-bg" : ""}:${c}`;
    if (l === 0 && s) {
      if (s === rt && n.length > 1) {
        const h = n.findIndex((C) => C.color === "light"), d = n.findIndex((C) => C.color === "dark");
        if (h === -1 || d === -1)
          throw new T('When using `defaultColor: "light-dark()"`, you must provide both `light` and `dark` themes');
        const p = F(e[h][o], t[h]) || "inherit", g = F(e[d][o], t[d]) || "inherit";
        return `light-dark(${p}, ${g});${u}`;
      }
      return c;
    }
    return i === "css-vars" ? u : null;
  }).filter((a) => !!a).join(";");
}
function Re(n, e, t, r = {
  meta: {},
  options: t,
  codeToHast: (s, o) => Re(n, s, o),
  codeToTokens: (s, o) => ke(n, s, o)
}) {
  var g, C;
  let s = e;
  for (const S of ve(t))
    s = ((g = S.preprocess) == null ? void 0 : g.call(r, s, t)) || s;
  let {
    tokens: o,
    fg: i,
    bg: a,
    themeName: l,
    rootStyle: c,
    grammarState: u
  } = ke(n, s, t);
  const {
    mergeWhitespaces: h = !0,
    mergeSameStyleTokens: d = !1
  } = t;
  h === !0 ? o = mo(o) : h === "never" && (o = yo(o)), d && (o = _o(o));
  const p = {
    ...r,
    get source() {
      return s;
    }
  };
  for (const S of ve(t))
    o = ((C = S.tokens) == null ? void 0 : C.call(p, o)) || o;
  return go(
    o,
    {
      ...t,
      fg: i,
      bg: a,
      themeName: l,
      rootStyle: c
    },
    p,
    u
  );
}
function go(n, e, t, r = ie(n)) {
  var g, C, S;
  const s = ve(e), o = [], i = {
    type: "root",
    children: []
  }, {
    structure: a = "classic",
    tabindex: l = "0"
  } = e;
  let c = {
    type: "element",
    tagName: "pre",
    properties: {
      class: `shiki ${e.themeName || ""}`,
      style: e.rootStyle || `background-color:${e.bg};color:${e.fg}`,
      ...l !== !1 && l != null ? {
        tabindex: l.toString()
      } : {},
      ...Object.fromEntries(
        Array.from(
          Object.entries(e.meta || {})
        ).filter(([_]) => !_.startsWith("_"))
      )
    },
    children: []
  }, u = {
    type: "element",
    tagName: "code",
    properties: {},
    children: o
  };
  const h = [], d = {
    ...t,
    structure: a,
    addClassToHast: dn,
    get source() {
      return t.source;
    },
    get tokens() {
      return n;
    },
    get options() {
      return e;
    },
    get root() {
      return i;
    },
    get pre() {
      return c;
    },
    get code() {
      return u;
    },
    get lines() {
      return h;
    }
  };
  if (n.forEach((_, y) => {
    var R, G;
    y && (a === "inline" ? i.children.push({ type: "element", tagName: "br", properties: {}, children: [] }) : a === "classic" && o.push({ type: "text", value: `
` }));
    let b = {
      type: "element",
      tagName: "span",
      properties: { class: "line" },
      children: []
    }, w = 0;
    for (const N of _) {
      let D = {
        type: "element",
        tagName: "span",
        properties: {
          ...N.htmlAttrs
        },
        children: [{ type: "text", value: N.content }]
      };
      const ce = Ye(N.htmlStyle || Ce(N));
      ce && (D.properties.style = ce);
      for (const Z of s)
        D = ((R = Z == null ? void 0 : Z.span) == null ? void 0 : R.call(d, D, y + 1, w, b, N)) || D;
      a === "inline" ? i.children.push(D) : a === "classic" && b.children.push(D), w += N.content.length;
    }
    if (a === "classic") {
      for (const N of s)
        b = ((G = N == null ? void 0 : N.line) == null ? void 0 : G.call(d, b, y + 1)) || b;
      h.push(b), o.push(b);
    }
  }), a === "classic") {
    for (const _ of s)
      u = ((g = _ == null ? void 0 : _.code) == null ? void 0 : g.call(d, u)) || u;
    c.children.push(u);
    for (const _ of s)
      c = ((C = _ == null ? void 0 : _.pre) == null ? void 0 : C.call(d, c)) || c;
    i.children.push(c);
  }
  let p = i;
  for (const _ of s)
    p = ((S = _ == null ? void 0 : _.root) == null ? void 0 : S.call(d, p)) || p;
  return r && Ne(p, r), p;
}
function mo(n) {
  return n.map((e) => {
    const t = [];
    let r = "", s = 0;
    return e.forEach((o, i) => {
      const l = !(o.fontStyle && (o.fontStyle & I.Underline || o.fontStyle & I.Strikethrough));
      l && o.content.match(/^\s+$/) && e[i + 1] ? (s || (s = o.offset), r += o.content) : r ? (l ? t.push({
        ...o,
        offset: s,
        content: r + o.content
      }) : t.push(
        {
          content: r,
          offset: s
        },
        o
      ), s = 0, r = "") : t.push(o);
    }), t;
  });
}
function yo(n) {
  return n.map((e) => e.flatMap((t) => {
    if (t.content.match(/^\s+$/))
      return t;
    const r = t.content.match(/^(\s*)(.*?)(\s*)$/);
    if (!r)
      return t;
    const [, s, o, i] = r;
    if (!s && !i)
      return t;
    const a = [{
      ...t,
      offset: t.offset + s.length,
      content: o
    }];
    return s && a.unshift({
      content: s,
      offset: t.offset
    }), i && a.push({
      content: i,
      offset: t.offset + s.length + o.length
    }), a;
  }));
}
function _o(n) {
  return n.map((e) => {
    const t = [];
    for (const r of e) {
      if (t.length === 0) {
        t.push({ ...r });
        continue;
      }
      const s = t[t.length - 1], o = Ye(s.htmlStyle || Ce(s)), i = Ye(r.htmlStyle || Ce(r)), a = s.fontStyle && (s.fontStyle & I.Underline || s.fontStyle & I.Strikethrough), l = r.fontStyle && (r.fontStyle & I.Underline || r.fontStyle & I.Strikethrough);
      !a && !l && o === i ? s.content += r.content : t.push({ ...r });
    }
    return t;
  });
}
const bo = Bs;
function So(n, e, t) {
  var o;
  const r = {
    meta: {},
    options: t,
    codeToHast: (i, a) => Re(n, i, a),
    codeToTokens: (i, a) => ke(n, i, a)
  };
  let s = bo(Re(n, e, t, r));
  for (const i of ve(t))
    s = ((o = i.postprocess) == null ? void 0 : o.call(r, s, t)) || s;
  return s;
}
const Nt = { light: "#333333", dark: "#bbbbbb" }, Tt = { light: "#fffffe", dark: "#1e1e1e" }, Pt = "__shiki_resolved";
function ot(n) {
  var a, l, c, u, h;
  if (n != null && n[Pt])
    return n;
  const e = {
    ...n
  };
  e.tokenColors && !e.settings && (e.settings = e.tokenColors, delete e.tokenColors), e.type || (e.type = "dark"), e.colorReplacements = { ...e.colorReplacements }, e.settings || (e.settings = []);
  let { bg: t, fg: r } = e;
  if (!t || !r) {
    const d = e.settings ? e.settings.find((p) => !p.name && !p.scope) : void 0;
    (a = d == null ? void 0 : d.settings) != null && a.foreground && (r = d.settings.foreground), (l = d == null ? void 0 : d.settings) != null && l.background && (t = d.settings.background), !r && ((c = e == null ? void 0 : e.colors) != null && c["editor.foreground"]) && (r = e.colors["editor.foreground"]), !t && ((u = e == null ? void 0 : e.colors) != null && u["editor.background"]) && (t = e.colors["editor.background"]), r || (r = e.type === "light" ? Nt.light : Nt.dark), t || (t = e.type === "light" ? Tt.light : Tt.dark), e.fg = r, e.bg = t;
  }
  e.settings[0] && e.settings[0].settings && !e.settings[0].scope || e.settings.unshift({
    settings: {
      foreground: e.fg,
      background: e.bg
    }
  });
  let s = 0;
  const o = /* @__PURE__ */ new Map();
  function i(d) {
    var g;
    if (o.has(d))
      return o.get(d);
    s += 1;
    const p = `#${s.toString(16).padStart(8, "0").toLowerCase()}`;
    return (g = e.colorReplacements) != null && g[`#${p}`] ? i(d) : (o.set(d, p), p);
  }
  e.settings = e.settings.map((d) => {
    var S, _;
    const p = ((S = d.settings) == null ? void 0 : S.foreground) && !d.settings.foreground.startsWith("#"), g = ((_ = d.settings) == null ? void 0 : _.background) && !d.settings.background.startsWith("#");
    if (!p && !g)
      return d;
    const C = {
      ...d,
      settings: {
        ...d.settings
      }
    };
    if (p) {
      const y = i(d.settings.foreground);
      e.colorReplacements[y] = d.settings.foreground, C.settings.foreground = y;
    }
    if (g) {
      const y = i(d.settings.background);
      e.colorReplacements[y] = d.settings.background, C.settings.background = y;
    }
    return C;
  });
  for (const d of Object.keys(e.colors || {}))
    if ((d === "editor.foreground" || d === "editor.background" || d.startsWith("terminal.ansi")) && !((h = e.colors[d]) != null && h.startsWith("#"))) {
      const p = i(e.colors[d]);
      e.colorReplacements[p] = e.colors[d], e.colors[d] = p;
    }
  return Object.defineProperty(e, Pt, {
    enumerable: !1,
    writable: !1,
    value: !0
  }), e;
}
async function mn(n) {
  return Array.from(new Set((await Promise.all(
    n.filter((e) => !Fs(e)).map(async (e) => await hn(e).then((t) => Array.isArray(t) ? t : [t]))
  )).flat()));
}
async function yn(n) {
  return (await Promise.all(
    n.map(
      async (t) => Ws(t) ? null : ot(await hn(t))
    )
  )).filter((t) => !!t);
}
let Co = 3;
function vo(n, e = 3) {
  e > Co || console.trace(`[SHIKI DEPRECATE]: ${n}`);
}
class q extends Error {
  constructor(e) {
    super(e), this.name = "ShikiError";
  }
}
class wo extends wr {
  constructor(t, r, s, o = {}) {
    super(t);
    f(this, "_resolvedThemes", /* @__PURE__ */ new Map());
    f(this, "_resolvedGrammars", /* @__PURE__ */ new Map());
    f(this, "_langMap", /* @__PURE__ */ new Map());
    f(this, "_langGraph", /* @__PURE__ */ new Map());
    f(this, "_textmateThemeCache", /* @__PURE__ */ new WeakMap());
    f(this, "_loadedThemesCache", null);
    f(this, "_loadedLanguagesCache", null);
    this._resolver = t, this._themes = r, this._langs = s, this._alias = o, this._themes.map((i) => this.loadTheme(i)), this.loadLanguages(this._langs);
  }
  getTheme(t) {
    return typeof t == "string" ? this._resolvedThemes.get(t) : this.loadTheme(t);
  }
  loadTheme(t) {
    const r = ot(t);
    return r.name && (this._resolvedThemes.set(r.name, r), this._loadedThemesCache = null), r;
  }
  getLoadedThemes() {
    return this._loadedThemesCache || (this._loadedThemesCache = [...this._resolvedThemes.keys()]), this._loadedThemesCache;
  }
  // Override and re-implement this method to cache the textmate themes as `TextMateTheme.createFromRawTheme`
  // is expensive. Themes can switch often especially for dual-theme support.
  //
  // The parent class also accepts `colorMap` as the second parameter, but since we don't use that,
  // we omit here so it's easier to cache the themes.
  setTheme(t) {
    let r = this._textmateThemeCache.get(t);
    r || (r = ge.createFromRawTheme(t), this._textmateThemeCache.set(t, r)), this._syncRegistry.setTheme(r);
  }
  getGrammar(t) {
    if (this._alias[t]) {
      const r = /* @__PURE__ */ new Set([t]);
      for (; this._alias[t]; ) {
        if (t = this._alias[t], r.has(t))
          throw new q(`Circular alias \`${Array.from(r).join(" -> ")} -> ${t}\``);
        r.add(t);
      }
    }
    return this._resolvedGrammars.get(t);
  }
  loadLanguage(t) {
    var i, a, l, c;
    if (this.getGrammar(t.name))
      return;
    const r = new Set(
      [...this._langMap.values()].filter((u) => {
        var h;
        return (h = u.embeddedLangsLazy) == null ? void 0 : h.includes(t.name);
      })
    );
    this._resolver.addLanguage(t);
    const s = {
      balancedBracketSelectors: t.balancedBracketSelectors || ["*"],
      unbalancedBracketSelectors: t.unbalancedBracketSelectors || []
    };
    this._syncRegistry._rawGrammars.set(t.scopeName, t);
    const o = this.loadGrammarWithConfiguration(t.scopeName, 1, s);
    if (o.name = t.name, this._resolvedGrammars.set(t.name, o), t.aliases && t.aliases.forEach((u) => {
      this._alias[u] = t.name;
    }), this._loadedLanguagesCache = null, r.size)
      for (const u of r)
        this._resolvedGrammars.delete(u.name), this._loadedLanguagesCache = null, (a = (i = this._syncRegistry) == null ? void 0 : i._injectionGrammars) == null || a.delete(u.scopeName), (c = (l = this._syncRegistry) == null ? void 0 : l._grammars) == null || c.delete(u.scopeName), this.loadLanguage(this._langMap.get(u.name));
  }
  dispose() {
    super.dispose(), this._resolvedThemes.clear(), this._resolvedGrammars.clear(), this._langMap.clear(), this._langGraph.clear(), this._loadedThemesCache = null;
  }
  loadLanguages(t) {
    for (const o of t)
      this.resolveEmbeddedLanguages(o);
    const r = Array.from(this._langGraph.entries()), s = r.filter(([o, i]) => !i);
    if (s.length) {
      const o = r.filter(([i, a]) => {
        var l;
        return a && ((l = a.embeddedLangs) == null ? void 0 : l.some((c) => s.map(([u]) => u).includes(c)));
      }).filter((i) => !s.includes(i));
      throw new q(`Missing languages ${s.map(([i]) => `\`${i}\``).join(", ")}, required by ${o.map(([i]) => `\`${i}\``).join(", ")}`);
    }
    for (const [o, i] of r)
      this._resolver.addLanguage(i);
    for (const [o, i] of r)
      this.loadLanguage(i);
  }
  getLoadedLanguages() {
    return this._loadedLanguagesCache || (this._loadedLanguagesCache = [
      .../* @__PURE__ */ new Set([...this._resolvedGrammars.keys(), ...Object.keys(this._alias)])
    ]), this._loadedLanguagesCache;
  }
  resolveEmbeddedLanguages(t) {
    if (this._langMap.set(t.name, t), this._langGraph.set(t.name, t), t.embeddedLangs)
      for (const r of t.embeddedLangs)
        this._langGraph.set(r, this._langMap.get(r));
  }
}
class ko {
  constructor(e, t) {
    f(this, "_langs", /* @__PURE__ */ new Map());
    f(this, "_scopeToLang", /* @__PURE__ */ new Map());
    f(this, "_injections", /* @__PURE__ */ new Map());
    f(this, "_onigLib");
    this._onigLib = {
      createOnigScanner: (r) => e.createScanner(r),
      createOnigString: (r) => e.createString(r)
    }, t.forEach((r) => this.addLanguage(r));
  }
  get onigLib() {
    return this._onigLib;
  }
  getLangRegistration(e) {
    return this._langs.get(e);
  }
  loadGrammar(e) {
    return this._scopeToLang.get(e);
  }
  addLanguage(e) {
    this._langs.set(e.name, e), e.aliases && e.aliases.forEach((t) => {
      this._langs.set(t, e);
    }), this._scopeToLang.set(e.scopeName, e), e.injectTo && e.injectTo.forEach((t) => {
      this._injections.get(t) || this._injections.set(t, []), this._injections.get(t).push(e.scopeName);
    });
  }
  getInjections(e) {
    const t = e.split(".");
    let r = [];
    for (let s = 1; s <= t.length; s++) {
      const o = t.slice(0, s).join(".");
      r = [...r, ...this._injections.get(o) || []];
    }
    return r;
  }
}
let ee = 0;
function Ro(n) {
  ee += 1, n.warnings !== !1 && ee >= 10 && ee % 10 === 0 && console.warn(`[Shiki] ${ee} instances have been created. Shiki is supposed to be used as a singleton, consider refactoring your code to cache your highlighter instance; Or call \`highlighter.dispose()\` to release unused instances.`);
  let e = !1;
  if (!n.engine)
    throw new q("`engine` option is required for synchronous mode");
  const t = (n.langs || []).flat(1), r = (n.themes || []).flat(1).map(ot), s = new ko(n.engine, t), o = new wo(s, r, t, n.langAlias);
  let i;
  function a(y) {
    S();
    const b = o.getGrammar(typeof y == "string" ? y : y.name);
    if (!b)
      throw new q(`Language \`${y}\` not found, you may need to load it first`);
    return b;
  }
  function l(y) {
    if (y === "none")
      return { bg: "", fg: "", name: "none", settings: [], type: "dark" };
    S();
    const b = o.getTheme(y);
    if (!b)
      throw new q(`Theme \`${y}\` not found, you may need to load it first`);
    return b;
  }
  function c(y) {
    S();
    const b = l(y);
    i !== y && (o.setTheme(b), i = y);
    const w = o.getColorMap();
    return {
      theme: b,
      colorMap: w
    };
  }
  function u() {
    return S(), o.getLoadedThemes();
  }
  function h() {
    return S(), o.getLoadedLanguages();
  }
  function d(...y) {
    S(), o.loadLanguages(y.flat(1));
  }
  async function p(...y) {
    return d(await mn(y));
  }
  function g(...y) {
    S();
    for (const b of y.flat(1))
      o.loadTheme(b);
  }
  async function C(...y) {
    return S(), g(await yn(y));
  }
  function S() {
    if (e)
      throw new q("Shiki instance has been disposed");
  }
  function _() {
    e || (e = !0, o.dispose(), ee -= 1);
  }
  return {
    setTheme: c,
    getTheme: l,
    getLanguage: a,
    getLoadedThemes: u,
    getLoadedLanguages: h,
    loadLanguage: p,
    loadLanguageSync: d,
    loadTheme: C,
    loadThemeSync: g,
    dispose: _,
    [Symbol.dispose]: _
  };
}
async function xo(n) {
  n.engine || vo("`engine` option is required. Use `createOnigurumaEngine` or `createJavaScriptRegexEngine` to create an engine.");
  const [
    e,
    t,
    r
  ] = await Promise.all([
    yn(n.themes || []),
    mn(n.langs || []),
    n.engine
  ]);
  return Ro({
    ...n,
    themes: e,
    langs: t,
    engine: r
  });
}
async function Ao(n) {
  const e = await xo(n);
  return {
    getLastGrammarState: (...t) => lo(e, ...t),
    codeToTokensBase: (t, r) => st(e, t, r),
    codeToTokensWithThemes: (t, r) => gn(e, t, r),
    codeToTokens: (t, r) => ke(e, t, r),
    codeToHast: (t, r) => Re(e, t, r),
    codeToHtml: (t, r) => So(e, t, r),
    getBundledLanguages: () => ({}),
    getBundledThemes: () => ({}),
    ...e,
    getInternalContext: () => e
  };
}
async function No(n) {
  const {
    themes: e,
    themeModulePath: t = "@shiki/themes/",
    langModulePath: r = "@shiki/langs/"
  } = n, s = await Promise.all(
    e.map(
      (c) => import(
        /* @vite-ignore */
        `${t}${c}.mjs`
      )
    )
  ), o = Nn(), i = !o || o.mode === "zero" ? window.__shiki_engine_wasm__ : (await import("./shiki-engine.js")).getEngine(), a = await Ao({
    themes: s,
    engine: i
  });
  async function l(c, u) {
    const { lang: h } = u;
    return h && await a.loadLanguage(
      import(
        /* @vite-ignore */
        `${r}${h}.mjs`
      )
    ), a.codeToHtml(c, u);
  }
  return {
    codeToHtml: l
  };
}
const Go = No({
  themes: ["vitesse-dark", "vitesse-light"]
});
function To() {
  let n = null;
  return async () => (n || (n = await import("@shiki/transformers")), n);
}
const Po = To();
async function Bo(n) {
  if (n.length === 0)
    return [];
  const e = await Po();
  return n.map((t) => {
    const r = `transformer${t.charAt(0).toUpperCase() + t.slice(1)}`;
    return e[r]();
  });
}
function Do(n) {
  const { copy: e, copied: t } = Bn({ source: n.code, legacy: !0 }), r = xe(() => An(["copy", { copied: t.value }]));
  function s(o) {
    e(n.code), It(
      t,
      (i) => {
        i || o.target.blur();
      },
      { once: !0 }
    );
  }
  return {
    copyButtonClick: s,
    btnClasses: r
  };
}
export {
  Bo as getTransformers,
  Po as getTransformersModule,
  Go as highlighterTask,
  Do as readyCopyButton
};
