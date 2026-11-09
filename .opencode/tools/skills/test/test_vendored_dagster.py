"""Offline packaged Dagster completeness and project safety checks."""
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[4]
SKILLS=ROOT/'.opencode/skills'

class VendoredDagsterTests(unittest.TestCase):
    def test_complete_skill_tree_and_policy(self):
        p=SKILLS/'dagster-expert'
        text=(p/'SKILL.md').read_text()
        self.assertIn('name: dagster-expert',text)
        self.assertIn('**Primary tool:** Dagster',text)
        self.assertIn('MotherDuck is the project',text)
        self.assertIn('never connect to, start or invoke Dagster',text)
        self.assertGreater(len(list((p/'references').rglob('*.md'))),150)
        for path in ['references/cli/launch.md','references/cli/api/general.md',
                     'references/assets/INDEX.md','references/automation/schedules.md',
                     'references/integrations/INDEX.md','LICENSE']:
            self.assertTrue((p/path).is_file(),path)
        self.assertIn('Project override', (p/'references/cli/api/general.md').read_text())
    def test_no_windows_ads_and_no_duplicate_dagster(self):
        self.assertFalse(any('Zone.Identifier' in str(p) for p in SKILLS.rglob('*')))
        self.assertFalse((ROOT/'.agents/skills/dagster-expert').exists())
    def test_dagster_relative_reference_links_resolve(self):
        import re
        folder=SKILLS/'dagster-expert'
        for document in (folder/'SKILL.md', *(folder/'references').rglob('*.md')):
            content=document.read_text()
            for link in re.findall(r'\]\(([^)]+)\)',content):
                if link.startswith(('https:','http:','mailto:','#','/')): continue
                target=link.split('#',1)[0]
                if not target or target.startswith(('<','`')) or '${' in target: continue
                self.assertTrue((document.parent/target).exists(),(document.relative_to(folder),target))

    def test_receipt_all_nine(self):
        data=json.loads((ROOT/'.opencode/vendor/official-skills/installed.json').read_text())
        entries=data['skills']
        self.assertEqual(len(entries),9)
        self.assertEqual({e['name'] for e in entries},set(p.name for p in SKILLS.iterdir() if p.name.startswith('dbt-'))|{'marimo-pair','dagster-expert'})
        self.assertEqual(next(e for e in entries if e['name']=='dagster-expert')['source_documents'],174)

if __name__=='__main__': unittest.main()
