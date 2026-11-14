#!/usr/bin/env node
/**
 * Local, on-demand adapter; no agent, model call, or warehouse connection here.
 * API references: AltimateAI/altimate-code, native/altimate-core.ts and
 * native/dbt/lineage.ts. See README.md for validation limits.
 */
import { readFileSync, statSync } from 'node:fs';
import { resolve, extname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
import { createHash } from 'node:crypto';
import { parseArgs } from 'node:util';

const require = createRequire(import.meta.url);
const HELP = `Usage:
  node tools/altimate/analyze.mjs self-test
  node tools/altimate/analyze.mjs check --sql FILE.sql --schema FILE.json
  node tools/altimate/analyze.mjs lineage --sql FILE.sql --schema FILE.json [--dialect duckdb]

JSON goes to stdout. Exit 0: completed (check: no error-severity findings).
Exit 1: validation/safety/error-severity lint findings. Exit 2: inconclusive,
missing input/dependency, unsupported API, or analysis failure.
A successful lineage invocation is NOT a completeness or correctness guarantee.
The --dialect option applies to lineage only; validate/lint use the engine's own
parser/planner and expose no dialect argument in the source API used here.
`;

export function readInput(filename, extension, maxBytes = 64 * 1024 * 1024) {
  if (!filename) throw new Error(`A ${extension} input path is required.`);
  const path = resolve(filename);
  if (extname(path).toLowerCase() !== extension) {
    throw new Error(`Expected a ${extension} file: ${path}`);
  }
  const stat = statSync(path);
  if (!stat.isFile() || stat.size > maxBytes) {
    throw new Error(`Input must be a regular file no larger than ${maxBytes} bytes: ${path}`);
  }
  return readFileSync(path, 'utf8');
}

export function assertSchema(definition) {
  if (!definition || typeof definition !== 'object' || Array.isArray(definition) ||
      !definition.tables || typeof definition.tables !== 'object' || Array.isArray(definition.tables)) {
    throw new Error('Schema must be an object with a tables map; this is not a raw dbt schema.yml.');
  }
  for (const [name, table] of Object.entries(definition.tables)) {
    if (!name || !Array.isArray(table?.columns) || table.columns.length === 0) {
      throw new Error(`Missing columns for schema relation '${name}'.`);
    }
    const seen = new Set();
    for (const col of table.columns) {
      if (typeof col.name !== 'string' || !col.name.trim() ||
          typeof col.type !== 'string' || !col.type.trim()) {
        throw new Error(`Missing column name or type in '${name}'; types must not be invented.`);
      }
      const key = col.name.toLowerCase();
      if (seen.has(key)) throw new Error(`Duplicate column '${col.name}' in '${name}'.`);
      seen.add(key);
    }
  }
}

export function assertCompiledSql(sql) {
  if (!sql.trim()) throw new Error('SQL input is empty.');
  if (/\{\{|\{%/.test(sql)) {
    throw new Error('Possible uncompiled Jinja found. Supply compiled SQL, or review a literal containing Jinja markers.');
  }
}

function engineFailure(result, label) {
  if (!result || typeof result !== 'object') throw new Error(`${label}: unexpected engine result.`);
  if (result.error || result.parse_error || result.success === false) {
    throw new Error(`${label}: ${result.error ?? result.parse_error ?? 'engine reported failure'}`);
  }
}

export function interpretCheck(validation, lint, safety) {
  for (const [name, value] of Object.entries({ validation, lint, safety })) engineFailure(value, name);
  if (typeof validation.valid !== 'boolean' || typeof safety.safe !== 'boolean') {
    throw new Error('Unexpected validation/safety result shape; update this adapter before trusting results.');
  }
  const findings = lint.findings ?? lint.violations;
  if (!Array.isArray(findings)) throw new Error('Unexpected lint result shape; expected findings or violations array.');
  const hasLintError = findings.some((f) => /^(error|high|critical|fatal)$/i.test(String(f.severity ?? '')));
  return { exitCode: (!validation.valid || !safety.safe || hasLintError) ? 1 : 0, findings };
}

export function assertLineage(result) {
  engineFailure(result, 'lineage');
  const hasMappings = result.column_dict && typeof result.column_dict === 'object' &&
    Object.keys(result.column_dict).length > 0;
  const hasEdges = Array.isArray(result.column_lineage) && result.column_lineage.length > 0;
  if (!hasMappings && !hasEdges) {
    throw new Error('No recognized lineage mappings/edges returned. This can be legitimate for constants, but is inconclusive here; do not report "no dependencies".');
  }
}

function loadEngine() {
  let core;
  try { core = require('@altimateai/altimate-core'); }
  catch (error) {
    throw new Error(`Cannot load Altimate native package. Run npm install inside tools/altimate on this WSL Linux installation. Do not copy Windows node_modules. Original: ${error.message}`);
  }
  for (const name of ['validate', 'lint', 'scanSql', 'columnLineage']) {
    if (typeof core[name] !== 'function') throw new Error(`Installed core does not export ${name}.`);
  }
  if (typeof core.Schema?.fromJson !== 'function') throw new Error('Installed core does not export Schema.fromJson.');
  return core;
}

export async function perform(core, command, sql, definition, dialect = 'duckdb') {
  assertCompiledSql(sql);
  assertSchema(definition);
  const schema = core.Schema.fromJson(JSON.stringify(definition));
  const fingerprint = createHash('sha256').update(sql).digest('hex');
  const schemaFingerprint = createHash('sha256').update(JSON.stringify(definition)).digest('hex');
  if (command === 'lineage') {
    const lineage = await core.columnLineage(sql, dialect, schema);
    assertLineage(lineage);
    return { exitCode: 0, report: {
      status: 'computed', scope: 'single-compiled-query', dialect,
      sql_sha256: fingerprint, schema_definition_sha256: schemaFingerprint, completeness: 'not_independently_verified', lineage,
    } };
  }
  if (command !== 'check') throw new Error(`Unknown command '${command}'.`);
  const validation = await core.validate(sql, schema);
  const lint = await core.lint(sql, schema);
  const safety = await core.scanSql(sql);
  const { exitCode } = interpretCheck(validation, lint, safety);
  return { exitCode, report: {
    status: exitCode ? 'findings' : 'completed', sql_sha256: fingerprint, schema_definition_sha256: schemaFingerprint,
    validation, lint, safety,
    caveat: 'Static checks only. A completed report can still contain warnings; it does not prove DuckDB runtime correctness or business semantics.',
  } };
}

async function smoke(core) {
  const definition = { version: '1', tables: { orders: { columns: [
    { name: 'order_id', type: 'INTEGER' }, { name: 'amount', type: 'DOUBLE' },
  ] } } };
  const sql = 'SELECT order_id, amount * 100 AS amount_cents FROM orders';
  const checked = await perform(core, 'check', sql, definition);
  if (checked.report.validation.valid !== true || checked.report.safety.safe !== true) {
    throw new Error(`Smoke test: valid query rejected: ${JSON.stringify(checked.report)}`);
  }
  const invalid = await perform(core, 'check', 'SELECT no_such_column FROM orders', definition);
  if (invalid.report.validation.valid !== false || invalid.exitCode !== 1) {
    throw new Error('Smoke test: nonexistent-column query was not rejected.');
  }
  const traced = await perform(core, 'lineage', sql, definition, 'duckdb');
  const serialized = JSON.stringify(traced.report.lineage).toLowerCase();
  for (const token of ['orders', 'order_id', 'amount', 'amount_cents']) {
    if (!serialized.includes(token)) throw new Error(`Smoke test: lineage did not include '${token}'.`);
  }
  return { status: 'smoke_checks_passed', invalid_column_was_rejected: true,
    expected_mapping_to_inspect: { order_id: ['orders.order_id'], amount_cents: ['orders.amount'] },
    actual_lineage: traced.report.lineage,
    caveat: 'Smoke checks verify API behavior and presence of column names, not general lineage accuracy. Inspect the actual mappings and test a real compiled model next.',
  };
}

async function main(argv) {
  const { values, positionals } = parseArgs({ args: argv, allowPositionals: true, options: {
    sql: { type: 'string' }, schema: { type: 'string' }, dialect: { type: 'string', default: 'duckdb' },
    help: { type: 'boolean', short: 'h' },
  } });
  if (values.help || positionals.length === 0) { console.log(HELP); return; }
  if (positionals.length !== 1 || !['self-test', 'check', 'lineage'].includes(positionals[0])) {
    throw new Error(HELP);
  }
  const command = positionals[0];
  // Validate files before loading the native dependency; errors remain actionable offline.
  let sql, definition;
  if (command !== 'self-test') {
    sql = readInput(values.sql, '.sql', 8 * 1024 * 1024);
    definition = JSON.parse(readInput(values.schema, '.json'));
    assertCompiledSql(sql); assertSchema(definition);
  }
  const core = loadEngine();
  if (command === 'self-test') { console.log(JSON.stringify(await smoke(core), null, 2)); return; }
  const result = await perform(core, command, sql, definition, values.dialect);
  console.log(JSON.stringify(result.report, null, 2));
  process.exitCode = result.exitCode;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main(process.argv.slice(2)).catch((error) => {
    console.log(JSON.stringify({ status: 'inconclusive', error: error.message }, null, 2));
    process.exitCode = 2;
  });
}
