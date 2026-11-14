# Validation report

Prepared 25 October 2026. These results describe the delivered files, not a deployed or production-verified integration.

## Executed successfully

| Check | Result | What it establishes |
|---|---|---|
| Altimate adapter, converter, freshness, skill installer and CLI tests | 39 passed | Fixture/mock behavior, conservative failures, actual prepare CLI wiring, hashes and stale-source rejection. |
| Guide checker tests | 18 passed | Metadata/reference structure, draft rejection, exact revision approval hashes and local review rules. |
| JavaScript syntax | All helper scripts passed `node --check` | Syntax only. |
| JSON/YAML/frontmatter audit | Passed | Config and metadata parse; skill names unique; agent modes and commands structurally consistent. |
| Permission scenario audit | Passed representative offline cases | Intended allow/ask/deny results for role/tool names, ownership, dbt and Altimate-agent prohibitions. Not OpenCode runtime enforcement. |
| Four new/modified skill validators | Passed | Frontmatter/naming conventions for the two portable skills and two updated Fido skills. |
| Local seed Guide structure | Passed with draft warning | Seed is a structurally valid draft, not a verified warehouse description. |
| Seed `--publish-ready` check | Rejected as intended, exit 1 | Unverified/unapproved seed cannot pass the local publication checklist. |
| Original-file preservation | All 57 original files retained | No supplied file was silently removed; changes are in the accompanying patch. |

Total dependency-free automated tests: **57 passed; 0 failed**. The two end-to-end CLI tests use synthetic manifest/catalog/source files and do not call dbt or the native engine.

## Not verified

- **Native engine:** no `@altimateai/altimate-core` package/native binary was installed. The self-test returned an inconclusive setup error (exit 2) for the missing module. No claim is made that the native response shapes, DuckDB types, qualified identifiers or actual lineage mappings work in your environment. Install the pinned dependency and run the native self-test plus a manually checked real model.
- **Upstream skill installation:** the installer was tested with a synthetic local Git repository. The actual upstream pack is not included and must be downloaded, reviewed and installed by you. No current upstream content is implicitly approved.
- **OpenCode:** configuration was inspected against documented V1 conventions and statically audited, not launched in an installed OpenCode process or checked against its complete runtime schema. Check your installed version and test actual tool names, approvals and edit boundaries. V2 needs a deliberate migration.
- **MotherDuck:** no account data or Guide bodies were read and no remote mutations were executed. Actual tool availability, credentials, ownership/visibility and version/update behavior need live acceptance testing. The connected client must expose the required Guide mutation tools; missing tools are not permission to bypass them.
- **dbt/warehouse correctness:** no dbt command, warehouse query, deployment, model build, row reconciliation or production verification ran. Static lineage is not proof of business equivalence.
- **Performance:** no WSL/OpenCode opening-time or MCP startup measurement was taken.

## Reproduce the local checks

From the merged repository root, Node 22+ is sufficient for these dependency-free checks:

```bash
node --test tools/altimate/test/*.test.mjs
node --test tools/guides/test/*.test.mjs
node tools/guides/check.mjs

# Expected to fail for the supplied unverified draft; do not weaken the gate.
node tools/guides/check.mjs --guide fido-warehouse-orientation --publish-ready
```

After installing the native dependency, run `node tools/altimate/analyze.mjs self-test` and the real-model acceptance workflow in `docs/setup-altimate.md`.

## Security and enforcement boundaries

OpenCode permissions are not an OS sandbox. Shell aliases, arbitrary Python, third-party scripts and alternative credentials cannot all be controlled by a command-name pattern. Inspect approval requests and retain least-privilege database roles. Do not use persistent blanket approval for Guide publication.

The Guide checker validates local structure and revision hashes. It cannot establish that a claimed user approval really happened, that evidence is true, that code was deployed, or that the remote Guide stayed unchanged between read and write. Those remain explicit workflow checks. MotherDuck metadata may change without incrementing the content version, so compare metadata as well as UUID/version/body and read back after mutation.

Artifact freshness checks are conservative local checks, not a signed build-provenance system. Verify target, variables, external macros, dependencies, actual deployed schema and artifact producer separately.
