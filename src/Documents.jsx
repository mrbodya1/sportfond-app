import React from 'react';
import policyText from './legal/policy.md?raw';
import consentText from './legal/consent.md?raw';
import {ArrowLeft,ArrowRight,FileText,ShieldCheck} from '@phosphor-icons/react';

const documents = {
 rules: { label:'УЧАСТИЕ', title:'Правила общего пути', intro:'Тренируемся в своём ритме и вместе приближаемся к цели — 9 000 километров.', sections:[
  ['О проекте','«9000 км вместе» — проект спортивного сообщества Югры. Участник загружает скриншоты собственных тренировок, а после проверки подтверждённые километры пополняют общий счётчик.'],
  ['Как присоединиться','В рабочей версии потребуется указать имя и email, принять правила и отдельно дать согласие на обработку персональных данных. Вход планируется по одноразовому коду из письма. Сейчас форма работает только в демонстрационном режиме.'],
  ['Как добавить тренировку','Подготовь скриншот, на котором читаются дата, дистанция и сведения о тренировке. Для пробежки на улице должен быть виден GPS-трек. Загрузи JPG, PNG или WEBP до 5 МБ. Не размещай на скриншоте чужие данные; по возможности скрой домашний адрес и ненужные личные сведения. Условия зачёта тренировок в помещении ещё согласовываются.'],
  ['Проверка и зачёт','Планируется автоматическое распознавание показателей с возможностью ручной проверки. В общий счётчик попадут только подтверждённые тренировки. Сомнительный результат можно будет передать модератору. Одна и та же тренировка не должна учитываться повторно; чужие и изменённые результаты не принимаются.'],
  ['Если возник вопрос','Модератор должен объяснить причину отклонения. Участник сможет запросить повторную проверку и уточнить результат. Контакт проекта: sportfondhm@ya.ru. Срок ответа и порядок апелляции будут закреплены в окончательной редакции.'],
  ['Что ещё согласовываем','Организатор — АНО «Сообщество любителей массового спорта Югры». Даты старта и окончания, возрастные условия, допустимые виды активности, пороги проверки, призы и сроки рассмотрения пока не утверждены. Исторические условия из старой версии сюда не перенесены. До утверждения этих условий набор настоящих участников не открыт.']
 ]},

};

export function DocumentPage({kind}) {
 if(kind==='privacy'||kind==='consent')return <SuppliedDocument kind={kind}/>;
 const doc=documents[kind];
 return <><section className="scenic document-hero"><div className="wrap"><header className="header"><a className="brand" href="#home" aria-label="Спортфонд — на главную"><img src="/assets/logo.png" alt="Спортфонд"/></a><a className="header-link" href="#registration"><ArrowLeft/> К регистрации</a></header><div className="document-heading"><p className="eyebrow">{doc.label}</p><h1>{doc.title}</h1><p>{doc.intro}</p></div></div></section><main id="content" className="document-layout wrap"><aside className="document-nav"><p className="eyebrow muted">ДОКУМЕНТЫ</p><a href="#rules" aria-current={kind==='rules'?'page':undefined}><FileText/>Правила участия</a><a href="#privacy" aria-current={kind==='privacy'?'page':undefined}><ShieldCheck/>Политика данных</a><a href="#consent" aria-current={kind==='consent'?'page':undefined}><FileText/>Согласие</a><small>Проекты · 13 ноября 2026</small></aside><article className="document-body"><div className="draft-banner"><ShieldCheck/><div><strong>Проект для согласования</strong><p>Регистрация настоящих участников ещё не запущена. Реквизиты и условия предстоит подтвердить.</p></div></div>{doc.sections.map(([title,body],i)=><section key={title}><h2><span>{String(i+1).padStart(2,'0')}</span>{title}</h2><p>{body}</p></section>)}<div className="document-actions"><a className="button primary" href="#registration">К регистрации <ArrowRight/></a><a className="text-link" href="#home">На главную</a></div></article></main></>;
}

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
 const policy=kind==='privacy';
 return <><section className="scenic document-hero"><div className="wrap"><header className="header"><a className="brand" href="#home" aria-label="Спортфонд — на главную"><img src="/assets/logo.png" alt="Спортфонд"/></a><a className="header-link" href="#registration"><ArrowLeft/> К регистрации</a></header><div className="document-heading"><p className="eyebrow">9000 КМ · ДОКУМЕНТЫ</p><h1>{policy?'Политика обработки персональных данных':'Согласие на обработку персональных данных'}</h1><p>АНО «Сообщество любителей массового спорта Югры»</p></div></div></section><main id="content" className="document-layout wrap"><aside className="document-nav"><p className="eyebrow muted">ДОКУМЕНТЫ</p><a href="#rules"><FileText/>Правила участия</a><a href="/policy/" aria-current={policy?'page':undefined}><ShieldCheck/>Политика данных</a><a href="/consent/" aria-current={!policy?'page':undefined}><FileText/>Согласие</a><small>Редакция · 13 ноября 2026</small></aside><article className="document-body supplied-document"><div className="demo-callout">Тестовая версия приложения: регистрация и фиксация согласия на сервере ещё не подключены.</div><DocumentText text={policy?policyText:consentText}/><div className="document-actions"><a className="button primary" href="#registration">К регистрации <ArrowRight/></a><a className="text-link" href="#home">На главную</a></div></article></main></>;
}
