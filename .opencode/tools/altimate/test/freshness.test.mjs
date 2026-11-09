import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync, utimesSync, rmSync, symlinkSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { verifyArtifacts } from '../freshness.mjs';
function fixture(t){
 const root=mkdtempSync(join(tmpdir(),'fido-artifacts-'));
 t.after(()=>rmSync(root,{recursive:true,force:true}));
 mkdirSync(join(root,'models'));const sql='select 1 as id\n';
 const path=join(root,'models','example.sql');writeFileSync(path,sql);
 const old=new Date(Date.now()-60000);utimesSync(path,old,old);
 return {root,path,sql,manifest:{metadata:{generated_at:new Date(Date.now()-30000).toISOString()},nodes:{'model.p.example':{original_file_path:'models/example.sql',raw_code:sql}}},catalog:{metadata:{generated_at:new Date(Date.now()-30000).toISOString()}}};
}
function check(f){return verifyArtifacts({manifest:f.manifest,catalog:f.catalog,projectRoot:f.root,modelUniqueId:'model.p.example'});}
test('accepts matching source and older project inputs',t=>{const f=fixture(t);assert.equal(check(f).status,'local_source_checks_passed');});
test('rejects changed raw source',t=>{const f=fixture(t);writeFileSync(f.path,'select 2 as id');assert.throws(()=>check(f),/differs/);});
test('rejects newly changed YAML',t=>{const f=fixture(t);writeFileSync(join(f.root,'models','schema.yml'),'models: []');assert.throws(()=>check(f),/newer/);});
test('requires artifact timestamps',t=>{const f=fixture(t);delete f.catalog.metadata.generated_at;assert.throws(()=>check(f),/generated_at/);});
test('requires raw source',t=>{const f=fixture(t);delete f.manifest.nodes['model.p.example'].raw_code;assert.throws(()=>check(f),/raw_code/);});
test('rejects source path escape',t=>{const f=fixture(t);f.manifest.nodes['model.p.example'].original_file_path='../secret.sql';assert.throws(()=>check(f),/within/);});
test('rejects symlink input',t=>{const f=fixture(t);symlinkSync(f.path,join(f.root,'models','alias.sql'));assert.throws(()=>check(f),/Symlink/);});
test('skips credential-like files and generated directories',t=>{const f=fixture(t);writeFileSync(join(f.root,'profiles.yml'),'DO NOT READ');mkdirSync(join(f.root,'target'));writeFileSync(join(f.root,'target','compiled.sql'),'new');assert.equal(check(f).inspected_project_file_count,1);});
test('rejects future timestamp',t=>{const f=fixture(t);f.manifest.metadata.generated_at=new Date(Date.now()+3600000).toISOString();assert.throws(()=>check(f),/future/);});
