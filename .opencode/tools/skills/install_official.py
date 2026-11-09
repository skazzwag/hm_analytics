#!/usr/bin/env python3
"""Reviewable, pinned installer for official skill collections (Dagster-only update supported).

No code from the downloaded skill bundles is executed during installation.
Requires network Git access only when fetching; project runtime uses only MotherDuck MCP.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
DEST = ROOT / '.opencode' / 'skills'
LOCK = Path(__file__).with_name('official-sources.lock.json')
PROVENANCE = ROOT / '.opencode' / 'vendor' / 'official-skills' / 'installed.json'
ALTIMATE = (
    'creating-dbt-models',
    'debugging-dbt-errors',
    'testing-dbt-models',
    'documenting-dbt-models',
    'migrating-sql-to-dbt',
    'refactoring-dbt-models',
    'developing-incremental-models',
)

POLICY = {
    'altimate': '''\n> **Primary tool:** dbt Core; standalone Altimate data-engineering workflow.\n> **Project override:** Repository `AGENTS.md`, `.opencode/rules/dbt-standards.md`, and `.opencode/rules/dbt-execution.md` take precedence over generic examples below. Execute dbt **only** through the separately enabled, approved development-only `python tools/dbt/run.py` wrapper. Never run raw `dbt`, `altimate-dbt`, the dbt Python API, Dagster to invoke dbt, or another Altimate agent. If that runner is unavailable, request traceable human/CI artifacts. Use `altimate-sql-analysis` for checks/lineage on current compiled SQL. MotherDuck Guides are Git-authored under `transformation/guides/` and CI-only published. Do not directly change published Guides.\n\n''',
    'marimo': '''\n> **Primary tool:** marimo (live notebook pairing, Python runtime); Altair for all project charts.\n> **Project override:** Pair only with the user's explicitly approved, authenticated localhost marimo session and only update notebooks under ignored root `analysis/`. A paired action executes Python: obtain separate approval before running code, live MotherDuck access, package installation or data export. Do not use `--no-token` to bypass authentication. Preserve the project notebook privacy, data-access and cost limits. A static notebook request uses `marimo-build-notebook` without requiring a running kernel.\n\n''',
    'dagster': '''\n> **Primary tool:** Dagster (`dg` CLI, assets and orchestration).\n> **Project override:** Use `.opencode/rules/dagster.md` and `dagster-fido-dagster` for repository conventions. `dg launch`, asset materialization, schedule/sensor execution and Dagster-triggered dbt/dlt may write to external systems: do not run without explicit approval of development-only identity, isolated state/destination and selected scope. Never use Dagster to bypass the approved dbt runner, production credential restrictions or Guide CI-only publication. Read-only definition checks also import project code and require appropriate authorization. MotherDuck is the project's ONLY MCP: never connect to, start or invoke Dagster or Dagster Plus MCP. Some upstream references describe MCP alternatives: disregard them and use approved `dg` / `dg api` CLI commands instead. Do not access Dagster Plus secrets, launch remote runs or modify deployments without separately granted authorization.\n\n''',
}


def manifest():
    obj = json.loads(LOCK.read_text(encoding='utf-8'))
    if set(obj) != {'altimate', 'marimo', 'dagster'}:
        raise ValueError('Unexpected official source names')
    for key, item in obj.items():
        if not re.fullmatch(r'[0-9a-f]{40}', item['sha']):
            raise ValueError(f'{key} requires a full pinned Git commit')
        if not item['repo'].startswith('https://github.com/') or not item['repo'].endswith('.git'):
            raise ValueError(f'{key} has an unexpected source URL')
    return obj


def specs():
    for name in ALTIMATE:
        yield ('altimate', 'dbt-' + name, 'skills/dbt/' + name)
    yield ('marimo', 'marimo-pair', 'skills/marimo-pair')
    # The older plugins/dagster-expert is now a deprecated STUB; use the dagster plugin.
    yield ('dagster', 'dagster-expert', 'plugins/dagster/skills/dagster-expert')


def installed_status(root=ROOT):
    base = root / '.opencode' / 'skills'
    return [(name, (base / name / 'SKILL.md').is_file()) for _, name, _ in specs()]


def cmd(*args, cwd=None):
    return subprocess.check_output(args, cwd=cwd, text=True, stderr=subprocess.STDOUT).strip()


def fetch_sources(temp_dir, items):
    repositories = {}
    for key, item in items.items():
        dst = temp_dir / key
        dst.mkdir(parents=True)
        cmd('git', 'init', '-q', str(dst))
        cmd('git', 'remote', 'add', 'origin', item['repo'], cwd=dst)
        try:
            cmd('git', '-c', 'protocol.version=2', 'fetch', '--quiet', '--depth=1', 'origin', item['sha'], cwd=dst)
        except subprocess.CalledProcessError as err:
            raise RuntimeError(f'Cannot fetch verified commit for {key}. Confirm WSL GitHub access and retry: {err.output[-400:]}') from err
        cmd('git', 'checkout', '-q', '--detach', 'FETCH_HEAD', cwd=dst)
        repositories[key] = dst
    return repositories


def validate_sources(sources, items):
    for key, path in sources.items():
        if not path.is_dir():
            raise ValueError(f'No source directory for {key}: {path}')
        revision = cmd('git', 'rev-parse', 'HEAD', cwd=path)
        if revision != items[key]['sha']:
            raise ValueError(f'{key} source commit {revision} does not match pinned {items[key]["sha"]}')
        # Dirty/untracked files could change what we vendor, including executable shell scripts.
        if cmd('git', 'status', '--porcelain', cwd=path):
            raise ValueError(f'{key} source checkout has modifications; use a clean verified checkout')
        if not (path / 'LICENSE').is_file():
            raise ValueError(f'{key} is missing its LICENSE file')


def scan_for_symlinks(src):
    if src.is_symlink():
        raise ValueError(f'Symlink forbidden in vendor source: {src}')
    for path in src.rglob('*'):
        if path.is_symlink():
            raise ValueError(f'Symlink forbidden in vendor source: {path}')


def adapt_entry(original, target_name, source):
    if not original.startswith('---\n'):
        raise ValueError(f'{target_name} is missing YAML frontmatter')
    match = re.match(r'\A(---\n)(.*?)(\n---\n)', original, flags=re.S)
    if not match:
        raise ValueError(f'{target_name} has invalid YAML frontmatter')
    front = match.group(2)
    # Only modify name; preserve all vendor instructions, relative reference links, and other fields.
    names = re.findall(r'^name:\s*.+$', front, flags=re.M)
    if len(names) != 1:
        raise ValueError(f'{target_name} has unexpected name frontmatter')
    front = re.sub(r'^name:\s*.+$', 'name: ' + target_name, front, count=1, flags=re.M)
    # Explicitly mention the provenance/source in body as well as tool-prefixed ID.
    note = POLICY[source]
    return '---\n' + front + '\n---\n' + note + original[match.end():]


def safe_copy(src, dst):
    scan_for_symlinks(src)
    shutil.copytree(src, dst, symlinks=False)
    # Reject nested git directories and files with unsafe links or data not in source tree.
    for path in dst.rglob('.git'):
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()


def install_sources(sources, items, root=ROOT, only=None):
    selected = [item for item in specs() if only is None or item[0] == only]
    if not selected:
        raise ValueError('No skills selected')
    required = {source for source, _, _ in selected}
    validate_sources({key: sources[key] for key in required}, items)
    target = root / '.opencode' / 'skills'
    target.mkdir(parents=True, exist_ok=True)
    records = []
    for key, name, rel in selected:
        if (target / name).exists():
            raise ValueError(f'Skill already exists: {target/name}. Back up local edits before replacing.')
        origin = sources[key] / rel
        if not (origin / 'SKILL.md').is_file():
            raise ValueError(f'Upstream entry missing: {origin/"SKILL.md"}')
        scan_for_symlinks(origin)
    # Fail before writing if legacy unprefixed installs are present.
    for name in (ALTIMATE if only in (None, 'altimate') else ()):
        legacy = root / '.agents' / 'skills' / name
        if legacy.exists():
            raise ValueError(f'Legacy Altimate skill would duplicate new workflow: {legacy}. Back up and remove it manually.')
    # A deprecated Dagster plugin may expose the same skill ID and mask the
    # real reference-rich skill. Stop rather than silently shadow it.
    if only in (None, 'dagster') and (root / '.agents' / 'skills' / 'dagster-expert').exists():
        raise ValueError('Deprecated .agents/skills/dagster-expert may shadow the real skill; back up and remove it first.')
    with tempfile.TemporaryDirectory(prefix='official-skill-stage-', dir=target) as tmp:
        tmp_dir = Path(tmp)
        for key, name, rel in selected:
            origin = sources[key] / rel
            dst = tmp_dir / name
            safe_copy(origin, dst)
            original = (dst / 'SKILL.md').read_text(encoding='utf-8')
            adapted = adapt_entry(original, name, key)
            (dst / 'SKILL.md').write_text(adapted, encoding='utf-8')
            shutil.copy2(sources[key]/'LICENSE', dst/'LICENSE')
            digest = hashlib.sha256(original.encode()).hexdigest()
            records.append({'name': name, 'source': key, 'origin': rel, 'upstream_skill_sha256': digest, 'upstream_commit': items[key]['sha'], 'files': sum(1 for p in dst.rglob('*') if p.is_file())})
        # Revalidate selected skills before exposing any for discovery.
        for key, name, rel in selected:
            text = (tmp_dir / name / 'SKILL.md').read_text(encoding='utf-8')
            if not re.search(r'^name:\s*' + re.escape(name) + r'\s*$', text, re.M):
                raise ValueError(f'Adapted skill header mismatch: {name}')
            if '**Primary tool:**' not in text:
                raise ValueError(f'Project policy missing: {name}')
        for _, name, _ in selected:
            (tmp_dir / name).rename(target / name)
    provenance = root / 'vendor' / 'official-skills' / 'installed.json'
    provenance.parent.mkdir(parents=True, exist_ok=True)
    previous = json.loads(provenance.read_text()) if provenance.exists() else {}
    prior = [r for r in previous.get('skills', []) if r.get('name') not in {r['name'] for r in records}]
    previous.update({'sources': items, 'skills': prior + records, 'installation': 'user-uploaded vetted skills plus pinned reviewed checkouts; adapted policy banners'})
    provenance.write_text(json.dumps(previous, indent=2) + '\n', encoding='utf-8')
    return records


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--apply', action='store_true', help='Install selected pinned upstream skills; use --only dagster with this ZIP')
    group.add_argument('--status', action='store_true', help='Show whether skills are installed without network access (default)')
    parser.add_argument('--source', action='append', default=[], metavar='KEY=PATH', help='Use verified local clean checkouts instead of fetching; repeat for altimate, marimo, dagster')
    parser.add_argument('--only', choices=['altimate','marimo','dagster'], help='Install only this missing collection without replacing already bundled skills')
    args = parser.parse_args(argv)
    missing = [name for name, yes in installed_status() if not yes]
    if not args.apply:
        for name, yes in installed_status():
            print(f'{"INSTALLED" if yes else "MISSING"}  {name}')
        return 0 if not missing else 1
    items = manifest()
    sources = {}
    for field in args.source:
        if '=' not in field:
            parser.error('--source must be KEY=/absolute/path')
        key, value = field.split('=', 1)
        if key not in items or key in sources:
            parser.error(f'Unknown/duplicate source: {key}')
        sources[key] = Path(value).expanduser().resolve()
    required = {args.only} if args.only else set(items)
    if sources and set(sources) != required:
        parser.error('Provide source directories for exactly the selected collection(s), or none to fetch them')
    try:
        if sources:
            records = install_sources(sources, items, only=args.only)
        else:
            with tempfile.TemporaryDirectory(prefix='opencode-upstream-skills-') as temp:
                repos = fetch_sources(Path(temp), {key: items[key] for key in required})
                records = install_sources(repos, items, only=args.only)
        print('Installed official skills:', ', '.join(r['name'] for r in records))
    except (ValueError, RuntimeError, subprocess.CalledProcessError, OSError) as error:
        print(f'INSTALL BLOCKED: {error}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
