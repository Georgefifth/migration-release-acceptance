"""Summarize preserved baseline, regression and untouched holdout evidence."""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import statistics

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/real-world-validation'


def main():
    plan=json.loads((OUT/'frozen.json').read_text())
    definitions={c['id']:c for c in plan['cases']}
    labels=['baseline-development','corrected-development','final-holdout']
    runs={label:json.loads((OUT/'runs'/label/'results.json').read_text()) for label in labels}
    final=runs['corrected-development']+runs['final-holdout']
    environments={label:json.loads((OUT/'runs'/label/'environment.json').read_text()) for label in labels}
    def score(rows):
        eligible=[r for r in rows if r['oracle']['status']!='UNRESOLVED']
        blocks=[r for r in eligible if r['expected_verdict']=='BLOCK']
        safe=[r for r in eligible if r['expected_verdict']=='GO_WITHIN_SCOPE']
        runtime=[r for r in rows if r['product']['cleanup'] is not None]
        return dict(cases=len(rows),reference_confirmed=sum(r['oracle']['status']=='CONFIRMED' for r in rows),
                    configuration_only=sum(r['oracle']['status']=='NOT_APPLICABLE' for r in rows),
                    unresolved=sum(r['oracle']['status']=='UNRESOLVED' for r in rows),
                    exact_verdict_and_exit_matches=sum(r['product']['verdict_matches'] and r['product']['exit_matches'] for r in eligible),
                    exact_denominator=len(eligible),known_incompatible=len(blocks),
                    correctly_classified_block=sum(r['product']['observed_verdict']=='BLOCK' for r in blocks),
                    false_go_in_scope=sum(r['product']['observed_verdict']=='GO_WITHIN_SCOPE' for r in blocks),
                    false_block_on_declared_compatible=sum(r['product']['observed_verdict']=='BLOCK' for r in safe),
                    independent_runtime_cleanup_confirmed=sum(r['product']['cleanup']['schema_absent'] and not r['product']['cleanup']['live_recorded_pids'] for r in runtime),
                    runtime_cleanup_denominator=len(runtime),
                    median_wall_seconds=statistics.median(r['product']['wall_seconds'] for r in rows),
                    max_wall_seconds=max(r['product']['wall_seconds'] for r in rows),
                    max_reported_rss_kib=max(step['resources'].get('peak_rss_kib',0) for r in rows for step in r['product']['steps']))
    scores={label:score(rows) for label,rows in runs.items()}
    summary=dict(decision='FAIL',criterion='Frozen exact classification requires every eligible case to match; two final cases do not.',
                 capability_assessment='Partial scoped capability; broad independent application integration remains unproven.',
                 plan_sha256=hashlib.sha256((OUT/'frozen.json').read_bytes()).hexdigest(),
                 scores=scores,final=score(final),
                 difficulty=dict(Counter(c['difficulty'] for c in plan['cases'])),
                 categories=dict(Counter(c['category'] for c in plan['cases'])),
                 final_failures=[r['id'] for r in final if not r['product']['verdict_matches']],
                 skipped_cases=[],unresolved_cases=[],
                 upstream_business_application_integrations_in_this_corpus=0,
                 out_of_scope_hazards=sum(r['out_of_scope_hazard'] for r in final),
                 all_owned_containers_removed=all(e['owned_container_removed'] for e in environments.values()),
                 all_final_remaining_owned_schema_counts_zero=all(e['remaining_owned_schemas']==0 for e in environments.values()),
                 installed_python314_wheel_exit=environments['final-holdout']['installed_wheel_exit'],
                 limits=['Developer-authored mappings and expectations; direct SQL oracle confirms specific semantics, not every real application behavior.',
                         'Small purposive corpus, repeated source statements, five-case holdout; no population accuracy claim.',
                         'Development and holdout use different Python versions; not a controlled speed comparison.',
                         'GNU time RSS is invocation/child maximum, not aggregate app+database peak memory.',
                         'Squawk static warning counts cannot be treated as runtime compatibility verdicts.'])
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    rows=[]
    for label,data in runs.items():
        for r in data:
            d=definitions[r['id']]
            rows.append(dict(run=label,id=r['id'],split=d['split'],difficulty=d['difficulty'],category=d['category'],
                             expected=r['expected_verdict'],observed=r['product']['observed_verdict'],
                             exit=r['product']['actual_exit'],match=r['product']['verdict_matches'],
                             oracle=r['oracle']['status'],wall_seconds=r['product']['wall_seconds'],
                             source_url=d['source']['url']))
    with (OUT/'case-results.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    table='\n'.join('| '+r['id']+' | '+definitions[r['id']]['split']+' | '+r['expected_verdict']+' | '+r['product']['observed_verdict']+' | '+r['oracle']['status']+' |' for r in final)
    sources='\n'.join('- ['+name+']('+next(x['url'] for x in json.loads((OUT/'sources/downloads.json').read_text()) if x['repository'].endswith('/'+name) and x['path'].endswith(suffix))+')'
                      for name,suffix in [('postgres','sql/alter_table.sql'),('postgres','expected/alter_table.out'),('squawk','renaming_column.rs'),('squawk','ban_drop_column.rs'),('squawk','changing_column_type.rs'),('squawk','disallow_unique_constraint.rs'),('pgroll','18_change_column_type.yaml')])
    report=f'''# Real-World Validation Report — 2026-10-24

**Final decision: FAIL against the frozen exact-classification criterion.**
The tool has partial scoped capability and failed conservatively in the two
remaining incompatible cases. No in-scope false GO was observed. General real-team
integration and broad production safety remain unproven.

## 1. Product and target

The product rehearses a reviewed PostgreSQL migration against one normalized
string CRUD workflow exposed by two independent HTTP app processes. It records
16 baseline/migration/old/new/mixed/rollback probes, lifecycle identities and
cleanup. Trusted Python Integration configuration, UTF-8 baseline/candidate SQL
and adapter methods are required inputs. Outputs are JSON, Markdown, HTML and
exit codes 0=GO_WITHIN_SCOPE, 1=BLOCK, 2=INCONCLUSIVE/setup failure. Static Pages
cannot execute these tests. There is no repository ingestion, arbitrary journey
discovery, migration generator or production deployment capability.

Existing 53 unit tests and the previous pinned FastAPI Item integration did not
establish broad real-world correctness. This evaluation targets external DDL,
classification, malformed input, data boundaries, cleanup, integration scope and
installation rather than visual polish.

## 2. Sources, permission and reference answers

{sources}

All 17 downloaded source/license files are listed with URL, immutable Git tree
revision, UTC download time, byte length and SHA-256 in
[sources/downloads.json](sources/downloads.json). PostgreSQL uses the PostgreSQL
License; Squawk MIT OR Apache-2.0; pgroll Apache-2.0. Original licenses are saved.
Public read access requires no account; no private code or data was obtained.
Only reviewed extracted SQL was executed in an owned disposable database. No
downloaded Python/Rust/Go programs or unknown installation scripts were executed.

These are real maintained-project SQL regression excerpts, **not actual customer
workloads or an industry application benchmark**. Baselines, data, HTTP mapping
and boundary variations are synthetic and labeled. PostgreSQL expected output
and upstream assertions provide reference context; separate direct-SQL probes in
another schema confirm specific errors/boolean outcomes. They do not provide
ground truth for every possible application behavior. Expected product labels
were authored and frozen before execution, independently of product output.

## 3. Corpus and scoring

21 cases: {json.dumps(summary['categories'])}. Difficulty:
{json.dumps(summary['difficulty'])}. Sixteen development cases and five holdout
cases were frozen with input hashes and acceptance rules before execution.
A preexecution review corrected three fixture placements without changing labels;
the original draft and explanation remain preserved. No executed failure was
deleted or relabeled. The holdout was opened once after fixes were locked.

The criterion requires every eligible expected verdict and exit code to match.
INCONCLUSIVE is safe non-approval but does not count as identifying a known
incompatibility. Broad application-integration claims additionally require at
least two independent upstream business applications; this SQL corpus tests zero.

19 cases have confirmed direct-SQL references; two are configuration-only format
rejections. No case was skipped, timed out or left unresolved. These references
are evaluator-confirmed facts in adapted contexts, not population annotations.

## 4. Environment and reproduction

Baseline: Python 3.12.3, psycopg 3.2.9, product v0.1.4 source f556ecdd.
Corrected development: Python 3.12.3, psycopg 3.3.6, working-source hashes recorded.
Holdout and installed wheel: Python 3.14.6, psycopg 3.3.6, local v0.1.5.
All used PostgreSQL 16.15 from the same cached official image, one CPU, 512MiB and
128 PIDs. Each run owned a separate container bound only to 127.0.0.1. Environment
files record image identity, code hashes and teardown; no DSN/password is logged.

See [validation/README.md](../../validation/README.md) in the source checkout for
fetch, freeze and run commands. Product execution uses the documented public
`python -m acceptance.project` CLI with preflight, reviewed configuration and
candidate, not an internal function shortcut. Each case retains stdout/stderr,
reports and GNU time data. Labels/oracle SQL stay outside the adapter input files.
The installed-wheel contract additionally uses actual console scripts from a
fresh virtualenv and a separate generated project without source PYTHONPATH.

## 5. Results

| Run | Exact verdict/exit matches | Meaning |
| --- | --- | --- |
| Original development | 13/16 | Initial failures preserved |
| Corrected development | 15/16 | Regression evidence, not independent validation |
| Untouched holdout | 4/5 | First run after fixing; no tuning afterwards |
| Corrected development + holdout | 19/21 (90.5%) | Overall case agreement, not population accuracy |

External-SQL-only agreement is 14/16 (87.5%). Four additional cases are malformed
or adversarial evaluator mutations; one is deliberately unsupported pgroll YAML.
Known in-scope incompatibilities classified BLOCK: 5/7 (71.4%, including the
comment mutation). The other two returned INCONCLUSIVE. False GO among these seven:
0/7. False BLOCK among declared compatible cases: 0. One independent unmapped
operation did fail while the mapped workload returned GO; that blind spot is not
hidden in the in-scope metric.

| Case | Split | Expected | Observed after correction | Reference |
| --- | --- | --- | --- | --- |
{table}

All 19 final runtime cases had independently confirmed absent schemas and no
live recorded application PIDs. All three corpus containers and owned volumes
were removed; final namespace queries found zero owned schemas. The installed
Python 3.14 wheel contract exited 0, including compatible/blocked runs, unavailable
DB handling and five exact rollback-value cases. All 53 unit tests passed on
both Python 3.12 and 3.14.

## 6. Representative successes and failures

- Real Squawk rename/drop SQL produced BLOCK with 42703. Explicit transaction
  wrappers, safe type casts, varchar widening on a partitioned table and Unicode
  character length behaved as expected. A 25,001-row synthetic baseline accepted
  the external NOT VALID operation when all mapped future writes satisfied it.
- `varchar-long-write`: old-to-new create encountered 22001. Initially this was
  labeled infrastructure_or_unknown/INCONCLUSIVE. The correction classifies that
  application-request rejection as compatibility/BLOCK; baseline result retained.
- `foreign-key-future-writes`: independently confirmed 23503 was similarly
  misclassified. It now returns BLOCK without changing the SQL or test labels.
- `not-valid-future-writes`: new/old creates fail known CHECK constraints, then
  rollback reads an ID that was never created. Our HTTP mapping turns missing
  row into an unclassified application response; the strict gate gives
  INCONCLUSIVE. This combines adapter error-mapping limitations and the runner's
  unconditional dependent probe. It is conservative but fails the expected
  diagnostic task. Do not convert arbitrary HTTP errors to BLOCK to hide it.
- Holdout `unique-mapped-write` independently reproduced that same downstream
  missing-record path after known unique violations. It remains a failed holdout;
  code was not adjusted after seeing it.
- `unmapped-operation-blindspot`: mapped payload CRUD passes 16/16, yet an
  independent write to an unmapped unique field fails with 23505. The declared
  GO is technically scoped; it cannot substantiate application-wide safety.
- Empty/non-UTF-8 fixtures are rejected at preflight. Malformed SQL, pgroll YAML,
  incompatible conversions and dependent composite types fail safely at runtime.
  Nonempty YAML is accepted by file preflight; preflight is not SQL validation.
- A misleading SQL comment did not change the BLOCK verdict. This deterministic
  CLI case is not a prompt-injection security audit of GitLab Duo.

## 7. Installation finding and fixes

Original psycopg[binary]==3.2.9 installation on Python 3.14.6 failed: no cp314
wheel, despite the package declaring Python >=3.12. The driver pin is now 3.3.6,
and a fresh noneditable v0.1.5 wheel installed and ran on Python 3.14. Official
[release notes](https://www.psycopg.org/psycopg3/docs/news.html) document newer
Python support. [PostgreSQL's error-code reference](https://www.postgresql.org/docs/16/errcodes-appendix.html)
supports the two added application-error classifications (22001 and 23503).
Lifecycle, unknown-error and cleanup guards remain unchanged. Distribution
verification now accepts a fresh output directory to preserve old evidence.

## 8. Competitor benchmark

Squawk CLI 2.70.0 ran on the same candidate SQL. Session lock/statement timeouts
were made explicit to match the product; assume-in-transaction was enabled;
parent config was ignored. Per-case raw JSON warnings and wall time are saved.
Rename/drop risks were flagged without a database. Squawk warned about type changes
on compatible short-value/widening cases and flagged the unmapped UNIQUE risk.
It emitted no warnings for the NOT VALID CHECK case that rejected mapped writes.

These are different tasks. Squawk identifies potential static migration risks;
the product observes selected application behavior with a database and processes.
Its valid lock/type warnings are not false positives merely because the tiny
CRUD workload passed. Conversely warning-free SQL is not an application safety
guarantee. No comparable accuracy winner or speed ratio is justified. Atlas and
pgroll were not executed as engines; their performance is unmeasured.

## 9. Performance and recovery

Corrected+holdout product median wall time: {summary['final']['median_wall_seconds']:.3f}s;
maximum {summary['final']['max_wall_seconds']:.3f}s, including preflight/runtime
command launch and excluding independent oracle and DB container startup. Maximum
GNU time RSS: {summary['final']['max_reported_rss_kib']} KiB. CPU values and each
step's wall/RSS are retained in JSON. RSS is an invocation/child maximum, not
aggregate app+DB memory; end-of-run docker stats are not peak memory. The 25,001-row
case does not establish large-backfill or concurrent behavior. Different Python
versions and developer-network conditions prevent controlled speed claims.

## 10. Demo and product-claim decision

Existing video may demonstrate the exact saved Item examples, failure filtering,
comparison and evidence inspection. It must not imply automatic project ingestion,
arbitrary app correctness, comprehensive constraint coverage, production approval,
or independent customer validation. These tests do not retroactively turn its
selected examples into representative success-rate evidence.

**Do not describe the current product as generally validated migration acceptance.**
The frozen classification criterion failed. Next engineering work should preserve
known failure causes while treating dependent missing-record probes explicitly,
then use a new untouched external set. Next product validation needs independent
business-app integrations and developer setup measurements. More UI polish or
another polished happy-path video would not resolve these gaps.

## 11. Artifacts and publication state

[Machine summary](summary.json), [all case results](case-results.csv),
[frozen plan](frozen.json), [holdout lock](holdout-lock.json), and each
`runs/LABEL/results.json` preserve successes and failures. Original and corrected
runs are separate directories. No failure was overwritten. The preexecution draft
and amendment note remain available. Raw case HTML/JSON/Markdown and logs are
inside their run directories.

v0.1.5 fixes and this evaluator are local work in codex/real-world-validation.
The public Pages/GitHub demo still represents the prior published v0.1.4 interface;
these local results are not claimed as a new GitLab CI run, deployment or Duo review.
No video was uploaded and no merge, production operation or package publication
was performed.
'''
    (OUT/'Real-World-Validation-Report.md').write_text(report)
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    main()
