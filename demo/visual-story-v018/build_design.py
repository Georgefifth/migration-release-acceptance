"""Author editable diagram objects; reuse recorder frames.js for PNG rendering."""
from pathlib import Path
import json,html,hashlib,shutil,base64
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'reports/demo-visuals-v018'
SOURCE=Path(__file__).resolve().parent
C=dict(paper='#FBFCFE',field='#E9F0F5',ink='#193647',link='#246B78',fail='#A03446',passed='#246148',line='#CDDCE5',muted='#506779',white='#FFFFFF')
slides=[];current=None

def obj(kind,name,x,y,w,h,**kw):
    current['objects'].append(dict(kind=kind,name=name,x=x,y=y,w=w,h=h,**kw))
def rect(name,x,y,w,h,fill='white',stroke='line',width=2):obj('rect',name,x,y,w,h,fill=C.get(fill,fill),stroke=C.get(stroke,stroke),stroke_width=width)
def text(name,value,x,y,w,h,size=32,color='ink',bold=False,mono=False):obj('text',name,x,y,w,h,text=value,size=size,color=C.get(color,color),bold=bold,font='DejaVu Sans Mono' if mono else 'DejaVu Sans')
def line(name,x,y,w,h,color='link',width=4):obj('line',name,x,y,w,h,color=C.get(color,color),stroke_width=width)
def arrow(name,x,y,w,h,color='link',direction='right'):obj('arrow',name,x,y,w,h,color=C.get(color,color),direction=direction)
def box(name,label,x,y,w=360,h=140,detail=None,color='ink'):
    rect(name,x,y,w,h,stroke=color);text(name+'-label',label,x+24,y+20,w-48,52,32,color,True)
    if detail:text(name+'-detail',detail,x+24,y+78,w-48,h-80,26,'muted')
def begin(id,title,sub='',notes=''):
    global current
    current=dict(id='s'+id,title=title,notes=notes,background=C['paper'],objects=[]);slides.append(current)
    rect('header-band',0,0,1920,12,'ink','ink',0)
    text('title',title,96,72,1728,150,64,'ink',True)
    if sub:text('subtitle',sub,100,220,1720,80,30,'muted')
def foot(value):text('scope-note',value,100,835,1720,54,23,'muted')

begin('01-overlap','Successful SQL can break old requests','A rolling release briefly runs two application versions.', 'Diagram based on the saved v0.1.8 pinned FastAPI rename-title result. API title stays unchanged. Physical v2 field is display_title. This change is ours, not an upstream defect.')
box('old','Old application',100,360,470,145,'Reads column title','fail')
box('new','New application',100,610,470,145,'Reads column display_title','passed')
arrow('old-request',590,412,380,24,'fail');text('old-failure','42703: column missing',600,360,500,50,28,'fail',True)
arrow('new-request',590,660,380,24,'passed');text('new-success','Request succeeds',620,610,400,50,28,'passed',True)
rect('database',1090,340,690,430,'field','ink',3)
text('db-title','Migrated PostgreSQL schema',1130,380,610,80,36,'ink',True)
text('rename','RENAME title TO display_title',1130,480,610,60,28,'ink',False,True)
text('present','display_title exists',1130,590,600,60,34,'passed',True)
text('missing','title no longer exists',1130,670,600,60,34,'fail',True)
foot('Pinned FastAPI reference. Synthetic records. The SQL succeeds before compatibility probes run.')

for phase in (1,2,3):
    begin(f'02-architecture-{phase}', ['A disposable migration rehearsal','Real requests cross version boundaries','Reports preserve bounded evidence'][phase-1], 'One reviewed workflow, two independent HTTP processes, one disposable schema.', 'Architecture verified against acceptance/runner.py, http_client.py, http_app.py and integrations/fastapi_launcher.py. Each HTTP request owns its DB connection. The runner separately applies baseline and candidate SQL. No concurrent load testing.')
    sqlcolor='link' if phase==1 else 'line';httpcolor='link' if phase==2 else 'line';reportcolor='link' if phase==3 else 'line'
    box('runner','Test runner',100,410,370,140,'Reviewed configuration')
    box('v1','Old HTTP app',700,360,370,135,'Independent process')
    box('v2','New HTTP app',700,590,370,135,'Independent process')
    box('pg','PostgreSQL',1410,430,400,230,'Disposable schema')
    text('pg-note','Synthetic records',1434,584,340,50,27)
    line('ddl-start',285,260,0,150,sqlcolor);line('ddl-top',285,260,1325,0,sqlcolor);arrow('ddl-end',1598,260,25,150,sqlcolor,'down')
    text('ddl-label','Baseline and candidate SQL',630,285,720,55,28,'link' if phase==1 else 'muted')
    line('http-fork-in',470,465,100,0,httpcolor);line('http-fork',570,425,0,230,httpcolor)
    arrow('http-v1',570,413,110,24,httpcolor);arrow('http-v2',570,643,110,24,httpcolor)
    text('http-label','HTTP',492,530,190,55,26)
    line('v1-db',1070,425,150,0,httpcolor);line('v2-db',1070,655,150,0,httpcolor);line('db-join',1220,425,0,230,httpcolor);arrow('db-in',1220,528,170,24,httpcolor)
    text('connections','Separate DB\nconnections',1210,710,590,95,26)
    arrow('report-flow',272,570,24,165,reportcolor,'down')
    rect('report-output',100,755,900,70,'field',reportcolor)
    text('report-types','JSON   Markdown   Offline HTML',125,766,840,50,30,'link' if phase==3 else 'muted',True)
    foot('Sequential request interleavings. Returning to old code does not undo the schema migration.')

begin('03-probes','The rehearsal follows the release','Six phases preserve operation-level results and cleanup evidence.', 'Stage counts come from runner.CHECK_IDS: baseline 3, migration 1, target 3, rollout 2, mixed 4, app_rollback 3. 16 total. Synthetic sequential interleavings, not concurrent requests.')
for i,(name,count) in enumerate([('Baseline',3),('Migration',1),('New app',3),('Old app',2),('Mixed versions',4),('App rollback',3)]):
    x=100+i*287
    rect('stage-'+str(i),x,365,260,200,'field','link')
    text('stage-name-'+str(i),name,x+20,390,225,70,26,'ink',True)
    text('stage-count-'+str(i),str(count)+' checks' if count>1 else '1 check',x+20,485,215,55,32,'link')
    if i<5:arrow('stage-arrow-'+str(i),x+258,451,24,24)
text('mixed-detail','Mixed-version probes',100,620,650,60,36,'ink',True)
text('old-new','Old writes, new reads',100,705,770,60,32)
arrow('mixed-direction',870,714,120,22)
text('new-old','New writes, old reads',1050,705,750,60,32)
foot('Probe count describes this declared workflow. It does not measure overall application coverage.')

begin('04-expand','Two candidates, different outcomes','The new API field remains title. Only its database storage mapping changes.', 'Sources: integrations/fastapi_fixtures/breaking.sql and expand.sql; package-v018/upstream reports. Expand retains title and display_title and synchronizes writes with a trigger. No assertion that all expand/contract migrations are safe.')
text('rename-title','Rename immediately',100,340,780,70,40,'fail',True)
text('expand-title','Retain and synchronize',1060,340,760,70,40,'passed',True)
rect('rename-schema',100,450,700,135,'field','fail');text('rename-field','display_title',140,490,610,60,36,'ink',False,True)
text('rename-old','Old code expects title',100,625,790,55,32,'fail')
text('rename-result','BLOCK',100,720,760,80,52,'fail',True)
rect('expand-schema',1060,450,760,135,'field','passed')
text('retained-field','title',1090,490,180,60,34,'ink',False,True);arrow('sync-right',1300,481,90,20,'passed');arrow('sync-left',1300,531,90,20,'passed','left')
text('new-field','display_title',1425,490,370,60,34,'ink',False,True)
text('expand-requests','Old and new requests work',1060,625,770,55,32,'passed')
text('expand-result','GO_WITHIN_SCOPE',1060,720,760,80,48,'passed',True)
foot('Observed in the pinned FastAPI test integration. Human reviewers still decide whether to release.')

begin('05-rollback','Code rollback keeps the new schema','A restarted old process must read data written during the rollout.', 'Source runner.run/restart_old, rollback_read and rollback_new_data. The latest acknowledged write is compared exactly. Both apps stop, old app restarts with a different PID, the migrated schema remains. No SQL undo.')
for i,(label,detail) in enumerate([('Stop both apps','End old and new processes'),('Restart old code','Verify a different process ID'),('Read committed data','Compare the expected value')]):
    x=100+i*590;box('rollback-'+str(i),label,x,370,530,160,detail)
    if i<2:arrow('rollback-arrow-'+str(i),x+540,435,40,24)
rect('schema-persists',100,630,1710,145,'field','link',3)
text('schema-persists-label','Same migrated PostgreSQL schema throughout',140,670,1620,65,38,'ink',True)
foot('This verifies application rollback for declared probes. It does not restore the previous schema.')

begin('06-evidence','External cases exposed a real gap','Single-statement concurrent index DDL needed an explicit execution mode.', 'Sources reports/validation-expansion5/frozen.json, original baseline-v017, repaired-v018, first-holdout-v018, legacy63/regression-v018. Atlas SQL excerpts pinned to tree ed994a77898e48377f9a9c391f2d1c49f5703b8d, Apache-2.0. Baselines and HTTP mapping are evaluator adaptations. 4/4 holdout all expect scoped GO. Counts mean expected-verdict agreement, not accuracy or fair competitor ranking.')
for row,(label,n,den,color) in enumerate([('Original development',3,4,'fail'),('Repaired development',4,4,'passed'),('Unseen holdout',4,4,'passed')]):
    y=350+row*145;text('evidence-label-'+str(row),label,100,y+8,650,70,34,'ink',True)
    for i in range(den):rect('case-'+str(row)+'-'+str(i),770+i*105,y,82,82,'passed' if i<n else 'fail','white',0)
    text('evidence-count-'+str(row),f'{n}/{den}',1250,y+8,250,70,46,color,True)
text('regression','63/63 earlier cases reproduced',100,760,1620,50,34,'ink',True)
foot('Expected verdict agreement. Repaired development and earlier cases are regressions, not independent accuracy.')

begin('07-decisions','Verdicts follow the evidence','Unknown failures never become release approval.', 'Simplified decision diagram of acceptance.runner.verdict. Lifecycle, candidate, completeness and cleanup gates remain decisive. Known compatibility failures yield BLOCK. Unknown request failures yield INCONCLUSIVE. Valid dependent skips require the failed parent and never permit GO.')
box('guard','Complete execution and cleanup?',100,340,1110,135,'Includes baseline, migration and app lifecycle')
arrow('no-arrow',1230,395,170,22,'muted');text('no-label','No',1270,345,120,45,26,'muted')
box('guard-unknown','INCONCLUSIVE',1430,340,390,135,'Evidence incomplete','muted')
arrow('yes-arrow',637,485,24,95,'link','down');text('yes-label','Yes',700,495,160,45,27,'link')
for x,title,detail,color in [(100,'BLOCK','Known compatibility failure','fail'),(690,'GO_WITHIN_SCOPE','All required probes pass','passed'),(1280,'INCONCLUSIVE','Unknown request failure','muted')]:
    box('outcome-'+str(x),title,x,660,530,145,detail,color)
line('decision-bar',365,605,1180,0);line('decision-vertical',650,580,0,25)
for x in (365,955,1545):arrow('branch-'+str(x),x-12,605,24,45,'link','down')
foot('Schematic decision logic. A scoped GO covers the recorded fixture and declared application operations only.')

begin('08-scope','Evidence has a defined boundary','Migration Acceptance helps reviewers inspect application compatibility.', 'Source current README, AGENTS, runner limitations and latest external validation results. No production scale, lock-duration, full security, customer adoption or cross-tool superiority has been established. Canonical project remains GitLab; Pages only shows static reports.')
rect('checked-scope',100,350,1000,430,'field','link',3)
text('checked-title','Verified rehearsal',140,395,900,70,42,'ink',True)
text('checked-copy','One mapped CRUD workflow\nOld and new HTTP applications\nExact reads after app rollback\nSaved results and cleanup evidence',140,505,900,230,34)
text('outside-title','Still unverified',1200,395,650,70,42,'muted',True)
text('outside-copy','Production scale and lock waits\nConcurrent application load\nUnmapped business invariants\nIndependent customer adoption',1200,505,650,230,32,'muted')
foot('GitLab hosts the project and CI integration. This video inspects saved local v0.1.8 test evidence.')

begin('09-report','One migration passed. Eight probes failed.','The saved report separates migration success from application compatibility.', 'Unmodified screenshot captured by the requested demo-recorder motion probe from the saved rename-title.html report. Cropped only for readability. Run 01f0b17e-afe4-4bde-8120-da3c68fa2193. Local v0.1.8 execution, not a live GitLab run.')
shot=OUT/'assets/actual-old-app-report.png'
if shot.exists():
    obj('image','report-headline',100,340,1232,330,path=str(shot),crop=[400/1920,180/1080,400/1920,600/1080],viewbox=[400,180,1120,300])
    obj('image','report-phases',100,720,1232,116,path=str(shot),crop=[400/1920,510/1080,400/1920,465/1080],viewbox=[400,510,1120,105])
text('report-result-label','Observed result',1430,350,400,60,34,'ink',True)
text('report-result','8 passed\n8 failed\nBLOCK',1430,450,390,190,40,'fail',True)
arrow('report-point',1350,545,55,24,'fail','left')
text('report-phase-note','Migration passed\nOld app failed',1400,720,430,115,30,'ink',True)
foot('Actual saved report screenshot. Cropped for readability. Source and run identity are retained in the manifest.')

order=['s01-overlap','s02-architecture-1','s02-architecture-2','s02-architecture-3','s03-probes','s09-report','s04-expand','s05-rollback','s07-decisions','s06-evidence','s08-scope']
slides.sort(key=lambda slide:order.index(slide['id']))

# Keep geometry editable and deterministic across SVG, HTML and native PPTX export.
for slide in slides:
 for o in slide['objects']:
  assert o['x']>=0 and o['y']>=0 and o['x']+o['w']<=1920 and o['y']+o['h']<=900,(slide['id'],o)
SOURCE.joinpath('slides.json').write_text(json.dumps(dict(canvas=[1920,1080],colors=C,slides=slides),indent=2)+'\n')
def esc(s):return html.escape(str(s),quote=True)
def svg(slide):
 parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080" role="img" aria-label="{esc(slide["title"])}">',f'<rect width="1920" height="1080" fill="{slide["background"]}"/>']
 for o in slide['objects']:
  x,y,w,h=o['x'],o['y'],o['w'],o['h'];k=o['kind'];start=f'<g id="{esc(o["name"])}">';parts.append(start)
  if k=='rect':parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{o["fill"]}" stroke="{o["stroke"]}" stroke-width="{o["stroke_width"]}"/>')
  elif k=='text':
   lines=o['text'].split('\n');size=o['size'];parts.append(f'<text fill="{o["color"]}" font-family="{o["font"]}" font-size="{size}" font-weight="{700 if o["bold"] else 400}">')
   for i,t in enumerate(lines):parts.append(f'<tspan x="{x}" y="{y+size+i*size*1.36}">{esc(t)}</tspan>')
   parts.append('</text>')
  elif k=='image':
   encoded=base64.b64encode(Path(o['path']).read_bytes()).decode()
   v=' '.join(str(t) for t in o['viewbox'])
   parts.append(f'<svg x="{x}" y="{y}" width="{w}" height="{h}" viewBox="{v}"><image width="1920" height="1080" href="data:image/png;base64,{encoded}"/></svg>')
  elif k=='line':parts.append(f'<line x1="{x}" y1="{y}" x2="{x+w}" y2="{y+h}" stroke="{o["color"]}" stroke-width="{o["stroke_width"]}"/>')
  elif k=='arrow':
   if o['direction']=='right':pts=[(x,y+h*.3),(x+w-h,y+h*.3),(x+w-h,y),(x+w,y+h*.5),(x+w-h,y+h),(x+w-h,y+h*.7),(x,y+h*.7)]
   elif o['direction']=='left':pts=[(x+w,y+h*.3),(x+h,y+h*.3),(x+h,y),(x,y+h*.5),(x+h,y+h),(x+h,y+h*.7),(x+w,y+h*.7)]
   else:pts=[(x+w*.3,y),(x+w*.7,y),(x+w*.7,y+h-w),(x+w,y+h-w),(x+w*.5,y+h),(x,y+h-w),(x+w*.3,y+h-w)]
   parts.append('<polygon points="'+' '.join(f'{a},{b}' for a,b in pts)+f'" fill="{o["color"]}"/>')
  parts.append('</g>')
 return ''.join(parts)+'</svg>'
svgs=OUT/'exports/svg';svgs.mkdir(parents=True,exist_ok=True)
for slide in slides:(svgs/(slide['id']+'.svg')).write_text(svg(slide))
body=''.join(f'<section class="slide" id="{s["id"]}" aria-label="{esc(s["title"])}">{svg(s)}</section>' for s in slides)
(OUT/'exports/slides.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>Migration Acceptance visual story</title><style>html,body{margin:0;background:#e9f0f5}.slide{width:1920px;height:1080px;overflow:hidden;margin:0 0 40px}svg{display:block}*{box-sizing:border-box}</style>'+body+'</html>')
inputs=[]
for name in ('rename-title','item-title-storage'):
 p=ROOT/'reports/validation-expansion5/runs/package-v018/upstream'/(name+'.json');data=json.loads(p.read_text());assert data['completed'] and data['cleanup_ok'] and len(data['checks'])==16
 assert data['verdict']==('BLOCK' if name=='rename-title' else 'GO_WITHIN_SCOPE')
 inputs.append(dict(path=str(p.relative_to(ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),run_id=data['run_id'],verdict=data['verdict'],recorded_commit=data['commit'],boundary='Saved local v0.1.8 run, not a live CI execution.'))
(OUT/'evidence-manifest.json').write_text(json.dumps(dict(inputs=inputs,validation_summary_sha256=hashlib.sha256((ROOT/'reports/validation-expansion5/summary.json').read_bytes()).hexdigest(),runtime_commit='88d12e9',upstream_commit='b1125d8839482cb7bbae603ddc6d0081bf87532e'),indent=2)+'\n')
print(f'Authored {len(slides)} editable vector frames, with actual evidence identities.')
