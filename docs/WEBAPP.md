# Web App

AppAutoAction includes a local chat, artifact canvas, and preview workspace for 3D experiment design and paper figures.

```bash
app-auto-action web --port 8787 --open
```

The app runs on `127.0.0.1` by default. If the requested port is busy, it chooses the next available port.

## Workflow

1. Chat to adjust the scene spec.
2. Generate an exact `NxM` SVG paper-figure grid from the canvas controls or chat.
3. Review artifacts in the canvas rail: SVG grids, AgInTi dry-run payloads, OpenSCAD files, Blender renders, `.blend` files, and scene specs.
4. Use Dry Run to validate Blender output paths.
5. Use Render to launch Blender headless.
6. Save backend settings for AgInTi image generation and BioRender MCP handoff.

The web app uses the same scene spec renderer documented in [SCENE_SPEC.md](SCENE_SPEC.md). It does not require API keys; chat edits are deterministic scene-spec mutations.
AgInTi image generation defaults to `--dry-run`, which writes a redacted prompt, request payload, and manifest without calling an image provider.

## Backends

- AgInTi: configured through command, workspace, provider, model, image size, and dry-run settings. Default command: `aginti image --json --dry-run`.
- BioRender: configured with the official MCP URL `https://mcp.services.biorender.com/mcp` and an auth environment variable name. The app does not store BioRender secrets.
- OpenSCAD: exports the current scene spec to a simplified `.scad` mechanical-layout proxy.
- Blender: renders the scene spec to PNG and `.blend` artifacts.

## API

| Route | Purpose |
|---|---|
| `GET /` | Static web app. |
| `GET /api/spec` | Load the default scene spec and preview image. |
| `GET /api/settings` | Load backend settings and detected status. |
| `POST /api/settings` | Save non-secret backend settings under `output/webapp/settings.json`. |
| `GET /api/artifacts` | List the project-local artifact manifest. |
| `POST /api/chat` | Apply a chat instruction to the current scene spec. |
| `POST /api/figure-grid` | Generate an exact SVG paper-figure grid and AgInTi image dry-run payloads. |
| `POST /api/openscad-export` | Export the current scene spec as OpenSCAD. |
| `POST /api/plan` | Validate and return a dry-run render plan. |
| `POST /api/render` | Render the current scene spec with Blender. |
| `GET /artifacts/...` | Serve generated SVG, PNG, `.blend`, `.scad`, text, and JSON artifacts. |

Generated files are written under `output/webapp/`.
