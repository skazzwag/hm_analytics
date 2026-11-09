# Bundled specialist skills — complete OpenCode setup

All **nine official specialist skills are included directly** in this ZIP. No WSL network installation step is necessary.

| Source | Installed under `.opencode/skills/` | Contents |
|---|---|---|
| Altimate data-engineering-skills | `dbt-creating-dbt-models`, `dbt-debugging-dbt-errors`, `dbt-testing-dbt-models`, `dbt-documenting-dbt-models`, `dbt-migrating-sql-to-dbt`, `dbt-refactoring-dbt-models`, `dbt-developing-incremental-models` | Seven standalone dbt workflows |
| marimo-team/marimo-pair | `marimo-pair` | Skill + five reference files + two shell helpers |
| dagster-io/skills | `dagster-expert` | Full official skill + 173 references, including `dg` CLI, assets, components, schedules, sensors and Dagster Plus CLI |

The **project-specific** `dagster-repo-structure` and `marimo-build-notebook` skills remain. So do the standalone `.agents/skills/transformation-quality`, `motherduck-guides` and `altimate-sql-analysis` workflows.

## Source and security notes

- `dbt-model-enhancement` remains omitted after the user reported a security flag. Altimate delegation is not included.
- Dagster's old deprecated stub was replaced by the **real** official skill. The new upload contained Windows `Zone.Identifier` sidecars; those are not part of the skill and were excluded.
- The official Dagster `SKILL.md` Git blob matches Dagster's pinned upstream commit, and its **173** reference docs come from the user upload. These supporting files have not all been independently verified against GitHub; see `.opencode/vendor/official-skills/installed.json` for the precise provenance.
- The upstream Dagster instructions describe Dagster Plus MCP. In **this project**, **MotherDuck is the only MCP**. Dagster must use the `dg` or `dg api` CLI (after approval), and must not connect or invoke Dagster MCP. Explicit project-policy notes are applied to the Dagster skill and its central API/launch references.
- `dg launch`, Dagster/Dbt/Dlt execution, local commands that import project definitions and production/cloud actions remain subject to role permissions and explicit development-only credential/state approval. No Dagster execution may bypass `.opencode/tools/dbt/run.py`. See `.opencode/rules/dagster.md`.
- Altimate workflows follow `.opencode/rules/dbt-execution.md` and use the disabled-by-default dev-only dbt wrapper. marimo-pair needs an explicitly approved authenticated localhost kernel and writes notebooks only inside ignored `analysis/`.
- Only Git/CI publishes MotherDuck Guides. The live code and services still require WSL verification.

## Verify after merging

```bash
python .opencode/tools/skills/install_official.py --status  # shows all nine INSTALLED
python .opencode/tools/config/list-skills.py --json
opencode agent list
```

The pinned installer remains available for future **reviewed upgrades**, not initial setup. It intentionally refuses to overwrite bundled skills. Avoid `python .opencode/tools/skills/install_official.py --apply` on the populated distribution.

## Avoid duplicate skill discovery

If you used `npx skills` previously, back up any local modifications and remove unprefixed copies in `.agents/skills/` — **including `.agents/skills/dagster-expert/`**, whether that copy is the old deprecated stub or the new full official version. The canonical project copy is `.opencode/skills/dagster-expert/`. Also review `REMOVALS.txt` and `.opencode/docs/skill-migration.md` before merging.
