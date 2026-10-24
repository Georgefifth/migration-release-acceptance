# External SQL validation

This evaluator tests the public project CLI, not a hidden runner API. It uses
unchanged SQL excerpts from Squawk and PostgreSQL and one deliberately unsupported
pgroll YAML file. All schema baselines, data and HTTP mapping are evaluator-authored
synthetic fixtures. This is not evidence of independent business-app adoption.

The source manifest records immutable Git tree revisions, source URLs, download
times and SHA-256 hashes. Licenses are downloaded with source: PostgreSQL License,
MIT OR Apache-2.0 for Squawk, Apache-2.0 for pgroll. These public text files require
no account. Never execute arbitrary downloaded build scripts or test programs.

Reproduce in a fresh project checkout with Python 3.12, Docker and GNU time:

```sh
uv venv reports/validation-env --python /usr/bin/python3
uv pip install --python reports/validation-env/bin/python -r requirements.txt squawk-cli==2.70.0
python3 -m validation.fetch_sources
python3 -m validation.freeze_corpus
reports/validation-env/bin/python -m validation.run_corpus --split development --label development
# Inspect development evidence. Any fix must precede opening holdout results.
reports/validation-env/bin/python -m validation.run_corpus --split holdout --label holdout
```

The runner starts only its own named official PostgreSQL 16 container, limits it
to one CPU/512MiB/128 PIDs and binds its random port to 127.0.0.1. It removes that
container and its owned volumes in finally. SQL is trusted reviewed test text;
schema isolation alone is not a security sandbox. Do not use a production DSN.

Before execution, freeze_corpus writes 21 cases, expected verdicts, input hashes,
scoring criteria and a five-case holdout split. Expected labels and independent
SQL probes are outside the adapter's input directory. The product adapter reads
only input.json, baseline.sql and candidate.sql. An independent direct SQL oracle
uses another schema; it records only boolean results and SQLSTATEs.

Runs never overwrite an existing label. Preserve all initial failures. A fixed
development rerun is regression evidence, not independent validation. Open the
holdout once after fixing; do not tune to its failures. If the oracle does not
confirm a case, mark it unresolved instead of counting it as correct.

Machine-readable artifacts are in reports/real-world-validation/: frozen.json,
frozen.sha256, sources/downloads.json and runs/LABEL/{environment,results}.json.
Each case retains CLI logs, JSON/Markdown/HTML reports, GNU time wall/CPU/RSS and
Squawk output. The direct-SQL oracle and independent schema/PID checks are separate
from product-reported cleanup. Resource readings do not establish production scale.

Squawk sees the same SQL with the runner's session timeouts made explicit and
assume-in-transaction enabled. It provides static risk warnings, not runtime
application compatibility verdicts: warning counts are not comparable accuracy.
The 25,001-row case is synthetic scale testing over an external SQL statement,
not a real production dataset. Unicode and malformed inputs are labeled variations.

The 2026-10-24 baseline used product v0.1.4/psycopg 3.2.9. Development fixes add
22001/23503 application-error classification and update the driver for Python 3.14.
The original corpus draft was reviewed and corrected before any execution; both
the draft and amendment explanation are preserved in local evidence. No expected
verdict was changed. No post-result corpus editing is permitted.

## Second untouched batch

The next 12 cases keep the v0.1.5 product runtime unchanged. They add domain,
generated-column, default-removal, integer-range and multi-operation cases from
other PostgreSQL regression excerpts. Use a separate corpus directory:

```sh
python3 -m validation.fetch_sources --round2
python3 -m validation.freeze_round2
reports/validation-env/bin/python -m validation.run_corpus --split holdout --label untouched-round2 --corpus reports/real-world-validation-round2
python3 -m validation.summarize_round2
```

Source manifest: round2-sources.json. A repeat run requires a fresh --label and
does not replace first-run evidence. Round two confirmed all references, matched
9/12 verdicts and failed the same strict acceptance criterion. Two 22003 overflow
cases and one failed-create/dependent-read case remain INCONCLUSIVE instead of
BLOCK. One unmapped generated-field invariant also fails outside the declared
mapped workflow. No product fix followed these results; this is challenge-set
evidence, not another tuned regression run or an independent customer trial.
