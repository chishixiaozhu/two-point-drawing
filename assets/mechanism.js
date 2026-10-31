/* 二维双点描形：内置图形与自由轮廓的恒长滑杆模型。使用范围见LICENSE.txt。 */
window.Mechanism=(()=>{'use strict';
const cv=document.getElementById('film'),g=cv.getContext('2d'),TAU=Math.PI*2,custom=typeof CUSTOM_DATA!=='undefined',L=custom?CUSTOM_DATA.length:390,DRAW=8,CX=custom?CUSTOM_DATA.origin[0]:960,CY=custom?CUSTOM_DATA.origin[1]:470;
const mix=(a,b,u)=>a+(b-a)*u,clamp=x=>Math.max(0,Math.min(1,x));
const lerp=(a,b,u)=>({x:mix(a.x,b.x,u),y:mix(a.y,b.y,u)});
function axisState(rotation,weight){
 const horizontal=L*Math.cos(rotation),vertical=-L*Math.sin(rotation);
 const endpoints={a:{x:horizontal,y:0},b:{x:0,y:vertical}};
 return {...endpoints,p:{x:horizontal*(1-weight),y:vertical*weight},theta:rotation,u:weight};
}
function samplePose(phase,table){
 const position=clamp(phase/TAU)*(table.length-1),index=Math.min(table.length-2,Math.floor(position)),fraction=position-index;
 const first=table[index],second=table[index+1];
 return {theta:first[1]+(second[1]-first[1])*fraction,u:first[2]+(second[2]-first[2])*fraction};
}
function pose(ph){if(custom){const q=samplePose(ph,CUSTOM_DATA.rows);return axisState(q.theta,q.u);}if(CONFIG.shape==='circle')return axisState(Math.PI/2+ph,.5);const q=samplePose(ph,CONFIG.shape==='heart'?HEART_DATA.rows:STAR_DATA.rows);return axisState(q.theta,q.u);}
function stateAt(t){const phase=(custom?clamp(t/DRAW):((Math.max(0,t)/DRAW)%1))*TAU,s=pose(phase);return {...s,time:t,phase,traceProgress:clamp(t/DRAW),distance:Math.hypot(s.a.x-s.b.x,s.a.y-s.b.y),shape:CONFIG.shape};}
const colors={ice:'150,210,255',rose:'255,174,207',gold:'255,223,153',violet:'204,180,255'},auto={circle:'ice',heart:'rose',star:'gold'},rgb=colors[CONFIG.color==='auto'||!CONFIG.color?(auto[CONFIG.shape]||'violet'):CONFIG.color];
const sprites={a:glowSprite('255,120,96',.9),b:glowSprite('120,190,255',.9),p:glowSprite('255,228,160',1)};
let seed=71;const random=()=>{seed=(1664525*seed+1013904223)>>>0;return seed/4294967296};
const bg=document.createElement('canvas');bg.width=1920;bg.height=1080;const c=bg.getContext('2d');c.fillStyle='#08111f';c.fillRect(0,0,1920,1080);
const mist=c.createRadialGradient(960,460,20,960,460,950);mist.addColorStop(0,'rgba(49,76,105,.20)');mist.addColorStop(1,'rgba(4,9,19,0)');c.fillStyle=mist;c.fillRect(0,0,1920,1080);
for(let i=0;i<350;i++){const x=random()*1920,y=random()*1080,r=.4+random()*1.1;c.fillStyle=`rgba(190,213,239,${.08+random()*.29})`;c.beginPath();c.arc(x,y,r,0,TAU);c.fill();}
for(const chain of [[[50,220],[110,120],[210,104],[300,55],[320,160]],[[1590,110],[1670,185],[1780,148],[1860,215]],[[90,720],[160,790],[110,890],[240,930]],[[1650,750],[1790,820],[1740,940],[1860,990]]]){c.strokeStyle='rgba(151,184,218,.16)';c.lineWidth=1;c.beginPath();chain.forEach(([x,y],i)=>i?c.lineTo(x,y):c.moveTo(x,y));c.stroke();for(const [x,y]of chain){c.globalAlpha=.25;c.drawImage(sprites.b,x-13,y-13,26,26)}c.globalAlpha=1;}
const path=Array.from({length:1601},(_,i)=>pose(TAU*i/1600).p);
function axes(){g.save();g.lineWidth=2;g.strokeStyle='rgba(255,194,166,.57)';g.beginPath();g.moveTo(custom?-190:-443,0);g.lineTo(custom?1070:443,0);g.stroke();g.strokeStyle='rgba(178,220,255,.57)';g.beginPath();g.moveTo(0,custom?-660:-420);g.lineTo(0,custom?120:420);g.stroke();g.font='600 26px Arial';g.fillStyle='#ffc2a6';g.fillText('X',custom?1080:453,-12);g.fillStyle='#b2dcff';g.fillText('Y',14,custom?-656:-416);g.font='18px Arial';g.fillStyle='#8194ad';g.fillText('O',-24,25);g.restore();}
function trace(progress){if(progress<=0)return;const last=Math.min(1600,Math.floor(progress*1600));g.save();g.beginPath();g.moveTo(path[0].x,path[0].y);for(let i=1;i<=last;i++)g.lineTo(path[i].x,path[i].y);const tip=pose(TAU*progress).p;g.lineTo(tip.x,tip.y);g.strokeStyle=`rgb(${rgb})`;g.lineWidth=3.6;g.lineJoin='round';g.lineCap='round';g.shadowColor=`rgb(${rgb})`;g.shadowBlur=14;g.stroke();g.shadowBlur=0;
 if(progress>=1&&(!custom||CUSTOM_DATA.closed)){g.closePath();const fill=g.createRadialGradient(-70,-70,20,0,45,300);fill.addColorStop(0,`rgba(${rgb},.16)`);fill.addColorStop(1,`rgba(${rgb},.035)`);g.fillStyle=fill;g.fill('evenodd');}g.restore();}
function point(key,s,t){g.save();const bright=key==='p',color=key==='a'?'255,128,100':key==='b'?'130,196,255':'255,232,170';
 for(let i=28;i>0;i--){const ago=.5*i/28,old=stateAt(Math.max(0,t-ago))[key],next=stateAt(Math.max(0,t-ago+.5/28))[key];g.strokeStyle=`rgba(${color},${Math.pow(1-i/29,1.6)*.65})`;g.lineWidth=(bright?3:4.5)*(1-i/30);g.beginPath();g.moveTo(old.x,old.y);g.lineTo(next.x,next.y);g.stroke();}
 const p=s[key];g.globalCompositeOperation='lighter';g.drawImage(sprites[key],p.x-52,p.y-52,104,104);g.globalCompositeOperation='source-over';g.fillStyle=bright?'#fffce9':`rgb(${color})`;g.beginPath();g.arc(p.x,p.y,bright?4.5:5.2,0,TAU);g.fill();g.font='500 21px Arial';g.fillStyle=`rgb(${color})`;g.fillText(key.toUpperCase(),p.x+(key==='a'?-24:15),p.y+(key==='a'?31:-16));g.restore();}
function render(t){const s=stateAt(t);g.setTransform(1,0,0,1,0,0);g.globalAlpha=1;g.drawImage(bg,0,0);g.save();g.translate(CX,CY);axes();trace(s.traceProgress);
 g.save();g.strokeStyle='rgba(218,229,241,.55)';g.lineWidth=2;g.beginPath();g.moveTo(s.a.x,s.a.y);g.lineTo(s.b.x,s.b.y);g.stroke();g.restore();point('a',s,t);point('b',s,t);point('p',s,t);g.restore();
 const labels={circle:'连线的中点，画出一个圆',heart:'描绘点沿连线移动，画出心形',star:'描绘点沿连线移动，画出五角星'};g.textAlign='center';g.font='600 46px "Microsoft YaHei",sans-serif';g.fillStyle='#e7eff8';g.fillText(CONFIG.label|| (custom?'描绘点沿连线移动，画出'+CUSTOM_DATA.label:labels[CONFIG.shape]),960,975);g.font='24px "Microsoft YaHei",sans-serif';g.fillStyle='#8c9fb9';g.fillText('A、B 分别沿两根坐标轴滑动，间距保持不变',960,1023);g.textAlign='start';return s;
}
return {stateAt,render,pose,length:L,drawSeconds:DRAW,path};
})();
