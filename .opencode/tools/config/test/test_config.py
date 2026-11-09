"""Static checks for this overlay; not a substitute for installed OpenCode QA."""
from pathlib import Path
import json
import re
import unittest
import yaml

ROOT=Path(__file__).resolve().parents[4]
def load_agent(name):
    text=(ROOT/'.opencode/agents'/f'{name}.md').read_text()
    return yaml.safe_load(text.split('---',2)[1])
def permits(rules, value):
    if isinstance(rules,str): return rules
    action=None
    for pattern,result in rules.items():
        pattern=re.escape(pattern).replace(r'\*','.*').replace(r'\?','.')
        if re.fullmatch(pattern,value): action=result
    return action

class ConfigTests(unittest.TestCase):
    def test_custom_planner(self):
        self.assertEqual(json.loads((ROOT/'.opencode/opencode.json').read_text())['default_agent'],'build')
        self.assertFalse((ROOT/'.opencode/agents/plan.md').exists())
        self.assertFalse((ROOT/'.opencode/agents/data-plan.md').exists())
        self.assertFalse((ROOT/'.opencode/agents/data-orchestrator.md').exists())
        self.assertTrue((ROOT/'.opencode/agents/product-owner.md').exists())
    def test_builtin_modes_remain_available(self):
        obj=json.loads((ROOT/'.opencode/opencode.json').read_text())
        self.assertNotIn('build',obj.get('agent',{}))
        self.assertFalse((ROOT/'.opencode/agents/build.md').exists())
        self.assertFalse((ROOT/'.opencode/agents/plan.md').exists())
        self.assertEqual(load_agent('product-owner')['mode'],'primary')

    def test_official_skills_replaces_custom_dbt_and_keeps_quality(self):
        self.assertFalse((ROOT/'.opencode/skills/dbt-fido-model').exists())
        self.assertTrue((ROOT/'.opencode/rules/dbt-standards.md').exists())
        self.assertTrue((ROOT/'.opencode/skills/transformation-quality/SKILL.md').exists())
        ae=load_agent('analytics-engineer')['permission']['skill']
        self.assertNotIn('dbt-fido-model',ae)
        self.assertEqual(ae['dbt-creating-dbt-models'],'allow')
        self.assertEqual(ae['dbt-testing-dbt-models'],'allow')
        de=load_agent('data-engineer')['permission']['skill']
        self.assertEqual(de['dagster-expert'],'allow')
        da=load_agent('data-analyst')['permission']['skill']
        self.assertEqual(da['marimo-pair'],'allow')
        self.assertFalse((ROOT/'.opencode/tools/altimate/install-skills.mjs').exists())

    def test_only_motherduck_mcp(self):
        obj=json.loads((ROOT/'.opencode/opencode.json').read_text())
        self.assertEqual(set(obj['mcp']), {'motherduck'})
        self.assertTrue(obj['mcp']['motherduck']['enabled'])
        for agent in (ROOT/'.opencode/agents').glob('*.md'):
            rules=load_agent(agent.stem)['permission']
            self.assertFalse(any(k.startswith('dlt*') for k in rules),agent.name)

    def test_dlt_cli_first_skills_do_not_require_external_mcp(self):
        for name in ['dlt-setup-secrets','dlt-toolkit-dispatch','dlt-create-filesystem-pipeline','dlt-create-rest-api-pipeline','dlt-create-sql-database-pipeline','dlt-validate-data']:
            skill=(ROOT/'.opencode/skills'/name/'SKILL.md').read_text()
            self.assertNotIn('dlt-workspace-mcp',skill,name)
            self.assertNotIn('secrets_update_fragment',skill,name)
        self.assertIn('Azure Blob', (ROOT/'.opencode/rules/dlt-workflows.md').read_text())

    def test_whole_analyst_workspace_is_ignored(self):
        rules=(ROOT/'.opencode/.gitignore.snippet').read_text().splitlines()
        self.assertIn('/analysis/',rules)
        self.assertIn('/.analysis/',rules)
        self.assertIn('analysis/**',load_agent('data-analyst')['permission']['edit'])
        self.assertEqual(load_agent('data-analyst')['permission']['bash']['git add*'],'deny')
        self.assertEqual(load_agent('data-analyst')['permission']['bash']['git commit*'],'deny')
        text=(ROOT/'.opencode/rules/notebooks.md').read_text()
        self.assertIn('entire workspace is Git-ignored',text)
        self.assertIn('do not commit notebooks',text)

    def test_orchestrator_paths(self):
        p=ROOT/'.opencode/agents/product-owner.md'
        t=p.read_text()
        self.assertIn('mode: primary',t)
        self.assertIn('Investigation path',t)
        self.assertIn('Engineering change path',t)
        self.assertIn('No formal engineering plan',t)
        self.assertIn('invoke `reviewer`',t)
        for name in ['explore','notebook']:
            c=(ROOT/'.opencode/commands'/f'{name}.md').read_text()
            self.assertIn('agent: data-analyst',c)
        self.assertIn('approval',t)
        self.assertIn('Product Owner',t)
        self.assertIn('user approval',t)

    def test_no_stale_coordinator_in_active_configuration(self):
        for base in ['AGENTS.md','.opencode/opencode.json']:
            self.assertNotIn('data-plan',(ROOT/base).read_text(),base)
            self.assertNotIn('data-orchestrator',(ROOT/base).read_text(),base)
        for folder in ['.opencode/agents','.opencode/commands','.opencode/rules','.opencode/skills','.agents/skills']:
            for path in (ROOT/folder).rglob('*'):
                if path.is_file() and path.suffix in {'.md','.json'}:
                    self.assertNotIn('data-plan',path.read_text(),str(path))
                    self.assertNotIn('data-orchestrator',path.read_text(),str(path))

    def test_eight_custom_roles(self): self.assertEqual(len(list((ROOT/'.opencode/agents').glob('*.md'))),8)
    def test_analyst_root_only(self):
        p=load_agent('data-analyst')['permission']['edit']
        self.assertEqual(permits(p,'analysis/a.py'),'allow')
        self.assertEqual(permits(p,'transformation/a.sql'),'deny')
    def test_analytics_independent(self):
        p=load_agent('analytics-engineer')['permission']['edit']
        self.assertEqual(permits(p,'analysis/a.py'),'deny')
        self.assertEqual(permits(p,'transformation/models/a.sql'),'allow')
        self.assertEqual(permits(p,'transformation/guides/db/a/guide.md'),'allow')
        self.assertEqual(permits(p,'transformation/guides/sync.sh'),'deny')
    def test_planner_context(self):
        p=load_agent('product-owner')['permission']
        self.assertEqual(p['motherduck*get_query_guide'],'allow')
        self.assertEqual(p['motherduck*query'],'ask')
        self.assertEqual(permits(p['edit'],'transformation/models/a.sql'),'deny')
    def test_no_guide_mutation_override(self):
        for path in (ROOT/'.opencode/agents').glob('*.md'):
            p=load_agent(path.stem)['permission']
            for key,value in p.items():
                if any(x in key for x in ['create_guide','update_guide','edit_guide_content']):
                    self.assertEqual(value,'deny')
    def test_guide_commands_no_publication(self):
        t=(ROOT/'.opencode/commands/guide-publish.md').read_text()
        self.assertIn('does NOT publish',t)
    def test_obsolete_guide_tree_removed(self):
        self.assertFalse((ROOT/'documentation/warehouse-guides').exists())
        self.assertFalse((ROOT/'tools/guides').exists())
    def test_quality_owner(self):
        de=load_agent('data-engineer')['permission']['skill']
        ae=load_agent('analytics-engineer')['permission']['skill']
        self.assertEqual(de['dlt-setup-data-quality'],'allow')
        self.assertNotIn('dlt-setup-data-quality',ae)
        self.assertEqual(ae['transformation-quality'],'allow')
    def test_runtime_eligible_roles(self):
        for p in (ROOT/'.opencode/agents').glob('*.md'):
            bash=load_agent(p.stem)['permission'].get('bash',{})
            value=bash.get('python .opencode/tools/dbt/run.py*') if isinstance(bash,dict) else bash
            if p.stem=='analytics-engineer': self.assertEqual(value,'ask')
            else: self.assertNotEqual(value,'allow')
    def test_reviewer_no_edit(self): self.assertEqual(load_agent('reviewer')['permission']['edit'],'deny')
    def test_policy_disabled(self):
        p=json.loads((ROOT/'.opencode/tools/dbt/agent-policy.example.json').read_text())
        self.assertFalse(p['enabled']); self.assertFalse(p['boundary_verified_by_user'])
    def test_no_stale_notebook_path_in_active_config(self):
        for base in ['.opencode/agents','.opencode/commands','.opencode/rules','.opencode/skills']:
            for p in (ROOT/base).rglob('*'):
                if p.is_file() and p.suffix in {'.md','.json','.py'}:
                    self.assertNotIn('transformation/analysis',p.read_text(),str(p))
    def test_all_frontmatter_parses(self):
        for folder in ['.opencode/agents','.opencode/commands','.opencode/skills','.agents/skills']:
            for p in (ROOT/folder).rglob('*.md'):
                t=p.read_text()
                if t.startswith('---\n'): self.assertIsInstance(yaml.safe_load(t.split('---',2)[1]),dict)
    def test_commands_use_existing_agents(self):
        names={p.stem for p in (ROOT/'.opencode/agents').glob('*.md')}|{'plan','build'}
        for p in (ROOT/'.opencode/commands').glob('*.md'):
            h=yaml.safe_load(p.read_text().split('---',2)[1])
            self.assertIn(h['agent'],names)
    def test_no_generic_guide_validator_in_active_instructions(self):
        for folder in ['.opencode/agents','.opencode/commands','.opencode/rules','.opencode/skills']:
            for p in (ROOT/folder).rglob('*.md'):
                self.assertNotIn('tools/guides/check.mjs',p.read_text())
    def test_direct_dbt_denied(self):
        p=json.loads((ROOT/'.opencode/opencode.json').read_text())['permission']['bash']
        self.assertEqual(permits(p,'dbt build --target prod'),'deny')
        self.assertEqual(permits(p,'python .opencode/tools/dbt/run.py build'),'deny')
    def test_no_unverified_dlt_bug_workaround(self):
        for name in ['dlt-setup-data-quality','dlt-define-data-quality-checks','dlt-run-data-quality','dlt-review-data-quality']:
            t=(ROOT/'.opencode/skills'/name/'SKILL.md').read_text()
            self.assertNotIn('dlt license issue',t)
            self.assertNotIn('h["args"]["columns"][0]',t)

if __name__=='__main__': unittest.main()
