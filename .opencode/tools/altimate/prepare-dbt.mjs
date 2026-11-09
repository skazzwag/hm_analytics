#!/usr/bin/env node
/** Prepare compiled SQL plus warehouse-derived column metadata; does not invoke dbt. */
import { mkdirSync, writeFileSync } from 'node:fs';
import { resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';
import { createHash } from 'node:crypto';
import { readInput, assertCompiledSql, assertSchema } from './analyze.mjs';
import { verifyArtifacts, sha256 } from './freshness.mjs';

export function findModel(manifest, selector) {
  const nodes = manifest.nodes ?? {};
  if (nodes[selector]?.resource_type === 'model') return [selector, nodes[selector]];
  const matches = Object.entries(nodes).filter(([, node]) => node.resource_type === 'model' && node.name === selector);
  if (matches.length !== 1) {
    throw new Error(`Expected exactly one model named '${selector}', got ${matches.length}. Use its full model.package.name unique_id.`);
  }
  return matches[0];
}

function relationParts(node) {
  return [node.database, node.schema, node.identifier || node.alias || node.name].filter((x) => x != null && x !== '');
}
function safeParts(parts) {
  if (!parts.length || parts.some((x) => typeof x !== 'string' || /[."`\[\]]/.test(x))) {
    throw new Error(`This conservative converter does not support relation components containing dots or quote characters: ${JSON.stringify(parts)}. Supply a reviewed schema manually.`);
  }
  return parts;
}

export function prepare(manifest, catalog, selector) {
  if (!manifest || typeof manifest !== 'object' || !catalog || typeof catalog !== 'object') {
    throw new Error('Both manifest and catalog must be JSON objects.');
  }
  if (manifest.metadata?.adapter_type && manifest.metadata.adapter_type !== 'duckdb') {
    throw new Error(`This starter targets dbt-duckdb/MotherDuck, not '${manifest.metadata.adapter_type}'.`);
  }
  if (Array.isArray(catalog.errors) ? catalog.errors.length : catalog.errors) {
    throw new Error('Catalog contains errors. Regenerate/fix catalog metadata before analysis.');
  }
  const [uid, model] = findModel(manifest, selector);
  if (model.language && model.language !== 'sql') throw new Error('Only SQL dbt models are supported.');
  const sql = (model.compiled_code || model.compiled_sql || '').trimEnd() + '\n';
  assertCompiledSql(sql);
  const resources = { ...(manifest.nodes ?? {}), ...(manifest.sources ?? {}) };
  const catalogResources = { ...(catalog.nodes ?? {}), ...(catalog.sources ?? {}) };
  const needed = new Set();
  const visited = new Set();
  function visit(id) {
    if (visited.has(id)) return;
    visited.add(id);
    const node = resources[id];
    if (!node) throw new Error(`Dependency '${id}' is missing from the manifest.`);
    if (node.resource_type === 'model' && node.config?.materialized === 'ephemeral') {
      for (const parent of node.depends_on?.nodes ?? []) visit(parent);
    } else if (['model', 'seed', 'snapshot', 'source'].includes(node.resource_type)) {
      needed.add(id);
    } else {
      throw new Error(`Unsupported dependency resource type '${node.resource_type}' for '${id}'.`);
    }
  }
  for (const id of model.depends_on?.nodes ?? []) visit(id);
  // An existing target may be read by an incremental model's compiled SQL.
  if (catalogResources[uid] && model.config?.materialized !== 'ephemeral') needed.add(uid);

  const candidates = new Map();
  const relations = [];
  for (const id of [...needed].sort()) {
    const node = resources[id];
    const observed = catalogResources[id];
    if (!observed) throw new Error(`No catalog entry for '${id}'. Build/inspect upstream dev relations and regenerate catalog; do not infer missing columns from YAML.`);
    const parts = safeParts(relationParts(node));
    const expected = { database: node.database, schema: node.schema, name: node.identifier || node.alias || node.name };
    for (const [field, value] of Object.entries(expected)) {
      if (value == null || value === '') continue;
      const actual = observed.metadata?.[field];
      if (actual == null || String(actual).toLowerCase() !== String(value).toLowerCase()) {
        throw new Error(`Catalog/manifest relation mismatch for '${id}', ${field}: expected '${value}', got '${actual}'. Use the same dbt target for both artifacts.`);
      }
    }
    const rawColumns = observed.columns;
    const columns = (Array.isArray(rawColumns) ? rawColumns : Object.values(rawColumns ?? {}))
      .map((col) => ({ name: col.name, type: col.type }));
    const canonical = parts.join('.');
    if (relations.some((r) => r.name.toLowerCase() === canonical.toLowerCase())) {
      throw new Error(`Two resources resolve to '${canonical}'. Review relation identity before tracing.`);
    }
    const table = { columns };
    assertSchema({ tables: { [canonical]: table } });
    relations.push({ unique_id: id, name: canonical, column_count: columns.length });
    // Full relation plus unambiguous schema.table/table aliases. Ambiguous short
    // aliases are omitted, never overwritten. Verify qualification on real SQL.
    for (let start = 0; start < parts.length; start++) {
      const alias = parts.slice(start).join('.');
      const key = alias.toLowerCase();
      if (!candidates.has(key)) candidates.set(key, []);
      candidates.get(key).push({ alias, id, table, canonical: start === 0 });
    }
  }
  const tables = Object.create(null);
  const omittedAliases = [];
  for (const [key, options] of candidates.entries()) {
    if (new Set(options.map((o) => o.id)).size > 1) {
      if (options.some((o) => o.canonical)) throw new Error(`Qualified schema-key collision for '${key}'.`);
      omittedAliases.push(key);
    } else {
      tables[options[0].alias] = options[0].table;
    }
  }
  const schema = { version: '1', tables };
  assertSchema(schema);
  return { sql, schema, metadata: {
    model_unique_id: uid, model_name: model.name,
    dialect: 'duckdb', compiled_sql_sha256: createHash('sha256').update(sql).digest('hex'),
    manifest_generated_at: manifest.metadata?.generated_at ?? null,
    catalog_generated_at: catalog.metadata?.generated_at ?? null,
    schema_source: 'catalog.json; no invented types or manifest-column fallback',
    relations, omitted_ambiguous_aliases: omittedAliases,
    scope: 'one compiled model; upstream ephemeral dependencies expanded',
    caveats: [
      'Artifact freshness and completeness are not proven by this converter. Compile after edits and regenerate catalog after upstream schema changes.',
      'Hard-coded SQL relations, external files/table functions, and undocumented dependencies may be absent. Review actual SQL and engine errors.',
      'No cross-model graph stitching or dlt/Python/Dagster lineage is performed.',
      'Qualified identifier resolution and DuckDB-specific types must pass a real-project test against the installed native engine.',
    ],
  } };
}

function main(argv) {
  const { values } = parseArgs({ args: argv, options: {
    manifest: { type: 'string' }, catalog: { type: 'string' }, model: { type: 'string' },
    out: { type: 'string' }, 'project-root': { type: 'string' }, help: { type: 'boolean', short: 'h' },
  } });
  if (values.help) {
    console.log('Usage: node tools/altimate/prepare-dbt.mjs --project-root transformation --manifest transformation/target/manifest.json --catalog transformation/target/catalog.json --model NAME --out .analysis/NAME');
    return;
  }
  for (const name of ['manifest', 'catalog', 'model', 'out', 'project-root']) if (!values[name]) throw new Error(`--${name} is required.`);
  const manifestText = readInput(values.manifest, '.json');
  const catalogText = readInput(values.catalog, '.json');
  const manifest = JSON.parse(manifestText);
  const catalog = JSON.parse(catalogText);
  const [uid] = findModel(manifest, values.model);
  const freshness = verifyArtifacts({manifest, catalog, projectRoot: values['project-root'], modelUniqueId: uid});
  const result = prepare(manifest, catalog, values.model);
  result.metadata.freshness = freshness;
  result.metadata.manifest_sha256 = sha256(manifestText);
  result.metadata.catalog_sha256 = sha256(catalogText);
  result.metadata.schema_definition_sha256 = sha256(JSON.stringify(result.schema));
  const directory = resolve(values.out);
  mkdirSync(directory, { recursive: true });
  writeFileSync(join(directory, 'model.sql'), result.sql.trimEnd() + '\n');
  writeFileSync(join(directory, 'schema.json'), JSON.stringify(result.schema, null, 2) + '\n');
  writeFileSync(join(directory, 'metadata.json'), JSON.stringify(result.metadata, null, 2) + '\n');
  console.log(JSON.stringify({ status: 'prepared', output_directory: directory, ...result.metadata }, null, 2));
}
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try { main(process.argv.slice(2)); }
  catch (error) { console.log(JSON.stringify({ status: 'inconclusive', error: error.message }, null, 2)); process.exitCode = 2; }
}
