#!/usr/bin/env node
"use strict";

const { spawnSync } = require("node:child_process");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const repoRoot = path.resolve(__dirname, "..");
const packagePath = path.join(repoRoot, "package.json");
const npmCommand = process.platform === "win32" ? "npm.cmd" : "npm";
const gitCommand = process.platform === "win32" ? "git.exe" : "git";

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: repoRoot,
    encoding: "utf8",
    stdio: options.capture ? ["ignore", "pipe", "pipe"] : "inherit",
    env: process.env,
  });
  if (options.capture) return result;
  if (result.status !== 0) {
    throw new Error(`${command} ${args.join(" ")} failed with exit code ${result.status}`);
  }
  return result;
}

function readPackage() {
  return JSON.parse(fs.readFileSync(packagePath, "utf8"));
}

function writePackage(pkg) {
  fs.writeFileSync(packagePath, `${JSON.stringify(pkg, null, 2)}\n`);
}

function cleanGitRequired() {
  const status = run(gitCommand, ["status", "--porcelain"], { capture: true });
  if (status.status !== 0) throw new Error("Unable to read git status.");
  if (status.stdout.trim()) {
    throw new Error("Working tree is not clean. Commit or stash changes before releasing.");
  }
}

function bumpVersion(current, request) {
  const match = current.match(/^(\d+)\.(\d+)\.(\d+)$/);
  if (!match) throw new Error(`Unsupported current version: ${current}`);
  const parts = match.slice(1).map(Number);
  if (request === "patch") parts[2] += 1;
  else if (request === "minor") {
    parts[1] += 1;
    parts[2] = 0;
  } else if (request === "major") {
    parts[0] += 1;
    parts[1] = 0;
    parts[2] = 0;
  } else if (/^\d+\.\d+\.\d+$/.test(request)) {
    return request;
  } else {
    throw new Error("Usage: npm run release:npm -- <patch|minor|major|x.y.z> [--dry-run] [--no-push]");
  }
  return parts.join(".");
}

function ensureVersionAvailable(name, version) {
  const result = run(npmCommand, ["view", `${name}@${version}`, "version", "--json"], { capture: true });
  if (result.status === 0) {
    throw new Error(`${name}@${version} is already published on npm.`);
  }
  if (!`${result.stderr}\n${result.stdout}`.includes("E404")) {
    throw new Error(`Unable to verify npm registry availability for ${name}@${version}.`);
  }
}

function ensureNoTag(version) {
  const result = run(gitCommand, ["rev-parse", "-q", "--verify", `refs/tags/v${version}`], { capture: true });
  if (result.status === 0) throw new Error(`Tag v${version} already exists.`);
}

function updateLockfileIfPresent() {
  if (fs.existsSync(path.join(repoRoot, "package-lock.json"))) {
    run(npmCommand, ["install", "--package-lock-only", "--ignore-scripts"]);
  }
}

function packageFilesForCommit() {
  return ["package.json", "package-lock.json", "npm-shrinkwrap.json"].filter((file) =>
    fs.existsSync(path.join(repoRoot, file))
  );
}

function verifyInstall(name, version, binSpec) {
  const tempPrefix = fs.mkdtempSync(path.join(os.tmpdir(), "labcanvas-npm-install-"));
  try {
    run(npmCommand, ["install", "--prefix", tempPrefix, "-g", `${name}@${version}`]);
    const binNames = typeof binSpec === "string" ? [path.basename(binSpec)] : Object.keys(binSpec || {});
    for (const binName of binNames) {
      const binPath =
        process.platform === "win32" ? path.join(tempPrefix, `${binName}.cmd`) : path.join(tempPrefix, "bin", binName);
      run(binPath, ["--version"]);
    }
  } finally {
    fs.rmSync(tempPrefix, { recursive: true, force: true });
  }
}

function main() {
  const args = process.argv.slice(2);
  const request = args.find((arg) => !arg.startsWith("--")) || "patch";
  const noPush = args.includes("--no-push");
  const dryRun = args.includes("--dry-run");
  const currentOnly = request === "current";
  const pkg = readPackage();
  const targetVersion = currentOnly ? pkg.version : bumpVersion(pkg.version, request);

  cleanGitRequired();
  ensureVersionAvailable(pkg.name, targetVersion);
  if (!currentOnly) ensureNoTag(targetVersion);

  run(npmCommand, ["whoami"]);
  run(npmCommand, ["test"]);

  if (dryRun) {
    run(npmCommand, ["run", "pack:dry-run"]);
    console.log(`Dry run complete. Next releasable version would be ${pkg.name}@${targetVersion}.`);
    return;
  }

  if (!currentOnly) {
    pkg.version = targetVersion;
    writePackage(pkg);
    updateLockfileIfPresent();
    run(npmCommand, ["test"]);
    run(npmCommand, ["run", "pack:dry-run"]);
    run(gitCommand, ["add", ...packageFilesForCommit()]);
    run(gitCommand, ["commit", "-m", `Release v${targetVersion}`]);
    run(gitCommand, ["tag", "-a", `v${targetVersion}`, "-m", `Release v${targetVersion}`]);
  } else {
    run(npmCommand, ["run", "pack:dry-run"]);
  }

  console.log(`Publishing ${pkg.name}@${targetVersion}. Complete npm web/2FA prompts if they appear.`);
  run(npmCommand, ["publish", "--access", "public"]);
  run(npmCommand, ["view", `${pkg.name}@${targetVersion}`, "version", "dist.tarball", "--json"]);
  verifyInstall(pkg.name, targetVersion, pkg.bin);

  if (!noPush) {
    run(gitCommand, ["push", "origin", "HEAD", "--follow-tags"]);
  } else {
    console.log("Skipped git push because --no-push was supplied.");
  }
}

try {
  main();
} catch (error) {
  console.error(error instanceof Error ? error.message : String(error));
  process.exit(1);
}
