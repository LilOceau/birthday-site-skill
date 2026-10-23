'use strict';
// Requested positions may advance while the visible photo and its metadata stay together.
const dialog=$('#photoDialog'),stage=$('.viewer-stage');
let currentAlbum=null,photoIndex=0,displayedIndex=-1,previousFocus;
let albumRender=0,mediaSession=0,frameDimensions=null,photoAnimation=null;
let viewerVideo=$('#viewerVideo'),pendingVideo=null;
let liveSession=0,liveMotionEnabled=false;
let liveLoadTimer=null,liveDeadline=null,liveRetryTimer=null;
const liveStills=new Map();
let loadTimer=null,loadTimeout=null,hdLoaded=false;
let hdState=null,hdTimer=null,hdTimeout=null;
let zoom=1,panX=0,panY=0;
const pointers=new Map();let gesture=null,lastTap=null,lastTouchTime=0;
function fitPhotoFrame(width,height){
  if(width>0&&height>0)frameDimensions={width,height};
  if(!frameDimensions)return;
  const border=parseFloat(getComputedStyle($('#activePhoto')).paddingLeft)||0;
  const w=stage.clientWidth-2*border,h=stage.clientHeight-2*border;
  if(w<=0||h<=0)return;
  const scale=Math.min(w/frameDimensions.width,h/frameDimensions.height);
  stage.style.setProperty('--frame-width',(frameDimensions.width*scale+2*border)+'px');
  stage.style.setProperty('--frame-height',(frameDimensions.height*scale+2*border)+'px');
  applyZoom();
}
let frameResizeRequest=0;
const frameObserver=new ResizeObserver(()=>{
  cancelAnimationFrame(frameResizeRequest);
  frameResizeRequest=requestAnimationFrame(()=>{frameResizeRequest=0;if(dialog.open)fitPhotoFrame();});
});frameObserver.observe(stage);
function showStatus(text){$('#viewerStatus').textContent=text;$('#viewerStatus').hidden=!text;}
function mediaReady(){
  clearTimeout(loadTimer);clearTimeout(loadTimeout);loadTimer=null;loadTimeout=null;
  stage.setAttribute('aria-busy','false');showStatus('');
  window.LiveMediaCache?.setForegroundBusy('viewer',false);
}
function beginMediaLoad(label='正在加载…'){
  mediaReady();const session=++mediaSession;
  stage.setAttribute('aria-busy','true');$('#imageError').hidden=true;
  window.LiveMediaCache?.setForegroundBusy('viewer',true);
  loadTimer=setTimeout(()=>{if(session===mediaSession&&dialog.open)showStatus(label);},350);
  loadTimeout=setTimeout(()=>{if(session===mediaSession)mediaFailure('加载有点久，请重试。');},20000);
  return session;
}
function visiblePhoto(){return currentAlbum?.photos[displayedIndex];}
function originalSource(photo){return photo?.original||(photo?.preview?photo.src:null);}
function updateTools(){
  const photo=visiblePhoto(),isImage=!!photo&&photo.type!=='video';
  const pending=photoIndex!==displayedIndex;
  $('#zoomIn').disabled=!isImage||zoom>=5;$('#zoomOut').disabled=!isImage||zoom<=1;$('#resetZoom').disabled=!isImage;
  $('#toggleLive').hidden=photo?.type!=='live';$('#toggleLive').disabled=pending;
  $('#toggleLive').textContent=liveMotionEnabled?'暂停动态':'恢复动态';
  $('#toggleLive').setAttribute('aria-pressed',String(liveMotionEnabled));
}
function updateNavigation(){
  $('#previousPhoto').disabled=photoIndex<=0;
  $('#nextPhoto').disabled=!currentAlbum||photoIndex>=currentAlbum.photos.length-1;
  updateTools();
}
function mediaFailure(message='这张照片暂时无法加载，请重试。'){
  mediaSession++;clearLivePlayback(true);liveMotionEnabled=false;mediaReady();
  if(pendingVideo){pendingVideo.removeAttribute('src');pendingVideo.load();pendingVideo=null;}
  if(displayedIndex<0){$('#imageError').hidden=false;$('#imageError').textContent=message;}
  else{photoIndex=displayedIndex;showStatus(message+' 仍显示当前图片。');}
  $('#retryMedia').hidden=false;updateNavigation();
}
function stopVideo(video=viewerVideo){
  video.pause();video.removeAttribute('src');video.load();
  if(video.dataset.objectUrl){URL.revokeObjectURL(video.dataset.objectUrl);delete video.dataset.objectUrl;}
}
function clearLivePlayback(keepImage=false){
  liveSession++;
  clearTimeout(liveLoadTimer);clearTimeout(liveDeadline);clearTimeout(liveRetryTimer);
  window.LiveMediaCache?.cancelCurrent();
  if(viewerVideo.dataset.live==='true'){viewerVideo.pause();if(!keepImage)stopVideo();}
  if(pendingVideo?.dataset.live==='true'){const video=pendingVideo;pendingVideo=null;stopVideo(video);video.remove();}
}
function prepareLiveStill(photo){
  const src=photo.poster||photo.thumb;
  if(!liveStills.has(src)){
    const image=new Image();image.decoding='async';image.src=src;
    const promise=image.decode().then(()=>image);liveStills.set(src,promise);
    promise.catch(()=>{if(liveStills.get(src)===promise)liveStills.delete(src);});
  }
  return liveStills.get(src);
}
function swapImage(image){
  photoAnimation?.cancel();const old=$('#viewerImage');
  image.id='viewerImage';image.hidden=false;image.draggable=false;image.alt=image.alt||old.alt;
  old.replaceWith(image);viewerVideo.hidden=true;stopVideo();
  fitPhotoFrame(image.naturalWidth,image.naturalHeight);applyZoom();
}
function loadViewerImage(src,{onReady,onError,label,session=beginMediaLoad(label)}={}){
  const image=new Image();
  image.fetchPriority='high';
  image.decoding='async';image.draggable=false;
  const valid=()=>session===mediaSession&&dialog.open;
  const fail=()=>{if(valid()){mediaFailure();onError?.();}};
  image.addEventListener('load',async()=>{
    if(!valid())return;
    try{await image.decode();}catch{fail();return;}
    if(!valid())return;
    swapImage(image);mediaReady();onReady?.();
  });
  image.addEventListener('error',fail);image.src=src;return image;
}
function commitPhoto(index,render){
  if(render!==albumRender)return;
  displayedIndex=index;photoIndex=index;hdLoaded=false;resetZoom();
  const photo=visiblePhoto();
  rememberPhoto(currentAlbum.progressKey||currentAlbum.date,photo);
  if(currentAlbum.progressKey==='collage'&&displayedCollageIndex!==index){
    collageIndex=index;renderCollage();
  }
  $('#viewerTitle').textContent=currentAlbum.title;
  $('#viewerImage').alt=photo.caption||currentAlbum.title+'，第 '+(index+1)+' 张';
  $('#mediaType').textContent=photo.type==='live'?'Live 照片':photo.type==='video'?'视频':'照片';
  $('#photoCaption').textContent=photo.caption||'';
  $('#photoCounter').textContent=(index+1)+' / '+currentAlbum.photos.length;
  [...$('#photoThumbnails').children].forEach((button,i)=>button.setAttribute('aria-current',String(i===index)));
  $('#photoThumbnails').children[index]?.scrollIntoView({block:'nearest',inline:'nearest',behavior:'instant'});
  ['#stackBack','#stackMiddle'].forEach((selector,offset)=>{
    const item=currentAlbum.photos[index+2-offset],previous=$(selector),image=new Image();
    image.id=selector.slice(1);image.className=previous.className;image.alt='';image.hidden=true;image.setAttribute('aria-hidden','true');previous.replaceWith(image);
    if(item){image.addEventListener('load',async()=>{try{await image.decode();}catch{return;}if(render===albumRender&&image===$(selector))image.hidden=false;});image.src=item.thumb||item.poster||item.preview||item.src;}
  });
  $('#retryMedia').hidden=true;updateNavigation();
  applyAutomaticHD();
  window.LiveMediaCache?.warm(currentAlbum.photos.slice(index,index+4).concat(currentAlbum.photos.slice(Math.max(0,index-1),index)),{live:!reduceMotion});
}
function loadViewerVideo(photo,onReady){
  const session=beginMediaLoad(),video=document.createElement('video');pendingVideo=video;
  const valid=()=>session===mediaSession&&dialog.open;
  video.id='viewerVideo';video.dataset.live='false';video.controls=true;video.playsInline=true;video.preload='auto';
  video.setAttribute('playsinline','');video.setAttribute('webkit-playsinline','');
  video.poster=photo.poster||photo.thumb||'';
  video.setAttribute('aria-label',photo.caption||'回忆视频');
  video.addEventListener('loadeddata',()=>{
    if(!valid())return;
    stopVideo();viewerVideo.replaceWith(video);viewerVideo=video;pendingVideo=null;
    $('#viewerImage').hidden=true;video.hidden=false;fitPhotoFrame(video.videoWidth,video.videoHeight);
    clearLivePlayback();mediaReady();onReady?.();applyZoom();
  },{once:true});
  video.addEventListener('error',()=>{if(valid())mediaFailure('视频暂时无法加载，请重试。');});
  video.src=photo.src;
}
async function pauseLivePhoto(){
  const photo=visiblePhoto();if(photo?.type!=='live')return;
  clearLivePlayback(true);const session=liveSession,media=++mediaSession;
  liveMotionEnabled=false;updateTools();
  try{
    const image=hdState?.ready&&hdState.photo===photo?hdState.image:await prepareLiveStill(photo);
    if(session!==liveSession||media!==mediaSession||!dialog.open)return;
    image.alt=photo.caption||'';swapImage(image);clearLivePlayback();mediaReady();applyAutomaticHD();
  }catch{if(session===liveSession)mediaFailure();}
}
function startLivePhoto(photo){
  clearLivePlayback(true);
  const session=liveSession,render=albumRender;
  const valid=()=>session===liveSession&&render===albumRender&&dialog.open&&visiblePhoto()===photo&&photoIndex===displayedIndex;
  liveMotionEnabled=true;$('#retryMedia').hidden=true;showStatus('');updateTools();
  liveLoadTimer=setTimeout(()=>{if(valid())showStatus('动态正在加载，可继续翻看');},350);
  function failed(message){
    if(!valid())return;
    clearLivePlayback(true);liveMotionEnabled=false;
    viewerVideo.hidden=true;$('#viewerImage').hidden=false;stopVideo();applyAutomaticHD();
    showStatus(message);$('#retryMedia').hidden=false;
    retryAction=()=>startLivePhoto(photo);updateTools();
  }
  async function attempt(number=0){
    try{
      const blob=await window.LiveMediaCache.get(photo.src);
      if(!valid())return;
      const video=document.createElement('video');pendingVideo=video;
      video.dataset.live='true';video.id='pendingLiveVideo';video.hidden=true;
      video.muted=true;video.defaultMuted=true;video.playsInline=true;video.preload='auto';video.loop=false;
      video.setAttribute('muted','');video.setAttribute('playsinline','');video.setAttribute('webkit-playsinline','');
      video.setAttribute('aria-label',photo.caption||'回忆动态');
      video.dataset.objectUrl=URL.createObjectURL(blob);video.src=video.dataset.objectUrl;
      $('#activePhoto').append(video);
      liveDeadline=setTimeout(()=>failed('动态暂时无法播放，照片仍可查看；可轻触“恢复动态”重试'),10000);
      video.addEventListener('playing',()=>{
        if(!valid())return;
        clearTimeout(liveDeadline);clearTimeout(liveLoadTimer);showStatus('');
        if(pendingVideo===video){
          stopVideo();viewerVideo.replaceWith(video);viewerVideo=video;pendingVideo=null;video.id='viewerVideo';
          $('#viewerImage').hidden=true;video.hidden=false;fitPhotoFrame(video.videoWidth,video.videoHeight);
        }
        updateTools();
      });
      video.addEventListener('waiting',()=>{
        if(!valid())return;clearTimeout(liveDeadline);
        liveDeadline=setTimeout(()=>failed('动态播放暂时中断，照片仍可查看；可重试'),10000);
      });
      video.addEventListener('error',()=>{if(valid())failed('动态暂时无法播放，照片仍可查看；可轻触“恢复动态”重试');});
      video.addEventListener('ended',()=>{if(valid())pauseLivePhoto();});
      // Request muted inline playback immediately, rather than waiting for a
      // preload event that mobile browsers may choose not to deliver.
      try{await video.play();}catch(error){
        if(valid())failed(error.name==='NotAllowedError'?'轻触“恢复动态”播放':'动态暂时无法播放，照片仍可查看；可轻触“恢复动态”重试');
      }
    }catch{
      if(!valid())return;
      if(number===0){showStatus('动态连接稍慢，正在重试；可继续翻看');liveRetryTimer=setTimeout(()=>{if(valid())attempt(1);},700);}
      else failed('动态加载未完成，照片仍可查看；可轻触“恢复动态”重试');
    }
  }
  attempt();
}
function renderThumbnails(){
  $('#photoThumbnails').replaceChildren(...currentAlbum.photos.map((photo,index)=>{
    const button=document.createElement('button');button.type='button';button.className='photo-thumbnail';
    button.setAttribute('aria-label','查看第 '+(index+1)+' 项');button.setAttribute('aria-current','false');
    const img=new Image();img.src=photo.thumb||photo.poster||photo.preview||photo.src;img.alt='';img.loading='lazy';
    const label=document.createElement('span');label.textContent=String(index+1)+(photo.type==='live'?' · Live':photo.type==='video'?' · 视频':'');
    button.append(img,label);button.addEventListener('click',()=>{photoIndex=index;renderPhoto();});return button;
  }));
}
let retryAction=null;
function renderPhoto(){
  const index=photoIndex,photo=currentAlbum.photos[index],render=++albumRender;
  mediaSession++;clearLivePlayback(true);viewerVideo.pause();
  if(pendingVideo){stopVideo(pendingVideo);pendingVideo=null;}
  liveMotionEnabled=false;$('#retryMedia').hidden=true;updateNavigation();
  retryAction=()=>{photoIndex=index;renderPhoto();};
  beginAutomaticHD(photo,index,render);
  const ready=()=>commitPhoto(index,render);
  if(photo.type==='video')loadViewerVideo(photo,ready);
  else if(photo.type==='live')loadViewerImage(photo.poster||photo.thumb,{onReady(){
    clearLivePlayback();ready();
    if(siteBehavior.liveAutoplay!==false&&!reduceMotion&&!document.hidden)startLivePhoto(photo);
  }});
  else loadViewerImage(photo.type==='live'?photo.poster||photo.thumb:photo.preview||photo.src,{onReady(){clearLivePlayback();ready();}});
}
function openAlbum(album,startIndex=savedPhotoIndex(album.progressKey||album.date,album.photos)){
  if(!album.photos.length)return;
  pointers.clear();gesture=null;
  mediaSession++;albumRender++;clearLivePlayback();stopVideo();resetZoom();
  currentAlbum=album;photoIndex=Math.max(0,Math.min(album.photos.length-1,startIndex));displayedIndex=-1;
  $('#viewerImage').hidden=true;viewerVideo.hidden=true;
  $('#stackBack').hidden=true;$('#stackMiddle').hidden=true;
  $('#photoCounter').textContent='';$('#photoCaption').textContent='';$('#mediaType').textContent='';$('#viewerTitle').textContent=album.title;
  if(!dialog.open){previousFocus=document.activeElement;dialog.showModal();document.body.classList.add('modal-open');}
  renderThumbnails();renderPhoto();
}
function movePhoto(delta){if(!currentAlbum)return;const next=photoIndex+delta;if(next<0||next>=currentAlbum.photos.length)return;photoIndex=next;renderPhoto();}
function applyZoom(){
  const image=!viewerVideo.hidden&&viewerVideo.dataset.live==='true'?viewerVideo:$('#viewerImage');
  const limitX=Math.max(0,(image.clientWidth*zoom-stage.clientWidth)/2),limitY=Math.max(0,(image.clientHeight*zoom-stage.clientHeight)/2);
  panX=Math.max(-limitX,Math.min(limitX,panX));
  panY=Math.max(-limitY,Math.min(limitY,panY));
  image.style.transform=`translate(${panX}px,${panY}px) scale(${zoom})`;
  stage.classList.toggle('is-zoomed',zoom>1.01);
  $('#zoomLevel').textContent=Math.round(zoom*100)+'%';
  updateTools();
  $('#viewerHelp').textContent=zoom>1.01?'拖动查看细节 · 双击复位 · 使用左右按钮翻页':'单指左右滑动翻页 · 双击或双指缩放';
}
function resetZoom(){zoom=1;panX=0;panY=0;lastTap=null;applyZoom();}
function setZoom(value,x,y){
  if(!visiblePhoto()||visiblePhoto().type==='video')return;
  const next=Math.max(1,Math.min(5,value)),ratio=next/zoom;
  const rect=$('#activePhoto').getBoundingClientRect();
  const dx=(x??rect.left+rect.width/2)-rect.left-rect.width/2,dy=(y??rect.top+rect.height/2)-rect.top-rect.height/2;
  panX=dx-(dx-panX)*ratio;panY=dy-(dy-panY)*ratio;zoom=next;applyZoom();
}
function doubleZoom(x,y){setZoom(zoom>1.01?1:2.5,x,y);}
function cancelAutomaticHD(){
  clearTimeout(hdTimer);clearTimeout(hdTimeout);hdTimer=null;hdTimeout=null;hdState=null;
}
function applyAutomaticHD(){
  const state=hdState;
  if(!state||state.render!==albumRender||displayedIndex!==state.index||photoIndex!==displayedIndex||!dialog.open||stage.getAttribute('aria-busy')==='true')return;
  if(state.ready){
    if(!liveMotionEnabled){
      if($('#viewerImage')!==state.image){state.image.alt=state.photo.caption||'';swapImage(state.image);}
      hdLoaded=true;
    }
    if(state.photo.type==='live')return;
    showStatus('');$('#retryMedia').hidden=true;
  }else if(state.failed){
    if(state.photo.type==='live')return;
    showStatus('高清暂时无法加载，仍可查看预览图');$('#retryMedia').hidden=false;
    retryAction=()=>{beginAutomaticHD(state.photo,state.index,state.render);$('#retryMedia').hidden=true;showStatus('');};
  }else if(state.slow&&state.photo.type!=='live')showStatus('正在加载高清…');
}
function beginAutomaticHD(photo,index,render){
  cancelAutomaticHD();hdLoaded=false;
  const src=originalSource(photo);if(!src||photo.type==='video')return;
  const image=new Image();image.decoding='async';image.draggable=false;
  if(photo.type==='live')image.fetchPriority='low';
  const state={photo,index,render,image,ready:false,failed:false,slow:false};hdState=state;
  const valid=()=>hdState===state&&render===albumRender&&dialog.open&&!state.failed;
  const fail=()=>{if(!valid())return;state.failed=true;clearTimeout(hdTimer);clearTimeout(hdTimeout);applyAutomaticHD();};
  hdTimer=setTimeout(()=>{if(valid()){state.slow=true;applyAutomaticHD();}},350);
  hdTimeout=setTimeout(fail,20000);
  image.addEventListener('load',async()=>{
    if(!valid())return;try{await image.decode();}catch{fail();return;}
    if(!valid())return;state.ready=true;clearTimeout(hdTimer);clearTimeout(hdTimeout);applyAutomaticHD();
  });
  image.addEventListener('error',fail);image.src=src;
}
$('#retryMedia').addEventListener('click',()=>retryAction?.());
$('#zoomIn').addEventListener('click',()=>setZoom(zoom+0.5));$('#zoomOut').addEventListener('click',()=>setZoom(zoom-0.5));$('#resetZoom').addEventListener('click',resetZoom);
$('#toggleLive').addEventListener('click',()=>{const photo=visiblePhoto();if(photo?.type!=='live'||photoIndex!==displayedIndex)return;if(liveMotionEnabled)pauseLivePhoto();else startLivePhoto(photo);});
$('#previousPhoto').addEventListener('click',()=>movePhoto(-1));$('#nextPhoto').addEventListener('click',()=>movePhoto(1));
$('#closeViewer').addEventListener('click',()=>dialog.close());
dialog.addEventListener('close',()=>{
  // A queued close event from the previous album must not cancel a new opening.
  if(dialog.open)return;
  mediaSession++;albumRender++;cancelAutomaticHD();mediaReady();clearLivePlayback();stopVideo();if(pendingVideo){stopVideo(pendingVideo);pendingVideo=null;}
  liveMotionEnabled=false;pointers.clear();gesture=null;resetZoom();
  document.body.classList.remove('modal-open');previousFocus?.focus({preventScroll:true});
});
dialog.addEventListener('click',e=>{if(e.target===dialog){const r=dialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)dialog.close();}});
dialog.addEventListener('keydown',e=>{
  if(e.target===viewerVideo&&visiblePhoto()?.type==='video')return;
  if(e.key==='ArrowLeft'||e.key==='ArrowRight'){e.preventDefault();if(zoom>1.01){panX+=e.key==='ArrowLeft'?40:-40;applyZoom();}else movePhoto(e.key==='ArrowLeft'?-1:1);}
  if(e.key==='+'||e.key==='='){e.preventDefault();setZoom(zoom+0.5);}
  if(e.key==='-'){e.preventDefault();setZoom(zoom-0.5);}
  if(e.key==='0'){e.preventDefault();resetZoom();}
});
const point=e=>({x:e.clientX,y:e.clientY});
function pinchGeometry(){const [a,b]=[...pointers.values()];return {distance:Math.hypot(b.x-a.x,b.y-a.y),x:(a.x+b.x)/2,y:(a.y+b.y)/2};}
stage.addEventListener('pointerdown',e=>{
  if(e.target.closest('button')||!visiblePhoto()||visiblePhoto().type==='video'||e.button>0)return;
  if(e.pointerType==='touch')lastTouchTime=Date.now();
  e.preventDefault();stage.setPointerCapture(e.pointerId);pointers.set(e.pointerId,point(e));
  if(pointers.size===1)gesture={start:point(e),last:point(e),moved:false,blocked:zoom>1.01,pinch:false};
  else if(pointers.size===2){gesture.blocked=true;gesture.pinch=true;gesture.geometry=pinchGeometry();lastTap=null;}
});
stage.addEventListener('pointermove',e=>{
  if(!pointers.has(e.pointerId)||!gesture)return;
  e.preventDefault();pointers.set(e.pointerId,point(e));
  if(pointers.size>=2){
    const next=pinchGeometry(),old=gesture.geometry;
    if(old&&old.distance>0){setZoom(zoom*next.distance/old.distance,old.x,old.y);panX+=next.x-old.x;panY+=next.y-old.y;applyZoom();}
    gesture.geometry=next;gesture.moved=true;return;
  }
  const dx=e.clientX-gesture.last.x,dy=e.clientY-gesture.last.y;
  if(Math.hypot(e.clientX-gesture.start.x,e.clientY-gesture.start.y)>8)gesture.moved=true;
  if(zoom>1.01){panX+=dx;panY+=dy;applyZoom();gesture.blocked=true;}
  gesture.last=point(e);
});
function endPointer(e,cancelled=false){
  if(!pointers.has(e.pointerId)||!gesture)return;
  pointers.delete(e.pointerId);
  if(cancelled){gesture.blocked=true;gesture.moved=true;lastTap=null;}
  if(pointers.size){gesture.last=[...pointers.values()][0];gesture.geometry=null;return;}
  const dx=e.clientX-gesture.start.x,dy=e.clientY-gesture.start.y;
  if(!cancelled&&!gesture.blocked&&!gesture.pinch&&Math.abs(dx)>50&&Math.abs(dx)>Math.abs(dy)*1.25){movePhoto(dx<0?1:-1);lastTap=null;}
  else if(!cancelled&&!gesture.moved&&!gesture.pinch&&Math.hypot(dx,dy)<8&&e.pointerType==='touch'){
    const now=Date.now();
    if(lastTap&&now-lastTap.time<300&&Math.hypot(e.clientX-lastTap.x,e.clientY-lastTap.y)<30){doubleZoom(e.clientX,e.clientY);lastTap=null;}
    else lastTap={time:now,x:e.clientX,y:e.clientY};
  }else lastTap=null;
  gesture=null;
}
stage.addEventListener('pointerup',e=>endPointer(e));stage.addEventListener('pointercancel',e=>endPointer(e,true));
stage.addEventListener('lostpointercapture',e=>{if(pointers.has(e.pointerId))endPointer(e,true);});
stage.addEventListener('dblclick',e=>{if((e.target===viewerVideo&&visiblePhoto()?.type==='video')||e.target.closest('button'))return;e.preventDefault();if(Date.now()-lastTouchTime<500)return;doubleZoom(e.clientX,e.clientY);});
stage.addEventListener('wheel',e=>{if(e.ctrlKey&&visiblePhoto()?.type!=='video'){e.preventDefault();setZoom(zoom*Math.exp(-e.deltaY/250),e.clientX,e.clientY);}},{passive:false});
document.addEventListener('visibilitychange',()=>{if(document.hidden){pointers.clear();gesture=null;viewerVideo.pause();if(liveMotionEnabled&&photoIndex===displayedIndex)pauseLivePhoto();}});

const collages=sectionEnabled('collage')&&Array.isArray(supplied.collage)?supplied.collage:[];
let collageIndex=savedPhotoIndex('collage',collages),displayedCollageIndex=-1,collageRender=0,collageTimer=null,collageTimeout=null,collageTouch=null,suppressCollageClick=false;
let collageResizeFrame=null,collageSize=null;
function fitCollage(piece,animate=false){
  const cover=$('#viewCollage'),width=cover.clientWidth;if(!width||!piece)return;
  const ratio=piece.width/piece.height||1,padding=parseFloat(getComputedStyle(cover).paddingLeft)||0;
  const landscape=ratio>1;
  const cap=$('#collageHeightLimit').getBoundingClientRect().height*(landscape&&matchMedia('(max-width:600px)').matches?2/3:1);
  const target=Math.min((width-2*padding)/ratio+2*padding,cap);
  const from=cover.getBoundingClientRect().height;
  if(collageSize===target&&!animate)return;
  collageSize=target;cancelAnimationFrame(collageResizeFrame);
  cover.dataset.orientation=landscape?'landscape':'portrait';
  const controls=$('.collage-controls'),rect=controls.getBoundingClientRect();
  const keepControls=animate&&!dialog.open&&cover.getBoundingClientRect().top<76&&rect.top>76&&rect.bottom<innerHeight;
  const apply=height=>{const before=controls.getBoundingClientRect().top;cover.style.height=height+'px';if(keepControls)window.scrollBy({top:controls.getBoundingClientRect().top-before,behavior:'instant'});};
  if(!animate||reduceMotion||Math.abs(from-target)<2){apply(target);return;}
  const start=performance.now();
  function step(now){const t=Math.min(1,(now-start)/220);apply(from+(target-from)*(1-Math.pow(1-t,3)));if(t<1)collageResizeFrame=requestAnimationFrame(step);}
  collageResizeFrame=requestAnimationFrame(step);
}
function markCollage(index){
  [...$('#collageGrid').children].forEach((button,i)=>button.setAttribute('aria-current',String(i===index)));
}
$('#toggleCollageOverview').textContent=uiText('overviewOpen',{count:collages.length});
$('#collageGrid').replaceChildren(...collages.map((piece,index)=>{
  const button=document.createElement('button');button.type='button';button.className='collage-thumbnail';
  button.setAttribute('aria-label',`查看拼贴 ${String(index+1).padStart(2,'0')}：${piece.caption||''}`);button.setAttribute('aria-current','false');
  const image=new Image();image.src=piece.thumb||piece.preview;image.alt='';image.loading='lazy';image.decoding='async';image.width=piece.width;image.height=piece.height;
  const label=document.createElement('span');label.textContent=String(index+1).padStart(2,'0');button.append(image,label);
  button.addEventListener('click',()=>openAlbum({title:uiText('collageTitle').replace(/\n/g,''),photos:collages,progressKey:'collage'},index));return button;
}));
$('#toggleCollageOverview').addEventListener('click',()=>{
  const expanded=$('#collageOverview').hidden;$('#collageOverview').hidden=!expanded;
  $('#toggleCollageOverview').setAttribute('aria-expanded',String(expanded));
  $('#toggleCollageOverview').textContent=expanded?uiText('overviewClose'):uiText('overviewOpen',{count:collages.length});
});
const collageObserver=new ResizeObserver(()=>fitCollage(collages[displayedCollageIndex>=0?displayedCollageIndex:collageIndex]));
collageObserver.observe($('#collageBoard'));
window.addEventListener('resize',()=>{collageSize=null;fitCollage(collages[displayedCollageIndex>=0?displayedCollageIndex:collageIndex]);});
if(siteBehavior.persistProgress===false)$('#progressNote').textContent=uiText('progressSession');
else if(!saveProgress())$('#progressNote').textContent=uiText('progressUnavailable');
function renderCollage(){
  const index=collageIndex,piece=collages[index];if(!piece)return;
  const render=++collageRender,image=new Image();image.decoding='async';image.draggable=false;
  image.fetchPriority='high';window.LiveMediaCache?.setForegroundBusy('collage',true);
  clearTimeout(collageTimer);clearTimeout(collageTimeout);$('#collageStatus').hidden=true;$('#retryCollage').hidden=true;$('#collageBoard').setAttribute('aria-busy','true');
  $('#previousCollage').disabled=index===0;$('#nextCollage').disabled=index===collages.length-1;
  collageTimer=setTimeout(()=>{if(render===collageRender){$('#collageStatus').textContent='正在加载…';$('#collageStatus').hidden=false;}},350);
  function fail(){if(render!==collageRender)return;window.LiveMediaCache?.setForegroundBusy('collage',false);collageRender++;clearTimeout(collageTimer);clearTimeout(collageTimeout);$('#collageBoard').setAttribute('aria-busy','false');$('#collageStatus').textContent='加载失败，请重试';$('#collageStatus').hidden=false;$('#retryCollage').hidden=false;collageIndex=Math.max(0,displayedCollageIndex);$('#previousCollage').disabled=collageIndex===0;$('#nextCollage').disabled=collageIndex===collages.length-1;}
  collageTimeout=setTimeout(fail,20000);
  image.addEventListener('load',async()=>{
    try{await image.decode();}catch{fail();return;}if(render!==collageRender)return;
    window.LiveMediaCache?.setForegroundBusy('collage',false);
    clearTimeout(collageTimer);clearTimeout(collageTimeout);image.id='collageImage';image.alt=piece.caption||'拼贴照片';$('#collageImage').replaceWith(image);
    const previous=displayedCollageIndex;displayedCollageIndex=index;$('#collageCounter').textContent=`${index+1} / ${collages.length}`;
    $('#viewCollage').dataset.orientation=piece.width>piece.height?'landscape':'portrait';
    fitCollage(piece,previous>=0);markCollage(index);rememberPhoto('collage',piece);
    $('#viewCollage').setAttribute('aria-label',`放大查看第 ${index+1} 张拼贴照片`);$('#collageStatus').hidden=true;$('#collageBoard').setAttribute('aria-busy','false');
  });
  image.addEventListener('error',fail);image.src=piece.preview||piece.src;
  $('#retryCollage').onclick=()=>{collageIndex=index;renderCollage();};
}
function moveCollage(delta){const next=collageIndex+delta;if(next<0||next>=collages.length)return;collageIndex=next;renderCollage();}
$('#previousCollage').addEventListener('click',()=>moveCollage(-1));$('#nextCollage').addEventListener('click',()=>moveCollage(1));
$('#viewCollage').addEventListener('click',e=>{if(suppressCollageClick){e.preventDefault();return;}if(displayedCollageIndex>=0)openAlbum({title:uiText('collageTitle').replace(/\n/g,''),photos:collages,progressKey:'collage'},displayedCollageIndex);});
$('#collageBoard').addEventListener('keydown',e=>{if(e.key==='ArrowLeft'||e.key==='ArrowRight'){e.preventDefault();moveCollage(e.key==='ArrowLeft'?-1:1);}});
$('#viewCollage').addEventListener('touchstart',e=>{suppressCollageClick=false;collageTouch=e.touches.length===1?{x:e.touches[0].clientX,y:e.touches[0].clientY}:null;},{passive:true});
$('#viewCollage').addEventListener('touchend',e=>{if(!collageTouch)return;const dx=e.changedTouches[0].clientX-collageTouch.x,dy=e.changedTouches[0].clientY-collageTouch.y;if(Math.abs(dx)>50&&Math.abs(dx)>Math.abs(dy)*1.25){suppressCollageClick=true;moveCollage(dx<0?1:-1);setTimeout(()=>{suppressCollageClick=false;},400);}collageTouch=null;},{passive:true});
$('#viewCollage').addEventListener('touchcancel',()=>{collageTouch=null;suppressCollageClick=false;},{passive:true});
renderCollage();
if(!collages.length)document.querySelector('#collage').hidden=true;
