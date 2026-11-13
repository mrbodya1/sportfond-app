import React,{useState,useEffect} from 'react';
import {DownloadSimple,ArrowClockwise,X} from '@phosphor-icons/react';
let installEvent=null;
const listeners=new Set();
window.addEventListener('beforeinstallprompt',e=>{e.preventDefault();installEvent=e;listeners.forEach(fn=>fn());});
window.addEventListener('appinstalled',()=>{installEvent=null;listeners.forEach(fn=>fn());});
export function InstallApp(){
 const [show,setShow]=useState(false),[,render]=useState(0);
 useEffect(()=>{const fn=()=>render(n=>n+1);listeners.add(fn);return()=>listeners.delete(fn);},[]);
 const standalone=window.matchMedia('(display-mode: standalone)').matches||navigator.standalone;
 if(standalone)return null;
 const install=async()=>{if(installEvent){const prompt=installEvent;installEvent=null;await prompt.prompt();await prompt.userChoice;render(n=>n+1);}else setShow(!show);};
 return <section className="install-card"><DownloadSimple/><div><h3>Всегда под рукой</h3><p>Добавь «9000 км» на экран телефона.</p><button className="text-link" onClick={install}>{installEvent?'Установить приложение':'Как установить'}</button>{show&&<div className="install-instructions"><p><strong>iPhone / Safari:</strong> открой меню «Поделиться» и выбери «На экран Домой».</p><p><strong>Android / Chrome:</strong> в меню браузера выбери «Установить приложение» или «Добавить на главный экран».</p><p className="form-note">Нужен HTTPS или локальный адрес. Автоматическое предложение появится в поддерживающем браузере на рабочей сборке.</p></div>}</div></section>;
}
export function PwaUpdate(){
 const [worker,setWorker]=useState(null),[dismissed,setDismissed]=useState(false),[failed,setFailed]=useState(false);
 useEffect(()=>{if(!import.meta.env.PROD||!('serviceWorker' in navigator))return;let mounted=true;let refreshing=false;const reload=()=>{if(refreshing)location.reload();};navigator.serviceWorker.addEventListener('controllerchange',reload);navigator.serviceWorker.register('/sw.js',{updateViaCache:'none'}).then(reg=>{if(!mounted)return;if(reg.waiting)setWorker(reg.waiting);reg.addEventListener('updatefound',()=>{const w=reg.installing;w?.addEventListener('statechange',()=>{if(w.state==='installed'&&navigator.serviceWorker.controller&&mounted){setWorker(w);setDismissed(false);}});});}).catch(()=>{if(mounted)setFailed(true);});const handler=()=>{refreshing=true;};window.addEventListener('sportfond-update',handler);return()=>{mounted=false;navigator.serviceWorker.removeEventListener('controllerchange',reload);window.removeEventListener('sportfond-update',handler);};},[]);
 if(failed)return <div className="pwa-update" role="status">Офлайн-режим не подключился. Можно продолжить в браузере.</div>;
 if(!worker||dismissed)return null;
 return <div className="pwa-update" role="status"><ArrowClockwise/><span>Доступна новая версия. Обновление сбросит демоданные и выбранные файлы.</span><button className="text-link" onClick={()=>{window.dispatchEvent(new Event('sportfond-update'));worker.postMessage({type:'SKIP_WAITING'});}}>Обновить</button><button className="icon-button" onClick={()=>setDismissed(true)} aria-label="Отложить обновление"><X/></button></div>;
}
