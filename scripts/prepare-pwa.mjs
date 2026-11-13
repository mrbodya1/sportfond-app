import {readFile,writeFile,readdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
const root=new URL('../dist/client/',import.meta.url);
const shell=['/','/index.html','/manifest.webmanifest','/icons/icon-192.png','/icons/icon-512.png','/icons/apple-touch-icon.png','/assets/logo.png','/assets/yugra-hero.webp'];
for(const name of await readdir(new URL('assets/',root)))if(/\.(js|css|woff2?)$/.test(name))shell.push('/assets/'+name);
const html=await readFile(new URL('index.html',root),'utf8');
const digest=createHash('sha256').update(html).update(JSON.stringify(shell));
for(const path of shell)digest.update(await readFile(new URL(path==='/'?'index.html':path.slice(1),root)));
const version=digest.digest('hex').slice(0,12);
const worker=`const CACHE='sportfond-shell-${version}';
const SHELL=${JSON.stringify(shell)};
self.addEventListener('install',event=>event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(SHELL))));
self.addEventListener('message',event=>{if(event.data?.type==='SKIP_WAITING')self.skipWaiting();});
self.addEventListener('activate',event=>event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith('sportfond-shell-')&&k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',event=>{
 const req=event.request;const url=new URL(req.url);
 if(req.method!=='GET'||url.origin!==self.location.origin||url.pathname.startsWith('/api/')||url.pathname.startsWith('/uploads/'))return;
 if(req.mode==='navigate'){event.respondWith(fetch(req).catch(()=>caches.match('/index.html')));return;}
 if(!SHELL.includes(url.pathname))return;
 event.respondWith(caches.open(CACHE).then(async cache=>(await cache.match(url.pathname))||fetch(req)));
});
`;
await writeFile(new URL('sw.js',root),worker);
console.log('Prepared versioned app-shell service worker');
