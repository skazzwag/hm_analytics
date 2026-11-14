"""Offline unit tests for pinned upstream skill copying and the execution boundary."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('install_official', HERE/'install_official.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


def git(path, *args):
    return subprocess.check_output(['git','-C',str(path),*args],text=True,stderr=subprocess.STDOUT).strip()


def prepare_fake_sources(base):
    repositories={}
    pins={}
    for key in ['altimate','marimo','dagster']:
        path=base/key
        path.mkdir()
        git(path,'init','-q')
        git(path,'config','user.email','test@example.invalid')
        git(path,'config','user.name','Skill Fixture')
        (path/'LICENSE').write_text(f'{key} test license\n')
        repositories[key]=path
    for key,name,rel in installer.specs():
        folder=repositories[key]/rel
        folder.mkdir(parents=True)
        (folder/'SKILL.md').write_text(f'---\nname: {name}\ndescription: Workflow for {name}\n---\n# {name}\n\nDo the job.\n')
        if key=='marimo':
            (folder/'reference').mkdir()
            (folder/'reference/example.md').write_text('Reference text')
            (folder/'scripts').mkdir()
            (folder/'scripts/discover-servers.sh').write_text('#!/bin/sh\nexit 0\n')
            (folder/'scripts/execute-code.sh').write_text('#!/bin/sh\nexit 0\n')
        if key=='dagster':
            (folder/'references/cli').mkdir(parents=True)
            (folder/'references/cli/launch.md').write_text('# dg launch docs\n')
    for key,path in repositories.items():
        git(path,'add','.')
        git(path,'commit','-qm','Fixture')
        pins[key]={'repo':f'https://github.com/{key}/example.git','sha':git(path,'rev-parse','HEAD')}
    return repositories, pins


class OfficialSkillsTests(unittest.TestCase):
    def test_expected_pins_and_unique_ids(self):
        m=installer.manifest()
        self.assertEqual(set(m), {'altimate','marimo','dagster'})
        names=[name for _,name,_ in installer.specs()]
        self.assertEqual(len(names),9)
        self.assertEqual(len(set(names)),9)
        self.assertTrue(all(len(x)<=64 for x in names))
        self.assertEqual(names[-1],'dagster-expert')
        self.assertEqual(names[-2],'marimo-pair')

    def test_adapted_skill_preserves_body_and_enforces_policies(self):
        base='---\nname: original\ndescription: Hello\nallowed-tools: Bash\n---\n# Heading\n\nBody\n'
        for kind,name in [('altimate','dbt-creating-dbt-models'),('marimo','marimo-pair'),('dagster','dagster-expert')]:
            value=installer.adapt_entry(base,name,kind)
            self.assertIn('name: '+name,value)
            self.assertIn('description: Hello',value)
            self.assertIn('allowed-tools: Bash',value)
            self.assertIn('# Heading\n\nBody\n',value)
            self.assertIn('**Primary tool:**',value)
            self.assertIn('Project override',value)
        self.assertIn('approved development-only', installer.POLICY['altimate'])
        self.assertIn('explicitly approved', installer.POLICY['marimo'])
        self.assertIn('Dagster-triggered', installer.POLICY['dagster'])

    def test_install_all_nine_with_complete_supporting_folders(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/'sources').mkdir()
            sources,pins=prepare_fake_sources(root/'sources')
            target=root/'project'
            records=installer.install_sources(sources,pins,root=target)
            self.assertEqual(len(records),9)
            self.assertEqual(len(installer.installed_status(target)),9)
            self.assertTrue(all(ok for _,ok in installer.installed_status(target)))
            self.assertTrue((target/'.opencode/skills/marimo-pair/reference/example.md').is_file())
            self.assertTrue((target/'.opencode/skills/marimo-pair/scripts/execute-code.sh').is_file())
            self.assertTrue((target/'.opencode/skills/dagster-expert/references/cli/launch.md').is_file())
            self.assertTrue((target/'.opencode/skills/dagster-expert/LICENSE').is_file())
            self.assertTrue((target/'vendor/official-skills/installed.json').exists())
            receipt=json.loads((target/'vendor/official-skills/installed.json').read_text())
            self.assertEqual(len(receipt['skills']),9)
            with self.assertRaisesRegex(ValueError,'already exists'):
                installer.install_sources(sources,pins,root=target)

    def test_install_only_dagster_after_bundling_other_collections(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); (root/'sources').mkdir()
            sources,pins=prepare_fake_sources(root/'sources')
            target=root/'project'
            installer.install_sources(sources,pins,root=target,only='altimate')
            installer.install_sources(sources,pins,root=target,only='marimo')
            records=installer.install_sources({'dagster':sources['dagster']},pins,root=target,only='dagster')
            self.assertEqual([r['name'] for r in records],['dagster-expert'])
            self.assertTrue(all(ok for _,ok in installer.installed_status(target)))
            receipt=json.loads((target/'vendor/official-skills/installed.json').read_text())
            self.assertEqual(len(receipt['skills']),9)

    def test_deprecated_dagster_shadow_blocks_install(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); (root/'sources').mkdir()
            sources,pins=prepare_fake_sources(root/'sources')
            target=root/'project'
            stale=target/'.agents/skills/dagster-expert'
            stale.mkdir(parents=True)
            (stale/'SKILL.md').write_text('deprecated notice only')
            with self.assertRaisesRegex(ValueError,'shadow'):
                installer.install_sources({'dagster':sources['dagster']},pins,root=target,only='dagster')
            self.assertFalse((target/'.opencode/skills/dagster-expert').exists())

    def test_wrong_ref_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); (root/'sources').mkdir()
            sources,pins=prepare_fake_sources(root/'sources')
            pins['altimate']['sha']='0'*40
            with self.assertRaisesRegex(ValueError,'does not match pinned'):
                installer.install_sources(sources,pins,root=root/'project')
            self.assertFalse((root/'project/.opencode/skills').exists())

    def test_dirty_source_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); (root/'sources').mkdir()
            sources,pins=prepare_fake_sources(root/'sources')
            (sources['marimo']/'README.md').write_text('Untracked')
            with self.assertRaisesRegex(ValueError,'modifications'):
                installer.install_sources(sources,pins,root=root/'project')

    def test_duplicate_legacy_skill_blocks_install(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); (root/'sources').mkdir()
            sources,pins=prepare_fake_sources(root/'sources')
            legacy=root/'project/.agents/skills/creating-dbt-models'
            legacy.mkdir(parents=True)
            (legacy/'SKILL.md').write_text('locally changed')
            with self.assertRaisesRegex(ValueError,'Legacy Altimate'):
                installer.install_sources(sources,pins,root=root/'project')
            self.assertEqual((legacy/'SKILL.md').read_text(),'locally changed')

if __name__=='__main__': unittest.main()
