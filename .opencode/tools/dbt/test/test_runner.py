"""Offline runner tests. No dbt installation, credentials or warehouse are used."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location("guard", Path(__file__).parents[1] / "run.py")
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)

class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.exe = self.root / "fake-dbt"
        self.exe.write_text('#!/usr/bin/env python3\nprint("fixture command; not dbt")\n')
        self.exe.chmod(0o700)
        self.config = {"enabled": True, "boundary_verified_by_user": True,
                       "dbt_executable": str(self.exe), "database": "agent_dev_test",
                       "attachments": [], "timeout_seconds": 5}
        (self.root / "transformation/models").mkdir(parents=True)
        (self.root / "transformation/dbt_project.yml").write_text('name: fixture\n')
        (self.root / "transformation/models/x.sql").write_text('select 1 as id\n')
    def tearDown(self): self.tmp.cleanup()
    def load(self, **updates):
        config = dict(self.config, **updates)
        p = self.root / 'policy.json'; p.write_text(json.dumps(config))
        return guard.load_config(p)
    def args(self, *extra):
        return guard.parse_args(['compile','--actor','implementer','--session','example','--select','+x',*extra])
    def test_valid_config(self): self.assertEqual(self.load()['database'],'agent_dev_test')
    def test_disabled(self):
        with self.assertRaises(guard.Blocked): self.load(enabled=False)
    def test_unverified(self):
        with self.assertRaises(guard.Blocked): self.load(boundary_verified_by_user=False)
    def test_prod_database(self):
        with self.assertRaises(guard.Blocked): self.load(database='prod_analytics')
    def test_url_in_database(self):
        with self.assertRaises(guard.Blocked): self.load(database='agent_dev_x?motherduck_token=x')
    def test_unknown_config(self):
        with self.assertRaises(guard.Blocked): self.load(token='never-read')
    def test_relative_executable(self):
        with self.assertRaises(guard.Blocked): self.load(dbt_executable='dbt')
    def test_missing_executable(self):
        with self.assertRaises(guard.Blocked): self.load(dbt_executable='/missing/dbt')
    def test_timeout_bounds(self):
        for value in [0,3601,True,'30']:
            with self.subTest(value=value), self.assertRaises(guard.Blocked): self.load(timeout_seconds=value)
    def test_share_only(self):
        with self.assertRaises(guard.Blocked): self.load(attachments=[{'path':'md:prod_analytics','alias':'source'}])
    def test_valid_share(self):
        cfg=self.load(attachments=[{'path':'md:_share/prod_analytics/b57bb6cc-f153-49c4-92c6-36f40631858b','alias':'prod_analytics'}])
        profile=guard.make_profile(cfg,'reviewer','task')
        self.assertTrue(profile['fido_agent']['outputs']['agent_dev']['attach'][0]['read_only'])
    def test_duplicate_alias(self):
        item={'path':'md:_share/db/00000000-0000-0000-0000-000000000001','alias':'source'}
        with self.assertRaises(guard.Blocked): self.load(attachments=[item,item])
    def test_token_not_in_profile(self):
        profile=guard.make_profile(self.config,'reviewer','example')
        self.assertEqual(set(profile['fido_agent']['outputs']),{'agent_dev'})
        self.assertNotIn('token',json.dumps(profile))
    def test_environment_drops_prod(self):
        env=guard.clean_environment(self.config,self.root/'home',{'MOTHERDUCK_AGENT_DEV_TOKEN':'fake-dev','MOTHERDUCK_PROD_TOKEN':'fake-prod','motherduck_token':'fake-prod','AWS_SECRET_ACCESS_KEY':'fake','HOME':'/prod','DBT_TARGET':'prod'})
        self.assertEqual(env['motherduck_token'],'fake-dev')
        self.assertNotIn('MOTHERDUCK_PROD_TOKEN',env); self.assertNotIn('DBT_TARGET',env)
        self.assertNotIn('AWS_SECRET_ACCESS_KEY',env); self.assertNotEqual(env['HOME'],'/prod')
    def test_no_cached_fallback(self):
        with self.assertRaises(guard.Blocked): guard.clean_environment(self.config,self.root,{'motherduck_token':'fake-prod'})
    def test_no_passthrough_flags(self):
        for flags in [['--target','prod'],['--full-refresh'],['--profiles-dir','/prod'],['--vars','{}']]:
            with self.subTest(flags=flags), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit): self.args(*flags)
    def test_no_operation(self):
        with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit): guard.parse_args(['run-operation','--actor','reviewer','--session','x'])
    def test_requires_selection(self):
        with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit): guard.parse_args(['build','--actor','reviewer','--session','x'])
    def test_parse_no_selection(self):
        self.assertEqual(guard.parse_args(['parse','--actor','reviewer','--session','x']).command,'parse')
    def test_session_traversal(self):
        with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit): guard.parse_args(['parse','--actor','reviewer','--session','../prod'])
    def test_option_in_selector(self):
        with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit): self.args('--select','x --target prod')
    def test_shell_in_selector(self):
        with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit): self.args('--select','x;echo evil')
    def test_command_fixed_target(self):
        cmd=guard.build_command(self.config,self.args(),self.root/'transformation',self.root/'out')
        self.assertEqual(cmd[cmd.index('--target')+1],'agent_dev')
    def test_dry_run_has_no_execution(self):
        with contextlib.redirect_stdout(io.StringIO()): code=guard.execute(self.args('--dry-run'),self.config,self.root,{})
        self.assertEqual(code,0); self.assertFalse((self.root/'.analysis').exists())
    def test_fake_process_receipt(self):
        with contextlib.redirect_stdout(io.StringIO()): code=guard.execute(self.args(),self.config,self.root,{'MOTHERDUCK_AGENT_DEV_TOKEN':'fake-dev'})
        self.assertEqual(code,0)
        receipt=json.loads(next((self.root/'.analysis').rglob('*.receipt.json')).read_text())
        self.assertEqual(receipt['status'],'passed'); self.assertFalse(receipt['production_verified'])
    def test_stale_session(self):
        with contextlib.redirect_stdout(io.StringIO()): guard.execute(self.args(),self.config,self.root,{'MOTHERDUCK_AGENT_DEV_TOKEN':'fake-dev'})
        (self.root/'transformation/models/x.sql').write_text('select 2 as id')
        with self.assertRaises(guard.Blocked): guard.execute(self.args(),self.config,self.root,{'MOTHERDUCK_AGENT_DEV_TOKEN':'fake-dev'})
    def test_source_mutation_is_inconclusive(self):
        self.exe.write_text('#!/usr/bin/env python3\nfrom pathlib import Path\nPath("models/x.sql").write_text("select 2 as id")\n')
        with contextlib.redirect_stdout(io.StringIO()): code=guard.execute(self.args(),self.config,self.root,{'MOTHERDUCK_AGENT_DEV_TOKEN':'fake-dev'})
        self.assertEqual(code,2)
    def test_output_symlink(self):
        other=self.root/'other'; other.mkdir(); (self.root/'.analysis').symlink_to(other,target_is_directory=True)
        with self.assertRaises(guard.Blocked): guard.execute(self.args(),self.config,self.root,{'MOTHERDUCK_AGENT_DEV_TOKEN':'fake-dev'})
    def test_literal_dev_token_redacted(self):
        self.exe.write_text('#!/usr/bin/env python3\nimport os\nprint(os.environ["motherduck_token"])\n')
        with contextlib.redirect_stdout(io.StringIO()): guard.execute(self.args(),self.config,self.root,{'MOTHERDUCK_AGENT_DEV_TOKEN':'fake-dev-sensitive'})
        text=next((self.root/'.analysis').rglob('*.output.txt')).read_text()
        self.assertNotIn('fake-dev-sensitive',text); self.assertIn('[REDACTED]',text)
    def test_source_digest_changes(self):
        a=guard.project_digest(self.root/'transformation'); (self.root/'transformation/models/x.sql').write_text('select 3')
        self.assertNotEqual(a,guard.project_digest(self.root/'transformation'))
    def test_missing_project(self):
        (self.root/'transformation/dbt_project.yml').unlink()
        with self.assertRaises(guard.Blocked): guard.execute(self.args('--dry-run'),self.config,self.root,{})

if __name__=='__main__': unittest.main()
