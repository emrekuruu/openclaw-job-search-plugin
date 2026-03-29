import { Type } from "@sinclair/typebox";
import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";
import { mkdirSync, readFileSync, readdirSync, writeFileSync, existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import xlsx from "xlsx";
import { spawn, spawnSync } from "node:child_process";

type Json = Record<string, any>;

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function repoRoot() {
  return __dirname;
}

function resolveJobSpyWorker(repoDir: string) {
  return {
    script: path.join(repoDir, "skills", "job-search-skill", "scripts", "run_jobspy_search.py"),
    uvProject: path.join(repoDir, "pyproject.toml"),
    venvPython: path.join(repoDir, ".venv", "bin", "python3"),
  };
}

function resolvePythonCommand(repoDir: string) {
  if (process.env.JOB_SEARCH_PYTHON) return process.env.JOB_SEARCH_PYTHON;
  const worker = resolveJobSpyWorker(repoDir);
  if (existsSync(worker.venvPython)) return worker.venvPython;
  return "python3";
}

function verifyJobSpyWorkerReadiness(repoDir: string) {
  const worker = resolveJobSpyWorker(repoDir);
  if (!existsSync(worker.script)) {
    throw new Error(
      [
        `JobSpy worker script is missing: ${worker.script}`,
        "The plugin install/runtime copy must include skills/job-search-skill/scripts/run_jobspy_search.py.",
      ].join(" "),
    );
  }

  const python = resolvePythonCommand(repoDir);
  const versionCheck = spawnSync(python, ["--version"], { encoding: "utf8" });
  if (versionCheck.error) {
    throw new Error(
      [
        `Python runtime not available via ${JSON.stringify(python)}.`,
        `Set JOB_SEARCH_PYTHON to a working interpreter or create ${worker.venvPython}.`,
        `Recommended setup: cd ${repoDir} && uv sync`,
        `Fallback: python3 -m venv .venv && .venv/bin/pip install -U pip python-jobspy pandas pydantic openpyxl`,
      ].join("\n"),
    );
  }

  const importCheck = spawnSync(
    python,
    [
      "-c",
      "from jobspy import scrape_jobs; import pandas, pydantic, openpyxl; print('jobspy-ready')",
    ],
    { encoding: "utf8", cwd: repoDir },
  );
  if (importCheck.status !== 0) {
    const stderr = (importCheck.stderr || importCheck.stdout || "").trim();
    throw new Error(
      [
        `JobSpy worker dependencies are not ready for interpreter ${JSON.stringify(python)}.`,
        stderr ? `Python said: ${stderr}` : "",
        `Recommended setup: cd ${repoDir} && uv sync`,
        `Then either let the plugin use ${worker.venvPython} automatically, or set JOB_SEARCH_PYTHON to the interpreter you want.`,
      ].filter(Boolean).join("\n"),
    );
  }

  return { python, script: worker.script, uvProject: worker.uvProject };
}

function resolvePluginStateDir(api: any) {
  const stateDir = api.runtime.state.resolveStateDir(process.env);
  return path.join(stateDir, "plugin-runtimes", api.id);
}

function resolvePluginConfig(api: any) {
  const cfg = (api.pluginConfig ?? {}) as Record<string, unknown>;
  return {
    stateDir: resolvePluginStateDir(api),
  };
}

function slugify(input: string) {
  return input
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "") || "run";
}

function nowStamp() {
  const now = new Date();
  const y = now.getFullYear();
  const m = String(now.getMonth() + 1).padStart(2, "0");
  const d = String(now.getDate()).padStart(2, "0");
  const hh = String(now.getHours()).padStart(2, "0");
  const mm = String(now.getMinutes()).padStart(2, "0");
  const ss = String(now.getSeconds()).padStart(2, "0");
  return `${y}-${m}-${d}-${hh}${mm}${ss}`;
}

function ensureDir(dir: string) {
  mkdirSync(dir, { recursive: true });
}

function readJson(filePath: string) {
  return JSON.parse(readFileSync(filePath, "utf8"));
}

function writeJson(filePath: string, value: unknown) {
  ensureDir(path.dirname(filePath));
  writeFileSync(filePath, JSON.stringify(value, null, 2) + "\n", "utf8");
}

function listJson(dir: string) {
  if (!existsSync(dir)) return [] as string[];
  return readdirSync(dir)
    .filter((name) => name.endsWith(".json") && !name.endsWith(".error.json"))
    .sort()
    .map((name) => path.join(dir, name));
}

function requireExistingFile(filePath: string, label: string) {
  if (!existsSync(filePath)) {
    throw new Error(`${label} does not exist: ${filePath}`);
  }
}

function resolveArtifacts(stateDir: string, runId: string) {
  const runDir = path.join(stateDir, "search-runs", runId);
  const listingsDir = path.join(runDir, "listings");
  const searchPath = path.join(runDir, "search.json");
  const evaluationsDir = path.join(stateDir, "evaluations", runId);
  const exportsDir = path.join(stateDir, "exports");
  return {
    stateDir,
    runDir,
    searchPath,
    listingsDir,
    evaluationsDir,
    exportsDir,
    exportPath: path.join(exportsDir, `${runId}.xlsx`),
    latestExportPath: path.join(exportsDir, "latest.xlsx"),
  };
}

function latestRunDir(stateDir: string) {
  const runsDir = path.join(stateDir, "search-runs");
  ensureDir(runsDir);
  const dirs = readdirSync(runsDir, { withFileTypes: true })
    .filter((d) => d.isDirectory())
    .map((d) => path.join(runsDir, d.name))
    .sort();
  if (!dirs.length) throw new Error("No search runs found.");
  return dirs[dirs.length - 1];
}

function runPythonJobSpy(repoDir: string, stateDir: string, runId?: string) {
  return new Promise<{ searchPath: string; listingsDir: string; listingCount?: number }>((resolve, reject) => {
    const { python, script } = verifyJobSpyWorkerReadiness(repoDir);
    const child = spawn(python, [script], {
      cwd: repoDir,
      env: {
        ...process.env,
        OPENCLAW_STATE_DIR: path.dirname(path.dirname(stateDir)),
        ...(runId ? { JOB_SEARCH_RUN_ID: runId } : {}),
      },
      stdio: ["ignore", "pipe", "pipe"],
    });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk) => {
      stdout += chunk.toString();
    });
    child.stderr.on("data", (chunk) => {
      stderr += chunk.toString();
    });
    child.on("error", reject);
    child.on("close", (code) => {
      if (code !== 0) {
        reject(new Error(`JobSpy runner failed with code ${code}: ${stderr || stdout}`));
        return;
      }
      const searchPath = stdout.trim().split(/\r?\n/).filter(Boolean).pop();
      if (!searchPath) {
        reject(new Error("JobSpy runner did not print a search.json path."));
        return;
      }
      const search = readJson(searchPath);
      resolve({
        searchPath,
        listingsDir: String(search?.artifacts?.listingsDir || ""),
        listingCount: Number(search?.listingCount || 0),
      });
    });
  });
}

function exportRun(stateDir: string, runId: string) {
  const artifacts = resolveArtifacts(stateDir, runId);
  ensureDir(artifacts.exportsDir);
  const evaluationFiles = listJson(artifacts.evaluationsDir);
  const rows = evaluationFiles.map((filePath) => {
    const evaluation = readJson(filePath);
    const listingPath = path.join(artifacts.listingsDir, `${evaluation.listingId}.json`);
    const listing = existsSync(listingPath) ? readJson(listingPath) : {};
    return {
      score: Number(evaluation.score ?? 0),
      decision: evaluation.decision ?? "",
      reasoning: evaluation.reasoning ?? "",
      title: listing.title ?? "",
      company: listing.company ?? "",
      location: listing.location ?? "",
      workMode: listing.workMode ?? "",
      source: listing.source ?? "",
      url: listing.url ?? "",
      query: listing.query ?? "",
      listingId: evaluation.listingId ?? path.basename(filePath, ".json"),
    };
  }).sort((a, b) => b.score - a.score);

  const wb = xlsx.utils.book_new();
  const ws = xlsx.utils.json_to_sheet(rows);
  xlsx.utils.book_append_sheet(wb, ws, "Evaluations");
  xlsx.writeFile(wb, artifacts.exportPath);
  xlsx.writeFile(wb, artifacts.latestExportPath);
  return artifacts.exportPath;
}


export default definePluginEntry({
  id: "job-search",
  name: "Job Search",
  description: "Concurrent job search workflow plugin with retrieval, evaluator fanout, and export.",
  register(api) {
    api.registerTool({
      name: "job_search_prepare_run",
      label: "Prepare job search run",
      description: "Create a new job search run under OpenClaw state storage and seed search.json for agent-authored retrieval planning.",
      parameters: Type.Object({
        runId: Type.Optional(Type.String()),
        profilePath: Type.String(),
        candidateUnderstanding: Type.Optional(Type.Any()),
        queries: Type.Optional(Type.Array(Type.Any())),
      }),
      async execute(_id, params) {
        const cfg = resolvePluginConfig(api);
        const profilePath = path.resolve(String(params.profilePath));
        requireExistingFile(profilePath, "Candidate profile");
        const runId = String(params.runId || `${nowStamp()}-${slugify(path.basename(profilePath, path.extname(profilePath)))}`);
        const artifacts = resolveArtifacts(cfg.stateDir, runId);
        ensureDir(artifacts.listingsDir);
        writeJson(artifacts.searchPath, {
          runId,
          profilePath,
          candidateUnderstanding: params.candidateUnderstanding || {},
          queries: params.queries || [],
          status: "draft",
          artifacts: {
            stateDir: artifacts.stateDir,
            runDir: artifacts.runDir,
            searchPath: artifacts.searchPath,
            listingsDir: artifacts.listingsDir,
            evaluationsDir: artifacts.evaluationsDir,
            exportsDir: artifacts.exportsDir,
          },
        });
        const details = { runId, searchPath: artifacts.searchPath, listingsDir: artifacts.listingsDir };
        return { content: [{ type: "text", text: JSON.stringify(details) }], details };
      },
    });

    api.registerTool({
      name: "job_search_check_worker",
      label: "Check JobSpy worker readiness",
      description: "Verify that the installed plugin copy can reach the JobSpy Python worker and that its dependencies are installed.",
      parameters: Type.Object({}),
      async execute() {
        const worker = verifyJobSpyWorkerReadiness(repoRoot());
        const details = {
          ready: true,
          python: worker.python,
          script: worker.script,
          uvProject: worker.uvProject,
        };
        return { content: [{ type: "text", text: JSON.stringify(details) }], details };
      },
    });

    api.registerTool({
      name: "job_search_run_retrieval",
      label: "Run job retrieval",
      description: "Run JobSpy retrieval through the job-search skill's Python runner for the latest or specified state-backed run.",
      parameters: Type.Object({
        runId: Type.Optional(Type.String()),
      }),
      async execute(_id, params) {
        const cfg = resolvePluginConfig(api);
        const runDir = params.runId ? resolveArtifacts(cfg.stateDir, String(params.runId)).runDir : latestRunDir(cfg.stateDir);
        const searchPath = path.join(runDir, "search.json");
        requireExistingFile(searchPath, "search.json");
        const result = await runPythonJobSpy(repoRoot(), cfg.stateDir, String(params.runId || path.basename(runDir)));
        return { content: [{ type: "text", text: JSON.stringify(result) }], details: result };
      },
    });

    api.registerTool({
      name: "job_search_export_run",
      label: "Export job search run",
      description: "Aggregate evaluation artifacts for a run and export them into an Excel workbook sorted by score.",
      parameters: Type.Object({
        runId: Type.String(),
      }),
      async execute(_id, params) {
        const cfg = resolvePluginConfig(api);
        const outputPath = exportRun(cfg.stateDir, String(params.runId));
        const details = { runId: params.runId, outputPath };
        return { content: [{ type: "text", text: JSON.stringify(details) }], details };
      },
    });

  },
});
