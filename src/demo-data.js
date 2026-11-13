export const km = n => Number(n).toLocaleString('ru-RU', {minimumFractionDigits:2,maximumFractionDigits:2});
export const statusText={approved:'Подтверждена',pending:'На проверке',rejected:'Отклонена'};
export const dateLabel=s=>new Date(`${s}T12:00:00`).toLocaleDateString('ru-RU',{day:'numeric',month:'long'});
export function initialWorkouts(){
 const distances=[13.22,10.05,7.30,6.24,5.10,4.50,3.20,2.80,4.10,5.17,10,6.24,4.20];
 return distances.map((distance,i)=>({id:`DEMO-${104-i}`,person:'Участник демоверсии',email:'demo@example.com',date:`2026-11-${String(12-Math.floor(i/2)).padStart(2,'0')}`,distance,duration:i===0?'01:20:08':'00:39:12',pace:i===0?'6:04':'6:17',gps:i===12?'Не виден':'Есть в примере',status:i<11?'approved':i===11?'pending':'rejected',reason:i===11?'Участник запросил ручную проверку.':i===12?'На скриншоте не видны дата и GPS-трек.':'Демонстрационная запись',decision:i===12?'Нужен скриншот с датой и GPS-треком.':'',activity:'Бег на улице',image:null}));
}
export const sampleParticipants=[
 {id:'runner-01',name:'Участник 01',distance:123.45,count:18},
 {id:'runner-02',name:'Участник 02',distance:108.20,count:16},
 {id:'runner-03',name:'Участник 03',distance:94.12,count:14},
 {id:'runner-04',name:'Участник 04',distance:62.15,count:10},
 {id:'runner-05',name:'Участник 05',distance:48.60,count:8}
];
