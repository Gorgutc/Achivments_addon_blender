#!/usr/bin/env node
// Pre-commit guard for frozen paths (zero dependencies).
//
// Reads `frozenPaths` (globs) from .agent-kit.json:
//   "frozenPaths": ["docs/frozen-decisions.md", "vendor/**", "**/*.lock"]
// A commit that stages a matching file is blocked, so a frozen decision cannot
// drift in by accident. No .agent-kit.json / no frozen paths configured -> pass;
// an .agent-kit.json that exists but does not parse -> fail (never fail-open).
//   node tools/frozen-guard.mjs          # guard the staged set (pre-commit)
//   node tools/frozen-guard.mjs --list   # print the configured globs
//
// The staged set is enumerated with rename detection OFF, so renaming a frozen
// file shows up as delete(old) + add(new) and cannot slip past the globs.
//
// Where durable decisions are recorded is configurable — a repo that keeps its
// frozen list somewhere else sets the optional `decisionsFile` key:
//   "decisionsFile": "docs/adr/frozen.md"   // default: docs/frozen-decisions.md
// Every message that names the file (--list, the override notice, the failure)
// uses that path. Present-but-not-a-non-empty-string is a hard error.
//
// Owner escape hatch: set OWNER_OVERRIDE=1 for the commit — one-shot, never a
// standing session variable. The override is announced, never silent — record
// the reasoning in the decisions file.
//
// Exit 0 if nothing frozen is staged (or the override is set), else 1.

import { execSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import process from "node:process";

function projectRoot() {
  try {
    return execSync("git rev-parse --show-toplevel", { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] }).trim();
  } catch {
    return process.cwd();
  }
}

// Same glob dialect as tools/evidence-gate.mjs (copied verbatim so both gates
// read a config the same way, and neither grows a dependency).
function globToRegExp(glob) {
  let re = "^";
  for (let i = 0; i < glob.length; ) {
    if (glob[i] === "*" && glob[i + 1] === "*") {
      if (glob[i + 2] === "/") {
        re += "(?:.*/)?";
        i += 3;
      } else {
        re += ".*";
        i += 2;
      }
    } else if (glob[i] === "*") {
      re += "[^/]*";
      i += 1;
    } else if ("\\^$+?.()|[]{}".includes(glob[i])) {
      re += "\\" + glob[i];
      i += 1;
    } else {
      re += glob[i];
      i += 1;
    }
  }
  return new RegExp(re + "$");
}

const ROOT = projectRoot();

// Where durable decisions live, unless .agent-kit.json overrides it.
const DEFAULT_DECISIONS_FILE = "docs/frozen-decisions.md";

// --no-renames: a rename must be seen as delete(old) + add(new), otherwise git
// lists only the destination and a frozen file can be renamed (and edited) past
// the guard. -z: NUL-separated and, crucially, *unquoted* — with the default
// core.quotePath=true a non-ASCII path comes back octal-escaped inside quotes
// and matches no glob at all.
function stagedFiles() {
  try {
    return execSync("git diff --name-only --cached --no-renames -z", {
      cwd: ROOT,
      encoding: "utf8",
      stdio: ["ignore", "pipe", "ignore"]
    })
      .split("\0")
      .map((s) => s.replace(/\\/g, "/"))
      .filter(Boolean);
  } catch {
    return [];
  }
}

function main() {
  let cfg = {};
  const cfgPath = path.join(ROOT, ".agent-kit.json");
  if (fs.existsSync(cfgPath)) {
    try {
      cfg = JSON.parse(fs.readFileSync(cfgPath, "utf8"));
    } catch (e) {
      // Fail closed: a broken config (merge markers, trailing comma) is exactly
      // what an edit to the frozen policy looks like mid-conflict.
      process.stderr.write(`frozen-guard: FAIL — .agent-kit.json exists but could not be parsed: ${e.message}\n`);
      process.stderr.write("The guard will not run fail-open. Fix the JSON, then re-run the commit.\n");
      return 1;
    }
  }
  const globs = Array.isArray(cfg.frozenPaths)
    ? cfg.frozenPaths.filter((g) => typeof g === "string" && g.trim())
    : [];

  // Optional override of the decisions doc. A key that IS present must be
  // well-formed — same shape rule (and wording) as tools/check-kit.mjs; a bad
  // value is a hard error rather than a silent fallback to the default.
  const declaresDecisionsFile = "decisionsFile" in cfg && cfg.decisionsFile !== undefined;
  if (declaresDecisionsFile && (typeof cfg.decisionsFile !== "string" || !cfg.decisionsFile.trim())) {
    process.stderr.write("frozen-guard: FAIL — decisionsFile must be a non-empty string\n");
    return 1;
  }
  const decisionsFile = declaresDecisionsFile ? cfg.decisionsFile : DEFAULT_DECISIONS_FILE;

  if (process.argv.includes("--list")) {
    process.stdout.write(`frozen-guard: ${globs.length} frozen path glob(s) configured.\n`);
    for (const g of globs) process.stdout.write(`- ${g}\n`);
    if (!globs.length) process.stdout.write("(none)\n");
    process.stdout.write(`Durable decisions are recorded in ${decisionsFile}.\n`);
    return 0;
  }

  if (!globs.length) {
    process.stdout.write("frozen-guard: no frozen paths configured — pass.\n");
    return 0;
  }

  const compiled = globs.map((glob) => ({ glob, re: globToRegExp(glob) }));
  const hits = [];
  for (const file of stagedFiles()) {
    const match = compiled.find((c) => c.re.test(file));
    if (match) hits.push({ file, glob: match.glob });
  }

  if (!hits.length) {
    process.stdout.write(`frozen-guard: ${globs.length} frozen glob(s) checked, nothing frozen staged.\n`);
    return 0;
  }

  if (process.env.OWNER_OVERRIDE === "1") {
    process.stdout.write("frozen-guard: OWNER_OVERRIDE accepted — committing frozen paths:\n");
    for (const h of hits) process.stdout.write(`- ${h.file}  (matched: ${h.glob})\n`);
    process.stdout.write(`Record the decision in ${decisionsFile}.\n`);
    return 0;
  }

  process.stderr.write("frozen-guard: FAIL — staged changes touch frozen paths\n");
  for (const h of hits) process.stderr.write(`- ${h.file}  (matched: ${h.glob})\n`);
  process.stderr.write('These globs are listed in "frozenPaths" of .agent-kit.json.\n');
  process.stderr.write("Unstage them (git restore --staged <file>), or override as the owner:\n");
  process.stderr.write("  sh:         OWNER_OVERRIDE=1 git commit ...\n");
  process.stderr.write("  PowerShell: $env:OWNER_OVERRIDE='1'; git commit ...; $env:OWNER_OVERRIDE=$null\n");
  process.stderr.write(`Durable decisions belong in ${decisionsFile}.\n`);
  return 1;
}

process.exitCode = main();
