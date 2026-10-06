var e=globalThis,t=e.ShadowRoot&&(e.ShadyCSS===void 0||e.ShadyCSS.nativeShadow)&&`adoptedStyleSheets`in Document.prototype&&`replace`in CSSStyleSheet.prototype,n=Symbol(),r=new WeakMap,i=class{constructor(e,t,r){if(this._$cssResult$=!0,r!==n)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=e,this.t=t}get styleSheet(){let e=this.o,n=this.t;if(t&&e===void 0){let t=n!==void 0&&n.length===1;t&&(e=r.get(n)),e===void 0&&((this.o=e=new CSSStyleSheet).replaceSync(this.cssText),t&&r.set(n,e))}return e}toString(){return this.cssText}},a=e=>new i(typeof e==`string`?e:e+``,void 0,n),o=(e,...t)=>new i(e.length===1?e[0]:t.reduce((t,n,r)=>t+(e=>{if(!0===e._$cssResult$)return e.cssText;if(typeof e==`number`)return e;throw Error(`Value passed to 'css' function must be a 'css' function result: `+e+`. Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.`)})(n)+e[r+1],e[0]),e,n),s=(n,r)=>{if(t)n.adoptedStyleSheets=r.map(e=>e instanceof CSSStyleSheet?e:e.styleSheet);else for(let t of r){let r=document.createElement(`style`),i=e.litNonce;i!==void 0&&r.setAttribute(`nonce`,i),r.textContent=t.cssText,n.appendChild(r)}},c=t?e=>e:e=>e instanceof CSSStyleSheet?(e=>{let t=``;for(let n of e.cssRules)t+=n.cssText;return a(t)})(e):e,{is:l,defineProperty:u,getOwnPropertyDescriptor:d,getOwnPropertyNames:f,getOwnPropertySymbols:p,getPrototypeOf:m}=Object,h=globalThis,g=h.trustedTypes,ee=g?g.emptyScript:``,te=h.reactiveElementPolyfillSupport,_=(e,t)=>e,v={toAttribute(e,t){switch(t){case Boolean:e=e?ee:null;break;case Object:case Array:e=e==null?e:JSON.stringify(e)}return e},fromAttribute(e,t){let n=e;switch(t){case Boolean:n=e!==null;break;case Number:n=e===null?null:Number(e);break;case Object:case Array:try{n=JSON.parse(e)}catch{n=null}}return n}},ne=(e,t)=>!l(e,t),re={attribute:!0,type:String,converter:v,reflect:!1,useDefault:!1,hasChanged:ne};Symbol.metadata??=Symbol(`metadata`),h.litPropertyMetadata??=new WeakMap;var y=class extends HTMLElement{static addInitializer(e){this._$Ei(),(this.l??=[]).push(e)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(e,t=re){if(t.state&&(t.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(e)&&((t=Object.create(t)).wrapped=!0),this.elementProperties.set(e,t),!t.noAccessor){let n=Symbol(),r=this.getPropertyDescriptor(e,n,t);r!==void 0&&u(this.prototype,e,r)}}static getPropertyDescriptor(e,t,n){let{get:r,set:i}=d(this.prototype,e)??{get(){return this[t]},set(e){this[t]=e}};return{get:r,set(t){let a=r?.call(this);i?.call(this,t),this.requestUpdate(e,a,n)},configurable:!0,enumerable:!0}}static getPropertyOptions(e){return this.elementProperties.get(e)??re}static _$Ei(){if(this.hasOwnProperty(_(`elementProperties`)))return;let e=m(this);e.finalize(),e.l!==void 0&&(this.l=[...e.l]),this.elementProperties=new Map(e.elementProperties)}static finalize(){if(this.hasOwnProperty(_(`finalized`)))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(_(`properties`))){let e=this.properties,t=[...f(e),...p(e)];for(let n of t)this.createProperty(n,e[n])}let e=this[Symbol.metadata];if(e!==null){let t=litPropertyMetadata.get(e);if(t!==void 0)for(let[e,n]of t)this.elementProperties.set(e,n)}this._$Eh=new Map;for(let[e,t]of this.elementProperties){let n=this._$Eu(e,t);n!==void 0&&this._$Eh.set(n,e)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(e){let t=[];if(Array.isArray(e)){let n=new Set(e.flat(1/0).reverse());for(let e of n)t.unshift(c(e))}else e!==void 0&&t.push(c(e));return t}static _$Eu(e,t){let n=t.attribute;return!1===n?void 0:typeof n==`string`?n:typeof e==`string`?e.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(e=>this.enableUpdating=e),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(e=>e(this))}addController(e){(this._$EO??=new Set).add(e),this.renderRoot!==void 0&&this.isConnected&&e.hostConnected?.()}removeController(e){this._$EO?.delete(e)}_$E_(){let e=new Map,t=this.constructor.elementProperties;for(let n of t.keys())this.hasOwnProperty(n)&&(e.set(n,this[n]),delete this[n]);e.size>0&&(this._$Ep=e)}createRenderRoot(){let e=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return s(e,this.constructor.elementStyles),e}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(e=>e.hostConnected?.())}enableUpdating(e){}disconnectedCallback(){this._$EO?.forEach(e=>e.hostDisconnected?.())}attributeChangedCallback(e,t,n){this._$AK(e,n)}_$ET(e,t){let n=this.constructor.elementProperties.get(e),r=this.constructor._$Eu(e,n);if(r!==void 0&&!0===n.reflect){let i=(n.converter?.toAttribute===void 0?v:n.converter).toAttribute(t,n.type);this._$Em=e,i==null?this.removeAttribute(r):this.setAttribute(r,i),this._$Em=null}}_$AK(e,t){let n=this.constructor,r=n._$Eh.get(e);if(r!==void 0&&this._$Em!==r){let e=n.getPropertyOptions(r),i=typeof e.converter==`function`?{fromAttribute:e.converter}:e.converter?.fromAttribute===void 0?v:e.converter;this._$Em=r;let a=i.fromAttribute(t,e.type);this[r]=a??this._$Ej?.get(r)??a,this._$Em=null}}requestUpdate(e,t,n,r=!1,i){if(e!==void 0){let a=this.constructor;if(!1===r&&(i=this[e]),n??=a.getPropertyOptions(e),!((n.hasChanged??ne)(i,t)||n.useDefault&&n.reflect&&i===this._$Ej?.get(e)&&!this.hasAttribute(a._$Eu(e,n))))return;this.C(e,t,n)}!1===this.isUpdatePending&&(this._$ES=this._$EP())}C(e,t,{useDefault:n,reflect:r,wrapped:i},a){n&&!(this._$Ej??=new Map).has(e)&&(this._$Ej.set(e,a??t??this[e]),!0!==i||a!==void 0)||(this._$AL.has(e)||(this.hasUpdated||n||(t=void 0),this._$AL.set(e,t)),!0===r&&this._$Em!==e&&(this._$Eq??=new Set).add(e))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(e){Promise.reject(e)}let e=this.scheduleUpdate();return e!=null&&await e,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(let[e,t]of this._$Ep)this[e]=t;this._$Ep=void 0}let e=this.constructor.elementProperties;if(e.size>0)for(let[t,n]of e){let{wrapped:e}=n,r=this[t];!0!==e||this._$AL.has(t)||r===void 0||this.C(t,void 0,n,r)}}let e=!1,t=this._$AL;try{e=this.shouldUpdate(t),e?(this.willUpdate(t),this._$EO?.forEach(e=>e.hostUpdate?.()),this.update(t)):this._$EM()}catch(t){throw e=!1,this._$EM(),t}e&&this._$AE(t)}willUpdate(e){}_$AE(e){this._$EO?.forEach(e=>e.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(e)),this.updated(e)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(e){return!0}update(e){this._$Eq&&=this._$Eq.forEach(e=>this._$ET(e,this[e])),this._$EM()}updated(e){}firstUpdated(e){}};y.elementStyles=[],y.shadowRootOptions={mode:`open`},y[_(`elementProperties`)]=new Map,y[_(`finalized`)]=new Map,te?.({ReactiveElement:y}),(h.reactiveElementVersions??=[]).push(`2.1.2`);var b=globalThis,ie=e=>e,x=b.trustedTypes,ae=x?x.createPolicy(`lit-html`,{createHTML:e=>e}):void 0,S=`$lit$`,C=`lit$${Math.random().toFixed(9).slice(2)}$`,w=`?`+C,oe=`<${w}>`,T=document,E=()=>T.createComment(``),D=e=>e===null||typeof e!=`object`&&typeof e!=`function`,O=Array.isArray,se=e=>O(e)||typeof e?.[Symbol.iterator]==`function`,k="[ \t\n\f\r]",A=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,j=/-->/g,ce=/>/g,M=RegExp(`>|${k}(?:([^\\s"'>=/]+)(${k}*=${k}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`,`g`),N=/'/g,P=/"/g,F=/^(?:script|style|textarea|title)$/i,I=(e=>(t,...n)=>({_$litType$:e,strings:t,values:n}))(1),L=Symbol.for(`lit-noChange`),R=Symbol.for(`lit-nothing`),z=new WeakMap,B=T.createTreeWalker(T,129);function V(e,t){if(!O(e)||!e.hasOwnProperty(`raw`))throw Error(`invalid template strings array`);return ae===void 0?t:ae.createHTML(t)}var le=(e,t)=>{let n=e.length-1,r=[],i,a=t===2?`<svg>`:t===3?`<math>`:``,o=A;for(let t=0;t<n;t++){let n=e[t],s,c,l=-1,u=0;for(;u<n.length&&(o.lastIndex=u,c=o.exec(n),c!==null);)u=o.lastIndex,o===A?c[1]===`!--`?o=j:c[1]===void 0?c[2]===void 0?c[3]!==void 0&&(o=M):(F.test(c[2])&&(i=RegExp(`</`+c[2],`g`)),o=M):o=ce:o===M?c[0]===`>`?(o=i??A,l=-1):c[1]===void 0?l=-2:(l=o.lastIndex-c[2].length,s=c[1],o=c[3]===void 0?M:c[3]===`"`?P:N):o===P||o===N?o=M:o===j||o===ce?o=A:(o=M,i=void 0);let d=o===M&&e[t+1].startsWith(`/>`)?` `:``;a+=o===A?n+oe:l>=0?(r.push(s),n.slice(0,l)+S+n.slice(l)+C+d):n+C+(l===-2?t:d)}return[V(e,a+(e[n]||`<?>`)+(t===2?`</svg>`:t===3?`</math>`:``)),r]},H=class e{constructor({strings:t,_$litType$:n},r){let i;this.parts=[];let a=0,o=0,s=t.length-1,c=this.parts,[l,u]=le(t,n);if(this.el=e.createElement(l,r),B.currentNode=this.el.content,n===2||n===3){let e=this.el.content.firstChild;e.replaceWith(...e.childNodes)}for(;(i=B.nextNode())!==null&&c.length<s;){if(i.nodeType===1){if(i.hasAttributes())for(let e of i.getAttributeNames())if(e.endsWith(S)){let t=u[o++],n=i.getAttribute(e).split(C),r=/([.?@])?(.*)/.exec(t);c.push({type:1,index:a,name:r[2],strings:n,ctor:r[1]===`.`?de:r[1]===`?`?fe:r[1]===`@`?pe:G}),i.removeAttribute(e)}else e.startsWith(C)&&(c.push({type:6,index:a}),i.removeAttribute(e));if(F.test(i.tagName)){let e=i.textContent.split(C),t=e.length-1;if(t>0){i.textContent=x?x.emptyScript:``;for(let n=0;n<t;n++)i.append(e[n],E()),B.nextNode(),c.push({type:2,index:++a});i.append(e[t],E())}}}else if(i.nodeType===8){if(i.data===w)c.push({type:2,index:a});else{let e=-1;for(;(e=i.data.indexOf(C,e+1))!==-1;)c.push({type:7,index:a}),e+=C.length-1}}a++}}static createElement(e,t){let n=T.createElement(`template`);return n.innerHTML=e,n}};function U(e,t,n=e,r){if(t===L)return t;let i=r===void 0?n._$Cl:n._$Co?.[r],a=D(t)?void 0:t._$litDirective$;return i?.constructor!==a&&(i?._$AO?.(!1),a===void 0?i=void 0:(i=new a(e),i._$AT(e,n,r)),r===void 0?n._$Cl=i:(n._$Co??=[])[r]=i),i!==void 0&&(t=U(e,i._$AS(e,t.values),i,r)),t}var ue=class{constructor(e,t){this._$AV=[],this._$AN=void 0,this._$AD=e,this._$AM=t}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(e){let{el:{content:t},parts:n}=this._$AD,r=(e?.creationScope??T).importNode(t,!0);B.currentNode=r;let i=B.nextNode(),a=0,o=0,s=n[0];for(;s!==void 0;){if(a===s.index){let t;s.type===2?t=new W(i,i.nextSibling,this,e):s.type===1?t=new s.ctor(i,s.name,s.strings,this,e):s.type===6&&(t=new me(i,this,e)),this._$AV.push(t),s=n[++o]}a!==s?.index&&(i=B.nextNode(),a++)}return B.currentNode=T,r}p(e){let t=0;for(let n of this._$AV)n!==void 0&&(n.strings===void 0?n._$AI(e[t]):(n._$AI(e,n,t),t+=n.strings.length-2)),t++}},W=class e{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(e,t,n,r){this.type=2,this._$AH=R,this._$AN=void 0,this._$AA=e,this._$AB=t,this._$AM=n,this.options=r,this._$Cv=r?.isConnected??!0}get parentNode(){let e=this._$AA.parentNode,t=this._$AM;return t!==void 0&&e?.nodeType===11&&(e=t.parentNode),e}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(e,t=this){e=U(this,e,t),D(e)?e===R||e==null||e===``?(this._$AH!==R&&this._$AR(),this._$AH=R):e!==this._$AH&&e!==L&&this._(e):e._$litType$===void 0?e.nodeType===void 0?se(e)?this.k(e):this._(e):this.T(e):this.$(e)}O(e){return this._$AA.parentNode.insertBefore(e,this._$AB)}T(e){this._$AH!==e&&(this._$AR(),this._$AH=this.O(e))}_(e){this._$AH!==R&&D(this._$AH)?this._$AA.nextSibling.data=e:this.T(T.createTextNode(e)),this._$AH=e}$(e){let{values:t,_$litType$:n}=e,r=typeof n==`number`?this._$AC(e):(n.el===void 0&&(n.el=H.createElement(V(n.h,n.h[0]),this.options)),n);if(this._$AH?._$AD===r)this._$AH.p(t);else{let e=new ue(r,this),n=e.u(this.options);e.p(t),this.T(n),this._$AH=e}}_$AC(e){let t=z.get(e.strings);return t===void 0&&z.set(e.strings,t=new H(e)),t}k(t){O(this._$AH)||(this._$AH=[],this._$AR());let n=this._$AH,r,i=0;for(let a of t)i===n.length?n.push(r=new e(this.O(E()),this.O(E()),this,this.options)):r=n[i],r._$AI(a),i++;i<n.length&&(this._$AR(r&&r._$AB.nextSibling,i),n.length=i)}_$AR(e=this._$AA.nextSibling,t){for(this._$AP?.(!1,!0,t);e!==this._$AB;){let t=ie(e).nextSibling;ie(e).remove(),e=t}}setConnected(e){this._$AM===void 0&&(this._$Cv=e,this._$AP?.(e))}},G=class{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(e,t,n,r,i){this.type=1,this._$AH=R,this._$AN=void 0,this.element=e,this.name=t,this._$AM=r,this.options=i,n.length>2||n[0]!==``||n[1]!==``?(this._$AH=Array(n.length-1).fill(new String),this.strings=n):this._$AH=R}_$AI(e,t=this,n,r){let i=this.strings,a=!1;if(i===void 0)e=U(this,e,t,0),a=!D(e)||e!==this._$AH&&e!==L,a&&(this._$AH=e);else{let r=e,o,s;for(e=i[0],o=0;o<i.length-1;o++)s=U(this,r[n+o],t,o),s===L&&(s=this._$AH[o]),a||=!D(s)||s!==this._$AH[o],s===R?e=R:e!==R&&(e+=(s??``)+i[o+1]),this._$AH[o]=s}a&&!r&&this.j(e)}j(e){e===R?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,e??``)}},de=class extends G{constructor(){super(...arguments),this.type=3}j(e){this.element[this.name]=e===R?void 0:e}},fe=class extends G{constructor(){super(...arguments),this.type=4}j(e){this.element.toggleAttribute(this.name,!!e&&e!==R)}},pe=class extends G{constructor(e,t,n,r,i){super(e,t,n,r,i),this.type=5}_$AI(e,t=this){if((e=U(this,e,t,0)??R)===L)return;let n=this._$AH,r=e===R&&n!==R||e.capture!==n.capture||e.once!==n.once||e.passive!==n.passive,i=e!==R&&(n===R||r);r&&this.element.removeEventListener(this.name,this,n),i&&this.element.addEventListener(this.name,this,e),this._$AH=e}handleEvent(e){typeof this._$AH==`function`?this._$AH.call(this.options?.host??this.element,e):this._$AH.handleEvent(e)}},me=class{constructor(e,t,n){this.element=e,this.type=6,this._$AN=void 0,this._$AM=t,this.options=n}get _$AU(){return this._$AM._$AU}_$AI(e){U(this,e)}},he=b.litHtmlPolyfillSupport;he?.(H,W),(b.litHtmlVersions??=[]).push(`3.3.3`);var ge=(e,t,n)=>{let r=n?.renderBefore??t,i=r._$litPart$;if(i===void 0){let e=n?.renderBefore??null;r._$litPart$=i=new W(t.insertBefore(E(),e),e,void 0,n??{})}return i._$AI(e),i},K=globalThis,q=class extends y{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){let e=super.createRenderRoot();return this.renderOptions.renderBefore??=e.firstChild,e}update(e){let t=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(e),this._$Do=ge(t,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return L}};q._$litElement$=!0,q.finalized=!0,K.litElementHydrateSupport?.({LitElement:q});var _e=K.litElementPolyfillSupport;_e?.({LitElement:q}),(K.litElementVersions??=[]).push(`4.2.2`);var ve=[o`
  :host {
    --vault-primary: var(--primary-color, #f59e0b);
    --vault-accent: #f59e0b;
    --vault-accent-light: #fbbf24;
    --vault-accent-muted: color-mix(in srgb, #f59e0b 16%, transparent);
    --vault-success: var(--success-color, #10b981);
    --vault-success-muted: color-mix(in srgb, #10b981 16%, transparent);
    --vault-warning: var(--warning-color, #f59e0b);
    --vault-warning-muted: color-mix(in srgb, #f59e0b 16%, transparent);
    --vault-error: var(--error-color, #ef4444);
    --vault-error-muted: color-mix(in srgb, #ef4444 16%, transparent);
    --vault-info: var(--info-color, #3b82f6);
    --vault-info-muted: color-mix(in srgb, #3b82f6 16%, transparent);
    --vault-standby: var(--disabled-text-color, #71717a);
    --vault-card-bg: var(--ha-card-background, var(--card-background-color, #18181b));
    --vault-surface: var(--secondary-background-color, rgba(255, 255, 255, 0.04));
    --vault-surface-hover: rgba(255, 255, 255, 0.08);
    --vault-border: var(--ha-card-border-color, var(--divider-color, rgba(255, 255, 255, 0.08)));
    --vault-radius: var(--ha-card-border-radius, 12px);
    --vault-text: var(--primary-text-color, #f4f4f5);
    --vault-subtext: var(--secondary-text-color, #a1a1aa);
  }
`,o`
    :host {
      display: block;
      height: 100%;
      box-sizing: border-box;
    }

    ha-card {
      height: 100%;
      box-sizing: border-box;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
      overflow: hidden;
      background: var(--vault-card-bg);
      border: 1px solid var(--vault-border);
      border-radius: var(--vault-radius);
      color: var(--vault-text);
      font-family: var(--ha-card-font-family, inherit);
    }

    :host([embedded]) ha-card {
      border: none;
      box-shadow: none;
      background: transparent;
      padding: 0;
    }

    .icon {
      display: inline-block;
      vertical-align: middle;
      fill: currentColor;
      flex-shrink: 0;
    }

    /* Card Header */
    .header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
    }

    .header-main {
      display: flex;
      align-items: center;
      gap: 10px;
      min-width: 0;
    }

    .header-icon {
      width: 32px;
      height: 32px;
      border-radius: 8px;
      background: var(--vault-accent-muted);
      color: var(--vault-accent);
      display: grid;
      place-items: center;
      flex-shrink: 0;
    }

    .header-icon.success {
      background: var(--vault-success-muted);
      color: var(--vault-success);
    }

    .header-icon.error {
      background: var(--vault-error-muted);
      color: var(--vault-error);
    }

    .header-titles {
      display: flex;
      flex-direction: column;
      min-width: 0;
    }

    .header-tag {
      font-size: 0.72rem;
      font-weight: 700;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      color: var(--vault-subtext);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .header-title {
      font-size: 1.05rem;
      font-weight: 700;
      color: var(--vault-text);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      line-height: 1.25;
    }

    .header-subtitle {
      font-size: 0.75rem;
      color: var(--vault-subtext);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .header-actions {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-shrink: 0;
    }

    /* KPI Display (Health, Protected, Next run, Last backup) */
    .kpi-container {
      display: flex;
      align-items: center;
      gap: 16px;
      padding-top: 4px;
    }

    .kpi-main {
      display: flex;
      flex-direction: column;
      min-width: 0;
    }

    .kpi-value-row {
      display: flex;
      align-items: baseline;
      gap: 4px;
    }

    .kpi-value {
      font-size: 1.85rem;
      font-weight: 800;
      line-height: 1.1;
      color: var(--vault-text);
      letter-spacing: -0.02em;
    }

    .kpi-unit {
      font-size: 1rem;
      font-weight: 600;
      color: var(--vault-subtext);
    }

    .kpi-label {
      font-size: 0.82rem;
      font-weight: 600;
      color: var(--vault-text);
      margin-top: 2px;
    }

    .kpi-sub {
      font-size: 0.75rem;
      color: var(--vault-subtext);
      margin-top: 2px;
    }

    /* Circular Score Gauge */
    .score-circle {
      position: relative;
      width: 52px;
      height: 52px;
      flex-shrink: 0;
      display: grid;
      place-items: center;
    }

    .score-circle svg {
      width: 100%;
      height: 100%;
      transform: rotate(-90deg);
    }

    .score-circle circle {
      fill: none;
      stroke-width: 5;
    }

    .score-circle-bg {
      stroke: rgba(255, 255, 255, 0.08);
    }

    .score-circle-fill {
      stroke: var(--vault-success);
      stroke-linecap: round;
      transition: stroke-dashoffset 0.5s ease;
    }

    .score-text {
      position: absolute;
      font-size: 0.85rem;
      font-weight: 800;
      color: var(--vault-text);
    }

    /* Status Badges */
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      font-size: 0.72rem;
      font-weight: 600;
      padding: 3px 8px;
      border-radius: 9999px;
      line-height: 1.2;
      width: fit-content;
    }

    .badge-dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: currentColor;
    }

    .badge.success {
      background: var(--vault-success-muted);
      color: var(--vault-success);
    }

    .badge.running {
      background: var(--vault-info-muted);
      color: var(--vault-info);
    }

    .badge.warning {
      background: var(--vault-warning-muted);
      color: var(--vault-warning);
    }

    .badge.error {
      background: var(--vault-error-muted);
      color: var(--vault-error);
    }

    .badge.neutral {
      background: rgba(255, 255, 255, 0.06);
      color: var(--vault-subtext);
    }

    /* Progress bar */
    .progress-bar {
      width: 100%;
      height: 6px;
      background: rgba(255, 255, 255, 0.08);
      border-radius: 9999px;
      overflow: hidden;
      position: relative;
    }

    .progress-fill {
      height: 100%;
      background: var(--vault-success);
      border-radius: 9999px;
      transition: width 0.3s ease;
    }

    .progress-fill.running {
      background: var(--vault-info);
      background-image: linear-gradient(
        45deg,
        rgba(255, 255, 255, 0.15) 25%,
        transparent 25%,
        transparent 50%,
        rgba(255, 255, 255, 0.15) 50%,
        rgba(255, 255, 255, 0.15) 75%,
        transparent 75%,
        transparent
      );
      background-size: 16px 16px;
      animation: progress-stripes 1s linear infinite;
    }

    .progress-fill.warning {
      background: var(--vault-warning);
    }

    .progress-fill.error {
      background: var(--vault-error);
    }

    @keyframes progress-stripes {
      from {
        background-position: 16px 0;
      }
      to {
        background-position: 0 0;
      }
    }

    /* List items & Job Rows */
    .item-list {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }

    .card-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 10px 12px;
      background: var(--vault-surface);
      border: 1px solid var(--vault-border);
      border-radius: 8px;
      transition: background 0.15s ease, border-color 0.15s ease;
    }

    .card-row:hover {
      background: var(--vault-surface-hover);
    }

    .card-row-main {
      display: flex;
      flex-direction: column;
      gap: 3px;
      min-width: 0;
      flex: 1;
    }

    .card-row-title-bar {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }

    .card-row-title {
      font-size: 0.88rem;
      font-weight: 600;
      color: var(--vault-text);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .card-row-meta {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 0.75rem;
      color: var(--vault-subtext);
      flex-wrap: wrap;
    }

    .card-row-actions {
      display: flex;
      align-items: center;
      gap: 6px;
      flex-shrink: 0;
    }

    /* Action Buttons */
    .btn {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      padding: 5px 10px;
      border-radius: 6px;
      font-size: 0.75rem;
      font-weight: 600;
      cursor: pointer;
      border: 1px solid transparent;
      transition: all 0.15s ease;
      background: rgba(255, 255, 255, 0.08);
      color: var(--vault-text);
    }

    .btn:hover:not(:disabled) {
      background: rgba(255, 255, 255, 0.14);
    }

    .btn:disabled {
      opacity: 0.4;
      cursor: not-allowed;
    }

    .btn.primary {
      background: var(--vault-accent);
      color: #111116;
      border-color: var(--vault-accent);
    }

    .btn.primary:hover:not(:disabled) {
      background: var(--vault-accent-light);
      border-color: var(--vault-accent-light);
    }

    .btn.amber {
      background: color-mix(in srgb, #f59e0b 20%, transparent);
      color: var(--vault-accent);
      border-color: color-mix(in srgb, #f59e0b 30%, transparent);
    }

    .btn.amber:hover:not(:disabled) {
      background: color-mix(in srgb, #f59e0b 30%, transparent);
    }

    /* Tag Chips (Items in backup, e.g. ✓ plex, ✓ seerr) */
    .chip-container {
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
      margin-top: 4px;
    }

    .chip {
      display: inline-flex;
      align-items: center;
      gap: 3px;
      padding: 2px 6px;
      border-radius: 4px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.08);
      font-size: 0.7rem;
      color: var(--vault-subtext);
    }

    .chip.success {
      color: var(--vault-success);
    }

    /* Empty state */
    .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      text-align: center;
      padding: 20px 16px;
      color: var(--vault-subtext);
      font-size: 0.85rem;
      gap: 8px;
    }

    .empty-state-icon {
      color: var(--vault-standby);
    }
  `],J=class extends q{static styles=ve;static editorTag=``;static async getConfigElement(){return document.createElement(this.editorTag)}static properties={hass:{attribute:!1},config:{attribute:!1}};constructor(){super(),this.config={type:``}}willUpdate(e){super.willUpdate(e),e.has(`config`)&&(this.config.embedded?this.setAttribute(`embedded`,``):this.removeAttribute(`embedded`))}setConfig(e){if(!e||typeof e.type!=`string`)throw Error(`Invalid card configuration`);this.config={...e},this.config.embedded?this.setAttribute(`embedded`,``):this.removeAttribute(`embedded`)}getCardSize(){return 3}getGridOptions(){return{columns:3,rows:2,min_columns:2,min_rows:2}}getVaultDevices(){return this.hass?.devices?Object.values(this.hass.devices).filter(e=>e.identifiers?.some(([e])=>e===`vault`)):[]}getActiveDevice(){let e=this.getVaultDevices();if(e.length!==0){if(this.config.server){let t=e.find(e=>e.id===this.config.server||e.name?.toLowerCase()===this.config.server?.toLowerCase()||e.name_by_user?.toLowerCase()===this.config.server?.toLowerCase());if(t)return t}return e[0]}}getEntity(e,t=`sensor`){if(!this.hass?.states)return;let n=this.getActiveDevice()?.id;if(n&&this.hass.entities){let r=Object.values(this.hass.entities).filter(r=>r.device_id===n&&r.entity_id.startsWith(`${t}.`)&&(r.translation_key===e||r.entity_id.endsWith(`_${e}`)||r.entity_id===`${t}.${e}`));if(r.length>0&&r[0]?.entity_id){let e=this.hass.states[r[0].entity_id];if(e)return e}}for(let[r,i]of Object.entries(this.hass.states))if(r.startsWith(`${t}.`)){if(this.hass.entities){let e=this.hass.entities[r];if(e&&(n&&e.device_id&&e.device_id!==n||e.platform&&e.platform!==`vault`))continue}if(r===`${t}.vault_${e}`||r===`${t}.${e}`||r===`${t}.vault_backup_${e}`)return i}for(let[r,i]of Object.entries(this.hass.states))if(r.startsWith(`${t}.`)){if(this.hass.entities){let e=this.hass.entities[r];if(e&&(n&&e.device_id&&e.device_id!==n||e.platform&&e.platform!==`vault`))continue}if(r.endsWith(`_${e}`))return i}}getEntities(e,t=`sensor`){if(!this.hass?.states)return[];let n=[],r=this.getActiveDevice()?.id;for(let[i,a]of Object.entries(this.hass.states)){if(!i.startsWith(`${t}.`))continue;if(this.hass.entities){let e=this.hass.entities[i];if(e){if(e.platform&&e.platform!==`vault`||r&&e.device_id&&e.device_id!==r)continue}else if(!i.startsWith(`${t}.vault_`)&&!i.includes(`vault`))continue}else if(!i.startsWith(`${t}.vault_`)&&!i.includes(`vault`))continue;let o=i.slice(t.length+1);(o===e||o.startsWith(`${e}_`)||o.startsWith(`vault_${e}_`)||o.endsWith(`_${e}`)||o.includes(`_${e}_`))&&n.push(a)}return n}parseDataSizeBytes(e,t){if(e==null||e===`unavailable`||e===`unknown`)return 0;let n=Number(e);if(isNaN(n)||n<=0)return 0;let r=(t||``).toUpperCase();return r===`TB`?n*0xe8d4a51000:r===`GB`?n*1e9:r===`MB`?n*1e6:r===`KB`?n*1e3:n}formatBytes(e,t){if(e==null||e===``||e===`unavailable`||e===`unknown`)return`--`;let n=Number(e);if(isNaN(n)||n<=0)return`--`;if(t&&t!==`B`&&t!==`bytes`){let e=t.toUpperCase();if([`TB`,`GB`,`MB`,`KB`].includes(e))return`${n<10?n.toFixed(1):Math.round(n)} ${e}`}return n>=0xe8d4a51000?`${(n/0xe8d4a51000).toFixed(1)} TB`:n>=1e9?`${(n/1e9).toFixed(1)} GB`:n>=1e6?`${(n/1e6).toFixed(1)} MB`:n>=1e3?`${(n/1e3).toFixed(1)} KB`:`${Math.round(n)} B`}formatDuration(e){if(e==null||e===``||e===`unavailable`||e===`unknown`)return`--`;if(typeof e==`string`&&/[a-z]/i.test(e))return e;let t=Number(e);if(isNaN(t)||t<0)return`--`;if(t<60)return`${Math.round(t)}s`;let n=Math.floor(t/60),r=Math.round(t%60);if(n<60)return r?`${n}m ${r}s`:`${n}m`;let i=Math.floor(n/60),a=n%60;return a?`${i}h ${a}m`:`${i}h`}formatTimeAgo(e){if(!e)return`--`;try{let t=new Date(e),n=new Date().getTime()-t.getTime(),r=n<0,i=Math.floor(Math.abs(n)/1e3);if(i<60)return r?`in < 1m`:`just now`;if(i<3600){let e=Math.floor(i/60);return r?`in ${e}m`:`${e}m ago`}if(i<86400){let e=Math.floor(i/3600),t=Math.floor(i%3600/60);return r?t>0?`in ${e}h ${t}m`:`in ${e}h`:t>0?`${e}h ${t}m ago`:`${e}h ago`}let a=Math.floor(i/86400);return r?`in ${a}d`:`${a}d ago`}catch{return String(e)}}async callAction(e,t,n={}){if(this.hass)try{await this.hass.callService(e,t,n)}catch(n){throw console.error(`Failed to call ${e}.${t}:`,n),n}}};function ye(e,t,n,r){let i=new CustomEvent(t,{bubbles:r?.bubbles??!0,cancelable:!!r?.cancelable,composed:r?.composed??!0,detail:n});return e.dispatchEvent(i),i}var Y=class extends q{static properties={hass:{attribute:!1},_config:{state:!0}};static styles=o`
    .card-config {
      display: flex;
      flex-direction: column;
      gap: 14px;
      padding: 8px 0;
      color: var(--primary-text-color, #fff);
      font-size: 0.9rem;
    }
    .form-row {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    label {
      font-size: 0.8rem;
      font-weight: 600;
      color: var(--secondary-text-color, #aaa);
    }
    input[type="text"],
    select {
      padding: 8px 12px;
      border-radius: 6px;
      border: 1px solid var(--divider-color, rgba(255, 255, 255, 0.15));
      background: var(--card-background-color, #18181b);
      color: var(--primary-text-color, #fff);
      font-size: 0.85rem;
    }
    .checkbox-row {
      display: flex;
      align-items: center;
      gap: 10px;
      cursor: pointer;
    }
    .checkbox-row input {
      width: 16px;
      height: 16px;
      accent-color: var(--primary-color, #f59e0b);
    }
  `;setConfig(e){this._config={...e}}_valueChanged(e,t){if(!this._config)return;let n={...this._config,[e]:t};this._config=n,ye(this,`config-changed`,{config:n})}render(){if(!this.hass||!this._config)return I``;let e=Object.values(this.hass.devices||{}).filter(e=>e.identifiers?.some(([e])=>e===`vault`));return I`
      <div class="card-config">
        <div class="form-row">
          <label>Title (Optional)</label>
          <input
            type="text"
            .value="${this._config.title||``}"
            @input="${e=>this._valueChanged(`title`,e.target.value)}"
          />
        </div>

        ${e.length>1?I`
              <div class="form-row">
                <label>Vault Server</label>
                <select
                  @change="${e=>this._valueChanged(`server`,e.target.value)}"
                >
                  <option value="">Default (First detected)</option>
                  ${e.map(e=>I`
                      <option
                        value="${e.id}"
                        ?selected="${this._config?.server===e.id}"
                      >
                        ${e.name_by_user||e.name||e.id}
                      </option>
                    `)}
                </select>
              </div>
            `:``}
      </div>
    `}},be=`vault-health-card`,xe=`vault-health-card-editor`,Se=`vault-protected-card`,Ce=`vault-protected-card-editor`,we=`vault-next-run-card`,Te=`vault-next-run-card-editor`,Ee=`vault-last-backup-card`,De=`vault-last-backup-card-editor`,Oe=`vault-progress-card`,ke=`vault-progress-card-editor`,Ae=`vault-jobs-card`,je=`vault-jobs-card-editor`,Me=`vault-activity-card`,Ne=`vault-activity-card-editor`,Pe=`vault-storage-card`,Fe=`vault-storage-card-editor`,Ie=`vault-anomalies-card`,Le=`vault-anomalies-card-editor`,Re=`vault-rules-card`,ze=`vault-rules-card-editor`,Be=`vault-dashboard-card`,Ve=`vault-dashboard-card-editor`,He=`M12,2L1,21H23M12,6L19.53,19H4.47M11,10V14H13V10M11,16V18H13V16`,Ue=`M20,6C20.58,6 21.05,6.2 21.42,6.59C21.8,7 22,7.45 22,8V19C22,19.55 21.8,20 21.42,20.41C21.05,20.8 20.58,21 20,21H4C3.42,21 2.95,20.8 2.58,20.41C2.2,20 2,19.55 2,19V8C2,7.45 2.2,7 2.58,6.59C2.95,6.2 3.42,6 4,6H8V4C8,3.42 8.2,2.95 8.58,2.58C8.95,2.2 9.42,2 10,2H14C14.58,2 15.05,2.2 15.42,2.58C15.8,2.95 16,3.42 16,4V6H20M4,8V19H20V8H4M14,6V4H10V6H14Z`,We=`M21,7L9,19L3.5,13.5L4.91,12.09L9,16.17L19.59,5.59L21,7Z`,X=`M12 2C6.5 2 2 6.5 2 12S6.5 22 12 22 22 17.5 22 12 17.5 2 12 2M10 17L5 12L6.41 10.59L10 14.17L17.59 6.58L19 8L10 17Z`,Ge=`M12,20A8,8 0 0,0 20,12A8,8 0 0,0 12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20M12,2A10,10 0 0,1 22,12A10,10 0 0,1 12,22C6.47,22 2,17.5 2,12A10,10 0 0,1 12,2M12.5,7V12.25L17,14.92L16.25,16.15L11,13V7H12.5Z`,Ke=`M6,2A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2H6M6,4H13V9H18V20H6V4M8,12V14H16V12H8M8,16V18H13V16H8Z`,qe=`M7,5H21V7H7V5M7,13V11H21V13H7M4,4.5A1.5,1.5 0 0,1 5.5,6A1.5,1.5 0 0,1 4,7.5A1.5,1.5 0 0,1 2.5,6A1.5,1.5 0 0,1 4,4.5M4,10.5A1.5,1.5 0 0,1 5.5,12A1.5,1.5 0 0,1 4,13.5A1.5,1.5 0 0,1 2.5,12A1.5,1.5 0 0,1 4,10.5M7,19V17H21V19H7M4,16.5A1.5,1.5 0 0,1 5.5,18A1.5,1.5 0 0,1 4,19.5A1.5,1.5 0 0,1 2.5,18A1.5,1.5 0 0,1 4,16.5Z`,Je=`M6,2H18A2,2 0 0,1 20,4V20A2,2 0 0,1 18,22H6A2,2 0 0,1 4,20V4A2,2 0 0,1 6,2M12,4A6,6 0 0,0 6,10C6,13.31 8.69,16 12.1,16L11.22,13.77C10.95,13.29 11.11,12.68 11.59,12.4L12.45,11.9C12.93,11.63 13.54,11.79 13.82,12.27L15.74,14.69C17.12,13.59 18,11.9 18,10A6,6 0 0,0 12,4M12,9A1,1 0 0,1 13,10A1,1 0 0,1 12,11A1,1 0 0,1 11,10A1,1 0 0,1 12,9M7,18A1,1 0 0,0 6,19A1,1 0 0,0 7,20A1,1 0 0,0 8,19A1,1 0 0,0 7,18M12.09,13.27L14.58,19.58L17.17,18.08L12.95,12.77L12.09,13.27Z`,Ye=`M12,21.35L10.55,20.03C5.4,15.36 2,12.27 2,8.5C2,5.41 4.42,3 7.5,3C9.24,3 10.91,3.81 12,5.08C13.09,3.81 14.76,3 16.5,3C19.58,3 22,5.41 22,8.5C22,12.27 18.6,15.36 13.45,20.03L12,21.35Z`,Xe=`M8,5.14V19.14L19,12.14L8,5.14Z`,Ze=`M12,4C14.1,4 16.1,4.8 17.6,6.3C20.7,9.4 20.7,14.5 17.6,17.6C15.8,19.5 13.3,20.2 10.9,19.9L11.4,17.9C13.1,18.1 14.9,17.5 16.2,16.2C18.5,13.9 18.5,10.1 16.2,7.7C15.1,6.6 13.5,6 12,6V10.6L7,5.6L12,0.6V4M6.3,17.6C3.7,15 3.3,11 5.1,7.9L6.6,9.4C5.5,11.6 5.9,14.4 7.8,16.2C8.3,16.7 8.9,17.1 9.6,17.4L9,19.4C8,19 7.1,18.4 6.3,17.6Z`,Z=`M10,17L6,13L7.41,11.59L10,14.17L16.59,7.58L18,9M12,1L3,5V11C3,16.55 6.84,21.74 12,23C17.16,21.74 21,16.55 21,11V5L12,1Z`,Qe=`M21,11C21,16.55 17.16,21.74 12,23C6.84,21.74 3,16.55 3,11V5L12,1L21,5V11M12,21C15.75,20 19,15.54 19,11.22V6.3L12,3.18L5,6.3V11.22C5,15.54 8.25,20 12,21Z`,$e=`M12,18A6,6 0 0,1 6,12C6,11 6.25,10.03 6.7,9.2L5.24,7.74C4.46,8.97 4,10.43 4,12A8,8 0 0,0 12,20V23L16,19L12,15M12,4V1L8,5L12,9V6A6,6 0 0,1 18,12C18,13 17.75,13.97 17.3,14.8L18.76,16.26C19.54,15.03 20,13.57 20,12A8,8 0 0,0 12,4Z`;function Q(e,t=20,n=`icon`){return I`
    <svg
      class="${n}"
      style="width: ${t}px; height: ${t}px;"
      viewBox="0 0 24 24"
    >
      <path d="${e}" fill="currentColor"></path>
    </svg>
  `}function et(e,t){if(!customElements.get(e))try{customElements.define(e,t)}catch(n){if(n instanceof Error&&(n.name===`NotSupportedError`||n.message.includes(`already been registered`))){class n extends t{}customElements.define(e,n)}else throw n}}function $(e){et(e.tag,e.card),e.editorTag&&e.editor&&et(e.editorTag,e.editor),window.customCards??=[],window.customCards.some(t=>t.type===e.tag)||window.customCards.push({type:e.tag,name:e.name,description:e.description,preview:!0,documentationURL:`https://github.com/ruaan-deysel/ha-vault`})}$({tag:be,editorTag:xe,card:class extends J{static editorTag=xe;render(){let e=this.getEntity(`vault_status`)||this.getEntity(`status`),t=e?.state?.toLowerCase(),n=!e||t===`unavailable`||t===`unknown`,r=!n&&(t===`ok`||t===`healthy`||t===`running`),i=this.getEntity(`open_anomalies`),a=Number(i?.state??0),o=100;n?o=null:r?a>0&&(o=Math.max(40,100-a*20)):o=25;let s=2*Math.PI*22,c=o===null?s:s-o/100*s,l=o===null?`var(--vault-standby)`:o>=90?`var(--vault-success)`:o>=60?`var(--vault-warning)`:`var(--vault-error)`,u=n?`Status unknown`:r&&a===0?`All backups healthy`:a>0?`${a} ${a===1?`anomaly`:`anomalies`} detected`:`Issues detected`,d=this.getEntity(`vault_version`),f=this.getEntity(`vault_mode`),p=f?.state?`Mode: ${f.state}`:d?.state?`v${d.state}`:`Vault Backup`;return I`
      <ha-card>
        <div class="header">
          <div class="header-main">
            <div class="header-icon ${n?``:r?`success`:`error`}">
              ${Q(Ye,18)}
            </div>
            <div class="header-titles">
              <span class="header-tag">Health Score</span>
              ${this.config.title?I`<span class="header-title">${this.config.title}</span>`:``}
            </div>
          </div>
        </div>

        <div class="kpi-container">
          <div class="score-circle">
            <svg viewBox="0 0 52 52">
              <circle class="score-circle-bg" cx="26" cy="26" r="22"></circle>
              <circle
                class="score-circle-fill"
                style="stroke: ${l}; stroke-dasharray: ${s}; stroke-dashoffset: ${c};"
                cx="26"
                cy="26"
                r="22"
              ></circle>
            </svg>
            <span class="score-text">${o===null?`--`:o}</span>
          </div>

          <div class="kpi-main">
            <span class="kpi-label">${u}</span>
            <span class="kpi-sub">${p}</span>
          </div>
        </div>
      </ha-card>
    `}},editor:class extends Y{},name:`Vault Health Score`,description:`Display Vault overall health score gauge and system status`}),$({tag:Se,editorTag:Ce,card:class extends J{static editorTag=Ce;render(){let e=this.getEntity(`total_jobs`)||this.getEntity(`jobs_total`),t=this.getEntity(`enabled_jobs`)||this.getEntity(`jobs_enabled`),n=this.getEntities(`status`).filter(e=>!e.entity_id.includes(`vault_status`)&&!e.entity_id.includes(`storage_`)),r=Number(e?.state??0),i=Number(t?.state??0),a=this.getEntities(`items_backed_up`),o=this.getEntities(`items_failed`),s=0,c=0;for(let e of a){let t=Number(e.state);!isNaN(t)&&t>0&&(s+=t)}for(let e of o){let t=Number(e.state);!isNaN(t)&&t>0&&(c+=t)}let l=0,u=0;r>0?(u=r,l=i>0?i:r):s>0||c>0?(l=s,u=s+c):n.length>0&&(u=n.length,l=n.filter(e=>e.state!==`disabled`).length||u);let d=u>0?Math.min(100,Math.round(l/u*100)):100,f=u>0&&l>=u&&c===0;return I`
      <ha-card>
        <div class="header">
          <div class="header-main">
            <div class="header-icon ${f?`success`:``}">
              ${Q(Qe,18)}
            </div>
            <div class="header-titles">
              <span class="header-tag">Protected</span>
              ${this.config.title?I`<span class="header-title">${this.config.title}</span>`:``}
            </div>
          </div>
        </div>

        <div class="kpi-main" style="padding-top: 4px;">
          <div class="kpi-value-row">
            <span class="kpi-value">${l}</span>
            <span class="kpi-unit">/${u||l}</span>
          </div>

          <div class="progress-bar" style="margin: 8px 0 6px 0;">
            <div
              class="progress-fill ${f?``:`warning`}"
              style="width: ${d}%;"
            ></div>
          </div>

          <span class="kpi-sub">
            ${f?`All items covered`:c>0?`${c} failed item${c===1?``:`s`}`:`${l} of ${u} jobs active`}
          </span>
        </div>
      </ha-card>
    `}},editor:class extends Y{},name:`Vault Protected Items`,description:`Display protected items and enabled jobs coverage`}),$({tag:we,editorTag:Te,card:class extends J{static editorTag=Te;render(){let e=this.getEntity(`total_jobs`)||this.getEntity(`jobs_total`),t=this.getEntity(`enabled_jobs`)||this.getEntity(`jobs_enabled`),n=this.getEntity(`runner_active_job`)||this.getEntity(`runner_current_job_id`),r=this.getEntities(`status`).filter(e=>!e.entity_id.includes(`vault_status`)&&!e.entity_id.includes(`storage_`)),i=Number(e?.state??(r.length||0)),a=Number(t?.state??i),o=n?.state&&n.state!==`idle`?n.state:null,s=this.getEntities(`next_run`),c=this.getEntities(`last_run`),l=``,u=null;for(let e of s){if(!e.state||e.state===`unavailable`||e.state===`unknown`)continue;let t=new Date(e.state).getTime();if(!isNaN(t)&&t>Date.now()&&(u===null||t<u)){u=t;let n=e.attributes?.friendly_name,r=(e.entity_id.split(`.`)[1]||``).replace(/^vault_backup_/,``).replace(/_next_run$/,``);l=n?.replace(/next run/i,``).replace(/vault backup/i,``).trim()||r||`Backup Job`}}if(!l&&c.length>0&&c[0]){let e=c[0].attributes?.friendly_name;e&&(l=e.replace(/last run/i,``).replace(/vault backup/i,``).trim()||``)}!l&&r.length>0&&r[0]&&(l=(r[0].attributes?.friendly_name)?.replace(/status/i,``).replace(/vault backup/i,``).trim()||``),l||=a>0?`Scheduled Jobs`:`No active jobs`;let d=o?`Running now`:u?this.formatTimeAgo(u):a>0?`Scheduled`:`Idle`,f=o?`Active: ${o}`:l,p=`${i} jobs · ${a} enabled`;return I`
      <ha-card>
        <div class="header">
          <div class="header-main">
            <div class="header-icon">
              ${Q(Ge,18)}
            </div>
            <div class="header-titles">
              <span class="header-tag">Next Run</span>
              ${this.config.title?I`<span class="header-title">${this.config.title}</span>`:``}
            </div>
          </div>
        </div>

        <div class="kpi-main" style="padding-top: 4px;">
          <div class="kpi-value-row">
            <span class="kpi-value" style="font-size: ${o?`1.4rem`:`1.7rem`};">
              ${d}
            </span>
          </div>

          <span class="kpi-label" style="margin-top: 4px;">${f}</span>
          <span class="kpi-sub" style="margin-top: 2px;">${p}</span>
        </div>
      </ha-card>
    `}},editor:class extends Y{},name:`Vault Next Run`,description:`Display next scheduled backup run and job status`}),$({tag:Ee,editorTag:De,card:class extends J{static editorTag=De;render(){let e=this.getEntities(`last_run`),t=this.getEntities(`last_size`),n=this.getEntities(`last_duration`),r=this.getEntities(`status`),i=0,a=``,o=`No backups recorded`,s=`--`,c=`--`,l=!0,u=!1;for(let t of e){if(!t.state||t.state===`unavailable`||t.state===`unknown`)continue;let e=new Date(t.state).getTime();if(!isNaN(e)&&e>i){i=e,u=!0,a=(t.entity_id.split(`.`)[1]||``).replace(/^vault_backup_/,``).replace(/_last_run$/,``);let n=t.attributes?.friendly_name;o=n?n.replace(/last run/i,``).replace(/vault backup/i,``).trim()||o:a||`Backup Job`}}if(u&&a){let e=t.find(e=>e.entity_id.endsWith(`_${a}_last_size`)||e.entity_id.endsWith(`_${a}_size`)||e.entity_id.includes(`_${a}_last_size`)),i=this.getEntities(`last_event`,`event`).find(e=>e.entity_id.includes(a)),o=this.parseDataSizeBytes(e?.state,e?.attributes?.unit_of_measurement);!o&&i?.attributes?.size_bytes&&(o=Number(i.attributes.size_bytes)),o>0&&(s=this.formatBytes(o));let u=n.find(e=>e.entity_id.endsWith(`_${a}_last_duration`)||e.entity_id.endsWith(`_${a}_duration`)||e.entity_id.includes(`_${a}_last_duration`));u?.state&&u.state!==`unavailable`&&u.state!==`unknown`&&(c=this.formatDuration(u.state));let d=r.find(e=>e.entity_id.endsWith(`_${a}_status`)||e.entity_id.includes(`_${a}_status`));if(d?.state){let e=d.state.toLowerCase();l=![`failed`,`error`,`aborted`].includes(e)}}let d=i>0?this.formatTimeAgo(i):`--`;return I`
      <ha-card>
        <div class="header">
          <div class="header-main">
            <div class="header-icon ${u?l?`success`:`error`:``}">
              ${Q(X,18)}
            </div>
            <div class="header-titles">
              <span class="header-tag">Last Backup</span>
              ${this.config.title?I`<span class="header-title">${this.config.title}</span>`:``}
            </div>
          </div>
        </div>

        <div class="kpi-main" style="padding-top: 4px;">
          <div style="display: flex; align-items: center; gap: 6px;">
            ${u?I`
                  <div class="badge ${l?`success`:`error`}">
                    <span class="badge-dot"></span>
                    ${l?`Success`:`Failed`}
                  </div>
                `:I`
                  <div class="badge neutral">
                    <span class="badge-dot"></span>
                    No Backups
                  </div>
                `}
          </div>

          <span class="kpi-label" style="margin-top: 6px;">
            ${o}${i>0?` · ${d}`:``}
          </span>
          <span class="kpi-sub" style="margin-top: 2px;">
            ${s} · ${c}
          </span>
        </div>
      </ha-card>
    `}},editor:class extends Y{},name:`Vault Last Backup`,description:`Display latest backup completion status, size, and duration`}),$({tag:Oe,editorTag:ke,card:class extends J{static editorTag=ke;getGridOptions(){return{columns:6,rows:3,min_columns:3,min_rows:2}}render(){let e=this.getEntities(`running`,`binary_sensor`),t=this.getEntity(`runner_active_job`)||this.getEntity(`runner_current_job_id`),n=e.some(e=>e.state===`on`)||t?.state&&t.state!==`idle`,r=e.find(e=>e.state===`on`)?.attributes?.friendly_name,i=t?.state&&t.state!==`idle`?t.state:r?.replace(/running/i,``).trim()||`Backup job`,a=this.getEntities(`progress`),o=0;for(let e of a){let t=Number(e.state);if(!isNaN(t)&&t>0){o=t;break}}return I`
      <ha-card>
        <div class="header">
          <div class="header-main">
            <div class="header-icon ${n?`running`:``}">
              ${Q($e,18)}
            </div>
            <div class="header-titles">
              <span class="header-tag">Backup In Progress</span>
              ${this.config.title?I`<span class="header-title">${this.config.title}</span>`:``}
            </div>
          </div>
          ${n?I`
                <div class="badge running">
                  <span class="badge-dot"></span>
                  Active
                </div>
              `:``}
        </div>

        ${n?I`
              <div class="card-row" style="margin-top: 4px;">
                <div class="card-row-main">
                  <div class="card-row-title-bar">
                    <span class="card-row-title">${i}</span>
                    <span class="badge running">${o}%</span>
                  </div>
                  <div class="progress-bar" style="margin: 6px 0;">
                    <div
                      class="progress-fill running"
                      style="width: ${Math.max(5,o)}%;"
                    ></div>
                  </div>
                  <div class="card-row-meta">
                    <span>Backing up items...</span>
                  </div>
                </div>
              </div>
            `:I`
              <div style="display: flex; align-items: center; gap: 12px; padding: 12px 4px;">
                <div style="color: var(--vault-standby);">
                  ${Q(Z,24)}
                </div>
                <div style="display: flex; flex-direction: column;">
                  <span style="font-size: 0.95rem; font-weight: 600; color: var(--vault-text);">
                    No backup running
                  </span>
                  <span style="font-size: 0.78rem; color: var(--vault-subtext);">
                    Next scheduled run will start automatically
                  </span>
                </div>
              </div>
            `}
      </ha-card>
    `}},editor:class extends Y{},name:`Vault Backup In Progress`,description:`Display active backup job progress or idle state`}),$({tag:Re,editorTag:ze,card:class extends J{static editorTag=ze;getGridOptions(){return{columns:6,rows:2,min_columns:3,min_rows:2}}render(){let e=this.getEntities(`storage`),t=e.filter(e=>e.entity_id.endsWith(`_type`)),n=new Set;for(let t of e){let e=t.entity_id;if(e.endsWith(`_total_space`)||e.endsWith(`_used_space`)||e.endsWith(`_free_space`)||e.endsWith(`_health`)||e.endsWith(`_status`))continue;let r=e.match(/storage_([a-z0-9_]+?)(?:_type|_path|$)/);r?.[1]?n.add(r[1]):n.add(e)}let r=t.map(e=>String(e.state||``).toLowerCase()).filter(e=>e&&e!==`unavailable`&&e!==`unknown`),i=r.some(e=>[`s3`,`sftp`,`webdav`,`smb`,`nfs`].includes(e)),a=new Set(r).size,o=a>=2,s=n.size||t.length,c=s>=3,l=c&&o&&i;return I`
      <ha-card>
        <div class="header">
          <div class="header-main">
            <div class="header-icon">
              ${Q(Ke,18)}
            </div>
            <div class="header-titles">
              <span class="header-tag">3-2-1 Backup Rule</span>
              ${this.config.title?I`<span class="header-title">${this.config.title}</span>`:``}
            </div>
          </div>
          <div class="badge ${l?`success`:`neutral`}">
            ${l?`Compliant`:`3-2-1 Status`}
          </div>
        </div>

        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-top: 6px;">
          <div style="background: var(--vault-surface); padding: 8px 10px; border-radius: 6px; border: 1px solid var(--vault-border); display: flex; align-items: center; gap: 8px;">
            <div style="color: ${c?`var(--vault-success)`:`var(--vault-standby)`};">
              ${Q(X,16)}
            </div>
            <div style="display: flex; flex-direction: column;">
              <span style="font-size: 0.75rem; font-weight: 700; color: var(--vault-text);">3 Copies</span>
              <span style="font-size: 0.7rem; color: var(--vault-subtext);">${c?`Target Verified`:`${s} Configured`}</span>
            </div>
          </div>

          <div style="background: var(--vault-surface); padding: 8px 10px; border-radius: 6px; border: 1px solid var(--vault-border); display: flex; align-items: center; gap: 8px;">
            <div style="color: ${o?`var(--vault-success)`:`var(--vault-standby)`};">
              ${Q(X,16)}
            </div>
            <div style="display: flex; flex-direction: column;">
              <span style="font-size: 0.75rem; font-weight: 700; color: var(--vault-text);">2 Media</span>
              <span style="font-size: 0.7rem; color: var(--vault-subtext);">${o?`${a} Media Types`:`Single Media`}</span>
            </div>
          </div>

          <div style="background: var(--vault-surface); padding: 8px 10px; border-radius: 6px; border: 1px solid var(--vault-border); display: flex; align-items: center; gap: 8px;">
            <div style="color: ${i?`var(--vault-success)`:`var(--vault-standby)`};">
              ${Q(X,16)}
            </div>
            <div style="display: flex; flex-direction: column;">
              <span style="font-size: 0.75rem; font-weight: 700; color: var(--vault-text);">1 Offsite</span>
              <span style="font-size: 0.7rem; color: var(--vault-subtext);">${i?`Remote Target`:`Local Only`}</span>
            </div>
          </div>
        </div>
      </ha-card>
    `}},editor:class extends Y{},name:`Vault 3-2-1 Rule`,description:`Display 3-2-1 backup compliance checklist`}),$({tag:Ae,editorTag:je,card:class extends J{static editorTag=je;getCardSize(){return 4}getGridOptions(){return{columns:6,rows:4,min_columns:3,min_rows:3}}_runningJobs=new Set;getJobs(){let e=this.getEntities(`status`),t=this.getEntities(`running`,`binary_sensor`),n=this.getEntities(`run_now`,`button`),r=new Map;for(let i of e){if(i.entity_id===`sensor.vault_status`||i.entity_id===`sensor.vault_backup_status`||i.entity_id.includes(`storage_`))continue;let e=(i.entity_id.split(`.`)[1]||``).replace(/^vault_backup_job_/,``).replace(/^vault_backup_/,``).replace(/^vault_job_/,``).replace(/^vault_/,``).replace(/_status$/,``);if(!e||e===`backup`||e===`status`)continue;let a=(i.attributes?.friendly_name||e).replace(/status/i,``).replace(/^vault backup/i,``).trim()||e,o=t.some(t=>t.entity_id.includes(e)&&t.state===`on`)||i.state.toLowerCase()===`running`,s=n.find(t=>t.entity_id.endsWith(`_${e}_run_backup`)||t.entity_id.endsWith(`_${e}_run_now`)||t.entity_id.endsWith(`_${e}`)||t.entity_id.includes(`_${e}_run_backup`)||t.entity_id.includes(`_${e}_run_now`)),c=i.attributes?.compression,l=i.attributes?.job_id,u=typeof l==`number`?l:typeof l==`string`&&!isNaN(Number(l))?Number(l):void 0;r.set(e,{id:e,jobId:u,name:a,status:i.state||`idle`,isRunning:o,enabled:i.state!==`disabled`,compression:c||void 0,buttonEntityId:s?.entity_id})}return Array.from(r.values())}async _handleRunNow(e){if(!this._runningJobs.has(e.id)){this._runningJobs.add(e.id),this.requestUpdate();try{e.buttonEntityId?await this.callAction(`button`,`press`,{entity_id:e.buttonEntityId}):e.jobId===void 0?await this.callAction(`vault`,`run_backup`,{job_name:e.name}):await this.callAction(`vault`,`run_backup`,{job_id:e.jobId})}catch(t){console.error(`Failed to trigger job ${e.name}:`,t)}finally{setTimeout(()=>{this._runningJobs.delete(e.id),this.requestUpdate()},3e3)}}}render(){let e=this.getJobs();return I`
      <ha-card>
        <div class="header">
          <div class="header-main">
            <div class="header-icon">
              ${Q(Ue,18)}
            </div>
            <div class="header-titles">
              <span class="header-tag">Backup Jobs</span>
              ${this.config.title?I`<span class="header-title">${this.config.title}</span>`:``}
            </div>
          </div>
          <span style="font-size: 0.78rem; font-weight: 600; color: var(--vault-accent);">
            ${e.length} jobs
          </span>
        </div>

        <div class="item-list">
          ${e.length===0?I`
                <div class="empty-state">
                  <span>No backup jobs found on this Vault instance</span>
                </div>
              `:e.map(e=>{let t=e.isRunning||this._runningJobs.has(e.id);return I`
                  <div class="card-row">
                    <div class="card-row-main">
                      <div class="card-row-title-bar">
                        <span class="card-row-title">${e.name}</span>
                        ${e.isRunning?I`
                              <span class="badge running">
                                <span class="badge-dot"></span>
                                Running
                              </span>
                            `:e.status.toLowerCase()===`completed`?I`
                              <span class="badge success">
                                <span class="badge-dot"></span>
                                Completed
                              </span>
                            `:I`
                              <span class="badge neutral">
                                ${e.enabled?`Enabled`:`Disabled`}
                              </span>
                            `}
                      </div>
                      <div class="card-row-meta">
                        <span>${e.enabled?`Enabled`:`Disabled`}${e.compression?` · ${e.compression}`:``}</span>
                      </div>
                    </div>

                    <div class="card-row-actions">
                      ${this.getActiveDevice()?.configuration_url?I`
                            <button
                              class="btn"
                              title="Restore"
                              @click="${()=>{let e=this.getActiveDevice()?.configuration_url;e&&window.open(e,`_blank`,`noopener,noreferrer`)}}"
                            >
                              ${Q(Ze,14)}
                              Restore
                            </button>
                          `:``}

                      <button
                        class="btn amber"
                        ?disabled="${t}"
                        @click="${()=>this._handleRunNow(e)}"
                      >
                        ${Q(Xe,14)}
                        ${t?`Starting...`:`Run Now`}
                      </button>
                    </div>
                  </div>
                `})}
        </div>
      </ha-card>
    `}},editor:class extends Y{},name:`Vault Backup Jobs`,description:`Display backup jobs with quick Run Now and Restore controls`}),$({tag:Me,editorTag:Ne,card:class extends J{static editorTag=Ne;getCardSize(){return 5}getGridOptions(){return{columns:6,rows:5,min_columns:4,min_rows:3}}getActivity(){let e=this.getEntities(`last_run`),t=this.getEntities(`last_size`),n=this.getEntities(`last_duration`),r=this.getEntities(`items_backed_up`),i=[];for(let a of e){if(!a.state||a.state===`unavailable`||a.state===`unknown`)continue;let e=(a.entity_id.split(`.`)[1]||``).replace(/^vault_backup_/,``).replace(/_last_run$/,``),o=(a.attributes?.friendly_name||e).replace(/last run/i,``).replace(/vault backup/i,``).trim(),s=t.find(t=>t.entity_id.endsWith(`_${e}_last_size`)||t.entity_id.endsWith(`_${e}_size`)||t.entity_id.includes(`_${e}_last_size`)),c=n.find(t=>t.entity_id.endsWith(`_${e}_last_duration`)||t.entity_id.endsWith(`_${e}_duration`)||t.entity_id.includes(`_${e}_last_duration`)),l=r.find(t=>t.entity_id.endsWith(`_${e}_items_backed_up`)||t.entity_id.includes(`_${e}_items_backed_up`)),u=this.getEntities(`last_event`,`event`).find(t=>t.entity_id.includes(e)),d=this.parseDataSizeBytes(s?.state,s?.attributes?.unit_of_measurement);!d&&u?.attributes?.size_bytes&&(d=Number(u.attributes.size_bytes));let f=this.formatDuration(c?.state),p=Number(l?.state||u?.attributes?.items_done||0),m=a.state;try{let e=new Date(a.state);isNaN(e.getTime())||(m=e.toLocaleDateString(`en-US`,{day:`numeric`,month:`short`,hour:`2-digit`,minute:`2-digit`}))}catch{}let h=[],g=a.attributes?.items||a.attributes?.item_names||l?.attributes?.items||l?.attributes?.item_names;Array.isArray(g)&&(h=g.map(e=>String(e).trim()).filter(Boolean));let ee=String(a.attributes?.status||a.attributes?.last_status||l?.attributes?.status||u?.attributes?.status||`completed`).toLowerCase();i.push({id:e,jobName:o,status:ee,timeStr:m,durationStr:f,sizeStr:this.formatBytes(d),itemsStr:p>0?`${p} items`:`--`,itemsList:h})}return i}render(){let e=this.getActivity();return I`
      <ha-card>
        <div class="header">
          <div class="header-main">
            <div class="header-icon">
              ${Q(qe,18)}
            </div>
            <div class="header-titles">
              <span class="header-tag">Recent Activity</span>
              ${this.config.title?I`<span class="header-title">${this.config.title}</span>`:``}
            </div>
          </div>
        </div>

        <div class="item-list" style="margin-top: 4px;">
          ${e.length===0?I`
                <div class="empty-state">
                  <span>No recent backup activity recorded</span>
                </div>
              `:e.map(e=>I`
                  <div class="card-row" style="flex-direction: column; align-items: stretch; gap: 8px;">
                    <div style="display: flex; align-items: center; justify-content: space-between; gap: 8px;">
                      <div style="display: flex; align-items: center; gap: 8px;">
                        <span
                          style="width: 8px; height: 8px; border-radius: 50%; background: ${e.status===`failed`||e.status===`error`?`var(--vault-error)`:`var(--vault-success)`}; display: inline-block;"
                        ></span>
                        <span style="font-size: 0.88rem; font-weight: 600; color: var(--vault-text);">
                          ${e.jobName}
                        </span>
                        <span class="badge ${e.status===`failed`||e.status===`error`?`error`:`success`}" style="font-size: 0.68rem; padding: 1px 6px;">
                          ${e.status}
                        </span>
                      </div>
                      <span style="font-size: 0.72rem; color: var(--vault-subtext);">
                        ${e.timeStr}
                      </span>
                    </div>

                    ${e.itemsList.length>0?I`
                          <div class="chip-container">
                            ${e.itemsList.map(e=>I`
                                <span class="chip success">
                                  ${Q(We,12)}
                                  ${e}
                                </span>
                              `)}
                          </div>
                        `:``}

                    <div style="font-size: 0.72rem; color: var(--vault-subtext); border-top: 1px solid var(--vault-border); padding-top: 6px; display: flex; gap: 8px;">
                      <span>${e.durationStr}</span>
                      <span>·</span>
                      <span>${e.sizeStr}</span>
                      <span>·</span>
                      <span>${e.itemsStr}</span>
                    </div>
                  </div>
                `)}
        </div>
      </ha-card>
    `}},editor:class extends Y{},name:`Vault Recent Activity`,description:`Display backup history timeline with backed up items tags`}),$({tag:Pe,editorTag:Fe,card:class extends J{static editorTag=Fe;getCardSize(){return 4}getGridOptions(){return{columns:6,rows:4,min_columns:3,min_rows:3}}getStorage(){if(!this.hass?.states)return[];let e=new Map,t=[];for(let[e,n]of Object.entries(this.hass.states))e.startsWith(`sensor.`)&&e.includes(`storage_`)&&t.push(n);let n=new Set;for(let e of t){let t=e.entity_id.match(/storage_([a-z0-9_]+?)_(?:name|type|health|free_space|used_space|total_space)$/);t&&t[1]&&n.add(t[1])}for(let r of n){let n=t.find(e=>e.entity_id.endsWith(`storage_${r}_name`)),i=t.find(e=>e.entity_id.endsWith(`storage_${r}_type`)),a=t.find(e=>e.entity_id.endsWith(`storage_${r}_health`)),o=t.find(e=>e.entity_id.endsWith(`storage_${r}_free_space`)),s=t.find(e=>e.entity_id.endsWith(`storage_${r}_used_space`)),c=t.find(e=>e.entity_id.endsWith(`storage_${r}_total_space`)),l=this.parseDataSizeBytes(o?.state,o?.attributes?.unit_of_measurement),u=this.parseDataSizeBytes(s?.state,s?.attributes?.unit_of_measurement)||Number(o?.attributes?.used_bytes||0),d=this.parseDataSizeBytes(c?.state,c?.attributes?.unit_of_measurement)||Number(o?.attributes?.total_bytes||0),f=n?.state;(!f||f===`unavailable`||f===`unknown`)&&(f=(o?.attributes?.friendly_name||r).replace(/free space/i,``).replace(/total space/i,``).replace(/used space/i,``).replace(/storage/i,``).replace(/vault backup/i,``).trim()||r);let p=0;if(d>0&&u>0)p=Math.min(100,Math.round(u/d*100));else if(d>0&&l>0){let e=Math.max(0,d-l);p=Math.min(100,Math.round(e/d*100))}e.set(r,{id:r,name:f,type:(i?.state&&i.state!==`unavailable`?i.state:`local`).toUpperCase(),health:a?.state&&a.state!==`unavailable`?a.state:`ok`,usedBytes:u,freeBytes:l,totalBytes:d,usagePct:p})}return Array.from(e.values())}render(){let e=this.getStorage();return I`
      <ha-card>
        <div class="header">
          <div class="header-main">
            <div class="header-icon">
              ${Q(Je,18)}
            </div>
            <div class="header-titles">
              <span class="header-tag">Storage Destinations</span>
              ${this.config.title?I`<span class="header-title">${this.config.title}</span>`:``}
            </div>
          </div>
          <span style="font-size: 0.78rem; font-weight: 600; color: var(--vault-accent);">
            ${e.length} targets
          </span>
        </div>

        <div class="item-list">
          ${e.length===0?I`
                <div class="empty-state">
                  <span>No storage destinations configured</span>
                </div>
              `:e.map(e=>{let t=e.health.toLowerCase()===`ok`||e.health.toLowerCase()===`healthy`,n=e.usagePct>=90;return I`
                  <div class="card-row">
                    <div class="card-row-main">
                      <div class="card-row-title-bar">
                        <span class="card-row-title">${e.name}</span>
                        <span class="badge neutral">${e.type}</span>
                        <span class="badge ${t?`success`:`warning`}">
                          <span class="badge-dot"></span>
                          ${t?`Healthy`:e.health}
                        </span>
                      </div>

                      ${e.totalBytes>0?I`
                            <div class="progress-bar" style="margin: 6px 0;">
                              <div
                                class="progress-fill ${n?`error`:e.usagePct>80?`warning`:``}"
                                style="width: ${e.usagePct}%;"
                              ></div>
                            </div>

                            <div class="card-row-meta">
                              <span>${this.formatBytes(e.freeBytes)} free</span>
                              <span>·</span>
                              <span>${this.formatBytes(e.usedBytes)} of ${this.formatBytes(e.totalBytes)} (${e.usagePct}%)</span>
                            </div>
                          `:I`
                            <div class="progress-bar" style="margin: 6px 0;">
                              <div
                                class="progress-fill"
                                style="width: 100%;"
                              ></div>
                            </div>

                            <div class="card-row-meta">
                              <span>${this.formatBytes(e.freeBytes)} free</span>
                              <span>·</span>
                              <span>Destination active</span>
                            </div>
                          `}
                    </div>
                  </div>
                `})}
        </div>
      </ha-card>
    `}},editor:class extends Y{},name:`Vault Storage`,description:`Display backup storage destinations and capacity usage`}),$({tag:Ie,editorTag:Le,card:class extends J{static editorTag=Le;getGridOptions(){return{columns:6,rows:3,min_columns:3,min_rows:2}}render(){let e=this.getEntity(`open_anomalies`),t=Number(e?.state??0),n=e?.attributes?.anomalies||[];return I`
      <ha-card>
        <div class="header">
          <div class="header-main">
            <div class="header-icon ${t>0?`error`:`success`}">
              ${Q(t>0?He:Z,18)}
            </div>
            <div class="header-titles">
              <span class="header-tag">Anomalies & Attention</span>
              ${this.config.title?I`<span class="header-title">${this.config.title}</span>`:``}
            </div>
          </div>
          <div class="badge ${t>0?`warning`:`success`}">
            ${t===0?`Clear`:`${t} Issue${t===1?``:`s`}`}
          </div>
        </div>

        ${t===0?I`
              <div style="display: flex; align-items: center; gap: 12px; padding: 12px 4px;">
                <div style="color: var(--vault-success);">
                  ${Q(Z,24)}
                </div>
                <div style="display: flex; flex-direction: column;">
                  <span style="font-size: 0.95rem; font-weight: 600; color: var(--vault-text);">
                    No open anomalies
                  </span>
                  <span style="font-size: 0.78rem; color: var(--vault-subtext);">
                    All backup monitors and detectors report normal operation
                  </span>
                </div>
              </div>
            `:I`
              <div class="item-list">
                ${n.map(e=>I`
                    <div class="card-row">
                      <div class="card-row-main">
                        <div class="card-row-title-bar">
                          <span class="card-row-title">${e.summary||e.detector||`Anomaly`}</span>
                          <span class="badge ${e.severity===`critical`?`error`:`warning`}">
                            ${e.severity||`warning`}
                          </span>
                        </div>
                        <div class="card-row-meta">
                          <span>${e.job?`Scope: ${e.job}`:`System detector`}</span>
                        </div>
                      </div>
                    </div>
                  `)}
              </div>
            `}
      </ha-card>
    `}},editor:class extends Y{},name:`Vault Anomalies`,description:`Display backup anomalies and attention alerts`}),$({tag:Be,editorTag:Ve,card:class extends J{static editorTag=Ve;static styles=[...J.styles,o`
      .dash-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        margin-top: 4px;
      }

      .dash-sections {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 12px;
        margin-top: 8px;
      }

      @media (max-width: 768px) {
        .dash-grid {
          grid-template-columns: repeat(2, 1fr);
        }
        .dash-sections {
          grid-template-columns: 1fr;
        }
      }

      @media (max-width: 480px) {
        .dash-grid {
          grid-template-columns: 1fr;
        }
      }
    `];getCardSize(){return 8}getGridOptions(){return{columns:12,rows:8,min_columns:6,min_rows:4}}render(){let e=this.getEntity(`online`,`binary_sensor`)||this.getEntity(`vault_online`,`binary_sensor`),t=!e||e.state===`on`,n=this.getEntity(`vault_version`)||this.getEntity(`version`),r=this.getActiveDevice(),i=r?.name_by_user||r?.name||`Vault Backup`,a=n?.state?`v${n.state}`:``;return I`
      <ha-card>
        <div class="header" style="border-bottom: 1px solid var(--vault-border); padding-bottom: 10px;">
          <div class="header-main">
            <div class="header-icon ${t?`success`:`error`}">
              ${Q(Z,20)}
            </div>
            <div class="header-titles">
              <span class="header-title">${this.config.title||i}</span>
              <span class="header-subtitle">Vault Unraid Backup Daemon ${a}</span>
            </div>
          </div>
          <div class="header-actions">
            <div class="badge ${t?`success`:`error`}">
              <span class="badge-dot"></span>
              ${t?`Online`:`Offline`}
            </div>
          </div>
        </div>

        <!-- KPI Row: 4 At-a-Glance Tiles -->
        <div class="dash-grid">
          <vault-health-card
            embedded
            .hass="${this.hass}"
            .config="${{type:`custom:vault-health-card`,embedded:!0,server:this.config.server}}"
          ></vault-health-card>

          <vault-protected-card
            embedded
            .hass="${this.hass}"
            .config="${{type:`custom:vault-protected-card`,embedded:!0,server:this.config.server}}"
          ></vault-protected-card>

          <vault-next-run-card
            embedded
            .hass="${this.hass}"
            .config="${{type:`custom:vault-next-run-card`,embedded:!0,server:this.config.server}}"
          ></vault-next-run-card>

          <vault-last-backup-card
            embedded
            .hass="${this.hass}"
            .config="${{type:`custom:vault-last-backup-card`,embedded:!0,server:this.config.server}}"
          ></vault-last-backup-card>
        </div>

        <!-- Backup in progress banner -->
        <vault-progress-card
          embedded
          .hass="${this.hass}"
          .config="${{type:`custom:vault-progress-card`,embedded:!0,server:this.config.server}}"
        ></vault-progress-card>

        <!-- Main Sections: Jobs & Activity -->
        <div class="dash-sections">
          <vault-jobs-card
            embedded
            .hass="${this.hass}"
            .config="${{type:`custom:vault-jobs-card`,embedded:!0,server:this.config.server}}"
          ></vault-jobs-card>

          <vault-activity-card
            embedded
            .hass="${this.hass}"
            .config="${{type:`custom:vault-activity-card`,embedded:!0,server:this.config.server}}"
          ></vault-activity-card>
        </div>

        <!-- Storage & 3-2-1 Row -->
        <div class="dash-sections">
          <vault-storage-card
            embedded
            .hass="${this.hass}"
            .config="${{type:`custom:vault-storage-card`,embedded:!0,server:this.config.server}}"
          ></vault-storage-card>

          <vault-rules-card
            embedded
            .hass="${this.hass}"
            .config="${{type:`custom:vault-rules-card`,embedded:!0,server:this.config.server}}"
          ></vault-rules-card>
        </div>
      </ha-card>
    `}},editor:class extends Y{},name:`Vault Dashboard`,description:`Complete unified dashboard replicating the Vault backup interface`});