# npm Package

AppAutoAction is packaged for npm as `@lazyingart/app-auto-action`.

Current published version: `0.1.0`.

## Install

```bash
npm install -g @lazyingart/app-auto-action
app-auto-action --version
app-auto-action webapp start --port 19473
```

The npm package is a thin Node wrapper around the bundled Python source. It requires Python 3.10+ on `PATH`; set `APPAUTOACTION_PYTHON=/path/to/python` if needed.

## Package Checks

```bash
npm test
npm run pack:dry-run
npm pack
```

The package includes the Python source, static web assets, examples, docs, bridges, configs, localized READMEs, and CLI wrappers. It excludes local outputs, `.env`, `.npmrc`, logs, caches, and generated tarballs.

## Publish

For the normal local release path, run the release helper from a clean working tree:

```bash
npm run release:npm:dry-run
npm run release:npm -- patch
```

Use `minor`, `major`, or an exact `x.y.z` version instead of `patch` when needed. For example, `npm run release:npm -- minor --dry-run` rehearses a minor release without changing files. The helper verifies npm auth, checks that the target version is not already published, runs tests, performs a dry-run pack, commits `Release vX.Y.Z`, tags `vX.Y.Z`, publishes to npm, verifies a temp-prefix install, then pushes the commit and tag.

If npm web/2FA approval times out after the release commit and tag are created, approve a fresh prompt and finish the same version with:

```bash
npm run publish:npm:current
```

Use `-- --no-push` when you want to publish but push the release commit/tag manually afterward.

Prefer GitHub Actions trusted publishing once npm trust is configured for this repository. The workflow is `.github/workflows/npm-publish.yml` and publishes with provenance.

Trusted Publisher settings on npm:

- Package: `@lazyingart/app-auto-action`
- Publisher: GitHub Actions
- Repository: `lachlanchen/AppAutoAction`
- Workflow filename: `npm-publish.yml`
- Environment: blank, unless a GitHub deployment environment is added later

Equivalent setup command:

```bash
npm install -g npm@^11.10.0
npm trust github @lazyingart/app-auto-action --repo lachlanchen/AppAutoAction --file npm-publish.yml
```

If the CLI reports that 2FA is required without opening a browser flow, configure the trusted publisher from the npm package settings page using the same package, repository, and workflow filename above.

For local bootstrap publishing, use a temporary npm config generated from an uncommitted env file:

```bash
APPAUTOACTION_NPM_ENV=../Agent/AgInTiFlow/.env npm run publish:env:whoami
APPAUTOACTION_NPM_ENV=../Agent/AgInTiFlow/.env npm run publish:env
```

`APPAUTOACTION_NPM_ENV` can also point to `../AAPS/.env` when that file contains `NPM_TOKEN` or `NODE_AUTH_TOKEN`. The helper writes a temporary `.npmrc`, runs npm, and deletes the credential material. Never commit npm tokens, `.env`, `.npmrc`, OTPs, or debug logs.
