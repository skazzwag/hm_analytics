# Changes — complete Dagster expert bundle (2026-11-01)

- Added the user-uploaded **complete** Dagster `dagster-expert` skill and **173** supporting reference files to `.opencode/skills/dagster-expert/`; included its Apache-2.0 license, excluded Windows `Zone.Identifier` sidecars and verified its entrypoint against the pinned upstream Git blob.
- Preserved the seven bundled Altimate dbt workflows and full marimo-pair, the `dagster-fido-dagster` project skill, the Product Owner agent and the sole MotherDuck MCP.
- Added CLI-only project overrides to the upstream Dagster skill's MCP guidance and central API/launch references; runtime approvals, dev-only dbt execution and pipeline state isolation still apply.
- Updated provenance, agent instructions, docs and tests. The installer now reports all nine official skills as bundled and is retained for future reviewed updates only.

## 2026-11-01 — Bundle user-provided vendor skills

- Integrated seven Altimate dbt workflows and complete marimo-pair (`SKILL.md`, scripts, references) directly from `.agents.zip` into tool-prefixed `.opencode/skills/`.
- Excluded flagged `dbt-model-enhancement`. Refused deprecated Dagster notice-only stub; official Dagster remains an explicit one-skill installation.
- Applied approved development dbt policy to every Altimate skill and added authenticated localhost-only checks to marimo code execution.
- Kept MotherDuck as sole MCP, project-specific analyst/Dagster skills, and Guide CI-only publishing.
- Added provenance with source SHA-256 checksums and documented the missing Dagster skill.

# Changes — official specialist skills integration (November 2026)

- Removed the original custom `dbt-fido-model` skill and its agent references. Kept all Fido dbt naming, layers, macros, tests and deployment conventions in `.opencode/rules/dbt-standards.md`. Retained `transformation-quality`.
- Added a **pinned, source-verified, one-command installer** for seven complete Altimate dbt skills (tool-prefixed), complete `marimo-pair` and complete active Dagster `dagster-expert` (not the deprecated stub). The packaging environment cannot fetch external Git content, so the nine official vendor trees are installed on the user's WSL machine with `python tools/skills/install_official.py --apply --only dagster`; they are **not in this ZIP until that step runs**.
- Aligned analytics-engineer, data-engineer, data-analyst, product-owner, notebook/new-model commands and repository rules with correct new skill IDs and execution boundaries.
- Preserved single MotherDuck MCP, ignored `analysis/`, dbt dev-identity runner, Git/CI-only Guides and all seven agent roles.
- Replaced the obsolete Altimate-only skill installer with central pinned vendor provisioning, license retention, provenance and offline tests.

---

# Current update: tool-prefixed skill IDs and explicit tool headers

- Renamed 28 bundled `.opencode/skills/` directories to `tool-skill` (kebab-case), including YAML `name` and tool-first `description`, plus visible Primary tool headers.
- Updated all agent allowlists, commands, cross-skill references, Altimate installer policy text and tests to use the renamed IDs. Preserved the contents, files and commands of the original skills.
- Added `docs/skill-catalog.md`, `docs/skill-migration.md`, a read-only inventory script, safe dry-run rename helper and a machine-readable rename map. Existing checkouts must migrate old skill directories explicitly.
- Left `.agents/skills/` external Altimate IDs unchanged and did not install marimo-pair or Dagster's official skill. Preserved MotherDuck-only MCP and the dev-only dbt boundary.

## Historical changes

# Current update: product-owner and MotherDuck-only MCP

- Renamed the custom primary agent from `data-orchestrator` to **`product-owner`**, updated the project default, routing commands, specialist handoffs, tests, and current documentation. The product owner defines outcomes and acceptance criteria and requests **user** approval; it cannot self-approve engineering work.
- Preserved OpenCode's normal built-in Build and Plan primary agents. The custom default is project-local; inside the repo all agents still obey `AGENTS.md` and project permissions.
- Aligned the configured MCP connections with the user's earlier preference: **MotherDuck only**. Removed enabled dlt MCP and disabled dbt MCP config, retained skills and existing safety rules, and adjusted inherited dlt skills for a CLI-first workflow without MCP-only secret operations.
- Preserved root Git-ignored `analysis/`, the lightweight investigation path, specialist responsibilities, Altimate SQL/lineage, Git-owned MotherDuck Guides, and the disabled-by-default dev-only dbt runner.

## Historical changes

# Current update: ignored analysis workspace and product-owner

- Renamed custom primary `data-plan` to **`product-owner`**, including agent file, `opencode.json`, command targets, handoffs, tests and setup references. Stock Plan and the separate data-architect remain available.
- Root `analysis/` is now **entirely Git-ignored**, including notebooks, plans, figures, extracts and Guide candidates. No notebook/analysis file is automatically committed; the local README and files are untracked after applying the ignore rule. The existing root `.analysis/` remains engineering evidence.
- Introduced lightweight personal investigation routing: direct analyst handoff or `/explore`/`/notebook`, no routine engineering-plan/reviewer ceremony for edits confined to ignored `analysis/`. Tracked code, PR and Guide changes still require formal planning/approval and independent review. External warehouse queries/runtime/export actions retain separate approvals.
- Explicitly separated personal finding notes from canonical `transformation/guides/`: analytics-engineer reviews/preserves evidence and uses existing Git/CI guide publication, no direct Guide mutation.
- Preserved dlt ingestion DQ, dbt transformation DQ, dev-only dbt runner (still disabled), reviewer independence, Altimate deterministic SQL/lineage, marimo/Altair conventions and existing MCP configuration.
- Added regression tests for the rename, ignore policy, workspace ownership and investigation/engineering routing. No production repo, credentials, Guides, warehouse or runtime configuration was modified.

---

# Changes from the marimo/Altair update
- Moved analyst ownership, commands, notebook references/templates and ignore rules to root analysis/.
- Replaced custom plan override with product-owner, preserving stock Plan and separate architect. Added Guide/catalog/documentation discovery before implementation approval.
- Moved ingestion DQ skills to data-engineer; core dlt and pytest are default. Removed mandatory licence flow and unsafe historical composite-key workaround. Added transformation-quality skill for dbt Core.
- Aligned Guide authorship with supplied README: transformation/guides/, organization metadata, share references, stable IDs, Git SHA external_id, CI-only publication/reconciliation. Removed the provisional Guide tree and bespoke validator. guide-publish is now a no-write CI handoff.
- Added disabled-by-default dev dbt runner with fixed profile/target, explicit dev token, isolated HOME/artifacts/schema, approved shares, bounded command surface and source-bound receipts. It is not a sandbox or live permission verifier.
- Allowed analytics-engineer/reviewer to request the runner; source-read-only reviewer may perform development writes through approved tests/builds. Direct dbt/MCP and production remain denied.
- Kept Altimate native helpers and marimo/Altair templates; migrated paths and policy references. No native/warehouse execution is claimed.
- Added offline runner/config tests and migration/removal instructions. No actual production project, Guide metadata, CI workflow, credentials or warehouse state was modified.
