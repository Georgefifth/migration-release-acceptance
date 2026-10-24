"""Freeze Atlas SQL excerpts and explicit migration-execution task expectations."""
import hashlib
import json
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/validation-expansion5'


def main():
    if (OUT/'frozen.json').exists():raise SystemExit('Do not overwrite frozen Atlas cases')
    records=json.loads((OUT/'sources/downloads.json').read_text())
    source=next(r for r in records if r['path']=='sql/postgres/migrate_test.go')
    raw=(OUT/'sources/atlas'/source['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==source['sha256']
    cases=[]
    base="CREATE TABLE users(id bigint PRIMARY KEY,payload text,success boolean DEFAULT true,a int DEFAULT 0,b int DEFAULT 0); INSERT INTO users(id,payload) VALUES(1,'12');"
    def add(name,statement,expected,probe,baseline=base,nontransactional=False,holdout=False,state=None):
        assert statement in raw.decode(),statement
        directory=OUT/'inputs'/name;directory.mkdir(parents=True)
        data=dict(id=name,table='users',key='id',old_column='payload',new_column='payload',
                  values=dict(initial='12',created='13',old_write='14',new_write='15',new_update='16',old_update='17'),
                  candidate_transactional=not nontransactional,
                  provenance={k:source[k] for k in ('repository','revision','path','sha256')})
        (directory/'input.json').write_text(json.dumps(data,indent=2)+'\n');(directory/'baseline.sql').write_text(baseline+'\n');(directory/'candidate.sql').write_text(statement+'\n')
        cases.append(dict(id=name,split='holdout' if holdout else 'development',difficulty='Advanced',category='external_sql',source=dict(source,extracted_statement=statement),
                          expected_verdict=expected,oracle_sql=probe,oracle_state=None,migration_state=state,
                          execution_boundary='Explicit no-wrapper mode requested for valid single-statement concurrent DDL; v0.1.7 has no such API.' if nontransactional else 'Default transaction wrapper',
                          capability_gap_case=nontransactional))
    def exists(name):return "SELECT EXISTS(SELECT 1 FROM pg_indexes WHERE schemaname=current_schema() AND indexname='"+name+"')"
    add('atlas-concurrent-create','CREATE INDEX CONCURRENTLY "add_con" ON "users" ("id")','GO_WITHIN_SCOPE',exists('add_con'),nontransactional=True)
    add('atlas-covering-index','CREATE INDEX "include_key" ON "users" ("id") INCLUDE ("a", "b")','GO_WITHIN_SCOPE',exists('include_key'))
    add('atlas-brin-order-option','CREATE INDEX "id_brin" ON "users" USING BRIN ("id" DESC) WITH (pages_per_range = 2)','INCONCLUSIVE','',state='0A000')
    add('atlas-ordinary-drop','DROP INDEX "name_index"','GO_WITHIN_SCOPE',exists('name_index').replace('SELECT EXISTS','SELECT NOT EXISTS'),baseline=base+' CREATE INDEX name_index ON users(id);')
    add('atlas-concurrent-drop','DROP INDEX CONCURRENTLY "drop_con"','GO_WITHIN_SCOPE',exists('drop_con').replace('SELECT EXISTS','SELECT NOT EXISTS'),
        baseline=base+' CREATE INDEX drop_con ON users(id);',nontransactional=True,holdout=True)
    add('atlas-partial-index','CREATE INDEX "id_key" ON "users" ("id" DESC) WHERE success','GO_WITHIN_SCOPE',exists('id_key'),holdout=True)
    add('atlas-brin-operator-classes','CREATE INDEX "operator_class" ON "users" USING BRIN ("id" int8_bloom_ops, "id", "id" int8_minmax_multi_ops(values_per_range=8))','GO_WITHIN_SCOPE',exists('operator_class'),holdout=True)
    add('atlas-unique-id-index','CREATE UNIQUE INDEX "nulls_distinct" ON "users" ("id")','GO_WITHIN_SCOPE',exists('nulls_distinct'),holdout=True)
    frozen=dict(frozen_at=datetime.now(timezone.utc).isoformat(),cases=cases,requires_least_privilege=True,
                input_sha256={str(p.relative_to(OUT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((OUT/'inputs').rglob('*')) if p.is_file()},
                acceptance='All confirmed task expectations must match. Concurrent SQL is valid under independent autocommit; unsupported requested mode is a capability gap, not a false approval. Unresolved references excluded, never relabeled after execution.',
                source_boundary='Atlas planner/formatter expected strings are not database ground truth. Direct PostgreSQL oracle confirms each statement. No Atlas engine execution or superiority claim.',
                mode_boundary='candidate_transactional input is an explicit requested capability; old adapter/product do not implement it. A later reviewed API passthrough is an implementation change, not altered oracle labels.')
    (OUT/'frozen.json').write_text(json.dumps(frozen,indent=2)+'\n');(OUT/'frozen.sha256').write_text(hashlib.sha256((OUT/'frozen.json').read_bytes()).hexdigest()+'\n')
    print('Frozen eight Atlas cases (four development, four untouched holdout).')


if __name__=='__main__':main()
