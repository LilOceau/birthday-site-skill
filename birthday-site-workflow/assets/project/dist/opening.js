'use strict';
/* 3000ms arrival + a user-controlled pause + 7000ms opening.
   All tracks share one document timeline. No frame loops, image swaps, paper
   stretching or chains of timers; cancelling/replaying invalidates stale work. */
class InvitationPlayer {
  constructor(root, {reducedMotion = matchMedia('(prefers-reduced-motion: reduce)')} = {}) {
    this.root=root;this.motionPreference=reducedMotion;this.serial=0;this.animations=[];
    this.phase='loading';this.shells=[...root.querySelectorAll('.shell-motion')];
    this.letter=root.querySelector('#letter');this.flap=root.querySelector('#flapHinge');
    this.alignment=root.querySelector('#envelopeScene');this.sleeve=root.querySelector('#letterSleeve');
    this.carrier=root.querySelector('#letterCarrier');
    this.flapMotion=root.querySelector('.envelope-flap-motion');this.palms=root.querySelector('#embroideredPalms');
    this.printLines=[...root.querySelectorAll('[data-print]')];
    this.openButton=root.querySelector('#openEnvelope');this.enterButton=root.querySelector('#enterMemories');
    this.replayButton=root.querySelector('#replay');this.hint=root.querySelector('#openingHint');
    this.openButton.addEventListener('click',()=>this.open());
    this.replayButton.addEventListener('click',()=>this.replay(true));
    this.enterButton.addEventListener('click',()=>{
      const chapters=document.querySelector('#chapters');chapters.hidden=false;
      chapters.scrollIntoView({behavior:this.motionPreference.matches?'instant':'smooth'});
    });
    this.motionPreference.addEventListener?.('change',()=>{
      if(!this.motionPreference.matches)return;
      const previous=this.phase;this.invalidate();
      if(previous==='opening'||previous==='opened')this.finishOpen();
      else this.finishArrival();
    });
    document.addEventListener('visibilitychange',()=>{
      this.animations.forEach(a=>{if(document.hidden)a.pause();else if(a.playState==='paused')a.play();});
    });
    this.assetsReady=this.loadAssets();
    this.textObserver=new ResizeObserver(()=>this.fitText());this.textObserver.observe(this.letter);
    this.replay(false);
  }
  fitText(){
    for(const line of this.printLines){
      line.style.fontSize='';
      const available=line.parentElement.clientWidth-4;
      // Layout width is independent of the envelope's animated scale/rotation.
      const width=Math.max(line.offsetWidth,line.scrollWidth);
      if(available>0&&width>available)line.style.fontSize=(parseFloat(getComputedStyle(line).fontSize)*available/width*.96)+'px';
    }
  }
  setPhase(phase){
    this.phase=phase;this.root.dataset.phase=phase;
    // Keep queued album downloads from competing with opening paint/decode.
    // Release through the existing cache API so replay can pause them again.
    window.LiveMediaCache?.setForegroundBusy('opening',phase!=='opened');
  }
  invalidate(){this.serial++;this.animations.forEach(a=>a.cancel());this.animations=[];}
  async loadAssets(){
    const texture=new Image();texture.src=siteConfig.assets.texture;
    // Decode the same responsive image selected by the browser and preload.
    const ocean=this.root.querySelector('#seaImage');
    const jobs=[texture.decode?.(),ocean.decode?.(),this.palms.decode?.(),document.fonts?.ready];
    let deadline;
    await Promise.race([Promise.allSettled(jobs),new Promise(resolve=>{deadline=setTimeout(resolve,6500);})]);
    clearTimeout(deadline);
    this.fitText();
  }
  track(element,frames,duration=7000,options={}){
    return {element,frames:frames.map(({at,...frame})=>({...frame,offset:at/duration})),options:{duration,fill:'both',easing:'linear',...options}};
  }
  async play(tracks,token){
    const commonStart=document.timeline.currentTime;
    this.animations=tracks.map(({element,frames,options})=>{
      const animation=element.animate(frames,options);
      if(commonStart!==null)animation.startTime=commonStart;
      if(document.hidden)animation.pause();
      return animation;
    });
    await Promise.all(this.animations.map(a=>a.finished)).catch(()=>{});
    return token===this.serial;
  }
  async replay(focusOnReady=false){
    this.invalidate();const token=this.serial;
    this.setPhase('loading');this.openButton.disabled=true;
    this.letter.setAttribute('aria-hidden','true');this.enterButton.hidden=true;this.replayButton.hidden=true;
    this.hint.hidden=false;this.hint.textContent=uiText('openingLoading');
    await this.assetsReady;
    if(token!==this.serial)return;
    if(this.motionPreference.matches||!this.letter.animate){this.finishArrival(focusOnReady);return;}
    this.setPhase('arriving');
    const entry=[
      {at:0,transform:'translateY(110vh)',opacity:1},
      {at:500,transform:'translateY(110vh)',opacity:1,easing:'cubic-bezier(.18,.63,.23,1)'},
      {at:2850,transform:'translateY(-.6%)',opacity:1,easing:'ease-out'},
      {at:3000,transform:'translateY(0)',opacity:1}
    ];
    const finished=await this.play(this.shells.map(el=>this.track(el,entry,3000)),token);
    if(finished)this.finishArrival(focusOnReady);
  }
  finishArrival(focus=false){
    this.setPhase('ready');this.animations.forEach(a=>a.cancel());this.animations=[];
    this.openButton.disabled=false;this.hint.hidden=false;this.hint.textContent=uiText('openingReady');
    if(focus)this.openButton.focus({preventScroll:true});
  }
  openingTracks(){
    // Move a fixed aperture with the pocket; counter-translate its child so
    // the paper stays in stage coordinates. Only transforms move the mask,
    // rather than repainting two changing clip paths over the suede texture.
    const drop=[
      {at:0,y:0,opacity:1},
      {at:1550,y:0,opacity:1,easing:'cubic-bezier(.45,0,.7,.45)'},
      {at:3050,y:110,opacity:1},
      {at:3150,y:120,opacity:0},
      {at:7000,y:120,opacity:0}
    ];
    const shell=drop.map(({y,...frame})=>({...frame,transform:`translateY(${y}vh)`}));
    const tracks=this.shells.map(el=>this.track(el,shell));
    tracks.push(this.track(this.alignment,[
      {at:0,transform:'rotate(-4deg)',easing:'cubic-bezier(.35,0,.2,1)'},
      {at:1200,transform:'rotate(0deg)'},{at:7000,transform:'rotate(0deg)'}
    ]));
    tracks.push(this.track(this.sleeve,drop.map(({y,opacity,...frame})=>({...frame,transform:`translateY(${y}vh)`}))));
    tracks.push(this.track(this.carrier,drop.map(({y,opacity,...frame})=>({...frame,transform:`translateY(${-y}vh)`}))));
    tracks.push(this.track(this.flap,[
      {at:0,transform:'rotateX(0deg)',easing:'cubic-bezier(.36,.02,.2,1)'},
      {at:1250,transform:'rotateX(165deg)',easing:'ease-out'},
      {at:1600,transform:'rotateX(178deg)'},{at:7000,transform:'rotateX(178deg)'}
    ]));
    // Move the upturned flap behind the emerging sheet only after it passes edge-on.
    tracks.push(this.track(this.flapMotion,[{at:0,zIndex:4},{at:850,zIndex:4},{at:851,zIndex:1},{at:7000,zIndex:1}]));
    tracks.push(this.track(this.letter,[
      // The closed flap hides the paper initially; its fixed pocket mask
      // supplies all lower-edge occlusion throughout this single smooth lift.
      {at:0,transform:'translateY(43%)',opacity:1},
      {at:700,transform:'translateY(43%)',opacity:1,easing:'cubic-bezier(.32,0,.18,1)'},
      {at:2850,transform:'translateY(0)',opacity:1},
      {at:7000,transform:'translateY(0)',opacity:1}
    ]));
    // Reveal complete, already-shaped lines continuously, then advance to the
    // next line. No character-sized jumps or simultaneous left/right printing.
    const printing={title:[3150,1250],subtitle:[4430,330],description:[4790,400],left1:[5220,140],left2:[5380,140],right1:[5540,160],right2:[5720,140],chinese1:[5890,260],chinese2:[6180,260],chinese3:[6470,270],year:[6770,90],invitation:[6880,100]};
    this.printLines.forEach(line=>{
      const [delay,duration]=printing[line.dataset.print];
      tracks.push({element:line,frames:[{clipPath:'inset(-.2em 100% -.3em 0)'},{clipPath:'inset(-.2em -.15em -.3em -.15em)'}],options:{delay,duration,fill:'both',easing:'linear'}});
    });
    tracks.push({element:this.palms,frames:[
      {offset:0,clipPath:'inset(100% 0 0 0)',opacity:0,transform:'scale(.94)'},
      {offset:.12,clipPath:'inset(90% 0 0 0)',opacity:1,transform:'scale(.95)'},
      {offset:.72,clipPath:'inset(20% 0 0 0)',opacity:1,transform:'scale(.99)'},
      {offset:1,clipPath:'inset(0% 0 0 0)',opacity:1,transform:'scale(1)'}
    ],options:{delay:5100,duration:1660,fill:'both',easing:'cubic-bezier(.25,.45,.3,1)'}});
    return tracks;
  }
  async open(){
    if(this.phase!=='ready')return;
    this.invalidate();const token=this.serial;this.setPhase('opening');this.openButton.disabled=true;
    this.letter.setAttribute('aria-hidden','false');this.hint.textContent='';
    if(this.motionPreference.matches||!this.letter.animate){this.finishOpen();return;}
    const finished=await this.play(this.openingTracks(),token);
    if(finished)this.finishOpen();
  }
  finishOpen(){
    this.setPhase('opened');this.animations.forEach(a=>a.cancel());this.animations=[];
    this.openButton.disabled=true;this.letter.setAttribute('aria-hidden','false');
    this.hint.hidden=true;this.enterButton.hidden=false;this.replayButton.hidden=false;
    // Announce once, after printing; never read out characters as they appear.
    this.hint.textContent=uiText('openingOpened');
  }
}
window.birthdayOpening=new InvitationPlayer(document.querySelector('#invitation'),siteBehavior.openingMotion==='reduced'?{reducedMotion:{matches:true}}:{});
// Use the existing opening, without adding a mandatory waiting screen.
window.birthdayOpening.assetsReady.then(()=>{
  if(!window.LiveMediaCache||siteBehavior.backgroundPreload===false)return;
  if(!dialog.open){
    const album=memories.find(m=>m.date===progress.lastAlbum&&unlocked.has(m.date))||memories.find(m=>m.date===supplied.welcomeDate);
    if(album){
      const index=savedPhotoIndex(album.date,album.photos);
      window.LiveMediaCache.warm(album.photos.slice(index).filter(p=>p.type==='live').slice(0,3),{live:siteBehavior.liveAutoplay!==false&&!reduceMotion});
    }
  }
  // Keep warming the remaining resources while the visitor reads or interacts.
  window.LiveMediaCache.start(memories.flatMap(m=>m.photos).concat(collages),{live:siteBehavior.liveAutoplay!==false&&!reduceMotion});
});
