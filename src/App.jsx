import React,{useState,useEffect} from 'react';
import {DocumentPage} from './Documents';
import {Admin} from './Admin';
import {Auth} from './Auth';
import {Member} from './Member';
import {PwaUpdate} from './Pwa';
import {initialWorkouts,sampleParticipants} from './demo-data';
import {ArrowRight,PersonSimpleRun,ListChecks,Trophy} from '@phosphor-icons/react';
import '@fontsource/montserrat/cyrillic-400.css';
import '@fontsource/montserrat/cyrillic-600.css';
import '@fontsource/montserrat/cyrillic-700.css';
import '@fontsource/montserrat/cyrillic-800.css';
import '@fontsource/open-sans/cyrillic-400.css';
import '@fontsource/open-sans/cyrillic-600.css';

const views=['home','registration','account','history','leaderboard','rules','privacy','consent','admin'];
const getView=()=>views.includes(location.hash.slice(1))?location.hash.slice(1):({'/policy/':'privacy','/consent/':'consent','/rules/':'rules','/history/':'history','/leaderboard/':'leaderboard','/admin/':'admin'}[location.pathname]||'home');
export function App(){
 const [view,setView]=useState(getView),[name,setName]=useState(''),[email,setEmail]=useState(''),[login,setLogin]=useState(false),[expired,setExpired]=useState(false),[endsAt,setEndsAt]=useState(0),[rows,setRows]=useState(initialWorkouts);
 useEffect(()=>{const change=()=>{setView(getView());scrollTo(0,0);};addEventListener('hashchange',change);return()=>removeEventListener('hashchange',change);},[]);
 const go=(next,l=false)=>{setLogin(l);location.hash=next;};
 const reset=()=>{rows.forEach(r=>{if(r.image)URL.revokeObjectURL(r.image);});setRows(initialWorkouts());};
 const expire=()=>{setExpired(true);setEndsAt(0);reset();go('registration',true);};
 useEffect(()=>{if(!endsAt)return;const timer=setInterval(()=>{if(Date.now()>=endsAt)expire();},1000);return()=>clearInterval(timer);},[endsAt]);
 const finish=()=>{setExpired(false);setEndsAt(Date.now()+30*60*1000);go('account');};
 const exit=()=>{reset();setName('');setEmail('');setEndsAt(0);setExpired(false);go('home');};
 const community=sampleParticipants.reduce((sum,r)=>sum+r.distance,0)+rows.filter(r=>r.status==='approved').reduce((sum,r)=>sum+r.distance,0);
 const Progress=()=> <progress className="native-progress" max={9000} value={community} aria-label="Пример общего прогресса"/>;
 const Header=()=> <header className="header"><a className="brand" href="#home" aria-label="Спортфонд — на главную"><img src="/assets/logo.png" alt="Спортфонд"/></a><button className="header-link" onClick={()=>go('registration',true)}>Войти</button></header>;
 let content;
 if(view==='admin')content=<Admin rows={rows} setRows={setRows}/>;
 else if(['rules','privacy','consent'].includes(view))content=<DocumentPage kind={view}/>;
 else if(view==='registration')content=<Auth key={String(login)} login={login} name={name} setName={setName} email={email} setEmail={setEmail} onComplete={finish} onSwitch={()=>{setLogin(!login);setExpired(false);}} expired={expired}/>;
 else if(['account','history','leaderboard'].includes(view))content=<Member view={view} rows={rows} setRows={setRows} name={name} email={email} onExit={exit} onExpire={expire}/>;
 else content=<>
{view==='home'&&<><section className="scenic home-hero"><div className="wrap"><Header/><main id="content" className="hero-copy"><p className="eyebrow">9000 КМ ВМЕСТЕ</p><h1>Спорт, который<br className="desktop-break"/> объединяет Югру</h1><p className="hero-subtitle">Твои тренировки — часть<br className="desktop-break"/> общего пути.</p><button className="button white" onClick={()=>go('registration')}>Присоединиться <ArrowRight weight="bold"/></button><p className="already">Уже с нами? <button className="text-link light" onClick={()=>go('registration',true)}>Войти</button></p></main></div></section><section className="goal wrap"><div><p className="eyebrow muted">ОБЩАЯ ЦЕЛЬ</p><h2 className="goal-number">9 000 <span>км</span></h2></div><div className="goal-detail"><Progress/><p>Каждая подтверждённая тренировка приближает нас к цели.</p><small>Прогресс показан для примера</small></div><div className="steps"><div><PersonSimpleRun/><span>01</span><strong>Тренируйся</strong></div><div><ListChecks/><span>02</span><strong>Загружай скриншот</strong></div><div><Trophy/><span>03</span><strong>Приближай общий старт</strong></div></div></section><footer className="footer wrap"><span>Спорт, который объединяет Югру</span><button className="text-link" onClick={()=>go('rules')}>Правила участия</button><a href="#privacy">Персональные данные</a><a href="#admin">Администратор · демо</a><a href="https://t.me/sportfond86" target="_blank" rel="noreferrer">Telegram</a></footer></>}
 </>;
 return <><button className="skip" onClick={()=>document.getElementById('content')?.scrollIntoView()}>Перейти к содержимому</button>{content}<PwaUpdate/></>;
}
