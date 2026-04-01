import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import crypto from 'node:crypto';
import plugin from '../index.ts';

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const stateRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'job-search-real-verify-'));
process.env.OPENCLAW_STATE_DIR = stateRoot;

const tools = new Map();
const api = {
  id: 'job-search',
  pluginConfig: { evaluationConcurrency: 2 },
  config: {},
  runtime: {
    state: {
      resolveStateDir() {
        return stateRoot;
      },
    },
    subagent: {
      async run() {
        throw new Error('Plugin runtime subagent methods are only available during a gateway request.');
      },
      async waitForRun() {
        throw new Error('Plugin runtime subagent methods are only available during a gateway request.');
      },
    },
    agent: {
      resolveAgentDir() {
        return path.join(stateRoot, 'agent');
      },
      resolveAgentWorkspaceDir() {
        return root;
      },
      session: {
        resolveSessionFilePath(_cfg, sessionId) {
          return path.join(stateRoot, 'sessions', `${sessionId}.jsonl`);
        },
      },
      async runEmbeddedPiAgent(params) {
        const outputMatch = params.prompt.match(/- outputPath: (.+)\n/);
        const errorMatch = params.prompt.match(/- errorPath: (.+)\n/);
        const listingMatch = params.prompt.match(/- listingPath: (.+)\n/);
        const outputPath = outputMatch?.[1]?.trim();
        const errorPath = errorMatch?.[1]?.trim();
        const listingPath = listingMatch?.[1]?.trim();
        if (!outputPath || !listingPath) {
          if (errorPath) {
            fs.mkdirSync(path.dirname(errorPath), { recursive: true });
            fs.writeFileSync(errorPath, JSON.stringify({ error: 'missing paths' }, null, 2));
          }
          return { payloads: [{ text: 'error' }] };
        }
        const listing = JSON.parse(fs.readFileSync(listingPath, 'utf8'));
        fs.mkdirSync(path.dirname(outputPath), { recursive: true });
        fs.writeFileSync(outputPath, JSON.stringify({
          listingId: listing.id,
          decision: 'keep',
          score: 77,
          reasoning: 'Fallback embedded evaluator wrote this result.'
        }, null, 2));
        return { payloads: [{ text: 'ok' }], runId: crypto.randomUUID() };
      },
    },
  },
  registerTool(def) {
    tools.set(def.name, def);
  },
};

plugin.register(api);
const tool = tools.get('job_search_full_run');
const result = await tool.execute('verify', {
  runId: 'verify-embedded-fallback',
  profilePath: path.join(root, 'assets/profiles/sample-software-engineer-profile.md'),
  queries: [
    { query: 'Junior Software Engineer', location: 'Istanbul, Turkey', site: 'linkedin' }
  ],
  evaluationLimit: 2,
  timeoutMs: 300000,
});
console.log(JSON.stringify({ stateRoot, details: result.details }, null, 2));
