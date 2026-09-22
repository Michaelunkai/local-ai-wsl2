// Pure file hashing: importing or invoking this module starts no integration.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';

export const revisionFiles = [
  'host-bridge.mjs',
  'integration-revision.mjs',
  'package.json',
  'package-lock.json',
  'windows-ui.toml',
  'uv-tools/windows-mcp/Lib/site-packages/windows_mcp/desktop/service.py',
  'node_modules/@wonderwhy-er/desktop-commander/dist/config.js',
];

export function integrationRevision(root) {
  const hash = crypto.createHash('sha256');
  for (const relative of revisionFiles) {
    const content = fs.readFileSync(path.join(root, relative));
    hash.update(relative + '\0' + content.length + '\0');
    hash.update(content);
  }
  return hash.digest('hex');
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  console.log(integrationRevision(process.argv[2] || path.dirname(fileURLToPath(import.meta.url))));
}
