/**
 * @license
 * Copyright 2019 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const q = globalThis, se = q.ShadowRoot && (q.ShadyCSS === void 0 || q.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype, ne = Symbol(), ue = /* @__PURE__ */ new WeakMap();
let Ne = class {
  constructor(e, t, i) {
    if (this._$cssResult$ = !0, i !== ne) throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
    this.cssText = e, this.t = t;
  }
  get styleSheet() {
    let e = this.o;
    const t = this.t;
    if (se && e === void 0) {
      const i = t !== void 0 && t.length === 1;
      i && (e = ue.get(t)), e === void 0 && ((this.o = e = new CSSStyleSheet()).replaceSync(this.cssText), i && ue.set(t, e));
    }
    return e;
  }
  toString() {
    return this.cssText;
  }
};
const je = (s) => new Ne(typeof s == "string" ? s : s + "", void 0, ne), K = (s, ...e) => {
  const t = s.length === 1 ? s[0] : e.reduce((i, r, n) => i + ((o) => {
    if (o._$cssResult$ === !0) return o.cssText;
    if (typeof o == "number") return o;
    throw Error("Value passed to 'css' function must be a 'css' function result: " + o + ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.");
  })(r) + s[n + 1], s[0]);
  return new Ne(t, s, ne);
}, Fe = (s, e) => {
  if (se) s.adoptedStyleSheets = e.map((t) => t instanceof CSSStyleSheet ? t : t.styleSheet);
  else for (const t of e) {
    const i = document.createElement("style"), r = q.litNonce;
    r !== void 0 && i.setAttribute("nonce", r), i.textContent = t.cssText, s.appendChild(i);
  }
}, me = se ? (s) => s : (s) => s instanceof CSSStyleSheet ? ((e) => {
  let t = "";
  for (const i of e.cssRules) t += i.cssText;
  return je(t);
})(s) : s;
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const { is: Be, defineProperty: qe, getOwnPropertyDescriptor: We, getOwnPropertyNames: Ve, getOwnPropertySymbols: Ge, getPrototypeOf: Ye } = Object, y = globalThis, fe = y.trustedTypes, Ke = fe ? fe.emptyScript : "", Qe = y.reactiveElementPolyfillSupport, R = (s, e) => s, V = { toAttribute(s, e) {
  switch (e) {
    case Boolean:
      s = s ? Ke : null;
      break;
    case Object:
    case Array:
      s = s == null ? s : JSON.stringify(s);
  }
  return s;
}, fromAttribute(s, e) {
  let t = s;
  switch (e) {
    case Boolean:
      t = s !== null;
      break;
    case Number:
      t = s === null ? null : Number(s);
      break;
    case Object:
    case Array:
      try {
        t = JSON.parse(s);
      } catch {
        t = null;
      }
  }
  return t;
} }, oe = (s, e) => !Be(s, e), ge = { attribute: !0, type: String, converter: V, reflect: !1, useDefault: !1, hasChanged: oe };
Symbol.metadata ?? (Symbol.metadata = Symbol("metadata")), y.litPropertyMetadata ?? (y.litPropertyMetadata = /* @__PURE__ */ new WeakMap());
let S = class extends HTMLElement {
  static addInitializer(e) {
    this._$Ei(), (this.l ?? (this.l = [])).push(e);
  }
  static get observedAttributes() {
    return this.finalize(), this._$Eh && [...this._$Eh.keys()];
  }
  static createProperty(e, t = ge) {
    if (t.state && (t.attribute = !1), this._$Ei(), this.prototype.hasOwnProperty(e) && ((t = Object.create(t)).wrapped = !0), this.elementProperties.set(e, t), !t.noAccessor) {
      const i = Symbol(), r = this.getPropertyDescriptor(e, i, t);
      r !== void 0 && qe(this.prototype, e, r);
    }
  }
  static getPropertyDescriptor(e, t, i) {
    const { get: r, set: n } = We(this.prototype, e) ?? { get() {
      return this[t];
    }, set(o) {
      this[t] = o;
    } };
    return { get: r, set(o) {
      const a = r?.call(this);
      n?.call(this, o), this.requestUpdate(e, a, i);
    }, configurable: !0, enumerable: !0 };
  }
  static getPropertyOptions(e) {
    return this.elementProperties.get(e) ?? ge;
  }
  static _$Ei() {
    if (this.hasOwnProperty(R("elementProperties"))) return;
    const e = Ye(this);
    e.finalize(), e.l !== void 0 && (this.l = [...e.l]), this.elementProperties = new Map(e.elementProperties);
  }
  static finalize() {
    if (this.hasOwnProperty(R("finalized"))) return;
    if (this.finalized = !0, this._$Ei(), this.hasOwnProperty(R("properties"))) {
      const t = this.properties, i = [...Ve(t), ...Ge(t)];
      for (const r of i) this.createProperty(r, t[r]);
    }
    const e = this[Symbol.metadata];
    if (e !== null) {
      const t = litPropertyMetadata.get(e);
      if (t !== void 0) for (const [i, r] of t) this.elementProperties.set(i, r);
    }
    this._$Eh = /* @__PURE__ */ new Map();
    for (const [t, i] of this.elementProperties) {
      const r = this._$Eu(t, i);
      r !== void 0 && this._$Eh.set(r, t);
    }
    this.elementStyles = this.finalizeStyles(this.styles);
  }
  static finalizeStyles(e) {
    const t = [];
    if (Array.isArray(e)) {
      const i = new Set(e.flat(1 / 0).reverse());
      for (const r of i) t.unshift(me(r));
    } else e !== void 0 && t.push(me(e));
    return t;
  }
  static _$Eu(e, t) {
    const i = t.attribute;
    return i === !1 ? void 0 : typeof i == "string" ? i : typeof e == "string" ? e.toLowerCase() : void 0;
  }
  constructor() {
    super(), this._$Ep = void 0, this.isUpdatePending = !1, this.hasUpdated = !1, this._$Em = null, this._$Ev();
  }
  _$Ev() {
    this._$ES = new Promise((e) => this.enableUpdating = e), this._$AL = /* @__PURE__ */ new Map(), this._$E_(), this.requestUpdate(), this.constructor.l?.forEach((e) => e(this));
  }
  addController(e) {
    (this._$EO ?? (this._$EO = /* @__PURE__ */ new Set())).add(e), this.renderRoot !== void 0 && this.isConnected && e.hostConnected?.();
  }
  removeController(e) {
    this._$EO?.delete(e);
  }
  _$E_() {
    const e = /* @__PURE__ */ new Map(), t = this.constructor.elementProperties;
    for (const i of t.keys()) this.hasOwnProperty(i) && (e.set(i, this[i]), delete this[i]);
    e.size > 0 && (this._$Ep = e);
  }
  createRenderRoot() {
    const e = this.shadowRoot ?? this.attachShadow(this.constructor.shadowRootOptions);
    return Fe(e, this.constructor.elementStyles), e;
  }
  connectedCallback() {
    this.renderRoot ?? (this.renderRoot = this.createRenderRoot()), this.enableUpdating(!0), this._$EO?.forEach((e) => e.hostConnected?.());
  }
  enableUpdating(e) {
  }
  disconnectedCallback() {
    this._$EO?.forEach((e) => e.hostDisconnected?.());
  }
  attributeChangedCallback(e, t, i) {
    this._$AK(e, i);
  }
  _$ET(e, t) {
    const i = this.constructor.elementProperties.get(e), r = this.constructor._$Eu(e, i);
    if (r !== void 0 && i.reflect === !0) {
      const n = (i.converter?.toAttribute !== void 0 ? i.converter : V).toAttribute(t, i.type);
      this._$Em = e, n == null ? this.removeAttribute(r) : this.setAttribute(r, n), this._$Em = null;
    }
  }
  _$AK(e, t) {
    const i = this.constructor, r = i._$Eh.get(e);
    if (r !== void 0 && this._$Em !== r) {
      const n = i.getPropertyOptions(r), o = typeof n.converter == "function" ? { fromAttribute: n.converter } : n.converter?.fromAttribute !== void 0 ? n.converter : V;
      this._$Em = r;
      const a = o.fromAttribute(t, n.type);
      this[r] = a ?? this._$Ej?.get(r) ?? a, this._$Em = null;
    }
  }
  requestUpdate(e, t, i, r = !1, n) {
    if (e !== void 0) {
      const o = this.constructor;
      if (r === !1 && (n = this[e]), i ?? (i = o.getPropertyOptions(e)), !((i.hasChanged ?? oe)(n, t) || i.useDefault && i.reflect && n === this._$Ej?.get(e) && !this.hasAttribute(o._$Eu(e, i)))) return;
      this.C(e, t, i);
    }
    this.isUpdatePending === !1 && (this._$ES = this._$EP());
  }
  C(e, t, { useDefault: i, reflect: r, wrapped: n }, o) {
    i && !(this._$Ej ?? (this._$Ej = /* @__PURE__ */ new Map())).has(e) && (this._$Ej.set(e, o ?? t ?? this[e]), n !== !0 || o !== void 0) || (this._$AL.has(e) || (this.hasUpdated || i || (t = void 0), this._$AL.set(e, t)), r === !0 && this._$Em !== e && (this._$Eq ?? (this._$Eq = /* @__PURE__ */ new Set())).add(e));
  }
  async _$EP() {
    this.isUpdatePending = !0;
    try {
      await this._$ES;
    } catch (t) {
      Promise.reject(t);
    }
    const e = this.scheduleUpdate();
    return e != null && await e, !this.isUpdatePending;
  }
  scheduleUpdate() {
    return this.performUpdate();
  }
  performUpdate() {
    if (!this.isUpdatePending) return;
    if (!this.hasUpdated) {
      if (this.renderRoot ?? (this.renderRoot = this.createRenderRoot()), this._$Ep) {
        for (const [r, n] of this._$Ep) this[r] = n;
        this._$Ep = void 0;
      }
      const i = this.constructor.elementProperties;
      if (i.size > 0) for (const [r, n] of i) {
        const { wrapped: o } = n, a = this[r];
        o !== !0 || this._$AL.has(r) || a === void 0 || this.C(r, void 0, n, a);
      }
    }
    let e = !1;
    const t = this._$AL;
    try {
      e = this.shouldUpdate(t), e ? (this.willUpdate(t), this._$EO?.forEach((i) => i.hostUpdate?.()), this.update(t)) : this._$EM();
    } catch (i) {
      throw e = !1, this._$EM(), i;
    }
    e && this._$AE(t);
  }
  willUpdate(e) {
  }
  _$AE(e) {
    this._$EO?.forEach((t) => t.hostUpdated?.()), this.hasUpdated || (this.hasUpdated = !0, this.firstUpdated(e)), this.updated(e);
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
  shouldUpdate(e) {
    return !0;
  }
  update(e) {
    this._$Eq && (this._$Eq = this._$Eq.forEach((t) => this._$ET(t, this[t]))), this._$EM();
  }
  updated(e) {
  }
  firstUpdated(e) {
  }
};
S.elementStyles = [], S.shadowRootOptions = { mode: "open" }, S[R("elementProperties")] = /* @__PURE__ */ new Map(), S[R("finalized")] = /* @__PURE__ */ new Map(), Qe?.({ ReactiveElement: S }), (y.reactiveElementVersions ?? (y.reactiveElementVersions = [])).push("2.1.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const O = globalThis, ve = (s) => s, G = O.trustedTypes, ye = G ? G.createPolicy("lit-html", { createHTML: (s) => s }) : void 0, Te = "$lit$", v = `lit$${Math.random().toFixed(9).slice(2)}$`, Re = "?" + v, Ze = `<${Re}>`, w = document, D = () => w.createComment(""), z = (s) => s === null || typeof s != "object" && typeof s != "function", ae = Array.isArray, Je = (s) => ae(s) || typeof s?.[Symbol.iterator] == "function", J = `[ 	
\f\r]`, N = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, _e = /-->/g, be = />/g, $ = RegExp(`>|${J}(?:([^\\s"'>=/]+)(${J}*=${J}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`, "g"), $e = /'/g, xe = /"/g, Oe = /^(?:script|style|textarea|title)$/i, Xe = (s) => (e, ...t) => ({ _$litType$: s, strings: e, values: t }), d = Xe(1), C = Symbol.for("lit-noChange"), l = Symbol.for("lit-nothing"), we = /* @__PURE__ */ new WeakMap(), x = w.createTreeWalker(w, 129);
function Me(s, e) {
  if (!ae(s) || !s.hasOwnProperty("raw")) throw Error("invalid template strings array");
  return ye !== void 0 ? ye.createHTML(e) : e;
}
const et = (s, e) => {
  const t = s.length - 1, i = [];
  let r, n = e === 2 ? "<svg>" : e === 3 ? "<math>" : "", o = N;
  for (let a = 0; a < t; a++) {
    const c = s[a];
    let h, u, p = -1, f = 0;
    for (; f < c.length && (o.lastIndex = f, u = o.exec(c), u !== null); ) f = o.lastIndex, o === N ? u[1] === "!--" ? o = _e : u[1] !== void 0 ? o = be : u[2] !== void 0 ? (Oe.test(u[2]) && (r = RegExp("</" + u[2], "g")), o = $) : u[3] !== void 0 && (o = $) : o === $ ? u[0] === ">" ? (o = r ?? N, p = -1) : u[1] === void 0 ? p = -2 : (p = o.lastIndex - u[2].length, h = u[1], o = u[3] === void 0 ? $ : u[3] === '"' ? xe : $e) : o === xe || o === $e ? o = $ : o === _e || o === be ? o = N : (o = $, r = void 0);
    const g = o === $ && s[a + 1].startsWith("/>") ? " " : "";
    n += o === N ? c + Ze : p >= 0 ? (i.push(h), c.slice(0, p) + Te + c.slice(p) + v + g) : c + v + (p === -2 ? a : g);
  }
  return [Me(s, n + (s[t] || "<?>") + (e === 2 ? "</svg>" : e === 3 ? "</math>" : "")), i];
};
class I {
  constructor({ strings: e, _$litType$: t }, i) {
    let r;
    this.parts = [];
    let n = 0, o = 0;
    const a = e.length - 1, c = this.parts, [h, u] = et(e, t);
    if (this.el = I.createElement(h, i), x.currentNode = this.el.content, t === 2 || t === 3) {
      const p = this.el.content.firstChild;
      p.replaceWith(...p.childNodes);
    }
    for (; (r = x.nextNode()) !== null && c.length < a; ) {
      if (r.nodeType === 1) {
        if (r.hasAttributes()) for (const p of r.getAttributeNames()) if (p.endsWith(Te)) {
          const f = u[o++], g = r.getAttribute(p).split(v), B = /([.?@])?(.*)/.exec(f);
          c.push({ type: 1, index: n, name: B[2], strings: g, ctor: B[1] === "." ? it : B[1] === "?" ? rt : B[1] === "@" ? st : Q }), r.removeAttribute(p);
        } else p.startsWith(v) && (c.push({ type: 6, index: n }), r.removeAttribute(p));
        if (Oe.test(r.tagName)) {
          const p = r.textContent.split(v), f = p.length - 1;
          if (f > 0) {
            r.textContent = G ? G.emptyScript : "";
            for (let g = 0; g < f; g++) r.append(p[g], D()), x.nextNode(), c.push({ type: 2, index: ++n });
            r.append(p[f], D());
          }
        }
      } else if (r.nodeType === 8) if (r.data === Re) c.push({ type: 2, index: n });
      else {
        let p = -1;
        for (; (p = r.data.indexOf(v, p + 1)) !== -1; ) c.push({ type: 7, index: n }), p += v.length - 1;
      }
      n++;
    }
  }
  static createElement(e, t) {
    const i = w.createElement("template");
    return i.innerHTML = e, i;
  }
}
function k(s, e, t = s, i) {
  if (e === C) return e;
  let r = i !== void 0 ? t._$Co?.[i] : t._$Cl;
  const n = z(e) ? void 0 : e._$litDirective$;
  return r?.constructor !== n && (r?._$AO?.(!1), n === void 0 ? r = void 0 : (r = new n(s), r._$AT(s, t, i)), i !== void 0 ? (t._$Co ?? (t._$Co = []))[i] = r : t._$Cl = r), r !== void 0 && (e = k(s, r._$AS(s, e.values), r, i)), e;
}
class tt {
  constructor(e, t) {
    this._$AV = [], this._$AN = void 0, this._$AD = e, this._$AM = t;
  }
  get parentNode() {
    return this._$AM.parentNode;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  u(e) {
    const { el: { content: t }, parts: i } = this._$AD, r = (e?.creationScope ?? w).importNode(t, !0);
    x.currentNode = r;
    let n = x.nextNode(), o = 0, a = 0, c = i[0];
    for (; c !== void 0; ) {
      if (o === c.index) {
        let h;
        c.type === 2 ? h = new j(n, n.nextSibling, this, e) : c.type === 1 ? h = new c.ctor(n, c.name, c.strings, this, e) : c.type === 6 && (h = new nt(n, this, e)), this._$AV.push(h), c = i[++a];
      }
      o !== c?.index && (n = x.nextNode(), o++);
    }
    return x.currentNode = w, r;
  }
  p(e) {
    let t = 0;
    for (const i of this._$AV) i !== void 0 && (i.strings !== void 0 ? (i._$AI(e, i, t), t += i.strings.length - 2) : i._$AI(e[t])), t++;
  }
}
class j {
  get _$AU() {
    return this._$AM?._$AU ?? this._$Cv;
  }
  constructor(e, t, i, r) {
    this.type = 2, this._$AH = l, this._$AN = void 0, this._$AA = e, this._$AB = t, this._$AM = i, this.options = r, this._$Cv = r?.isConnected ?? !0;
  }
  get parentNode() {
    let e = this._$AA.parentNode;
    const t = this._$AM;
    return t !== void 0 && e?.nodeType === 11 && (e = t.parentNode), e;
  }
  get startNode() {
    return this._$AA;
  }
  get endNode() {
    return this._$AB;
  }
  _$AI(e, t = this) {
    e = k(this, e, t), z(e) ? e === l || e == null || e === "" ? (this._$AH !== l && this._$AR(), this._$AH = l) : e !== this._$AH && e !== C && this._(e) : e._$litType$ !== void 0 ? this.$(e) : e.nodeType !== void 0 ? this.T(e) : Je(e) ? this.k(e) : this._(e);
  }
  O(e) {
    return this._$AA.parentNode.insertBefore(e, this._$AB);
  }
  T(e) {
    this._$AH !== e && (this._$AR(), this._$AH = this.O(e));
  }
  _(e) {
    this._$AH !== l && z(this._$AH) ? this._$AA.nextSibling.data = e : this.T(w.createTextNode(e)), this._$AH = e;
  }
  $(e) {
    const { values: t, _$litType$: i } = e, r = typeof i == "number" ? this._$AC(e) : (i.el === void 0 && (i.el = I.createElement(Me(i.h, i.h[0]), this.options)), i);
    if (this._$AH?._$AD === r) this._$AH.p(t);
    else {
      const n = new tt(r, this), o = n.u(this.options);
      n.p(t), this.T(o), this._$AH = n;
    }
  }
  _$AC(e) {
    let t = we.get(e.strings);
    return t === void 0 && we.set(e.strings, t = new I(e)), t;
  }
  k(e) {
    ae(this._$AH) || (this._$AH = [], this._$AR());
    const t = this._$AH;
    let i, r = 0;
    for (const n of e) r === t.length ? t.push(i = new j(this.O(D()), this.O(D()), this, this.options)) : i = t[r], i._$AI(n), r++;
    r < t.length && (this._$AR(i && i._$AB.nextSibling, r), t.length = r);
  }
  _$AR(e = this._$AA.nextSibling, t) {
    for (this._$AP?.(!1, !0, t); e !== this._$AB; ) {
      const i = ve(e).nextSibling;
      ve(e).remove(), e = i;
    }
  }
  setConnected(e) {
    this._$AM === void 0 && (this._$Cv = e, this._$AP?.(e));
  }
}
class Q {
  get tagName() {
    return this.element.tagName;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  constructor(e, t, i, r, n) {
    this.type = 1, this._$AH = l, this._$AN = void 0, this.element = e, this.name = t, this._$AM = r, this.options = n, i.length > 2 || i[0] !== "" || i[1] !== "" ? (this._$AH = Array(i.length - 1).fill(new String()), this.strings = i) : this._$AH = l;
  }
  _$AI(e, t = this, i, r) {
    const n = this.strings;
    let o = !1;
    if (n === void 0) e = k(this, e, t, 0), o = !z(e) || e !== this._$AH && e !== C, o && (this._$AH = e);
    else {
      const a = e;
      let c, h;
      for (e = n[0], c = 0; c < n.length - 1; c++) h = k(this, a[i + c], t, c), h === C && (h = this._$AH[c]), o || (o = !z(h) || h !== this._$AH[c]), h === l ? e = l : e !== l && (e += (h ?? "") + n[c + 1]), this._$AH[c] = h;
    }
    o && !r && this.j(e);
  }
  j(e) {
    e === l ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, e ?? "");
  }
}
class it extends Q {
  constructor() {
    super(...arguments), this.type = 3;
  }
  j(e) {
    this.element[this.name] = e === l ? void 0 : e;
  }
}
class rt extends Q {
  constructor() {
    super(...arguments), this.type = 4;
  }
  j(e) {
    this.element.toggleAttribute(this.name, !!e && e !== l);
  }
}
class st extends Q {
  constructor(e, t, i, r, n) {
    super(e, t, i, r, n), this.type = 5;
  }
  _$AI(e, t = this) {
    if ((e = k(this, e, t, 0) ?? l) === C) return;
    const i = this._$AH, r = e === l && i !== l || e.capture !== i.capture || e.once !== i.once || e.passive !== i.passive, n = e !== l && (i === l || r);
    r && this.element.removeEventListener(this.name, this, i), n && this.element.addEventListener(this.name, this, e), this._$AH = e;
  }
  handleEvent(e) {
    typeof this._$AH == "function" ? this._$AH.call(this.options?.host ?? this.element, e) : this._$AH.handleEvent(e);
  }
}
class nt {
  constructor(e, t, i) {
    this.element = e, this.type = 6, this._$AN = void 0, this._$AM = t, this.options = i;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AI(e) {
    k(this, e);
  }
}
const ot = O.litHtmlPolyfillSupport;
ot?.(I, j), (O.litHtmlVersions ?? (O.litHtmlVersions = [])).push("3.3.3");
const at = (s, e, t) => {
  const i = t?.renderBefore ?? e;
  let r = i._$litPart$;
  if (r === void 0) {
    const n = t?.renderBefore ?? null;
    i._$litPart$ = r = new j(e.insertBefore(D(), n), n, void 0, t ?? {});
  }
  return r._$AI(s), r;
};
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const M = globalThis;
class _ extends S {
  constructor() {
    super(...arguments), this.renderOptions = { host: this }, this._$Do = void 0;
  }
  createRenderRoot() {
    var t;
    const e = super.createRenderRoot();
    return (t = this.renderOptions).renderBefore ?? (t.renderBefore = e.firstChild), e;
  }
  update(e) {
    const t = this.render();
    this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(e), this._$Do = at(t, this.renderRoot, this.renderOptions);
  }
  connectedCallback() {
    super.connectedCallback(), this._$Do?.setConnected(!0);
  }
  disconnectedCallback() {
    super.disconnectedCallback(), this._$Do?.setConnected(!1);
  }
  render() {
    return C;
  }
}
_._$litElement$ = !0, _.finalized = !0, M.litElementHydrateSupport?.({ LitElement: _ });
const ct = M.litElementPolyfillSupport;
ct?.({ LitElement: _ });
(M.litElementVersions ?? (M.litElementVersions = [])).push("4.2.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const lt = { attribute: !0, type: String, converter: V, reflect: !1, hasChanged: oe }, dt = (s = lt, e, t) => {
  const { kind: i, metadata: r } = t;
  let n = globalThis.litPropertyMetadata.get(r);
  if (n === void 0 && globalThis.litPropertyMetadata.set(r, n = /* @__PURE__ */ new Map()), i === "setter" && ((s = Object.create(s)).wrapped = !0), n.set(t.name, s), i === "accessor") {
    const { name: o } = t;
    return { set(a) {
      const c = e.get.call(this);
      e.set.call(this, a), this.requestUpdate(o, c, s, !0, a);
    }, init(a) {
      return a !== void 0 && this.C(o, void 0, s, a), a;
    } };
  }
  if (i === "setter") {
    const { name: o } = t;
    return function(a) {
      const c = this[o];
      e.call(this, a), this.requestUpdate(o, c, s, !0, a);
    };
  }
  throw Error("Unsupported decorator location: " + i);
};
function F(s) {
  return (e, t) => typeof t == "object" ? dt(s, e, t) : ((i, r, n) => {
    const o = r.hasOwnProperty(n);
    return r.constructor.createProperty(n, i), o ? Object.getOwnPropertyDescriptor(r, n) : void 0;
  })(s, e, t);
}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
function P(s) {
  return F({ ...s, state: !0, attribute: !1 });
}
const pt = K`
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
`, ht = K`
  :host {
    display: block;
  }

  ha-card {
    padding: 12px 14px 14px;
    display: flex;
    flex-direction: column;
    gap: 10px;
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
    font-size: 1.05rem;
    font-weight: 600;
  }

  .title .icon {
    font-size: 1.2rem;
    line-height: 1;
  }

  .count {
    font-size: 0.8rem;
    color: var(--secondary-text-color, #757575);
  }

  .empty,
  .unavailable {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 12px;
    border-radius: 10px;
    background: var(--secondary-background-color, rgba(0, 0, 0, 0.03));
    color: var(--secondary-text-color, #757575);
    font-size: 0.9rem;
  }

  .list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .rec {
    border-radius: 10px;
    border-left: 4px solid var(--rec-color, var(--divider-color, #bdbdbd));
    background: var(--card-background-color, rgba(0, 0, 0, 0.03));
    box-shadow: inset 0 0 0 1px var(--divider-color, rgba(0, 0, 0, 0.08));
    overflow: hidden;
  }

  .rec-head {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 12px;
    cursor: pointer;
    user-select: none;
  }

  .rec-head:focus-visible {
    outline: 2px solid var(--primary-color, #03a9f4);
    outline-offset: -2px;
  }

  .badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 2px 8px;
    border-radius: 999px;
    color: white;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    background: var(--rec-color, #9e9e9e);
    flex-shrink: 0;
  }

  .rec-text {
    display: flex;
    flex-direction: column;
    flex: 1 1 auto;
    min-width: 0;
  }

  .rec-title {
    font-weight: 600;
    font-size: 0.95rem;
    line-height: 1.2;
  }

  .rec-desc {
    font-size: 0.8rem;
    color: var(--secondary-text-color, #757575);
    margin-top: 2px;
  }

  .chevron {
    font-size: 1.1rem;
    color: var(--secondary-text-color, #757575);
    transition: transform 0.2s ease;
    flex-shrink: 0;
  }

  .chevron.open {
    transform: rotate(90deg);
  }

  .rec-detail {
    padding: 0 12px 10px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    font-size: 0.85rem;
  }

  .rec-reason {
    color: var(--secondary-text-color, #757575);
  }

  .treatments {
    display: flex;
    flex-direction: column;
    gap: 4px;
    margin: 0;
    padding: 0;
    list-style: none;
  }

  .treatments li {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 8px;
    padding: 4px 0;
    border-top: 1px solid var(--divider-color, rgba(0, 0, 0, 0.08));
  }

  .treatments li:first-child {
    border-top: none;
  }

  .treatment-product {
    font-weight: 500;
  }

  .treatment-qty {
    color: var(--secondary-text-color, #757575);
    font-variant-numeric: tabular-nums;
  }

  .metrics-row {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
  }

  .metric-chip {
    font-size: 0.7rem;
    padding: 2px 8px;
    border-radius: 999px;
    background: var(--secondary-background-color, rgba(0, 0, 0, 0.06));
    color: var(--secondary-text-color, #757575);
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }

  .actions {
    display: flex;
    gap: 8px;
    justify-content: flex-end;
    flex-wrap: wrap;
  }

  .rec-actions {
    display: flex;
    gap: 8px;
    justify-content: flex-end;
    flex-wrap: wrap;
    padding: 0 12px 10px;
  }

  button.btn {
    border: none;
    border-radius: 8px;
    padding: 6px 14px;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    font-family: inherit;
    transition: filter 0.15s ease;
  }

  button.btn:focus-visible {
    outline: 2px solid var(--primary-color, #03a9f4);
    outline-offset: 2px;
  }

  button.btn.apply {
    background: var(--rec-color, var(--primary-color, #03a9f4));
    color: white;
  }

  button.btn.ignore {
    background: transparent;
    color: var(--secondary-text-color, #757575);
    box-shadow: inset 0 0 0 1px var(--divider-color, rgba(0, 0, 0, 0.15));
  }

  button.btn:hover {
    filter: brightness(0.95);
  }

  button.btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  @media (max-width: 360px) {
    ha-card {
      padding: 10px;
    }

    .rec-head {
      padding: 8px 10px;
    }

    .actions {
      justify-content: stretch;
    }

    button.btn {
      flex: 1 1 auto;
    }
  }
`, ut = K`
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

  .title .header-icon {
    font-size: 1.3rem;
    line-height: 1;
  }

  .total {
    font-size: 0.8rem;
    color: var(--secondary-text-color, #757575);
  }

  .timeline {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .day-header {
    margin: 8px 0 2px;
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--secondary-text-color, #757575);
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }

  .day-header:first-child {
    margin-top: 0;
  }

  .action-row {
    display: grid;
    grid-template-columns: auto 1fr auto;
    align-items: center;
    gap: 10px;
    padding: 8px 10px;
    border-radius: 10px;
    background: var(--card-background-color, rgba(0, 0, 0, 0.04));
    box-shadow: inset 0 0 0 1px var(--divider-color, rgba(0, 0, 0, 0.08));
  }

  .action-row.interactive {
    cursor: pointer;
    user-select: none;
  }

  .action-row.interactive:focus-visible {
    outline: 2px solid var(--primary-color, #03a9f4);
    outline-offset: 2px;
  }

  .action-icon {
    font-size: 1.4rem;
    line-height: 1;
    width: 1.6rem;
    text-align: center;
  }

  .action-body {
    display: flex;
    flex-direction: column;
    gap: 2px;
    min-width: 0;
  }

  .action-title {
    font-size: 0.95rem;
    font-weight: 600;
    color: var(--primary-text-color, #212121);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .action-meta {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 6px;
    font-size: 0.75rem;
    color: var(--secondary-text-color, #757575);
  }

  .source-badge {
    display: inline-flex;
    align-items: center;
    padding: 1px 8px;
    border-radius: 999px;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: white;
    background: var(--secondary-text-color, #757575);
  }

  .source-badge.recommendation {
    background: var(--warning-color, #ff9800);
  }

  .source-badge.automation {
    background: var(--primary-color, #03a9f4);
  }

  .source-badge.user {
    background: var(--success-color, #43a047);
  }

  .action-time {
    font-size: 0.75rem;
    color: var(--secondary-text-color, #757575);
    text-align: right;
    white-space: nowrap;
  }

  .empty {
    padding: 16px;
    text-align: center;
    color: var(--secondary-text-color, #757575);
    background: var(--secondary-background-color, rgba(0, 0, 0, 0.03));
    border-radius: 10px;
  }

  @media (max-width: 360px) {
    ha-card {
      padding: 12px;
    }

    .action-row {
      grid-template-columns: auto 1fr;
      grid-template-areas:
        "icon body"
        "icon time";
      row-gap: 2px;
    }

    .action-icon {
      grid-area: icon;
    }

    .action-body {
      grid-area: body;
    }

    .action-time {
      grid-area: time;
      text-align: left;
    }
  }
`, A = "—", mt = /* @__PURE__ */ new Set(["unavailable", "unknown", "none", ""]);
function b(s) {
  return s ? mt.has(s.state) : !0;
}
function Y(s, e) {
  const t = {
    ...e.entities ?? {}
  }, i = {
    status: "_status",
    water_quality_score: "_water_quality_score",
    recommendations: "_recommendations",
    problems: "_problems",
    action_history: "_action_history",
    temperature: "_temperature",
    ph: "_ph",
    free_chlorine: "_free_chlorine",
    orp: "_orp"
  }, r = (n) => n.endsWith("_status") && !/_(ph|orp|free_chlorine|tac|cya|hardness|salt|tds)_status$/.test(n);
  if (e.device_id && s.entities) {
    for (const n of Object.values(s.entities))
      if (n.device_id === e.device_id)
        for (const [o, a] of Object.entries(i))
          t[o] || (o === "status" ? r(n.entity_id) && (t[o] = n.entity_id) : n.entity_id.endsWith(a) && (t[o] = n.entity_id));
  }
  return t;
}
function m(s, e) {
  if (e)
    return s.states[e];
}
function ft(s) {
  if (!s || b(s)) return "unknown";
  const e = s.state.toLowerCase();
  return e === "ok" || e === "warning" || e === "critical" ? e : "unknown";
}
const gt = {
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
function vt(s) {
  return gt[s];
}
const yt = {
  temperature: { icon: "🌡️", label: "Temp", fractionDigits: 1, unitFallback: "°C" },
  ph: { icon: "⚗️", label: "pH", fractionDigits: 1, unitFallback: "" },
  free_chlorine: { icon: "🧪", label: "Cl", fractionDigits: 1, unitFallback: "mg/L" },
  orp: { icon: "⚡", label: "ORP", fractionDigits: 0, unitFallback: "mV" }
};
function _t(s) {
  return yt[s];
}
function bt(s, e, t) {
  if (b(s)) return A;
  const i = s.state, r = Number(i), n = s.attributes.unit_of_measurement ?? t;
  return Number.isFinite(r) ? `${r.toFixed(e)}${n ? ` ${n}` : ""}`.trim() : `${i}${n ? ` ${n}` : ""}`.trim();
}
function $t(s, e, t) {
  if (s.metrics?.length) return s.metrics;
  const i = ["temperature", "ph", "free_chlorine"], r = m(t, e.free_chlorine);
  return b(r) && e.orp && !b(m(t, e.orp)) ? ["temperature", "ph", "orp"] : i;
}
function xt(s) {
  return s >= 80 ? "good" : s >= 50 ? "warn" : "bad";
}
function De(s) {
  if (!s) return { count: 0, list: [] };
  const e = Number(s.state), t = s.attributes.recommendations ?? [];
  return { count: Number.isFinite(e) ? e : t.length, list: t };
}
const wt = {
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
function W(s) {
  return wt[s];
}
const ce = {
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
function ze(s, e) {
  return e ? `${s} ${e}` : s;
}
function At(s, e) {
  if (e === null || !Number.isFinite(e)) return A;
  if (s === null) return String(e);
  const t = ce[s];
  return t ? ze(e.toFixed(t.fractionDigits), t.unit) : String(e);
}
function Et(s, e) {
  if (!e || e.length !== 2) return A;
  const [t, i] = e;
  if (!Number.isFinite(t) || !Number.isFinite(i)) return A;
  if (s === null) return `${t}–${i}`;
  const r = ce[s];
  if (!r) return `${t}–${i}`;
  const n = t.toFixed(r.fractionDigits), o = i.toFixed(r.fractionDigits);
  return ze(`${n}–${o}`, r.unit);
}
function St(s) {
  return s === null ? "" : ce[s]?.label ?? s;
}
function Ae(s) {
  if (!s || b(s))
    return { count: 0, list: [], worst: "ok" };
  const e = s.attributes.problems ?? [], t = Number(s.state), i = Number.isFinite(t) ? t : e.length, n = s.attributes.worst_severity ?? e[0]?.severity ?? "ok";
  return { count: i, list: e, worst: n };
}
function Ct(s) {
  return s.treatments ?? s.actions ?? [];
}
const kt = {
  low: {
    label: "LOW",
    color: "var(--info-color, #2196f3)",
    icon: "ℹ️"
  },
  medium: {
    label: "MEDIUM",
    color: "var(--warning-color, #fbc02d)",
    icon: "⚠️"
  },
  high: {
    label: "HIGH",
    color: "var(--warning-color, #ff9800)",
    icon: "⚠️"
  },
  critical: {
    label: "CRITICAL",
    color: "var(--error-color, #e53935)",
    icon: "🚨"
  }
};
function Ie(s) {
  if (s.priority) return s.priority;
  switch (s.severity) {
    case "critical":
      return "critical";
    case "medium":
      return "medium";
    default:
      return "low";
  }
}
function Pt(s) {
  const e = Ie(s);
  return { key: e, ...kt[e] };
}
function Nt(s, e) {
  if (e.entity) return e.entity;
  if (!(!e.device_id || !s.entities)) {
    for (const t of Object.values(s.entities))
      if (t.device_id === e.device_id && t.entity_id.endsWith("_recommendations"))
        return t.entity_id;
  }
}
var Tt = Object.defineProperty, Ue = (s, e, t, i) => {
  for (var r = void 0, n = s.length - 1, o; n >= 0; n--)
    (o = s[n]) && (r = o(e, t, r) || r);
  return r && Tt(e, t, r), r;
};
const ee = "poolman-pool-overview-card", le = class le extends _ {
  /** Lovelace card size hint (1 unit ≈ 50px). */
  getCardSize() {
    return 3;
  }
  static getStubConfig() {
    return { type: `custom:${ee}` };
  }
  setConfig(e) {
    if (!e)
      throw new Error("Invalid configuration");
    if (!e.device_id && !e.entities)
      throw new Error(
        "poolman-pool-overview-card: either `device_id` or `entities` must be provided"
      );
    this._config = { show_score: !0, ...e };
  }
  render() {
    if (!this._config || !this.hass) return l;
    const e = Y(this.hass, this._config), t = m(this.hass, e.status), i = ft(t), r = vt(i), n = this._config.name ?? this._deviceName(this._config.device_id) ?? "Pool", o = $t(this._config, e, this.hass);
    return d`
      <ha-card>
        <div class="header">
          <div class="title">
            <span class="pool-icon" aria-hidden="true">🏊</span>
            <span>${n}</span>
          </div>
          <span
            class="badge"
            style=${`background:${r.color}`}
            role="status"
            aria-label=${`Status: ${r.label}`}
          >
            <span class="dot" aria-hidden="true"></span>
            ${r.label}
          </span>
        </div>

        <div class="metrics">
          ${o.map((a) => this._renderMetric(a, e))}
        </div>

        ${this._config.show_score !== !1 ? this._renderScore(e.water_quality_score) : l}
        ${this._renderRecommendations(e.recommendations)}
      </ha-card>
    `;
  }
  _renderMetric(e, t) {
    const i = _t(e), r = m(this.hass, t[e]), n = bt(r, i.fractionDigits, i.unitFallback);
    return d`
      <div class="metric" data-key=${e}>
        <span class="metric-label">
          <span aria-hidden="true">${i.icon}</span>
          ${i.label}
        </span>
        <span class="metric-value">${n}</span>
      </div>
    `;
  }
  _renderScore(e) {
    const t = m(this.hass, e);
    if (b(t))
      return d`
        <div class="score">
          <div class="score-row">
            <span>Quality score</span>
            <strong>${A}</strong>
          </div>
        </div>
      `;
    const i = Math.max(0, Math.min(100, Number(t.state) || 0)), r = xt(i);
    return d`
      <div class="score">
        <div class="score-row">
          <span>Quality score</span>
          <strong>${i} / 100</strong>
        </div>
        <div class="score-bar">
          <div
            class="score-bar-fill ${r === "good" ? "" : r}"
            style=${`width:${i}%`}
          ></div>
        </div>
      </div>
    `;
  }
  _renderRecommendations(e) {
    const t = m(this.hass, e);
    if (!t) return l;
    const { count: i } = De(t), r = this._config?.recommendations_path, n = i > 0, o = i === 0 ? "Your pool is in good condition" : `${i} recommendation${i === 1 ? "" : "s"}`;
    return d`
      <div
        class="recommendations"
        role=${n ? "button" : "presentation"}
        tabindex=${n ? "0" : "-1"}
        ?disabled=${!n}
        @click=${() => n && this._openRecommendations(t.entity_id, r)}
        @keydown=${(c) => {
      n && (c.key === "Enter" || c.key === " ") && (c.preventDefault(), this._openRecommendations(t.entity_id, r));
    }}
      >
        <span class="label">
          <span aria-hidden="true">${i === 0 ? "✅" : "⚠️"}</span>
          ${o}
        </span>
        ${n ? d`<span class="chevron" aria-hidden="true">›</span>` : l}
      </div>
    `;
  }
  _openRecommendations(e, t) {
    if (t) {
      this.dispatchEvent(
        new CustomEvent("location-changed", {
          bubbles: !0,
          composed: !0,
          detail: { replace: !1 }
        })
      ), history.pushState(null, "", t);
      return;
    }
    this.dispatchEvent(
      new CustomEvent("hass-more-info", {
        bubbles: !0,
        composed: !0,
        detail: { entityId: e }
      })
    );
  }
  _deviceName(e) {
    if (!e || !this.hass?.devices) return;
    const t = this.hass.devices[e];
    if (t)
      return t.name_by_user ?? t.name ?? void 0;
  }
};
le.styles = pt;
let U = le;
Ue([
  F({ attribute: !1 })
], U.prototype, "hass");
Ue([
  P()
], U.prototype, "_config");
customElements.get(ee) || customElements.define(ee, U);
const Rt = K`
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
var Ot = Object.defineProperty, Le = (s, e, t, i) => {
  for (var r = void 0, n = s.length - 1, o; n >= 0; n--)
    (o = s[n]) && (r = o(e, t, r) || r);
  return r && Ot(e, t, r), r;
};
const te = "poolman-problem-card", Ee = {
  ok: {
    label: "OK",
    color: "var(--success-color, #43a047)",
    icon: "✅"
  },
  low: W("low"),
  medium: W("medium"),
  critical: W("critical")
}, de = class de extends _ {
  /** Lovelace card size hint (1 unit ≈ 50px). */
  getCardSize() {
    const e = this._resolveEntity();
    if (!e) return 1;
    const { count: t } = Ae(e);
    if (t === 0) return 1;
    const i = this._config?.max ?? t;
    return 1 + Math.min(t, i);
  }
  static getStubConfig() {
    return { type: `custom:${te}` };
  }
  setConfig(e) {
    if (!e)
      throw new Error("Invalid configuration");
    if (!e.device_id && !e.entity)
      throw new Error(
        "poolman-problem-card: either `device_id` or `entity` must be provided"
      );
    if (e.max !== void 0 && (!Number.isFinite(e.max) || e.max < 1))
      throw new Error("poolman-problem-card: `max` must be a positive integer");
    this._config = { ...e };
  }
  render() {
    if (!this._config || !this.hass) return l;
    const e = this._resolveEntity(), t = this._config.name ?? this._deviceName() ?? "Pool Problems";
    if (!e || b(e))
      return d`
        <ha-card>
          <div class="header">
            <div class="title">
              <span class="icon" aria-hidden="true">🩺</span>
              <span>${t}</span>
            </div>
          </div>
          <div class="unavailable" role="status">
            <span aria-hidden="true">❔</span>
            <span>Problems entity unavailable</span>
          </div>
        </ha-card>
      `;
    const { count: i, list: r, worst: n } = Ae(e), o = Ee[n] ?? Ee.ok;
    return d`
      <ha-card>
        <div class="header">
          <div class="title">
            <span class="icon" aria-hidden="true">🩺</span>
            <span>${t}</span>
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

        ${i === 0 ? d`
              <div class="empty" role="status">
                <span aria-hidden="true">✅</span>
                <span>No problems detected — pool is healthy</span>
              </div>
            ` : this._renderProblems(r, i)}
      </ha-card>
    `;
  }
  _renderProblems(e, t) {
    const i = this._config?.max, r = i !== void 0 ? e.slice(0, i) : e, n = Math.max(0, t - r.length);
    return d`
      <div class="problems">
        ${r.map((o) => this._renderProblem(o))}
        ${n > 0 ? d`<div class="more">
              +${n} more problem${n === 1 ? "" : "s"}
            </div>` : l}
      </div>
    `;
  }
  _renderProblem(e) {
    const t = e.severity, i = W(t), r = St(e.metric), n = e.metric !== null && e.value !== null && e.expected_range !== null;
    return d`
      <div
        class="problem"
        data-code=${e.code}
        data-severity=${t}
        style=${`--problem-color:${i.color}`}
      >
        <span class="severity" aria-label=${`Severity: ${i.label}`}>
          <span aria-hidden="true">${i.icon}</span>
          ${i.label}
        </span>
        <span class="message">${e.message}</span>
        ${n ? d`
              <div class="details">
                ${r ? d`<span class="metric-label">${r}</span>
                      <span class="sep" aria-hidden="true">•</span>` : l}
                <span>
                  Current:
                  <strong>${At(e.metric, e.value)}</strong>
                </span>
                <span class="sep" aria-hidden="true">—</span>
                <span>
                  Expected:
                  <strong
                    >${Et(e.metric, e.expected_range)}</strong
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
      return m(this.hass, this._config.entity);
    const e = Y(this.hass, {
      type: this._config.type,
      device_id: this._config.device_id
    });
    return m(this.hass, e.problems);
  }
  _deviceName() {
    const e = this._config?.device_id;
    if (!e || !this.hass?.devices) return;
    const t = this.hass.devices[e];
    if (t)
      return t.name_by_user ?? t.name ?? void 0;
  }
};
de.styles = Rt;
let L = de;
Le([
  F({ attribute: !1 })
], L.prototype, "hass");
Le([
  P()
], L.prototype, "_config");
customElements.get(te) || customElements.define(te, L);
var Mt = Object.defineProperty, Z = (s, e, t, i) => {
  for (var r = void 0, n = s.length - 1, o; n >= 0; n--)
    (o = s[n]) && (r = o(e, t, r) || r);
  return r && Mt(e, t, r), r;
};
const ie = "poolman-recommendations-card", pe = class pe extends _ {
  constructor() {
    super(...arguments), this._dismissed = /* @__PURE__ */ new Set(), this._expanded = /* @__PURE__ */ new Set(), this._lastSeenIds = /* @__PURE__ */ new Set();
  }
  /** Lovelace card size hint (1 unit ≈ 50px). */
  getCardSize() {
    return 4;
  }
  static getStubConfig() {
    return { type: `custom:${ie}` };
  }
  setConfig(e) {
    if (!e)
      throw new Error("Invalid configuration");
    if (!e.device_id && !e.entity)
      throw new Error(
        "poolman-recommendations-card: either `device_id` or `entity` must be provided"
      );
    const t = e.confirm_apply ?? "critical_high";
    this._config = {
      show_severity: !0,
      ...e,
      confirm_apply: t
    };
  }
  updated(e) {
    if (this._dismissed.size === 0) return;
    let t = !1;
    for (const i of this._dismissed)
      this._lastSeenIds.has(i) || (this._dismissed.delete(i), t = !0);
    t && (this._dismissed = new Set(this._dismissed));
  }
  render() {
    if (!this._config || !this.hass) return l;
    const e = Nt(this.hass, this._config), t = m(this.hass, e), i = this._config.name ?? this._deviceName() ?? "Recommendations";
    if (!t || b(t))
      return d`
        <ha-card>
          <div class="header">
            <div class="title">
              <span class="icon" aria-hidden="true">📋</span>
              <span>${i}</span>
            </div>
          </div>
          <div class="unavailable" role="status">
            <span aria-hidden="true">⚠️</span>
            Recommendations unavailable
          </div>
        </ha-card>
      `;
    const { count: r, list: n } = De(t);
    this._lastSeenIds = new Set(n.map((a) => a.id));
    const o = n.filter((a) => !this._dismissed.has(a.id));
    return d`
      <ha-card>
        <div class="header">
          <div class="title">
            <span class="icon" aria-hidden="true">📋</span>
            <span>${i}</span>
          </div>
          ${r > 0 ? d`<span class="count">${o.length} / ${r}</span>` : l}
        </div>

        ${o.length === 0 ? this._renderEmpty() : d`<div class="list">${o.map((a) => this._renderRecommendation(a))}</div>`}
      </ha-card>
    `;
  }
  _renderEmpty() {
    return d`
      <div class="empty" role="status">
        <span aria-hidden="true">✅</span>
        Your pool is in good condition
      </div>
    `;
  }
  _renderRecommendation(e) {
    const t = Pt(e), i = this._expanded.has(e.id), r = this._config?.show_severity !== !1, n = Ct(e);
    return d`
      <div
        class="rec"
        data-id=${e.id}
        data-priority=${t.key}
        style=${`--rec-color:${t.color}`}
      >
        <div
          class="rec-head"
          role="button"
          tabindex="0"
          aria-expanded=${i ? "true" : "false"}
          @click=${() => this._toggle(e.id)}
          @keydown=${(o) => {
      (o.key === "Enter" || o.key === " ") && (o.preventDefault(), this._toggle(e.id));
    }}
        >
          <span
            class="badge"
            aria-label=${`Priority: ${t.label}`}
          >
            <span aria-hidden="true">${t.icon}</span>
            ${r ? d`<span>${t.label}</span>` : l}
          </span>
          <span class="rec-text">
            <span class="rec-title">${e.title}</span>
            ${e.description ? d`<span class="rec-desc">${e.description}</span>` : l}
          </span>
          <span
            class=${`chevron ${i ? "open" : ""}`}
            aria-hidden="true"
          >›</span>
        </div>
        ${i ? this._renderDetail(e, n) : l}
        <div class="rec-actions">
          <button
            class="btn ignore"
            type="button"
            @click=${(o) => {
      o.stopPropagation(), this._ignore(e.id);
    }}
          >
            Ignore
          </button>
          <button
            class="btn apply"
            type="button"
            @click=${(o) => {
      o.stopPropagation(), this._apply(e);
    }}
          >
            Apply
          </button>
        </div>
      </div>
    `;
  }
  _renderDetail(e, t) {
    return d`
      <div class="rec-detail">
        ${e.reason ? d`<div class="rec-reason"><strong>Reason:</strong> ${e.reason}</div>` : l}
        ${t.length > 0 ? d`
              <ul class="treatments" aria-label="Treatments">
                ${t.map(
      (i) => d`
                    <li>
                      <span class="treatment-product">${i.name}</span>
                      <span class="treatment-qty"
                        >${this._formatQuantity(i.quantity)} ${i.unit}</span
                      >
                    </li>
                  `
    )}
              </ul>
            ` : l}
        ${e.related_metrics && e.related_metrics.length > 0 ? d`
              <div class="metrics-row">
                ${e.related_metrics.map(
      (i) => d`<span class="metric-chip">${i}</span>`
    )}
              </div>
            ` : l}
      </div>
    `;
  }
  _toggle(e) {
    const t = new Set(this._expanded);
    t.has(e) ? t.delete(e) : t.add(e), this._expanded = t;
  }
  _formatQuantity(e) {
    if (!Number.isFinite(e)) return String(e ?? "");
    const t = this.hass?.locale?.language ?? "en";
    return e.toLocaleString(t, { maximumFractionDigits: 2 });
  }
  _ignore(e) {
    const t = new Set(this._dismissed);
    t.add(e), this._dismissed = t;
  }
  async _apply(e) {
    if (!this.hass?.callService) return;
    const t = this._config?.device_id;
    if (!t) {
      console.error(
        "poolman-recommendations-card: cannot apply recommendation without `device_id`"
      );
      return;
    }
    if (!this._shouldConfirm(e)) {
      await this._callApply(t, e.id);
      return;
    }
    const i = globalThis.confirm;
    (i ? i(`Apply "${e.title}"?`) : !0) && await this._callApply(t, e.id);
  }
  async _callApply(e, t) {
    try {
      await this.hass.callService("poolman", "apply_recommendation", {
        device_id: e,
        recommendation_id: t
      });
    } catch (i) {
      console.error("poolman-recommendations-card: apply failed", i);
    }
  }
  _shouldConfirm(e) {
    const t = this._config?.confirm_apply ?? "critical_high";
    if (t === "never") return !1;
    if (t === "always") return !0;
    const i = Ie(e);
    return i === "critical" || i === "high";
  }
  _deviceName() {
    const e = this._config?.device_id;
    if (!e || !this.hass?.devices) return;
    const t = this.hass.devices[e];
    if (t)
      return t.name_by_user ?? t.name ?? void 0;
  }
};
pe.styles = ht;
let E = pe;
Z([
  F({ attribute: !1 })
], E.prototype, "hass");
Z([
  P()
], E.prototype, "_config");
Z([
  P()
], E.prototype, "_dismissed");
Z([
  P()
], E.prototype, "_expanded");
customElements.get(ie) || customElements.define(ie, E);
var Dt = Object.defineProperty, He = (s, e, t, i) => {
  for (var r = void 0, n = s.length - 1, o; n >= 0; n--)
    (o = s[n]) && (r = o(e, t, r) || r);
  return r && Dt(e, t, r), r;
};
const re = "poolman-action-history-card", X = 50, zt = {
  chemical: "🧪",
  cleaning: "🧹",
  maintenance: "🔧"
}, It = {
  chemical: "Chemical treatment",
  cleaning: "Cleaning",
  maintenance: "Maintenance"
}, Ut = {
  user: "Manual",
  recommendation: "Recommendation",
  automation: "Automation"
};
function Lt(s) {
  if (s.type !== "chemical" || !Number.isFinite(s.quantity)) return A;
  const e = Number.isInteger(s.quantity) ? s.quantity.toString() : s.quantity.toFixed(1);
  return s.unit ? `${e} ${s.unit}` : e;
}
function T(s) {
  return `${s.getFullYear()}-${String(s.getMonth() + 1).padStart(2, "0")}-${String(
    s.getDate()
  ).padStart(2, "0")}`;
}
const he = class he extends _ {
  /** Lovelace card size hint (1 unit ≈ 50px). */
  getCardSize() {
    return 4;
  }
  static getStubConfig() {
    return { type: `custom:${re}` };
  }
  setConfig(e) {
    if (!e)
      throw new Error("Invalid configuration");
    if (!e.device_id && !e.entities?.action_history)
      throw new Error(
        "poolman-action-history-card: either `device_id` or `entities.action_history` must be provided"
      );
    const t = e.limit, i = typeof t == "number" && t > 0 ? Math.min(Math.floor(t), X) : X;
    this._config = {
      show_source: !0,
      group_by_day: !0,
      ...e,
      limit: i
    };
  }
  render() {
    if (!this._config || !this.hass) return l;
    const t = Y(this.hass, this._config).action_history, i = m(this.hass, t), r = this._readActions(i), n = this._config.name ?? this._deviceName(this._config.device_id) ?? "Pool";
    return d`
      <ha-card>
        <div class="header">
          <div class="title">
            <span class="header-icon" aria-hidden="true">📋</span>
            <span>${n} — Action history</span>
          </div>
          ${r.length > 0 ? d`<span class="total">${r.length}</span>` : l}
        </div>

        ${r.length === 0 ? d`<div class="empty">No actions recorded yet</div>` : d`<div class="timeline">${this._renderTimeline(r)}</div>`}
      </ha-card>
    `;
  }
  _readActions(e) {
    if (!e) return [];
    const t = e.attributes.actions;
    if (!Array.isArray(t)) return [];
    const i = this._config?.limit ?? X;
    return t.filter((r) => r && typeof r.timestamp == "string").slice().sort((r, n) => r.timestamp < n.timestamp ? 1 : -1).slice(0, i);
  }
  _renderTimeline(e) {
    if (!(this._config?.group_by_day !== !1))
      return e.map((n) => this._renderRow(n));
    const i = [];
    let r;
    for (const n of e) {
      const o = new Date(n.timestamp), a = T(o);
      a !== r && (r = a, i.push(
        d`<div class="day-header">${this._formatDayHeader(o)}</div>`
      )), i.push(this._renderRow(n));
    }
    return i;
  }
  _renderRow(e) {
    const t = zt[e.type] ?? "•", i = It[e.type] ?? e.type, r = Ut[e.source] ?? e.source, n = Lt(e), o = !!e.recommendation_id, a = this._formatTime(new Date(e.timestamp)), c = () => this._openAction(e);
    return d`
      <div
        class="action-row ${o ? "interactive" : ""}"
        data-type=${e.type}
        data-source=${e.source}
        role=${o ? "button" : "presentation"}
        tabindex=${o ? "0" : "-1"}
        @click=${o ? c : l}
        @keydown=${o ? (h) => {
      (h.key === "Enter" || h.key === " ") && (h.preventDefault(), c());
    } : l}
      >
        <span class="action-icon" aria-hidden="true">${t}</span>
        <div class="action-body">
          <span class="action-title">
            ${i}${e.treatment_id ? d` · ${e.treatment_id}` : l}
          </span>
          <span class="action-meta">
            <span class="quantity">${n}</span>
            ${this._config?.show_source !== !1 ? d`<span class="source-badge ${e.source}">${r}</span>` : l}
          </span>
        </div>
        <span class="action-time">${a}</span>
      </div>
    `;
  }
  _openAction(e) {
    const t = Y(this.hass, this._config), i = t.recommendations ?? t.action_history;
    i && this.dispatchEvent(
      new CustomEvent("hass-more-info", {
        bubbles: !0,
        composed: !0,
        detail: { entityId: i, action_id: e.id }
      })
    );
  }
  _formatDayHeader(e) {
    const t = /* @__PURE__ */ new Date(), i = /* @__PURE__ */ new Date();
    if (i.setDate(t.getDate() - 1), T(e) === T(t)) return "Today";
    if (T(e) === T(i)) return "Yesterday";
    const r = this.hass?.locale?.language;
    try {
      return new Intl.DateTimeFormat(r, {
        weekday: "long",
        day: "2-digit",
        month: "short",
        year: e.getFullYear() === t.getFullYear() ? void 0 : "numeric"
      }).format(e);
    } catch {
      return e.toDateString();
    }
  }
  _formatTime(e) {
    const t = this.hass?.locale?.language;
    try {
      return new Intl.DateTimeFormat(t, {
        hour: "2-digit",
        minute: "2-digit"
      }).format(e);
    } catch {
      return `${String(e.getHours()).padStart(2, "0")}:${String(
        e.getMinutes()
      ).padStart(2, "0")}`;
    }
  }
  _deviceName(e) {
    if (!e || !this.hass?.devices) return;
    const t = this.hass.devices[e];
    if (t)
      return t.name_by_user ?? t.name ?? void 0;
  }
};
he.styles = ut;
let H = he;
He([
  F({ attribute: !1 })
], H.prototype, "hass");
He([
  P()
], H.prototype, "_config");
customElements.get(re) || customElements.define(re, H);
const Se = "poolman-pool-overview-card", Ce = "poolman-problem-card", ke = "poolman-recommendations-card", Pe = "poolman-action-history-card", Ht = "0.1.0";
window.customCards = window.customCards ?? [];
window.customCards.some((s) => s.type === Se) || window.customCards.push({
  type: Se,
  name: "Pool Overview",
  description: "Glanceable summary card for a Pool Manager pool: status badge, key chemistry metrics, water quality score and recommendation count.",
  preview: !0,
  documentationURL: "https://noirbizarre.github.io/hass-poolman/pool-overview-card/"
});
window.customCards.some((s) => s.type === Ce) || window.customCards.push({
  type: Ce,
  name: "Pool Problems",
  description: "Diagnostic card listing the current pool problems by severity, with measured value and expected range.",
  preview: !0,
  documentationURL: "https://noirbizarre.github.io/hass-poolman/problem-card/"
});
window.customCards.some((s) => s.type === ke) || window.customCards.push({
  type: ke,
  name: "Pool Recommendations",
  description: "Actionable pool recommendation list: severity badges, expandable details, and one-tap Apply / Ignore buttons backed by the poolman.apply_recommendation service.",
  preview: !0,
  documentationURL: "https://noirbizarre.github.io/hass-poolman/recommendations-card/"
});
window.customCards.some((s) => s.type === Pe) || window.customCards.push({
  type: Pe,
  name: "Pool Action History",
  description: "Chronological timeline of recorded pool actions (chemical treatments, cleaning, maintenance) with source badges.",
  preview: !0,
  documentationURL: "https://noirbizarre.github.io/hass-poolman/action-history-card/"
});
console.info(
  `%c POOLMAN-CARDS %c v${Ht} `,
  "color: white; background: #03a9f4; font-weight: 700;",
  "color: #03a9f4; background: transparent; font-weight: 700;"
);
//# sourceMappingURL=poolman-pool-overview-card.js.map
