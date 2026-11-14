# OpenCode data-platform agent configuration (complete overlay)

This archive contains the **full current OpenCode configuration overlay**: seven custom agents, commands, rules, on-demand skills, Altimate helpers, dev-only dbt runner, tests and setup docs. It is based on `opencode-agentic-data-update.zip`, not on a checked-out copy of your private repository. It does **not** contain your real dlt/dbt/Dagster project, MotherDuck credentials or PR implementation.

## Install/migrate safely

1. Inspect this package, then merge the **contents of this `opencode/` directory into your repository root**. Do **not** overwrite the real repository README or existing `AGENTS.md` without reviewing/merging instructions, `transformation/guides/`, deployment workflow, Makefile, Python dependency manifest or CI scripts without review. The package's README/CHANGELOG/VALIDATION are distribution notes; save them under a suitable documentation name if you want them in your repository.
2. Merge `.gitignore.snippet` into the existing **root `.gitignore`**. Run `mkdir -p analysis` once per checkout (the ignored directory is not cloned). It adds `/analysis/` so **all analyst notebooks, plans, extracts, context candidates and exports are Git-ignored**, and `/.analysis/` for engineering evidence. Confirm with `git check-ignore analysis/notebooks/example.py`. If `git ls-files -- analysis/` shows previously tracked analyst files, review them and use `git rm -r --cached -- analysis/` to untrack without deleting local copies; commit that change. Git ignores are not access controls or backups.
3. Use `.opencode/agents/product-owner.md` as the default coordinator, as configured in `opencode.json`. **Remove stale `.opencode/agents/data-orchestrator.md` and `.opencode/agents/data-plan.md`** from prior installations (review local edits first). Do not restore the older `.opencode/agents/plan.md` override. Search your other custom commands for old names.
4. Use `/explore` or `/notebook` for fast analyst work in ignored `analysis/` without an engineering review ceremony. `product-owner` defaults to this lightweight path for personal investigation and to formal plan -> approve -> implement -> review for **tracked** engineering changes. SQL queries, notebook execution and exports still require the separate approvals documented in rules.
5. Read `docs/setup-notebooks.md`, `docs/warehouse-guides.md` and `docs/setup-dbt-safety.md` before enabling the relevant integrations. Canonical MotherDuck Guides remain **Git-authored under `transformation/guides/` and CI-published**. The dev-only dbt runner is disabled by default; only a verified development identity can unlock it. Native Altimate compatibility still requires your WSL smoke test.
6. Consult `REMOVALS.txt` before deleting earlier files, `docs/workflows.md` for routing and `VALIDATION.md` for the verification performed on this archive. Apply to your actual repository via a reviewed merge, not by assuming this distribution is a drop-in replacement for the whole repository.

The seven custom agents are `product-owner` (primary), `ask`, `data-architect`, `data-engineer`, `analytics-engineer`, `data-analyst`, `reviewer`. No extra platform agent, always-running Altimate MCP server or notebook service was added.


## Skill ID convention and migration

The **36 bundled** `.opencode/skills/` entries (27 project-specific plus nine upstream) follow using the portable `tool-skill` pattern (`dlt-*`, `dbt-*`, `dagster-*`, `marimo-*`, `motherduck-*`, `opencode-*`). Every skill has matching YAML `name`, a tool-specific `description`, and a **Primary tool** note just below its heading. OpenCode requires single-hyphen IDs, not `tool__skill`. See `docs/skill-catalog.md` and `python tools/config/list-skills.py`.

**If upgrading an existing checkout, do not just copy the archive:** read `docs/skill-migration.md` and run the dry-run migration helper before merging the overlay. Old folders otherwise remain discoverable alongside renamed skills. Altimate and marimo-pair are now copied under `.opencode/skills/` with OpenCode-compatible identifiers. Remove unprefixed duplicates from `.agents/skills/` after reviewing local changes.

## Normal OpenCode modes are retained

The default `product-owner` applies **only when this configuration is installed in this project**; do not install it as global `~/.config/opencode/opencode.json`. OpenCode's built-in **Build** (ordinary code work) and **Plan** (read-only planning) remain selectable via **Tab** or your `switch_agent` keybind. Verify with `opencode agent list`. For unrelated repositories opened outside this project, your normal global/default OpenCode setup applies. **Inside this repository, Build still obeys the repository's `AGENTS.md` and shared permission rules**; switching modes is not a credential or dbt-execution bypass.

## MCP policy

Based on the requested CLI/skills approach, `motherduck-remote` is the **only configured MCP**. dlt and dbt MCP entries were removed. dlt pipeline diagnostics use local `uv run dlt` commands and approved Azure CLI/Blob inspection; existing dlt skills have been adjusted so they do not demand a dlt MCP or run secret-management tools. Do not assume local dlt traces represent Azure Container Apps executions.

## Official specialist skills — all nine bundled

The latest user-provided `.agents(1).zip` supplies the **complete** Dagster `dagster-expert`, with 173 upstream reference documents. It is now included under `.opencode/skills/dagster-expert/`, with Windows `Zone.Identifier` metadata excluded. The `data-engineer` role loads it alongside the retained `dagster-fido-dagster` project skill. No further download or installer step is required.

- **Seven Altimate dbt skills** are bundled at `.opencode/skills/dbt-*`, including creation, debugging, testing, documentation, migration, refactoring and incremental models. `dbt-model-enhancement` (user-reported security flag) and Altimate agent delegation remain excluded. Project conventions are preserved in `.opencode/rules/dbt-standards.md`.
- **marimo-pair** is bundled at `.opencode/skills/marimo-pair/` with two execution/discovery helpers and five references; approval, authenticated localhost and root ignored `analysis/` rules remain.
- **Dagster expert** is bundled with its complete reference tree. The skill recommends Dagster Plus MCP as a general alternative, but the adapted skill and repository rules explicitly require **CLI-only Dagster work**. `dg launch` and all operations that might run code or write state remain approval-gated, with dbt execution still restricted to the separate dev-only wrapper.

To confirm all nine official skills exist after merging:

```bash
python tools/skills/install_official.py --status
python tools/config/list-skills.py
```

The pinned installer is retained only for future controlled updates; **do not run `--apply` over already bundled skills**. Read `docs/setup-official-skills.md` and `REMOVALS.txt` for de-duplicating unprefixed npx-installed copies. All agents retain project execution approvals, CI-only Guide publication and MotherDuck as the sole MCP.
