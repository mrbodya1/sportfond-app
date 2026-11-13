import React,{useRef,useEffect,useState} from 'react';
import {X,MagnifyingGlassPlus,MagnifyingGlassMinus,ArrowCounterClockwise} from '@phosphor-icons/react';
export function ImageViewer({src,onClose}){
 const dialog=useRef(null);const [zoom,setZoom]=useState(1);
 useEffect(()=>{if(src){setZoom(1);dialog.current.showModal();}else dialog.current?.close();},[src]);
 return <dialog className="image-viewer" ref={dialog} onCancel={onClose} aria-label="Просмотр скриншота"><div className="image-toolbar"><span>Скриншот тренировки</span><button onClick={()=>setZoom(z=>Math.max(.5,z-.25))} aria-label="Уменьшить"><MagnifyingGlassMinus/></button><output aria-live="polite">{Math.round(zoom*100)}%</output><button onClick={()=>setZoom(z=>Math.min(3,z+.25))} aria-label="Увеличить"><MagnifyingGlassPlus/></button><button onClick={()=>setZoom(1)} aria-label="Сбросить масштаб"><ArrowCounterClockwise/></button><button onClick={onClose} aria-label="Закрыть скриншот"><X/></button></div><div className="image-pan">{src&&<img src={src} alt="Оригинал выбранного скриншота тренировки" style={{width:`${zoom*100}%`,maxWidth:'none'}}/>}</div></dialog>;
}
