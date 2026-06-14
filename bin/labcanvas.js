#!/usr/bin/env node
"use strict";

const { spawnSync } = require("node:child_process");
const path = require("node:path");

const packageRoot = path.resolve(__dirname, "..");
const sourceRoot = path.join(packageRoot, "src");
const pythonCandidates = [
  process.env.LABCANVAS_PYTHON,
  process.env.APPAUTOACTION_PYTHON,
  process.env.PYTHON,
  process.platform === "win32" ? "python.exe" : "python3",
  "python",
].filter(Boolean);

function runWithPython(command) {
  const env = {
    ...process.env,
    PYTHONPATH: [sourceRoot, process.env.PYTHONPATH].filter(Boolean).join(path.delimiter),
  };
  return spawnSync(command, ["-m", "agenticapp", ...process.argv.slice(2)], {
    cwd: process.cwd(),
    env,
    stdio: "inherit",
  });
}

let lastError = null;
for (const command of pythonCandidates) {
  const result = runWithPython(command);
  if (!result.error) {
    process.exit(result.status ?? 0);
  }
  if (result.error.code !== "ENOENT") {
    console.error(result.error.message);
    process.exit(1);
  }
  lastError = result.error;
}

console.error(
  "AgInTi LabCanvas requires Python 3.10+. Set LABCANVAS_PYTHON to a Python executable if python3 is not on PATH."
);
if (lastError && process.env.LABCANVAS_DEBUG) {
  console.error(lastError.message);
}
process.exit(1);
