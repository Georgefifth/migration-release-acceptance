# Small-team validation session

Status: proposed protocol. No interviews or external installations have been
completed. Internal fixture tests cannot establish market demand.

## Who to involve
Five teams that use PostgreSQL with rolling application releases and can describe
a recent schema compatibility incident or an upcoming migration. Prefer the
engineer responsible for release checks. Do not ask for proprietary source code,
production records, credentials, or logs containing customer data.

## Before adding more product scope
Compare with the team's actual alternative: ordinary CI tests for old/new app
versions, its existing migration tool, a SQL linter such as Squawk, or a short
manual rehearsal. If an existing approach is adequate, record that outcome and
stop trying to replace it. Keep all evaluation on free existing infrastructure;
no service purchase is needed.

## Session (target 30–45 minutes, not a measured installation claim)
1. Ask about the last migration: who tested it, which versions overlapped, whether
   rollback was attempted, and what manual steps or failures occurred. Start with
   an actual event, not a request for opinions about this product.
2. Have the engineer show how they would test a synthetic equivalent with current
   tools. Record active setup time, steps, and behavior covered.
3. Let them run the reference example from the README without coaching. Record
   errors, help needed, and whether the report tells them what action to take.
4. Ask them to map one non-sensitive business operation to the adapter boundary.
   Record which fixtures, endpoints, startup steps, assertions, and CI changes
   would be needed. Do not call this a successful installation until it runs.
5. Compare the same migration with the baseline approach. Would they use the
   report for a real upcoming migration? What would they remove? What would make
   ordinary CI simpler? Ask permission separately before any follow-up message.

## Record one row per team

| Field | What to record |
|---|---|
| Context | Team size, PostgreSQL, release overlap, existing migration/CI tools |
| Recent event | Anonymized problem and actual consequences; no sensitive logs |
| Baseline | Active setup/review minutes, manual steps, covered behaviors |
| Harness | Active setup/review minutes, help events, configuration changes |
| Added evidence | A failure caught that the baseline missed, or no added coverage |
| Repeated need | Next real migration and whether the engineer wants to use it |
| Rejection | Reason the current tools or simpler checks are enough |

Do not invent values or treat a friendly reaction as adoption. Record unsuccessful
attempts and time spent fixing setup. Keep internal fixture runtime separate from
human installation/review time. Preserve only consented, anonymized observations.

## Continue or stop
Continue product expansion only if at least three of five teams want it for a
real upcoming migration and it adds useful coverage or meaningfully reduces
setup/review work relative to their baseline. These are prospective criteria.
Stop or narrow the idea if mapping business probes is as much work as ordinary CI,
if reports do not change a release decision, or if repeated use is unlikely.
No agent-generated confidence score substitutes for this evidence.
