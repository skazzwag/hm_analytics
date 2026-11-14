# Local OpenCode skill catalog

The 27 project-specific skills and eight vendored specialist skills are stored under `.opencode/skills/`. **Prefix = primary tool or workflow**, not necessarily the only library used. `name:` in each SKILL.md matches its directory ID, `description:` identifies the relevant tool, and the body starts with a **Primary tool** callout. Skills load on demand; they are not MCP servers.

Names use `tool-skill` (single hyphens), **not** `tool__skill`: OpenCode portable skill IDs must follow `^[a-z0-9]+(-[a-z0-9]+)*$`, be at most 64 characters and match the folder. See [OpenCode Agent Skills](https://opencode.ai/docs/skills).

## Bundled skills by tool

| Tool | Skill ID | Agent allowlists |
|---|---|---|
| Dagster | `dagster-repo-structure` | `data-engineer`, `product-owner` |
| dlt / dltHub | `dlt-add-incremental-loading` | `data-engineer` |
| dlt / dltHub | `dlt-add-table` | `data-engineer` |
| dlt / dltHub | `dlt-adjust-endpoint` | `data-engineer` |
| dlt / dltHub | `dlt-adjust-table` | `data-engineer` |
| dlt / dltHub | `dlt-annotate-sources` | `data-architect` |
| dlt / dltHub | `dlt-create-filesystem-pipeline` | `data-engineer` |
| dlt / dltHub | `dlt-create-ontology` | `data-architect` |
| dlt / dltHub | `dlt-create-rest-api-pipeline` | `data-engineer` |
| dlt / dltHub | `dlt-create-sql-database-pipeline` | `data-engineer` |
| dlt / dltHub | `dlt-create-transformation` | *No direct allowlist* |
| dlt / dltHub | `dlt-debug-pipeline` | `data-engineer` |
| dlt / dltHub | `dlt-define-data-quality-checks` | `data-engineer` |
| dlt / dltHub | `dlt-find-source` | `data-engineer`, `product-owner` |
| dlt / dltHub | `dlt-generate-cdm` | `data-architect` |
| dlt / dltHub | `dlt-new-endpoint` | `data-engineer` |
| dlt / dltHub | `dlt-review-data-quality` | `data-engineer`, `reviewer` |
| dlt / dltHub | `dlt-run-data-quality` | `data-engineer` |
| dlt / dltHub | `dlt-setup-data-quality` | `data-engineer`, `reviewer` |
| dlt / dltHub | `dlt-setup-secrets` | `data-engineer` |
| dlt / dltHub | `dlt-toolkit-dispatch` | `ask`, `data-engineer`, `product-owner` |
| dlt / dltHub | `dlt-validate-data` | `data-engineer` |
| dlt / dltHub | `dlt-view-data` | `ask`, `data-analyst`, `data-engineer` |
| marimo / Altair | `marimo-build-notebook` | `data-analyst`, `reviewer` |
| MotherDuck | `motherduck-explore-data` | `ask`, `data-analyst` |
| OpenCode workflow | `opencode-review` | `product-owner`, `reviewer` |
| OpenCode workflow | `opencode-improve-skills` | *No direct allowlist* |

## Upstream specialist skills (all nine bundled)

This ZIP **includes seven Altimate dbt skills, marimo-pair and the complete official Dagster `dagster-expert`**, adapted for CLI-first OpenCode workflows and repository-specific execution approval. The Dagster entrypoint was verified against pinned upstream and all its 173 reference documents were copied from the new user-provided ZIP. The old deprecated stub remains excluded. See `.opencode/vendor/official-skills/installed.json` for provenance and `.opencode/docs/setup-official-skills.md` for usage.

| Tool / vendor | Installed skill ID | Agent allowlist |
|---|---|---|
| dbt Core (Altimate) | `dbt-creating-dbt-models` | analytics-engineer, product-owner |
| dbt Core (Altimate) | `dbt-debugging-dbt-errors` | analytics-engineer |
| dbt Core (Altimate) | `dbt-testing-dbt-models` | analytics-engineer, product-owner |
| dbt Core (Altimate) | `dbt-documenting-dbt-models` | analytics-engineer |
| dbt Core (Altimate) | `dbt-migrating-sql-to-dbt` | analytics-engineer |
| dbt Core (Altimate) | `dbt-refactoring-dbt-models` | analytics-engineer |
| dbt Core (Altimate) | `dbt-developing-incremental-models` | analytics-engineer |
| marimo (marimo-team) | `marimo-pair` | data-analyst |
| Dagster (dagster-io) | `dagster-expert` — **bundled, full references** | data-engineer |

Retained alongside the bundled skills: `transformation-quality`, `motherduck-guides` and `altimate-sql-analysis` were merged into `.opencode/skills/` (`transformation-quality` predates the tool-prefix convention and is exempt from the prefix check). Their project-specific policies remain valuable, including ingested-vs-transformed data quality checks, Git/CI-only Guide publication, and deterministic SQL/lineage. No dbt Labs official skills, Altimate agent delegation, Dagster MCP, or dlt MCP are installed.

**Bundled now:** 36 discoverable `.opencode/skills/` entries (27 project-local + seven Altimate dbt + marimo-pair + Dagster expert) and three retained `.agents/skills/` workflow entries. No upstream installation is needed. Use `python .opencode/tools/config/list-skills.py --json` and `python .opencode/tools/skills/install_official.py --status` to confirm.

## Maintain the convention

1. Choose one of the existing prefixes (`altimate`, `dlt`, `dbt`, `dagster`, `marimo`, `motherduck`, `opencode`) or document a new single-token tool prefix here.
2. Name directory and `name:` identically, and make `description:` explicitly identify the tool and when to load the skill.
3. Place a `> **Primary tool:** ...` line immediately below the main H1 heading. Distinguish a CLI, Python SDK, MCP, or an OpenCode-only workflow.
4. Update role `permission.skill` allowlists, agent prompts, commands, cross-skill references, helper script paths and tests whenever renaming.
5. Run `python .opencode/tools/config/list-skills.py` for a live inventory and the full static test suites. Do **not** add extra MCP servers just to satisfy a skill.
6. For future upstream skill installations, retain vendor content and provenance under the pinned local tool-prefixed IDs, with an explicit adaptation banner and upstream original hashes; avoid duplicate skill IDs.

## Migrating an existing checkout

**This is a migration**, not a file-copy-only change. The new ZIP cannot delete the 28 old directories already on disk. See `.opencode/docs/skill-migration.md` and use the provided dry-run migration helper **before** merging the new overlay.
