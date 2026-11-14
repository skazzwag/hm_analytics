import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, utimesSync, rmSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
const script = fileURLToPath(new URL('../prepare-dbt.mjs', import.meta.url));
function fixture(t) {
  const root = mkdtempSync(join(tmpdir(), 'fido-prepare-cli-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  const project = join(root, 'transformation');
  mkdirSync(join(project, 'models'), { recursive: true });
  mkdirSync(join(project, 'target'));
  const source = join(project, 'models', 'orders.sql');
  const sql = 'select order_id from analytics.raw.orders\n';
  writeFileSync(source, sql);
  const old = new Date(Date.now() - 60000);
  utimesSync(source, old, old);
  const metadata = { adapter_type: 'duckdb', generated_at: new Date(Date.now() - 30000).toISOString() };
  const manifest = { metadata, nodes: { 'model.demo.orders': {
    name: 'orders', resource_type: 'model', original_file_path: 'models/orders.sql',
    raw_code: sql, compiled_code: sql, database: 'analytics', schema: 'main', alias: 'orders',
    config: { materialized: 'table' }, depends_on: { nodes: ['source.demo.raw.orders'] },
  } }, sources: { 'source.demo.raw.orders': {
    name: 'orders', identifier: 'orders', resource_type: 'source', database: 'analytics', schema: 'raw',
  } } };
  const catalog = { metadata, errors: [], nodes: {}, sources: { 'source.demo.raw.orders': {
    metadata: { database: 'analytics', schema: 'raw', name: 'orders' },
    columns: { order_id: { name: 'order_id', type: 'INTEGER' } },
  } } };
  const manifestPath = join(project, 'target', 'manifest.json');
  const catalogPath = join(project, 'target', 'catalog.json');
  writeFileSync(manifestPath, JSON.stringify(manifest));
  writeFileSync(catalogPath, JSON.stringify(catalog));
  const out = join(root, 'output');
  return { source, sql, out, args: [script, '--project-root', project, '--manifest', manifestPath,
    '--catalog', catalogPath, '--model', 'orders', '--out', out] };
}
test('CLI prepares current fixture artifacts and records reproducible hashes', (t) => {
  const f = fixture(t);
  const result = spawnSync(process.execPath, f.args, { encoding: 'utf8' });
  assert.equal(result.status, 0, result.stdout + result.stderr);
  assert.equal(JSON.parse(result.stdout).status, 'prepared');
  const sql = readFileSync(join(f.out, 'model.sql'), 'utf8');
  const schema = JSON.parse(readFileSync(join(f.out, 'schema.json'), 'utf8'));
  const metadata = JSON.parse(readFileSync(join(f.out, 'metadata.json'), 'utf8'));
  assert.equal(sql, f.sql);
  assert.equal(metadata.compiled_sql_sha256, createHash('sha256').update(sql).digest('hex'));
  assert.equal(metadata.schema_definition_sha256, createHash('sha256').update(JSON.stringify(schema)).digest('hex'));
  assert.equal(metadata.freshness.status, 'local_source_checks_passed');
});
test('CLI rejects changed source without creating prepared output', (t) => {
  const f = fixture(t);
  writeFileSync(f.source, 'select missing_column from analytics.raw.orders\n');
  const result = spawnSync(process.execPath, f.args, { encoding: 'utf8' });
  assert.equal(result.status, 2);
  assert.equal(JSON.parse(result.stdout).status, 'inconclusive');
  assert.match(JSON.parse(result.stdout).error, /differs/);
  assert.equal(existsSync(f.out), false);
});
