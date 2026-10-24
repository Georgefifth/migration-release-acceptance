import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {Presentation, PresentationFile} from '@oai/artifact-tool';
const root='/home/yap/Hack/Life After Code/migration-release-acceptance';
const workspaceDir=path.join(root,'reports/demo-visuals-v018');
const skill='/home/yap/.codex/plugins/cache/openai-primary-runtime/presentations/26.1022.11436/skills/presentations';
const runtime='/home/yap/.cache/codex-runtimes/codex-primary-runtime/dependencies';
process.env.RUNTIME_NODE_MODULES=path.join(runtime,'node/node_modules');
const data=JSON.parse(await fs.readFile(path.join(root,'demo/visual-story-v018/slides.json'),'utf8'));
const presentation=Presentation.create({slideSize:{width:1920,height:1080}});
for(const spec of data.slides){
 const slide=presentation.slides.add();slide.background.fill=spec.background;
 slide.speakerNotes.text=spec.notes+'\nSource evidence: reports/demo-visuals-v018/evidence-manifest.json. Visual explanation, not a live execution.\nThe bottom 180 px are reserved for video captions.';
 for(const o of spec.objects){
  if(o.kind==='image'){
   const [left,top,right,bottom]=o.crop;
   slide.images.add({blob:new Uint8Array(await fs.readFile(o.path)),contentType:'image/png',alt:o.name,fit:'cover',crop:{left,top,right,bottom},position:{left:o.x,top:o.y,width:o.w,height:o.h}});
   continue;
  }
  let geom=o.kind==='text'?'textbox':o.kind==='line'?'line':o.kind==='arrow'?({right:'rightArrow',left:'leftArrow',down:'downArrow'}[o.direction]):'rect';
  const shape=slide.shapes.add({geometry:geom,name:o.name,position:{left:o.x,top:o.y,width:o.w,height:o.h},fill:o.kind==='text'||o.kind==='line'?'none':o.fill||o.color,line:{fill:o.kind==='rect'?o.stroke:o.kind==='line'?o.color:'none',width:o.stroke_width||0,style:'solid'}});
  if(o.kind==='text'){
   shape.text=o.text;shape.text.insets=0;
   shape.text.style={typeface:o.font,fontSize:o.size,color:o.color,bold:o.bold,verticalAlignment:'top'};
  }
 }
}
await fs.mkdir(path.join(workspaceDir,'.codex-finalizer'),{recursive:true});
const candidate=path.join(workspaceDir,'.codex-finalizer/candidate.pptx');
await (await PresentationFile.exportPptx(presentation)).save(candidate);
await fs.mkdir(path.join(workspaceDir,'.build/native-previews'),{recursive:true});
for(let i=0;i<presentation.slides.items.length;i++){
 const blob=await presentation.export({slide:presentation.slides.items[i],format:'png',scale:1});
 await fs.writeFile(path.join(workspaceDir,'.build/native-previews',data.slides[i].id+'.png'),new Uint8Array(await blob.arrayBuffer()));
}
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const result=await finalizePresentation({workspaceDir,candidatePath:candidate,finalPath:path.join(workspaceDir,'exports/migration-acceptance-visual-story-v2.pptx'),pythonExecutable:path.join(runtime,'python/bin/python3'),integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','18288000,10287000','--validate-bullet-geometry','--validate-heading-fit'],requiredNativeTableOwnerSlides:[],requiredNativeChartOwnerSlides:[],fontPolicy:{basis:'design',families:['DejaVu Sans','DejaVu Sans Mono']},verifyArtifactToolImport:true,receiptPath:path.join(workspaceDir,'.codex-finalizer/validation-v2.json')});
console.log(JSON.stringify(result,null,2));
