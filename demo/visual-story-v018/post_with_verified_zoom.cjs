'use strict';
// Reuse the recorder's post stage; repair only its inert dynamic crop expression.
// Original crop w/h are evaluated at initialization, so time-dependent dimensions
// never zoomed in decoded probe frames. zoompan evaluates its expression per frame.
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const root=path.resolve(__dirname,'../..');
const build=path.join(root,'reports/demo-visuals-v018/.build');
const original='/home/yap/tools/demo-recorder/lib/post.js';
let src=fs.readFileSync(original,'utf8');
const sourceSha=crypto.createHash('sha256').update(src).digest('hex');
const start=src.indexOf('  return `crop=w=');
const end=src.indexOf('\n}',start);
if(start<0||end<0)throw new Error('Recorder post implementation changed; review patch first');
src=src.slice(0,start)+`  const timed = value => value.replace(/\\bt\\b/g, "it");
  const scale = timed(S), centerX = timed(cx), centerY = timed(cy);
  return "fps=30,zoompan=z='1+" + (Z - 1) + "*" + scale + "'"
    + ":x='min(max(" + centerX + "-iw/zoom/2,0),iw-iw/zoom)'"
    + ":y='min(max(" + centerY + "-ih/zoom/2,0),ih-ih/zoom)'"
    + ":d=1:s=" + width + "x" + height + ":fps=30";`+src.slice(end);
src=src.replace('`fps=30,format=yuv420p`;', '(scene.card ? "" : "scale=1600:900,pad=1920:1080:160:0:color=0x193647,") + `fps=30,format=yuv420p`;');
const patched=path.join(build,'post-verified.cjs');fs.writeFileSync(patched,src);
fs.writeFileSync(path.join(build,'recorder-zoom-patch.json'),JSON.stringify({original,sourceSha256:sourceSha,patchedSha256:crypto.createHash('sha256').update(src).digest('hex'),boundary:'Project-local copy of existing post stage. Shared recorder unchanged. Director policy: center report tables horizontally at x=960, follow recorded vertical focus, reserve a 180px caption band for live UI and keep its full frame visible. Original focus coordinates stay in source_focus. fps=30 normalizes captured frames, zoompan d=1 evaluates original focus envelope per input frame.'},null,2));
const scenes=process.argv.includes('--probe') ? require(path.join(build,'motion-probe.cjs')) : require('./scenes-captioned.cjs');
const sourceDir=process.argv[2]||'reports/demo-visuals-v018/captioned-video-v2';
const outDir=path.resolve(root,process.argv[3]||'reports/demo-visuals-v018/verified-video-safe');
if(fs.existsSync(outDir))throw new Error('Choose a fresh post output directory');
fs.mkdirSync(outDir,{recursive:true});
const manifest=JSON.parse(fs.readFileSync(path.resolve(root,sourceDir,'timestamps.json'),'utf8')).map(m=>({...m,source_focus:m.focus||[],focus:(m.focus||[]).map(f=>({...f,x:960}))}));
if(manifest.length!==scenes.length||manifest.some(m=>m.error||!fs.existsSync(m.file)))throw new Error('Capture evidence incomplete');
fs.writeFileSync(path.join(outDir,'timestamps.json'),JSON.stringify(manifest,null,2));
fs.writeFileSync(path.join(outDir,'scenes.used.json'),JSON.stringify(scenes,null,2));
require(patched).post(scenes,manifest,{outDir,width:1920,height:1080,log:console.log}).catch(e=>{console.error(e);process.exitCode=1;});
