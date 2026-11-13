export const km = n => n===null||n===undefined?'—':Number(n).toLocaleString('ru-RU', {minimumFractionDigits:2,maximumFractionDigits:2});
export const statusText={approved:'Подтверждена',pending:'На проверке',rejected:'Отклонена'};
export const dateLabel=s=>!s?'Дата не определена':new Date(`${s}T12:00:00`).toLocaleDateString('ru-RU',{day:'numeric',month:'long'});
