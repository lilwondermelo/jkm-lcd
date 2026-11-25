#!/usr/bin/env node
// npm-обёртка: запускает Python-CLI из этого же каталога.
const { spawnSync } = require('child_process');
const path = require('path');
const result = spawnSync('python3', [path.join(__dirname, 'jkmctl'), ...process.argv.slice(2)], { stdio: 'inherit' });
if (result.error) {
  console.error('Нужен Python 3.10+: ' + result.error.message);
  process.exit(1);
}
process.exit(result.status ?? 1);
