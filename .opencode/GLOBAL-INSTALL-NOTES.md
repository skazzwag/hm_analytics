# Global install restructure for OpenCode v2.2.6

This directory is the OpenCode configuration overlay restructured for a **global install**
(`~/.config/opencode`), verified against the opencode v2.2.6 binary. The original archive was
authored as a project-root overlay; installed globally as-is, OpenCode v2 discovered none of
its agents, commands or skills. The fixes below make the global layout work on v2.2.6.

## Why it did not work

OpenCode v2 discovers global definitions at the top level of the config directory, not under a
nested `.opencode/` directory:

| Kind     | v2 global discovery path              |
|----------|---------------------------------------|
| Agents   | `~/.config/opencode/agents/*.md`      |
| Commands | `~/.config/opencode/commands/*.md`    |
| Skills   | `~/.config/opencode/skills/<id>/`     |
| Plugins  | `~/.config/opencode/plugins/*.js`     |
| Rules    | no auto-discovery; loaded by reference |

The archive kept them at `~/.config/opencode/.opencode/{agents,commands,skills}/` and
`~/.config/opencode/.agents/skills/`, which v2 only matches as *project-level* sources. With
`default_agent` pointing at the undiscovered `product-owner`, OpenCode silently fell back to
the built-in `build` agent, so every session behaved like plain opencode.

## What changed

1. Moved `.opencode/agents/`, `.opencode/commands/`, `.opencode/skills/` and `.opencode/rules/`
   up to the top level of the config directory (`agents/`, `commands/`, `skills/`, `rules/`).
2. Merged the three remaining `.agents/skills/` skills (`motherduck-guides`,
   `altimate-sql-analysis`, `transformation-quality`) into `skills/`.
3. Plan files moved in v2 from the project (`.opencode/plans/`) to the home directory
   (`~/.opencode/plan/`). The old path was also hard-coded as the only allowed edit target, so
   the plan agent and `product-owner` could not write plan files at all on v2.2.6. All
   references and permission allows now use `~/.opencode/plan/**`.
4. Rule-file references in agents, commands, skills, rules and `AGENTS.md` now point at
   `~/.config/opencode/rules/...` (the read tool expands `~`, verified in the v2.2.6 source).
5. Added `"~/.config/opencode/**": "deny"` to the edit permission, so agents cannot edit this
   global configuration, agents or skills in any project.
6. Removed `tui.jsonc`: it is V1 terminal configuration, no longer read by v2. The V2
   equivalent, `cli.json` with the herdr TUI plugin entry, is already present and verified
   loading on v2.2.6.

## What did not need to change

The V1-format `opencode.json` keys (`permission`, flat `mcp`, `agent` map, `watcher`,
`default_agent`) are deprecated but fully normalized by v2.2.6; the agent Markdown frontmatter
(V1 `permission` maps, `task` action) is likewise read and normalized (`bash` -> `shell`,
`task` -> `subagent`). Verified against the binary: all seven agents load with correct
permissions and the MotherDuck MCP entry normalizes into `mcp.servers`.

## Caveats of the global install

- The agents, rules and `AGENTS.md` describe the Fido data platform and reference
  repository-relative paths (`transformation/`, `ingestion/`, `tools/dbt/run.py`). They apply
  in every project; outside the data repository those paths simply do not exist, so agents
  report them as missing rather than acting on them.
- `AGENTS.md` at the config root is loaded as **global instructions for all projects**.
  The repo-specific deny patterns (`AGENTS.md`, `opencode.json`, `.opencode/**`) likewise apply
  everywhere, which matches the original protective intent (agents cannot edit instruction or
  config files in any project) but is stricter than the project-only install.
- The maintenance scripts under `tools/` (skill installer, config tests) still assume the
  project-overlay layout. Do not run them from this directory against the moved
  `agents/`/`commands/`/`skills/` layout; maintain skills by editing `skills/` directly.
- If you later want this configuration scoped to the data repository only, the original
  overlay layout is still the documented design: merge the overlay contents into the
  repository root instead (see `README.md`), and OpenCode discovers everything under
  `.opencode/` automatically.

## Install

Back up your current config, then replace it with this directory's contents:

```bash
cp -R ~/.config/opencode ~/.config/opencode.backup-$(date +%Y%m%d)
# extract this archive, then:
rsync -a opencode/ ~/.config/opencode/
```

Verify:

```bash
opencode debug agents        # product-owner, reviewer, ask, data-* agents must appear
opencode plugin list         # herdr-opencode entry
```
