// Offline regression check. No bridge, child integration or service is started.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { integrationRevision, revisionFiles } from '../integrations/integration-revision.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const fixture = path.join(root, 'tmp', 'revision-review-' + Date.now());
for (const name of revisionFiles) {
  const file = path.join(fixture, name);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, 'fixture:' + name);
}
const baseline = integrationRevision(fixture);
assert.equal(integrationRevision(fixture), baseline);
for (const name of revisionFiles) {
  const file = path.join(fixture, name);
  fs.appendFileSync(file, '\nchanged');
  assert.notEqual(integrationRevision(fixture), baseline, name);
  fs.writeFileSync(file, 'fixture:' + name);
  assert.equal(integrationRevision(fixture), baseline);
}
fs.renameSync(path.join(fixture, 'windows-ui.toml'), path.join(fixture, 'windows-ui.toml.absent'));
assert.throws(() => integrationRevision(fixture), { code: 'ENOENT' });
const report = { mode: 'offline_fixtures', passed: true,
  checks: ['stable unchanged revision', ...revisionFiles.map(n => 'detect change: ' + n), 'missing input fails'],
  fixture, servicesStarted: false };
fs.writeFileSync(path.join(root, 'logs', 'integration-revision-review.json'), JSON.stringify(report, null, 2));
console.log(JSON.stringify(report));
