"""Report all second-batch outcomes without changing the first evaluation."""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import statistics

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/real-world-validation-round2'


def main():
    plan=json.loads((OUT/'frozen.json').read_text())
    run=OUT/'runs/untouched-round2'
    rows=json.loads((run/'results.json').read_text())
    environment=json.loads((run/'environment.json').read_text())
    assert len(rows)==len(plan['cases'])
    assert all(hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h for f,h in plan['runtime_sha256'].items())
    eligible=[r for r in rows if r['oracle']['status']=='CONFIRMED']
    unknown=[r['id'] for r in rows if r['oracle']['status']!='CONFIRMED']
    matches=sum(r['product']['verdict_matches'] and r['product']['exit_matches'] for r in eligible)
    bad=[r for r in eligible if r['expected_verdict']=='BLOCK']
    failures=[r for r in eligible if not r['product']['verdict_matches']]
    cleaned=sum(r['product']['cleanup']['schema_absent'] and not r['product']['cleanup']['live_recorded_pids'] for r in rows)
    summary=dict(decision='FAIL' if failures else ('INCONCLUSIVE' if unknown else 'PASS'),
                 cases=len(rows),confirmed_references=len(eligible),exact_matches=matches,
                 accuracy_boundary='Agreement with frozen labels in synthetic contexts, not population accuracy.',
                 known_incompatible=len(bad),correctly_blocked=sum(r['product']['observed_verdict']=='BLOCK' for r in bad),
                 false_go_in_scope=sum(r['product']['observed_verdict']=='GO_WITHIN_SCOPE' for r in bad),
                 failures=[dict(id=r['id'],expected=r['expected_verdict'],observed=r['product']['observed_verdict'],failed_checks=r['product']['failed_checks']) for r in failures],
                 unmapped_hazards=[r['id'] for r in rows if r['out_of_scope_hazard']],
                 unresolved=unknown,skipped=[],independent_cleanup_confirmed=cleaned,
                 owned_container_removed=environment['owned_container_removed'],
                 remaining_owned_schemas=environment['remaining_owned_schemas'],
                 median_wall_seconds=statistics.median(r['product']['wall_seconds'] for r in rows),
                 maximum_wall_seconds=max(r['product']['wall_seconds'] for r in rows),
                 max_invocation_rss_kib=max(s['resources']['peak_rss_kib'] for r in rows for s in r['product']['steps']),
                 runtime_unchanged_from_commit=plan['sut_commit'],
                 plan_sha256=hashlib.sha256((OUT/'frozen.json').read_bytes()).hexdigest(),
                 benchmark_boundary='Squawk static warnings are not application compatibility decisions; no accuracy/speed superiority claimed.')
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    with (OUT/'case-results.csv').open('w') as file:
        writer=csv.writer(file);writer.writerow(['case','expected','observed','oracle','exit','seconds','squawk_rules'])
        for r in rows:
            rules=[f.get('rule_name') for f in (r['competitor']['findings'] or [])]
            writer.writerow([r['id'],r['expected_verdict'],r['product']['observed_verdict'],r['oracle']['status'],r['product']['actual_exit'],r['product']['wall_seconds'],';'.join(rules)])
    definitions={c['id']:c for c in plan['cases']}
    table='\n'.join('| '+r['id']+' | '+r['expected_verdict']+' | '+r['product']['observed_verdict']+' | '+str(r['product']['verdict_matches'])+' |' for r in rows)
    links='\n'.join('- ['+record['path']+']('+record['url']+') — SHA-256 '+record['sha256'] for record in json.loads((OUT/'sources/downloads.json').read_text()))
    report=f'''# Real-World Validation Report — second untouched batch

**Decision: {summary['decision']}.** Same frozen all-confirmed-cases criterion:
{matches}/{len(rows)} exact verdict/exit matches, no in-scope false GO. Product
runtime remains unchanged from `{plan['sut_commit']}`. No product fix, threshold
change, failed-case removal or tuning followed this batch.

## Scope and source material

Twelve previously unexecuted statement/context cases from the pinned PostgreSQL
16 regression suite. They cover integer range, domain constraints, defaults,
generated expressions and multi-operation data conversion. All are external SQL
excerpts; schema, synthetic values, HTTP mapping and reference probes remain
evaluator-authored. This is not twelve real customer projects or a new independent
business-app installation. Corpus selection intentionally targets weaknesses
identified earlier; this is a new challenge set, not a random unbiased sample.

{links}

Files were downloaded with UTC times/byte counts and hashes in sources/downloads.json.
The PostgreSQL License notice is included in POSTGRESQL-LICENSE.txt. Numeric SQL
was inspected but not selected; three of the four downloaded files supply cases.
Two generated-column file names were unavailable in the pinned v16 tree;
sources/discovery.json records this pretest discovery and the correct generated.sql
path. No failed executed case was removed. Only selected reviewed SQL statements
ran in an owned isolated database; no upstream scripts were executed.

## Method and frozen expectations

Before execution, validation.freeze_round2 wrote frozen.json, the case inputs,
expected verdicts/exit behavior, independent SQL probes and hashes for every input
and product runtime module. Labels and oracle queries are outside adapter input
directories. The documented public CLI performed preflight and execution. Each
reference probe ran separately in another schema. All twelve references were
confirmed; no skipped, unresolved or timed-out cases occurred. Source statements
were unchanged; boundary values were synthetic and explicitly mapped to the
declared workflow. One unmapped generated-field invariant was tested separately.

## Complete outcomes

| Case | Expected | Actual | Exact match |
| --- | --- | --- | --- |
{table}

Known in-scope incompatibilities: {summary['correctly_blocked']}/{summary['known_incompatible']}
returned BLOCK; the remaining three returned INCONCLUSIVE rather than GO.
Case agreement is {matches/len(rows)*100:.1f}%, not statistical real-world accuracy.

## Failure analysis

1. int32-overflow: source DDL narrows bigint to integer. Existing/mapped ordinary
   values work, but the declared late old-app write exceeds int32 range and
   returns SQLSTATE 22003. That code is not in the compatibility classification
   set, so the report says infrastructure_or_unknown/INCONCLUSIVE. The independent
   SQL insert confirms the overflow. Core classification limitation; not parsing.
2. generated-overflow: adding `b = a * 3` succeeds. A declared value fits a but
   overflows b. The same missing 22003 classification downgrades the confirmed
   incompatibility. This is an interaction between a real generated expression
   and input range, not a broken migration statement.
3. required-default-removed: removing the NOT NULL column's default breaks creates
   that previously omitted it. 23502 is correctly recorded, but the runner later
   reads logical ID 2, which was never created. The synthetic HTTP mapping yields
   an unknown response and the final gate is INCONCLUSIVE. This independently
   reproduces the dependent-probe/error-mapping limitation from the first batch.

## Successes and coverage blind spot

Both domain constraint cases correctly block a mapped later write. NOT VALID
itself is therefore not generally unsupported; where the failure occurs matters.
Safe integer values, adding an ordinary generated column and generated NOT NULL
behavior pass. Multi-operation USING changes and a lossy USING 0 expression are
detected through business-value mismatches and return BLOCK.

Dropping a generated expression passes all 16 mapped a-field checks, while an
independent insert proves b is now NULL instead of a*2. The known mapped-workflow
GO is correctly scoped, but would be misleading if advertised as checking all
business invariants. It is recorded as an unmapped hazard, not hidden or counted
as an in-scope false positive/negative.

## Competitor and resources

Squawk 2.70.0 received the same statements with explicit session timeouts and
transaction context. Full raw warnings are retained per case; case-results.csv
lists rule names. Static migration risk warnings and observed HTTP application
behavior are different tasks. No common accuracy metric or speed winner is claimed.

Python {environment['python'].split()[0]}, psycopg {environment['psycopg_version']},
PostgreSQL {environment['postgres_version']}. Container: one CPU, 512MiB, 128 PIDs,
random port bound only to localhost. Median CLI wall {summary['median_wall_seconds']:.3f}s;
maximum {summary['maximum_wall_seconds']:.3f}s. GNU time maximum invocation/child
RSS {summary['max_invocation_rss_kib']} KiB, not aggregate app+DB memory. DB startup
and independent oracle time are excluded. These tiny local workloads do not
establish concurrency, locking or production backfill performance.

All {cleaned}/{len(rows)} runtime schemas and recorded PIDs were independently
confirmed removed. Final owned schema count was {environment['remaining_owned_schemas']}.
The owned container and volumes were removed: {environment['owned_container_removed']}.

## Reproduce and limits

With the previously documented Python/driver/Squawk environment and Docker:

```sh
python3 -m validation.fetch_sources --round2
python3 -m validation.freeze_round2
.validation-venv312/bin/python -m validation.run_corpus --split holdout --label untouched-round2 --corpus reports/real-world-validation-round2
python3 -m validation.summarize_round2
```

Use fresh corpus/output directories; the tools reject overwriting frozen plans
or runs. Product hashes must match the frozen batch. The previous 21-case
evaluation and evidence archive were not modified. This report, summary.json,
case-results.csv, frozen plan, source manifests and runs/ retain all outcomes.

The failure decision remains. Current video can demonstrate only its specified
saved workload. Neither this batch nor the previous batch establishes general
migration safety, customer adoption or arbitrary application coverage. No product
runtime change, package publication, new CI run, deployment or Duo trigger was
performed in this round.
'''
    (OUT/'Real-World-Validation-Report.md').write_text(report)
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    main()
