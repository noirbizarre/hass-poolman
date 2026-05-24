/**
 * @license
 * Copyright 2019 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const j = globalThis, J = j.ShadowRoot && (j.ShadyCSS === void 0 || j.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype, X = Symbol(), ae = /* @__PURE__ */ new WeakMap();
let we = class {
  constructor(e, t, i) {
    if (this._$cssResult$ = !0, i !== X) throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
    this.cssText = e, this.t = t;
  }
  get styleSheet() {
    let e = this.o;
    const t = this.t;
    if (J && e === void 0) {
      const i = t !== void 0 && t.length === 1;
      i && (e = ae.get(t)), e === void 0 && ((this.o = e = new CSSStyleSheet()).replaceSync(this.cssText), i && ae.set(t, e));
    }
    return e;
  }
  toString() {
    return this.cssText;
  }
};
const Me = (r) => new we(typeof r == "string" ? r : r + "", void 0, X), ee = (r, ...e) => {
  const t = r.length === 1 ? r[0] : e.reduce((i, s, n) => i + ((o) => {
    if (o._$cssResult$ === !0) return o.cssText;
    if (typeof o == "number") return o;
    throw Error("Value passed to 'css' function must be a 'css' function result: " + o + ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.");
  })(s) + r[n + 1], r[0]);
  return new we(t, r, X);
}, Ue = (r, e) => {
  if (J) r.adoptedStyleSheets = e.map((t) => t instanceof CSSStyleSheet ? t : t.styleSheet);
  else for (const t of e) {
    const i = document.createElement("style"), s = j.litNonce;
    s !== void 0 && i.setAttribute("nonce", s), i.textContent = t.cssText, r.appendChild(i);
  }
}, ce = J ? (r) => r : (r) => r instanceof CSSStyleSheet ? ((e) => {
  let t = "";
  for (const i of e.cssRules) t += i.cssText;
  return Me(t);
})(r) : r;
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const { is: ze, defineProperty: De, getOwnPropertyDescriptor: Ie, getOwnPropertyNames: He, getOwnPropertySymbols: Le, getPrototypeOf: je } = Object, _ = globalThis, le = _.trustedTypes, Fe = le ? le.emptyScript : "", We = _.reactiveElementPolyfillSupport, P = (r, e) => r, W = { toAttribute(r, e) {
  switch (e) {
    case Boolean:
      r = r ? Fe : null;
      break;
    case Object:
    case Array:
      r = r == null ? r : JSON.stringify(r);
  }
  return r;
}, fromAttribute(r, e) {
  let t = r;
  switch (e) {
    case Boolean:
      t = r !== null;
      break;
    case Number:
      t = r === null ? null : Number(r);
      break;
    case Object:
    case Array:
      try {
        t = JSON.parse(r);
      } catch {
        t = null;
      }
  }
  return t;
} }, te = (r, e) => !ze(r, e), de = { attribute: !0, type: String, converter: W, reflect: !1, useDefault: !1, hasChanged: te };
Symbol.metadata ?? (Symbol.metadata = Symbol("metadata")), _.litPropertyMetadata ?? (_.litPropertyMetadata = /* @__PURE__ */ new WeakMap());
let E = class extends HTMLElement {
  static addInitializer(e) {
    this._$Ei(), (this.l ?? (this.l = [])).push(e);
  }
  static get observedAttributes() {
    return this.finalize(), this._$Eh && [...this._$Eh.keys()];
  }
  static createProperty(e, t = de) {
    if (t.state && (t.attribute = !1), this._$Ei(), this.prototype.hasOwnProperty(e) && ((t = Object.create(t)).wrapped = !0), this.elementProperties.set(e, t), !t.noAccessor) {
      const i = Symbol(), s = this.getPropertyDescriptor(e, i, t);
      s !== void 0 && De(this.prototype, e, s);
    }
  }
  static getPropertyDescriptor(e, t, i) {
    const { get: s, set: n } = Ie(this.prototype, e) ?? { get() {
      return this[t];
    }, set(o) {
      this[t] = o;
    } };
    return { get: s, set(o) {
      const c = s?.call(this);
      n?.call(this, o), this.requestUpdate(e, c, i);
    }, configurable: !0, enumerable: !0 };
  }
  static getPropertyOptions(e) {
    return this.elementProperties.get(e) ?? de;
  }
  static _$Ei() {
    if (this.hasOwnProperty(P("elementProperties"))) return;
    const e = je(this);
    e.finalize(), e.l !== void 0 && (this.l = [...e.l]), this.elementProperties = new Map(e.elementProperties);
  }
  static finalize() {
    if (this.hasOwnProperty(P("finalized"))) return;
    if (this.finalized = !0, this._$Ei(), this.hasOwnProperty(P("properties"))) {
      const t = this.properties, i = [...He(t), ...Le(t)];
      for (const s of i) this.createProperty(s, t[s]);
    }
    const e = this[Symbol.metadata];
    if (e !== null) {
      const t = litPropertyMetadata.get(e);
      if (t !== void 0) for (const [i, s] of t) this.elementProperties.set(i, s);
    }
    this._$Eh = /* @__PURE__ */ new Map();
    for (const [t, i] of this.elementProperties) {
      const s = this._$Eu(t, i);
      s !== void 0 && this._$Eh.set(s, t);
    }
    this.elementStyles = this.finalizeStyles(this.styles);
  }
  static finalizeStyles(e) {
    const t = [];
    if (Array.isArray(e)) {
      const i = new Set(e.flat(1 / 0).reverse());
      for (const s of i) t.unshift(ce(s));
    } else e !== void 0 && t.push(ce(e));
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
    return Ue(e, this.constructor.elementStyles), e;
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
    const i = this.constructor.elementProperties.get(e), s = this.constructor._$Eu(e, i);
    if (s !== void 0 && i.reflect === !0) {
      const n = (i.converter?.toAttribute !== void 0 ? i.converter : W).toAttribute(t, i.type);
      this._$Em = e, n == null ? this.removeAttribute(s) : this.setAttribute(s, n), this._$Em = null;
    }
  }
  _$AK(e, t) {
    const i = this.constructor, s = i._$Eh.get(e);
    if (s !== void 0 && this._$Em !== s) {
      const n = i.getPropertyOptions(s), o = typeof n.converter == "function" ? { fromAttribute: n.converter } : n.converter?.fromAttribute !== void 0 ? n.converter : W;
      this._$Em = s;
      const c = o.fromAttribute(t, n.type);
      this[s] = c ?? this._$Ej?.get(s) ?? c, this._$Em = null;
    }
  }
  requestUpdate(e, t, i, s = !1, n) {
    if (e !== void 0) {
      const o = this.constructor;
      if (s === !1 && (n = this[e]), i ?? (i = o.getPropertyOptions(e)), !((i.hasChanged ?? te)(n, t) || i.useDefault && i.reflect && n === this._$Ej?.get(e) && !this.hasAttribute(o._$Eu(e, i)))) return;
      this.C(e, t, i);
    }
    this.isUpdatePending === !1 && (this._$ES = this._$EP());
  }
  C(e, t, { useDefault: i, reflect: s, wrapped: n }, o) {
    i && !(this._$Ej ?? (this._$Ej = /* @__PURE__ */ new Map())).has(e) && (this._$Ej.set(e, o ?? t ?? this[e]), n !== !0 || o !== void 0) || (this._$AL.has(e) || (this.hasUpdated || i || (t = void 0), this._$AL.set(e, t)), s === !0 && this._$Em !== e && (this._$Eq ?? (this._$Eq = /* @__PURE__ */ new Set())).add(e));
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
        for (const [s, n] of this._$Ep) this[s] = n;
        this._$Ep = void 0;
      }
      const i = this.constructor.elementProperties;
      if (i.size > 0) for (const [s, n] of i) {
        const { wrapped: o } = n, c = this[s];
        o !== !0 || this._$AL.has(s) || c === void 0 || this.C(s, void 0, n, c);
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
E.elementStyles = [], E.shadowRootOptions = { mode: "open" }, E[P("elementProperties")] = /* @__PURE__ */ new Map(), E[P("finalized")] = /* @__PURE__ */ new Map(), We?.({ ReactiveElement: E }), (_.reactiveElementVersions ?? (_.reactiveElementVersions = [])).push("2.1.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const N = globalThis, pe = (r) => r, B = N.trustedTypes, he = B ? B.createPolicy("lit-html", { createHTML: (r) => r }) : void 0, Ae = "$lit$", v = `lit$${Math.random().toFixed(9).slice(2)}$`, Ee = "?" + v, Be = `<${Ee}>`, w = document, T = () => w.createComment(""), O = (r) => r === null || typeof r != "object" && typeof r != "function", ie = Array.isArray, Ve = (r) => ie(r) || typeof r?.[Symbol.iterator] == "function", K = `[ 	
\f\r]`, k = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, ue = /-->/g, me = />/g, y = RegExp(`>|${K}(?:([^\\s"'>=/]+)(${K}*=${K}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`, "g"), fe = /'/g, ge = /"/g, Se = /^(?:script|style|textarea|title)$/i, qe = (r) => (e, ...t) => ({ _$litType$: r, strings: e, values: t }), d = qe(1), S = Symbol.for("lit-noChange"), l = Symbol.for("lit-nothing"), ve = /* @__PURE__ */ new WeakMap(), $ = w.createTreeWalker(w, 129);
function Ce(r, e) {
  if (!ie(r) || !r.hasOwnProperty("raw")) throw Error("invalid template strings array");
  return he !== void 0 ? he.createHTML(e) : e;
}
const Ge = (r, e) => {
  const t = r.length - 1, i = [];
  let s, n = e === 2 ? "<svg>" : e === 3 ? "<math>" : "", o = k;
  for (let c = 0; c < t; c++) {
    const a = r[c];
    let h, u, p = -1, m = 0;
    for (; m < a.length && (o.lastIndex = m, u = o.exec(a), u !== null); ) m = o.lastIndex, o === k ? u[1] === "!--" ? o = ue : u[1] !== void 0 ? o = me : u[2] !== void 0 ? (Se.test(u[2]) && (s = RegExp("</" + u[2], "g")), o = y) : u[3] !== void 0 && (o = y) : o === y ? u[0] === ">" ? (o = s ?? k, p = -1) : u[1] === void 0 ? p = -2 : (p = o.lastIndex - u[2].length, h = u[1], o = u[3] === void 0 ? y : u[3] === '"' ? ge : fe) : o === ge || o === fe ? o = y : o === ue || o === me ? o = k : (o = y, s = void 0);
    const g = o === y && r[c + 1].startsWith("/>") ? " " : "";
    n += o === k ? a + Be : p >= 0 ? (i.push(h), a.slice(0, p) + Ae + a.slice(p) + v + g) : a + v + (p === -2 ? c : g);
  }
  return [Ce(r, n + (r[t] || "<?>") + (e === 2 ? "</svg>" : e === 3 ? "</math>" : "")), i];
};
class M {
  constructor({ strings: e, _$litType$: t }, i) {
    let s;
    this.parts = [];
    let n = 0, o = 0;
    const c = e.length - 1, a = this.parts, [h, u] = Ge(e, t);
    if (this.el = M.createElement(h, i), $.currentNode = this.el.content, t === 2 || t === 3) {
      const p = this.el.content.firstChild;
      p.replaceWith(...p.childNodes);
    }
    for (; (s = $.nextNode()) !== null && a.length < c; ) {
      if (s.nodeType === 1) {
        if (s.hasAttributes()) for (const p of s.getAttributeNames()) if (p.endsWith(Ae)) {
          const m = u[o++], g = s.getAttribute(p).split(v), L = /([.?@])?(.*)/.exec(m);
          a.push({ type: 1, index: n, name: L[2], strings: g, ctor: L[1] === "." ? Ye : L[1] === "?" ? Qe : L[1] === "@" ? Ze : V }), s.removeAttribute(p);
        } else p.startsWith(v) && (a.push({ type: 6, index: n }), s.removeAttribute(p));
        if (Se.test(s.tagName)) {
          const p = s.textContent.split(v), m = p.length - 1;
          if (m > 0) {
            s.textContent = B ? B.emptyScript : "";
            for (let g = 0; g < m; g++) s.append(p[g], T()), $.nextNode(), a.push({ type: 2, index: ++n });
            s.append(p[m], T());
          }
        }
      } else if (s.nodeType === 8) if (s.data === Ee) a.push({ type: 2, index: n });
      else {
        let p = -1;
        for (; (p = s.data.indexOf(v, p + 1)) !== -1; ) a.push({ type: 7, index: n }), p += v.length - 1;
      }
      n++;
    }
  }
  static createElement(e, t) {
    const i = w.createElement("template");
    return i.innerHTML = e, i;
  }
}
function C(r, e, t = r, i) {
  if (e === S) return e;
  let s = i !== void 0 ? t._$Co?.[i] : t._$Cl;
  const n = O(e) ? void 0 : e._$litDirective$;
  return s?.constructor !== n && (s?._$AO?.(!1), n === void 0 ? s = void 0 : (s = new n(r), s._$AT(r, t, i)), i !== void 0 ? (t._$Co ?? (t._$Co = []))[i] = s : t._$Cl = s), s !== void 0 && (e = C(r, s._$AS(r, e.values), s, i)), e;
}
class Ke {
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
    const { el: { content: t }, parts: i } = this._$AD, s = (e?.creationScope ?? w).importNode(t, !0);
    $.currentNode = s;
    let n = $.nextNode(), o = 0, c = 0, a = i[0];
    for (; a !== void 0; ) {
      if (o === a.index) {
        let h;
        a.type === 2 ? h = new I(n, n.nextSibling, this, e) : a.type === 1 ? h = new a.ctor(n, a.name, a.strings, this, e) : a.type === 6 && (h = new Je(n, this, e)), this._$AV.push(h), a = i[++c];
      }
      o !== a?.index && (n = $.nextNode(), o++);
    }
    return $.currentNode = w, s;
  }
  p(e) {
    let t = 0;
    for (const i of this._$AV) i !== void 0 && (i.strings !== void 0 ? (i._$AI(e, i, t), t += i.strings.length - 2) : i._$AI(e[t])), t++;
  }
}
class I {
  get _$AU() {
    return this._$AM?._$AU ?? this._$Cv;
  }
  constructor(e, t, i, s) {
    this.type = 2, this._$AH = l, this._$AN = void 0, this._$AA = e, this._$AB = t, this._$AM = i, this.options = s, this._$Cv = s?.isConnected ?? !0;
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
    e = C(this, e, t), O(e) ? e === l || e == null || e === "" ? (this._$AH !== l && this._$AR(), this._$AH = l) : e !== this._$AH && e !== S && this._(e) : e._$litType$ !== void 0 ? this.$(e) : e.nodeType !== void 0 ? this.T(e) : Ve(e) ? this.k(e) : this._(e);
  }
  O(e) {
    return this._$AA.parentNode.insertBefore(e, this._$AB);
  }
  T(e) {
    this._$AH !== e && (this._$AR(), this._$AH = this.O(e));
  }
  _(e) {
    this._$AH !== l && O(this._$AH) ? this._$AA.nextSibling.data = e : this.T(w.createTextNode(e)), this._$AH = e;
  }
  $(e) {
    const { values: t, _$litType$: i } = e, s = typeof i == "number" ? this._$AC(e) : (i.el === void 0 && (i.el = M.createElement(Ce(i.h, i.h[0]), this.options)), i);
    if (this._$AH?._$AD === s) this._$AH.p(t);
    else {
      const n = new Ke(s, this), o = n.u(this.options);
      n.p(t), this.T(o), this._$AH = n;
    }
  }
  _$AC(e) {
    let t = ve.get(e.strings);
    return t === void 0 && ve.set(e.strings, t = new M(e)), t;
  }
  k(e) {
    ie(this._$AH) || (this._$AH = [], this._$AR());
    const t = this._$AH;
    let i, s = 0;
    for (const n of e) s === t.length ? t.push(i = new I(this.O(T()), this.O(T()), this, this.options)) : i = t[s], i._$AI(n), s++;
    s < t.length && (this._$AR(i && i._$AB.nextSibling, s), t.length = s);
  }
  _$AR(e = this._$AA.nextSibling, t) {
    for (this._$AP?.(!1, !0, t); e !== this._$AB; ) {
      const i = pe(e).nextSibling;
      pe(e).remove(), e = i;
    }
  }
  setConnected(e) {
    this._$AM === void 0 && (this._$Cv = e, this._$AP?.(e));
  }
}
class V {
  get tagName() {
    return this.element.tagName;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  constructor(e, t, i, s, n) {
    this.type = 1, this._$AH = l, this._$AN = void 0, this.element = e, this.name = t, this._$AM = s, this.options = n, i.length > 2 || i[0] !== "" || i[1] !== "" ? (this._$AH = Array(i.length - 1).fill(new String()), this.strings = i) : this._$AH = l;
  }
  _$AI(e, t = this, i, s) {
    const n = this.strings;
    let o = !1;
    if (n === void 0) e = C(this, e, t, 0), o = !O(e) || e !== this._$AH && e !== S, o && (this._$AH = e);
    else {
      const c = e;
      let a, h;
      for (e = n[0], a = 0; a < n.length - 1; a++) h = C(this, c[i + a], t, a), h === S && (h = this._$AH[a]), o || (o = !O(h) || h !== this._$AH[a]), h === l ? e = l : e !== l && (e += (h ?? "") + n[a + 1]), this._$AH[a] = h;
    }
    o && !s && this.j(e);
  }
  j(e) {
    e === l ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, e ?? "");
  }
}
class Ye extends V {
  constructor() {
    super(...arguments), this.type = 3;
  }
  j(e) {
    this.element[this.name] = e === l ? void 0 : e;
  }
}
class Qe extends V {
  constructor() {
    super(...arguments), this.type = 4;
  }
  j(e) {
    this.element.toggleAttribute(this.name, !!e && e !== l);
  }
}
class Ze extends V {
  constructor(e, t, i, s, n) {
    super(e, t, i, s, n), this.type = 5;
  }
  _$AI(e, t = this) {
    if ((e = C(this, e, t, 0) ?? l) === S) return;
    const i = this._$AH, s = e === l && i !== l || e.capture !== i.capture || e.once !== i.once || e.passive !== i.passive, n = e !== l && (i === l || s);
    s && this.element.removeEventListener(this.name, this, i), n && this.element.addEventListener(this.name, this, e), this._$AH = e;
  }
  handleEvent(e) {
    typeof this._$AH == "function" ? this._$AH.call(this.options?.host ?? this.element, e) : this._$AH.handleEvent(e);
  }
}
class Je {
  constructor(e, t, i) {
    this.element = e, this.type = 6, this._$AN = void 0, this._$AM = t, this.options = i;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AI(e) {
    C(this, e);
  }
}
const Xe = N.litHtmlPolyfillSupport;
Xe?.(M, I), (N.litHtmlVersions ?? (N.litHtmlVersions = [])).push("3.3.3");
const et = (r, e, t) => {
  const i = t?.renderBefore ?? e;
  let s = i._$litPart$;
  if (s === void 0) {
    const n = t?.renderBefore ?? null;
    i._$litPart$ = s = new I(e.insertBefore(T(), n), n, void 0, t ?? {});
  }
  return s._$AI(r), s;
};
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const R = globalThis;
class x extends E {
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
    this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(e), this._$Do = et(t, this.renderRoot, this.renderOptions);
  }
  connectedCallback() {
    super.connectedCallback(), this._$Do?.setConnected(!0);
  }
  disconnectedCallback() {
    super.disconnectedCallback(), this._$Do?.setConnected(!1);
  }
  render() {
    return S;
  }
}
x._$litElement$ = !0, x.finalized = !0, R.litElementHydrateSupport?.({ LitElement: x });
const tt = R.litElementPolyfillSupport;
tt?.({ LitElement: x });
(R.litElementVersions ?? (R.litElementVersions = [])).push("4.2.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const it = { attribute: !0, type: String, converter: W, reflect: !1, hasChanged: te }, st = (r = it, e, t) => {
  const { kind: i, metadata: s } = t;
  let n = globalThis.litPropertyMetadata.get(s);
  if (n === void 0 && globalThis.litPropertyMetadata.set(s, n = /* @__PURE__ */ new Map()), i === "setter" && ((r = Object.create(r)).wrapped = !0), n.set(t.name, r), i === "accessor") {
    const { name: o } = t;
    return { set(c) {
      const a = e.get.call(this);
      e.set.call(this, c), this.requestUpdate(o, a, r, !0, c);
    }, init(c) {
      return c !== void 0 && this.C(o, void 0, r, c), c;
    } };
  }
  if (i === "setter") {
    const { name: o } = t;
    return function(c) {
      const a = this[o];
      e.call(this, c), this.requestUpdate(o, a, r, !0, c);
    };
  }
  throw Error("Unsupported decorator location: " + i);
};
function q(r) {
  return (e, t) => typeof t == "object" ? st(r, e, t) : ((i, s, n) => {
    const o = s.hasOwnProperty(n);
    return s.constructor.createProperty(n, i), o ? Object.getOwnPropertyDescriptor(s, n) : void 0;
  })(r, e, t);
}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
function H(r) {
  return q({ ...r, state: !0, attribute: !1 });
}
const rt = ee`
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
`, nt = ee`
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
`, U = "—", ot = /* @__PURE__ */ new Set(["unavailable", "unknown", "none", ""]);
function b(r) {
  return r ? ot.has(r.state) : !0;
}
function ke(r, e) {
  const t = { ...e.entities ?? {} }, i = {
    status: "_status",
    water_quality_score: "_water_quality_score",
    recommendations: "_recommendations",
    problems: "_problems",
    temperature: "_temperature",
    ph: "_ph",
    free_chlorine: "_free_chlorine",
    orp: "_orp"
  }, s = (n) => n.endsWith("_status") && !/_(ph|orp|free_chlorine|tac|cya|hardness|salt|tds)_status$/.test(n);
  if (e.device_id && r.entities) {
    for (const n of Object.values(r.entities))
      if (n.device_id === e.device_id)
        for (const [o, c] of Object.entries(i))
          t[o] || (o === "status" ? s(n.entity_id) && (t[o] = n.entity_id) : n.entity_id.endsWith(c) && (t[o] = n.entity_id));
  }
  return t;
}
function f(r, e) {
  if (e)
    return r.states[e];
}
function at(r) {
  if (!r || b(r)) return "unknown";
  const e = r.state.toLowerCase();
  return e === "ok" || e === "warning" || e === "critical" ? e : "unknown";
}
const ct = {
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
function lt(r) {
  return ct[r];
}
const dt = {
  temperature: { icon: "🌡️", label: "Temp", fractionDigits: 1, unitFallback: "°C" },
  ph: { icon: "⚗️", label: "pH", fractionDigits: 1, unitFallback: "" },
  free_chlorine: { icon: "🧪", label: "Cl", fractionDigits: 1, unitFallback: "mg/L" },
  orp: { icon: "⚡", label: "ORP", fractionDigits: 0, unitFallback: "mV" }
};
function pt(r) {
  return dt[r];
}
function ht(r, e, t) {
  if (b(r)) return U;
  const i = r.state, s = Number(i), n = r.attributes.unit_of_measurement ?? t;
  return Number.isFinite(s) ? `${s.toFixed(e)}${n ? ` ${n}` : ""}`.trim() : `${i}${n ? ` ${n}` : ""}`.trim();
}
function ut(r, e, t) {
  if (r.metrics?.length) return r.metrics;
  const i = ["temperature", "ph", "free_chlorine"], s = f(t, e.free_chlorine);
  return b(s) && e.orp && !b(f(t, e.orp)) ? ["temperature", "ph", "orp"] : i;
}
function mt(r) {
  return r >= 80 ? "good" : r >= 50 ? "warn" : "bad";
}
function Pe(r) {
  if (!r) return { count: 0, list: [] };
  const e = Number(r.state), t = r.attributes.recommendations ?? [];
  return { count: Number.isFinite(e) ? e : t.length, list: t };
}
const ft = {
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
function F(r) {
  return ft[r];
}
const se = {
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
function Ne(r, e) {
  return e ? `${r} ${e}` : r;
}
function gt(r, e) {
  if (e === null || !Number.isFinite(e)) return U;
  if (r === null) return String(e);
  const t = se[r];
  return t ? Ne(e.toFixed(t.fractionDigits), t.unit) : String(e);
}
function vt(r, e) {
  if (!e || e.length !== 2) return U;
  const [t, i] = e;
  if (!Number.isFinite(t) || !Number.isFinite(i)) return U;
  if (r === null) return `${t}–${i}`;
  const s = se[r];
  if (!s) return `${t}–${i}`;
  const n = t.toFixed(s.fractionDigits), o = i.toFixed(s.fractionDigits);
  return Ne(`${n}–${o}`, s.unit);
}
function _t(r) {
  return r === null ? "" : se[r]?.label ?? r;
}
function _e(r) {
  if (!r || b(r))
    return { count: 0, list: [], worst: "ok" };
  const e = r.attributes.problems ?? [], t = Number(r.state), i = Number.isFinite(t) ? t : e.length, n = r.attributes.worst_severity ?? e[0]?.severity ?? "ok";
  return { count: i, list: e, worst: n };
}
function bt(r) {
  return r.treatments ?? r.actions ?? [];
}
const yt = {
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
function Re(r) {
  if (r.priority) return r.priority;
  switch (r.severity) {
    case "critical":
      return "critical";
    case "medium":
      return "medium";
    default:
      return "low";
  }
}
function $t(r) {
  const e = Re(r);
  return { key: e, ...yt[e] };
}
function xt(r, e) {
  if (e.entity) return e.entity;
  if (!(!e.device_id || !r.entities)) {
    for (const t of Object.values(r.entities))
      if (t.device_id === e.device_id && t.entity_id.endsWith("_recommendations"))
        return t.entity_id;
  }
}
var wt = Object.defineProperty, Te = (r, e, t, i) => {
  for (var s = void 0, n = r.length - 1, o; n >= 0; n--)
    (o = r[n]) && (s = o(e, t, s) || s);
  return s && wt(e, t, s), s;
};
const Y = "poolman-pool-overview-card", re = class re extends x {
  /** Lovelace card size hint (1 unit ≈ 50px). */
  getCardSize() {
    return 3;
  }
  static getStubConfig() {
    return { type: `custom:${Y}` };
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
    const e = ke(this.hass, this._config), t = f(this.hass, e.status), i = at(t), s = lt(i), n = this._config.name ?? this._deviceName(this._config.device_id) ?? "Pool", o = ut(this._config, e, this.hass);
    return d`
      <ha-card>
        <div class="header">
          <div class="title">
            <span class="pool-icon" aria-hidden="true">🏊</span>
            <span>${n}</span>
          </div>
          <span
            class="badge"
            style=${`background:${s.color}`}
            role="status"
            aria-label=${`Status: ${s.label}`}
          >
            <span class="dot" aria-hidden="true"></span>
            ${s.label}
          </span>
        </div>

        <div class="metrics">
          ${o.map((c) => this._renderMetric(c, e))}
        </div>

        ${this._config.show_score !== !1 ? this._renderScore(e.water_quality_score) : l}
        ${this._renderRecommendations(e.recommendations)}
      </ha-card>
    `;
  }
  _renderMetric(e, t) {
    const i = pt(e), s = f(this.hass, t[e]), n = ht(s, i.fractionDigits, i.unitFallback);
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
    const t = f(this.hass, e);
    if (b(t))
      return d`
        <div class="score">
          <div class="score-row">
            <span>Quality score</span>
            <strong>${U}</strong>
          </div>
        </div>
      `;
    const i = Math.max(0, Math.min(100, Number(t.state) || 0)), s = mt(i);
    return d`
      <div class="score">
        <div class="score-row">
          <span>Quality score</span>
          <strong>${i} / 100</strong>
        </div>
        <div class="score-bar">
          <div
            class="score-bar-fill ${s === "good" ? "" : s}"
            style=${`width:${i}%`}
          ></div>
        </div>
      </div>
    `;
  }
  _renderRecommendations(e) {
    const t = f(this.hass, e);
    if (!t) return l;
    const { count: i } = Pe(t), s = this._config?.recommendations_path, n = i > 0, o = i === 0 ? "Your pool is in good condition" : `${i} recommendation${i === 1 ? "" : "s"}`;
    return d`
      <div
        class="recommendations"
        role=${n ? "button" : "presentation"}
        tabindex=${n ? "0" : "-1"}
        ?disabled=${!n}
        @click=${() => n && this._openRecommendations(t.entity_id, s)}
        @keydown=${(a) => {
      n && (a.key === "Enter" || a.key === " ") && (a.preventDefault(), this._openRecommendations(t.entity_id, s));
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
re.styles = rt;
let z = re;
Te([
  q({ attribute: !1 })
], z.prototype, "hass");
Te([
  H()
], z.prototype, "_config");
customElements.get(Y) || customElements.define(Y, z);
const At = ee`
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
var Et = Object.defineProperty, Oe = (r, e, t, i) => {
  for (var s = void 0, n = r.length - 1, o; n >= 0; n--)
    (o = r[n]) && (s = o(e, t, s) || s);
  return s && Et(e, t, s), s;
};
const Q = "poolman-problem-card", be = {
  ok: {
    label: "OK",
    color: "var(--success-color, #43a047)",
    icon: "✅"
  },
  low: F("low"),
  medium: F("medium"),
  critical: F("critical")
}, ne = class ne extends x {
  /** Lovelace card size hint (1 unit ≈ 50px). */
  getCardSize() {
    const e = this._resolveEntity();
    if (!e) return 1;
    const { count: t } = _e(e);
    if (t === 0) return 1;
    const i = this._config?.max ?? t;
    return 1 + Math.min(t, i);
  }
  static getStubConfig() {
    return { type: `custom:${Q}` };
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
    const { count: i, list: s, worst: n } = _e(e), o = be[n] ?? be.ok;
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
            ` : this._renderProblems(s, i)}
      </ha-card>
    `;
  }
  _renderProblems(e, t) {
    const i = this._config?.max, s = i !== void 0 ? e.slice(0, i) : e, n = Math.max(0, t - s.length);
    return d`
      <div class="problems">
        ${s.map((o) => this._renderProblem(o))}
        ${n > 0 ? d`<div class="more">
              +${n} more problem${n === 1 ? "" : "s"}
            </div>` : l}
      </div>
    `;
  }
  _renderProblem(e) {
    const t = e.severity, i = F(t), s = _t(e.metric), n = e.metric !== null && e.value !== null && e.expected_range !== null;
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
                ${s ? d`<span class="metric-label">${s}</span>
                      <span class="sep" aria-hidden="true">•</span>` : l}
                <span>
                  Current:
                  <strong>${gt(e.metric, e.value)}</strong>
                </span>
                <span class="sep" aria-hidden="true">—</span>
                <span>
                  Expected:
                  <strong
                    >${vt(e.metric, e.expected_range)}</strong
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
      return f(this.hass, this._config.entity);
    const e = ke(this.hass, {
      type: this._config.type,
      device_id: this._config.device_id
    });
    return f(this.hass, e.problems);
  }
  _deviceName() {
    const e = this._config?.device_id;
    if (!e || !this.hass?.devices) return;
    const t = this.hass.devices[e];
    if (t)
      return t.name_by_user ?? t.name ?? void 0;
  }
};
ne.styles = At;
let D = ne;
Oe([
  q({ attribute: !1 })
], D.prototype, "hass");
Oe([
  H()
], D.prototype, "_config");
customElements.get(Q) || customElements.define(Q, D);
var St = Object.defineProperty, G = (r, e, t, i) => {
  for (var s = void 0, n = r.length - 1, o; n >= 0; n--)
    (o = r[n]) && (s = o(e, t, s) || s);
  return s && St(e, t, s), s;
};
const Z = "poolman-recommendations-card", oe = class oe extends x {
  constructor() {
    super(...arguments), this._dismissed = /* @__PURE__ */ new Set(), this._expanded = /* @__PURE__ */ new Set(), this._lastSeenIds = /* @__PURE__ */ new Set();
  }
  /** Lovelace card size hint (1 unit ≈ 50px). */
  getCardSize() {
    return 4;
  }
  static getStubConfig() {
    return { type: `custom:${Z}` };
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
    const e = xt(this.hass, this._config), t = f(this.hass, e), i = this._config.name ?? this._deviceName() ?? "Recommendations";
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
    const { count: s, list: n } = Pe(t);
    this._lastSeenIds = new Set(n.map((c) => c.id));
    const o = n.filter((c) => !this._dismissed.has(c.id));
    return d`
      <ha-card>
        <div class="header">
          <div class="title">
            <span class="icon" aria-hidden="true">📋</span>
            <span>${i}</span>
          </div>
          ${s > 0 ? d`<span class="count">${o.length} / ${s}</span>` : l}
        </div>

        ${o.length === 0 ? this._renderEmpty() : d`<div class="list">${o.map((c) => this._renderRecommendation(c))}</div>`}
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
    const t = $t(e), i = this._expanded.has(e.id), s = this._config?.show_severity !== !1, n = bt(e);
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
            ${s ? d`<span>${t.label}</span>` : l}
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
    const i = Re(e);
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
oe.styles = nt;
let A = oe;
G([
  q({ attribute: !1 })
], A.prototype, "hass");
G([
  H()
], A.prototype, "_config");
G([
  H()
], A.prototype, "_dismissed");
G([
  H()
], A.prototype, "_expanded");
customElements.get(Z) || customElements.define(Z, A);
const ye = "poolman-pool-overview-card", $e = "poolman-problem-card", xe = "poolman-recommendations-card", Ct = "0.1.0";
window.customCards = window.customCards ?? [];
window.customCards.some((r) => r.type === ye) || window.customCards.push({
  type: ye,
  name: "Pool Overview",
  description: "Glanceable summary card for a Pool Manager pool: status badge, key chemistry metrics, water quality score and recommendation count.",
  preview: !0,
  documentationURL: "https://noirbizarre.github.io/hass-poolman/pool-overview-card/"
});
window.customCards.some((r) => r.type === $e) || window.customCards.push({
  type: $e,
  name: "Pool Problems",
  description: "Diagnostic card listing the current pool problems by severity, with measured value and expected range.",
  preview: !0,
  documentationURL: "https://noirbizarre.github.io/hass-poolman/problem-card/"
});
window.customCards.some((r) => r.type === xe) || window.customCards.push({
  type: xe,
  name: "Pool Recommendations",
  description: "Actionable pool recommendation list: severity badges, expandable details, and one-tap Apply / Ignore buttons backed by the poolman.apply_recommendation service.",
  preview: !0,
  documentationURL: "https://noirbizarre.github.io/hass-poolman/recommendations-card/"
});
console.info(
  `%c POOLMAN-CARDS %c v${Ct} `,
  "color: white; background: #03a9f4; font-weight: 700;",
  "color: #03a9f4; background: transparent; font-weight: 700;"
);
//# sourceMappingURL=poolman-pool-overview-card.js.map
