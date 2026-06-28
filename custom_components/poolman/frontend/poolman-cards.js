const ee = globalThis, Ee = ee.ShadowRoot && (ee.ShadyCSS === void 0 || ee.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype, Ae = /* @__PURE__ */ Symbol(), qe = /* @__PURE__ */ new WeakMap();
let et = class {
  constructor(e, t, i) {
    if (this._$cssResult$ = !0, i !== Ae) throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
    this.cssText = e, this.t = t;
  }
  get styleSheet() {
    let e = this.o;
    const t = this.t;
    if (Ee && e === void 0) {
      const i = t !== void 0 && t.length === 1;
      i && (e = qe.get(t)), e === void 0 && ((this.o = e = new CSSStyleSheet()).replaceSync(this.cssText), i && qe.set(t, e));
    }
    return e;
  }
  toString() {
    return this.cssText;
  }
};
const yt = (o) => new et(typeof o == "string" ? o : o + "", void 0, Ae), W = (o, ...e) => {
  const t = o.length === 1 ? o[0] : e.reduce((i, r, s) => i + ((n) => {
    if (n._$cssResult$ === !0) return n.cssText;
    if (typeof n == "number") return n;
    throw Error("Value passed to 'css' function must be a 'css' function result: " + n + ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.");
  })(r) + o[s + 1], o[0]);
  return new et(t, o, Ae);
}, bt = (o, e) => {
  if (Ee) o.adoptedStyleSheets = e.map((t) => t instanceof CSSStyleSheet ? t : t.styleSheet);
  else for (const t of e) {
    const i = document.createElement("style"), r = ee.litNonce;
    r !== void 0 && i.setAttribute("nonce", r), i.textContent = t.cssText, o.appendChild(i);
  }
}, ze = Ee ? (o) => o : (o) => o instanceof CSSStyleSheet ? ((e) => {
  let t = "";
  for (const i of e.cssRules) t += i.cssText;
  return yt(t);
})(o) : o;
const { is: $t, defineProperty: xt, getOwnPropertyDescriptor: wt, getOwnPropertyNames: Et, getOwnPropertySymbols: At, getPrototypeOf: St } = Object, w = globalThis, De = w.trustedTypes, Ct = De ? De.emptyScript : "", kt = w.reactiveElementPolyfillSupport, M = (o, e) => o, ie = { toAttribute(o, e) {
  switch (e) {
    case Boolean:
      o = o ? Ct : null;
      break;
    case Object:
    case Array:
      o = o == null ? o : JSON.stringify(o);
  }
  return o;
}, fromAttribute(o, e) {
  let t = o;
  switch (e) {
    case Boolean:
      t = o !== null;
      break;
    case Number:
      t = o === null ? null : Number(o);
      break;
    case Object:
    case Array:
      try {
        t = JSON.parse(o);
      } catch {
        t = null;
      }
  }
  return t;
} }, Se = (o, e) => !$t(o, e), Ie = { attribute: !0, type: String, converter: ie, reflect: !1, useDefault: !1, hasChanged: Se };
Symbol.metadata ?? (Symbol.metadata = /* @__PURE__ */ Symbol("metadata")), w.litPropertyMetadata ?? (w.litPropertyMetadata = /* @__PURE__ */ new WeakMap());
let R = class extends HTMLElement {
  static addInitializer(e) {
    this._$Ei(), (this.l ?? (this.l = [])).push(e);
  }
  static get observedAttributes() {
    return this.finalize(), this._$Eh && [...this._$Eh.keys()];
  }
  static createProperty(e, t = Ie) {
    if (t.state && (t.attribute = !1), this._$Ei(), this.prototype.hasOwnProperty(e) && ((t = Object.create(t)).wrapped = !0), this.elementProperties.set(e, t), !t.noAccessor) {
      const i = /* @__PURE__ */ Symbol(), r = this.getPropertyDescriptor(e, i, t);
      r !== void 0 && xt(this.prototype, e, r);
    }
  }
  static getPropertyDescriptor(e, t, i) {
    const { get: r, set: s } = wt(this.prototype, e) ?? { get() {
      return this[t];
    }, set(n) {
      this[t] = n;
    } };
    return { get: r, set(n) {
      const a = r?.call(this);
      s?.call(this, n), this.requestUpdate(e, a, i);
    }, configurable: !0, enumerable: !0 };
  }
  static getPropertyOptions(e) {
    return this.elementProperties.get(e) ?? Ie;
  }
  static _$Ei() {
    if (this.hasOwnProperty(M("elementProperties"))) return;
    const e = St(this);
    e.finalize(), e.l !== void 0 && (this.l = [...e.l]), this.elementProperties = new Map(e.elementProperties);
  }
  static finalize() {
    if (this.hasOwnProperty(M("finalized"))) return;
    if (this.finalized = !0, this._$Ei(), this.hasOwnProperty(M("properties"))) {
      const t = this.properties, i = [...Et(t), ...At(t)];
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
      for (const r of i) t.unshift(ze(r));
    } else e !== void 0 && t.push(ze(e));
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
    return bt(e, this.constructor.elementStyles), e;
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
      const s = (i.converter?.toAttribute !== void 0 ? i.converter : ie).toAttribute(t, i.type);
      this._$Em = e, s == null ? this.removeAttribute(r) : this.setAttribute(r, s), this._$Em = null;
    }
  }
  _$AK(e, t) {
    const i = this.constructor, r = i._$Eh.get(e);
    if (r !== void 0 && this._$Em !== r) {
      const s = i.getPropertyOptions(r), n = typeof s.converter == "function" ? { fromAttribute: s.converter } : s.converter?.fromAttribute !== void 0 ? s.converter : ie;
      this._$Em = r;
      const a = n.fromAttribute(t, s.type);
      this[r] = a ?? this._$Ej?.get(r) ?? a, this._$Em = null;
    }
  }
  requestUpdate(e, t, i, r = !1, s) {
    if (e !== void 0) {
      const n = this.constructor;
      if (r === !1 && (s = this[e]), i ?? (i = n.getPropertyOptions(e)), !((i.hasChanged ?? Se)(s, t) || i.useDefault && i.reflect && s === this._$Ej?.get(e) && !this.hasAttribute(n._$Eu(e, i)))) return;
      this.C(e, t, i);
    }
    this.isUpdatePending === !1 && (this._$ES = this._$EP());
  }
  C(e, t, { useDefault: i, reflect: r, wrapped: s }, n) {
    i && !(this._$Ej ?? (this._$Ej = /* @__PURE__ */ new Map())).has(e) && (this._$Ej.set(e, n ?? t ?? this[e]), s !== !0 || n !== void 0) || (this._$AL.has(e) || (this.hasUpdated || i || (t = void 0), this._$AL.set(e, t)), r === !0 && this._$Em !== e && (this._$Eq ?? (this._$Eq = /* @__PURE__ */ new Set())).add(e));
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
        for (const [r, s] of this._$Ep) this[r] = s;
        this._$Ep = void 0;
      }
      const i = this.constructor.elementProperties;
      if (i.size > 0) for (const [r, s] of i) {
        const { wrapped: n } = s, a = this[r];
        n !== !0 || this._$AL.has(r) || a === void 0 || this.C(r, void 0, s, a);
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
R.elementStyles = [], R.shadowRootOptions = { mode: "open" }, R[M("elementProperties")] = /* @__PURE__ */ new Map(), R[M("finalized")] = /* @__PURE__ */ new Map(), kt?.({ ReactiveElement: R }), (w.reactiveElementVersions ?? (w.reactiveElementVersions = [])).push("2.1.2");
const L = globalThis, Me = (o) => o, re = L.trustedTypes, Le = re ? re.createPolicy("lit-html", { createHTML: (o) => o }) : void 0, tt = "$lit$", x = `lit$${Math.random().toFixed(9).slice(2)}$`, it = "?" + x, Tt = `<${it}>`, k = document, j = () => k.createComment(""), H = (o) => o === null || typeof o != "object" && typeof o != "function", Ce = Array.isArray, Ot = (o) => Ce(o) || typeof o?.[Symbol.iterator] == "function", ue = `[ 	
\f\r]`, D = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, Ue = /-->/g, je = />/g, A = RegExp(`>|${ue}(?:([^\\s"'>=/]+)(${ue}*=${ue}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`, "g"), He = /'/g, Be = /"/g, rt = /^(?:script|style|textarea|title)$/i, Pt = (o) => (e, ...t) => ({ _$litType$: o, strings: e, values: t }), l = Pt(1), N = /* @__PURE__ */ Symbol.for("lit-noChange"), c = /* @__PURE__ */ Symbol.for("lit-nothing"), Fe = /* @__PURE__ */ new WeakMap(), S = k.createTreeWalker(k, 129);
function ot(o, e) {
  if (!Ce(o) || !o.hasOwnProperty("raw")) throw Error("invalid template strings array");
  return Le !== void 0 ? Le.createHTML(e) : e;
}
const Rt = (o, e) => {
  const t = o.length - 1, i = [];
  let r, s = e === 2 ? "<svg>" : e === 3 ? "<math>" : "", n = D;
  for (let a = 0; a < t; a++) {
    const d = o[a];
    let p, f, h = -1, b = 0;
    for (; b < d.length && (n.lastIndex = b, f = n.exec(d), f !== null); ) b = n.lastIndex, n === D ? f[1] === "!--" ? n = Ue : f[1] !== void 0 ? n = je : f[2] !== void 0 ? (rt.test(f[2]) && (r = RegExp("</" + f[2], "g")), n = A) : f[3] !== void 0 && (n = A) : n === A ? f[0] === ">" ? (n = r ?? D, h = -1) : f[1] === void 0 ? h = -2 : (h = n.lastIndex - f[2].length, p = f[1], n = f[3] === void 0 ? A : f[3] === '"' ? Be : He) : n === Be || n === He ? n = A : n === Ue || n === je ? n = D : (n = A, r = void 0);
    const $ = n === A && o[a + 1].startsWith("/>") ? " " : "";
    s += n === D ? d + Tt : h >= 0 ? (i.push(p), d.slice(0, h) + tt + d.slice(h) + x + $) : d + x + (h === -2 ? a : $);
  }
  return [ot(o, s + (o[t] || "<?>") + (e === 2 ? "</svg>" : e === 3 ? "</math>" : "")), i];
};
class B {
  constructor({ strings: e, _$litType$: t }, i) {
    let r;
    this.parts = [];
    let s = 0, n = 0;
    const a = e.length - 1, d = this.parts, [p, f] = Rt(e, t);
    if (this.el = B.createElement(p, i), S.currentNode = this.el.content, t === 2 || t === 3) {
      const h = this.el.content.firstChild;
      h.replaceWith(...h.childNodes);
    }
    for (; (r = S.nextNode()) !== null && d.length < a; ) {
      if (r.nodeType === 1) {
        if (r.hasAttributes()) for (const h of r.getAttributeNames()) if (h.endsWith(tt)) {
          const b = f[n++], $ = r.getAttribute(h).split(x), X = /([.?@])?(.*)/.exec(b);
          d.push({ type: 1, index: s, name: X[2], strings: $, ctor: X[1] === "." ? qt : X[1] === "?" ? zt : X[1] === "@" ? Dt : se }), r.removeAttribute(h);
        } else h.startsWith(x) && (d.push({ type: 6, index: s }), r.removeAttribute(h));
        if (rt.test(r.tagName)) {
          const h = r.textContent.split(x), b = h.length - 1;
          if (b > 0) {
            r.textContent = re ? re.emptyScript : "";
            for (let $ = 0; $ < b; $++) r.append(h[$], j()), S.nextNode(), d.push({ type: 2, index: ++s });
            r.append(h[b], j());
          }
        }
      } else if (r.nodeType === 8) if (r.data === it) d.push({ type: 2, index: s });
      else {
        let h = -1;
        for (; (h = r.data.indexOf(x, h + 1)) !== -1; ) d.push({ type: 7, index: s }), h += x.length - 1;
      }
      s++;
    }
  }
  static createElement(e, t) {
    const i = k.createElement("template");
    return i.innerHTML = e, i;
  }
}
function q(o, e, t = o, i) {
  if (e === N) return e;
  let r = i !== void 0 ? t._$Co?.[i] : t._$Cl;
  const s = H(e) ? void 0 : e._$litDirective$;
  return r?.constructor !== s && (r?._$AO?.(!1), s === void 0 ? r = void 0 : (r = new s(o), r._$AT(o, t, i)), i !== void 0 ? (t._$Co ?? (t._$Co = []))[i] = r : t._$Cl = r), r !== void 0 && (e = q(o, r._$AS(o, e.values), r, i)), e;
}
class Nt {
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
    const { el: { content: t }, parts: i } = this._$AD, r = (e?.creationScope ?? k).importNode(t, !0);
    S.currentNode = r;
    let s = S.nextNode(), n = 0, a = 0, d = i[0];
    for (; d !== void 0; ) {
      if (n === d.index) {
        let p;
        d.type === 2 ? p = new Y(s, s.nextSibling, this, e) : d.type === 1 ? p = new d.ctor(s, d.name, d.strings, this, e) : d.type === 6 && (p = new It(s, this, e)), this._$AV.push(p), d = i[++a];
      }
      n !== d?.index && (s = S.nextNode(), n++);
    }
    return S.currentNode = k, r;
  }
  p(e) {
    let t = 0;
    for (const i of this._$AV) i !== void 0 && (i.strings !== void 0 ? (i._$AI(e, i, t), t += i.strings.length - 2) : i._$AI(e[t])), t++;
  }
}
class Y {
  get _$AU() {
    return this._$AM?._$AU ?? this._$Cv;
  }
  constructor(e, t, i, r) {
    this.type = 2, this._$AH = c, this._$AN = void 0, this._$AA = e, this._$AB = t, this._$AM = i, this.options = r, this._$Cv = r?.isConnected ?? !0;
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
    e = q(this, e, t), H(e) ? e === c || e == null || e === "" ? (this._$AH !== c && this._$AR(), this._$AH = c) : e !== this._$AH && e !== N && this._(e) : e._$litType$ !== void 0 ? this.$(e) : e.nodeType !== void 0 ? this.T(e) : Ot(e) ? this.k(e) : this._(e);
  }
  O(e) {
    return this._$AA.parentNode.insertBefore(e, this._$AB);
  }
  T(e) {
    this._$AH !== e && (this._$AR(), this._$AH = this.O(e));
  }
  _(e) {
    this._$AH !== c && H(this._$AH) ? this._$AA.nextSibling.data = e : this.T(k.createTextNode(e)), this._$AH = e;
  }
  $(e) {
    const { values: t, _$litType$: i } = e, r = typeof i == "number" ? this._$AC(e) : (i.el === void 0 && (i.el = B.createElement(ot(i.h, i.h[0]), this.options)), i);
    if (this._$AH?._$AD === r) this._$AH.p(t);
    else {
      const s = new Nt(r, this), n = s.u(this.options);
      s.p(t), this.T(n), this._$AH = s;
    }
  }
  _$AC(e) {
    let t = Fe.get(e.strings);
    return t === void 0 && Fe.set(e.strings, t = new B(e)), t;
  }
  k(e) {
    Ce(this._$AH) || (this._$AH = [], this._$AR());
    const t = this._$AH;
    let i, r = 0;
    for (const s of e) r === t.length ? t.push(i = new Y(this.O(j()), this.O(j()), this, this.options)) : i = t[r], i._$AI(s), r++;
    r < t.length && (this._$AR(i && i._$AB.nextSibling, r), t.length = r);
  }
  _$AR(e = this._$AA.nextSibling, t) {
    for (this._$AP?.(!1, !0, t); e !== this._$AB; ) {
      const i = Me(e).nextSibling;
      Me(e).remove(), e = i;
    }
  }
  setConnected(e) {
    this._$AM === void 0 && (this._$Cv = e, this._$AP?.(e));
  }
}
class se {
  get tagName() {
    return this.element.tagName;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  constructor(e, t, i, r, s) {
    this.type = 1, this._$AH = c, this._$AN = void 0, this.element = e, this.name = t, this._$AM = r, this.options = s, i.length > 2 || i[0] !== "" || i[1] !== "" ? (this._$AH = Array(i.length - 1).fill(new String()), this.strings = i) : this._$AH = c;
  }
  _$AI(e, t = this, i, r) {
    const s = this.strings;
    let n = !1;
    if (s === void 0) e = q(this, e, t, 0), n = !H(e) || e !== this._$AH && e !== N, n && (this._$AH = e);
    else {
      const a = e;
      let d, p;
      for (e = s[0], d = 0; d < s.length - 1; d++) p = q(this, a[i + d], t, d), p === N && (p = this._$AH[d]), n || (n = !H(p) || p !== this._$AH[d]), p === c ? e = c : e !== c && (e += (p ?? "") + s[d + 1]), this._$AH[d] = p;
    }
    n && !r && this.j(e);
  }
  j(e) {
    e === c ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, e ?? "");
  }
}
class qt extends se {
  constructor() {
    super(...arguments), this.type = 3;
  }
  j(e) {
    this.element[this.name] = e === c ? void 0 : e;
  }
}
class zt extends se {
  constructor() {
    super(...arguments), this.type = 4;
  }
  j(e) {
    this.element.toggleAttribute(this.name, !!e && e !== c);
  }
}
class Dt extends se {
  constructor(e, t, i, r, s) {
    super(e, t, i, r, s), this.type = 5;
  }
  _$AI(e, t = this) {
    if ((e = q(this, e, t, 0) ?? c) === N) return;
    const i = this._$AH, r = e === c && i !== c || e.capture !== i.capture || e.once !== i.once || e.passive !== i.passive, s = e !== c && (i === c || r);
    r && this.element.removeEventListener(this.name, this, i), s && this.element.addEventListener(this.name, this, e), this._$AH = e;
  }
  handleEvent(e) {
    typeof this._$AH == "function" ? this._$AH.call(this.options?.host ?? this.element, e) : this._$AH.handleEvent(e);
  }
}
class It {
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
const Mt = L.litHtmlPolyfillSupport;
Mt?.(B, Y), (L.litHtmlVersions ?? (L.litHtmlVersions = [])).push("3.3.3");
const Lt = (o, e, t) => {
  const i = t?.renderBefore ?? e;
  let r = i._$litPart$;
  if (r === void 0) {
    const s = t?.renderBefore ?? null;
    i._$litPart$ = r = new Y(e.insertBefore(j(), s), s, void 0, t ?? {});
  }
  return r._$AI(o), r;
};
const U = globalThis;
class _ extends R {
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
    this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(e), this._$Do = Lt(t, this.renderRoot, this.renderOptions);
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
_._$litElement$ = !0, _.finalized = !0, U.litElementHydrateSupport?.({ LitElement: _ });
const Ut = U.litElementPolyfillSupport;
Ut?.({ LitElement: _ });
(U.litElementVersions ?? (U.litElementVersions = [])).push("4.2.2");
const jt = { attribute: !0, type: String, converter: ie, reflect: !1, hasChanged: Se }, Ht = (o = jt, e, t) => {
  const { kind: i, metadata: r } = t;
  let s = globalThis.litPropertyMetadata.get(r);
  if (s === void 0 && globalThis.litPropertyMetadata.set(r, s = /* @__PURE__ */ new Map()), i === "setter" && ((o = Object.create(o)).wrapped = !0), s.set(t.name, o), i === "accessor") {
    const { name: n } = t;
    return { set(a) {
      const d = e.get.call(this);
      e.set.call(this, a), this.requestUpdate(n, d, o, !0, a);
    }, init(a) {
      return a !== void 0 && this.C(n, void 0, o, a), a;
    } };
  }
  if (i === "setter") {
    const { name: n } = t;
    return function(a) {
      const d = this[n];
      e.call(this, a), this.requestUpdate(n, d, o, !0, a);
    };
  }
  throw Error("Unsupported decorator location: " + i);
};
function g(o) {
  return (e, t) => typeof t == "object" ? Ht(o, e, t) : ((i, r, s) => {
    const n = r.hasOwnProperty(s);
    return r.constructor.createProperty(s, i), n ? Object.getOwnPropertyDescriptor(r, s) : void 0;
  })(o, e, t);
}
function m(o) {
  return g({ ...o, state: !0, attribute: !1 });
}
const Bt = W`
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
`, Ft = W`
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
`, Vt = W`
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
`, Gt = {
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
  dialog_validation_quantity: "Quantity must be a positive number",
  editor_device: "Pool device",
  editor_entity: "Entity",
  editor_name: "Name",
  editor_metrics: "Metrics",
  editor_metric_temperature: "Temperature",
  editor_metric_ph: "pH",
  editor_metric_free_chlorine: "Free chlorine",
  editor_metric_orp: "ORP",
  editor_show_score: "Show water quality score",
  editor_recommendations_path: "Recommendations navigation path",
  editor_max: "Maximum rows",
  editor_show_severity: "Show severity label",
  editor_confirm_apply: "Confirm before applying",
  editor_confirm_apply_never: "Never",
  editor_confirm_apply_always: "Always",
  editor_confirm_apply_critical_high: "Critical and high priority",
  editor_limit: "Maximum actions",
  editor_show_source: "Show source badge",
  editor_group_by_day: "Group by day",
  editor_analyze: "Show Analyze button",
  editor_boost: "Show filtration boost buttons",
  editor_record: "Show Record treatment button",
  editor_device_required: "Pool device is required",
  editor_device_or_entity_required: "A pool device or an entity is required"
}, Wt = {
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
  dialog_validation_quantity: "La quantité doit être un nombre positif",
  editor_device: "Bassin",
  editor_entity: "Entité",
  editor_name: "Nom",
  editor_metrics: "Mesures",
  editor_metric_temperature: "Température",
  editor_metric_ph: "pH",
  editor_metric_free_chlorine: "Chlore libre",
  editor_metric_orp: "ORP",
  editor_show_score: "Afficher le score de qualité",
  editor_recommendations_path: "Chemin de navigation des recommandations",
  editor_max: "Nombre maximum de lignes",
  editor_show_severity: "Afficher le libellé de sévérité",
  editor_confirm_apply: "Confirmer avant application",
  editor_confirm_apply_never: "Jamais",
  editor_confirm_apply_always: "Toujours",
  editor_confirm_apply_critical_high: "Priorité critique et haute",
  editor_limit: "Nombre maximum d'actions",
  editor_show_source: "Afficher la source",
  editor_group_by_day: "Grouper par jour",
  editor_analyze: "Afficher le bouton Analyser",
  editor_boost: "Afficher les boutons Booster",
  editor_record: "Afficher le bouton Enregistrer",
  editor_device_required: "Le bassin est requis",
  editor_device_or_entity_required: "Un bassin ou une entité est requis"
}, Ve = { en: Gt, fr: Wt };
function Yt(o) {
  return o && o.toLowerCase().replace("_", "-").split("-")[0] === "fr" ? "fr" : "en";
}
function u(o, e) {
  const t = Yt(o);
  return Ve[t][e] ?? Ve.en[e] ?? e;
}
const st = "poolman";
function Q(o, e) {
  o.dispatchEvent(
    new CustomEvent("config-changed", {
      detail: { config: e },
      bubbles: !0,
      composed: !0
    })
  );
}
function K(o) {
  return (e) => {
    const t = Qt(e.name);
    return t ? u(o, t) : e.name;
  };
}
function Qt(o) {
  switch (o) {
    case "device_id":
      return "editor_device";
    case "entity":
      return "editor_entity";
    case "name":
      return "editor_name";
    case "metrics":
      return "editor_metrics";
    case "show_score":
      return "editor_show_score";
    case "recommendations_path":
      return "editor_recommendations_path";
    case "max":
      return "editor_max";
    case "show_severity":
      return "editor_show_severity";
    case "confirm_apply":
      return "editor_confirm_apply";
    case "limit":
      return "editor_limit";
    case "show_source":
      return "editor_show_source";
    case "group_by_day":
      return "editor_group_by_day";
    case "analyze":
      return "editor_analyze";
    case "boost":
      return "editor_boost";
    case "record":
      return "editor_record";
    default:
      return;
  }
}
const Z = {
  device: { integration: st }
};
function nt(o = "sensor") {
  return { entity: { domain: o } };
}
const C = { boolean: {} }, z = { text: {} };
function at(o, e, t = 1) {
  return { number: { min: o, max: e, step: t, mode: "box" } };
}
function J(o) {
  if (o?.devices) {
    if (o.entities) {
      for (const e of Object.values(o.entities))
        if (e.platform === st && e.device_id && o.devices[e.device_id])
          return e.device_id;
    }
    return Object.keys(o.devices)[0];
  }
}
const T = "—", Kt = /* @__PURE__ */ new Set(["unavailable", "unknown", "none", ""]);
function E(o) {
  return o ? Kt.has(o.state) : !0;
}
function oe(o, e) {
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
  }, r = (s) => s.endsWith("_status") && !/_(ph|orp|free_chlorine|tac|cya|hardness|salt|tds)_status$/.test(s);
  if (e.device_id && o.entities) {
    for (const s of Object.values(o.entities))
      if (s.device_id === e.device_id)
        for (const [n, a] of Object.entries(i))
          t[n] || (n === "status" ? r(s.entity_id) && (t[n] = s.entity_id) : s.entity_id.endsWith(a) && (t[n] = s.entity_id));
  }
  return t;
}
function v(o, e) {
  if (e)
    return o.states[e];
}
function Zt(o) {
  if (!o || E(o)) return "unknown";
  const e = o.state.toLowerCase();
  return e === "ok" || e === "warning" || e === "critical" ? e : "unknown";
}
const Jt = {
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
function Xt(o) {
  return Jt[o];
}
const ei = {
  temperature: { icon: "🌡️", label: "Temp", fractionDigits: 1, unitFallback: "°C" },
  ph: { icon: "⚗️", label: "pH", fractionDigits: 1, unitFallback: "" },
  free_chlorine: { icon: "🧪", label: "Cl", fractionDigits: 1, unitFallback: "mg/L" },
  orp: { icon: "⚡", label: "ORP", fractionDigits: 0, unitFallback: "mV" }
};
function ti(o) {
  return ei[o];
}
function ii(o, e, t) {
  if (E(o)) return T;
  const i = o.state, r = Number(i), s = o.attributes.unit_of_measurement ?? t;
  return Number.isFinite(r) ? `${r.toFixed(e)}${s ? ` ${s}` : ""}`.trim() : `${i}${s ? ` ${s}` : ""}`.trim();
}
function ri(o, e, t) {
  if (o.metrics?.length) return o.metrics;
  const i = ["temperature", "ph", "free_chlorine"], r = v(t, e.free_chlorine);
  return E(r) && e.orp && !E(v(t, e.orp)) ? ["temperature", "ph", "orp"] : i;
}
function oi(o) {
  return o >= 80 ? "good" : o >= 50 ? "warn" : "bad";
}
function ct(o) {
  if (!o) return { count: 0, list: [] };
  const e = Number(o.state), t = o.attributes.recommendations ?? [];
  return { count: Number.isFinite(e) ? e : t.length, list: t };
}
const si = {
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
function te(o) {
  return si[o];
}
const ke = {
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
function lt(o, e) {
  return e ? `${o} ${e}` : o;
}
function ni(o, e) {
  if (e === null || !Number.isFinite(e)) return T;
  if (o === null) return String(e);
  const t = ke[o];
  return t ? lt(e.toFixed(t.fractionDigits), t.unit) : String(e);
}
function ai(o, e) {
  if (!e || e.length !== 2) return T;
  const [t, i] = e;
  if (!Number.isFinite(t) || !Number.isFinite(i)) return T;
  if (o === null) return `${t}–${i}`;
  const r = ke[o];
  if (!r) return `${t}–${i}`;
  const s = t.toFixed(r.fractionDigits), n = i.toFixed(r.fractionDigits);
  return lt(`${s}–${n}`, r.unit);
}
function ci(o) {
  return o === null ? "" : ke[o]?.label ?? o;
}
function Ge(o) {
  if (!o || E(o))
    return { count: 0, list: [], worst: "ok" };
  const e = o.attributes.problems ?? [], t = Number(o.state), i = Number.isFinite(t) ? t : e.length, s = o.attributes.worst_severity ?? e[0]?.severity ?? "ok";
  return { count: i, list: e, worst: s };
}
function li(o) {
  return o.treatments ?? o.actions ?? [];
}
const di = {
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
function dt(o) {
  if (o.priority) return o.priority;
  switch (o.severity) {
    case "critical":
      return "critical";
    case "medium":
      return "medium";
    default:
      return "low";
  }
}
function pi(o) {
  const e = dt(o);
  return { key: e, ...di[e] };
}
function ui(o, e) {
  if (e.entity) return e.entity;
  if (!(!e.device_id || !o.entities)) {
    for (const t of Object.values(o.entities))
      if (t.device_id === e.device_id && t.entity_id.endsWith("_recommendations"))
        return t.entity_id;
  }
}
var hi = Object.defineProperty, pt = (o, e, t, i) => {
  for (var r = void 0, s = o.length - 1, n; s >= 0; s--)
    (n = o[s]) && (r = n(e, t, r) || r);
  return r && hi(e, t, r), r;
};
const me = "poolman-pool-overview-card", Te = class Te extends _ {
  /** Lovelace card size hint (1 unit ≈ 50px). */
  getCardSize() {
    return 3;
  }
  static getStubConfig(e) {
    const t = J(e);
    return {
      type: `custom:${me}`,
      ...t ? { device_id: t } : {}
    };
  }
  static async getConfigElement() {
    return await Promise.resolve().then(() => Ni), document.createElement("poolman-pool-overview-card-editor");
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
    if (!this._config || !this.hass) return c;
    const e = oe(this.hass, this._config), t = v(this.hass, e.status), i = Zt(t), r = Xt(i), s = this._config.name ?? this._deviceName(this._config.device_id) ?? "Pool", n = ri(this._config, e, this.hass);
    return l`
      <ha-card>
        <div class="header">
          <div class="title">
            <span class="pool-icon" aria-hidden="true">🏊</span>
            <span>${s}</span>
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

        ${this._config.show_score !== !1 ? this._renderScore(e.water_quality_score) : c}
        ${this._renderRecommendations(e.recommendations)}
      </ha-card>
    `;
  }
  _renderMetric(e, t) {
    const i = ti(e), r = v(this.hass, t[e]), s = ii(r, i.fractionDigits, i.unitFallback);
    return l`
      <div class="metric" data-key=${e}>
        <span class="metric-label">
          <span aria-hidden="true">${i.icon}</span>
          ${i.label}
        </span>
        <span class="metric-value">${s}</span>
      </div>
    `;
  }
  _renderScore(e) {
    const t = v(this.hass, e);
    if (E(t))
      return l`
        <div class="score">
          <div class="score-row">
            <span>Quality score</span>
            <strong>${T}</strong>
          </div>
        </div>
      `;
    const i = Math.max(0, Math.min(100, Number(t.state) || 0)), r = oi(i);
    return l`
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
    const t = v(this.hass, e);
    if (!t) return c;
    const { count: i } = ct(t), r = this._config?.recommendations_path, s = i > 0, n = i === 0 ? "Your pool is in good condition" : `${i} recommendation${i === 1 ? "" : "s"}`;
    return l`
      <div
        class="recommendations"
        role=${s ? "button" : "presentation"}
        tabindex=${s ? "0" : "-1"}
        ?disabled=${!s}
        @click=${() => s && this._openRecommendations(t.entity_id, r)}
        @keydown=${(d) => {
      s && (d.key === "Enter" || d.key === " ") && (d.preventDefault(), this._openRecommendations(t.entity_id, r));
    }}
      >
        <span class="label">
          <span aria-hidden="true">${i === 0 ? "✅" : "⚠️"}</span>
          ${n}
        </span>
        ${s ? l`<span class="chevron" aria-hidden="true">›</span>` : c}
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
Te.styles = Bt;
let F = Te;
pt([
  g({ attribute: !1 })
], F.prototype, "hass");
pt([
  m()
], F.prototype, "_config");
customElements.get(me) || customElements.define(me, F);
const mi = W`
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
var fi = Object.defineProperty, ut = (o, e, t, i) => {
  for (var r = void 0, s = o.length - 1, n; s >= 0; s--)
    (n = o[s]) && (r = n(e, t, r) || r);
  return r && fi(e, t, r), r;
};
const fe = "poolman-problem-card", We = {
  ok: {
    label: "OK",
    color: "var(--success-color, #43a047)",
    icon: "✅"
  },
  low: te("low"),
  medium: te("medium"),
  critical: te("critical")
}, Oe = class Oe extends _ {
  /** Lovelace card size hint (1 unit ≈ 50px). */
  getCardSize() {
    const e = this._resolveEntity();
    if (!e) return 1;
    const { count: t } = Ge(e);
    if (t === 0) return 1;
    const i = this._config?.max ?? t;
    return 1 + Math.min(t, i);
  }
  static getStubConfig(e) {
    const t = J(e);
    return {
      type: `custom:${fe}`,
      ...t ? { device_id: t } : {}
    };
  }
  static async getConfigElement() {
    return await Promise.resolve().then(() => zi), document.createElement("poolman-problem-card-editor");
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
    if (!this._config || !this.hass) return c;
    const e = this._resolveEntity(), t = this._config.name ?? this._deviceName() ?? "Pool Problems";
    if (!e || E(e))
      return l`
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
    const { count: i, list: r, worst: s } = Ge(e), n = We[s] ?? We.ok;
    return l`
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

        ${i === 0 ? l`
              <div class="empty" role="status">
                <span aria-hidden="true">✅</span>
                <span>No problems detected — pool is healthy</span>
              </div>
            ` : this._renderProblems(r, i)}
      </ha-card>
    `;
  }
  _renderProblems(e, t) {
    const i = this._config?.max, r = i !== void 0 ? e.slice(0, i) : e, s = Math.max(0, t - r.length);
    return l`
      <div class="problems">
        ${r.map((n) => this._renderProblem(n))}
        ${s > 0 ? l`<div class="more">
              +${s} more problem${s === 1 ? "" : "s"}
            </div>` : c}
      </div>
    `;
  }
  _renderProblem(e) {
    const t = e.severity, i = te(t), r = ci(e.metric), s = e.metric !== null && e.value !== null && e.expected_range !== null;
    return l`
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
        ${s ? l`
              <div class="details">
                ${r ? l`<span class="metric-label">${r}</span>
                      <span class="sep" aria-hidden="true">•</span>` : c}
                <span>
                  Current:
                  <strong>${ni(e.metric, e.value)}</strong>
                </span>
                <span class="sep" aria-hidden="true">—</span>
                <span>
                  Expected:
                  <strong
                    >${ai(e.metric, e.expected_range)}</strong
                  >
                </span>
              </div>
            ` : c}
      </div>
    `;
  }
  _resolveEntity() {
    if (!this.hass || !this._config) return;
    if (this._config.entity)
      return v(this.hass, this._config.entity);
    const e = oe(this.hass, {
      type: this._config.type,
      device_id: this._config.device_id
    });
    return v(this.hass, e.problems);
  }
  _deviceName() {
    const e = this._config?.device_id;
    if (!e || !this.hass?.devices) return;
    const t = this.hass.devices[e];
    if (t)
      return t.name_by_user ?? t.name ?? void 0;
  }
};
Oe.styles = mi;
let V = Oe;
ut([
  g({ attribute: !1 })
], V.prototype, "hass");
ut([
  m()
], V.prototype, "_config");
customElements.get(fe) || customElements.define(fe, V);
var _i = Object.defineProperty, ne = (o, e, t, i) => {
  for (var r = void 0, s = o.length - 1, n; s >= 0; s--)
    (n = o[s]) && (r = n(e, t, r) || r);
  return r && _i(e, t, r), r;
};
const _e = "poolman-recommendations-card", Pe = class Pe extends _ {
  constructor() {
    super(...arguments), this._dismissed = /* @__PURE__ */ new Set(), this._expanded = /* @__PURE__ */ new Set(), this._lastSeenIds = /* @__PURE__ */ new Set();
  }
  /** Lovelace card size hint (1 unit ≈ 50px). */
  getCardSize() {
    return 4;
  }
  static getStubConfig(e) {
    const t = J(e);
    return {
      type: `custom:${_e}`,
      ...t ? { device_id: t } : {}
    };
  }
  static async getConfigElement() {
    return await Promise.resolve().then(() => Mi), document.createElement("poolman-recommendations-card-editor");
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
    if (!this._config || !this.hass) return c;
    const e = ui(this.hass, this._config), t = v(this.hass, e), i = this._config.name ?? this._deviceName() ?? "Recommendations";
    if (!t || E(t))
      return l`
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
    const { count: r, list: s } = ct(t);
    this._lastSeenIds = new Set(s.map((a) => a.id));
    const n = s.filter((a) => !this._dismissed.has(a.id));
    return l`
      <ha-card>
        <div class="header">
          <div class="title">
            <span class="icon" aria-hidden="true">📋</span>
            <span>${i}</span>
          </div>
          ${r > 0 ? l`<span class="count">${n.length} / ${r}</span>` : c}
        </div>

        ${n.length === 0 ? this._renderEmpty() : l`<div class="list">${n.map((a) => this._renderRecommendation(a))}</div>`}
      </ha-card>
    `;
  }
  _renderEmpty() {
    return l`
      <div class="empty" role="status">
        <span aria-hidden="true">✅</span>
        Your pool is in good condition
      </div>
    `;
  }
  _renderRecommendation(e) {
    const t = pi(e), i = this._expanded.has(e.id), r = this._config?.show_severity !== !1, s = li(e);
    return l`
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
            ${r ? l`<span>${t.label}</span>` : c}
          </span>
          <span class="rec-text">
            <span class="rec-title">${e.title}</span>
            ${e.description ? l`<span class="rec-desc">${e.description}</span>` : c}
          </span>
          <span
            class=${`chevron ${i ? "open" : ""}`}
            aria-hidden="true"
          >›</span>
        </div>
        ${i ? this._renderDetail(e, s) : c}
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
    return l`
      <div class="rec-detail">
        ${e.reason ? l`<div class="rec-reason"><strong>Reason:</strong> ${e.reason}</div>` : c}
        ${t.length > 0 ? l`
              <ul class="treatments" aria-label="Treatments">
                ${t.map(
      (i) => l`
                    <li>
                      <span class="treatment-product">${i.name}</span>
                      <span class="treatment-qty"
                        >${this._formatQuantity(i.quantity)} ${i.unit}</span
                      >
                    </li>
                  `
    )}
              </ul>
            ` : c}
        ${e.related_metrics && e.related_metrics.length > 0 ? l`
              <div class="metrics-row">
                ${e.related_metrics.map(
      (i) => l`<span class="metric-chip">${i}</span>`
    )}
              </div>
            ` : c}
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
    (!i || i(`Apply "${e.title}"?`)) && await this._callApply(t, e.id);
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
    const i = dt(e);
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
Pe.styles = Ft;
let O = Pe;
ne([
  g({ attribute: !1 })
], O.prototype, "hass");
ne([
  m()
], O.prototype, "_config");
ne([
  m()
], O.prototype, "_dismissed");
ne([
  m()
], O.prototype, "_expanded");
customElements.get(_e) || customElements.define(_e, O);
var gi = Object.defineProperty, ht = (o, e, t, i) => {
  for (var r = void 0, s = o.length - 1, n; s >= 0; s--)
    (n = o[s]) && (r = n(e, t, r) || r);
  return r && gi(e, t, r), r;
};
const ge = "poolman-action-history-card", he = 50, vi = {
  chemical: "🧪",
  cleaning: "🧹",
  maintenance: "🔧"
}, yi = {
  chemical: "Chemical treatment",
  cleaning: "Cleaning",
  maintenance: "Maintenance"
}, bi = {
  user: "Manual",
  recommendation: "Recommendation",
  automation: "Automation"
};
function $i(o) {
  if (o.type !== "chemical" || !Number.isFinite(o.quantity)) return T;
  const e = Number.isInteger(o.quantity) ? o.quantity.toString() : o.quantity.toFixed(1);
  return o.unit ? `${e} ${o.unit}` : e;
}
function I(o) {
  return `${o.getFullYear()}-${String(o.getMonth() + 1).padStart(2, "0")}-${String(
    o.getDate()
  ).padStart(2, "0")}`;
}
const Re = class Re extends _ {
  /** Lovelace card size hint (1 unit ≈ 50px). */
  getCardSize() {
    return 4;
  }
  static getStubConfig(e) {
    const t = J(e);
    return {
      type: `custom:${ge}`,
      ...t ? { device_id: t } : {}
    };
  }
  static async getConfigElement() {
    return await Promise.resolve().then(() => Ui), document.createElement("poolman-action-history-card-editor");
  }
  setConfig(e) {
    if (!e)
      throw new Error("Invalid configuration");
    if (!e.device_id && !e.entities?.action_history)
      throw new Error(
        "poolman-action-history-card: either `device_id` or `entities.action_history` must be provided"
      );
    const t = e.limit, i = typeof t == "number" && t > 0 ? Math.min(Math.floor(t), he) : he;
    this._config = {
      show_source: !0,
      group_by_day: !0,
      ...e,
      limit: i
    };
  }
  render() {
    if (!this._config || !this.hass) return c;
    const t = oe(this.hass, this._config).action_history, i = v(this.hass, t), r = this._readActions(i), s = this._config.name ?? this._deviceName(this._config.device_id) ?? "Pool";
    return l`
      <ha-card>
        <div class="header">
          <div class="title">
            <span class="header-icon" aria-hidden="true">📋</span>
            <span>${s} — Action history</span>
          </div>
          ${r.length > 0 ? l`<span class="total">${r.length}</span>` : c}
        </div>

        ${r.length === 0 ? l`<div class="empty">No actions recorded yet</div>` : l`<div class="timeline">${this._renderTimeline(r)}</div>`}
      </ha-card>
    `;
  }
  _readActions(e) {
    if (!e) return [];
    const t = e.attributes.actions;
    if (!Array.isArray(t)) return [];
    const i = this._config?.limit ?? he;
    return t.filter((r) => r && typeof r.timestamp == "string").slice().sort((r, s) => r.timestamp < s.timestamp ? 1 : -1).slice(0, i);
  }
  _renderTimeline(e) {
    if (!(this._config?.group_by_day !== !1))
      return e.map((s) => this._renderRow(s));
    const i = [];
    let r;
    for (const s of e) {
      const n = new Date(s.timestamp), a = I(n);
      a !== r && (r = a, i.push(
        l`<div class="day-header">${this._formatDayHeader(n)}</div>`
      )), i.push(this._renderRow(s));
    }
    return i;
  }
  _renderRow(e) {
    const t = vi[e.type] ?? "•", i = yi[e.type] ?? e.type, r = bi[e.source] ?? e.source, s = $i(e), n = !!e.recommendation_id, a = this._formatTime(new Date(e.timestamp)), d = () => this._openAction(e);
    return l`
      <div
        class="action-row ${n ? "interactive" : ""}"
        data-type=${e.type}
        data-source=${e.source}
        role=${n ? "button" : "presentation"}
        tabindex=${n ? "0" : "-1"}
        @click=${n ? d : c}
        @keydown=${n ? (p) => {
      (p.key === "Enter" || p.key === " ") && (p.preventDefault(), d());
    } : c}
      >
        <span class="action-icon" aria-hidden="true">${t}</span>
        <div class="action-body">
          <span class="action-title">
            ${i}${e.treatment_id ? l` · ${e.treatment_id}` : c}
          </span>
          <span class="action-meta">
            <span class="quantity">${s}</span>
            ${this._config?.show_source !== !1 ? l`<span class="source-badge ${e.source}">${r}</span>` : c}
          </span>
        </div>
        <span class="action-time">${a}</span>
      </div>
    `;
  }
  _openAction(e) {
    const t = oe(this.hass, this._config), i = t.recommendations ?? t.action_history;
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
    if (i.setDate(t.getDate() - 1), I(e) === I(t)) return "Today";
    if (I(e) === I(i)) return "Yesterday";
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
Re.styles = Vt;
let G = Re;
ht([
  g({ attribute: !1 })
], G.prototype, "hass");
ht([
  m()
], G.prototype, "_config");
customElements.get(ge) || customElements.define(ge, G);
const xi = W`
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
`, wi = ["g", "kg", "mL", "L", "tablet"];
var Ei = Object.defineProperty, P = (o, e, t, i) => {
  for (var r = void 0, s = o.length - 1, n; s >= 0; s--)
    (n = o[s]) && (r = n(e, t, r) || r);
  return r && Ei(e, t, r), r;
};
const ve = "poolman-quick-actions-card", Ai = "poolman", Si = "analyze", Ci = "boost_filtration", ki = "record_action", Ti = 1500, Oi = 3e3, Ye = {
  type: "chemical",
  product_id: "",
  quantity: "",
  unit: "",
  note: ""
}, Ne = class Ne extends _ {
  constructor() {
    super(...arguments), this._states = {}, this._errors = {}, this._dialogOpen = !1, this._draft = { ...Ye }, this._validationError = "", this._resetTimers = {};
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
    const t = J(e);
    return {
      type: `custom:${ve}`,
      device_id: t ?? ""
    };
  }
  static async getConfigElement() {
    return await Promise.resolve().then(() => Hi), document.createElement("poolman-quick-actions-card-editor");
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
    if (!this._config || !this.hass) return c;
    const e = this.hass.locale?.language, t = this._config.name ?? this._deviceName(this._config.device_id) ?? u(e, "card_name"), i = typeof this.hass.callService == "function";
    return l`
      <ha-card>
        <div class="header">${t}</div>
        ${i ? c : l`<div class="qa-notice" role="status">
              ${u(e, "service_unavailable")}
            </div>`}
        <div class="buttons">
          ${this._config.analyze !== !1 ? this._renderButton(
      "analyze",
      "🔍",
      "analyze",
      "analyze_aria",
      () => this._invokeAnalyze()
    ) : c}
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
    ] : c}
          ${this._config.record !== !1 ? this._renderButton(
      "record",
      "🧪",
      "record",
      "record_aria",
      () => this._openDialog()
    ) : c}
          ${this._renderErrors()}
        </div>
        ${this._dialogOpen ? this._renderDialog() : c}
      </ha-card>
    `;
  }
  // ---- button rendering ----------------------------------------------------
  _renderButton(e, t, i, r, s) {
    const n = this.hass?.locale?.language, a = this._states[e] ?? "idle", d = a === "pending" || typeof this.hass?.callService != "function", p = a === "pending" ? u(n, "pending") : a === "success" ? u(n, "success") : u(n, i);
    return l`
      <button
        type="button"
        class="qa-btn"
        data-action=${e}
        data-state=${a}
        aria-label=${u(n, r)}
        ?disabled=${d}
        @click=${s}
      >
        ${a === "pending" ? l`<span class="qa-spinner" aria-hidden="true"></span>` : l`<span class="qa-icon" aria-hidden="true">${t}</span>`}
        <span class="qa-label">${p}</span>
      </button>
    `;
  }
  _renderErrors() {
    const e = Object.entries(this._errors).filter(
      ([, t]) => !!t
    );
    return e.length === 0 ? c : e.map(
      ([t, i]) => l`
        <div class="qa-error-message" role="alert" data-action=${t}>
          ${i}
        </div>
      `
    );
  }
  // ---- dialog rendering ----------------------------------------------------
  _renderDialog() {
    const e = this.hass?.locale?.language, t = this._states.record === "pending";
    return l`
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
          aria-label=${u(e, "dialog_title")}
        >
          <h2>${u(e, "dialog_title")}</h2>

          <div class="qa-field">
            <label for="qa-type">${u(e, "dialog_type")}</label>
            <select
              id="qa-type"
              .value=${this._draft.type}
              @change=${(i) => this._updateDraft({
      type: i.target.value
    })}
            >
              <option value="chemical">
                ${u(e, "dialog_type_chemical")}
              </option>
              <option value="cleaning">
                ${u(e, "dialog_type_cleaning")}
              </option>
              <option value="maintenance">
                ${u(e, "dialog_type_maintenance")}
              </option>
            </select>
          </div>

          <div class="qa-field">
            <label for="qa-product">${u(e, "dialog_product_id")}</label>
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
            <label for="qa-quantity">${u(e, "dialog_quantity")}</label>
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
            <label for="qa-unit">${u(e, "dialog_unit")}</label>
            <select
              id="qa-unit"
              .value=${this._draft.unit}
              @change=${(i) => this._updateDraft({
      unit: i.target.value
    })}
            >
              <option value="">${u(e, "dialog_unit_none")}</option>
              ${wi.map(
      (i) => l`<option value=${i}>${i}</option>`
    )}
            </select>
          </div>

          <div class="qa-field">
            <label for="qa-note">${u(e, "dialog_note")}</label>
            <textarea
              id="qa-note"
              .value=${this._draft.note}
              @input=${(i) => this._updateDraft({
      note: i.target.value
    })}
            ></textarea>
          </div>

          ${this._validationError ? l`<div class="qa-validation" role="alert">
                ${this._validationError}
              </div>` : c}

          <div class="qa-dialog-actions">
            <button
              type="button"
              ?disabled=${t}
              @click=${() => this._closeDialog()}
            >
              ${u(e, "dialog_cancel")}
            </button>
            <button
              type="button"
              class="primary"
              ?disabled=${t}
              @click=${() => this._submitDialog()}
            >
              ${u(e, "dialog_submit")}
            </button>
          </div>
        </div>
      </div>
    `;
  }
  // ---- service calls -------------------------------------------------------
  async _invokeAnalyze() {
    const e = this._config?.device_id;
    e && await this._runService("analyze", Si, { device_id: e });
  }
  async _invokeBoost(e, t) {
    const i = this._config?.device_id;
    i && await this._runService(t, Ci, { device_id: i, hours: e });
  }
  async _runService(e, t, i) {
    const r = this.hass?.callService;
    if (typeof r != "function") return !1;
    this._clearError(e), this._setState(e, "pending");
    try {
      return await r(Ai, t, i), this._setState(e, "success"), this._scheduleReset(e, Ti), !0;
    } catch (s) {
      const n = this.hass?.locale?.language, a = s instanceof Error && s.message ? s.message : u(n, "error_generic");
      return this._setError(e, a), this._setState(e, "error"), this._scheduleReset(e, Oi), !1;
    }
  }
  // ---- dialog state --------------------------------------------------------
  _openDialog() {
    this._draft = { ...Ye }, this._validationError = "", this._clearError("record"), this._dialogOpen = !0;
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
    const s = this._draft.quantity.trim();
    if (s !== "") {
      const p = Number(s);
      if (!Number.isFinite(p) || p < 0) {
        this._validationError = u(e, "dialog_validation_quantity");
        return;
      }
      i.quantity = p;
    }
    const n = this._draft.unit.trim();
    n && r && (i.unit = n);
    const a = this._draft.note.trim();
    a && (i.note = a), await this._runService("record", ki, i) && this._closeDialog();
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
Ne.styles = xi;
let y = Ne;
P([
  g({ attribute: !1 })
], y.prototype, "hass");
P([
  m()
], y.prototype, "_config");
P([
  m()
], y.prototype, "_states");
P([
  m()
], y.prototype, "_errors");
P([
  m()
], y.prototype, "_dialogOpen");
P([
  m()
], y.prototype, "_draft");
P([
  m()
], y.prototype, "_validationError");
customElements.get(ve) || customElements.define(ve, y);
var Pi = Object.defineProperty, mt = (o, e, t, i) => {
  for (var r = void 0, s = o.length - 1, n; s >= 0; s--)
    (n = o[s]) && (r = n(e, t, r) || r);
  return r && Pi(e, t, r), r;
};
const ye = "poolman-pool-overview-card-editor", Ri = [
  { value: "temperature", label_key: "editor_metric_temperature" },
  { value: "ph", label_key: "editor_metric_ph" },
  { value: "free_chlorine", label_key: "editor_metric_free_chlorine" },
  { value: "orp", label_key: "editor_metric_orp" }
];
class ae extends _ {
  constructor() {
    super(...arguments), this._onValueChanged = (e) => {
      if (e.stopPropagation(), !this._config) return;
      const t = { ...this._config, ...e.detail.value };
      this._config = t, Q(this, t);
    };
  }
  setConfig(e) {
    this._config = { ...e };
  }
  render() {
    if (!this._config) return c;
    const e = this.hass?.locale?.language, t = [
      { name: "device_id", selector: Z },
      { name: "name", selector: z },
      {
        name: "metrics",
        selector: {
          select: {
            multiple: !0,
            mode: "list",
            options: Ri.map((i) => ({
              value: i.value,
              label: u(e, i.label_key)
            }))
          }
        }
      },
      { name: "show_score", selector: C, default: !0 },
      { name: "recommendations_path", selector: z }
    ];
    return l`
      <ha-form
        .hass=${this.hass}
        .data=${this._config}
        .schema=${t}
        .computeLabel=${K(e)}
        @value-changed=${this._onValueChanged}
      ></ha-form>
    `;
  }
}
mt([
  g({ attribute: !1 })
], ae.prototype, "hass");
mt([
  m()
], ae.prototype, "_config");
customElements.get(ye) || customElements.define(ye, ae);
const Ni = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  POOL_OVERVIEW_EDITOR_TAG: ye,
  PoolmanPoolOverviewCardEditor: ae
}, Symbol.toStringTag, { value: "Module" }));
var qi = Object.defineProperty, ft = (o, e, t, i) => {
  for (var r = void 0, s = o.length - 1, n; s >= 0; s--)
    (n = o[s]) && (r = n(e, t, r) || r);
  return r && qi(e, t, r), r;
};
const be = "poolman-problem-card-editor";
class ce extends _ {
  constructor() {
    super(...arguments), this._onValueChanged = (e) => {
      if (e.stopPropagation(), !this._config) return;
      const t = { ...this._config, ...e.detail.value };
      this._config = t, Q(this, t);
    };
  }
  setConfig(e) {
    this._config = { ...e };
  }
  render() {
    if (!this._config) return c;
    const e = this.hass?.locale?.language, t = [
      { name: "device_id", selector: Z },
      { name: "entity", selector: nt("sensor") },
      { name: "name", selector: z },
      { name: "max", selector: at(1, 50, 1) }
    ];
    return l`
      <ha-form
        .hass=${this.hass}
        .data=${this._config}
        .schema=${t}
        .computeLabel=${K(e)}
        @value-changed=${this._onValueChanged}
      ></ha-form>
    `;
  }
}
ft([
  g({ attribute: !1 })
], ce.prototype, "hass");
ft([
  m()
], ce.prototype, "_config");
customElements.get(be) || customElements.define(be, ce);
const zi = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  PROBLEM_EDITOR_TAG: be,
  PoolmanProblemCardEditor: ce
}, Symbol.toStringTag, { value: "Module" }));
var Di = Object.defineProperty, _t = (o, e, t, i) => {
  for (var r = void 0, s = o.length - 1, n; s >= 0; s--)
    (n = o[s]) && (r = n(e, t, r) || r);
  return r && Di(e, t, r), r;
};
const $e = "poolman-recommendations-card-editor", Ii = ["never", "always", "critical_high"];
class le extends _ {
  constructor() {
    super(...arguments), this._onValueChanged = (e) => {
      if (e.stopPropagation(), !this._config) return;
      const t = {
        ...this._config,
        ...e.detail.value
      };
      this._config = t, Q(this, t);
    };
  }
  setConfig(e) {
    const t = e.confirm_apply ?? "critical_high";
    this._config = {
      show_severity: e.show_severity ?? !0,
      ...e,
      confirm_apply: t
    };
  }
  render() {
    if (!this._config) return c;
    const e = this.hass?.locale?.language, t = [
      { name: "device_id", selector: Z },
      { name: "entity", selector: nt("sensor") },
      { name: "name", selector: z },
      { name: "show_severity", selector: C, default: !0 },
      {
        name: "confirm_apply",
        selector: {
          select: {
            mode: "dropdown",
            options: Ii.map((i) => ({
              value: i,
              label: u(e, `editor_confirm_apply_${i}`)
            }))
          }
        },
        default: "critical_high"
      }
    ];
    return l`
      <ha-form
        .hass=${this.hass}
        .data=${this._config}
        .schema=${t}
        .computeLabel=${K(e)}
        @value-changed=${this._onValueChanged}
      ></ha-form>
    `;
  }
}
_t([
  g({ attribute: !1 })
], le.prototype, "hass");
_t([
  m()
], le.prototype, "_config");
customElements.get($e) || customElements.define($e, le);
const Mi = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  PoolmanRecommendationsCardEditor: le,
  RECOMMENDATIONS_EDITOR_TAG: $e
}, Symbol.toStringTag, { value: "Module" }));
var Li = Object.defineProperty, gt = (o, e, t, i) => {
  for (var r = void 0, s = o.length - 1, n; s >= 0; s--)
    (n = o[s]) && (r = n(e, t, r) || r);
  return r && Li(e, t, r), r;
};
const xe = "poolman-action-history-card-editor";
class de extends _ {
  constructor() {
    super(...arguments), this._onValueChanged = (e) => {
      if (e.stopPropagation(), !this._config) return;
      const t = { ...this._config, ...e.detail.value };
      this._config = t, Q(this, t);
    };
  }
  setConfig(e) {
    this._config = {
      show_source: e.show_source ?? !0,
      group_by_day: e.group_by_day ?? !0,
      ...e
    };
  }
  render() {
    if (!this._config) return c;
    const e = this.hass?.locale?.language, t = [
      { name: "device_id", selector: Z },
      { name: "name", selector: z },
      { name: "limit", selector: at(1, 50, 1) },
      { name: "show_source", selector: C, default: !0 },
      { name: "group_by_day", selector: C, default: !0 }
    ];
    return l`
      <ha-form
        .hass=${this.hass}
        .data=${this._config}
        .schema=${t}
        .computeLabel=${K(e)}
        @value-changed=${this._onValueChanged}
      ></ha-form>
    `;
  }
}
gt([
  g({ attribute: !1 })
], de.prototype, "hass");
gt([
  m()
], de.prototype, "_config");
customElements.get(xe) || customElements.define(xe, de);
const Ui = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  ACTION_HISTORY_EDITOR_TAG: xe,
  PoolmanActionHistoryCardEditor: de
}, Symbol.toStringTag, { value: "Module" }));
var ji = Object.defineProperty, vt = (o, e, t, i) => {
  for (var r = void 0, s = o.length - 1, n; s >= 0; s--)
    (n = o[s]) && (r = n(e, t, r) || r);
  return r && ji(e, t, r), r;
};
const we = "poolman-quick-actions-card-editor";
class pe extends _ {
  constructor() {
    super(...arguments), this._onValueChanged = (e) => {
      if (e.stopPropagation(), !this._config) return;
      const t = { ...this._config, ...e.detail.value };
      this._config = t, Q(this, t);
    };
  }
  setConfig(e) {
    this._config = {
      analyze: e.analyze ?? !0,
      boost: e.boost ?? !0,
      record: e.record ?? !0,
      ...e
    };
  }
  render() {
    if (!this._config) return c;
    const e = this.hass?.locale?.language, t = [
      { name: "device_id", required: !0, selector: Z },
      { name: "name", selector: z },
      { name: "analyze", selector: C, default: !0 },
      { name: "boost", selector: C, default: !0 },
      { name: "record", selector: C, default: !0 }
    ], i = !this._config.device_id;
    return l`
      <ha-form
        .hass=${this.hass}
        .data=${this._config}
        .schema=${t}
        .computeLabel=${K(e)}
        @value-changed=${this._onValueChanged}
      ></ha-form>
      <p
        class="poolman-editor-error"
        role="alert"
        ?hidden=${!i}
      >
        ${u(e, "editor_device_required")}
      </p>
    `;
  }
}
vt([
  g({ attribute: !1 })
], pe.prototype, "hass");
vt([
  m()
], pe.prototype, "_config");
customElements.get(we) || customElements.define(we, pe);
const Hi = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  PoolmanQuickActionsCardEditor: pe,
  QUICK_ACTIONS_EDITOR_TAG: we
}, Symbol.toStringTag, { value: "Module" })), Qe = "poolman-pool-overview-card", Ke = "poolman-problem-card", Ze = "poolman-recommendations-card", Je = "poolman-action-history-card", Xe = "poolman-quick-actions-card", Bi = "0.1.0";
window.customCards = window.customCards ?? [];
window.customCards.some((o) => o.type === Qe) || window.customCards.push({
  type: Qe,
  name: "Pool Overview",
  description: "Glanceable summary card for a Pool Manager pool: status badge, key chemistry metrics, water quality score and recommendation count.",
  preview: !0,
  documentationURL: "https://noirbizarre.github.io/hass-poolman/pool-overview-card/"
});
window.customCards.some((o) => o.type === Ke) || window.customCards.push({
  type: Ke,
  name: "Pool Problems",
  description: "Diagnostic card listing the current pool problems by severity, with measured value and expected range.",
  preview: !0,
  documentationURL: "https://noirbizarre.github.io/hass-poolman/problem-card/"
});
window.customCards.some((o) => o.type === Ze) || window.customCards.push({
  type: Ze,
  name: "Pool Recommendations",
  description: "Actionable pool recommendation list: severity badges, expandable details, and one-tap Apply / Ignore buttons backed by the poolman.apply_recommendation service.",
  preview: !0,
  documentationURL: "https://noirbizarre.github.io/hass-poolman/recommendations-card/"
});
window.customCards.some((o) => o.type === Je) || window.customCards.push({
  type: Je,
  name: "Pool Action History",
  description: "Chronological timeline of recorded pool actions (chemical treatments, cleaning, maintenance) with source badges.",
  preview: !0,
  documentationURL: "https://noirbizarre.github.io/hass-poolman/action-history-card/"
});
window.customCards.some((o) => o.type === Xe) || window.customCards.push({
  type: Xe,
  name: "Pool Quick Actions",
  description: "One-tap access to common pool operations: trigger analysis, boost filtration and record a treatment.",
  preview: !0,
  documentationURL: "https://noirbizarre.github.io/hass-poolman/quick-actions-card/"
});
console.info(
  `%c POOLMAN-CARDS %c v${Bi} `,
  "color: white; background: #03a9f4; font-weight: 700;",
  "color: #03a9f4; background: transparent; font-weight: 700;"
);
//# sourceMappingURL=poolman-cards.js.map
