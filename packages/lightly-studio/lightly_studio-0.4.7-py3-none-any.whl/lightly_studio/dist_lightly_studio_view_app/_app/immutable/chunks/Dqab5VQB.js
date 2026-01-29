import"./CWj6FrbW.js";import{p as x,f as A,a as p,i as P,g as M,b as K,c as v,r as d,s as T,t as G}from"./Yb_TZ_Rf.js";import{c as C,a as o,f as y}from"./DnGquTil.js";import{s as b}from"./DTWlVeDn.js";import{s as L,r as k,p as j,b as H}from"./CmJZ_CaC.js";import{I as Q,S as X,q as F,J as Y}from"./DcA8i6zt.js";import{s as I}from"./CGH6oPk7.js";import{i as q}from"./DVJdaASW.js";import{e as Z,s as O,d as S,g as $}from"./Dcv4bg-q.js";import{a as aa}from"./DELrRF6e.js";function pa(l,a){x(a,!0);/**
 * @license @lucide/svelte v0.482.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2022 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2022.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 */let r=k(a,["$$slots","$$events","$$legacy"]);const s=[["ellipse",{cx:"12",cy:"5",rx:"9",ry:"3"}],["path",{d:"M3 5V19A9 3 0 0 0 21 19V5"}],["path",{d:"M3 12A9 3 0 0 0 21 12"}]];Q(l,L({name:"database"},()=>r,{get iconNode(){return s},children:(e,n)=>{var t=C(),f=A(t);b(f,()=>a.children??P),o(e,t)},$$slots:{default:!0}})),p()}function ya(l,a){x(a,!0);/**
 * @license @lucide/svelte v0.482.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2022 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2022.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 */let r=k(a,["$$slots","$$events","$$legacy"]);const s=[["path",{d:"M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8"}],["path",{d:"M3 10a2 2 0 0 1 .709-1.528l7-5.999a2 2 0 0 1 2.582 0l7 5.999A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"}]];Q(l,L({name:"house"},()=>r,{get iconNode(){return s},children:(e,n)=>{var t=C(),f=A(t);b(f,()=>a.children??P),o(e,t)},$$slots:{default:!0}})),p()}var ea=y('<div class="flex items-start gap-3"><span class="truncate text-sm font-medium"> </span> <pre class="min-w-[8rem] flex-1 overflow-x-auto whitespace-pre-wrap rounded bg-muted p-2 text-sm"> </pre></div>'),ta=y('<div class="flex items-start gap-3"><span class="truncate text-sm font-medium"> </span> <span class="min-w-[8rem] flex-1 break-all text-sm"> </span></div>'),ra=y('<div class="space-y-3 text-diffuse-foreground"></div>');function Ma(l,a){x(a,!0);const r=K(()=>{const t=[];if(a.metadata_dict&&typeof a.metadata_dict=="object"&&"data"in a.metadata_dict){const f=a.metadata_dict.data;f&&typeof f=="object"&&Object.entries(f).forEach(([i,c])=>{const _=aa(c),h=typeof c=="object"&&c!==null&&!Array.isArray(c);t.push({id:`metadata_${i}`,label:`${i}:`,value:_,isComplex:h})})}return t});var s=C(),e=A(s);{var n=t=>{X(t,{title:"Metadata",children:(f,i)=>{var c=ra();Z(c,21,()=>M(r),({label:_,value:h,id:w,isComplex:m})=>_,(_,h)=>{let w=()=>M(h).label,m=()=>M(h).value,u=()=>M(h).id,z=()=>M(h).isComplex;var N=C(),R=A(N);{var U=V=>{var B=ea(),g=v(B),E=v(g,!0);d(g);var D=T(g,2),J=v(D,!0);d(D),d(B),G(()=>{O(g,"title",w()),I(E,w()),I(J,m())}),o(V,B)},W=V=>{var B=ta(),g=v(B),E=v(g,!0);d(g);var D=T(g,2),J=v(D,!0);d(D),d(B),G(()=>{O(g,"title",w()),I(E,w()),O(D,"data-testid",`sample-metadata-${u()}`),I(J,m())}),o(V,B)};q(R,V=>{z()?V(U):V(W,!1)})}o(_,N)}),d(c),o(f,c)}})};q(e,t=>{M(r).length>0&&t(n)})}o(l,s),p()}var sa=y("<nav><!></nav>");function Pa(l,a){x(a,!0);let r=j(a,"ref",15),s=k(a,["$$slots","$$events","$$legacy","ref","class","children"]);var e=sa();S(e,()=>({class:a.class,"aria-label":"breadcrumb",...s}));var n=v(e);b(n,()=>a.children??P),d(e),H(e,t=>r(t),()=>r()),o(l,e),p()}var la=y("<li><!></li>");function ka(l,a){x(a,!0);let r=j(a,"ref",15,null),s=k(a,["$$slots","$$events","$$legacy","ref","class","children"]);var e=la();S(e,t=>({class:t,...s}),[()=>F("inline-flex items-center gap-1.5",a.class)]);var n=v(e);b(n,()=>a.children??P),d(e),H(e,t=>r(t),()=>r()),o(l,e),p()}var na=y("<li><!></li>");function wa(l,a){x(a,!0);let r=j(a,"ref",15,null),s=k(a,["$$slots","$$events","$$legacy","ref","class","children"]);var e=na();S(e,i=>({role:"presentation","aria-hidden":"true",class:i,...s}),[()=>F("[&>svg]:size-3.5",a.class)]);var n=v(e);{var t=i=>{var c=C(),_=A(c);b(_,()=>a.children??P),o(i,c)},f=i=>{Y(i,{})};q(n,i=>{a.children?i(t):i(f,!1)})}d(e),H(e,i=>r(i),()=>r()),o(l,e),p()}var ia=y("<a><!></a>");function Ba(l,a){x(a,!0);let r=j(a,"ref",15,null),s=j(a,"href",3,void 0),e=k(a,["$$slots","$$events","$$legacy","ref","class","href","child","children"]);const n=K(()=>({class:F("hover:text-foreground transition-colors",a.class),href:s(),...e})),t=$(),[f,i]=t;var c=C(),_=A(c);{var h=m=>{var u=C(),z=A(u);b(z,()=>a.child,()=>({props:M(n)})),o(m,u)},w=m=>{var u=ia();S(u,N=>({...N}),[()=>i({...M(n)},[{attribute_name:"href",lang_attribute_name:"hreflang"}])]);var z=v(u);b(z,()=>a.children??P),d(u),H(u,N=>r(N),()=>r()),o(m,u)};q(_,m=>{a.child?m(h):m(w,!1)})}o(l,c),p()}var oa=y("<ol><!></ol>");function Aa(l,a){x(a,!0);let r=j(a,"ref",15,null),s=k(a,["$$slots","$$events","$$legacy","ref","class","children"]);var e=oa();S(e,t=>({class:t,...s}),[()=>F("text-muted-foreground flex flex-wrap items-center gap-1.5 break-words text-sm sm:gap-2.5",a.class)]);var n=v(e);b(n,()=>a.children??P),d(e),H(e,t=>r(t),()=>r()),o(l,e),p()}var ca=y("<span><!></span>");function Ca(l,a){x(a,!0);let r=j(a,"ref",15,null),s=k(a,["$$slots","$$events","$$legacy","ref","class","children"]);var e=ca();S(e,t=>({role:"link","aria-disabled":"true","aria-current":"page",class:t,...s}),[()=>F("text-foreground font-normal",a.class)]);var n=v(e);b(n,()=>a.children??P),d(e),H(e,t=>r(t),()=>r()),o(l,e),p()}export{Pa as B,pa as D,ya as H,Ma as M,Aa as a,ka as b,Ba as c,wa as d,Ca as e};
