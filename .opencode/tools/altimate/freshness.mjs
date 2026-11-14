/** Conservative local evidence gate. Does not invoke dbt or connect to a warehouse. */
import { readFileSync, readdirSync, lstatSync, realpathSync } from 'node:fs';
import { resolve, relative, sep, extname, basename } from 'node:path';
import { createHash } from 'node:crypto';

export const sha256 = (value) => createHash('sha256').update(value).digest('hex');
const excluded = new Set(['.git', '.venv', 'node_modules', 'target', 'logs', 'dbt_packages', 'dbt_modules', '.analysis', '.dlt']);
const extensions = new Set(['.sql', '.yml', '.yaml', '.csv']);
function isSecretName(name) {
  return name.startsWith('.env') || /(^|[._-])(secrets?|credentials?|profiles?)([._-]|$)/i.test(name);
}
function timestamp(value, label) {
  const result = typeof value === 'string' ? Date.parse(value) : NaN;
  if (!Number.isFinite(result)) throw new Error(`${label}: missing/invalid generated_at; provenance is required.`);
  if (result > Date.now() + 300000) throw new Error(`${label}: timestamp is in the future; check clock/artifact provenance.`);
  return result;
}
export function projectPath(root, supplied) {
  if (typeof supplied !== 'string' || !supplied) throw new Error('Manifest lacks original_file_path.');
  const path = resolve(root, supplied);
  const rel = relative(root, path);
  if (rel.startsWith('..' + sep) || rel === '..' || rel === '' || resolve(supplied) === supplied) {
    throw new Error('Manifest source path must stay within the project root.');
  }
  const real = realpathSync(path);
  const realRelative = relative(root, real);
  if (realRelative === '..' || realRelative.startsWith('..' + sep)) throw new Error('Source symlink escapes project root.');
  if (isSecretName(basename(path))) throw new Error('Refusing a credential-like source filename.');
  return path;
}

export function verifyArtifacts({ manifest, catalog, projectRoot, modelUniqueId }) {
  const root = realpathSync(resolve(projectRoot));
  const generated = timestamp(manifest.metadata?.generated_at, 'Manifest');
  timestamp(catalog.metadata?.generated_at, 'Catalog');
  const model = manifest.nodes?.[modelUniqueId];
  if (!model) throw new Error(`Model '${modelUniqueId}' is absent from manifest.`);
  if (typeof model.raw_code !== 'string' && typeof model.raw_sql !== 'string') {
    throw new Error('Selected model has no raw_code/raw_sql; cannot compare to current source.');
  }
  const sourcePath = projectPath(root, model.original_file_path);
  const source = readFileSync(sourcePath, 'utf8');
  const normalize = (s) => s.replace(/\r\n/g, '\n').trimEnd();
  if (normalize(source) !== normalize(model.raw_code ?? model.raw_sql)) {
    throw new Error('Selected source differs from the manifest. Request user/CI recompilation; do not trace stale SQL.');
  }
  const files = [];
  let bytes = 0;
  function walk(directory) {
    for (const entry of readdirSync(directory, { withFileTypes: true }).sort((a,b) => a.name.localeCompare(b.name))) {
      if (excluded.has(entry.name) || isSecretName(entry.name)) continue;
      const path = resolve(directory, entry.name);
      if (entry.isSymbolicLink()) throw new Error(`Symlink requires manual provenance review: ${relative(root,path)}`);
      if (entry.isDirectory()) { walk(path); continue; }
      if (!entry.isFile() || !extensions.has(extname(entry.name).toLowerCase())) continue;
      const info = lstatSync(path);
      bytes += info.size;
      if (files.length >= 20000 || bytes > 256 * 1024 * 1024) throw new Error('Project snapshot limit exceeded; use a reviewed artifact workflow.');
      if (info.mtimeMs > generated) {
        throw new Error(`Project input is newer than manifest: ${relative(root,path)}. Request refreshed artifacts; do not change timestamps to bypass this check.`);
      }
      files.push({ path: relative(root,path).split(sep).join('/'), sha256: sha256(readFileSync(path)) });
    }
  }
  walk(root);
  return {
    status: 'local_source_checks_passed',
    model_source_path: relative(root,sourcePath).split(sep).join('/'),
    model_source_sha256: sha256(source),
    project_snapshot_sha256: sha256(JSON.stringify(files)),
    inspected_project_file_count: files.length,
    checked_at: new Date().toISOString(),
    caveats: [
      'Raw source comparison plus conservative modification-time checks are not proof of every compilation input.',
      'Confirm target, vars, environment, packages, external macros and catalog freshness with the artifact producer.',
      'Credential files, dependency directories and generated artifacts are deliberately not inspected.',
      'A fresh checkout can conservatively require regenerated artifacts even when content is unchanged.',
    ],
  };
}
