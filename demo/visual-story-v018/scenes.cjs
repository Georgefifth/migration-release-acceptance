'use strict';
const path=require('path');
const fs=require('fs');
const crypto=require('crypto');
const {pathToFileURL}=require('url');
const root=path.resolve(__dirname,'../..');
const out=path.join(root,'reports/demo-visuals-v018');
const evidence=JSON.parse(fs.readFileSync(path.join(out,'evidence-manifest.json'),'utf8'));
for(const item of evidence.inputs){
 const digest=crypto.createHash('sha256').update(fs.readFileSync(path.join(root,item.path))).digest('hex');
 if(digest!==item.sha256)throw new Error('Saved demo evidence changed: '+item.path);
}
const card=(name,image,duration,vo)=>({name,duration,card:{preset:'swiss',accent:'#246B78',bg1:'#FBFCFE',bg2:'#E9F0F5',image:path.join(out,'assets',image+'.png')},vo});
const report=(candidate)=>pathToFileURL(path.join(root,'reports/validation-expansion5/runs/package-v018/upstream',candidate+'.html')).href;
const action=(sel,ms,shot)=>[{type:'waitFor',sel},{type:'click',sel},{type:'scrollIntoView',sel:'#operation-table'},{type:'wait',ms}];
module.exports=[
 card('problem','s01-overlap',11,'During a rolling release, old and new code share the migrated database. A successful rename can leave old requests pointing at a missing column.'),
 card('architecture-sql','s02-architecture-1',8,'Migration Acceptance applies reviewed SQL inside a disposable PostgreSQL schema. The runner has its own database connection.'),
 card('architecture-http','s02-architecture-2',9,'Two independent HTTP applications send real requests. Each request uses a separate database connection, so the probes observe committed behavior.'),
 card('architecture-reports','s02-architecture-3',7,'The runner preserves operation results and cleanup evidence as JSON, Markdown, and offline HTML. These diagrams explain the system.'),
 card('release-probes','s03-probes',9,'Six phases check the baseline, migration, both application versions, mixed writes, and a restarted old application. This workflow contains sixteen checks.'),
 {name:'actual-migration-pass',session:'rename',url:report('rename-title'),actions:action('label[for="stage-migration"]',8000,'live-migration'),vo:'Now inspect the saved local FastAPI test report. The migration passed. This is recorded evidence from version zero point one point eight.'},
 {name:'actual-old-app-failure',session:'rename',actions:action('label[for="stage-rollout"]',9000,'live-old-app'),caption:'The migration passed. Old-version reads and writes failed with SQLSTATE 42703. Verdict: BLOCK.',vo:'Selecting the old application reveals failed reads and writes. The missing-column SQL state is four two seven zero three. The result is BLOCK.'},
 {...card('annotated-result','s09-report',9,'The same run records eight passing checks and eight failures. Migration success and application compatibility are separate observations.'),session:'rename'},
 card('compatible-expansion','s04-expand',12,'The compatible candidate retains both storage columns and synchronizes writes. Both application versions can keep using their expected column during the overlap.'),
 {name:'actual-compatible-run',session:'compatible',url:report('item-title-storage'),actions:action('label[for="stage-mixed"]',9500,'live-compatible'),vo:'In the compatible FastAPI run, all sixteen checks pass. Mixed-version probes confirm that one version can read what the other version wrote.'},
 {...card('rollback-sequence','s05-rollback',11,'Application rollback keeps the migrated schema. The harness stops both apps, restarts old code, and compares its reads with the latest acknowledged writes.'),session:'compatible'},
 {name:'actual-rollback-probes',session:'compatible',actions:action('label[for="stage-app_rollback"]',9000,'live-rollback'),vo:'The report records the restart and both rollback reads. A running old process alone is insufficient. Its data requests must still return the expected values.'},
 card('verdict-boundaries','s07-decisions',11,'Known compatibility failures block. Incomplete execution, uncertain cleanup, or unknown request errors remain inconclusive. A scoped go requires every declared probe to pass.'),
 card('external-evidence','s06-evidence',13,'External SQL cases exposed a concurrent-index execution gap. Development agreement improved from three of four to four of four. Four unopened cases then matched. Earlier cases passed regression.'),
 card('scope-and-close','s08-scope',12,'These results support a bounded compatibility rehearsal. They do not establish production scale, concurrent load, or unmapped business rules. The GitLab project preserves the implementation and CI integration.')
];
