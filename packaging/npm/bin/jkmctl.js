#!/usr/bin/env node
// CLI-обёртка: управление сервером JKM LCD через Python-скрипт из пакета.
const { spawnSync } = require('child_process');
const path = require('path');

const script = path.join(__dirname, 'jkmctl.py');
const result = spawnSync('python3', [script, ...process.argv.slice(2)], { stdio: 'inherit' });
if (result.error) {
  console.error('Нужен Python 3.10+: ' + result.error.message);
  process.exit(1);
}
process.exit(result.status ?? 1);
