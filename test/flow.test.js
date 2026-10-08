'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const test = require('node:test');

const root = path.resolve(__dirname, '..');
const flowDir = path.join(root, 'docs', 'flow');

test('flow contract artifacts exist and match simplicio.flow/v1', () => {
  const flowJsonPath = path.join(flowDir, 'simplicio-local.flow.json');
  assert.ok(fs.existsSync(flowJsonPath), 'simplicio-local.flow.json missing');
  const flowData = JSON.parse(fs.readFileSync(flowJsonPath, 'utf8'));
  assert.equal(flowData.schema, 'simplicio.flow/v1');
  assert.ok(Array.isArray(flowData.inputs) && flowData.inputs.length > 0);
  assert.ok(Array.isArray(flowData.nodes) && flowData.nodes.length > 0);
  assert.ok(Array.isArray(flowData.edges) && flowData.edges.length > 0);
  assert.ok(Array.isArray(flowData.outputs) && flowData.outputs.length > 0);
});

test('flow derived mermaid and langflow files are present', () => {
  const mmdPath = path.join(flowDir, 'simplicio-local.mmd');
  const langflowPath = path.join(flowDir, 'langflow', 'simplicio-local.langflow.json');
  assert.ok(fs.existsSync(mmdPath), 'simplicio-local.mmd missing');
  assert.ok(fs.existsSync(langflowPath), 'simplicio-local.langflow.json missing');

  const mmdContent = fs.readFileSync(mmdPath, 'utf8');
  assert.match(mmdContent, /flowchart TD/);
  assert.match(mmdContent, /subgraph Inputs/);
  assert.match(mmdContent, /subgraph Steps/);
  assert.match(mmdContent, /subgraph Outputs/);

  const langflowData = JSON.parse(fs.readFileSync(langflowPath, 'utf8'));
  assert.equal(langflowData.name, 'simplicio-local');
  assert.ok(Array.isArray(langflowData.data?.nodes) && langflowData.data.nodes.length > 0);
  assert.ok(Array.isArray(langflowData.data?.edges) && langflowData.data.edges.length > 0);
});

test('flow image artifacts exist (SVG or PNG)', () => {
  const svgPath = path.join(flowDir, 'simplicio-local.svg');
  const pngPath = path.join(flowDir, 'simplicio-local.png');
  const hasImage = fs.existsSync(svgPath) || fs.existsSync(pngPath);
  assert.ok(hasImage, 'Expected either SVG or PNG image artifact');
});

test('flow generator drift check passes with exit code 0', () => {
  const result = spawnSync('python3', ['scripts/generate_flow.py', '--check-drift'], {
    cwd: root,
    encoding: 'utf8',
  });
  assert.equal(result.status, 0, `Drift check failed: ${result.stderr || result.stdout}`);
});
