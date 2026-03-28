import { Type } from "@sinclair/typebox";
import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";
import { mkdirSync, readFileSync, readdirSync, rmSync, writeFileSync, existsSync } from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { fileURLToPath } from "node:url";
import xlsx from "xlsx";

type Json = Record<string, any>;

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function repoRoot() {
  return __dirname;
}

function resolvePluginStateDir(api: any) {
  const stateDir = api.runtime.state.resolveStateDir(process.env);
  return path.join(stateDir, "plugin-runtimes", api.id);
}

function resolvePluginConfig(api: any) {
  const cfg = (api.pluginConfig ?? {}) as Record<string, unknown>;
  return {
    stateDir: resolvePluginStateDir(api),
    evaluationConcurrency: Number(cfg.evaluationConcurrency ?? 20),
    evaluationModel: cfg.evaluationModel ? String(cfg.evaluationModel) : null,
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

function loadSearchDefaults() {
  const defaultsPath = path.join(repoRoot(), "config", "search-defaults.json");
  requireExistingFile(defaultsPath, "Search defaults");
  return readJson(defaultsPath);
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

function listingIdentity(listing: Json) {
  return String(
    listing.url || `${listing.company || "unknown-company"}::${listing.title || "unknown-title"}::${listing.location || "unknown-location"}::${listing.query || "unknown-query"}`,
  );
}

function listingId(runId: string, listing: Json) {
  const base = slugify(`${runId}-${listing.company || "unknown-company"}-${listing.title || "unknown-title"}`);
  const suffix = crypto.createHash("sha1").update(listingIdentity(listing)).digest("hex").slice(0, 10);
  return `${base}-${suffix}`;
}

function normalizeListing(runId: string, raw: Json, queryEntry: Json) {
  const listing = {
    title: raw.title || raw.job_title || "Unknown Title",
    company: raw.company || raw.company_name || "Unknown Company",
    location: raw.location || raw.job_location || "Unknown Location",
    workMode: raw.workMode || (raw.is_remote ? "remote" : null),
    source: raw.source || raw.site || raw.site_name || "unknown",
    url: raw.url || raw.job_url || raw.job_url_direct || "",
    postedDate: raw.postedDate || raw.date_posted || null,
    salary: raw.salary || raw.min_amount || null,
    summary: raw.summary || raw.description || raw.job_summary || "",
    query: queryEntry.query,
    reasoning: queryEntry.reasoning,
    filters: queryEntry.filters || {},
    filterReasoning: queryEntry.filterReasoning || {},
    runId,
    retrievedAt: new Date().toISOString(),
  } as Json;
  listing.id = listingId(runId, listing);
  return listing;
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

async function runJobSpySearch(runDir: string) {
  const searchPath = path.join(runDir, "search.json");
  requireExistingFile(searchPath, "search.json");
  const search = readJson(searchPath);
  requireExistingFile(String(search.profilePath || ""), "Candidate profile");
  const queries = search.queries || [];
  if (!queries.length) throw new Error("search.json has no queries.");
  const defaults = loadSearchDefaults();
  const listingsDir = path.join(runDir, "listings");
  rmSync(listingsDir, { recursive: true, force: true });
  ensureDir(listingsDir);

  const { scrape_jobs } = await import("jobspy");
  const seen = new Set<string>();
  const executedQueries: Json[] = [];
  let listingCount = 0;

  for (const queryEntry of queries) {
    const filters = queryEntry.filters || {};
    const request: Json = {
      site_name: filters.site_name ?? defaults.siteNames,
      search_term: queryEntry.query,
      location: filters.location,
      results_wanted: filters.results_wanted ?? defaults.resultsWanted ?? 10,
      hours_old: filters.hours_old ?? defaults.hoursOld ?? defaults.freshnessHours ?? 720,
      is_remote: filters.is_remote ?? false,
      easy_apply: filters.easy_apply ?? defaults.easyApply ?? false,
      linkedin_fetch_description: filters.linkedin_fetch_description ?? defaults.linkedinFetchDescription ?? true,
      country_indeed: filters.country_indeed ?? defaults.defaultCountryIndeed ?? "turkey",
      verbose: filters.verbose ?? defaults.verbose ?? 1,
      job_type: filters.job_type ?? defaults.jobType ?? "fulltime",
      distance: filters.distance ?? defaults.distance,
    };
    Object.keys(request).forEach((key) => request[key] == null && delete request[key]);
    const df = await scrape_jobs(request as any);
    const results = JSON.parse(df.to_json({ orient: "records", date_format: "iso" } as any));
    executedQueries.push({
      query: queryEntry.query,
      reasoning: queryEntry.reasoning,
      filters,
      filterReasoning: queryEntry.filterReasoning || {},
      request,
      resultCount: results.length,
    });
    for (const raw of results) {
      const listing = normalizeListing(search.runId || path.basename(runDir), raw, queryEntry);
      const identity = listingIdentity(listing).toLowerCase();
      if (seen.has(identity)) continue;
      seen.add(identity);
      writeJson(path.join(listingsDir, `${listing.id}.json`), listing);
      listingCount += 1;
    }
  }

  search.status = "completed";
  search.listingCount = listingCount;
  search.executedQueries = executedQueries;
  search.artifacts = {
    ...(search.artifacts || {}),
    searchPath,
    listingsDir,
  };
  writeJson(searchPath, search);
  return { searchPath, listingsDir, listingCount };
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

async function spawnEvaluators(api: any, stateDir: string, params: Json) {
  const runId = String(params.runId);
  const profilePath = path.resolve(String(params.profilePath));
  requireExistingFile(profilePath, "Candidate profile");
  const artifacts = resolveArtifacts(stateDir, runId);
  ensureDir(artifacts.evaluationsDir);
  const listingFiles = listJson(artifacts.listingsDir).slice(0, Number(params.limit ?? resolvePluginConfig(api).evaluationConcurrency));
  const promptPath = path.join(repoRoot(), "prompts", "job-listing-evaluator-subagent-prompt.md");
  const promptTemplate = existsSync(promptPath) ? readFileSync(promptPath, "utf8") : "Evaluate the listing and write one JSON result to outputPath.";
  const modelRef = resolvePluginConfig(api).evaluationModel;

  const runs = await Promise.all(listingFiles.map(async (listingPath, idx) => {
    const listing = readJson(listingPath);
    const outputPath = path.join(artifacts.evaluationsDir, `${listing.id}.json`);
    const errorPath = path.join(artifacts.evaluationsDir, `${listing.id}.error.json`);
    const sessionKey = `job-search-eval-${slugify(runId).slice(-12)}-${String(idx + 1).padStart(2, "0")}`;
    const message = `${promptTemplate}\n\nInputs:\n- profilePath: ${profilePath}\n- listingPath: ${listingPath}\n- runId: ${runId}\n- outputPath: ${outputPath}\n- errorPath: ${errorPath}\n\nRules:\n- Read profilePath and listingPath.\n- Write exactly one JSON evaluation object to outputPath.\n- If evaluation fails, write a JSON error object to errorPath.\n- Do not rely on stdout for the result.`;
    const req: Json = {
      sessionKey,
      message,
      deliver: false,
    };
    if (modelRef) {
      const [provider, model] = modelRef.split("/", 2);
      if (provider && model) {
        req.provider = provider;
        req.model = model;
      }
    }
    const started = await api.runtime.subagent.run(req);
    return { runId: started.runId, listingPath, outputPath, errorPath };
  }));

  await Promise.all(runs.map((r) => api.runtime.subagent.waitForRun({ runId: r.runId, timeoutMs: Number(params.timeoutMs ?? 600000) })));

  const results = runs.map((r) => ({
    listingPath: r.listingPath,
    outputPath: r.outputPath,
    errorPath: r.errorPath,
    ok: existsSync(r.outputPath),
    error: existsSync(r.errorPath) ? readJson(r.errorPath) : null,
  }));
  return { runId, evaluationsDir: artifacts.evaluationsDir, results };
}

export default definePluginEntry({
  id: "job-search",
  name: "Job Search",
  description: "Concurrent job search workflow plugin with retrieval, evaluator fanout, and export.",
  register(api) {
    api.registerTool({
      name: "job_search_prepare_run",
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
        return { content: [{ type: "text", text: JSON.stringify({ runId, searchPath: artifacts.searchPath, listingsDir: artifacts.listingsDir }) }] };
      },
    });

    api.registerTool({
      name: "job_search_run_retrieval",
      description: "Run JobSpy retrieval for the latest or specified state-backed run using the authored search.json plan.",
      parameters: Type.Object({
        runId: Type.Optional(Type.String()),
      }),
      async execute(_id, params) {
        const cfg = resolvePluginConfig(api);
        const runDir = params.runId ? resolveArtifacts(cfg.stateDir, String(params.runId)).runDir : latestRunDir(cfg.stateDir);
        const result = await runJobSpySearch(runDir);
        return { content: [{ type: "text", text: JSON.stringify(result) }] };
      },
    });

    api.registerTool({
      name: "job_search_spawn_evaluators",
      description: "Spawn concurrent evaluator subagents, one per listing, writing state-backed artifacts into evaluations/<runId>/.",
      parameters: Type.Object({
        runId: Type.String(),
        profilePath: Type.String(),
        limit: Type.Optional(Type.Integer({ minimum: 1 })),
        timeoutMs: Type.Optional(Type.Integer({ minimum: 1 })),
      }),
      async execute(_id, params) {
        const cfg = resolvePluginConfig(api);
        const result = await spawnEvaluators(api, cfg.stateDir, params as Json);
        return { content: [{ type: "text", text: JSON.stringify(result) }] };
      },
    });

    api.registerTool({
      name: "job_search_export_run",
      description: "Aggregate evaluation artifacts for a run and export them into an Excel workbook sorted by score.",
      parameters: Type.Object({
        runId: Type.String(),
      }),
      async execute(_id, params) {
        const cfg = resolvePluginConfig(api);
        const outputPath = exportRun(cfg.stateDir, String(params.runId));
        return { content: [{ type: "text", text: JSON.stringify({ runId: params.runId, outputPath }) }] };
      },
    });

    api.registerTool({
      name: "job_search_full_run",
      description: "Prepare, retrieve, evaluate concurrently, and export a full job search run backed by OpenClaw state storage.",
      parameters: Type.Object({
        runId: Type.Optional(Type.String()),
        profilePath: Type.String(),
        candidateUnderstanding: Type.Optional(Type.Any()),
        queries: Type.Array(Type.Any()),
        evaluationLimit: Type.Optional(Type.Integer({ minimum: 1 })),
        timeoutMs: Type.Optional(Type.Integer({ minimum: 1 })),
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
          queries: params.queries,
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
        const retrieval = await runJobSpySearch(artifacts.runDir);
        const evaluation = await spawnEvaluators(api, cfg.stateDir, {
          runId,
          profilePath,
          limit: params.evaluationLimit ?? cfg.evaluationConcurrency,
          timeoutMs: params.timeoutMs,
        });
        const exportPath = exportRun(cfg.stateDir, runId);
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({ runId, retrieval, evaluation, exportPath }),
            },
          ],
        };
      },
    });
  },
});
