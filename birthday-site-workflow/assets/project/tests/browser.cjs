'use strict';
// Browser checks own their server and browser; no authenticated browser session is used.
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict');
const {spawn}=require('node:child_process');
const fs=require('node:fs');const path=require('node:path');
const root=path.resolve(__dirname,'..');
async function check(page,base,label){
  const errors=[],bad=[],requests=[];
  page.on('pageerror',e=>errors.push(e.message));
  page.on('response',r=>{if(r.status()>=400)bad.push(r.status()+' '+r.url());});
  page.on('request',r=>requests.push(r.url()));
  await page.goto(base);await page.locator('#openEnvelope').click();
  await page.locator('#enterMemories').waitFor({state:'visible',timeout:15000});
  assert(await page.locator('.letter h1 .print-line').evaluate(line=>line.getBoundingClientRect().width<=line.parentElement.clientWidth),'Letter title overflows');
  assert(!requests.some(url=>/original\.(png|jpg|webp)/.test(url)),'Originals loaded before opening a picture');
  await page.screenshot({path:path.join(root,'.local',label+'-letter.png')});
  await page.locator('#enterMemories').click();await page.locator('#startMemory').click();
  await page.waitForFunction(()=>document.querySelector('#photoCounter').textContent==='1 / 3');
  assert.equal(await page.locator('#unlockedCount').textContent(),'1');
  await page.locator('#nextPhoto').click();await page.waitForFunction(()=>document.querySelector('#photoCounter').textContent==='2 / 3');
  await page.locator('#zoomIn').click();assert.notEqual(await page.locator('#zoomLevel').textContent(),'100%');await page.locator('#resetZoom').click();
  await page.keyboard.press('ArrowRight');await page.waitForFunction(()=>document.querySelector('#photoCounter').textContent==='3 / 3');
  await page.locator('#toggleLive').waitFor({state:'visible'});
  if(await page.locator('#toggleLive').getAttribute('aria-pressed')==='true')await page.locator('#toggleLive').click();
  await page.locator('#toggleLive').click();
  await page.waitForFunction(()=>{const video=document.querySelector('#viewerVideo');return !video.hidden&&!video.paused&&video.currentTime>0;});
  await page.waitForFunction(()=>document.querySelector('#toggleLive').getAttribute('aria-pressed')==='false');
  assert.equal(await page.locator('#viewerImage').isVisible(),true);
  await page.locator('#closeViewer').click();
  await page.locator('#clearDate').click();
  for(const digit of ['0','8','2','2'])await page.getByRole('button',{name:'选择数字 '+digit,exact:true}).click();
  await page.locator('#unlockDate').click();await page.waitForFunction(()=>document.querySelector('#photoCounter').textContent==='1 / 2');
  assert.equal(await page.locator('#unlockedCount').textContent(),'2');
  await page.locator('#nextPhoto').click();await page.waitForFunction(()=>document.querySelector('#photoCounter').textContent==='2 / 2');
  await page.locator('#viewerVideo').waitFor({state:'visible'});await page.locator('#closeViewer').click();
  await page.locator('#nextCollage').click();await page.waitForFunction(()=>document.querySelector('#collageCounter').textContent==='2 / 2');
  await page.locator('#collageBoard').focus();await page.keyboard.press('ArrowLeft');await page.waitForFunction(()=>document.querySelector('#collageCounter').textContent==='1 / 2');
  if(label==='mobile'){
    await page.locator('#viewCollage').evaluate(target=>{
      const start=new Touch({identifier:1,target,clientX:260,clientY:300});
      const end=new Touch({identifier:1,target,clientX:80,clientY:302});
      target.dispatchEvent(new TouchEvent('touchstart',{touches:[start],bubbles:true}));
      target.dispatchEvent(new TouchEvent('touchend',{touches:[],changedTouches:[end],bubbles:true}));
    });
    await page.waitForFunction(()=>document.querySelector('#collageCounter').textContent==='2 / 2');
    await page.locator('#previousCollage').click();await page.waitForFunction(()=>document.querySelector('#collageCounter').textContent==='1 / 2');
    // The viewer deliberately suppresses the click synthesized immediately after a swipe.
    await page.waitForTimeout(450);
  }
  await page.locator('#toggleCollageOverview').click();assert.equal(await page.locator('#collageGrid button').count(),2);
  await page.locator('#viewCollage').click();await page.locator('#photoDialog').waitFor({state:'visible'});await page.locator('#closeViewer').click();
  await page.locator('#startQuiz').click();await page.locator('.quiz-option').first().click();await page.locator('#nextQuestion').click();
  assert.equal(await page.locator('.quiz-inspect').count(),4);
  await page.locator('.quiz-inspect').first().click();await page.locator('#photoDialog').waitFor({state:'visible'});await page.locator('#closeViewer').click();
  await page.locator('.quiz-option').first().click();await page.locator('#nextQuestion').click();
  await page.locator('.quiz-option').last().click();await page.locator('#nextQuestion').click();
  assert.equal(await page.locator('#questionText').textContent(),'答对了 2 / 2 题');
  await page.locator('#quiz').screenshot({path:path.join(root,'.local',label+'-quiz.png')});
  await page.reload();await page.locator('#openEnvelope').click();await page.locator('#enterMemories').click();
  if(label!=='blocked-storage'){
    assert.equal(await page.locator('#unlockedCount').textContent(),'2');
    await page.locator('#startQuiz').click();assert.equal(await page.locator('#questionText').textContent(),'答对了 2 / 2 题');
  }
  assert.deepEqual(errors,[]);assert.deepEqual(bad,[]);
  console.log('PASS '+label+' (opening, albums, Live, video, zoom, collage, image quiz, progress; no page errors or HTTP failures)');
}
(async()=>{
  fs.mkdirSync(path.join(root,'.local'),{recursive:true});
  const server=spawn(process.env.PYTHON||'python',['serve.py','--port','0'],{cwd:root,stdio:['ignore','pipe','pipe']});
  let browser;
  try{
    const base=await new Promise((resolve,reject)=>{
      const timer=setTimeout(()=>reject(new Error('Server startup timeout')),10000);let output='';
      server.on('error',reject);server.stdout.on('data',chunk=>{output+=chunk;const m=output.match(/Preview: (http:\/\/[^\s]+)/);if(m){clearTimeout(timer);resolve(m[1]);}});
    });
    browser=await chromium.launch({headless:true,...(process.env.CHROMIUM_PATH?{executablePath:process.env.CHROMIUM_PATH}:{})});
    for(const [label,options] of [['desktop',{viewport:{width:1365,height:900}}],['mobile',{viewport:{width:390,height:844},isMobile:true,hasTouch:true,reducedMotion:'reduce'}],['blocked-storage',{viewport:{width:1024,height:768},reducedMotion:'reduce'}]]){
      const context=await browser.newContext(options);
      if(label==='blocked-storage')await context.addInitScript(()=>Object.defineProperty(window,'localStorage',{get(){throw new Error('Storage blocked');}}));
      const page=await context.newPage();page.setDefaultTimeout(20000);await check(page,base,label);await context.close();
    }
  }finally{if(browser)await browser.close();server.kill();}
})().catch(error=>{console.error(error);process.exitCode=1;});
