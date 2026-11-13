export const FIRST_TRAINING_DATE='2026-10-29';
export function todayISO(){const d=new Date();return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;}
export function approvalError({date,distance,gpsConfirmed,hash,id},rows=[],today=todayISO()){
 if(!/^\d{4}-\d{2}-\d{2}$/.test(date||'')||!Number.isFinite(Date.parse(`${date}T12:00:00Z`))||new Date(`${date}T12:00:00Z`).toISOString().slice(0,10)!==date)return 'Укажи корректную дату тренировки.';
 if(date<FIRST_TRAINING_DATE)return 'В зачёт входят тренировки с 29 октября 2026 года включительно.';
 if(date>today)return 'Дата тренировки не может быть в будущем.';
 if(!Number.isFinite(Number(distance))||Number(distance)<=0)return 'Укажи дистанцию больше нуля.';
 if(!gpsConfirmed)return 'Для зачёта нужно подтвердить GPS-маршрут на скриншоте.';
 if(hash&&rows.some(r=>r.id!==id&&r.hash===hash&&r.status==='approved'))return 'Этот скриншот уже зачтён. Повторный зачёт запрещён.';
 return '';
}
