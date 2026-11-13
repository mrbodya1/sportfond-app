import React,{useState,useEffect,useRef} from 'react';
import {ArrowRight,Clock} from '@phosphor-icons/react';
import {km,dateLabel} from './demo-data';
import {api} from './api';
export function OpenAIRecognition({file,onAdd}){
 const [busy,setBusy]=useState(false),[result,setResult]=useState(null),[error,setError]=useState('');
 const abort=useRef(null);
 useEffect(()=>{abort.current?.abort();abort.current=null;setResult(null);setError('');setBusy(false);return()=>{abort.current?.abort();abort.current=null;};},[file]);
 const check=async()=>{if(!file)return;setBusy(true);setError('');const controller=new AbortController();abort.current=controller;const timer=setTimeout(()=>controller.abort(),65000);try{
  const image=await new Promise((resolve,reject)=>{const r=new FileReader();r.onload=()=>resolve(r.result);r.onerror=reject;r.readAsDataURL(file);});
  if(controller.signal.aborted)return;
  const data=await api('/recognition',{image,allow_openai_processing:true},controller.signal);
  if(abort.current!==controller)return;
  onAdd(data);setResult({...data,workout:data.workouts.find(r=>r.id===data.workout_id)});
 }catch(e){if(abort.current===controller)setError(e.name==='AbortError'?'Время ожидания истекло. Проверь историю перед повторной отправкой.':e.message);}finally{clearTimeout(timer);if(abort.current===controller)setBusy(false);}};
 const restore=async()=>{setBusy(true);try{const data=await api(`/workouts/${result.workout_id}/restore`,{});onAdd(data);setResult({...data,workout_id:result.workout_id,workout:data.workouts.find(r=>r.id===result.workout_id)});}catch(e){setError(e.message);}finally{setBusy(false);}};
 const row=result?.workout;
 return <section aria-label="Отправка тренировки"><button className="button primary" onClick={check} disabled={!file||busy||Boolean(result)}>{busy?'Отправляем…':'Отправить'}{busy?<Clock/>:<ArrowRight/>}</button>{!file&&<p className="form-note">Сначала выбери изображение выше.</p>}{error&&<p className="error" role="alert">{error}</p>}<div aria-live="polite">{busy&&<p className="form-note">Обработка может занять несколько секунд.</p>}{result&&<div className="recognition-result"><h3>{result.duplicate?'Уже загружена':row?.status==='approved'?'Тренировка засчитана':row?.status==='pending'?'На ручной проверке':'Тренировка не засчитана'}</h3>{row&&<><dl className="result-metrics"><div><dt>Дистанция</dt><dd>{km(row.distance)} км</dd></div><div><dt>Дата тренировки</dt><dd>{dateLabel(row.date)}</dd></div></dl><p>{row.reason}</p></>}{result.duplicate&&<p>Повторная загрузка не добавляет километры.</p>}{result.deleted&&<><p>Эта тренировка была удалена из истории.</p><button className="button primary" onClick={restore} disabled={busy}>Восстановить тренировку</button></>}<p className="form-note">Результат хранится на сервере. <a href="#history">Открыть историю</a></p></div>}</div></section>;
}
