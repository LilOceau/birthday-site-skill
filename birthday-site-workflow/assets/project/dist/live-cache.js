'use strict';
// HTTP cache persists resources; only a bounded Live Blob LRU stays in memory.
window.LiveMediaCache=(()=>{
  const version=window.BIRTHDAY_CONTENT?.mediaVersion||'1',limit=12*1024*1024;
  const entries=new Map(),jobs=new Map(),catalog=new Set(),done=new Set(),failures=new Map(),busy=new Set();
  let near=new Set(),bytes=0,running=0,scheduled=false,cooldown=0,wakeTimer=null;
  const isLive=src=>/\.live\.mp4(?:[?#]|$)/.test(src);
  const url=src=>isLive(src)?src+(src.includes('?')?'&':'?')+'liveVersion='+version:src;
  const canWarm=()=>window.BIRTHDAY_CONTENT?.config?.behavior?.backgroundPreload!==false&&!document.hidden&&navigator.onLine!==false&&!navigator.connection?.saveData&&!busy.size&&Date.now()>=cooldown;
  const abortError=()=>new DOMException('Cancelled','AbortError');
  function assets(photos,live=true){
    const clips=live?photos.filter(p=>p.type==='live').map(p=>p.src):[];
    return [...new Set(clips.concat(photos.flatMap(p=>[p.type==='live'||p.type==='video'?p.poster:p.preview||p.src,p.thumb]).filter(Boolean)))];
  }
  function remember(src,blob){
    done.add(src);failures.delete(src);
    if(!isLive(src)||blob.size>limit)return;
    if(entries.has(src)){bytes-=entries.get(src).size;entries.delete(src);}
    entries.set(src,blob);bytes+=blob.size;
    while(bytes>limit){const first=entries.keys().next().value;bytes-=entries.get(first).size;entries.delete(first);}
  }
  function kick(){if(!scheduled){scheduled=true;queueMicrotask(()=>{scheduled=false;pump();});}}
  function cancel(job){
    if(jobs.get(job.src)!==job)return;
    jobs.delete(job.src);job.cancelled=true;
    if(job.running)job.controller.abort();else job.reject(abortError());
  }
  function makeJob(src,priority){
    const job={src,priority,running:false,cancelled:false};
    job.promise=new Promise((resolve,reject)=>{job.resolve=resolve;job.reject=reject;});jobs.set(src,job);return job;
  }
  function candidate(){return [...near,...catalog].find(src=>!done.has(src)&&!jobs.has(src)&&(failures.get(src)||0)<2);}
  function pump(){
    while(running<2){
      let job=[...jobs.values()].filter(j=>!j.running&&(j.priority===0||canWarm())).sort((a,b)=>a.priority-b.priority)[0];
      if(!job&&canWarm()){
        const src=candidate();if(src){job=makeJob(src,near.has(src)?1:2);job.promise.catch(()=>{});}
      }
      if(!job)return;
      job.running=true;running++;job.controller=new AbortController();
      job.timer=setTimeout(()=>job.controller.abort(),15000);
      fetch(url(job.src),{signal:job.controller.signal,cache:'default',priority:job.priority===0?'high':'low'})
        .then(response=>{if(!response.ok)throw new Error('HTTP '+response.status);return response.blob();})
        .then(blob=>{if(!blob.size)throw new Error('Empty resource');if(job.cancelled)throw abortError();remember(job.src,blob);job.resolve(blob);})
        .catch(error=>{
          if(!job.cancelled){
            failures.set(job.src,(failures.get(job.src)||0)+1);
            // Back off on unstable networks. Foreground retries bypass this pause.
            cooldown=Date.now()+5000;clearTimeout(wakeTimer);wakeTimer=setTimeout(kick,5000);
          }
          job.reject(error);
        })
        .finally(()=>{clearTimeout(job.timer);if(jobs.get(job.src)===job)jobs.delete(job.src);running--;kick();});
    }
  }
  function get(src,priority=0){
    if(entries.has(src)){const blob=entries.get(src);entries.delete(src);entries.set(src,blob);return Promise.resolve(blob);}
    const job=jobs.get(src)||makeJob(src,priority);job.priority=Math.min(job.priority,priority);
    if(priority===0&&job.timer){clearTimeout(job.timer);job.timer=setTimeout(()=>job.controller.abort(),15000);}
    if(priority===0&&!job.running&&running>=2){
      const background=[...jobs.values()].filter(j=>j.running&&j.priority>0).sort((a,b)=>b.priority-a.priority)[0];if(background)cancel(background);
    }
    kick();return job.promise;
  }
  function warm(photos,{live=true}={}){
    near=new Set(assets(photos,live));
    // Retain the catalog so interrupted background downloads resume later.
    for(const src of near)catalog.add(src);
    for(const job of [...jobs.values()])if(job.priority>0){
      job.priority=near.has(job.src)?1:2;
      if(job.running&&!near.has(job.src)&&[...near].some(src=>!done.has(src)&&!jobs.has(src)))cancel(job);
    }
    kick();
  }
  function start(photos,{live=true}={}){for(const src of assets(photos,live))catalog.add(src);kick();}
  function cancelCurrent(){for(const job of [...jobs.values()])if(job.priority===0)cancel(job);kick();}
  function setForegroundBusy(key,value){
    if(value)busy.add(key);else busy.delete(key);
    if(value)for(const job of [...jobs.values()])if(job.priority>0)cancel(job);
    kick();
  }
  function suspend(){for(const job of [...jobs.values()])if(job.priority>0)cancel(job);}
  document.addEventListener('visibilitychange',()=>{if(document.hidden)suspend();else kick();});
  window.addEventListener('offline',suspend);
  window.addEventListener('online',()=>{failures.clear();cooldown=0;clearTimeout(wakeTimer);kick();});
  navigator.connection?.addEventListener?.('change',()=>{if(navigator.connection.saveData)suspend();else kick();});
  return {get,warm,start,cancelCurrent,setForegroundBusy};
})();
