export function reviewRows(rows, filter, search='') {
 const query=search.toLowerCase();
 return rows.filter(r=>(filter==='all'||r.status===filter)&&[r.person,r.id,r.email].join(' ').toLowerCase().includes(query));
}
export function activeReview(rows, selected) {
 return rows.find(r=>r.id===selected)||rows[0]||null;
}
