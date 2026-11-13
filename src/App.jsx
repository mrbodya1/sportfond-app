import React,{useState,useEffect} from 'react';
import {DocumentPage} from './Documents';
import {Admin} from './Admin';
import {Auth} from './Auth';
import {Member} from './Member';
import {PwaUpdate} from './Pwa';
import {api} from './api';
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
 const [view,setView]=useState(getView),[name,setName]=useState(''),[email,setEmail]=useState(''),[login,setLogin]=useState(false),[expired,setExpired]=useState(false),[data,setData]=useState({user:null,workouts:[],admin_workouts:[],participants:[],total:0}),[loading,setLoading]=useState(true),[error,setError]=useState('');
 const go=(next,l=false)=>{setLogin(l);location.hash=next;};
 const refresh=async()=>{const state=await api('/session');setData(state);setError('');return state;};
 useEffect(()=>{refresh().catch(e=>setError(e.message)).finally(()=>setLoading(false));const change=()=>{setView(getView());scrollTo(0,0);};const expire=()=>{setData(d=>({...d,user:null,workouts:[],admin_workouts:[]}));setExpired(true);go('registration',true);};addEventListener('hashchange',change);addEventListener('sf-auth-required',expire);return()=>{removeEventListener('hashchange',change);removeEventListener('sf-auth-required',expire);};},[]);
 const finish=async()=>{await refresh();setExpired(false);go('account');};
 const exit=async()=>{try{await api('/auth/logout',{});setData(d=>({...d,user:null,workouts:[],admin_workouts:[]}));go('home');}catch(e){setError(e.message);}};
 const mutate=async(id,action,body={})=>{const state=await api(`/workouts/${id}/${action}`,body);setData(state);return state;};
 const community=data.total||0;
 const Progress=()=> <progress className="native-progress" max={9000} value={community} aria-label="Общий прогресс"/>;
 const Header=()=> <header className="header"><a className="brand" href="#home" aria-label="Спортфонд — на главную"><img src="/assets/logo.png" alt="Спортфонд"/></a><button className="header-link" onClick={()=>go(data.user?'account':'registration',true)}>{data.user?'Кабинет':'Войти'}</button></header>;
 const auth=<Auth key={String(login)} login={login} name={name} setName={setName} email={email} setEmail={setEmail} onComplete={finish} onSwitch={()=>{setLogin(!login);setExpired(false);}} expired={expired}/>;
 let content;
 if(['rules','privacy','consent'].includes(view))content=<DocumentPage kind={view}/>;
 else if(loading)content=<main id="content" className="wrap empty-state"><p role="status">Загружаем приложение…</p></main>;
 else if(error)content=<main id="content" className="wrap empty-state"><h1>Нет связи с сервером</h1><p role="alert">{error}</p><button className="button primary" onClick={()=>refresh().catch(e=>setError(e.message))}>Повторить</button></main>;
 else if(view==='registration'||(['account','history','leaderboard','admin'].includes(view)&&!data.user))content=auth;
 else if(view==='admin')content=data.user.is_admin?<Admin rows={data.admin_workouts||[]} onDecision={(id,body)=>mutate(id,'decision',body)}/>:<main id="content" className="wrap empty-state"><h1>Доступ ограничен</h1><p>Этот аккаунт не является администратором.</p><a href="#account">В кабинет</a></main>;
 else if(['account','history','leaderboard'].includes(view))content=<Member view={view} rows={data.workouts} name={data.user.name} email={data.user.email} isAdmin={data.user.is_admin} participants={data.participants} community={community} onRefresh={setData} onDelete={id=>mutate(id,'delete')} onRestore={id=>mutate(id,'restore')} onExit={exit}/>;
 else content=<>
{view==='home'&&<><section className="scenic home-hero"><div className="wrap"><Header/><main id="content" className="hero-copy"><p className="eyebrow">9000 КМ ВМЕСТЕ</p><h1>Спорт, который<br className="desktop-break"/> объединяет Югру</h1><p className="hero-subtitle">Твои тренировки — часть<br className="desktop-break"/> общего пути.</p><button className="button white" onClick={()=>go('registration')}>Присоединиться <ArrowRight weight="bold"/></button><p className="already">Уже с нами? <button className="text-link light" onClick={()=>go('registration',true)}>Войти</button></p></main></div></section><section className="goal wrap"><div><p className="eyebrow muted">ОБЩАЯ ЦЕЛЬ</p><h2 className="goal-number">9 000 <span>км</span></h2></div><div className="goal-detail"><Progress/><p>Каждая подтверждённая тренировка приближает нас к цели.</p><small>{community.toLocaleString('ru-RU')} км подтверждено</small></div><div className="steps"><div><PersonSimpleRun/><span>01</span><strong>Тренируйся</strong></div><div><ListChecks/><span>02</span><strong>Загружай скриншот</strong></div><div><Trophy/><span>03</span><strong>Приближай общий старт</strong></div></div></section><footer className="footer wrap"><span>Спорт, который объединяет Югру</span><button className="text-link" onClick={()=>go('rules')}>Правила участия</button><a href="#privacy">Персональные данные</a><a href="#admin">Администратор</a><a href="https://t.me/sportfond86" target="_blank" rel="noreferrer">Telegram</a></footer></>}
 </>;
 return <><button className="skip" onClick={()=>document.getElementById('content')?.scrollIntoView()}>Перейти к содержимому</button>{content}<PwaUpdate/></>;
}
