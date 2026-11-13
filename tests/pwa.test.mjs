import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile,access} from 'node:fs/promises';
import vm from 'node:vm';
const root=new URL('../dist/client/',import.meta.url);
async function runtime(){
 const events={};const shell=new Response('cached shell');const asset=new Response('cached asset');
 const scope={self:{location:{origin:'https://example.test'},addEventListener:(name,fn)=>events[name]=fn},URL,caches:{match:async()=>shell,open:async()=>({match:async()=>asset})},fetch:async()=>{throw new Error('offline');}};
 vm.runInNewContext(await readFile(new URL('sw.js',root),'utf8'),scope);
 return {events,shell,asset};
}
test('service worker bypasses API, uploads, POST and cross-origin traffic',async()=>{
 const {events}=await runtime();
 for(const [path,method] of [['/api/session','GET'],['/uploads/private.png','GET'],['/','POST'],['https://other.test/assets/app.js','GET']]){
  let handled=false;
  events.fetch({request:{url:new URL(path,'https://example.test').href,method,mode:'cors'},respondWith:()=>handled=true});
  assert.equal(handled,false,path);
 }
});
test('offline navigation returns cached shell, not user data',async()=>{
 const {events}=await runtime();let response;
 events.fetch({request:{url:'https://example.test/history/',method:'GET',mode:'navigate'},respondWith:p=>response=p});
 assert.equal(await (await response).text(),'cached shell');
});
test('manifest icon sizes and static document routes exist',async()=>{
 const manifest=JSON.parse(await readFile(new URL('manifest.webmanifest',root),'utf8'));
 assert.equal(manifest.scope,'/');assert.equal(manifest.display,'standalone');
 for(const icon of manifest.icons){const buf=await readFile(new URL(icon.src.slice(1),root));const size=Number(icon.sizes.split('x')[0]);assert.equal(buf.readUInt32BE(16),size);assert.equal(buf.readUInt32BE(20),size);}
 for(const name of ['policy','consent','rules','history','leaderboard','admin'])await access(new URL(name+'/index.html',root));
});
