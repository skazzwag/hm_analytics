"""Regression tests for the user-uploaded upstream skills and project security adaptations."""
from pathlib import Path
import json, shutil, subprocess, unittest

ROOT = Path(__file__).resolve().parents[4]
VENDOR = ROOT/'.opencode/skills'
NAMES = (
    'dbt-creating-dbt-models', 'dbt-debugging-dbt-errors',
    'dbt-developing-incremental-models', 'dbt-documenting-dbt-models',
    'dbt-migrating-sql-to-dbt', 'dbt-refactoring-dbt-models',
    'dbt-testing-dbt-models', 'marimo-pair', 'dagster-expert',
)

class VendorBundleTests(unittest.TestCase):
    def test_all_nine_have_sources_and_approval_banners(self):
        sources = json.loads((ROOT/'.opencode/vendor/official-skills/installed.json').read_text())
        receipts={item['name']:item for item in sources['skills']}
        self.assertEqual(set(NAMES),set(receipts))
        for name in NAMES:
            file=VENDOR/name/'SKILL.md'
            self.assertTrue(file.exists(),name)
            self.assertIn('**Project override:**', file.read_text())
            self.assertIn('**Primary tool:**', file.read_text())
            self.assertTrue((VENDOR/name/'LICENSE').is_file())
            self.assertEqual(len(receipts[name]['upstream_skill_sha256']),64)
        self.assertNotIn('dbt-model-enhancement',receipts)

    def test_dagster_full_skill_not_deprecated_stub(self):
        skill=VENDOR/'dagster-expert'
        self.assertGreater((skill/'SKILL.md').stat().st_size,5000)
        self.assertEqual(len(list((skill/'references').rglob('*.md'))),173)
        self.assertIn('dg launch',(skill/'references/cli/launch.md').read_text())
        self.assertTrue((VENDOR/'dagster-repo-structure'/'SKILL.md').is_file())

    def test_marimo_scripts_and_refs_present(self):
        folder=VENDOR/'marimo-pair'
        self.assertEqual(len(list((folder/'reference').glob('*.md'))),5)
        for name in ('discover-servers.sh','execute-code.sh'):
            path=folder/'scripts'/name
            self.assertTrue(path.is_file())
            test=subprocess.run(['bash','-n',str(path)],capture_output=True,text=True)
            self.assertEqual(test.returncode,0,test.stderr)

    @unittest.skipUnless(shutil.which('jq') and shutil.which('curl'), 'Needs jq and curl')
    def test_marimo_execution_rejects_untrusted_kernel_targets(self):
        script=VENDOR/'marimo-pair/scripts/execute-code.sh'
        for args in [
            ['--url','http://localhost:2718@evil.test','--token','x','-c','print(1)'],
            ['--url','http://example.com:2718','--token','x','-c','print(1)'],
            ['--url','http://127.0.0.1:2718','-c','print(1)'],
        ]:
            p=subprocess.run(['bash',str(script),*args],capture_output=True,text=True,timeout=5)
            self.assertEqual(p.returncode,2,(args,p.stdout,p.stderr))

if __name__=='__main__': unittest.main()
