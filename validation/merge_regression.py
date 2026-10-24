"""Copy every prior case unchanged into one clearly labeled regression batch."""
import hashlib
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/validation-expansion4/legacy39'


def main():
    if OUT.exists():raise SystemExit('Do not overwrite previous regression corpus')
    OUT.mkdir(parents=True)
    cases=[];parents=[];ids=set()
    for name in ('real-world-validation','real-world-validation-round2','optimization-validation'):
        parent=ROOT/'reports'/name;raw=(parent/'frozen.json').read_bytes();sha=hashlib.sha256(raw).hexdigest()
        assert sha==(parent/'frozen.sha256').read_text().strip()
        plan=json.loads(raw);parents.append(dict(corpus=name,sha256=sha))
        for case in plan['cases']:
            assert case['id'] not in ids;ids.add(case['id'])
            for file in (parent/'inputs'/case['id']).iterdir():
                key=str(file.relative_to(parent))
                assert hashlib.sha256(file.read_bytes()).hexdigest()==plan['input_sha256'][key]
            shutil.copytree(parent/'inputs'/case['id'],OUT/'inputs'/case['id'])
            cases.append(dict(case,split='development',original_split=case['split'],original_corpus=name))
    assert len(cases)==39
    frozen=dict(cases=cases,parents=parents,requires_least_privilege=True,
                boundary='All prior 39 contexts, unchanged bytes and labels. Split normalised only to run one regression loop; no case is a new holdout.',
                input_sha256={str(p.relative_to(OUT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((OUT/'inputs').rglob('*')) if p.is_file()})
    (OUT/'frozen.json').write_text(json.dumps(frozen,indent=2)+'\n');(OUT/'frozen.sha256').write_text(hashlib.sha256((OUT/'frozen.json').read_bytes()).hexdigest()+'\n')
    print('Copied all 39 prior contexts with unchanged input bytes and expected verdicts.')


if __name__=='__main__':main()
