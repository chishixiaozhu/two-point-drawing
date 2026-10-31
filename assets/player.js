(()=>{'use strict';
const D=12,W=1920,H=1080,$=id=>document.getElementById(id),canvas=$('film'),render=t=>{Mechanism.render(t);$('seek').value=t;$('time').textContent=t.toFixed(1)+' / 12.0';return t};
let t=0,playing=false,raf=0,start=0,busy=false,rec=null,stream=null,lastFrame=-1,frames=0,maxGap=0,lastT=0,recording=false;
function pause(){playing=false;cancelAnimationFrame(raf);$('play').textContent='播放';}
function loop(now){if(!playing)return;const next=Math.min(D,(now-start)/1000),f=Math.floor(next*30);if(!recording||f>lastFrame){t=render(next);if(recording){lastFrame=f;frames++;maxGap=Math.max(maxGap,t-lastT);lastT=t;stream.getVideoTracks()[0]?.requestFrame?.();}}if(t>=D){pause();if(recording&&rec.state==='recording')rec.stop();}else raf=requestAnimationFrame(loop);}
function play(){pause();if(t>=D)t=0;start=performance.now()-t*1000;playing=true;$('play').textContent='暂停';raf=requestAnimationFrame(loop);}
function lock(on){busy=on;for(const id of ['play','restart','seek','export'])$(id).disabled=on;}
function fail(message){window.exportResult={ok:false,error:message};$('status').textContent=message;pause();recording=false;if(rec?.state==='recording')rec.stop();stream?.getTracks().forEach(x=>x.stop());lock(false);}
async function exportVideo(){
 if(!EXPORT_ENABLED)return {ok:false,error:'请先在对话里要求导出视频'};
 if(busy)return {ok:false,error:'正在导出'};
 if(!window.MediaRecorder||!canvas.captureStream){fail('此环境不支持导出，请用桌面浏览器打开此文件。');return window.exportResult;}
 const mime=['video/mp4','video/webm;codecs=vp9','video/webm'].find(v=>MediaRecorder.isTypeSupported(v));if(!mime){fail('没有可用的视频编码器');return window.exportResult;}
 pause();t=render(0);window.exportResult=null;lock(true);$('save').hidden=true;$('status').textContent='正在准备导出，请保持前台。';
 try{
  // 同规格预热并丢弃这一段，避免编码器冷启动吞掉片头。
  stream=canvas.captureStream(0);rec=new MediaRecorder(stream,{mimeType:mime,videoBitsPerSecond:12000000});
  await new Promise(resolve=>{let done=false;const finish=()=>{if(done)return;done=true;clearInterval(tick);clearTimeout(stop);clearTimeout(timeout);stream.getTracks().forEach(x=>x.stop());resolve();};const tick=setInterval(()=>{render(0);stream.getVideoTracks()[0]?.requestFrame?.()},33),stop=setTimeout(()=>{if(rec.state==='recording')rec.stop()},2200),timeout=setTimeout(()=>{fail('编码器准备超时');finish()},6500);rec.onstop=finish;rec.onerror=()=>{fail('编码器准备失败');finish()};try{rec.start()}catch(e){fail(e.message);finish()}});
  if(window.exportResult?.ok===false)return window.exportResult;
  stream=canvas.captureStream(0);rec=new MediaRecorder(stream,{mimeType:mime,videoBitsPerSecond:12000000});const chunks=[];let timeout;
  rec.ondataavailable=e=>{if(e.data.size)chunks.push(e.data)};rec.onerror=()=>fail('视频录制失败');
  rec.onstop=()=>{clearTimeout(timeout);recording=false;stream.getTracks().forEach(x=>x.stop());lock(false);if(window.exportResult?.ok===false)return;const blob=new Blob(chunks,{type:rec.mimeType||mime});if(t<D-.05||blob.size<1000){fail('视频未完整录制，请保持前台重试');return;}if(window.lastVideoURL)URL.revokeObjectURL(window.lastVideoURL);const url=URL.createObjectURL(blob),ext=blob.type.includes('mp4')?'mp4':'webm';window.lastVideoURL=url;$('save').href=url;$('save').download='双点描形-'+CONFIG.shape+'.'+ext;$('save').hidden=false;window.exportResult={ok:true,mime:blob.type,bytes:blob.size,renderedFrames:frames,maxRenderGap:maxGap};$('status').textContent=frames/D<24||maxGap>.2?'已导出，但渲染出现卡顿，请检查实际文件。':'已导出，请打开下载的视频检查。';$('save').click();};
  t=render(0);lastFrame=-1;frames=0;lastT=0;maxGap=0;recording=true;$('status').textContent='正在导出，请保持前台。';rec.start();play();timeout=setTimeout(()=>fail('导出超时，请保持前台重试'),22000);
 }catch(e){fail('无法导出：'+e.message)}return {ok:busy,started:busy};
}
$('play').onclick=()=>playing?pause():play();$('restart').onclick=()=>{t=render(0);play()};$('seek').oninput=e=>{pause();t=render(+e.target.value)};$('export').hidden=!EXPORT_ENABLED;$('export').onclick=exportVideo;
document.addEventListener('visibilitychange',()=>{if(busy&&document.hidden)fail('页面进入后台，请保持前台重新导出')});
window.SAMPLE={ready:true,renderAt(time){if(busy)throw Error('正在导出');pause();t=render(time);return Mechanism.stateAt(t)},play,pause};
window.animationInfo={version:'two-point-nc-2',shape:CONFIG.shape,color:CONFIG.color||'auto',duration:D,width:W,height:H,audio:'none',exportEnabled:EXPORT_ENABLED};window.exportVideo=exportVideo;render(0);
})();
