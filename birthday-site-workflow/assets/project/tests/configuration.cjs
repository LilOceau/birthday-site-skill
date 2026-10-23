'use strict';
// Exercise generated custom sites in isolated copies, including network/storage effects.
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {spawn,spawnSync}=require('node:child_process');
const root=path.resolve(__dirname,'..'),local=path.join(root,'.local');
fs.mkdirSync(local,{recursive:true});
const temporary=fs.mkdtempSync(path.join(local,'configuration-test-'));
const copy=path.join(temporary,'site');
fs.mkdirSync(copy);
const included=source=>!path.relative(root,source).split(path.sep).some(part=>['.local','.work','.backups','.venv','node_modules','__pycache__'].includes(part));
for(const name of fs.readdirSync(root)){
  const source=path.join(root,name);
  if(included(source))fs.cpSync(source,path.join(copy,name),{recursive:true,filter:included});
}
const python=process.env.PYTHON||'python';
function build(site){
  fs.writeFileSync(path.join(copy,'site.json'),JSON.stringify(site,null,2)+'\n');
  const result=spawnSync(python,['build.py'],{cwd:copy,encoding:'utf8'});
  assert.equal(result.status,0,result.stdout+result.stderr);
}
async function startServer(){
  const server=spawn(python,['serve.py','--port','0'],{cwd:copy,stdio:['ignore','pipe','pipe']});
  try{
    const base=await new Promise((resolve,reject)=>{
      let output='';const timer=setTimeout(()=>reject(new Error('Server timeout')),10000);
      server.on('error',error=>{clearTimeout(timer);reject(error);});
      server.stdout.on('data',chunk=>{output+=chunk;const match=output.match(/Preview: (http:\/\/[^\s]+)/);if(match){clearTimeout(timer);resolve(match[1]);}});
    });
    return {server,base};
  }catch(error){server.kill();throw error;}
}
(async()=>{
  let server,browser;
  try{
    const custom=JSON.parse(fs.readFileSync(path.join(copy,'site.custom.example.json'),'utf8'));
    build(custom);
    const running=await startServer();server=running.server;const base=running.base;
    browser=await chromium.launch({headless:true,...(process.env.CHROMIUM_PATH?{executablePath:process.env.CHROMIUM_PATH}:{})});
    let context=await browser.newContext({viewport:{width:1365,height:900},reducedMotion:'no-preference'});
    await context.addInitScript(()=>{
      const original=window.localStorage;
      original.setItem('birthday-birthday-demo-progress-v1',JSON.stringify({version:1,unlocked:['08/22']}));
      window.storedBefore=original.getItem('birthday-birthday-demo-progress-v1');window.storageAccesses=0;
      window.readTestStorage=()=>original.getItem('birthday-birthday-demo-progress-v1');
      Object.defineProperty(window,'localStorage',{get(){window.storageAccesses++;return original;}});
    });
    const page=await context.newPage();page.setDefaultTimeout(20000);
    const errors=[],bad=[],requests=[];
    page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>requests.push(r.url()));
    page.on('response',r=>{if(r.status()>=400)bad.push(r.status()+' '+r.url());});
    await page.goto(base);await page.locator('#openEnvelope').click();await page.locator('#enterMemories').waitFor({state:'visible'});
    assert.equal(await page.locator('#invitation').getAttribute('data-phase'),'opened');
    assert.equal(await page.locator('meta[name="theme-color"]').getAttribute('content'),'#a76b52');
    assert.equal(await page.locator('#seaImage').getAttribute('src'),'assets/demo/choice-1.png');
    assert.equal(await page.locator('.letter').evaluate(el=>getComputedStyle(el).backgroundColor),'rgb(255, 248, 238)');
    assert.equal(await page.locator('.opening-header span').last().textContent(),'A LETTER FOR YOU');
    await page.screenshot({path:path.join(local,'configured-letter.png')});
    await page.locator('#enterMemories').click();
    assert.equal(await page.locator('#collage').isVisible(),false);
    assert.equal(await page.locator('.chapter-nav a[href="#collage"]').isVisible(),false);
    assert.equal(await page.locator('#dates h2').innerText(),'收藏日子，\n慢慢回看。');
    assert.equal(await page.locator('#quizWelcome h3').textContent(),'小夏的记忆小测验');
    assert.equal(await page.locator('#unlockedCount').textContent(),'0');
    await page.evaluate(()=>{recordDateFailure();});assert.equal(await page.locator('#dateHint').isVisible(),true);
    await page.locator('#startMemory').click();await page.locator('#nextPhoto').click();await page.keyboard.press('ArrowRight');
    await page.waitForFunction(()=>document.querySelector('#photoCounter').textContent==='3 / 3');
    assert.equal(await page.locator('#toggleLive').getAttribute('aria-pressed'),'false');
    await page.evaluate(()=>window.LiveMediaCache.warm(window.BIRTHDAY_CONTENT.memories[0].photos));
    await page.waitForTimeout(200);
    assert(!requests.some(url=>url.includes('.live.mp4')),'Disabled preload/autoplay fetched a Live video');
    await page.locator('#toggleLive').click();
    await page.waitForFunction(()=>{const v=document.querySelector('#viewerVideo');return !v.hidden&&!v.paused&&v.currentTime>0;});
    await page.locator('#closeViewer').click();await page.locator('#startQuiz').click();await page.locator('.quiz-option').first().click();
    assert.equal(await page.locator('#quizFeedback').textContent(),'记得真清楚！');
    assert.equal(await page.evaluate(()=>window.storageAccesses),0);
    assert.equal(await page.evaluate(()=>window.readTestStorage()===window.storedBefore),true);
    await page.reload();await page.locator('#openEnvelope').click();await page.locator('#enterMemories').click();
    assert.equal(await page.locator('#unlockedCount').textContent(),'0');
    await page.locator('#dates').screenshot({path:path.join(local,'configured-dates.png')});
    assert.deepEqual(errors,[]);assert.deepEqual(bad,[]);await context.close();
    for(const [name,sections] of [['collage-only',{dates:false,collage:true,quiz:false}],['no-sections',{dates:false,collage:false,quiz:false}]]){
      build({...custom,sections,behavior:{...custom.behavior,hintAfterAttempts:0}});
      context=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true});
      const next=await context.newPage();const failures=[];next.on('pageerror',e=>failures.push(e.message));
      await next.goto(base);await next.locator('#openEnvelope').click();await next.locator('#enterMemories').click();
      for(const [section,visible] of Object.entries(sections)){
        assert.equal(await next.locator('#'+section).isVisible(),visible);
        assert.equal(await next.locator('.chapter-nav a[href="#'+section+'"]').isVisible(),visible);
      }
      await next.evaluate(()=>recordDateFailure());assert.equal(await next.locator('#dateHint').getAttribute('hidden'),'');
      assert.equal(await next.locator('footer').isVisible(),true);
      assert.deepEqual(failures,[]);await next.screenshot({path:path.join(local,name+'.png')});await context.close();
    }
    console.log('PASS custom configuration (palette, assets, copy, sections/navigation, reduced motion, hint threshold, session-only progress, preload off, manual Live)');
  }finally{
    if(browser)await browser.close();
    if(server){const stopped=new Promise(resolve=>server.once('exit',resolve));server.kill();await stopped;}
    assert(temporary.startsWith(local+path.sep));fs.rmSync(temporary,{recursive:true,force:true});
  }
})().catch(error=>{console.error(error);process.exitCode=1;});
