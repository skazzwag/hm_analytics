# Migrate existing `.opencode/skills/` directories

The preceding release renamed **28 local project skills**. This release then removes the superseded `dbt-fido-model`, leaving 27 local project skills before installing the nine official vendors. Agent allowlists and references use the new IDs. An ordinary file-copy merge leaves stale old folders active, so take care to remove or move the old skill folders.

## Safe sequence

1. Commit or back up changes in your repository and ensure no local skill modifications will be discarded.
2. Unzip the new distribution **outside** your repository.
3. Run the included dry-run tool (replace the repository path):

   ```bash
   python /path/to/unzipped/opencode/.opencode/tools/config/migrate-skill-paths.py --repo /path/to/analytics-pipelines
   ```

4. Inspect the proposed moves. If it reports a conflict, reconcile the pre-existing destination manually. The tool refuses to overwrite anything and never edits Git files, credentials or tracked project code.
5. Apply the renames **before** merging the updated files:

   ```bash
   python /path/to/unzipped/opencode/.opencode/tools/config/migrate-skill-paths.py --repo /path/to/analytics-pipelines --apply
   ```

6. Review/merge `.opencode/skills/`, `.opencode/agents/`, `.opencode/rules/`, `.opencode/commands/`, `tools/`, and other updated distribution files. Merge `AGENTS.md` and repository-specific docs; do not replace your production project or CI. The copies in the new `.opencode/skills/` folders carry the revised frontmatter, callouts and references.
7. Run `git status` and review all renames and any lingering obsolete folders. Use `python .opencode/tools/config/list-skills.py` from your repository root and the regression tests if you have their dependencies.
8. Run OpenCode from the project and confirm the expected skill IDs and agent access. Do not claim live validation from this archive's offline tests.

**Important:** `--apply` only changes directory names. It does not update references by itself; step 6 is required. If you already copied the new overlay and old folders still exist, the tool will report destination conflicts rather than deleting the old versions. Review those duplicates manually, then remove only the obsolete old folders once you've preserved your changes.

The new official installer uses tool-prefixed vendor IDs under `.opencode/skills/`. Previously installed unprefixed Altimate skills under `.agents/skills/` must be backed up and removed before running it; the three separate local `.agents/skills/` policies remain intact.


## Replacing the old custom dbt skill and adding official skills

After backing up any modifications, remove the old `.opencode/skills/dbt-fido-model/` directory. The new ZIP omits it and removes its allowlist references. Fido dbt conventions continue in `.opencode/rules/dbt-standards.md`; the retained `transformation-quality` skill handles dbt DQ.

If you previously ran the old Altimate installer, first back up and remove the seven unprefixed `.agents/skills/<upstream-name>/` directories. Do **not** remove the separate `altimate-sql-analysis`, `transformation-quality` or `motherduck-guides` skills. The official installer detects legacy copies and **fails instead of deleting** them. Run `python .opencode/tools/skills/install_official.py --apply` only after the new overlay is merged and those collisions are cleared. The old `.opencode/tools/altimate/install-skills.mjs` and its test are removed; do not keep executing them. See `.opencode/docs/setup-official-skills.md`.
