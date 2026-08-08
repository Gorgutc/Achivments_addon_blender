#!/usr/bin/env node
// Canonical harness -> generated Claude mirror (zero dependencies).
//
// Some repos keep ONE canonical layer (skills as directories, agent contracts as
// TOML, hook wiring as JSON) and expose it to Claude Code as a *generated*
// mirror under `.claude/`. This tool writes that mirror and proves it never
// drifts:
//   node tools/sync-harness.mjs --write   # regenerate the mirror from the canon
//   node tools/sync-harness.mjs --check   # verify parity (CI / pre-push gate)
// Conventional npm aliases: "sync:harness" -> --write, "check:parity" -> --check.
//
// Configured by the "mirror" key of .agent-kit.json. Absent or null = the
// feature is off: --check passes as a no-op, --write explains how to enable it.
//   "mirror": {
//     "skillRoots": [".agents/skills"],  // canonical skill dirs (one dir per skill)
//     "agentsRoot": ".codex/agents",     // canonical *.toml agent contracts
//     "hooksJson":  ".codex/hooks.json", // canonical hook wiring
//     "claudeDir":  ".claude"            // generated mirror root
//   }
// Every key is optional; the values above are the defaults. A key that IS
// present must be well-formed — same shape rules as tools/check-kit.mjs, and a
// bad value is a hard error in both modes rather than a silent fallback.
// Hook scripts are expected next to their wiring, in <dir of hooksJson>/hooks/;
// the parity matcher is derived from that directory. Script names are recognized
// with any of these extensions — .js .mjs .cjs .py .sh .ps1 — so a repo whose
// hooks are Python or shell scripts is compared exactly like a .js one.
// Agent contracts are read in either spelling: the instructions body may be
// `developer_instructions = """..."""` or `prompt = """..."""` (the former wins
// when both are present), and read-only may be declared as
// `sandbox_mode = "read-only"` or `read_only = true` (either one adds
// `tools: Read, Grep, Glob` to the mirror; neither = no tools line). A contract
// that yields NO instructions body is a hard error in both --write and --check
// — an empty mirror agent is never produced silently.
// Caveat: tools/check-kit.mjs self-checks the kit's own `.codex/` layout, so a
// relocated agentsRoot/hooksJson is honored here but not there — see AGENTS.md.
//
// The mirror (<claudeDir>/skills, <claudeDir>/agents) is generated output — it
// is wiped and rewritten by --write and must never be edited by hand. --write
// refuses (and deletes nothing) when the canon yields 0 skills AND 0 agents.
//
// Exit 0 if the mirror matches the canon, else 1.

import { execSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import process from "node:process";

const MIRROR_DEFAULTS = {
  skillRoots: [".agents/skills"],
  agentsRoot: ".codex/agents",
  hooksJson: ".codex/hooks.json",
  claudeDir: ".claude"
};

// Extensions compared after CRLF normalization; anything else must be byte-equal.
const TEXT_EXTENSIONS = new Set([
  ".md",
  ".markdown",
  ".yaml",
  ".yml",
  ".json",
  ".jsonc",
  ".js",
  ".mjs",
  ".toml",
  ".txt",
  ".html",
  ".css",
  ".sh"
]);

function projectRoot() {
  try {
    return execSync("git rev-parse --show-toplevel", { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] }).trim();
  } catch {
    return process.cwd();
  }
}

const ROOT = projectRoot();

const checks = [];
function check(name, condition, detail = "") {
  checks.push({ name, condition: Boolean(condition), detail });
}

function listFilesRecursive(startPath, prefix = "") {
  if (!fs.existsSync(startPath)) return [];
  const files = [];
  for (const entry of fs.readdirSync(startPath, { withFileTypes: true })) {
    const rel = prefix ? `${prefix}/${entry.name}` : entry.name;
    if (entry.isDirectory()) files.push(...listFilesRecursive(path.join(startPath, entry.name), rel));
    else if (entry.isFile()) files.push(rel);
  }
  return files.sort();
}

function normalizedEquals(fileA, fileB) {
  const bufA = fs.readFileSync(fileA);
  const bufB = fs.readFileSync(fileB);
  if (bufA.equals(bufB)) return true;
  if (!TEXT_EXTENSIONS.has(path.extname(fileA).toLowerCase())) return false;
  const normalize = (buf) => buf.toString("utf8").replaceAll("\r\n", "\n");
  return normalize(bufA) === normalize(bufB);
}

// One skill = one directory under a canonical skill root. A name may exist in
// only one root; two roots claiming the same skill is a hard error, not a race.
function collectSkillSources(skillRootsAbs) {
  const sources = new Map();
  for (const skillsRoot of skillRootsAbs) {
    if (!fs.existsSync(skillsRoot)) continue;
    for (const entry of fs.readdirSync(skillsRoot, { withFileTypes: true })) {
      if (!entry.isDirectory()) continue;
      if (sources.has(entry.name)) {
        throw new Error(`duplicate skill name across canonical roots: ${entry.name}`);
      }
      sources.set(entry.name, path.join(skillsRoot, entry.name));
    }
  }
  return sources;
}

// Minimal TOML reader for the agent-contract subset: plain double-quoted
// scalars, a bare boolean, and one triple-quoted instructions block.
//
// Two contract spellings are in the wild and both are read here:
//   instructions:  developer_instructions = """..."""   or  prompt = """..."""
//   read-only:     sandbox_mode = "read-only"           or  read_only = true
// developer_instructions wins when a contract carries both; a contract that
// declares neither read-only form is simply not read-only (no tools line, no
// crash). A contract with NO instructions block is a hard error — see
// agentMarkdown.
function parseAgentToml(file) {
  const raw = fs.readFileSync(file, "utf8");
  const scalar = (key) => {
    const match = raw.match(new RegExp(`^${key}\\s*=\\s*"([^"]*)"`, "m"));
    const value = match ? match[1] : "";
    if (value.includes("\\")) {
      throw new Error(`unsupported escape sequence in ${path.basename(file)} key "${key}"; keep contract values plain`);
    }
    return value;
  };
  const bool = (key) => {
    const match = raw.match(new RegExp(`^${key}\\s*=\\s*(true|false)\\b`, "m"));
    return match ? match[1] === "true" : null;
  };
  const block = (key) => {
    const match = raw.match(new RegExp(`^${key}\\s*=\\s*"""\\r?\\n?([\\s\\S]*?)"""`, "m"));
    return match ? match[1].replaceAll("\r\n", "\n").trim() : "";
  };
  return {
    name: scalar("name"),
    description: scalar("description"),
    // First non-empty wins, developer_instructions preferred.
    instructions: block("developer_instructions") || block("prompt"),
    readOnly: scalar("sandbox_mode") === "read-only" || bool("read_only") === true
  };
}

function agentMarkdown(tomlFile, agentsRootRel) {
  const agent = parseAgentToml(tomlFile);
  const contractRel = `${agentsRootRel}/${path.basename(tomlFile)}`;
  // A contract whose instructions block is missing (or spelled in a way this
  // reader does not know) used to mirror an agent with an EMPTY body — and
  // --check compared that empty mirror to the same empty expectation, so both
  // modes reported success. Fail loudly in both instead; an empty mirror agent
  // must never be produced silently.
  if (!agent.instructions) {
    throw new Error(
      `agent contract has no instructions block: ${contractRel}` +
        ' — expected developer_instructions = """..."""  or  prompt = """..."""'
    );
  }
  const kebab = agent.name.replaceAll("_", "-");
  const lines = ["---", `name: ${kebab}`, `description: ${JSON.stringify(agent.description)}`];
  if (agent.readOnly) lines.push("tools: Read, Grep, Glob");
  lines.push("---", "");
  lines.push(
    `<!-- Generated from ${agentsRootRel}/${path.basename(tomlFile)} by tools/sync-harness.mjs.` +
      " Do not edit; run: node tools/sync-harness.mjs --write -->",
    ""
  );
  lines.push(agent.instructions, "");
  return { kebab, content: lines.join("\n") };
}

function skillsReadme(cfg) {
  return [
    "# Generated Claude Code skill mirror",
    "",
    "Every directory here is a generated copy of a canonical skill from",
    cfg.skillRoots.map((r) => `\`${r}/\``).join(", ") + ".",
    "Do not edit these copies. Edit the canonical skill, then run",
    "`node tools/sync-harness.mjs --write`.",
    "Parity is enforced by `node tools/sync-harness.mjs --check`.",
    ""
  ].join("\n");
}

function expectedMirrorState(cfg) {
  const skillFiles = new Map();
  for (const [name, sourceDir] of collectSkillSources(cfg.skillRootsAbs)) {
    for (const rel of listFilesRecursive(sourceDir)) {
      skillFiles.set(`${name}/${rel}`, path.join(sourceDir, rel));
    }
  }
  const agents = fs.existsSync(cfg.agentsRootAbs)
    ? fs
        .readdirSync(cfg.agentsRootAbs)
        .filter((file) => file.endsWith(".toml"))
        .sort()
        .map((file) => agentMarkdown(path.join(cfg.agentsRootAbs, file), cfg.agentsRoot))
    : [];
  // Two contracts whose names kebab-case to the same file would make --write
  // last-wins and --check unsatisfiable; same hard error as duplicate skills.
  const seenAgents = new Set();
  for (const agent of agents) {
    if (seenAgents.has(agent.kebab)) {
      throw new Error(`duplicate agent name after kebab-case: ${agent.kebab}`);
    }
    seenAgents.add(agent.kebab);
  }
  return { skillFiles, agents };
}

// Script extensions the hook matcher recognizes. One list feeds both the regex
// alternation and its failure message, so they can never drift apart. Hook
// scripts are not always JavaScript: a uv/Python repo wires `.py`, others `.sh`
// or `.ps1`, and all of them must be comparable by name.
const HOOK_SCRIPT_EXTENSIONS = ["js", "mjs", "cjs", "py", "sh", "ps1"];

// Hook scripts live next to their wiring, in <dir of hooksJson>/hooks/. The
// reference matcher is derived from that directory (not hardcoded to .codex),
// so a relocated hooks config is still compared by script name. Both slash
// directions are accepted because the two harnesses spell commands differently.
// The captured name includes its extension, so the existence check below works
// for every extension in HOOK_SCRIPT_EXTENSIONS.
function hookScriptRefRegex(hooksJsonRel) {
  const escape = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const segments = path
    .dirname(hooksJsonRel)
    .split(/[\\/]/)
    .filter((s) => s && s !== ".");
  const head = segments.length ? `${segments.map(escape).join("[\\\\/]")}[\\\\/]` : "(?:^|[^\\w\\\\/])";
  return new RegExp(`${head}hooks[\\\\/]([\\w-]+\\.(?:${HOOK_SCRIPT_EXTENSIONS.join("|")}))`, "g");
}

// Hook wiring is compared by the script names each event references. Also
// reports how many command strings were seen vs how many references were
// extractable, so "no references at all" can FAIL instead of passing vacuously.
function hookScriptsByEvent(config, scriptRef) {
  const byEvent = new Map();
  let commandCount = 0;
  let refCount = 0;
  for (const [event, entries] of Object.entries(config.hooks || {})) {
    const scripts = new Set();
    for (const entry of entries || []) {
      for (const hook of entry.hooks || []) {
        const commands = [hook.command, hook.commandWindows].filter((c) => typeof c === "string" && c.trim());
        commandCount += commands.length;
        for (const match of commands.join("\n").matchAll(scriptRef)) {
          scripts.add(match[1]);
          refCount += 1;
        }
      }
    }
    byEvent.set(event, scripts);
  }
  return { byEvent, commandCount, refCount };
}

function loadMirrorConfig() {
  const cfgPath = path.join(ROOT, ".agent-kit.json");
  if (!fs.existsSync(cfgPath)) {
    process.stderr.write(`sync-harness: no .agent-kit.json at ${ROOT} — run this from an agent-kit project root.\n`);
    return null;
  }
  let raw;
  try {
    raw = JSON.parse(fs.readFileSync(cfgPath, "utf8"));
  } catch (e) {
    process.stderr.write(`sync-harness: .agent-kit.json invalid JSON: ${e.message}\n`);
    return null;
  }
  const mirror = raw.mirror;
  if (mirror === null || mirror === undefined) return { configured: false };
  if (typeof mirror !== "object" || Array.isArray(mirror)) {
    process.stderr.write('sync-harness: .agent-kit.json "mirror" must be null or an object.\n');
    return null;
  }
  // Absent keys take the defaults; a present key must be well-formed. Same
  // wording as tools/check-kit.mjs so the two validators never disagree.
  const errors = [];
  if ("skillRoots" in mirror) {
    const roots = mirror.skillRoots;
    if (!Array.isArray(roots) || !roots.length || roots.some((r) => typeof r !== "string" || !r.trim())) {
      errors.push("mirror.skillRoots must be a non-empty array of non-empty strings");
    }
  }
  for (const key of ["agentsRoot", "hooksJson", "claudeDir"]) {
    if (key in mirror && (typeof mirror[key] !== "string" || !mirror[key].trim())) {
      errors.push(`mirror.${key} must be a non-empty string`);
    }
  }
  if (errors.length) {
    for (const message of errors) process.stderr.write(`sync-harness: ${message}\n`);
    return null;
  }

  const skillRoots = "skillRoots" in mirror ? mirror.skillRoots : MIRROR_DEFAULTS.skillRoots;
  const agentsRoot = "agentsRoot" in mirror ? mirror.agentsRoot : MIRROR_DEFAULTS.agentsRoot;
  const hooksJson = "hooksJson" in mirror ? mirror.hooksJson : MIRROR_DEFAULTS.hooksJson;
  const claudeDir = "claudeDir" in mirror ? mirror.claudeDir : MIRROR_DEFAULTS.claudeDir;
  const hookScriptsDir = path.posix.join(path.dirname(hooksJson).replaceAll("\\", "/"), "hooks");
  return {
    configured: true,
    skillRoots,
    agentsRoot,
    hooksJson,
    claudeDir,
    // Which keys the user actually declared: a defaulted path that is absent is
    // "this project has none", a declared path that is absent is a mistake.
    agentsRootExplicit: "agentsRoot" in mirror,
    skillRootsAbs: skillRoots.map((rel) => path.join(ROOT, rel)),
    agentsRootAbs: path.join(ROOT, agentsRoot),
    hooksJsonAbs: path.join(ROOT, hooksJson),
    // Hook scripts live next to their wiring, in <dir of hooksJson>/hooks/.
    hookScriptsDir,
    hookScriptsDirAbs: path.join(ROOT, hookScriptsDir),
    mirrorSkillsAbs: path.join(ROOT, claudeDir, "skills"),
    mirrorAgentsAbs: path.join(ROOT, claudeDir, "agents"),
    settingsAbs: path.join(ROOT, claudeDir, "settings.json")
  };
}

function explainUnconfigured() {
  process.stderr.write('sync-harness: "mirror" is not configured in .agent-kit.json — nothing to generate.\n');
  process.stderr.write("Enable the generated Claude mirror by adding, at the top level of .agent-kit.json:\n");
  process.stderr.write('  "mirror": {\n');
  process.stderr.write('    "skillRoots": [".agents/skills"],\n');
  process.stderr.write('    "agentsRoot": ".codex/agents",\n');
  process.stderr.write('    "hooksJson":  ".codex/hooks.json",\n');
  process.stderr.write('    "claudeDir":  ".claude"\n');
  process.stderr.write("  }\n");
  process.stderr.write("Every key is optional; the values above are the defaults.\n");
}

function write(cfg) {
  const { skillFiles, agents } = expectedMirrorState(cfg);
  // An empty canon means "wipe everything" — almost always a misconfiguration
  // (mirror enabled before the canonical dirs exist) rather than an intent to
  // delete a hand-authored .claude/. Refuse before touching anything.
  if (!skillFiles.size && !agents.length) {
    process.stderr.write("sync-harness: refusing to write — the canon yields 0 skill files and 0 agents.\n");
    process.stderr.write(`  skill roots: ${cfg.skillRoots.join(", ")}\n`);
    process.stderr.write(`  agents root: ${cfg.agentsRoot}\n`);
    process.stderr.write(
      `Nothing was deleted. Populate the canonical dirs (or fix "mirror" in .agent-kit.json) before regenerating ${cfg.claudeDir}/.\n`
    );
    return 1;
  }
  fs.rmSync(cfg.mirrorSkillsAbs, { recursive: true, force: true });
  fs.rmSync(cfg.mirrorAgentsAbs, { recursive: true, force: true });
  for (const [rel, source] of skillFiles) {
    const target = path.join(cfg.mirrorSkillsAbs, rel);
    fs.mkdirSync(path.dirname(target), { recursive: true });
    fs.writeFileSync(target, fs.readFileSync(source));
  }
  fs.mkdirSync(cfg.mirrorSkillsAbs, { recursive: true });
  fs.writeFileSync(path.join(cfg.mirrorSkillsAbs, "README.md"), skillsReadme(cfg));
  fs.mkdirSync(cfg.mirrorAgentsAbs, { recursive: true });
  for (const agent of agents) {
    fs.writeFileSync(path.join(cfg.mirrorAgentsAbs, `${agent.kebab}.md`), agent.content);
  }
  const skillCount = new Set([...skillFiles.keys()].map((rel) => rel.split("/")[0])).size;
  process.stdout.write(
    `sync-harness: mirrored ${skillCount} skills (${skillFiles.size} files) and ${agents.length} agents into ${cfg.claudeDir}/\n`
  );
  return 0;
}

function verify(cfg) {
  const { skillFiles, agents } = expectedMirrorState(cfg);

  // A declared agentsRoot must exist; a defaulted one that is absent simply
  // means the project has no agent contracts (orphan detection still runs
  // below, so a stale mirror agent is still caught).
  if (fs.existsSync(cfg.agentsRootAbs)) {
    check(`${cfg.agentsRoot} directory exists`, true);
  } else if (cfg.agentsRootExplicit) {
    check(`${cfg.agentsRoot} directory exists`, false, 'declared as "agentsRoot" in .agent-kit.json');
  } else {
    check("agents root absent — 0 agent contracts", true, cfg.agentsRoot);
  }

  let skillMismatches = 0;
  for (const [rel, source] of skillFiles) {
    const target = path.join(cfg.mirrorSkillsAbs, rel);
    if (!fs.existsSync(target)) {
      skillMismatches += 1;
      check(`mirror skill file exists: ${rel}`, false);
    } else if (!normalizedEquals(source, target)) {
      skillMismatches += 1;
      check(`mirror skill file matches canon: ${rel}`, false);
    }
  }
  check("mirror skills match canon", skillMismatches === 0, `${skillFiles.size} files compared`);

  const expectedSkillPaths = new Set([...skillFiles.keys(), "README.md"]);
  const orphanSkillFiles = listFilesRecursive(cfg.mirrorSkillsAbs).filter((rel) => !expectedSkillPaths.has(rel));
  check(
    `no orphan files in ${cfg.claudeDir}/skills`,
    orphanSkillFiles.length === 0,
    orphanSkillFiles.slice(0, 3).join(", ")
  );

  for (const agent of agents) {
    const target = path.join(cfg.mirrorAgentsAbs, `${agent.kebab}.md`);
    const matches =
      fs.existsSync(target) && fs.readFileSync(target, "utf8").replaceAll("\r\n", "\n") === agent.content;
    check(`mirror agent matches contract: ${agent.kebab}`, matches);
  }
  const expectedAgentFiles = new Set(agents.map((agent) => `${agent.kebab}.md`));
  const orphanAgentFiles = listFilesRecursive(cfg.mirrorAgentsAbs).filter((rel) => !expectedAgentFiles.has(rel));
  check(
    `no orphan files in ${cfg.claudeDir}/agents`,
    orphanAgentFiles.length === 0,
    orphanAgentFiles.slice(0, 3).join(", ")
  );

  // The README body is a function of the configured skill roots, so presence is
  // not enough — a stale README means --write and --check disagree.
  const readmeAbs = path.join(cfg.mirrorSkillsAbs, "README.md");
  const readmeMatches =
    fs.existsSync(readmeAbs) && fs.readFileSync(readmeAbs, "utf8").replaceAll("\r\n", "\n") === skillsReadme(cfg);
  check(`${cfg.claudeDir}/skills README matches config`, readmeMatches);

  const settingsExists = fs.existsSync(cfg.settingsAbs);
  const canonHooksExists = fs.existsSync(cfg.hooksJsonAbs);
  if (settingsExists && canonHooksExists) {
    const scriptRef = hookScriptRefRegex(cfg.hooksJson);
    const claudeConfig = JSON.parse(fs.readFileSync(cfg.settingsAbs, "utf8"));
    const claude = hookScriptsByEvent(claudeConfig, scriptRef);
    const canon = hookScriptsByEvent(JSON.parse(fs.readFileSync(cfg.hooksJsonAbs, "utf8")), scriptRef);
    // Wired hooks whose commands reference no script we can recognize would
    // compare empty-set to empty-set — a vacuous pass. Say so instead.
    for (const side of [
      { label: cfg.hooksJson, parsed: canon },
      { label: `${cfg.claudeDir}/settings.json`, parsed: claude }
    ]) {
      if (side.parsed.commandCount && !side.parsed.refCount) {
        check(
          `${side.label}: hook script references extractable`,
          false,
          `no recognizable ${cfg.hookScriptsDir}/*.{${HOOK_SCRIPT_EXTENSIONS.join(",")}} references — parity cannot be checked`
        );
      }
    }
    for (const event of new Set([...canon.byEvent.keys(), ...claude.byEvent.keys()])) {
      const canonScripts = canon.byEvent.get(event) || new Set();
      const claudeScripts = claude.byEvent.get(event) || new Set();
      const same =
        canonScripts.size === claudeScripts.size && [...canonScripts].every((script) => claudeScripts.has(script));
      check(`hooks parity for ${event}`, same, `canon=[${[...canonScripts]}] mirror=[${[...claudeScripts]}]`);
      for (const script of new Set([...canonScripts, ...claudeScripts])) {
        check(`hook script exists: ${script}`, fs.existsSync(path.join(cfg.hookScriptsDirAbs, script)));
      }
    }
    // Only meaningful for a harness that actually wires PostToolUse.
    const postToolEntries = claudeConfig.hooks?.PostToolUse || [];
    if (postToolEntries.length) {
      const postToolMatchers = postToolEntries.flatMap((entry) => (entry.matcher || "").split("|"));
      check(
        "PostToolUse matcher covers Edit and Write",
        postToolMatchers.includes("Edit") && postToolMatchers.includes("Write"),
        postToolMatchers.join("|")
      );
    }
  } else if (settingsExists || canonHooksExists) {
    // One side wires hooks and the other does not — that is real drift.
    check(`${cfg.claudeDir}/settings.json exists`, settingsExists);
    check(`${cfg.hooksJson} exists`, canonHooksExists);
  } else {
    check("no hook wiring on either side — parity skipped", true);
  }

  const claudeMd = path.join(ROOT, "CLAUDE.md");
  check("CLAUDE.md imports AGENTS.md", fs.existsSync(claudeMd) && fs.readFileSync(claudeMd, "utf8").includes("@AGENTS.md"));

  let failed = 0;
  for (const item of checks) {
    const line = `${item.name}${item.detail ? ` - ${item.detail}` : ""}`;
    if (item.condition) {
      process.stdout.write(`[PASS] ${line}\n`);
    } else {
      failed += 1;
      process.stderr.write(`[FAIL] ${line}\n`);
    }
  }
  process.stdout.write(`SUMMARY: ${checks.length - failed}/${checks.length} PASS, ${failed} FAIL\n`);
  if (failed) process.stderr.write("Run: node tools/sync-harness.mjs --write to regenerate the mirror from the canon.\n");
  return failed ? 1 : 0;
}

function main() {
  const mode = process.argv.includes("--write") ? "write" : process.argv.includes("--check") ? "check" : null;
  if (!mode) {
    process.stderr.write("Usage: node tools/sync-harness.mjs --write | --check\n");
    return 1;
  }

  const cfg = loadMirrorConfig();
  if (!cfg) return 1;
  if (!cfg.configured) {
    if (mode === "check") {
      process.stdout.write("sync-harness: mirror not configured — pass.\n");
      return 0;
    }
    explainUnconfigured();
    return 1;
  }

  try {
    return mode === "write" ? write(cfg) : verify(cfg);
  } catch (e) {
    process.stderr.write(`sync-harness: ${e.message}\n`);
    return 1;
  }
}

process.exitCode = main();
