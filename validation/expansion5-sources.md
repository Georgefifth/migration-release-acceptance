# Atlas SQL validation excerpts

The SQL statements in `freeze_expansion5.py` are attributed excerpts from
https://github.com/ariga/atlas/blob/ed994a77898e48377f9a9c391f2d1c49f5703b8d/sql/postgres/migrate_test.go
(Atlas, Ariga; Apache-2.0). Original license is retained in
`validation/licenses/ATLAS_LICENSE.txt`. Source file hash:
`b735c4f3c1b072dd28b86eb070e408cbd5f2e62ba037ce5187bcdc5c54cd949f`.

The evaluator adds synthetic schema/data, reviewed HTTP mapping, independent
PostgreSQL assertions and verdict expectations. Those adaptations are ours, not
Atlas application behavior. A formatter's expected string is not ground truth:
the server determines whether selected DDL is valid. Atlas's engine is not run.
Downloaded public files, full provenance and original license are also preserved
in the ignored local evidence bundle; they are not part of the runtime wheel.
