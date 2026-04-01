import { Type } from "@sinclair/typebox";
import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";
import { mkdirSync, readFileSync, readdirSync, writeFileSync, existsSync, copyFileSync } from "node:fs";
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
    defaultResumeTheme: typeof cfg.defaultResumeTheme === "string" && cfg.defaultResumeTheme.trim()
      ? cfg.defaultResumeTheme.trim()
      : "jsonresume-theme-even",
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
  const resumesDir = path.join(stateDir, "resumes", runId);
  const exportsDir = path.join(stateDir, "exports");
  return {
    stateDir,
    runDir,
    searchPath,
    listingsDir,
    evaluationsDir,
    resumesDir,
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

function resumedBin(repoDir: string) {
  const binName = process.platform === "win32" ? "resumed.cmd" : "resumed";
  return path.join(repoDir, "node_modules", ".bin", binName);
}

function verifyResumeRendererReadiness(repoDir: string, theme: string) {
  const bin = resumedBin(repoDir);
  if (!existsSync(bin)) {
    throw new Error(
      [
        `Resumed CLI is not installed at ${bin}.`,
        `Run: cd ${repoDir} && npm install`,
      ].join("\n"),
    );
  }

  const themeDir = path.join(repoDir, "node_modules", theme);
  if (!existsSync(themeDir)) {
    throw new Error(
      [
        `Resume theme is not installed: ${theme}`,
        `Expected under ${themeDir}`,
        `Run: cd ${repoDir} && npm install`,
      ].join("\n"),
    );
  }

  const versionCheck = spawnSync(bin, ["--version"], { cwd: repoDir, encoding: "utf8" });
  if (versionCheck.error || versionCheck.status !== 0) {
    throw new Error(
      [
        `Unable to execute Resumed CLI from ${bin}.`,
        versionCheck.error ? String(versionCheck.error) : (versionCheck.stderr || versionCheck.stdout || "").trim(),
      ].filter(Boolean).join("\n"),
    );
  }

  return { bin, theme };
}

function normalizeResumeFormat(format?: string) {
  const value = String(format || "both").toLowerCase();
  if (!["html", "pdf", "both"].includes(value)) {
    throw new Error(`Unsupported resume format: ${format}`);
  }
  return value as "html" | "pdf" | "both";
}

function renderResumeFile(repoDir: string, inputPath: string, theme: string, format: "html" | "pdf" | "both") {
  const { bin } = verifyResumeRendererReadiness(repoDir, theme);
  requireExistingFile(inputPath, "Resume JSON");

  const outputPaths: string[] = [];
  const base = inputPath.replace(/\.json$/i, "");

  const validate = spawnSync(bin, ["validate", inputPath], { cwd: repoDir, encoding: "utf8" });
  if (validate.status !== 0) {
    throw new Error(
      [
        `Resume validation failed for ${inputPath}`,
        (validate.stderr || validate.stdout || "").trim(),
      ].filter(Boolean).join("\n"),
    );
  }

  if (format === "html" || format === "both") {
    const htmlPath = `${base}.html`;
    const render = spawnSync(bin, ["render", inputPath, "--theme", theme, "--output", htmlPath], {
      cwd: repoDir,
      encoding: "utf8",
    });
    if (render.status !== 0) {
      throw new Error(
        [
          `HTML render failed for ${inputPath}`,
          (render.stderr || render.stdout || "").trim(),
        ].filter(Boolean).join("\n"),
      );
    }
    outputPaths.push(htmlPath);
  }

  if (format === "pdf" || format === "both") {
    const pdfPath = `${base}.pdf`;
    const exportResult = spawnSync(bin, ["export", inputPath, "--theme", theme, "--output", pdfPath], {
      cwd: repoDir,
      encoding: "utf8",
    });
    if (exportResult.status !== 0) {
      throw new Error(
        [
          `PDF export failed for ${inputPath}`,
          (exportResult.stderr || exportResult.stdout || "").trim(),
        ].filter(Boolean).join("\n"),
      );
    }
    outputPaths.push(pdfPath);
  }

  return outputPaths;
}

function prepareResumePath(stateDir: string, runId: string, listingId: string) {
  const artifacts = resolveArtifacts(stateDir, runId);
  ensureDir(artifacts.resumesDir);
  return path.join(artifacts.resumesDir, `${listingId}.json`);
}

function renderRunResumes(repoDir: string, stateDir: string, runId: string, theme: string, format: "html" | "pdf" | "both") {
  const artifacts = resolveArtifacts(stateDir, runId);
  ensureDir(artifacts.resumesDir);
  const files = listJson(artifacts.resumesDir);
  const resumeFiles = files.filter((file) => !file.endsWith(".error.json"));
  if (!resumeFiles.length) {
    throw new Error(`No resume JSON files found in ${artifacts.resumesDir}`);
  }

  const rendered = resumeFiles.map((inputPath) => ({
    inputPath,
    outputPaths: renderResumeFile(repoDir, inputPath, theme, format),
  }));

  return {
    runId,
    resumesDir: artifacts.resumesDir,
    theme,
    format,
    rendered,
  };
}

function importResumeJson(stateDir: string, runId: string, listingId: string, sourcePath: string) {
  const destinationPath = prepareResumePath(stateDir, runId, listingId);
  requireExistingFile(sourcePath, "Source resume JSON");
  const parsed = readJson(sourcePath);
  writeJson(destinationPath, parsed);
  return destinationPath;
}

function buildResumeJsonFromTailored(repoDir: string, stateDir: string, runId: string, listingId: string, profilePath: string, tailoredCvPath: string) {
  const scriptPath = path.join(repoDir, "skills", "resume-builder", "scripts", "build_resume.py");
  requireExistingFile(scriptPath, "Resume bridge script");
  requireExistingFile(profilePath, "Candidate profile");
  requireExistingFile(tailoredCvPath, "Tailored CV JSON");

  const python = resolvePythonCommand(repoDir);
  const destinationPath = prepareResumePath(stateDir, runId, listingId);
  const bridgeOutputPath = `${destinationPath}.bridge.json`;

  const result = spawnSync(
    python,
    [scriptPath, profilePath, "--tailored-cv", tailoredCvPath, "--out", bridgeOutputPath],
    { cwd: repoDir, encoding: "utf8" },
  );
  if (result.status !== 0) {
    throw new Error(
      [
        `Resume bridge generation failed for listing ${listingId}.`,
        (result.stderr || result.stdout || "").trim(),
      ].filter(Boolean).join("\n"),
    );
  }

  const bridge = readJson(bridgeOutputPath);
  if (!bridge?.json_resume) {
    throw new Error(`Resume bridge did not produce json_resume in ${bridgeOutputPath}`);
  }

  writeJson(destinationPath, bridge.json_resume);
  return {
    outputPath: destinationPath,
    bridgeOutputPath,
    previewText: bridge.preview_text || "",
  };
}

export default definePluginEntry({
  id: "job-search",
  name: "Job Search",
  description: "Concurrent job search workflow plugin with retrieval, evaluator fanout, export, and JSON Resume rendering.",
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
        ensureDir(artifacts.resumesDir);
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
            resumesDir: artifacts.resumesDir,
            exportsDir: artifacts.exportsDir,
          },
        });
        const details = { runId, searchPath: artifacts.searchPath, listingsDir: artifacts.listingsDir, resumesDir: artifacts.resumesDir };
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
      name: "job_search_check_resume_renderer",
      label: "Check JSON Resume renderer readiness",
      description: "Verify that the installed plugin copy can render JSON Resume files with the configured CLI and theme.",
      parameters: Type.Object({
        theme: Type.Optional(Type.String()),
      }),
      async execute(_id, params) {
        const cfg = resolvePluginConfig(api);
        const theme = String(params.theme || cfg.defaultResumeTheme);
        const renderer = verifyResumeRendererReadiness(repoRoot(), theme);
        const details = {
          ready: true,
          bin: renderer.bin,
          theme: renderer.theme,
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
      name: "job_search_prepare_resume_path",
      label: "Prepare resume output path",
      description: "Return the canonical runtime path where an agent should write one JSON Resume file for a selected listing.",
      parameters: Type.Object({
        runId: Type.String(),
        listingId: Type.String(),
      }),
      async execute(_id, params) {
        const cfg = resolvePluginConfig(api);
        const outputPath = prepareResumePath(cfg.stateDir, String(params.runId), String(params.listingId));
        const details = { runId: params.runId, listingId: params.listingId, outputPath };
        return { content: [{ type: "text", text: JSON.stringify(details) }], details };
      },
    });

    api.registerTool({
      name: "job_search_import_resume_json",
      label: "Import JSON Resume into runtime",
      description: "Copy a generated JSON Resume file into the plugin runtime resumes directory for a run/listing.",
      parameters: Type.Object({
        runId: Type.String(),
        listingId: Type.String(),
        sourcePath: Type.String(),
      }),
      async execute(_id, params) {
        const cfg = resolvePluginConfig(api);
        const sourcePath = path.resolve(String(params.sourcePath));
        const outputPath = importResumeJson(cfg.stateDir, String(params.runId), String(params.listingId), sourcePath);
        const details = { runId: params.runId, listingId: params.listingId, outputPath };
        return { content: [{ type: "text", text: JSON.stringify(details) }], details };
      },
    });

    api.registerTool({
      name: "job_search_build_resume_json",
      label: "Build JSON Resume from tailored CV",
      description: "Bridge the text-first tailoring flow into the renderer pipeline by converting cv-tailoring output plus the base profile into runtime JSON Resume.",
      parameters: Type.Object({
        runId: Type.String(),
        listingId: Type.String(),
        profilePath: Type.String(),
        tailoredCvPath: Type.String(),
      }),
      async execute(_id, params) {
        const cfg = resolvePluginConfig(api);
        const details = buildResumeJsonFromTailored(
          repoRoot(),
          cfg.stateDir,
          String(params.runId),
          String(params.listingId),
          path.resolve(String(params.profilePath)),
          path.resolve(String(params.tailoredCvPath)),
        );
        return { content: [{ type: "text", text: JSON.stringify(details) }], details };
      },
    });

    api.registerTool({
      name: "job_search_render_resumes",
      label: "Render JSON Resume files",
      description: "Validate and render JSON Resume files for a run into HTML, PDF, or both using the configured CLI theme.",
      parameters: Type.Object({
        runId: Type.String(),
        theme: Type.Optional(Type.String()),
        format: Type.Optional(Type.Union([
          Type.Literal("html"),
          Type.Literal("pdf"),
          Type.Literal("both"),
        ])),
      }),
      async execute(_id, params) {
        const cfg = resolvePluginConfig(api);
        const theme = String(params.theme || cfg.defaultResumeTheme);
        const format = normalizeResumeFormat(params.format ? String(params.format) : "both");
        const details = renderRunResumes(repoRoot(), cfg.stateDir, String(params.runId), theme, format);
        return { content: [{ type: "text", text: JSON.stringify(details) }], details };
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
