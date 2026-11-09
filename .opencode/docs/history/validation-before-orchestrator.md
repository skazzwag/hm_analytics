# Validation: Guide README, root analysis and dev-only execution update

## Executed offline checks
| Check | Result | Scope |
|---|---|---|
| Python runner tests | 31 passed | Disabled/unverified policy, destination/attachment checks, fixed args, explicit dev token, environment filtering, mock executable, session/source binding, redaction and path safeguards |
| Configuration tests | 18 passed | Role ownership, planner separation, permissions/skill routing, Guide CI-only rules and active path consistency |
| Notebook AST/template tests | 29 passed | Retained static notebook safeguards after root-path migration |
| Altimate adapter/freshness/installer tests | 39 passed | Dependency-free tests; installer adaptation updated to new policy |

Total: **117 tests passed**, plus 8 pytest subtests reported. No real dbt or warehouse process ran. Mock runner tests use a temporary synthetic executable, not dbt.

Additional checks: default CLI returns BLOCKED/exit 2 without policy; Python sources parse; JSON/YAML/frontmatter parse; user-supplied README is retained byte-for-byte. Updated skills are validated and packaged. Final packaging checks and counts appear below.

The former 18 generic Guide-validator tests were retired with the incompatible provisional layout/checker. They are not counted as current tests. Your actual make guides-validate/validate.sh/sync.sh implementation was not supplied and has not been tested or replaced.

## Not established here
- Live MotherDuck identity, grants, source shares, production credential absence, token/cache behavior or Guide operations. Only the documentation Q&A connector was used; no organization metadata/data queries were performed.
- Actual dbt/Core/adapter command compatibility, project macros/hooks, custom target/schema/database routing, dependency environment, dev execution or CI deployment. The wrapper is an opt-in accident guardrail, not a sandbox or permission proof.
- Real installed OpenCode permission merging/enforcement, tool-name matches, stock/custom Plan behavior or runtime latency.
- Native Altimate package compatibility, real column lineage, marimo rendering/browser interactions or actual pipeline DQ assertions. This update changes configuration/workflow and helpers, not your unavailable production project.
- PR code beyond the provided README: metadata JSON schema, Makefile, validate.sh, sync.sh, workflow, UUID write-back and deletion reconciliation all still require repository inspection.

## Local acceptance before enabling execution
Follow docs/setup-dbt-safety.md. Have the user/admin verify identity/permissions, remove all accessible production capabilities, restart processes and inspect hooks/macros. Review dry-run output; test a small known dev model before broader builds/reviewer execution. Keep the policy disabled until those steps are complete. Treat a new token for the prod identity as prod, not development.

Apply the migration/removal instructions rather than blindly copying over real files. The patch is against the prior generated archive, not against the inaccessible live repository. Do not overwrite your canonical Guide content/scripts or actual project README/Makefile/CI unreviewed.

## Packaging checks
- Baseline: 113 files. Updated: 122 files. Added: 23. Modified: 51. Removed: 14.
- 13 updated skills pass the skill validator and package as skill.zip.
- Patch applied to a clean copy of the preceding archive and reconstructed the updated tree byte-for-byte.
- ZIP integrity passed; no caches, installed native dependencies, database files or credentials are bundled.
