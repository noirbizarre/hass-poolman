/**
 * @license
 * Copyright 2019 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const Y = globalThis, ce = Y.ShadowRoot && (Y.ShadyCSS === void 0 || Y.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype, le = Symbol(), ve = /* @__PURE__ */ new WeakMap();
let Me = class {
  constructor(e, t, i) {
    if (this._$cssResult$ = !0, i !== le) throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
    this.cssText = e, this.t = t;
  }
  get styleSheet() {
    let e = this.o;
    const t = this.t;
    if (ce && e === void 0) {
      const i = t !== void 0 && t.length === 1;
      i && (e = ve.get(t)), e === void 0 && ((this.o = e = new CSSStyleSheet()).replaceSync(this.cssText), i && ve.set(t, e));
    }
    return e;
  }
  toString() {
    return this.cssText;
  }
};
const Qe = (s) => new Me(typeof s == "string" ? s : s + "", void 0, le), V = (s, ...e) => {
  const t = s.length === 1 ? s[0] : e.reduce((i, r, o) => i + ((n) => {
    if (n._$cssResult$ === !0) return n.cssText;
    if (typeof n == "number") return n;
    throw Error("Value passed to 'css' function must be a 'css' function result: " + n + ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.");
  })(r) + s[o + 1], s[0]);
  return new Me(t, s, le);
}, Ke = (s, e) => {
  if (ce) s.adoptedStyleSheets = e.map((t) => t instanceof CSSStyleSheet ? t : t.styleSheet);
  else for (const t of e) {
    const i = document.createElement("style"), r = Y.litNonce;
    r !== void 0 && i.setAttribute("nonce", r), i.textContent = t.cssText, s.appendChild(i);
  }
}, ye = ce ? (s) => s : (s) => s instanceof CSSStyleSheet ? ((e) => {
  let t = "";
  for (const i of e.cssRules) t += i.cssText;
  return Qe(t);
})(s) : s;
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const { is: Ze, defineProperty: Je, getOwnPropertyDescriptor: Xe, getOwnPropertyNames: et, getOwnPropertySymbols: tt, getPrototypeOf: it } = Object, x = globalThis, be = x.trustedTypes, rt = be ? be.emptyScript : "", st = x.reactiveElementPolyfillSupport, z = (s, e) => s, K = { toAttribute(s, e) {
  switch (e) {
    case Boolean:
      s = s ? rt : null;
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
} }, de = (s, e) => !Ze(s, e), $e = { attribute: !0, type: String, converter: K, reflect: !1, useDefault: !1, hasChanged: de };
Symbol.metadata ?? (Symbol.metadata = Symbol("metadata")), x.litPropertyMetadata ?? (x.litPropertyMetadata = /* @__PURE__ */ new WeakMap());
let R = class extends HTMLElement {
  static addInitializer(e) {
    this._$Ei(), (this.l ?? (this.l = [])).push(e);
  }
  static get observedAttributes() {
    return this.finalize(), this._$Eh && [...this._$Eh.keys()];
  }
  static createProperty(e, t = $e) {
    if (t.state && (t.attribute = !1), this._$Ei(), this.prototype.hasOwnProperty(e) && ((t = Object.create(t)).wrapped = !0), this.elementProperties.set(e, t), !t.noAccessor) {
      const i = Symbol(), r = this.getPropertyDescriptor(e, i, t);
      r !== void 0 && Je(this.prototype, e, r);
    }
  }
  static getPropertyDescriptor(e, t, i) {
    const { get: r, set: o } = Xe(this.prototype, e) ?? { get() {
      return this[t];
    }, set(n) {
      this[t] = n;
    } };
    return { get: r, set(n) {
      const a = r?.call(this);
      o?.call(this, n), this.requestUpdate(e, a, i);
    }, configurable: !0, enumerable: !0 };
  }
  static getPropertyOptions(e) {
    return this.elementProperties.get(e) ?? $e;
  }
  static _$Ei() {
    if (this.hasOwnProperty(z("elementProperties"))) return;
    const e = it(this);
    e.finalize(), e.l !== void 0 && (this.l = [...e.l]), this.elementProperties = new Map(e.elementProperties);
  }
  static finalize() {
    if (this.hasOwnProperty(z("finalized"))) return;
    if (this.finalized = !0, this._$Ei(), this.hasOwnProperty(z("properties"))) {
      const t = this.properties, i = [...et(t), ...tt(t)];
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
      for (const r of i) t.unshift(ye(r));
    } else e !== void 0 && t.push(ye(e));
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
    return Ke(e, this.constructor.elementStyles), e;
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
      const o = (i.converter?.toAttribute !== void 0 ? i.converter : K).toAttribute(t, i.type);
      this._$Em = e, o == null ? this.removeAttribute(r) : this.setAttribute(r, o), this._$Em = null;
    }
  }
  _$AK(e, t) {
    const i = this.constructor, r = i._$Eh.get(e);
    if (r !== void 0 && this._$Em !== r) {
      const o = i.getPropertyOptions(r), n = typeof o.converter == "function" ? { fromAttribute: o.converter } : o.converter?.fromAttribute !== void 0 ? o.converter : K;
      this._$Em = r;
      const a = n.fromAttribute(t, o.type);
      this[r] = a ?? this._$Ej?.get(r) ?? a, this._$Em = null;
    }
  }
  requestUpdate(e, t, i, r = !1, o) {
    if (e !== void 0) {
      const n = this.constructor;
      if (r === !1 && (o = this[e]), i ?? (i = n.getPropertyOptions(e)), !((i.hasChanged ?? de)(o, t) || i.useDefault && i.reflect && o === this._$Ej?.get(e) && !this.hasAttribute(n._$Eu(e, i)))) return;
      this.C(e, t, i);
    }
    this.isUpdatePending === !1 && (this._$ES = this._$EP());
  }
  C(e, t, { useDefault: i, reflect: r, wrapped: o }, n) {
    i && !(this._$Ej ?? (this._$Ej = /* @__PURE__ */ new Map())).has(e) && (this._$Ej.set(e, n ?? t ?? this[e]), o !== !0 || n !== void 0) || (this._$AL.has(e) || (this.hasUpdated || i || (t = void 0), this._$AL.set(e, t)), r === !0 && this._$Em !== e && (this._$Eq ?? (this._$Eq = /* @__PURE__ */ new Set())).add(e));
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
        for (const [r, o] of this._$Ep) this[r] = o;
        this._$Ep = void 0;
      }
      const i = this.constructor.elementProperties;
      if (i.size > 0) for (const [r, o] of i) {
        const { wrapped: n } = o, a = this[r];
        n !== !0 || this._$AL.has(r) || a === void 0 || this.C(r, void 0, o, a);
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
R.elementStyles = [], R.shadowRootOptions = { mode: "open" }, R[z("elementProperties")] = /* @__PURE__ */ new Map(), R[z("finalized")] = /* @__PURE__ */ new Map(), st?.({ ReactiveElement: R }), (x.reactiveElementVersions ?? (x.reactiveElementVersions = [])).push("2.1.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const I = globalThis, xe = (s) => s, Z = I.trustedTypes, we = Z ? Z.createPolicy("lit-html", { createHTML: (s) => s }) : void 0, Ue = "$lit$", $ = `lit$${Math.random().toFixed(9).slice(2)}$`, Le = "?" + $, ot = `<${Le}>`, S = document, U = () => S.createComment(""), L = (s) => s === null || typeof s != "object" && typeof s != "function", pe = Array.isArray, nt = (s) => pe(s) || typeof s?.[Symbol.iterator] == "function", te = `[ 	
\f\r]`, P = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, Ae = /-->/g, Ee = />/g, A = RegExp(`>|${te}(?:([^\\s"'>=/]+)(${te}*=${te}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`, "g"), Se = /'/g, ke = /"/g, He = /^(?:script|style|textarea|title)$/i, at = (s) => (e, ...t) => ({ _$litType$: s, strings: e, values: t }), d = at(1), N = Symbol.for("lit-noChange"), l = Symbol.for("lit-nothing"), Ce = /* @__PURE__ */ new WeakMap(), E = S.createTreeWalker(S, 129);
function je(s, e) {
  if (!pe(s) || !s.hasOwnProperty("raw")) throw Error("invalid template strings array");
  return we !== void 0 ? we.createHTML(e) : e;
}
const ct = (s, e) => {
  const t = s.length - 1, i = [];
  let r, o = e === 2 ? "<svg>" : e === 3 ? "<math>" : "", n = P;
  for (let a = 0; a < t; a++) {
    const c = s[a];
    let p, f, u = -1, v = 0;
    for (; v < c.length && (n.lastIndex = v, f = n.exec(c), f !== null); ) v = n.lastIndex, n === P ? f[1] === "!--" ? n = Ae : f[1] !== void 0 ? n = Ee : f[2] !== void 0 ? (He.test(f[2]) && (r = RegExp("</" + f[2], "g")), n = A) : f[3] !== void 0 && (n = A) : n === A ? f[0] === ">" ? (n = r ?? P, u = -1) : f[1] === void 0 ? u = -2 : (u = n.lastIndex - f[2].length, p = f[1], n = f[3] === void 0 ? A : f[3] === '"' ? ke : Se) : n === ke || n === Se ? n = A : n === Ae || n === Ee ? n = P : (n = A, r = void 0);
    const b = n === A && s[a + 1].startsWith("/>") ? " " : "";
    o += n === P ? c + ot : u >= 0 ? (i.push(p), c.slice(0, u) + Ue + c.slice(u) + $ + b) : c + $ + (u === -2 ? a : b);
  }
  return [je(s, o + (s[t] || "<?>") + (e === 2 ? "</svg>" : e === 3 ? "</math>" : "")), i];
};
class H {
  constructor({ strings: e, _$litType$: t }, i) {
    let r;
    this.parts = [];
    let o = 0, n = 0;
    const a = e.length - 1, c = this.parts, [p, f] = ct(e, t);
    if (this.el = H.createElement(p, i), E.currentNode = this.el.content, t === 2 || t === 3) {
      const u = this.el.content.firstChild;
      u.replaceWith(...u.childNodes);
    }
    for (; (r = E.nextNode()) !== null && c.length < a; ) {
      if (r.nodeType === 1) {
        if (r.hasAttributes()) for (const u of r.getAttributeNames()) if (u.endsWith(Ue)) {
          const v = f[n++], b = r.getAttribute(u).split($), G = /([.?@])?(.*)/.exec(v);
          c.push({ type: 1, index: o, name: G[2], strings: b, ctor: G[1] === "." ? dt : G[1] === "?" ? pt : G[1] === "@" ? ut : X }), r.removeAttribute(u);
        } else u.startsWith($) && (c.push({ type: 6, index: o }), r.removeAttribute(u));
        if (He.test(r.tagName)) {
          const u = r.textContent.split($), v = u.length - 1;
          if (v > 0) {
            r.textContent = Z ? Z.emptyScript : "";
            for (let b = 0; b < v; b++) r.append(u[b], U()), E.nextNode(), c.push({ type: 2, index: ++o });
            r.append(u[v], U());
          }
        }
      } else if (r.nodeType === 8) if (r.data === Le) c.push({ type: 2, index: o });
      else {
        let u = -1;
        for (; (u = r.data.indexOf($, u + 1)) !== -1; ) c.push({ type: 7, index: o }), u += $.length - 1;
      }
      o++;
    }
  }
  static createElement(e, t) {
    const i = S.createElement("template");
    return i.innerHTML = e, i;
  }
}
function q(s, e, t = s, i) {
  if (e === N) return e;
  let r = i !== void 0 ? t._$Co?.[i] : t._$Cl;
  const o = L(e) ? void 0 : e._$litDirective$;
  return r?.constructor !== o && (r?._$AO?.(!1), o === void 0 ? r = void 0 : (r = new o(s), r._$AT(s, t, i)), i !== void 0 ? (t._$Co ?? (t._$Co = []))[i] = r : t._$Cl = r), r !== void 0 && (e = q(s, r._$AS(s, e.values), r, i)), e;
}
class lt {
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
    const { el: { content: t }, parts: i } = this._$AD, r = (e?.creationScope ?? S).importNode(t, !0);
    E.currentNode = r;
    let o = E.nextNode(), n = 0, a = 0, c = i[0];
    for (; c !== void 0; ) {
      if (n === c.index) {
        let p;
        c.type === 2 ? p = new W(o, o.nextSibling, this, e) : c.type === 1 ? p = new c.ctor(o, c.name, c.strings, this, e) : c.type === 6 && (p = new ht(o, this, e)), this._$AV.push(p), c = i[++a];
      }
      n !== c?.index && (o = E.nextNode(), n++);
    }
    return E.currentNode = S, r;
  }
  p(e) {
    let t = 0;
    for (const i of this._$AV) i !== void 0 && (i.strings !== void 0 ? (i._$AI(e, i, t), t += i.strings.length - 2) : i._$AI(e[t])), t++;
  }
}
class W {
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
    e = q(this, e, t), L(e) ? e === l || e == null || e === "" ? (this._$AH !== l && this._$AR(), this._$AH = l) : e !== this._$AH && e !== N && this._(e) : e._$litType$ !== void 0 ? this.$(e) : e.nodeType !== void 0 ? this.T(e) : nt(e) ? this.k(e) : this._(e);
  }
  O(e) {
    return this._$AA.parentNode.insertBefore(e, this._$AB);
  }
  T(e) {
    this._$AH !== e && (this._$AR(), this._$AH = this.O(e));
  }
  _(e) {
    this._$AH !== l && L(this._$AH) ? this._$AA.nextSibling.data = e : this.T(S.createTextNode(e)), this._$AH = e;
  }
  $(e) {
    const { values: t, _$litType$: i } = e, r = typeof i == "number" ? this._$AC(e) : (i.el === void 0 && (i.el = H.createElement(je(i.h, i.h[0]), this.options)), i);
    if (this._$AH?._$AD === r) this._$AH.p(t);
    else {
      const o = new lt(r, this), n = o.u(this.options);
      o.p(t), this.T(n), this._$AH = o;
    }
  }
  _$AC(e) {
    let t = Ce.get(e.strings);
    return t === void 0 && Ce.set(e.strings, t = new H(e)), t;
  }
  k(e) {
    pe(this._$AH) || (this._$AH = [], this._$AR());
    const t = this._$AH;
    let i, r = 0;
    for (const o of e) r === t.length ? t.push(i = new W(this.O(U()), this.O(U()), this, this.options)) : i = t[r], i._$AI(o), r++;
    r < t.length && (this._$AR(i && i._$AB.nextSibling, r), t.length = r);
  }
  _$AR(e = this._$AA.nextSibling, t) {
    for (this._$AP?.(!1, !0, t); e !== this._$AB; ) {
      const i = xe(e).nextSibling;
      xe(e).remove(), e = i;
    }
  }
  setConnected(e) {
    this._$AM === void 0 && (this._$Cv = e, this._$AP?.(e));
  }
}
class X {
  get tagName() {
    return this.element.tagName;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  constructor(e, t, i, r, o) {
    this.type = 1, this._$AH = l, this._$AN = void 0, this.element = e, this.name = t, this._$AM = r, this.options = o, i.length > 2 || i[0] !== "" || i[1] !== "" ? (this._$AH = Array(i.length - 1).fill(new String()), this.strings = i) : this._$AH = l;
  }
  _$AI(e, t = this, i, r) {
    const o = this.strings;
    let n = !1;
    if (o === void 0) e = q(this, e, t, 0), n = !L(e) || e !== this._$AH && e !== N, n && (this._$AH = e);
    else {
      const a = e;
      let c, p;
      for (e = o[0], c = 0; c < o.length - 1; c++) p = q(this, a[i + c], t, c), p === N && (p = this._$AH[c]), n || (n = !L(p) || p !== this._$AH[c]), p === l ? e = l : e !== l && (e += (p ?? "") + o[c + 1]), this._$AH[c] = p;
    }
    n && !r && this.j(e);
  }
  j(e) {
    e === l ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, e ?? "");
  }
}
class dt extends X {
  constructor() {
    super(...arguments), this.type = 3;
  }
  j(e) {
    this.element[this.name] = e === l ? void 0 : e;
  }
}
class pt extends X {
  constructor() {
    super(...arguments), this.type = 4;
  }
  j(e) {
    this.element.toggleAttribute(this.name, !!e && e !== l);
  }
}
class ut extends X {
  constructor(e, t, i, r, o) {
    super(e, t, i, r, o), this.type = 5;
  }
  _$AI(e, t = this) {
    if ((e = q(this, e, t, 0) ?? l) === N) return;
    const i = this._$AH, r = e === l && i !== l || e.capture !== i.capture || e.once !== i.once || e.passive !== i.passive, o = e !== l && (i === l || r);
    r && this.element.removeEventListener(this.name, this, i), o && this.element.addEventListener(this.name, this, e), this._$AH = e;
  }
  handleEvent(e) {
    typeof this._$AH == "function" ? this._$AH.call(this.options?.host ?? this.element, e) : this._$AH.handleEvent(e);
  }
}
class ht {
  constructor(e, t, i) {
    this.element = e, this.type = 6, this._$AN = void 0, this._$AM = t, this.options = i;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AI(e) {
    q(this, e);
  }
}
const ft = I.litHtmlPolyfillSupport;
ft?.(H, W), (I.litHtmlVersions ?? (I.litHtmlVersions = [])).push("3.3.3");
const mt = (s, e, t) => {
  const i = t?.renderBefore ?? e;
  let r = i._$litPart$;
  if (r === void 0) {
    const o = t?.renderBefore ?? null;
    i._$litPart$ = r = new W(e.insertBefore(U(), o), o, void 0, t ?? {});
  }
  return r._$AI(s), r;
};
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const M = globalThis;
class y extends R {
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
    this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(e), this._$Do = mt(t, this.renderRoot, this.renderOptions);
  }
  connectedCallback() {
    super.connectedCallback(), this._$Do?.setConnected(!0);
  }
  disconnectedCallback() {
    super.disconnectedCallback(), this._$Do?.setConnected(!1);
  }
  render() {
    return N;
  }
}
y._$litElement$ = !0, y.finalized = !0, M.litElementHydrateSupport?.({ LitElement: y });
const gt = M.litElementPolyfillSupport;
gt?.({ LitElement: y });
(M.litElementVersions ?? (M.litElementVersions = [])).push("4.2.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const _t = { attribute: !0, type: String, converter: K, reflect: !1, hasChanged: de }, vt = (s = _t, e, t) => {
  const { kind: i, metadata: r } = t;
  let o = globalThis.litPropertyMetadata.get(r);
  if (o === void 0 && globalThis.litPropertyMetadata.set(r, o = /* @__PURE__ */ new Map()), i === "setter" && ((s = Object.create(s)).wrapped = !0), o.set(t.name, s), i === "accessor") {
    const { name: n } = t;
    return { set(a) {
      const c = e.get.call(this);
      e.set.call(this, a), this.requestUpdate(n, c, s, !0, a);
    }, init(a) {
      return a !== void 0 && this.C(n, void 0, s, a), a;
    } };
  }
  if (i === "setter") {
    const { name: n } = t;
    return function(a) {
      const c = this[n];
      e.call(this, a), this.requestUpdate(n, c, s, !0, a);
    };
  }
  throw Error("Unsupported decorator location: " + i);
};
function O(s) {
  return (e, t) => typeof t == "object" ? vt(s, e, t) : ((i, r, o) => {
    const n = r.hasOwnProperty(o);
    return r.constructor.createProperty(o, i), n ? Object.getOwnPropertyDescriptor(r, o) : void 0;
  })(s, e, t);
}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
function m(s) {
  return O({ ...s, state: !0, attribute: !1 });
}
const yt = V`
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
`, bt = V`
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
`, $t = V`
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
`, k = "—", xt = /* @__PURE__ */ new Set(["unavailable", "unknown", "none", ""]);
function w(s) {
  return s ? xt.has(s.state) : !0;
}
function J(s, e) {
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
  }, r = (o) => o.endsWith("_status") && !/_(ph|orp|free_chlorine|tac|cya|hardness|salt|tds)_status$/.test(o);
  if (e.device_id && s.entities) {
    for (const o of Object.values(s.entities))
      if (o.device_id === e.device_id)
        for (const [n, a] of Object.entries(i))
          t[n] || (n === "status" ? r(o.entity_id) && (t[n] = o.entity_id) : o.entity_id.endsWith(a) && (t[n] = o.entity_id));
  }
  return t;
}
function g(s, e) {
  if (e)
    return s.states[e];
}
function wt(s) {
  if (!s || w(s)) return "unknown";
  const e = s.state.toLowerCase();
  return e === "ok" || e === "warning" || e === "critical" ? e : "unknown";
}
const At = {
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
function Et(s) {
  return At[s];
}
const St = {
  temperature: { icon: "🌡️", label: "Temp", fractionDigits: 1, unitFallback: "°C" },
  ph: { icon: "⚗️", label: "pH", fractionDigits: 1, unitFallback: "" },
  free_chlorine: { icon: "🧪", label: "Cl", fractionDigits: 1, unitFallback: "mg/L" },
  orp: { icon: "⚡", label: "ORP", fractionDigits: 0, unitFallback: "mV" }
};
function kt(s) {
  return St[s];
}
function Ct(s, e, t) {
  if (w(s)) return k;
  const i = s.state, r = Number(i), o = s.attributes.unit_of_measurement ?? t;
  return Number.isFinite(r) ? `${r.toFixed(e)}${o ? ` ${o}` : ""}`.trim() : `${i}${o ? ` ${o}` : ""}`.trim();
}
function Tt(s, e, t) {
  if (s.metrics?.length) return s.metrics;
  const i = ["temperature", "ph", "free_chlorine"], r = g(t, e.free_chlorine);
  return w(r) && e.orp && !w(g(t, e.orp)) ? ["temperature", "ph", "orp"] : i;
}
function Rt(s) {
  return s >= 80 ? "good" : s >= 50 ? "warn" : "bad";
}
function Be(s) {
  if (!s) return { count: 0, list: [] };
  const e = Number(s.state), t = s.attributes.recommendations ?? [];
  return { count: Number.isFinite(e) ? e : t.length, list: t };
}
const Nt = {
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
function Q(s) {
  return Nt[s];
}
const ue = {
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
function Fe(s, e) {
  return e ? `${s} ${e}` : s;
}
function qt(s, e) {
  if (e === null || !Number.isFinite(e)) return k;
  if (s === null) return String(e);
  const t = ue[s];
  return t ? Fe(e.toFixed(t.fractionDigits), t.unit) : String(e);
}
function Ot(s, e) {
  if (!e || e.length !== 2) return k;
  const [t, i] = e;
  if (!Number.isFinite(t) || !Number.isFinite(i)) return k;
  if (s === null) return `${t}–${i}`;
  const r = ue[s];
  if (!r) return `${t}–${i}`;
  const o = t.toFixed(r.fractionDigits), n = i.toFixed(r.fractionDigits);
  return Fe(`${o}–${n}`, r.unit);
}
function Pt(s) {
  return s === null ? "" : ue[s]?.label ?? s;
}
function Te(s) {
  if (!s || w(s))
    return { count: 0, list: [], worst: "ok" };
  const e = s.attributes.problems ?? [], t = Number(s.state), i = Number.isFinite(t) ? t : e.length, o = s.attributes.worst_severity ?? e[0]?.severity ?? "ok";
  return { count: i, list: e, worst: o };
}
function Dt(s) {
  return s.treatments ?? s.actions ?? [];
}
const zt = {
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
function Ve(s) {
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
function It(s) {
  const e = Ve(s);
  return { key: e, ...zt[e] };
}
function Mt(s, e) {
  if (e.entity) return e.entity;
  if (!(!e.device_id || !s.entities)) {
    for (const t of Object.values(s.entities))
      if (t.device_id === e.device_id && t.entity_id.endsWith("_recommendations"))
        return t.entity_id;
  }
}
var Ut = Object.defineProperty, We = (s, e, t, i) => {
  for (var r = void 0, o = s.length - 1, n; o >= 0; o--)
    (n = s[o]) && (r = n(e, t, r) || r);
  return r && Ut(e, t, r), r;
};
const re = "poolman-pool-overview-card", he = class he extends y {
  /** Lovelace card size hint (1 unit ≈ 50px). */
  getCardSize() {
    return 3;
  }
  static getStubConfig() {
    return { type: `custom:${re}` };
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
    const e = J(this.hass, this._config), t = g(this.hass, e.status), i = wt(t), r = Et(i), o = this._config.name ?? this._deviceName(this._config.device_id) ?? "Pool", n = Tt(this._config, e, this.hass);
    return d`
      <ha-card>
        <div class="header">
          <div class="title">
            <span class="pool-icon" aria-hidden="true">🏊</span>
            <span>${o}</span>
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
          ${n.map((a) => this._renderMetric(a, e))}
        </div>

        ${this._config.show_score !== !1 ? this._renderScore(e.water_quality_score) : l}
        ${this._renderRecommendations(e.recommendations)}
      </ha-card>
    `;
  }
  _renderMetric(e, t) {
    const i = kt(e), r = g(this.hass, t[e]), o = Ct(r, i.fractionDigits, i.unitFallback);
    return d`
      <div class="metric" data-key=${e}>
        <span class="metric-label">
          <span aria-hidden="true">${i.icon}</span>
          ${i.label}
        </span>
        <span class="metric-value">${o}</span>
      </div>
    `;
  }
  _renderScore(e) {
    const t = g(this.hass, e);
    if (w(t))
      return d`
        <div class="score">
          <div class="score-row">
            <span>Quality score</span>
            <strong>${k}</strong>
          </div>
        </div>
      `;
    const i = Math.max(0, Math.min(100, Number(t.state) || 0)), r = Rt(i);
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
    const t = g(this.hass, e);
    if (!t) return l;
    const { count: i } = Be(t), r = this._config?.recommendations_path, o = i > 0, n = i === 0 ? "Your pool is in good condition" : `${i} recommendation${i === 1 ? "" : "s"}`;
    return d`
      <div
        class="recommendations"
        role=${o ? "button" : "presentation"}
        tabindex=${o ? "0" : "-1"}
        ?disabled=${!o}
        @click=${() => o && this._openRecommendations(t.entity_id, r)}
        @keydown=${(c) => {
      o && (c.key === "Enter" || c.key === " ") && (c.preventDefault(), this._openRecommendations(t.entity_id, r));
    }}
      >
        <span class="label">
          <span aria-hidden="true">${i === 0 ? "✅" : "⚠️"}</span>
          ${n}
        </span>
        ${o ? d`<span class="chevron" aria-hidden="true">›</span>` : l}
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
he.styles = yt;
let j = he;
We([
  O({ attribute: !1 })
], j.prototype, "hass");
We([
  m()
], j.prototype, "_config");
customElements.get(re) || customElements.define(re, j);
const Lt = V`
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
var Ht = Object.defineProperty, Ge = (s, e, t, i) => {
  for (var r = void 0, o = s.length - 1, n; o >= 0; o--)
    (n = s[o]) && (r = n(e, t, r) || r);
  return r && Ht(e, t, r), r;
};
const se = "poolman-problem-card", Re = {
  ok: {
    label: "OK",
    color: "var(--success-color, #43a047)",
    icon: "✅"
  },
  low: Q("low"),
  medium: Q("medium"),
  critical: Q("critical")
}, fe = class fe extends y {
  /** Lovelace card size hint (1 unit ≈ 50px). */
  getCardSize() {
    const e = this._resolveEntity();
    if (!e) return 1;
    const { count: t } = Te(e);
    if (t === 0) return 1;
    const i = this._config?.max ?? t;
    return 1 + Math.min(t, i);
  }
  static getStubConfig() {
    return { type: `custom:${se}` };
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
    if (!e || w(e))
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
    const { count: i, list: r, worst: o } = Te(e), n = Re[o] ?? Re.ok;
    return d`
      <ha-card>
        <div class="header">
          <div class="title">
            <span class="icon" aria-hidden="true">🩺</span>
            <span>${t}</span>
          </div>
          <span
            class="badge"
            style=${`background:${n.color}`}
            role="status"
            aria-label=${`Worst severity: ${n.label}`}
          >
            <span class="dot" aria-hidden="true"></span>
            ${n.label}
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
    const i = this._config?.max, r = i !== void 0 ? e.slice(0, i) : e, o = Math.max(0, t - r.length);
    return d`
      <div class="problems">
        ${r.map((n) => this._renderProblem(n))}
        ${o > 0 ? d`<div class="more">
              +${o} more problem${o === 1 ? "" : "s"}
            </div>` : l}
      </div>
    `;
  }
  _renderProblem(e) {
    const t = e.severity, i = Q(t), r = Pt(e.metric), o = e.metric !== null && e.value !== null && e.expected_range !== null;
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
        ${o ? d`
              <div class="details">
                ${r ? d`<span class="metric-label">${r}</span>
                      <span class="sep" aria-hidden="true">•</span>` : l}
                <span>
                  Current:
                  <strong>${qt(e.metric, e.value)}</strong>
                </span>
                <span class="sep" aria-hidden="true">—</span>
                <span>
                  Expected:
                  <strong
                    >${Ot(e.metric, e.expected_range)}</strong
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
      return g(this.hass, this._config.entity);
    const e = J(this.hass, {
      type: this._config.type,
      device_id: this._config.device_id
    });
    return g(this.hass, e.problems);
  }
  _deviceName() {
    const e = this._config?.device_id;
    if (!e || !this.hass?.devices) return;
    const t = this.hass.devices[e];
    if (t)
      return t.name_by_user ?? t.name ?? void 0;
  }
};
fe.styles = Lt;
let B = fe;
Ge([
  O({ attribute: !1 })
], B.prototype, "hass");
Ge([
  m()
], B.prototype, "_config");
customElements.get(se) || customElements.define(se, B);
var jt = Object.defineProperty, ee = (s, e, t, i) => {
  for (var r = void 0, o = s.length - 1, n; o >= 0; o--)
    (n = s[o]) && (r = n(e, t, r) || r);
  return r && jt(e, t, r), r;
};
const oe = "poolman-recommendations-card", me = class me extends y {
  constructor() {
    super(...arguments), this._dismissed = /* @__PURE__ */ new Set(), this._expanded = /* @__PURE__ */ new Set(), this._lastSeenIds = /* @__PURE__ */ new Set();
  }
  /** Lovelace card size hint (1 unit ≈ 50px). */
  getCardSize() {
    return 4;
  }
  static getStubConfig() {
    return { type: `custom:${oe}` };
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
    const e = Mt(this.hass, this._config), t = g(this.hass, e), i = this._config.name ?? this._deviceName() ?? "Recommendations";
    if (!t || w(t))
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
    const { count: r, list: o } = Be(t);
    this._lastSeenIds = new Set(o.map((a) => a.id));
    const n = o.filter((a) => !this._dismissed.has(a.id));
    return d`
      <ha-card>
        <div class="header">
          <div class="title">
            <span class="icon" aria-hidden="true">📋</span>
            <span>${i}</span>
          </div>
          ${r > 0 ? d`<span class="count">${n.length} / ${r}</span>` : l}
        </div>

        ${n.length === 0 ? this._renderEmpty() : d`<div class="list">${n.map((a) => this._renderRecommendation(a))}</div>`}
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
    const t = It(e), i = this._expanded.has(e.id), r = this._config?.show_severity !== !1, o = Dt(e);
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
          @keydown=${(n) => {
      (n.key === "Enter" || n.key === " ") && (n.preventDefault(), this._toggle(e.id));
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
        ${i ? this._renderDetail(e, o) : l}
        <div class="rec-actions">
          <button
            class="btn ignore"
            type="button"
            @click=${(n) => {
      n.stopPropagation(), this._ignore(e.id);
    }}
          >
            Ignore
          </button>
          <button
            class="btn apply"
            type="button"
            @click=${(n) => {
      n.stopPropagation(), this._apply(e);
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
    const i = Ve(e);
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
me.styles = bt;
let C = me;
ee([
  O({ attribute: !1 })
], C.prototype, "hass");
ee([
  m()
], C.prototype, "_config");
ee([
  m()
], C.prototype, "_dismissed");
ee([
  m()
], C.prototype, "_expanded");
customElements.get(oe) || customElements.define(oe, C);
var Bt = Object.defineProperty, Ye = (s, e, t, i) => {
  for (var r = void 0, o = s.length - 1, n; o >= 0; o--)
    (n = s[o]) && (r = n(e, t, r) || r);
  return r && Bt(e, t, r), r;
};
const ne = "poolman-action-history-card", ie = 50, Ft = {
  chemical: "🧪",
  cleaning: "🧹",
  maintenance: "🔧"
}, Vt = {
  chemical: "Chemical treatment",
  cleaning: "Cleaning",
  maintenance: "Maintenance"
}, Wt = {
  user: "Manual",
  recommendation: "Recommendation",
  automation: "Automation"
};
function Gt(s) {
  if (s.type !== "chemical" || !Number.isFinite(s.quantity)) return k;
  const e = Number.isInteger(s.quantity) ? s.quantity.toString() : s.quantity.toFixed(1);
  return s.unit ? `${e} ${s.unit}` : e;
}
function D(s) {
  return `${s.getFullYear()}-${String(s.getMonth() + 1).padStart(2, "0")}-${String(
    s.getDate()
  ).padStart(2, "0")}`;
}
const ge = class ge extends y {
  /** Lovelace card size hint (1 unit ≈ 50px). */
  getCardSize() {
    return 4;
  }
  static getStubConfig() {
    return { type: `custom:${ne}` };
  }
  setConfig(e) {
    if (!e)
      throw new Error("Invalid configuration");
    if (!e.device_id && !e.entities?.action_history)
      throw new Error(
        "poolman-action-history-card: either `device_id` or `entities.action_history` must be provided"
      );
    const t = e.limit, i = typeof t == "number" && t > 0 ? Math.min(Math.floor(t), ie) : ie;
    this._config = {
      show_source: !0,
      group_by_day: !0,
      ...e,
      limit: i
    };
  }
  render() {
    if (!this._config || !this.hass) return l;
    const t = J(this.hass, this._config).action_history, i = g(this.hass, t), r = this._readActions(i), o = this._config.name ?? this._deviceName(this._config.device_id) ?? "Pool";
    return d`
      <ha-card>
        <div class="header">
          <div class="title">
            <span class="header-icon" aria-hidden="true">📋</span>
            <span>${o} — Action history</span>
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
    const i = this._config?.limit ?? ie;
    return t.filter((r) => r && typeof r.timestamp == "string").slice().sort((r, o) => r.timestamp < o.timestamp ? 1 : -1).slice(0, i);
  }
  _renderTimeline(e) {
    if (!(this._config?.group_by_day !== !1))
      return e.map((o) => this._renderRow(o));
    const i = [];
    let r;
    for (const o of e) {
      const n = new Date(o.timestamp), a = D(n);
      a !== r && (r = a, i.push(
        d`<div class="day-header">${this._formatDayHeader(n)}</div>`
      )), i.push(this._renderRow(o));
    }
    return i;
  }
  _renderRow(e) {
    const t = Ft[e.type] ?? "•", i = Vt[e.type] ?? e.type, r = Wt[e.source] ?? e.source, o = Gt(e), n = !!e.recommendation_id, a = this._formatTime(new Date(e.timestamp)), c = () => this._openAction(e);
    return d`
      <div
        class="action-row ${n ? "interactive" : ""}"
        data-type=${e.type}
        data-source=${e.source}
        role=${n ? "button" : "presentation"}
        tabindex=${n ? "0" : "-1"}
        @click=${n ? c : l}
        @keydown=${n ? (p) => {
      (p.key === "Enter" || p.key === " ") && (p.preventDefault(), c());
    } : l}
      >
        <span class="action-icon" aria-hidden="true">${t}</span>
        <div class="action-body">
          <span class="action-title">
            ${i}${e.treatment_id ? d` · ${e.treatment_id}` : l}
          </span>
          <span class="action-meta">
            <span class="quantity">${o}</span>
            ${this._config?.show_source !== !1 ? d`<span class="source-badge ${e.source}">${r}</span>` : l}
          </span>
        </div>
        <span class="action-time">${a}</span>
      </div>
    `;
  }
  _openAction(e) {
    const t = J(this.hass, this._config), i = t.recommendations ?? t.action_history;
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
    if (i.setDate(t.getDate() - 1), D(e) === D(t)) return "Today";
    if (D(e) === D(i)) return "Yesterday";
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
ge.styles = $t;
let F = ge;
Ye([
  O({ attribute: !1 })
], F.prototype, "hass");
Ye([
  m()
], F.prototype, "_config");
customElements.get(ne) || customElements.define(ne, F);
const Yt = V`
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
    font-size: 1.05rem;
    font-weight: 600;
  }

  .buttons {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 8px;
  }

  .qa-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    min-height: 48px;
    padding: 10px 12px;
    border: 1px solid var(--divider-color, rgba(0, 0, 0, 0.12));
    border-radius: 12px;
    background: var(--card-background-color, #fff);
    color: var(--primary-text-color, #212121);
    font: inherit;
    font-weight: 500;
    cursor: pointer;
    transition:
      transform 120ms ease,
      background-color 200ms ease,
      border-color 200ms ease,
      color 200ms ease;
  }

  .qa-btn:focus-visible {
    outline: 2px solid var(--primary-color, #03a9f4);
    outline-offset: 2px;
  }

  .qa-btn:hover:not(:disabled) {
    border-color: var(--primary-color, #03a9f4);
  }

  .qa-btn:active:not(:disabled) {
    transform: scale(0.98);
  }

  .qa-btn:disabled {
    cursor: progress;
    opacity: 0.85;
  }

  .qa-btn[data-state="success"] {
    background: var(--success-color, #43a047);
    border-color: var(--success-color, #43a047);
    color: #fff;
    animation: qa-pop 250ms ease;
  }

  .qa-btn[data-state="error"] {
    background: var(--error-color, #d32f2f);
    border-color: var(--error-color, #d32f2f);
    color: #fff;
  }

  .qa-btn[data-state="pending"] {
    color: var(--secondary-text-color, #6c6c6c);
  }

  .qa-icon {
    font-size: 1.15rem;
    line-height: 1;
  }

  .qa-spinner {
    width: 16px;
    height: 16px;
    border-radius: 50%;
    border: 2px solid currentColor;
    border-right-color: transparent;
    animation: qa-spin 800ms linear infinite;
  }

  .qa-error-message {
    grid-column: 1 / -1;
    font-size: 0.85rem;
    color: var(--error-color, #d32f2f);
    background: color-mix(in srgb, var(--error-color, #d32f2f) 12%, transparent);
    padding: 8px 10px;
    border-radius: 8px;
  }

  .qa-notice {
    font-size: 0.85rem;
    color: var(--warning-color, #ffa000);
  }

  /* Dialog overlay (lives inside the shadow root). */
  .qa-dialog-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.4);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 16px;
    z-index: 99;
  }

  .qa-dialog {
    background: var(--card-background-color, #fff);
    color: var(--primary-text-color, #212121);
    border-radius: 14px;
    padding: 20px;
    width: min(420px, 100%);
    max-height: 90vh;
    overflow: auto;
    display: flex;
    flex-direction: column;
    gap: 12px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
  }

  .qa-dialog h2 {
    margin: 0;
    font-size: 1.1rem;
  }

  .qa-field {
    display: flex;
    flex-direction: column;
    gap: 4px;
    font-size: 0.9rem;
  }

  .qa-field label {
    color: var(--secondary-text-color, #6c6c6c);
  }

  .qa-field input,
  .qa-field select,
  .qa-field textarea {
    font: inherit;
    color: inherit;
    background: var(--card-background-color, #fff);
    border: 1px solid var(--divider-color, rgba(0, 0, 0, 0.2));
    border-radius: 8px;
    padding: 8px 10px;
    min-height: 40px;
  }

  .qa-field textarea {
    min-height: 72px;
    resize: vertical;
  }

  .qa-dialog-actions {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
    margin-top: 4px;
  }

  .qa-dialog-actions button {
    min-height: 40px;
    padding: 8px 16px;
    border-radius: 8px;
    border: 1px solid var(--divider-color, rgba(0, 0, 0, 0.2));
    background: var(--card-background-color, #fff);
    color: inherit;
    font: inherit;
    font-weight: 500;
    cursor: pointer;
  }

  .qa-dialog-actions button.primary {
    background: var(--primary-color, #03a9f4);
    border-color: var(--primary-color, #03a9f4);
    color: var(--text-primary-color, #fff);
  }

  .qa-dialog-actions button:disabled {
    opacity: 0.6;
    cursor: progress;
  }

  .qa-validation {
    font-size: 0.85rem;
    color: var(--error-color, #d32f2f);
  }

  @keyframes qa-spin {
    to {
      transform: rotate(360deg);
    }
  }

  @keyframes qa-pop {
    0% {
      transform: scale(1);
    }
    40% {
      transform: scale(1.04);
    }
    100% {
      transform: scale(1);
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .qa-btn,
    .qa-btn[data-state="success"],
    .qa-spinner {
      animation: none;
      transition: none;
    }
  }
`, Qt = {
  card_name: "Quick Actions",
  card_description: "One-tap buttons to trigger a pool analysis, boost filtration or record a treatment.",
  analyze: "Analyze now",
  analyze_aria: "Trigger an immediate pool analysis",
  boost_2h: "+2 h",
  boost_4h: "+4 h",
  boost_aria: "Boost filtration",
  record: "Record treatment",
  record_aria: "Record a manual pool action",
  pending: "Working…",
  success: "Done",
  error_generic: "Service call failed",
  service_unavailable: "Service calls unavailable",
  dialog_title: "Record treatment",
  dialog_type: "Type",
  dialog_type_chemical: "Chemical",
  dialog_type_cleaning: "Cleaning",
  dialog_type_maintenance: "Maintenance",
  dialog_product_id: "Product ID",
  dialog_quantity: "Quantity",
  dialog_unit: "Unit",
  dialog_unit_none: "—",
  dialog_note: "Note",
  dialog_submit: "Record",
  dialog_cancel: "Cancel",
  dialog_validation_quantity: "Quantity must be a positive number"
}, Kt = {
  card_name: "Actions rapides",
  card_description: "Boutons en un tap pour déclencher une analyse, booster la filtration ou enregistrer un traitement.",
  analyze: "Analyser",
  analyze_aria: "Déclencher une analyse immédiate",
  boost_2h: "+2 h",
  boost_4h: "+4 h",
  boost_aria: "Booster la filtration",
  record: "Enregistrer un traitement",
  record_aria: "Enregistrer une action manuelle",
  pending: "En cours…",
  success: "Fait",
  error_generic: "Échec de l'appel du service",
  service_unavailable: "Appels de service indisponibles",
  dialog_title: "Enregistrer un traitement",
  dialog_type: "Type",
  dialog_type_chemical: "Produit chimique",
  dialog_type_cleaning: "Nettoyage",
  dialog_type_maintenance: "Maintenance",
  dialog_product_id: "Identifiant produit",
  dialog_quantity: "Quantité",
  dialog_unit: "Unité",
  dialog_unit_none: "—",
  dialog_note: "Note",
  dialog_submit: "Enregistrer",
  dialog_cancel: "Annuler",
  dialog_validation_quantity: "La quantité doit être un nombre positif"
}, Ne = { en: Qt, fr: Kt };
function Zt(s) {
  return s && s.toLowerCase().replace("_", "-").split("-")[0] === "fr" ? "fr" : "en";
}
function h(s, e) {
  const t = Zt(s);
  return Ne[t][e] ?? Ne.en[e] ?? e;
}
const Jt = ["g", "kg", "mL", "L", "tablet"];
var Xt = Object.defineProperty, T = (s, e, t, i) => {
  for (var r = void 0, o = s.length - 1, n; o >= 0; o--)
    (n = s[o]) && (r = n(e, t, r) || r);
  return r && Xt(e, t, r), r;
};
const ae = "poolman-quick-actions-card", ei = "poolman", ti = "analyze", ii = "boost_filtration", ri = "record_action", si = 1500, oi = 3e3, qe = {
  type: "chemical",
  product_id: "",
  quantity: "",
  unit: "",
  note: ""
}, _e = class _e extends y {
  constructor() {
    super(...arguments), this._states = {}, this._errors = {}, this._dialogOpen = !1, this._draft = { ...qe }, this._validationError = "", this._resetTimers = {};
  }
  disconnectedCallback() {
    super.disconnectedCallback();
    for (const e of Object.keys(this._resetTimers)) {
      const t = this._resetTimers[e];
      t && clearTimeout(t);
    }
    this._resetTimers = {};
  }
  /** Lovelace card size hint (1 unit ≈ 50px). */
  getCardSize() {
    return 2;
  }
  static getStubConfig(e) {
    const t = e?.devices ? Object.keys(e.devices)[0] : void 0;
    return {
      type: `custom:${ae}`,
      device_id: t ?? ""
    };
  }
  setConfig(e) {
    if (!e)
      throw new Error("Invalid configuration");
    if (!e.device_id)
      throw new Error(
        "poolman-quick-actions-card: `device_id` is required"
      );
    this._config = {
      analyze: !0,
      boost: !0,
      record: !0,
      ...e
    };
  }
  render() {
    if (!this._config || !this.hass) return l;
    const e = this.hass.locale?.language, t = this._config.name ?? this._deviceName(this._config.device_id) ?? h(e, "card_name"), i = typeof this.hass.callService == "function";
    return d`
      <ha-card>
        <div class="header">${t}</div>
        ${i ? l : d`<div class="qa-notice" role="status">
              ${h(e, "service_unavailable")}
            </div>`}
        <div class="buttons">
          ${this._config.analyze !== !1 ? this._renderButton(
      "analyze",
      "🔍",
      "analyze",
      "analyze_aria",
      () => this._invokeAnalyze()
    ) : l}
          ${this._config.boost !== !1 ? [
      this._renderButton(
        "boost_2h",
        "⏱",
        "boost_2h",
        "boost_aria",
        () => this._invokeBoost(2, "boost_2h")
      ),
      this._renderButton(
        "boost_4h",
        "⏱",
        "boost_4h",
        "boost_aria",
        () => this._invokeBoost(4, "boost_4h")
      )
    ] : l}
          ${this._config.record !== !1 ? this._renderButton(
      "record",
      "🧪",
      "record",
      "record_aria",
      () => this._openDialog()
    ) : l}
          ${this._renderErrors()}
        </div>
        ${this._dialogOpen ? this._renderDialog() : l}
      </ha-card>
    `;
  }
  // ---- button rendering ----------------------------------------------------
  _renderButton(e, t, i, r, o) {
    const n = this.hass?.locale?.language, a = this._states[e] ?? "idle", c = a === "pending" || typeof this.hass?.callService != "function", p = a === "pending" ? h(n, "pending") : a === "success" ? h(n, "success") : h(n, i);
    return d`
      <button
        type="button"
        class="qa-btn"
        data-action=${e}
        data-state=${a}
        aria-label=${h(n, r)}
        ?disabled=${c}
        @click=${o}
      >
        ${a === "pending" ? d`<span class="qa-spinner" aria-hidden="true"></span>` : d`<span class="qa-icon" aria-hidden="true">${t}</span>`}
        <span class="qa-label">${p}</span>
      </button>
    `;
  }
  _renderErrors() {
    const e = Object.entries(this._errors).filter(
      ([, t]) => !!t
    );
    return e.length === 0 ? l : e.map(
      ([t, i]) => d`
        <div class="qa-error-message" role="alert" data-action=${t}>
          ${i}
        </div>
      `
    );
  }
  // ---- dialog rendering ----------------------------------------------------
  _renderDialog() {
    const e = this.hass?.locale?.language, t = this._states.record === "pending";
    return d`
      <div
        class="qa-dialog-backdrop"
        role="presentation"
        @click=${(i) => {
      i.target === i.currentTarget && !t && this._closeDialog();
    }}
      >
        <div
          class="qa-dialog"
          role="dialog"
          aria-modal="true"
          aria-label=${h(e, "dialog_title")}
        >
          <h2>${h(e, "dialog_title")}</h2>

          <div class="qa-field">
            <label for="qa-type">${h(e, "dialog_type")}</label>
            <select
              id="qa-type"
              .value=${this._draft.type}
              @change=${(i) => this._updateDraft({
      type: i.target.value
    })}
            >
              <option value="chemical">
                ${h(e, "dialog_type_chemical")}
              </option>
              <option value="cleaning">
                ${h(e, "dialog_type_cleaning")}
              </option>
              <option value="maintenance">
                ${h(e, "dialog_type_maintenance")}
              </option>
            </select>
          </div>

          <div class="qa-field">
            <label for="qa-product">${h(e, "dialog_product_id")}</label>
            <input
              id="qa-product"
              type="text"
              .value=${this._draft.product_id}
              @input=${(i) => this._updateDraft({
      product_id: i.target.value
    })}
            />
          </div>

          <div class="qa-field">
            <label for="qa-quantity">${h(e, "dialog_quantity")}</label>
            <input
              id="qa-quantity"
              type="number"
              min="0"
              step="any"
              inputmode="decimal"
              .value=${this._draft.quantity}
              @input=${(i) => this._updateDraft({
      quantity: i.target.value
    })}
            />
          </div>

          <div class="qa-field">
            <label for="qa-unit">${h(e, "dialog_unit")}</label>
            <select
              id="qa-unit"
              .value=${this._draft.unit}
              @change=${(i) => this._updateDraft({
      unit: i.target.value
    })}
            >
              <option value="">${h(e, "dialog_unit_none")}</option>
              ${Jt.map(
      (i) => d`<option value=${i}>${i}</option>`
    )}
            </select>
          </div>

          <div class="qa-field">
            <label for="qa-note">${h(e, "dialog_note")}</label>
            <textarea
              id="qa-note"
              .value=${this._draft.note}
              @input=${(i) => this._updateDraft({
      note: i.target.value
    })}
            ></textarea>
          </div>

          ${this._validationError ? d`<div class="qa-validation" role="alert">
                ${this._validationError}
              </div>` : l}

          <div class="qa-dialog-actions">
            <button
              type="button"
              ?disabled=${t}
              @click=${() => this._closeDialog()}
            >
              ${h(e, "dialog_cancel")}
            </button>
            <button
              type="button"
              class="primary"
              ?disabled=${t}
              @click=${() => this._submitDialog()}
            >
              ${h(e, "dialog_submit")}
            </button>
          </div>
        </div>
      </div>
    `;
  }
  // ---- service calls -------------------------------------------------------
  async _invokeAnalyze() {
    const e = this._config?.device_id;
    e && await this._runService("analyze", ti, { device_id: e });
  }
  async _invokeBoost(e, t) {
    const i = this._config?.device_id;
    i && await this._runService(t, ii, { device_id: i, hours: e });
  }
  async _runService(e, t, i) {
    const r = this.hass?.callService;
    if (typeof r != "function") return !1;
    this._clearError(e), this._setState(e, "pending");
    try {
      return await r(ei, t, i), this._setState(e, "success"), this._scheduleReset(e, si), !0;
    } catch (o) {
      const n = this.hass?.locale?.language, a = o instanceof Error && o.message ? o.message : h(n, "error_generic");
      return this._setError(e, a), this._setState(e, "error"), this._scheduleReset(e, oi), !1;
    }
  }
  // ---- dialog state --------------------------------------------------------
  _openDialog() {
    this._draft = { ...qe }, this._validationError = "", this._clearError("record"), this._dialogOpen = !0;
  }
  _closeDialog() {
    this._dialogOpen = !1, this._validationError = "";
  }
  _updateDraft(e) {
    this._draft = { ...this._draft, ...e }, this._validationError && (this._validationError = "");
  }
  async _submitDialog() {
    const e = this.hass?.locale?.language, t = this._config?.device_id;
    if (!t) return;
    const i = {
      device_id: t,
      type: this._draft.type
    }, r = this._draft.product_id.trim();
    r && (i.product_id = r);
    const o = this._draft.quantity.trim();
    if (o !== "") {
      const p = Number(o);
      if (!Number.isFinite(p) || p < 0) {
        this._validationError = h(e, "dialog_validation_quantity");
        return;
      }
      i.quantity = p;
    }
    const n = this._draft.unit.trim();
    n && r && (i.unit = n);
    const a = this._draft.note.trim();
    a && (i.note = a), await this._runService("record", ri, i) && this._closeDialog();
  }
  // ---- helpers -------------------------------------------------------------
  _setState(e, t) {
    this._states = { ...this._states, [e]: t };
  }
  _setError(e, t) {
    this._errors = { ...this._errors, [e]: t };
  }
  _clearError(e) {
    if (!this._errors[e]) return;
    const t = { ...this._errors };
    delete t[e], this._errors = t;
  }
  _scheduleReset(e, t) {
    const i = this._resetTimers[e];
    i && clearTimeout(i), this._resetTimers[e] = setTimeout(() => {
      this._setState(e, "idle"), this._clearError(e), delete this._resetTimers[e];
    }, t);
  }
  _deviceName(e) {
    if (!e || !this.hass?.devices) return;
    const t = this.hass.devices[e];
    if (t)
      return t.name_by_user ?? t.name ?? void 0;
  }
};
_e.styles = Yt;
let _ = _e;
T([
  O({ attribute: !1 })
], _.prototype, "hass");
T([
  m()
], _.prototype, "_config");
T([
  m()
], _.prototype, "_states");
T([
  m()
], _.prototype, "_errors");
T([
  m()
], _.prototype, "_dialogOpen");
T([
  m()
], _.prototype, "_draft");
T([
  m()
], _.prototype, "_validationError");
customElements.get(ae) || customElements.define(ae, _);
const Oe = "poolman-pool-overview-card", Pe = "poolman-problem-card", De = "poolman-recommendations-card", ze = "poolman-action-history-card", Ie = "poolman-quick-actions-card", ni = "0.1.0";
window.customCards = window.customCards ?? [];
window.customCards.some((s) => s.type === Oe) || window.customCards.push({
  type: Oe,
  name: "Pool Overview",
  description: "Glanceable summary card for a Pool Manager pool: status badge, key chemistry metrics, water quality score and recommendation count.",
  preview: !0,
  documentationURL: "https://noirbizarre.github.io/hass-poolman/pool-overview-card/"
});
window.customCards.some((s) => s.type === Pe) || window.customCards.push({
  type: Pe,
  name: "Pool Problems",
  description: "Diagnostic card listing the current pool problems by severity, with measured value and expected range.",
  preview: !0,
  documentationURL: "https://noirbizarre.github.io/hass-poolman/problem-card/"
});
window.customCards.some((s) => s.type === De) || window.customCards.push({
  type: De,
  name: "Pool Recommendations",
  description: "Actionable pool recommendation list: severity badges, expandable details, and one-tap Apply / Ignore buttons backed by the poolman.apply_recommendation service.",
  preview: !0,
  documentationURL: "https://noirbizarre.github.io/hass-poolman/recommendations-card/"
});
window.customCards.some((s) => s.type === ze) || window.customCards.push({
  type: ze,
  name: "Pool Action History",
  description: "Chronological timeline of recorded pool actions (chemical treatments, cleaning, maintenance) with source badges.",
  preview: !0,
  documentationURL: "https://noirbizarre.github.io/hass-poolman/action-history-card/"
});
window.customCards.some((s) => s.type === Ie) || window.customCards.push({
  type: Ie,
  name: "Pool Quick Actions",
  description: "One-tap access to common pool operations: trigger analysis, boost filtration and record a treatment.",
  preview: !0,
  documentationURL: "https://noirbizarre.github.io/hass-poolman/quick-actions-card/"
});
console.info(
  `%c POOLMAN-CARDS %c v${ni} `,
  "color: white; background: #03a9f4; font-weight: 700;",
  "color: #03a9f4; background: transparent; font-weight: 700;"
);
//# sourceMappingURL=poolman-pool-overview-card.js.map
