"""Freeze a second untouched external-SQL batch against unchanged v0.1.5."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/real-world-validation-round2'


def main():
    if (OUT/'frozen.json').exists():
        raise SystemExit('Do not overwrite a frozen second batch')
    sources=json.loads((OUT/'sources/downloads.json').read_text())
    cases=[]

    def add(name,file,statement,baseline,table,column,expected,probe='',state=None,
            migration_state=None,values=None,hazard=False):
        assert statement in (OUT/'sources'/file).read_text(), statement
        record=next(s for s in sources if s['path'].endswith('/'+file))
        folder=OUT/'inputs'/name;folder.mkdir(parents=True)
        values=dict(dict(initial='12',created='13',old_write='14',new_write='15',new_update='16',old_update='17'),**(values or {}))
        data=dict(id=name,table=table,key='id',old_column=column,new_column=column,
                  values=values,provenance={k:record[k] for k in ('repository','revision','path','sha256')})
        (folder/'input.json').write_text(json.dumps(data,indent=2)+'\n')
        (folder/'baseline.sql').write_text(baseline+'\n')
        (folder/'candidate.sql').write_text(statement+'\n')
        cases.append(dict(id=name,difficulty='Advanced' if hazard or state else 'Intermediate',
                          split='holdout',category='external_sql',source=dict(record,extracted_statement=statement),
                          expected_verdict=expected,oracle_sql=probe,oracle_state=state,
                          migration_state=migration_state,out_of_scope_hazard=hazard))

    narrow='alter table anothertab alter column atcol1 type integer;'
    basenarrow='CREATE TABLE anothertab(id int PRIMARY KEY,atcol1 bigint); INSERT INTO anothertab VALUES(1,12);'
    add('int32-in-range','alter_table.sql',narrow,basenarrow,'anothertab','atcol1','GO_WITHIN_SCOPE',
        "INSERT INTO anothertab VALUES(201,2147483647) RETURNING atcol1=2147483647")
    add('int32-overflow','alter_table.sql',narrow,basenarrow,'anothertab','atcol1','BLOCK',
        'INSERT INTO anothertab VALUES(201,2147483648)','22003',values={'old_write':'2147483648'})
    add('domain-new-write-constraint','domain.sql','alter domain con add constraint t check (VALUE < 34);',
        'CREATE DOMAIN con AS integer; CREATE TABLE domcontest(id int PRIMARY KEY,col1 con); INSERT INTO domcontest VALUES(1,12);',
        'domcontest','col1','BLOCK','INSERT INTO domcontest VALUES(201,42)','23514',values={'old_write':'42'})
    domain='CREATE DOMAIN things AS integer; CREATE TABLE thethings(id int PRIMARY KEY,stuff things); INSERT INTO thethings VALUES(1,55);'
    add('domain-not-valid','domain.sql','ALTER DOMAIN things ADD CONSTRAINT meow CHECK (VALUE < 11) NOT VALID;',
        domain,'thethings','stuff','BLOCK','INSERT INTO thethings VALUES(201,12)','23514',
        values={'initial':'55','created':'5','old_write':'12','new_write':'6','new_update':'7','old_update':'8'})
    add('domain-existing-invalid','domain.sql','ALTER DOMAIN things ADD CONSTRAINT meow CHECK (VALUE < 11);',
        domain,'thethings','stuff','INCONCLUSIVE',migration_state='23514',values={'initial':'55','created':'5'})
    add('required-default-removed','domain.sql','alter table defaulttest alter column col5 drop default;',
        "CREATE TABLE defaulttest(id int PRIMARY KEY,payload text,col5 integer NOT NULL DEFAULT 0); INSERT INTO defaulttest(id,payload) VALUES(1,'12');",
        'defaulttest','payload','BLOCK',"INSERT INTO defaulttest(id,payload) VALUES(201,'13')",'23502')
    generated='ALTER TABLE gtest25 ADD COLUMN b int GENERATED ALWAYS AS (a * 3) STORED;'
    basegenerated='CREATE TABLE gtest25(id int PRIMARY KEY,a integer); INSERT INTO gtest25 VALUES(1,12);'
    add('generated-column-safe','generated.sql',generated,basegenerated,'gtest25','a','GO_WITHIN_SCOPE',
        'INSERT INTO gtest25(id,a) VALUES(201,100) RETURNING b=300')
    add('generated-overflow','generated.sql',generated,basegenerated,'gtest25','a','BLOCK',
        'INSERT INTO gtest25(id,a) VALUES(201,1000000000)','22003',values={'old_write':'1000000000'})
    add('generated-expression-removed','generated.sql','ALTER TABLE gtest29 ALTER COLUMN b DROP EXPRESSION;',
        'CREATE TABLE gtest29(id int PRIMARY KEY,a integer,b integer GENERATED ALWAYS AS (a*2) STORED); INSERT INTO gtest29(id,a) VALUES(1,12);',
        'gtest29','a','GO_WITHIN_SCOPE','INSERT INTO gtest29(id,a) VALUES(201,10) RETURNING b IS NULL',hazard=True)
    change='alter table another\n  alter f1 type text using f2 || \' and \' || f3 || \' more\',\n  alter f2 type bigint using f1 * 10,\n  drop column f3;'
    add('multi-operation-data-change','alter_table.sql',change,
        "CREATE TABLE another(id int PRIMARY KEY,f1 integer,f2 text,f3 text); INSERT INTO another VALUES(1,1,'one','uno');",
        'another','f1','BLOCK',"SELECT f1='one and uno more' AND f2=10 FROM another WHERE id=1",values={'initial':'1'})
    add('lossy-using-expression','alter_table.sql','alter table atacc1 alter column test type integer using 0;',
        "CREATE TABLE atacc1(id int PRIMARY KEY,test text); INSERT INTO atacc1 VALUES(1,'12');",
        'atacc1','test','BLOCK','SELECT test=0 FROM atacc1 WHERE id=1')
    add('generated-not-null','generated.sql','ALTER TABLE gtest21b ALTER COLUMN b SET NOT NULL;',
        'CREATE TABLE gtest21b(id int PRIMARY KEY,a integer DEFAULT 2,b integer GENERATED ALWAYS AS (a*2) STORED,payload text); INSERT INTO gtest21b(id,payload) VALUES(1,\'12\');',
        'gtest21b','payload','GO_WITHIN_SCOPE','INSERT INTO gtest21b(id,payload) VALUES(201,\'x\') RETURNING b=4')
    hashes={str(p.relative_to(OUT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((OUT/'inputs').rglob('*')) if p.is_file()}
    runtime={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'acceptance').glob('*.py'))}
    frozen=dict(frozen_at=datetime.now(timezone.utc).isoformat(),sut_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                cases=cases,input_sha256=hashes,runtime_sha256=runtime,
                acceptance='Every confirmed reference must match the frozen verdict and exit; any mismatch fails this batch. No code tuning after this batch. Unresolved references are excluded and reported.',
                boundaries='New external statements/contexts; synthetic fixtures and HTTP mapping; one explicit unmapped generated-field hazard is not an in-scope false GO.')
    (OUT/'frozen.json').write_text(json.dumps(frozen,indent=2)+'\n')
    (OUT/'frozen.sha256').write_text(hashlib.sha256((OUT/'frozen.json').read_bytes()).hexdigest()+'\n')
    print('Frozen',len(cases),'new cases before execution; product runtime unchanged.')


if __name__=='__main__':
    main()
