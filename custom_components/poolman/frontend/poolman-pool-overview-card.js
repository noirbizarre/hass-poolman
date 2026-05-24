/**
 * @license
 * Copyright 2019 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const L = globalThis, G = L.ShadowRoot && (L.ShadyCSS === void 0 || L.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype, K = Symbol(), et = /* @__PURE__ */ new WeakMap();
let gt = class {
  constructor(t, e, s) {
    if (this._$cssResult$ = !0, s !== K) throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
    this.cssText = t, this.t = e;
  }
  get styleSheet() {
    let t = this.o;
    const e = this.t;
    if (G && t === void 0) {
      const s = e !== void 0 && e.length === 1;
      s && (t = et.get(e)), t === void 0 && ((this.o = t = new CSSStyleSheet()).replaceSync(this.cssText), s && et.set(e, t));
    }
    return t;
  }
  toString() {
    return this.cssText;
  }
};
const Ct = (r) => new gt(typeof r == "string" ? r : r + "", void 0, K), $t = (r, ...t) => {
  const e = r.length === 1 ? r[0] : t.reduce((s, i, n) => s + ((o) => {
    if (o._$cssResult$ === !0) return o.cssText;
    if (typeof o == "number") return o;
    throw Error("Value passed to 'css' function must be a 'css' function result: " + o + ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.");
  })(i) + r[n + 1], r[0]);
  return new gt(e, r, K);
}, Pt = (r, t) => {
  if (G) r.adoptedStyleSheets = t.map((e) => e instanceof CSSStyleSheet ? e : e.styleSheet);
  else for (const e of t) {
    const s = document.createElement("style"), i = L.litNonce;
    i !== void 0 && s.setAttribute("nonce", i), s.textContent = e.cssText, r.appendChild(s);
  }
}, st = G ? (r) => r : (r) => r instanceof CSSStyleSheet ? ((t) => {
  let e = "";
  for (const s of t.cssRules) e += s.cssText;
  return Ct(e);
})(r) : r;
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const { is: Nt, defineProperty: kt, getOwnPropertyDescriptor: Ot, getOwnPropertyNames: Rt, getOwnPropertySymbols: Tt, getPrototypeOf: Mt } = Object, _ = globalThis, it = _.trustedTypes, Ut = it ? it.emptyScript : "", Dt = _.reactiveElementPolyfillSupport, P = (r, t) => r, j = { toAttribute(r, t) {
  switch (t) {
    case Boolean:
      r = r ? Ut : null;
      break;
    case Object:
    case Array:
      r = r == null ? r : JSON.stringify(r);
  }
  return r;
}, fromAttribute(r, t) {
  let e = r;
  switch (t) {
    case Boolean:
      e = r !== null;
      break;
    case Number:
      e = r === null ? null : Number(r);
      break;
    case Object:
    case Array:
      try {
        e = JSON.parse(r);
      } catch {
        e = null;
      }
  }
  return e;
} }, Y = (r, t) => !Nt(r, t), rt = { attribute: !0, type: String, converter: j, reflect: !1, useDefault: !1, hasChanged: Y };
Symbol.metadata ?? (Symbol.metadata = Symbol("metadata")), _.litPropertyMetadata ?? (_.litPropertyMetadata = /* @__PURE__ */ new WeakMap());
let w = class extends HTMLElement {
  static addInitializer(t) {
    this._$Ei(), (this.l ?? (this.l = [])).push(t);
  }
  static get observedAttributes() {
    return this.finalize(), this._$Eh && [...this._$Eh.keys()];
  }
  static createProperty(t, e = rt) {
    if (e.state && (e.attribute = !1), this._$Ei(), this.prototype.hasOwnProperty(t) && ((e = Object.create(e)).wrapped = !0), this.elementProperties.set(t, e), !e.noAccessor) {
      const s = Symbol(), i = this.getPropertyDescriptor(t, s, e);
      i !== void 0 && kt(this.prototype, t, i);
    }
  }
  static getPropertyDescriptor(t, e, s) {
    const { get: i, set: n } = Ot(this.prototype, t) ?? { get() {
      return this[e];
    }, set(o) {
      this[e] = o;
    } };
    return { get: i, set(o) {
      const c = i?.call(this);
      n?.call(this, o), this.requestUpdate(t, c, s);
    }, configurable: !0, enumerable: !0 };
  }
  static getPropertyOptions(t) {
    return this.elementProperties.get(t) ?? rt;
  }
  static _$Ei() {
    if (this.hasOwnProperty(P("elementProperties"))) return;
    const t = Mt(this);
    t.finalize(), t.l !== void 0 && (this.l = [...t.l]), this.elementProperties = new Map(t.elementProperties);
  }
  static finalize() {
    if (this.hasOwnProperty(P("finalized"))) return;
    if (this.finalized = !0, this._$Ei(), this.hasOwnProperty(P("properties"))) {
      const e = this.properties, s = [...Rt(e), ...Tt(e)];
      for (const i of s) this.createProperty(i, e[i]);
    }
    const t = this[Symbol.metadata];
    if (t !== null) {
      const e = litPropertyMetadata.get(t);
      if (e !== void 0) for (const [s, i] of e) this.elementProperties.set(s, i);
    }
    this._$Eh = /* @__PURE__ */ new Map();
    for (const [e, s] of this.elementProperties) {
      const i = this._$Eu(e, s);
      i !== void 0 && this._$Eh.set(i, e);
    }
    this.elementStyles = this.finalizeStyles(this.styles);
  }
  static finalizeStyles(t) {
    const e = [];
    if (Array.isArray(t)) {
      const s = new Set(t.flat(1 / 0).reverse());
      for (const i of s) e.unshift(st(i));
    } else t !== void 0 && e.push(st(t));
    return e;
  }
  static _$Eu(t, e) {
    const s = e.attribute;
    return s === !1 ? void 0 : typeof s == "string" ? s : typeof t == "string" ? t.toLowerCase() : void 0;
  }
  constructor() {
    super(), this._$Ep = void 0, this.isUpdatePending = !1, this.hasUpdated = !1, this._$Em = null, this._$Ev();
  }
  _$Ev() {
    this._$ES = new Promise((t) => this.enableUpdating = t), this._$AL = /* @__PURE__ */ new Map(), this._$E_(), this.requestUpdate(), this.constructor.l?.forEach((t) => t(this));
  }
  addController(t) {
    (this._$EO ?? (this._$EO = /* @__PURE__ */ new Set())).add(t), this.renderRoot !== void 0 && this.isConnected && t.hostConnected?.();
  }
  removeController(t) {
    this._$EO?.delete(t);
  }
  _$E_() {
    const t = /* @__PURE__ */ new Map(), e = this.constructor.elementProperties;
    for (const s of e.keys()) this.hasOwnProperty(s) && (t.set(s, this[s]), delete this[s]);
    t.size > 0 && (this._$Ep = t);
  }
  createRenderRoot() {
    const t = this.shadowRoot ?? this.attachShadow(this.constructor.shadowRootOptions);
    return Pt(t, this.constructor.elementStyles), t;
  }
  connectedCallback() {
    this.renderRoot ?? (this.renderRoot = this.createRenderRoot()), this.enableUpdating(!0), this._$EO?.forEach((t) => t.hostConnected?.());
  }
  enableUpdating(t) {
  }
  disconnectedCallback() {
    this._$EO?.forEach((t) => t.hostDisconnected?.());
  }
  attributeChangedCallback(t, e, s) {
    this._$AK(t, s);
  }
  _$ET(t, e) {
    const s = this.constructor.elementProperties.get(t), i = this.constructor._$Eu(t, s);
    if (i !== void 0 && s.reflect === !0) {
      const n = (s.converter?.toAttribute !== void 0 ? s.converter : j).toAttribute(e, s.type);
      this._$Em = t, n == null ? this.removeAttribute(i) : this.setAttribute(i, n), this._$Em = null;
    }
  }
  _$AK(t, e) {
    const s = this.constructor, i = s._$Eh.get(t);
    if (i !== void 0 && this._$Em !== i) {
      const n = s.getPropertyOptions(i), o = typeof n.converter == "function" ? { fromAttribute: n.converter } : n.converter?.fromAttribute !== void 0 ? n.converter : j;
      this._$Em = i;
      const c = o.fromAttribute(e, n.type);
      this[i] = c ?? this._$Ej?.get(i) ?? c, this._$Em = null;
    }
  }
  requestUpdate(t, e, s, i = !1, n) {
    if (t !== void 0) {
      const o = this.constructor;
      if (i === !1 && (n = this[t]), s ?? (s = o.getPropertyOptions(t)), !((s.hasChanged ?? Y)(n, e) || s.useDefault && s.reflect && n === this._$Ej?.get(t) && !this.hasAttribute(o._$Eu(t, s)))) return;
      this.C(t, e, s);
    }
    this.isUpdatePending === !1 && (this._$ES = this._$EP());
  }
  C(t, e, { useDefault: s, reflect: i, wrapped: n }, o) {
    s && !(this._$Ej ?? (this._$Ej = /* @__PURE__ */ new Map())).has(t) && (this._$Ej.set(t, o ?? e ?? this[t]), n !== !0 || o !== void 0) || (this._$AL.has(t) || (this.hasUpdated || s || (e = void 0), this._$AL.set(t, e)), i === !0 && this._$Em !== t && (this._$Eq ?? (this._$Eq = /* @__PURE__ */ new Set())).add(t));
  }
  async _$EP() {
    this.isUpdatePending = !0;
    try {
      await this._$ES;
    } catch (e) {
      Promise.reject(e);
    }
    const t = this.scheduleUpdate();
    return t != null && await t, !this.isUpdatePending;
  }
  scheduleUpdate() {
    return this.performUpdate();
  }
  performUpdate() {
    if (!this.isUpdatePending) return;
    if (!this.hasUpdated) {
      if (this.renderRoot ?? (this.renderRoot = this.createRenderRoot()), this._$Ep) {
        for (const [i, n] of this._$Ep) this[i] = n;
        this._$Ep = void 0;
      }
      const s = this.constructor.elementProperties;
      if (s.size > 0) for (const [i, n] of s) {
        const { wrapped: o } = n, c = this[i];
        o !== !0 || this._$AL.has(i) || c === void 0 || this.C(i, void 0, n, c);
      }
    }
    let t = !1;
    const e = this._$AL;
    try {
      t = this.shouldUpdate(e), t ? (this.willUpdate(e), this._$EO?.forEach((s) => s.hostUpdate?.()), this.update(e)) : this._$EM();
    } catch (s) {
      throw t = !1, this._$EM(), s;
    }
    t && this._$AE(e);
  }
  willUpdate(t) {
  }
  _$AE(t) {
    this._$EO?.forEach((e) => e.hostUpdated?.()), this.hasUpdated || (this.hasUpdated = !0, this.firstUpdated(t)), this.updated(t);
  }
  _$EM() {
    this._$AL = /* @__PURE__ */ new Map(), this.isUpdatePending = !1;
  }
  get updateComplete() {
    return this.getUpdateComplete();
  }
  getUpdateComplete() {
    return this._$ES;
  }
  shouldUpdate(t) {
    return !0;
  }
  update(t) {
    this._$Eq && (this._$Eq = this._$Eq.forEach((e) => this._$ET(e, this[e]))), this._$EM();
  }
  updated(t) {
  }
  firstUpdated(t) {
  }
};
w.elementStyles = [], w.shadowRootOptions = { mode: "open" }, w[P("elementProperties")] = /* @__PURE__ */ new Map(), w[P("finalized")] = /* @__PURE__ */ new Map(), Dt?.({ ReactiveElement: w }), (_.reactiveElementVersions ?? (_.reactiveElementVersions = [])).push("2.1.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const N = globalThis, nt = (r) => r, F = N.trustedTypes, ot = F ? F.createPolicy("lit-html", { createHTML: (r) => r }) : void 0, _t = "$lit$", g = `lit$${Math.random().toFixed(9).slice(2)}$`, vt = "?" + g, Ht = `<${vt}>`, y = document, O = () => y.createComment(""), R = (r) => r === null || typeof r != "object" && typeof r != "function", Z = Array.isArray, zt = (r) => Z(r) || typeof r?.[Symbol.iterator] == "function", V = `[ 	
\f\r]`, C = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, at = /-->/g, ct = />/g, v = RegExp(`>|${V}(?:([^\\s"'>=/]+)(${V}*=${V}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`, "g"), lt = /'/g, dt = /"/g, bt = /^(?:script|style|textarea|title)$/i, Lt = (r) => (t, ...e) => ({ _$litType$: r, strings: t, values: e }), u = Lt(1), E = Symbol.for("lit-noChange"), l = Symbol.for("lit-nothing"), ht = /* @__PURE__ */ new WeakMap(), b = y.createTreeWalker(y, 129);
function yt(r, t) {
  if (!Z(r) || !r.hasOwnProperty("raw")) throw Error("invalid template strings array");
  return ot !== void 0 ? ot.createHTML(t) : t;
}
const It = (r, t) => {
  const e = r.length - 1, s = [];
  let i, n = t === 2 ? "<svg>" : t === 3 ? "<math>" : "", o = C;
  for (let c = 0; c < e; c++) {
    const a = r[c];
    let h, p, d = -1, f = 0;
    for (; f < a.length && (o.lastIndex = f, p = o.exec(a), p !== null); ) f = o.lastIndex, o === C ? p[1] === "!--" ? o = at : p[1] !== void 0 ? o = ct : p[2] !== void 0 ? (bt.test(p[2]) && (i = RegExp("</" + p[2], "g")), o = v) : p[3] !== void 0 && (o = v) : o === v ? p[0] === ">" ? (o = i ?? C, d = -1) : p[1] === void 0 ? d = -2 : (d = o.lastIndex - p[2].length, h = p[1], o = p[3] === void 0 ? v : p[3] === '"' ? dt : lt) : o === dt || o === lt ? o = v : o === at || o === ct ? o = C : (o = v, i = void 0);
    const m = o === v && r[c + 1].startsWith("/>") ? " " : "";
    n += o === C ? a + Ht : d >= 0 ? (s.push(h), a.slice(0, d) + _t + a.slice(d) + g + m) : a + g + (d === -2 ? c : m);
  }
  return [yt(r, n + (r[e] || "<?>") + (t === 2 ? "</svg>" : t === 3 ? "</math>" : "")), s];
};
class T {
  constructor({ strings: t, _$litType$: e }, s) {
    let i;
    this.parts = [];
    let n = 0, o = 0;
    const c = t.length - 1, a = this.parts, [h, p] = It(t, e);
    if (this.el = T.createElement(h, s), b.currentNode = this.el.content, e === 2 || e === 3) {
      const d = this.el.content.firstChild;
      d.replaceWith(...d.childNodes);
    }
    for (; (i = b.nextNode()) !== null && a.length < c; ) {
      if (i.nodeType === 1) {
        if (i.hasAttributes()) for (const d of i.getAttributeNames()) if (d.endsWith(_t)) {
          const f = p[o++], m = i.getAttribute(d).split(g), z = /([.?@])?(.*)/.exec(f);
          a.push({ type: 1, index: n, name: z[2], strings: m, ctor: z[1] === "." ? Ft : z[1] === "?" ? Bt : z[1] === "@" ? Vt : B }), i.removeAttribute(d);
        } else d.startsWith(g) && (a.push({ type: 6, index: n }), i.removeAttribute(d));
        if (bt.test(i.tagName)) {
          const d = i.textContent.split(g), f = d.length - 1;
          if (f > 0) {
            i.textContent = F ? F.emptyScript : "";
            for (let m = 0; m < f; m++) i.append(d[m], O()), b.nextNode(), a.push({ type: 2, index: ++n });
            i.append(d[f], O());
          }
        }
      } else if (i.nodeType === 8) if (i.data === vt) a.push({ type: 2, index: n });
      else {
        let d = -1;
        for (; (d = i.data.indexOf(g, d + 1)) !== -1; ) a.push({ type: 7, index: n }), d += g.length - 1;
      }
      n++;
    }
  }
  static createElement(t, e) {
    const s = y.createElement("template");
    return s.innerHTML = t, s;
  }
}
function S(r, t, e = r, s) {
  if (t === E) return t;
  let i = s !== void 0 ? e._$Co?.[s] : e._$Cl;
  const n = R(t) ? void 0 : t._$litDirective$;
  return i?.constructor !== n && (i?._$AO?.(!1), n === void 0 ? i = void 0 : (i = new n(r), i._$AT(r, e, s)), s !== void 0 ? (e._$Co ?? (e._$Co = []))[s] = i : e._$Cl = i), i !== void 0 && (t = S(r, i._$AS(r, t.values), i, s)), t;
}
class jt {
  constructor(t, e) {
    this._$AV = [], this._$AN = void 0, this._$AD = t, this._$AM = e;
  }
  get parentNode() {
    return this._$AM.parentNode;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  u(t) {
    const { el: { content: e }, parts: s } = this._$AD, i = (t?.creationScope ?? y).importNode(e, !0);
    b.currentNode = i;
    let n = b.nextNode(), o = 0, c = 0, a = s[0];
    for (; a !== void 0; ) {
      if (o === a.index) {
        let h;
        a.type === 2 ? h = new H(n, n.nextSibling, this, t) : a.type === 1 ? h = new a.ctor(n, a.name, a.strings, this, t) : a.type === 6 && (h = new Wt(n, this, t)), this._$AV.push(h), a = s[++c];
      }
      o !== a?.index && (n = b.nextNode(), o++);
    }
    return b.currentNode = y, i;
  }
  p(t) {
    let e = 0;
    for (const s of this._$AV) s !== void 0 && (s.strings !== void 0 ? (s._$AI(t, s, e), e += s.strings.length - 2) : s._$AI(t[e])), e++;
  }
}
class H {
  get _$AU() {
    return this._$AM?._$AU ?? this._$Cv;
  }
  constructor(t, e, s, i) {
    this.type = 2, this._$AH = l, this._$AN = void 0, this._$AA = t, this._$AB = e, this._$AM = s, this.options = i, this._$Cv = i?.isConnected ?? !0;
  }
  get parentNode() {
    let t = this._$AA.parentNode;
    const e = this._$AM;
    return e !== void 0 && t?.nodeType === 11 && (t = e.parentNode), t;
  }
  get startNode() {
    return this._$AA;
  }
  get endNode() {
    return this._$AB;
  }
  _$AI(t, e = this) {
    t = S(this, t, e), R(t) ? t === l || t == null || t === "" ? (this._$AH !== l && this._$AR(), this._$AH = l) : t !== this._$AH && t !== E && this._(t) : t._$litType$ !== void 0 ? this.$(t) : t.nodeType !== void 0 ? this.T(t) : zt(t) ? this.k(t) : this._(t);
  }
  O(t) {
    return this._$AA.parentNode.insertBefore(t, this._$AB);
  }
  T(t) {
    this._$AH !== t && (this._$AR(), this._$AH = this.O(t));
  }
  _(t) {
    this._$AH !== l && R(this._$AH) ? this._$AA.nextSibling.data = t : this.T(y.createTextNode(t)), this._$AH = t;
  }
  $(t) {
    const { values: e, _$litType$: s } = t, i = typeof s == "number" ? this._$AC(t) : (s.el === void 0 && (s.el = T.createElement(yt(s.h, s.h[0]), this.options)), s);
    if (this._$AH?._$AD === i) this._$AH.p(e);
    else {
      const n = new jt(i, this), o = n.u(this.options);
      n.p(e), this.T(o), this._$AH = n;
    }
  }
  _$AC(t) {
    let e = ht.get(t.strings);
    return e === void 0 && ht.set(t.strings, e = new T(t)), e;
  }
  k(t) {
    Z(this._$AH) || (this._$AH = [], this._$AR());
    const e = this._$AH;
    let s, i = 0;
    for (const n of t) i === e.length ? e.push(s = new H(this.O(O()), this.O(O()), this, this.options)) : s = e[i], s._$AI(n), i++;
    i < e.length && (this._$AR(s && s._$AB.nextSibling, i), e.length = i);
  }
  _$AR(t = this._$AA.nextSibling, e) {
    for (this._$AP?.(!1, !0, e); t !== this._$AB; ) {
      const s = nt(t).nextSibling;
      nt(t).remove(), t = s;
    }
  }
  setConnected(t) {
    this._$AM === void 0 && (this._$Cv = t, this._$AP?.(t));
  }
}
class B {
  get tagName() {
    return this.element.tagName;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  constructor(t, e, s, i, n) {
    this.type = 1, this._$AH = l, this._$AN = void 0, this.element = t, this.name = e, this._$AM = i, this.options = n, s.length > 2 || s[0] !== "" || s[1] !== "" ? (this._$AH = Array(s.length - 1).fill(new String()), this.strings = s) : this._$AH = l;
  }
  _$AI(t, e = this, s, i) {
    const n = this.strings;
    let o = !1;
    if (n === void 0) t = S(this, t, e, 0), o = !R(t) || t !== this._$AH && t !== E, o && (this._$AH = t);
    else {
      const c = t;
      let a, h;
      for (t = n[0], a = 0; a < n.length - 1; a++) h = S(this, c[s + a], e, a), h === E && (h = this._$AH[a]), o || (o = !R(h) || h !== this._$AH[a]), h === l ? t = l : t !== l && (t += (h ?? "") + n[a + 1]), this._$AH[a] = h;
    }
    o && !i && this.j(t);
  }
  j(t) {
    t === l ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, t ?? "");
  }
}
class Ft extends B {
  constructor() {
    super(...arguments), this.type = 3;
  }
  j(t) {
    this.element[this.name] = t === l ? void 0 : t;
  }
}
class Bt extends B {
  constructor() {
    super(...arguments), this.type = 4;
  }
  j(t) {
    this.element.toggleAttribute(this.name, !!t && t !== l);
  }
}
class Vt extends B {
  constructor(t, e, s, i, n) {
    super(t, e, s, i, n), this.type = 5;
  }
  _$AI(t, e = this) {
    if ((t = S(this, t, e, 0) ?? l) === E) return;
    const s = this._$AH, i = t === l && s !== l || t.capture !== s.capture || t.once !== s.once || t.passive !== s.passive, n = t !== l && (s === l || i);
    i && this.element.removeEventListener(this.name, this, s), n && this.element.addEventListener(this.name, this, t), this._$AH = t;
  }
  handleEvent(t) {
    typeof this._$AH == "function" ? this._$AH.call(this.options?.host ?? this.element, t) : this._$AH.handleEvent(t);
  }
}
class Wt {
  constructor(t, e, s) {
    this.element = t, this.type = 6, this._$AN = void 0, this._$AM = e, this.options = s;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AI(t) {
    S(this, t);
  }
}
const qt = N.litHtmlPolyfillSupport;
qt?.(T, H), (N.litHtmlVersions ?? (N.litHtmlVersions = [])).push("3.3.3");
const Gt = (r, t, e) => {
  const s = e?.renderBefore ?? t;
  let i = s._$litPart$;
  if (i === void 0) {
    const n = e?.renderBefore ?? null;
    s._$litPart$ = i = new H(t.insertBefore(O(), n), n, void 0, e ?? {});
  }
  return i._$AI(r), i;
};
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const k = globalThis;
class A extends w {
  constructor() {
    super(...arguments), this.renderOptions = { host: this }, this._$Do = void 0;
  }
  createRenderRoot() {
    var e;
    const t = super.createRenderRoot();
    return (e = this.renderOptions).renderBefore ?? (e.renderBefore = t.firstChild), t;
  }
  update(t) {
    const e = this.render();
    this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(t), this._$Do = Gt(e, this.renderRoot, this.renderOptions);
  }
  connectedCallback() {
    super.connectedCallback(), this._$Do?.setConnected(!0);
  }
  disconnectedCallback() {
    super.disconnectedCallback(), this._$Do?.setConnected(!1);
  }
  render() {
    return E;
  }
}
A._$litElement$ = !0, A.finalized = !0, k.litElementHydrateSupport?.({ LitElement: A });
const Kt = k.litElementPolyfillSupport;
Kt?.({ LitElement: A });
(k.litElementVersions ?? (k.litElementVersions = [])).push("4.2.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const Yt = { attribute: !0, type: String, converter: j, reflect: !1, hasChanged: Y }, Zt = (r = Yt, t, e) => {
  const { kind: s, metadata: i } = e;
  let n = globalThis.litPropertyMetadata.get(i);
  if (n === void 0 && globalThis.litPropertyMetadata.set(i, n = /* @__PURE__ */ new Map()), s === "setter" && ((r = Object.create(r)).wrapped = !0), n.set(e.name, r), s === "accessor") {
    const { name: o } = e;
    return { set(c) {
      const a = t.get.call(this);
      t.set.call(this, c), this.requestUpdate(o, a, r, !0, c);
    }, init(c) {
      return c !== void 0 && this.C(o, void 0, r, c), c;
    } };
  }
  if (s === "setter") {
    const { name: o } = e;
    return function(c) {
      const a = this[o];
      t.call(this, c), this.requestUpdate(o, a, r, !0, c);
    };
  }
  throw Error("Unsupported decorator location: " + s);
};
function J(r) {
  return (t, e) => typeof e == "object" ? Zt(r, t, e) : ((s, i, n) => {
    const o = i.hasOwnProperty(n);
    return i.constructor.createProperty(n, s), o ? Object.getOwnPropertyDescriptor(i, n) : void 0;
  })(r, t, e);
}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
function xt(r) {
  return J({ ...r, state: !0, attribute: !1 });
}
const Jt = $t`
  :host {
    display: block;
  }

  ha-card {
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 12px;
    font-family: var(--primary-font-family, sans-serif);
    color: var(--primary-text-color, #212121);
  }

  .header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
  }

  .title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 1.1rem;
    font-weight: 600;
  }

  .title .pool-icon {
    font-size: 1.3rem;
    line-height: 1;
  }

  .badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    border-radius: 999px;
    color: white;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    background: var(--badge-color, #9e9e9e);
  }

  .badge .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.85);
  }

  .metrics {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
    gap: 8px;
  }

  .metric {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 2px;
    padding: 8px 10px;
    border-radius: 10px;
    background: var(--card-background-color, rgba(0, 0, 0, 0.04));
    box-shadow: inset 0 0 0 1px var(--divider-color, rgba(0, 0, 0, 0.08));
  }

  .metric-label {
    font-size: 0.75rem;
    color: var(--secondary-text-color, #757575);
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .metric-value {
    font-size: 1.05rem;
    font-weight: 600;
  }

  .score {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .score-row {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    font-size: 0.85rem;
    color: var(--secondary-text-color, #757575);
  }

  .score-row strong {
    color: var(--primary-text-color, #212121);
    font-size: 1rem;
  }

  .score-bar {
    height: 6px;
    border-radius: 999px;
    background: var(--divider-color, rgba(0, 0, 0, 0.08));
    overflow: hidden;
  }

  .score-bar-fill {
    height: 100%;
    background: var(--success-color, #43a047);
    transition: width 0.3s ease;
  }

  .score-bar-fill.warn {
    background: var(--warning-color, #ff9800);
  }

  .score-bar-fill.bad {
    background: var(--error-color, #e53935);
  }

  .recommendations {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    padding: 8px 12px;
    border-radius: 10px;
    background: var(--secondary-background-color, rgba(0, 0, 0, 0.03));
    cursor: pointer;
    user-select: none;
  }

  .recommendations[disabled] {
    cursor: default;
    opacity: 0.7;
  }

  .recommendations:focus-visible {
    outline: 2px solid var(--primary-color, #03a9f4);
    outline-offset: 2px;
  }

  .recommendations .label {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.9rem;
  }

  .recommendations .chevron {
    font-size: 1.1rem;
    color: var(--secondary-text-color, #757575);
  }

  @media (max-width: 360px) {
    ha-card {
      padding: 12px;
    }

    .title {
      font-size: 1rem;
    }
  }
`, M = "—", Qt = /* @__PURE__ */ new Set(["unavailable", "unknown", "none", ""]);
function x(r) {
  return r ? Qt.has(r.state) : !0;
}
function wt(r, t) {
  const e = { ...t.entities ?? {} }, s = {
    status: "_status",
    water_quality_score: "_water_quality_score",
    recommendations: "_recommendations",
    problems: "_problems",
    temperature: "_temperature",
    ph: "_ph",
    free_chlorine: "_free_chlorine",
    orp: "_orp"
  }, i = (n) => n.endsWith("_status") && !/_(ph|orp|free_chlorine|tac|cya|hardness|salt|tds)_status$/.test(n);
  if (t.device_id && r.entities) {
    for (const n of Object.values(r.entities))
      if (n.device_id === t.device_id)
        for (const [o, c] of Object.entries(s))
          e[o] || (o === "status" ? i(n.entity_id) && (e[o] = n.entity_id) : n.entity_id.endsWith(c) && (e[o] = n.entity_id));
  }
  return e;
}
function $(r, t) {
  if (t)
    return r.states[t];
}
function Xt(r) {
  if (!r || x(r)) return "unknown";
  const t = r.state.toLowerCase();
  return t === "ok" || t === "warning" || t === "critical" ? t : "unknown";
}
const te = {
  ok: { label: "OK", color: "var(--success-color, #43a047)", icon: "✅" },
  warning: {
    label: "WARNING",
    color: "var(--warning-color, #ff9800)",
    icon: "⚠️"
  },
  critical: {
    label: "CRITICAL",
    color: "var(--error-color, #e53935)",
    icon: "🚨"
  },
  unknown: {
    label: "UNKNOWN",
    color: "var(--disabled-text-color, #9e9e9e)",
    icon: "❔"
  }
};
function ee(r) {
  return te[r];
}
const se = {
  temperature: { icon: "🌡️", label: "Temp", fractionDigits: 1, unitFallback: "°C" },
  ph: { icon: "⚗️", label: "pH", fractionDigits: 1, unitFallback: "" },
  free_chlorine: { icon: "🧪", label: "Cl", fractionDigits: 1, unitFallback: "mg/L" },
  orp: { icon: "⚡", label: "ORP", fractionDigits: 0, unitFallback: "mV" }
};
function ie(r) {
  return se[r];
}
function re(r, t, e) {
  if (x(r)) return M;
  const s = r.state, i = Number(s), n = r.attributes.unit_of_measurement ?? e;
  return Number.isFinite(i) ? `${i.toFixed(t)}${n ? ` ${n}` : ""}`.trim() : `${s}${n ? ` ${n}` : ""}`.trim();
}
function ne(r, t, e) {
  if (r.metrics?.length) return r.metrics;
  const s = ["temperature", "ph", "free_chlorine"], i = $(e, t.free_chlorine);
  return x(i) && t.orp && !x($(e, t.orp)) ? ["temperature", "ph", "orp"] : s;
}
function oe(r) {
  return r >= 80 ? "good" : r >= 50 ? "warn" : "bad";
}
function ae(r) {
  if (!r) return { count: 0, list: [] };
  const t = Number(r.state), e = r.attributes.recommendations ?? [];
  return { count: Number.isFinite(t) ? t : e.length, list: e };
}
const ce = {
  low: {
    label: "INFO",
    color: "var(--info-color, #2196f3)",
    icon: "ℹ️"
  },
  medium: {
    label: "WARNING",
    color: "var(--warning-color, #ff9800)",
    icon: "⚠️"
  },
  critical: {
    label: "CRITICAL",
    color: "var(--error-color, #e53935)",
    icon: "🚨"
  }
};
function I(r) {
  return ce[r];
}
const Q = {
  ph: { unit: "", fractionDigits: 2, label: "pH" },
  orp: { unit: "mV", fractionDigits: 0, label: "ORP" },
  chlorine: { unit: "mg/L", fractionDigits: 1, label: "Chlorine" },
  temperature: { unit: "°C", fractionDigits: 1, label: "Temperature" },
  cya: { unit: "mg/L", fractionDigits: 0, label: "CYA" },
  alkalinity: { unit: "mg/L", fractionDigits: 0, label: "Alkalinity" },
  hardness: { unit: "mg/L", fractionDigits: 0, label: "Hardness" },
  tds: { unit: "mg/L", fractionDigits: 0, label: "TDS" },
  salt: { unit: "g/L", fractionDigits: 2, label: "Salt" },
  ec: { unit: "µS/cm", fractionDigits: 0, label: "EC" }
};
function At(r, t) {
  return t ? `${r} ${t}` : r;
}
function le(r, t) {
  if (t === null || !Number.isFinite(t)) return M;
  if (r === null) return String(t);
  const e = Q[r];
  return e ? At(t.toFixed(e.fractionDigits), e.unit) : String(t);
}
function de(r, t) {
  if (!t || t.length !== 2) return M;
  const [e, s] = t;
  if (!Number.isFinite(e) || !Number.isFinite(s)) return M;
  if (r === null) return `${e}–${s}`;
  const i = Q[r];
  if (!i) return `${e}–${s}`;
  const n = e.toFixed(i.fractionDigits), o = s.toFixed(i.fractionDigits);
  return At(`${n}–${o}`, i.unit);
}
function he(r) {
  return r === null ? "" : Q[r]?.label ?? r;
}
function pt(r) {
  if (!r || x(r))
    return { count: 0, list: [], worst: "ok" };
  const t = r.attributes.problems ?? [], e = Number(r.state), s = Number.isFinite(e) ? e : t.length, n = r.attributes.worst_severity ?? t[0]?.severity ?? "ok";
  return { count: s, list: t, worst: n };
}
var pe = Object.defineProperty, Et = (r, t, e, s) => {
  for (var i = void 0, n = r.length - 1, o; n >= 0; n--)
    (o = r[n]) && (i = o(t, e, i) || i);
  return i && pe(t, e, i), i;
};
const W = "poolman-pool-overview-card", X = class X extends A {
  /** Lovelace card size hint (1 unit ≈ 50px). */
  getCardSize() {
    return 3;
  }
  static getStubConfig() {
    return { type: `custom:${W}` };
  }
  setConfig(t) {
    if (!t)
      throw new Error("Invalid configuration");
    if (!t.device_id && !t.entities)
      throw new Error(
        "poolman-pool-overview-card: either `device_id` or `entities` must be provided"
      );
    this._config = { show_score: !0, ...t };
  }
  render() {
    if (!this._config || !this.hass) return l;
    const t = wt(this.hass, this._config), e = $(this.hass, t.status), s = Xt(e), i = ee(s), n = this._config.name ?? this._deviceName(this._config.device_id) ?? "Pool", o = ne(this._config, t, this.hass);
    return u`
      <ha-card>
        <div class="header">
          <div class="title">
            <span class="pool-icon" aria-hidden="true">🏊</span>
            <span>${n}</span>
          </div>
          <span
            class="badge"
            style=${`background:${i.color}`}
            role="status"
            aria-label=${`Status: ${i.label}`}
          >
            <span class="dot" aria-hidden="true"></span>
            ${i.label}
          </span>
        </div>

        <div class="metrics">
          ${o.map((c) => this._renderMetric(c, t))}
        </div>

        ${this._config.show_score !== !1 ? this._renderScore(t.water_quality_score) : l}
        ${this._renderRecommendations(t.recommendations)}
      </ha-card>
    `;
  }
  _renderMetric(t, e) {
    const s = ie(t), i = $(this.hass, e[t]), n = re(i, s.fractionDigits, s.unitFallback);
    return u`
      <div class="metric" data-key=${t}>
        <span class="metric-label">
          <span aria-hidden="true">${s.icon}</span>
          ${s.label}
        </span>
        <span class="metric-value">${n}</span>
      </div>
    `;
  }
  _renderScore(t) {
    const e = $(this.hass, t);
    if (x(e))
      return u`
        <div class="score">
          <div class="score-row">
            <span>Quality score</span>
            <strong>${M}</strong>
          </div>
        </div>
      `;
    const s = Math.max(0, Math.min(100, Number(e.state) || 0)), i = oe(s);
    return u`
      <div class="score">
        <div class="score-row">
          <span>Quality score</span>
          <strong>${s} / 100</strong>
        </div>
        <div class="score-bar">
          <div
            class="score-bar-fill ${i === "good" ? "" : i}"
            style=${`width:${s}%`}
          ></div>
        </div>
      </div>
    `;
  }
  _renderRecommendations(t) {
    const e = $(this.hass, t);
    if (!e) return l;
    const { count: s } = ae(e), i = this._config?.recommendations_path, n = s > 0, o = s === 0 ? "Your pool is in good condition" : `${s} recommendation${s === 1 ? "" : "s"}`;
    return u`
      <div
        class="recommendations"
        role=${n ? "button" : "presentation"}
        tabindex=${n ? "0" : "-1"}
        ?disabled=${!n}
        @click=${() => n && this._openRecommendations(e.entity_id, i)}
        @keydown=${(a) => {
      n && (a.key === "Enter" || a.key === " ") && (a.preventDefault(), this._openRecommendations(e.entity_id, i));
    }}
      >
        <span class="label">
          <span aria-hidden="true">${s === 0 ? "✅" : "⚠️"}</span>
          ${o}
        </span>
        ${n ? u`<span class="chevron" aria-hidden="true">›</span>` : l}
      </div>
    `;
  }
  _openRecommendations(t, e) {
    if (e) {
      this.dispatchEvent(
        new CustomEvent("location-changed", {
          bubbles: !0,
          composed: !0,
          detail: { replace: !1 }
        })
      ), history.pushState(null, "", e);
      return;
    }
    this.dispatchEvent(
      new CustomEvent("hass-more-info", {
        bubbles: !0,
        composed: !0,
        detail: { entityId: t }
      })
    );
  }
  _deviceName(t) {
    if (!t || !this.hass?.devices) return;
    const e = this.hass.devices[t];
    if (e)
      return e.name_by_user ?? e.name ?? void 0;
  }
};
X.styles = Jt;
let U = X;
Et([
  J({ attribute: !1 })
], U.prototype, "hass");
Et([
  xt()
], U.prototype, "_config");
customElements.get(W) || customElements.define(W, U);
const ue = $t`
  :host {
    display: block;
  }

  ha-card {
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 12px;
    font-family: var(--primary-font-family, sans-serif);
    color: var(--primary-text-color, #212121);
  }

  .header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
  }

  .title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 1.1rem;
    font-weight: 600;
  }

  .title .icon {
    font-size: 1.3rem;
    line-height: 1;
  }

  .badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    border-radius: 999px;
    color: white;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    background: var(--badge-color, #9e9e9e);
  }

  .badge .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.85);
  }

  .problems {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .problem {
    display: grid;
    grid-template-columns: auto 1fr;
    column-gap: 12px;
    row-gap: 2px;
    align-items: start;
    padding: 10px 12px;
    border-radius: 10px;
    background: var(--card-background-color, rgba(0, 0, 0, 0.04));
    box-shadow: inset 0 0 0 1px var(--divider-color, rgba(0, 0, 0, 0.08));
    border-left: 4px solid var(--problem-color, #9e9e9e);
  }

  .severity {
    grid-row: 1;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 2px 8px;
    border-radius: 999px;
    color: white;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    background: var(--problem-color, #9e9e9e);
    white-space: nowrap;
  }

  .message {
    grid-row: 1;
    grid-column: 2;
    font-size: 0.95rem;
    font-weight: 600;
    line-height: 1.3;
  }

  .details {
    grid-row: 2;
    grid-column: 2;
    display: flex;
    flex-wrap: wrap;
    gap: 4px 12px;
    font-size: 0.8rem;
    color: var(--secondary-text-color, #757575);
  }

  .details .sep {
    opacity: 0.6;
  }

  .empty {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px;
    border-radius: 10px;
    background: var(--secondary-background-color, rgba(67, 160, 71, 0.08));
    color: var(--success-color, #43a047);
    font-weight: 500;
  }

  .unavailable {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px;
    border-radius: 10px;
    background: var(--secondary-background-color, rgba(0, 0, 0, 0.03));
    color: var(--secondary-text-color, #757575);
    font-style: italic;
  }

  .more {
    font-size: 0.8rem;
    color: var(--secondary-text-color, #757575);
    text-align: center;
    padding: 4px 0 0;
  }

  @media (max-width: 360px) {
    ha-card {
      padding: 12px;
    }

    .title {
      font-size: 1rem;
    }

    .problem {
      grid-template-columns: 1fr;
    }

    .message,
    .details {
      grid-column: 1;
    }
  }
`;
var fe = Object.defineProperty, St = (r, t, e, s) => {
  for (var i = void 0, n = r.length - 1, o; n >= 0; n--)
    (o = r[n]) && (i = o(t, e, i) || i);
  return i && fe(t, e, i), i;
};
const q = "poolman-problem-card", ut = {
  ok: {
    label: "OK",
    color: "var(--success-color, #43a047)",
    icon: "✅"
  },
  low: I("low"),
  medium: I("medium"),
  critical: I("critical")
}, tt = class tt extends A {
  /** Lovelace card size hint (1 unit ≈ 50px). */
  getCardSize() {
    const t = this._resolveEntity();
    if (!t) return 1;
    const { count: e } = pt(t);
    if (e === 0) return 1;
    const s = this._config?.max ?? e;
    return 1 + Math.min(e, s);
  }
  static getStubConfig() {
    return { type: `custom:${q}` };
  }
  setConfig(t) {
    if (!t)
      throw new Error("Invalid configuration");
    if (!t.device_id && !t.entity)
      throw new Error(
        "poolman-problem-card: either `device_id` or `entity` must be provided"
      );
    if (t.max !== void 0 && (!Number.isFinite(t.max) || t.max < 1))
      throw new Error("poolman-problem-card: `max` must be a positive integer");
    this._config = { ...t };
  }
  render() {
    if (!this._config || !this.hass) return l;
    const t = this._resolveEntity(), e = this._config.name ?? this._deviceName() ?? "Pool Problems";
    if (!t || x(t))
      return u`
        <ha-card>
          <div class="header">
            <div class="title">
              <span class="icon" aria-hidden="true">🩺</span>
              <span>${e}</span>
            </div>
          </div>
          <div class="unavailable" role="status">
            <span aria-hidden="true">❔</span>
            <span>Problems entity unavailable</span>
          </div>
        </ha-card>
      `;
    const { count: s, list: i, worst: n } = pt(t), o = ut[n] ?? ut.ok;
    return u`
      <ha-card>
        <div class="header">
          <div class="title">
            <span class="icon" aria-hidden="true">🩺</span>
            <span>${e}</span>
          </div>
          <span
            class="badge"
            style=${`background:${o.color}`}
            role="status"
            aria-label=${`Worst severity: ${o.label}`}
          >
            <span class="dot" aria-hidden="true"></span>
            ${o.label}
          </span>
        </div>

        ${s === 0 ? u`
              <div class="empty" role="status">
                <span aria-hidden="true">✅</span>
                <span>No problems detected — pool is healthy</span>
              </div>
            ` : this._renderProblems(i, s)}
      </ha-card>
    `;
  }
  _renderProblems(t, e) {
    const s = this._config?.max, i = s !== void 0 ? t.slice(0, s) : t, n = Math.max(0, e - i.length);
    return u`
      <div class="problems">
        ${i.map((o) => this._renderProblem(o))}
        ${n > 0 ? u`<div class="more">
              +${n} more problem${n === 1 ? "" : "s"}
            </div>` : l}
      </div>
    `;
  }
  _renderProblem(t) {
    const e = t.severity, s = I(e), i = he(t.metric), n = t.metric !== null && t.value !== null && t.expected_range !== null;
    return u`
      <div
        class="problem"
        data-code=${t.code}
        data-severity=${e}
        style=${`--problem-color:${s.color}`}
      >
        <span class="severity" aria-label=${`Severity: ${s.label}`}>
          <span aria-hidden="true">${s.icon}</span>
          ${s.label}
        </span>
        <span class="message">${t.message}</span>
        ${n ? u`
              <div class="details">
                ${i ? u`<span class="metric-label">${i}</span>
                      <span class="sep" aria-hidden="true">•</span>` : l}
                <span>
                  Current:
                  <strong>${le(t.metric, t.value)}</strong>
                </span>
                <span class="sep" aria-hidden="true">—</span>
                <span>
                  Expected:
                  <strong
                    >${de(t.metric, t.expected_range)}</strong
                  >
                </span>
              </div>
            ` : l}
      </div>
    `;
  }
  _resolveEntity() {
    if (!this.hass || !this._config) return;
    if (this._config.entity)
      return $(this.hass, this._config.entity);
    const t = wt(this.hass, {
      type: this._config.type,
      device_id: this._config.device_id
    });
    return $(this.hass, t.problems);
  }
  _deviceName() {
    const t = this._config?.device_id;
    if (!t || !this.hass?.devices) return;
    const e = this.hass.devices[t];
    if (e)
      return e.name_by_user ?? e.name ?? void 0;
  }
};
tt.styles = ue;
let D = tt;
St([
  J({ attribute: !1 })
], D.prototype, "hass");
St([
  xt()
], D.prototype, "_config");
customElements.get(q) || customElements.define(q, D);
const ft = "poolman-pool-overview-card", mt = "poolman-problem-card", me = "0.1.0";
window.customCards = window.customCards ?? [];
window.customCards.some((r) => r.type === ft) || window.customCards.push({
  type: ft,
  name: "Pool Overview",
  description: "Glanceable summary card for a Pool Manager pool: status badge, key chemistry metrics, water quality score and recommendation count.",
  preview: !0,
  documentationURL: "https://noirbizarre.github.io/hass-poolman/pool-overview-card/"
});
window.customCards.some((r) => r.type === mt) || window.customCards.push({
  type: mt,
  name: "Pool Problems",
  description: "Diagnostic card listing the current pool problems by severity, with measured value and expected range.",
  preview: !0,
  documentationURL: "https://noirbizarre.github.io/hass-poolman/problem-card/"
});
console.info(
  `%c POOLMAN-CARDS %c v${me} `,
  "color: white; background: #03a9f4; font-weight: 700;",
  "color: #03a9f4; background: transparent; font-weight: 700;"
);
//# sourceMappingURL=poolman-pool-overview-card.js.map
