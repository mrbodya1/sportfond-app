import React from 'react';
import policyText from './legal/policy.md?raw';
import consentText from './legal/consent.md?raw';
import rulesText from './legal/rules.md?raw';
import {ArrowLeft,ArrowRight,FileText,ShieldCheck} from '@phosphor-icons/react';

export function DocumentPage({kind}) {return <SuppliedDocument kind={kind}/>;}

function InlineText({text}) {
 return text.split(/(\*\*[^*]+\*\*|https:\/\/[^\s]+)/g).map((part,i)=>{
  if(part.startsWith('**')&&part.endsWith('**'))return <strong key={i}>{part.slice(2,-2)}</strong>;
  if(part.startsWith('https://')) {const url=part.replace(/[.,;]+$/,'');const suffix=part.slice(url.length);return <React.Fragment key={i}><a href={url==='https://app.sportfondhm.ru/policy/'?'/policy/':url}>{url}</a>{suffix}</React.Fragment>;}
  return part;
 });
}
function DocumentText({text}) {
 const blocks=text.trim().split(/\r?\n\s*\r?\n/);
 return blocks.map((block,i)=>{
  if(block.startsWith('# '))return null;
  if(block.startsWith('### '))return <h2 key={i}>{block.slice(4)}</h2>;
  if(block.split(/\r?\n/).every(line=>line.startsWith('- ')))return <ul key={i}>{block.split(/\r?\n/).map((line,j)=><li key={j}><InlineText text={line.slice(2)}/></li>)}</ul>;
  return <p key={i}><InlineText text={block}/></p>;
 });
}
function SuppliedDocument({kind}) {
 const policy=kind==='privacy',rules=kind==='rules';
 return <><section className="scenic document-hero"><div className="wrap"><header className="header"><a className="brand" href="#home" aria-label="Спортфонд — на главную"><img src="/assets/logo.png" alt="Спортфонд"/></a><a className="header-link" href="#registration"><ArrowLeft/> К регистрации</a></header><div className="document-heading"><p className="eyebrow">9000 КМ · ДОКУМЕНТЫ</p><h1>{rules?'Правила общего пути':policy?'Политика обработки персональных данных':'Согласие на обработку персональных данных'}</h1><p>АНО «Сообщество любителей массового спорта Югры»</p></div></div></section><main id="content" className="document-layout wrap"><aside className="document-nav"><p className="eyebrow muted">ДОКУМЕНТЫ</p><a href="/rules/" aria-current={rules?'page':undefined}><FileText/>Правила участия</a><a href="/policy/" aria-current={policy?'page':undefined}><ShieldCheck/>Политика данных</a><a href="/consent/" aria-current={kind==='consent'?'page':undefined}><FileText/>Согласие</a><small>Редакция · 13 ноября 2026</small></aside><article className="document-body supplied-document"><DocumentText text={rules?rulesText:policy?policyText:consentText}/><div className="document-actions"><a className="button primary" href="#registration">К регистрации <ArrowRight/></a><a className="text-link" href="#home">На главную</a></div></article></main></>;
}
