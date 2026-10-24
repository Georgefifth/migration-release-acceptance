# Third-party components

No upstream application source is vendored. Original harness code is MIT.
The integration downloads a fixed public upstream revision into an ignored
working directory and retains its original license.

- PostgreSQL: PostgreSQL License; run as a separate disposable service.
  https://www.postgresql.org/about/licence/
- psycopg 3: LGPL-3.0; installed dependency, not relicensed or vendored.
  https://github.com/psycopg/psycopg
- Python: Python Software Foundation License.
  https://docs.python.org/3/license.html
- GitLab Duo Agent Platform: hosted service subject to GitLab terms.

The official hackathon rules permit OSI-approved third-party components subject
to license compatibility, while the FAQ uses broader MIT-only language. This
dependency choice needs organizer clarification before final submission; do not
claim that dependencies become MIT because the original project is MIT.

## Public upstream application integration

`fastapi/full-stack-fastapi-template`, commit
`b1125d8839482cb7bbae603ddc6d0081bf87532e`, MIT, copyright 2019
Sebastián Ramírez. Full license is preserved in `integrations/FASTAPI_LICENSE.txt`
and the downloaded source. Only the derived v2 copy changes ItemBase.title's
physical SQL column mapping; API routes and authentication remain upstream code.
The wrapper supplies isolated configuration, readiness, baseline seeding, and
sanitized SQLSTATE reporting. These changes are our integration code, not an
upstream feature or claim of an upstream defect. Dependencies retain their own
licenses and are installed from the upstream lockfile.

## External validation excerpts

The evaluator in validation/freeze_corpus.py includes attributed SQL test excerpts
from sbdchd/squawk (MIT OR Apache-2.0) and postgres/postgres (PostgreSQL License).
Their original license notices are retained in validation/licenses/. Exact source
URLs, immutable Git tree revisions and file hashes are in validation/sources.json.
The evaluator downloads pgroll examples (Apache-2.0) together with their license;
no pgroll implementation is vendored or executed. Downloaded full source files
remain in ignored reports/real-world-validation/sources/. Test baselines, data,
HTTP mapping and independent SQL probes are our evaluation adaptations, not
upstream application behavior or defects attributed to those projects.
