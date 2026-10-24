"""Freeze untouched external cases before the dependency-handling repair."""
import hashlib
import json
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/optimization-validation'


def main():
    if (OUT/'frozen.json').exists():
        raise SystemExit('Do not overwrite frozen optimization holdout')
    OUT.mkdir(parents=True,exist_ok=True)
    previous=ROOT/'reports/real-world-validation-round2/sources'
    sources=json.loads((previous/'downloads.json').read_text())
    cases=[]
    def add(name,file,statement,baseline,table,column,expected,probe='',state=None,migration_state=None,values=None):
        source=next(s for s in sources if s['path'].endswith('/'+file))
        assert hashlib.sha256((previous/file).read_bytes()).hexdigest()==source['sha256']
        assert statement in (previous/file).read_text()
        folder=OUT/'inputs'/name;folder.mkdir(parents=True)
        v=dict(initial='12',created='13',old_write='14',new_write='15',new_update='16',old_update='17');v.update(values or {})
        (folder/'input.json').write_text(json.dumps(dict(id=name,table=table,key='id',old_column=column,new_column=column,values=v,provenance={k:source[k] for k in ('repository','revision','path','sha256')}),indent=2)+'\n')
        (folder/'baseline.sql').write_text(baseline+'\n');(folder/'candidate.sql').write_text(statement+'\n')
        cases.append(dict(id=name,difficulty='Advanced',split='holdout',category='external_sql',source=dict(source,extracted_statement=statement),expected_verdict=expected,oracle_sql=probe,oracle_state=state,migration_state=migration_state))
    add('numeric-widen-large-write','alter_table.sql','ALTER TABLE test_inh_check ALTER COLUMN a TYPE numeric;',
        'CREATE TABLE test_inh_check(id int PRIMARY KEY,a integer); INSERT INTO test_inh_check VALUES(1,12);',
        'test_inh_check','a','GO_WITHIN_SCOPE','INSERT INTO test_inh_check VALUES(201,2147483648) RETURNING a=2147483648',values={'old_write':'2147483648'})
    add('add-default-column','generated.sql','ALTER TABLE gtest25 ADD COLUMN d int DEFAULT 101;',
        'CREATE TABLE gtest25(id int PRIMARY KEY,a integer); INSERT INTO gtest25 VALUES(1,12);',
        'gtest25','a','GO_WITHIN_SCOPE','INSERT INTO gtest25(id,a) VALUES(201,14) RETURNING d=101')
    add('domain-positive-only','domain.sql','alter domain con add check (VALUE > 0);',
        'CREATE DOMAIN con AS integer; CREATE TABLE domcontest(id int PRIMARY KEY,col1 con); INSERT INTO domcontest VALUES(1,12);',
        'domcontest','col1','BLOCK','INSERT INTO domcontest VALUES(201,-5)','23514',values={'old_write':'-5'})
    add('validate-domain-existing-invalid','domain.sql','ALTER DOMAIN things VALIDATE CONSTRAINT meow;',
        'CREATE DOMAIN things AS integer; CREATE TABLE thethings(id int PRIMARY KEY,stuff things); INSERT INTO thethings VALUES(1,55); ALTER DOMAIN things ADD CONSTRAINT meow CHECK(VALUE<11) NOT VALID;',
        'thethings','stuff','INCONCLUSIVE',migration_state='23514',values={'initial':'55','created':'5'})
    add('drop-expression-if-absent','generated.sql','ALTER TABLE gtest29 ALTER COLUMN a DROP EXPRESSION IF EXISTS;',
        'CREATE TABLE gtest29(id int PRIMARY KEY,a integer); INSERT INTO gtest29 VALUES(1,12);',
        'gtest29','a','GO_WITHIN_SCOPE','SELECT a=12 FROM gtest29 WHERE id=1')
    add('generated-on-generated-invalid','generated.sql','ALTER TABLE gtest25 ADD COLUMN x int GENERATED ALWAYS AS (b * 4) STORED;',
        'CREATE TABLE gtest25(id int PRIMARY KEY,a integer,b integer GENERATED ALWAYS AS(a*3) STORED); INSERT INTO gtest25(id,a) VALUES(1,12);',
        'gtest25','a','INCONCLUSIVE',migration_state='42P17')
    frozen=dict(frozen_at=datetime.now(timezone.utc).isoformat(),cases=cases,
                input_sha256={str(p.relative_to(OUT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((OUT/'inputs').rglob('*')) if p.is_file()},
                acceptance='All confirmed verdicts and exits must match; unresolved references excluded and reported. No tuning after opening.',
                source_boundary='New unexecuted SQL excerpts; synthetic schema/data/HTTP mapping, not new upstream business applications.')
    (OUT/'frozen.json').write_text(json.dumps(frozen,indent=2)+'\n');(OUT/'frozen.sha256').write_text(hashlib.sha256((OUT/'frozen.json').read_bytes()).hexdigest()+'\n')
    print('Frozen six external holdout cases before runtime changes.')


if __name__=='__main__':main()
