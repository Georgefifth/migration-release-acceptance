# Record the verified release-acceptance demo

## Evidence to show
Base project URL:
https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43208246/showcase

| Scene | Verified evidence |
|---|---|
| Unsafe HTTP acceptance | MR !2, commit `aaa01d4880269f45129e7dcee85fc72b14111907`, job 17324276746 |
| Unsafe Duo explanation | MR !2 note 4052241066; completed session 9765659 |
| Compatible HTTP acceptance | MR !1, commit `8388d156b7878ccd1e61b0f69986d9c714890f1d`, job 17324294284 |
| Compatible Duo explanation | MR !1 note 4052261568; completed session 9765744 |

Direct links:
- [Unsafe job](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43208246/showcase/-/jobs/17324276746)
- [Unsafe Duo report](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43208246/showcase/-/merge_requests/2#note_4052241066)
- [Compatible job](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43208246/showcase/-/jobs/17324294284)
- [Compatible Duo report](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43208246/showcase/-/merge_requests/1#note_4052261568)

These are historical, commit-bound results. The newer application-factory
integration is not covered by them. If that integration is included in the
recording, first obtain and show its own terminal CI and Duo evidence.

## Recording order
1. Open the unsafe acceptance report. Show that migration and v2 checks pass,
   then focus on the old/mixed/rollback failures. Avoid scrolling through runner
   setup logs; the report is the useful evidence.
2. Show the actual unsafe Duo note, including the commit binding and BLOCK.
3. Open the compatible report. Show all sixteen checks and GO_WITHIN_SCOPE,
   including rollback_restart and rollback_new_data.
4. Show the compatible Duo note and its scope limits. Explain the difference
   between deterministic CI and the agent's explanation.
5. End with the practical validation question in the script. Keep interviews,
   adoption, installation savings, and production claims explicitly unvalidated.

## Local preparation already available
- `reports/expand.html` and `reports/breaking.html`: saved copies of the verified
  HTTP reports, identified by their embedded commit and run IDs.
- `reports/duo-http-block-finished.jpg` and `reports/duo-http-go-finished.jpg`:
  screenshots captured after the actual sessions finished.
- `reports/http-milestone-verification.md`: the verified milestone record.
- `reports/pending-integration-commit.json`: newer local changes awaiting remote
  reconciliation. Read remote head/files before retrying its create actions.

The video has not been recorded. The draft MRs have not been merged, and no
production deployment has been performed.
