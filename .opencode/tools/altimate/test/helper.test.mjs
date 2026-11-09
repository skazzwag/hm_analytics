import test from 'node:test';
import assert from 'node:assert/strict';
import { assertSchema, assertCompiledSql, interpretCheck, assertLineage, perform } from '../analyze.mjs';
import { findModel, prepare } from '../prepare-dbt.mjs';

const copy = (x) => structuredClone(x);
const columns = [{ name: 'order_id', type: 'INTEGER' }, { name: 'amount', type: 'DOUBLE' }];
const schema = { version: '1', tables: { orders: { columns } } };
const uid = 'model.demo.fct_orders';
const sourceId = 'source.demo.raw.orders';
const manifest = {
  metadata: { adapter_type: 'duckdb', generated_at: '2026-09-18T00:00:00Z' },
  nodes: { [uid]: { name: 'fct_orders', resource_type: 'model', language: 'sql',
    database: 'analytics', schema: 'main', alias: 'fct_orders',
    compiled_code: 'SELECT order_id, amount FROM analytics.raw.orders',
    config: { materialized: 'table' }, depends_on: { nodes: [sourceId] } } },
  sources: { [sourceId]: { name: 'orders_logical', identifier: 'orders', resource_type: 'source',
    database: 'analytics', schema: 'raw' } },
};
const catalog = { metadata: { generated_at: '2026-09-18T00:00:00Z' }, errors: [], nodes: {},
  sources: { [sourceId]: { metadata: { database: 'analytics', schema: 'raw', name: 'orders' },
    columns: Object.fromEntries(columns.map((c) => [c.name, c])) } } };

test('schema accepts typed columns and rejects raw dbt YAML-shaped JSON', () => {
  assert.doesNotThrow(() => assertSchema(schema));
  assert.throws(() => assertSchema({ models: [] }), /tables map/);
});
test('missing type cannot become invented VARCHAR', () => {
  assert.throws(() => assertSchema({ tables: { t: { columns: [{ name: 'id' }] } } }), /invented/);
});
test('empty column sets fail', () => {
  assert.throws(() => assertSchema({ tables: { t: { columns: [] } } }), /Missing columns/);
});
test('case-insensitive duplicate columns fail', () => {
  assert.throws(() => assertSchema({ tables: { t: { columns: [{ name: 'ID', type: 'INT' }, { name: 'id', type: 'INT' }] } } }), /Duplicate/);
});
test('empty SQL or Jinja is rejected', () => {
  assert.throws(() => assertCompiledSql(''), /empty/);
  assert.throws(() => assertCompiledSql("select * from {{ ref('a') }}"), /Jinja/);
});
test('clean check passes and advisory warnings remain nonblocking', () => {
  assert.equal(interpretCheck({ valid: true }, { findings: [] }, { safe: true }).exitCode, 0);
  assert.equal(interpretCheck({ valid: true }, { findings: [{ severity: 'warning' }] }, { safe: true }).exitCode, 0);
});
test('engine operation success does not override invalid SQL', () => {
  assert.equal(interpretCheck({ success: true, valid: false }, { findings: [] }, { safe: true }).exitCode, 1);
});
test('unsafe SQL and error lint each fail checks', () => {
  assert.equal(interpretCheck({ valid: true }, { findings: [] }, { safe: false }).exitCode, 1);
  assert.equal(interpretCheck({ valid: true }, { findings: [{ severity: 'Error' }] }, { safe: true }).exitCode, 1);
});
test('unknown result shape is inconclusive, not a clean pass', () => {
  assert.throws(() => interpretCheck({ success: true }, { findings: [] }, { safe: true }), /shape/);
  assert.throws(() => interpretCheck({ valid: true }, {}, { safe: true }), /shape/);
});
test('parser errors are not silently dropped', () => {
  assert.throws(() => interpretCheck({ valid: true }, { findings: [], parse_error: 'unsupported' }, { safe: true }), /unsupported/);
});
test('empty lineage is not proof of no dependencies', () => {
  assert.throws(() => assertLineage({ column_dict: {}, column_lineage: [] }), /inconclusive/);
  assert.throws(() => assertLineage({ error: 'unsupported syntax' }), /unsupported/);
});
test('recognized lineage structures accepted', () => {
  assert.doesNotThrow(() => assertLineage({ column_dict: { id: ['t.id'] } }));
  assert.doesNotThrow(() => assertLineage({ column_lineage: [{ source: 't.id', target: 'id' }] }));
});
test('adapter invokes real API signatures (mock core, not native engine)', async () => {
  const calls = [];
  const core = {
    Schema: { fromJson: (x) => { calls.push(['schema', JSON.parse(x)]); return 'schema-handle'; } },
    validate: async (s, c) => { calls.push(['validate', s, c]); return { valid: true }; },
    lint: (s, c) => { calls.push(['lint', s, c]); return { findings: [] }; },
    scanSql: (s) => { calls.push(['safety', s]); return { safe: true }; },
    columnLineage: (s, d, c) => { calls.push(['lineage', s, d, c]); return { column_dict: { order_id: ['orders.order_id'] } }; },
  };
  assert.equal((await perform(core, 'check', 'SELECT order_id FROM orders', schema)).exitCode, 0);
  const result = await perform(core, 'lineage', 'SELECT order_id FROM orders', schema);
  assert.equal(result.report.scope, 'single-compiled-query');
  assert.deepEqual(calls.at(-1), ['lineage', 'SELECT order_id FROM orders', 'duckdb', 'schema-handle']);
});
test('model selection supports exact IDs and unique names', () => {
  assert.equal(findModel(manifest, uid)[0], uid);
  assert.equal(findModel(manifest, 'fct_orders')[0], uid);
});
test('ambiguous model selection requires full ID', () => {
  const m = copy(manifest); m.nodes['model.other.fct_orders'] = copy(m.nodes[uid]);
  assert.throws(() => findModel(m, 'fct_orders'), /exactly one/);
});
test('prepare uses catalog, source identifier and qualified aliases', () => {
  const result = prepare(manifest, catalog, 'fct_orders');
  assert.deepEqual(result.schema.tables['analytics.raw.orders'].columns, columns);
  assert.deepEqual(result.schema.tables['raw.orders'].columns, columns);
  assert.deepEqual(result.schema.tables.orders.columns, columns);
  assert.equal(result.sql.endsWith('\n'), true);
});
test('catalog column arrays also accepted', () => {
  const c = copy(catalog); c.sources[sourceId].columns = copy(columns);
  assert.equal(prepare(manifest, c, uid).schema.tables.orders.columns.length, 2);
});
test('missing upstream metadata is not replaced with manifest column guesses', () => {
  const c = copy(catalog); delete c.sources[sourceId];
  assert.throws(() => prepare(manifest, c, uid), /No catalog entry/);
});
test('different target artifacts fail', () => {
  const c = copy(catalog); c.sources[sourceId].metadata.database = 'production';
  assert.throws(() => prepare(manifest, c, uid), /mismatch/);
});
test('catalog errors fail', () => {
  const c = copy(catalog); c.errors = ['metadata query failed'];
  assert.throws(() => prepare(manifest, c, uid), /Catalog contains errors/);
});
test('ephemeral model expands to physical source, not fake table', () => {
  const m = copy(manifest);
  m.nodes[uid].depends_on.nodes = ['model.demo.eph'];
  m.nodes['model.demo.eph'] = { name: 'eph', resource_type: 'model', config: { materialized: 'ephemeral' }, depends_on: { nodes: [sourceId] } };
  const result = prepare(m, catalog, uid);
  assert.equal(result.metadata.relations.length, 1);
  assert.equal(result.schema.tables.eph, undefined);
});
test('colliding short table names are omitted rather than overwritten', () => {
  const m = copy(manifest), c = copy(catalog);
  const other = 'source.demo.other.orders';
  m.sources[other] = { ...copy(m.sources[sourceId]), schema: 'other' };
  m.nodes[uid].depends_on.nodes.push(other);
  c.sources[other] = { ...copy(c.sources[sourceId]), metadata: { database: 'analytics', schema: 'other', name: 'orders' } };
  const result = prepare(m, c, uid);
  assert.equal(result.schema.tables.orders, undefined);
  assert.ok(result.schema.tables['analytics.raw.orders']);
  assert.ok(result.schema.tables['analytics.other.orders']);
  assert.deepEqual(result.metadata.omitted_ambiguous_aliases, ['orders']);
});
test('existing incremental target included in schema', () => {
  const m = copy(manifest), c = copy(catalog);
  m.nodes[uid].config.materialized = 'incremental';
  c.nodes[uid] = { metadata: { database: 'analytics', schema: 'main', name: 'fct_orders' }, columns: copy(columns) };
  assert.ok(prepare(m, c, uid).schema.tables['analytics.main.fct_orders']);
});
test('unsupported types are preserved for engine to accept or reject', () => {
  const c = copy(catalog); c.sources[sourceId].columns.amount.type = 'STRUCT(value INTEGER)';
  assert.equal(prepare(manifest, c, uid).schema.tables.orders.columns[1].type, 'STRUCT(value INTEGER)');
});
test('converter rejects unsupported adapters, Python models and identifier shapes', () => {
  let m = copy(manifest); m.metadata.adapter_type = 'snowflake';
  assert.throws(() => prepare(m, catalog, uid), /dbt-duckdb/);
  m = copy(manifest); m.nodes[uid].language = 'python';
  assert.throws(() => prepare(m, catalog, uid), /SQL dbt models/);
  m = copy(manifest); m.sources[sourceId].identifier = 'orders.with.dot';
  assert.throws(() => prepare(m, catalog, uid), /dots or quote/);
});
