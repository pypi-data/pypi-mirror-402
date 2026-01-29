import"../chunks/CWj6FrbW.js";import{p as D,f as i,i as W,a as M,n as j,g as d,b as v,s as I,c as k,r as q,t as z}from"../chunks/Yb_TZ_Rf.js";import{c as C,a as r,f as B,t as J}from"../chunks/DnGquTil.js";import{s as E}from"../chunks/DTWlVeDn.js";import{i as Z,s as X,a as Y}from"../chunks/DVJdaASW.js";import{p as V}from"../chunks/CnA6nQDP.js";import{I as ee}from"../chunks/DcA8i6zt.js";import"../chunks/CvGjimpO.js";import{u as se}from"../chunks/C3A6m4-m.js";import"../chunks/Dcv4bg-q.js";import"../chunks/BztKn-jM.js";import"../chunks/69_IOA4Y.js";import{g as oe}from"../chunks/C1bEftoN.js";import{b as le}from"../chunks/DtWZc_tl.js";import{r as Q}from"../chunks/Bz2KBNfb.js";import{i as ne,a as ce,e as de}from"../chunks/BQhJr0Qw.js";import{S as ie}from"../chunks/a1JJegV1.js";import{S as me}from"../chunks/DnCfFZRi.js";import{s as T}from"../chunks/CGH6oPk7.js";import{B as ue,a as pe,b as R,c as G,H as fe,d as O,D as ve,e as he}from"../chunks/Dqab5VQB.js";import{s as te,r as ae}from"../chunks/CmJZ_CaC.js";function ge(s,e){D(e,!0);/**
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
 */let t=ae(e,["$$slots","$$events","$$legacy"]);const n=[["path",{d:"M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"}],["path",{d:"M14 2v4a2 2 0 0 0 2 2h4"}],["circle",{cx:"10",cy:"12",r:"2"}],["path",{d:"m20 17-1.296-1.296a2.41 2.41 0 0 0-3.408 0L9 22"}]];ee(s,te({name:"file-image"},()=>t,{get iconNode(){return n},children:(m,u)=>{var o=C(),h=i(o);E(h,()=>e.children??W),r(m,o)},$$slots:{default:!0}})),M()}function _e(s,e){D(e,!0);/**
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
 */let t=ae(e,["$$slots","$$events","$$legacy"]);const n=[["path",{d:"M18 22H4a2 2 0 0 1-2-2V6"}],["path",{d:"m22 13-1.296-1.296a2.41 2.41 0 0 0-3.408 0L11 18"}],["circle",{cx:"12",cy:"8",r:"2"}],["rect",{width:"16",height:"16",x:"6",y:"2",rx:"2"}]];ee(s,te({name:"images"},()=>t,{get iconNode(){return n},children:(m,u)=>{var o=C(),h=i(o);E(h,()=>e.children??W),r(m,o)},$$slots:{default:!0}})),M()}const $e=s=>`${le}/sample/${s}`,xe=({sampleId:s})=>{const e=ne({path:{sample_id:s}}),t=ce(),n=de(e);return{refetch:()=>{t.invalidateQueries({queryKey:e.queryKey})},image:n}};var Ie=B('<!> <span class="hidden sm:inline">Home</span>',1),be=B('<!> <span class="max-w-[150px] truncate"> </span>',1),Pe=B('<!> <span class="hidden sm:inline">Samples</span>',1),Se=B('<!> <span class="max-w-[200px] truncate"><!></span>',1),ye=B("<!> <!> <!> <!> <!> <!> <!>",1);function we(s,e){D(e,!0);const t=()=>X(u,"$filteredSampleCount",n),[n,m]=Y(),{filteredSampleCount:u}=se();ue(s,{class:"mb-2","data-testid":"sample-details-breadcrumb",children:(o,h)=>{pe(o,{children:(H,K)=>{var b=ye(),S=i(b);R(S,{children:(g,P)=>{{let f=v(()=>Q.toCollectionHome(e.rootCollection.collection_id));G(g,{get href(){return d(f)},class:"flex items-center gap-2",children:(x,L)=>{var c=Ie(),_=i(c);fe(_,{class:"h-4 w-4"}),j(2),r(x,c)},$$slots:{default:!0}})}},$$slots:{default:!0}});var y=I(S,2);O(y,{});var $=I(y,2);R($,{children:(g,P)=>{{let f=v(()=>Q.toCollectionHome(e.rootCollection.collection_id));G(g,{get href(){return d(f)},class:"flex items-center gap-2",children:(x,L)=>{var c=be(),_=i(c);ve(_,{class:"h-4 w-4"});var N=I(_,2),F=k(N,!0);q(N),z(()=>T(F,e.rootCollection.name)),r(x,c)},$$slots:{default:!0}})}},$$slots:{default:!0}});var a=I($,2);O(a,{});var l=I(a,2);R(l,{children:(g,P)=>{{let f=v(()=>Q.toSamples(V.params.collection_id));G(g,{get href(){return d(f)},class:"flex items-center gap-2",children:(x,L)=>{var c=Pe(),_=i(c);_e(_,{class:"h-4 w-4"}),j(2),r(x,c)},$$slots:{default:!0}})}},$$slots:{default:!0}});var p=I(l,2);O(p,{});var A=I(p,2);R(A,{children:(g,P)=>{he(g,{class:"flex items-center gap-2",children:(f,x)=>{var L=Se(),c=i(L);ge(c,{class:"h-4 w-4"});var _=I(c,2),N=k(_);{var F=w=>{var U=J();z(()=>T(U,`Sample ${e.sampleIndex+1} of ${t()??""}`)),r(w,U)},re=w=>{var U=J("Sample");r(w,U)};Z(N,w=>{e.sampleIndex!==void 0?w(F):w(re,!1)})}q(_),r(f,L)},$$slots:{default:!0}})},$$slots:{default:!0}}),r(H,b)},$$slots:{default:!0}})},$$slots:{default:!0}}),M(),m()}function Ce(s,e){D(e,!0);const t=()=>X(d(H),"$image",n),[n,m]=Y(),u=e.collection.collection_id,o=()=>{oe(Q.toSamples(u))},h=v(()=>xe({sampleId:e.sampleId})),H=v(()=>d(h).image),K=v(()=>d(h).refetch);let b=v(()=>$e(e.sampleId));{const S=(a,l)=>{let p=()=>l==null?void 0:l().collection;we(a,{get rootCollection(){return p()},get sampleIndex(){return e.sampleIndex}})},y=a=>{me(a,{get sample(){return t().data}})};let $=v(()=>{var a,l,p;return(a=t().data)!=null&&a.sample?{...(l=t().data)==null?void 0:l.sample,width:t().data.width,height:t().data.height,annotations:(p=t().data)==null?void 0:p.annotations}:void 0});ie(s,{get collectionId(){return u},get sampleId(){return e.sampleId},get sampleURL(){return d(b)},get sample(){return d($)},get refetch(){return d(K)},handleEscape:o,breadcrumb:S,metadataValue:y,children:(a,l)=>{var p=C(),A=i(p);{var g=P=>{var f=C(),x=i(f);E(x,()=>e.children),r(P,f)};Z(A,P=>{e.children&&P(g)})}r(a,p)},$$slots:{breadcrumb:!0,metadataValue:!0,default:!0}})}M(),m()}var Be=B('<div class="flex h-full w-full space-x-4 px-4 pb-4" data-testid="sample-details"><div class="h-full w-full space-y-6 rounded-[1vw] bg-card p-4"><!></div></div>');function Te(s,e){D(e,!0);const t=v(()=>V.params.sampleId),n=V.data.collection,m=v(()=>Number(V.params.sampleIndex));var u=Be(),o=k(u),h=k(o);Ce(h,{get sampleId(){return d(t)},get collection(){return n},get sampleIndex(){return d(m)},children:(H,K)=>{var b=C(),S=i(b);{var y=$=>{var a=C(),l=i(a);E(l,()=>e.children),r($,a)};Z(S,$=>{e.children&&$(y)})}r(H,b)},$$slots:{default:!0}}),q(o),q(u),r(s,u),M()}export{Te as component};
