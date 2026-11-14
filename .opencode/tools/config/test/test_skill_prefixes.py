"""Regressions for portable tool-prefixed OpenCode skills and safe migration."""
from pathlib import Path
import json
import re
import subprocess
import sys
import tempfile
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[4]
PREFIXES = {'altimate', 'dlt', 'dagster', 'dbt', 'marimo', 'motherduck', 'opencode'}
BASE = ROOT / '.opencode' / 'skills'
MAPPING = json.loads((ROOT / '.opencode/tools/config/skill-rename-map.json').read_text())['previous_to_current']
RETAINED = {'altimate-sql-analysis','motherduck-guides','transformation-quality'}


class SkillPrefixTests(unittest.TestCase):
    def test_all_existing_skill_ids_have_portable_names(self):
        folders = {p.name for p in BASE.iterdir() if p.is_dir()}
        vendors = {'dbt-creating-dbt-models','dbt-debugging-dbt-errors','dbt-testing-dbt-models','dbt-documenting-dbt-models','dbt-migrating-sql-to-dbt','dbt-refactoring-dbt-models','dbt-developing-incremental-models','marimo-pair','dagster-expert'}
        present = folders & vendors
        self.assertEqual(present, vendors, 'All nine upstream skills must be bundled')
        self.assertEqual(folders, set(MAPPING.values())|present|RETAINED)
        self.assertEqual(len(folders),30+len(present))
        for name in folders:
            self.assertRegex(name, r'^[a-z0-9]+(-[a-z0-9]+)*$')
            self.assertLessEqual(len(name), 64)
            # transformation-quality is the retained workflow skill that predates the tool-prefix convention
            if name != 'transformation-quality':
                self.assertIn(name.split('-', 1)[0], PREFIXES)
            self.assertTrue((BASE/name/'SKILL.md').is_file())

    def test_names_descriptions_and_primary_tool_are_visible(self):
        for folder in BASE.iterdir():
            text = (folder/'SKILL.md').read_text()
            self.assertTrue(text.startswith('---\n'),folder)
            front, body = text.split('---', 2)[1:]
            info = yaml.safe_load(front)
            self.assertEqual(info['name'],folder.name)
            self.assertTrue(info['description'])
            self.assertLessEqual(len(info['description']),1024)
            self.assertIn(folder.name.split('-',1)[0],info['description'].lower())
            self.assertIn('**Primary tool:**',body)
            self.assertLess(body.index('**Primary tool:**'),body.index('\n## ') if '\n## ' in body else len(body))

    def test_agent_allowlisted_skill_ids_all_exist_locally_or_as_vendor_skill(self):
        local = {p.name for p in BASE.iterdir() if p.is_dir()}
        external = {p.name for p in (ROOT/'.agents/skills').iterdir() if p.is_dir()} if (ROOT/'.agents/skills').is_dir() else set()
        # All nine official skills are bundled in .opencode/skills; no external installer required.
        for path in (ROOT/'.opencode/agents').glob('*.md'):
            info = yaml.safe_load(path.read_text().split('---',2)[1])
            permissions=info.get('permission',{}).get('skill',{})
            if isinstance(permissions,str): continue
            for key,decision in permissions.items():
                if decision == 'allow' and key != '*':
                    self.assertIn(key,local|external,(path,key))

    def test_no_legacy_identifiers_in_active_configuration(self):
        old=set(MAPPING)
        pattern=re.compile(r'(?<![a-z0-9-])('+'|'.join(map(re.escape,sorted(old,key=len,reverse=True)))+r')(?![a-z0-9-])')
        for path in [ROOT/'AGENTS.md',ROOT/'.opencode/opencode.json',*(ROOT/'.opencode/agents').rglob('*.md'),*(ROOT/'.opencode/commands').rglob('*.md'),*(ROOT/'.opencode/rules').rglob('*.md'),*(ROOT/'.opencode/skills').rglob('*.md')]:
            self.assertIsNone(pattern.search(path.read_text()),str(path))

    def test_no_name_collisions_with_vendor_skills(self):
        opencode={p.name for p in BASE.iterdir() if p.is_dir()}
        vendor={p.name for p in (ROOT/'.agents/skills').iterdir() if p.is_dir()} if (ROOT/'.agents/skills').is_dir() else set()
        self.assertFalse(opencode & vendor)

    def test_migration_script_is_dry_run_then_idempotent(self):
        helper=ROOT/'.opencode/tools/config/migrate-skill-paths.py'
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)/'.opencode/skills'
            folder.mkdir(parents=True)
            (folder/'build-notebook').mkdir()
            (folder/'build-notebook'/'custom.txt').write_text('local edits stay')
            dry=subprocess.run([sys.executable,str(helper),'--repo',temp],capture_output=True,text=True)
            self.assertEqual(dry.returncode,0,dry.stderr)
            self.assertTrue((folder/'build-notebook').is_dir())
            self.assertFalse((folder/'marimo-build-notebook').exists())
            apply=subprocess.run([sys.executable,str(helper),'--repo',temp,'--apply'],capture_output=True,text=True)
            self.assertEqual(apply.returncode,0,apply.stderr)
            self.assertFalse((folder/'build-notebook').exists())
            self.assertEqual((folder/'marimo-build-notebook'/'custom.txt').read_text(),'local edits stay')
            again=subprocess.run([sys.executable,str(helper),'--repo',temp,'--apply'],capture_output=True,text=True)
            self.assertEqual(again.returncode,0,again.stderr)

    def test_migration_script_refuses_overwrite_all_or_nothing(self):
        helper=ROOT/'.opencode/tools/config/migrate-skill-paths.py'
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)/'.opencode/skills'
            folder.mkdir(parents=True)
            for name in ('build-notebook','marimo-build-notebook','debug-pipeline'):
                (folder/name).mkdir()
            ret=subprocess.run([sys.executable,str(helper),'--repo',temp,'--apply'],capture_output=True,text=True)
            self.assertEqual(ret.returncode,2)
            self.assertIn('CONFLICT',ret.stderr)
            self.assertTrue((folder/'debug-pipeline').exists())
            self.assertFalse((folder/'dlt-debug-pipeline').exists())

    def test_inventory_command_matches_files(self):
        script=ROOT/'.opencode/tools/config/list-skills.py'
        res=subprocess.run([sys.executable,str(script),'--root',str(ROOT),'--json'],capture_output=True,text=True)
        self.assertEqual(res.returncode,0,res.stderr)
        rows=json.loads(res.stdout)
        self.assertEqual(len(rows),39)
        self.assertTrue(all(row['matches'] for row in rows))


if __name__=='__main__':
    unittest.main()
