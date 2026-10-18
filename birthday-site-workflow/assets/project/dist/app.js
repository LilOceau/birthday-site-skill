'use strict';
const $ = (s) => document.querySelector(s);
const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;

const supplied = window.BIRTHDAY_CONTENT || {};
// Only completed user actions are persisted; blocked storage falls back to this visit.
const progressKey='birthday-'+(supplied.siteId||'demo')+'-progress-v1';
let progress={};
try{const saved=JSON.parse(localStorage.getItem(progressKey));if(saved&&saved.version===1)progress=saved;}catch{}
function saveProgress(){try{localStorage.setItem(progressKey,JSON.stringify({...progress,version:1}));return true;}catch{return false;}}
function savedPhotoIndex(key,photos){const saved=progress.positions?.[key],src=typeof saved==='string'?saved.replace(/\.live\.webp$/,'.live.mp4'):saved;const index=photos.findIndex(p=>p.src===src);return Math.max(0,index);}
function rememberPhoto(key,photo){if(!key||!photo)return;if(!progress.positions||typeof progress.positions!=='object'||Array.isArray(progress.positions))progress.positions={};progress.positions[key]=photo.src;if(memories.some(m=>m.date===key))progress.lastAlbum=key;saveProgress();}
const memories=Array.isArray(supplied.memories)?supplied.memories:[];
const isDemo=false;
if(!isDemo) $('#dateNote').textContent=memories.length+'个日期，'+memories.reduce((n,m)=>n+m.photos.length,0)+'个瞬间，等你逐一开启。';
let digits=['','','',''];let currentSlot=0;
let failedDateAttempts=0,lastHintDate=null;
const hintYear=Number.isInteger(supplied.hintYear)?supplied.hintYear:2026;
$('#dateHint').hidden=true;
const unlocked=new Set();
const slotNames=['月份十位','月份个位','日期十位','日期个位'];
const slots=[...document.querySelectorAll('.date-slot')];
const photoMonths=[...new Set(memories.filter(m=>m.photos?.length&&validDate(m.date)).map(m=>Number(m.date.slice(0,2))))];
// Dates have no year; retain the existing leap-day support for February 29.
function monthLength(month){return month>=1&&month<=12?new Date(2024,month,0).getDate():0;}
function allowedDigits(slot=currentSlot,values=digits){
  if(slot===0)return [0,1];
  if(values.slice(0,slot).some(d=>d===''))return [];
  if(slot===1)return values[0]==='0'?photoMonths.filter(m=>m>=1&&m<=9).sort((a,b)=>a-b):values[0]==='1'?[0,1,2]:[];
  const days=monthLength(Number(values[0]+values[1]));
  if(!days)return [];
  if(slot===2)return [0,1,2,3].filter(n=>Math.max(1,n*10)<=days);
  if(slot===3)return Array.from({length:10},(_,n)=>n).filter(n=>{const day=Number(values[2])*10+n;return day>=1&&day<=days;});
  return [];
}
function updateDigits(){
  slots.forEach((slot,i)=>{slot.textContent=digits[i]||'_';slot.disabled=digits.slice(0,i).some(d=>d==='');slot.classList.toggle('active',i===currentSlot);slot.setAttribute('aria-label',slotNames[i]+'，'+(digits[i]||'未填写'));});
  $('#unlockDate').disabled=digits.some(d=>d==='');
  $('#digitHint').textContent=['先选月份首位',digits[0]==='0'?'只显示有照片的月份':'选择 10、11 或 12 月','选择日期首位','按月份天数筛选'][currentSlot];
  shuffleDigits();
}
function selectDigit(d){
  if(!/^\d$/.test(String(d))) return;
  if(!allowedDigits().includes(Number(d))){dateMessage('请从当前显示的数字中选择。',true);return;}
  if(digits[currentSlot]!==String(d))digits.fill('',currentSlot+1);
  digits[currentSlot]=String(d);
  if(currentSlot<3) currentSlot++;
  updateDigits();slots[currentSlot].focus({preventScroll:true});dateMessage('选好日期后，试着解锁这一天。');
}
function dateMessage(text,error=false){$('#dateMessage').textContent=text;$('#dateMessage').classList.toggle('error',error);}
function shuffleDigits(){
  const values=allowedDigits();
  for(let i=values.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[values[i],values[j]]=[values[j],values[i]];}
  $('#numberPool').style.setProperty('--digit-columns',Math.max(1,Math.min(5,values.length)));
  $('#numberPool').setAttribute('aria-label',slotNames[currentSlot]+'的可选数字');
  $('#shuffleDigits').disabled=values.length<2;
  $('#numberPool').replaceChildren(...values.map(n=>{
    const button=document.createElement('button');button.type='button';button.textContent=n;button.setAttribute('aria-label','选择数字 '+n);
    button.style.setProperty('--x',Math.round(Math.random()*10-5)+'px');button.style.setProperty('--y',Math.round(Math.random()*14-7)+'px');button.style.setProperty('--r',Math.round(Math.random()*20-10)+'deg');
    button.addEventListener('click',()=>selectDigit(n));return button;
  }));
}
function validDate(date){
  if(!/^\d{2}\/\d{2}$/.test(date)) return false;
  const [m,d]=date.split('/').map(Number);const check=new Date(2024,m-1,d);
  return check.getMonth()===m-1 && check.getDate()===d;
}
function recordDateFailure(){
  failedDateAttempts++;
  if(failedDateAttempts===2){
    const button=$('#dateHint');button.hidden=false;
    if(!reduceMotion)button.animate([{opacity:0,transform:'translateY(6px)'},{opacity:1,transform:'translateY(0)'}],{duration:300,easing:'ease-out'});
  }
}
function calendarHint(date){
  const [month,day]=date.split('/').map(Number);
  const monthNames=['一','二','三','四','五','六','七','八','九','十','十一','十二'];
  const ordinals=['一','二','三','四','五'];const weekdays=['日','一','二','三','四','五','六'];
  const calendarDate=new Date(Date.UTC(hintYear,month-1,day));
  if(calendarDate.getUTCMonth()!==month-1)return '二月里，只在闰年出现的那一天。';
  return monthNames[month-1]+'月的第'+ordinals[Math.floor((day-1)/7)]+'个周'+weekdays[calendarDate.getUTCDay()]+'。';
}
function unlockDate(){
  const date=digits.slice(0,2).join('')+'/'+digits.slice(2).join('');
  const complete=digits.length===4&&digits.every(d=>/^\d$/.test(d));
  if(!complete||!validDate(date)){if(complete)recordDateFailure();dateMessage('这个日期好像不成立，检查一下月份和天数吧。',true);return {ok:false,reason:'invalid_date'};}
  const matching=memories.filter(m=>m.date===date);
  const photos=matching.flatMap(m=>Array.isArray(m.photos)?m.photos:[]);
  if(!matching.length){recordDateFailure();dateMessage('这一天还没有照片，再想一个日子吧。',true);return {ok:false,reason:'no_memory'};}
  if(!photos.length){recordDateFailure();dateMessage('日期猜对了，这一天的照片还在准备中。');return {ok:false,reason:'photos_pending'};}
  const album={date,title:matching[0].title||date,photos};
  addUnlockedAlbum(album);
  progress.unlocked=[...unlocked];saveProgress();
  dateMessage('日期猜对了！这一天的照片，已经为你打开。');openAlbum(album);
  return {ok:true,date,photoCount:photos.length};
}
function addUnlockedAlbum(album){
  const {date,photos}=album;
  if(!unlocked.has(date)){
    unlocked.add(date);$('#unlockedCount').textContent=unlocked.size;
    const button=document.createElement('button');button.className='album-button';
    const img=new Image();img.src=photos[0].thumb||photos[0].poster||photos[0].src;img.alt='';img.loading='lazy';
    const label=document.createElement('span');label.textContent=date;
    const subtitle=document.createElement('small');const videos=photos.filter(p=>p.type==='live'||p.type==='video').length;subtitle.textContent=isDemo?'示例相册 · '+photos.length+' 张':(photos.length-videos)+' 张照片'+(videos?' · '+videos+' 段动态':'');
    button.append(img,label,subtitle);button.setAttribute('aria-label','重新翻看 '+date+' 的照片');button.addEventListener('click',()=>openAlbum(album));$('#unlockedAlbums').append(button);
  }
}
for(const date of Array.isArray(progress.unlocked)?progress.unlocked:[]){
  const matching=memories.filter(m=>m.date===date),photos=matching.flatMap(m=>m.photos||[]);
  if(matching.length&&photos.length)addUnlockedAlbum({date,title:matching[0].title||date,photos});
}
// One fixed welcome album, never a new random unlock on another click or visit.
const welcomeMemories=memories.filter(m=>m.date===supplied.welcomeDate);
const welcomePhotos=welcomeMemories.flatMap(m=>Array.isArray(m.photos)?m.photos:[]);
$('#memoryWelcome').hidden=!welcomePhotos.length;
$('#startMemory').addEventListener('click',()=>{
  if(!welcomePhotos.length)return;
  const album={date:supplied.welcomeDate,title:welcomeMemories[0].title||supplied.welcomeDate,photos:welcomePhotos};
  addUnlockedAlbum(album);progress.unlocked=[...unlocked];saveProgress();
  dateMessage('先从这段回忆开始。其他日子，等你逐个解锁。');
  openAlbum(album);
});
slots.forEach((slot,i)=>slot.addEventListener('click',()=>{if(digits.slice(0,i).some(d=>d===''))return;currentSlot=i;updateDigits();}));
$('#shuffleDigits').addEventListener('click',shuffleDigits);
function eraseDigit(){if(!digits[currentSlot]&&currentSlot>0)currentSlot--;digits.fill('',currentSlot);updateDigits();slots[currentSlot].focus({preventScroll:true});}
$('#eraseDigit').addEventListener('click',eraseDigit);
$('#clearDate').addEventListener('click',()=>{digits=['','','',''];currentSlot=0;updateDigits();dateMessage('重新选一个，值得被记住的日子。');});
$('#unlockDate').addEventListener('click',unlockDate);
$('.date-game').addEventListener('keydown',e=>{
  if(e.ctrlKey||e.metaKey||e.altKey)return;
  if(/^\d$/.test(e.key)){e.preventDefault();selectDigit(e.key);}
  else if(e.key==='Backspace'){e.preventDefault();eraseDigit();}
  else if(e.key==='Enter'&&e.target.classList.contains('date-slot')){e.preventDefault();unlockDate();}
});
$('#dateHint').addEventListener('click',()=>{
  if(failedDateAttempts<2)return;
  const remaining=memories.filter(m=>m.photos?.length&&!unlocked.has(m.date));
  const selectedMonth=digits.slice(0,2).join('');
  const inMonth=remaining.filter(m=>selectedMonth.length===2&&m.date.slice(0,2)===selectedMonth);
  const candidates=inMonth.length?inMonth:remaining;
  if(!candidates.length){dateMessage('所有日期都已解锁，点开下面的相册，再看一遍吧。');return;}
  const next=candidates[(candidates.findIndex(m=>m.date===lastHintDate)+1)%candidates.length];lastHintDate=next.date;
  dateMessage('按 '+hintYear+' 年的日历想一想：'+calendarHint(next.date));
});
updateDigits();

const quiz=Array.isArray(supplied.quiz)?supplied.quiz:[];
let questionIndex=0;let score=0;let answered=false;let quizStarted=false;
// Image additions keep the same answer history as the original text options.
const quizSignature=JSON.stringify(quiz.map(({explanation,explanationImages,...question})=>({...question,options:question.options.map(option=>option&&typeof option==='object'&&option.label?option.label:option)})));
const savedQuiz=progress.quiz?.signature===quizSignature?progress.quiz:null;
let quizAnswers=savedQuiz&&Array.isArray(savedQuiz.answers)?savedQuiz.answers.slice(0,quiz.length).map((answer,i)=>Number.isInteger(answer)&&answer>=0&&answer<quiz[i].options.length?answer:null):[];
let quizComplete=false;
function saveQuizProgress(){progress.quiz={signature:quizSignature,answers:quizAnswers,index:questionIndex,complete:quizComplete};saveProgress();}
const hasQuizAnswer=q=>Number.isInteger(q.answer)&&q.answer>=0&&q.answer<q.options.length;
const scoredQuizCount=()=>quiz.filter(q=>!q.pendingImages&&hasQuizAnswer(q)).length;
function clearQuizExplanation(){
  $('#quizExplanation').hidden=true;$('#quizExplanationText').textContent='';$('#quizExplanationImages').replaceChildren();
}
function renderQuizExplanation(q){
  clearQuizExplanation();
  const photos=Array.isArray(q.explanationImages)?q.explanationImages.filter(photo=>photo&&photo.src):[];
  if(!q.explanation&&!photos.length)return;
  $('#quizExplanationText').textContent=q.explanation||'';
  const title='第 '+(questionIndex+1)+' 题 · 解析配图';
  $('#quizExplanationImages').replaceChildren(...photos.map((photo,i)=>{
    const button=document.createElement('button');button.type='button';button.className='quiz-explanation-image';button.setAttribute('aria-label','放大查看 '+(photo.alt||'解析配图'));
    const picture=document.createElement('img');picture.src=photo.src;picture.alt=photo.alt||'解析配图';picture.decoding='async';if(photo.width)picture.width=photo.width;if(photo.height)picture.height=photo.height;
    const label=document.createElement('span');label.textContent='点击图片放大查看';button.append(picture,label);
    button.addEventListener('click',()=>openAlbum({title,photos:photos.map(p=>({...p,caption:p.alt||'解析配图',thumb:p.src}))},i));return button;
  }));
  $('#quizExplanation').hidden=false;
}
function renderQuestion(){
  answered=false;const q=quiz[questionIndex];
  clearQuizExplanation();
  $('#quizOptions').classList.toggle('quiz-options-images',q.options.some(option=>option&&typeof option==='object'&&option.src));
  $('#questionCount').textContent=String(questionIndex+1).padStart(2,'0')+' / '+String(quiz.length).padStart(2,'0');
  $('#questionText').textContent=q.question;$('#quizFeedback').textContent='';$('#nextQuestion').hidden=true;$('#retryQuiz').hidden=true;
  $('#quizOptions').replaceChildren(...q.options.map((option,i)=>{
    const button=document.createElement('button');button.className='quiz-option';button.disabled=!!q.pendingImages;
    const letter=document.createElement('b');letter.textContent=String.fromCharCode(65+i);button.append(letter);
    if(option&&typeof option==='object'&&option.src){
      button.classList.add('quiz-option-image');const picture=document.createElement('img');picture.src=option.preview||option.src;picture.alt=option.alt||option.label||'图片选项 '+letter.textContent;picture.decoding='async';button.append(picture);
      if(option.label){const text=document.createElement('span');text.textContent=option.label;button.append(text);button.setAttribute('aria-label',letter.textContent+' '+option.label);}
    }else{const text=document.createElement('span');text.textContent=option;button.append(text);}
    button.addEventListener('click',()=>answerQuestion(i));
    if(option&&typeof option==='object'&&option.src){
      const card=document.createElement('div');card.classList.add('quiz-image-card');
      const inspect=document.createElement('button');inspect.type='button';inspect.className='quiz-inspect';inspect.textContent='放大查看 '+letter.textContent;
      inspect.addEventListener('click',()=>openAlbum({title:'第 '+(questionIndex+1)+' 题 · 图片选项',photos:q.options.filter(o=>o&&typeof o==='object'&&o.src).map((o,n)=>({...o,caption:'选项 '+String.fromCharCode(65+n)+(o.label?' · '+o.label:''),thumb:o.preview||o.src}))},i));
      card.append(button,inspect);return card;
    }
    return button;
  }));
  if(q.pendingImages){answered=true;$('#quizFeedback').textContent='头像图片待补充，这题先跳过。';$('#nextQuestion').textContent=questionIndex===quiz.length-1?'看看结果 ↗':'跳过，下一题 ↗';$('#nextQuestion').hidden=false;}
  $('#questionText').focus();
}
function answerQuestion(index,restoring=false){
  const q=quiz[questionIndex];if(!quizStarted||answered||!Number.isInteger(index)||index<0||index>3)return {ok:false,reason:'invalid_or_answered'};
  answered=true;const canScore=hasQuizAnswer(q);const correct=canScore?index===q.answer:null;if(correct&&!restoring)score++;
  quizAnswers[questionIndex]=index;if(!restoring)saveQuizProgress();
  [...$('#quizOptions').children].forEach((entry,i)=>{const button=entry.classList.contains('quiz-image-card')?entry.children[0]:entry;button.disabled=true;button.classList.toggle('correct',canScore&&i===q.answer);button.classList.toggle('wrong',canScore&&i===index&&!correct);button.classList.toggle('selected',!canScore&&i===index);});
  $('#quizFeedback').textContent=canScore?(correct?'答对啦！':'这次的答案是 '+String.fromCharCode(65+q.answer)+'。'):'你选择了 '+String.fromCharCode(65+index)+'，答案待揭晓。';
  renderQuizExplanation(q);
  $('#nextQuestion').textContent=questionIndex===quiz.length-1?'看看结果 ↗':'下一题 ↗';$('#nextQuestion').hidden=false;
  return {ok:true,correct,score};
}
$('#nextQuestion').addEventListener('click',()=>{
  if(!answered)return;
  if(questionIndex<quiz.length-1){questionIndex++;renderQuestion();}
  else showQuizResult();
  saveQuizProgress();
});
function showQuizResult(){quizComplete=true;clearQuizExplanation();const total=scoredQuizCount();$('#questionText').textContent=total?'答对了 '+score+' / '+total+' 题':'本轮问答已完成';$('#quizOptions').replaceChildren();$('#quizFeedback').textContent=(total<quiz.length?'图片或答案待补充的题目暂不计分。':'')+('谢谢你，陪我把这些瞬间再记了一遍。生日快乐，'+(supplied.recipient||'你')+'！');$('#nextQuestion').hidden=true;$('#retryQuiz').hidden=false;}
$('#retryQuiz').addEventListener('click',()=>{questionIndex=0;score=0;quizAnswers=[];quizComplete=false;saveQuizProgress();renderQuestion();});
clearQuizExplanation();$('#quizSummary').textContent='共 '+quiz.length+' 道题，来试试我们的默契。';
$('#quizWelcome').hidden=false;$('#quizPlay').hidden=true;
if(savedQuiz){$('#startQuiz').textContent=savedQuiz.complete?'查看上次结果 ↗':'继续上次答题 ↗';$('#quizSummary').textContent='已保留这台设备上的答题进度。';}
$('#startQuiz').addEventListener('click',()=>{
  if(quizStarted)return;
  quizStarted=true;$('#quizWelcome').hidden=true;$('#quizPlay').hidden=false;
  // Stop at the first unanswered question; never trust an out-of-range saved cursor.
  const firstUnanswered=quiz.findIndex((q,i)=>!q.pendingImages&&!Number.isInteger(quizAnswers[i]));
  questionIndex=savedQuiz&&Number.isInteger(savedQuiz.index)?Math.max(0,Math.min(savedQuiz.index,firstUnanswered<0?quiz.length-1:firstUnanswered)):0;
  score=quizAnswers.reduce((total,answer,i)=>total+(hasQuizAnswer(quiz[i])&&answer===quiz[i].answer?1:0),0);
  renderQuestion();if(Number.isInteger(quizAnswers[questionIndex]))answerQuestion(quizAnswers[questionIndex],true);
  if(savedQuiz?.complete&&firstUnanswered<0)showQuizResult();saveQuizProgress();
});


if(!memories.length)document.querySelector('#dates').hidden=true;
if(!quiz.length)document.querySelector('#quiz').hidden=true;
