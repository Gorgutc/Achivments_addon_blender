#!/usr/bin/env node
// Git-hook dispatcher (zero dependencies). Called by the hooks that
// tools/install-hooks.mjs writes. Usage:
//   node tools/git-gate.mjs pre-commit   # runs frozen-guard + verify.fast
//   node tools/git-gate.mjs pre-push     # runs verify.ship||deep + check-kit +
//                                        #   sync-harness --check + evidence-gate
// Every step is optional/no-op when not configured. Exits non-zero on failure.
//
// The kit's helper steps are adoptable one at a time: each of frozen-guard,
// check-kit, sync-harness and evidence-gate runs only if its tool file is
// present, and is announced as "[git-gate] skip: tools/<name> not present"
// otherwise. A project that copies in only the pieces it wants — or deletes one
// it does not (e.g. check-kit after relocating agentsRoot/hooksJson) — still
// gets a working gate. The verify tiers themselves are unaffected: they run
// exactly when .agent-kit.json configures them.

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

const ROOT = projectRoot();
const stage = process.argv[2] || "pre-commit";

let cfg = {};
try {
  cfg = JSON.parse(fs.readFileSync(path.join(ROOT, ".agent-kit.json"), "utf8"));
} catch {
  /* no config */
}
const v = cfg.verify || {};

function run(cmd) {
  process.stdout.write(`[git-gate:${stage}] ${cmd}\n`);
  execSync(cmd, { cwd: ROOT, stdio: "inherit" });
}
function node(script, args = "") {
  run(`node ${JSON.stringify(path.join(ROOT, script))}${args ? " " + args : ""}`);
}
// A helper the project has not adopted (or has deliberately dropped) is skipped
// out loud, not silently and not fatally.
function nodeIfPresent(script, args = "") {
  if (!fs.existsSync(path.join(ROOT, script))) {
    process.stdout.write(`[git-gate] skip: ${script} not present\n`);
    return;
  }
  node(script, args);
}

try {
  if (stage === "pre-commit") {
    nodeIfPresent("tools/frozen-guard.mjs"); // no-op when frozenPaths is empty
    const cmd = v.fast || cfg.verifyCommand;
    if (cmd) run(cmd);
  } else if (stage === "pre-push") {
    const cmd = v.ship || v.deep || v.fast || cfg.verifyCommand;
    if (cmd) run(cmd);
    nodeIfPresent("tools/check-kit.mjs");
    nodeIfPresent("tools/sync-harness.mjs", "--check"); // no-op when mirror is unconfigured
    nodeIfPresent("tools/evidence-gate.mjs");
  } else {
    process.stderr.write(`[git-gate] unknown stage: ${stage}\n`);
    process.exit(2);
  }
  process.exit(0);
} catch (err) {
  process.stderr.write(`[git-gate:${stage}] FAILED — commit/push blocked.\n`);
  process.exit(typeof err.status === "number" ? err.status : 1);
}
