# Studio CLI

AgInTi LabCanvas's studio CLI mirrors the web app. It follows the AAPS and AgInTiFlow pattern: actions should be runnable from the terminal, produce durable artifacts, support `--json`, and default to safe dry-run when talking to external tools.

## Web App Control

Use `webapp` to control the local studio in tmux:

```bash
labcanvas webapp start --port 19473
labcanvas webapp status --json
labcanvas webapp restart
labcanvas webapp stop
```

The default session is `labcanvas-web`. The command prints the URL when running.

## Studio Status

```bash
labcanvas studio status
labcanvas studio settings --json
labcanvas studio artifacts
labcanvas studio targets
```

These commands read the same `output/webapp/` state as the browser UI.

## Artifact Actions

Generate an editable SVG grid plus AgInTi image-generation dry-run artifacts:

```bash
labcanvas studio figure-grid "optical device icons 2x3" --rows 2 --cols 3
```

Export a scene spec to OpenSCAD and register it in the canvas manifest:

```bash
labcanvas studio openscad examples/paper-optics-setup.scene.json
```

Dry-run any configured registry target and save the dispatch envelope:

```bash
labcanvas studio dispatch blender "Prepare an editable paper figure device setup"
labcanvas studio dispatch biorender "Find BioRender assets for panel A" --json
```

Use `--live` only when the target bridge is configured and the side effects are intended.

## CLI/Web Alignment

The CLI and web app call the same backend functions for figure grids, OpenSCAD export, artifact registration, target listing, and target dispatch. This keeps terminal runs, browser runs, and agent-driven runs pointed at the same artifact manifest and backend settings.

## Design Notes From AAPS And AgInTiFlow

- AAPS-style commands expose focused verbs, validate project state, and return JSON for automation.
- AgInTiFlow-style commands keep image generation and web control available from the CLI, while preserving artifacts for the canvas.
- AgInTi LabCanvas uses both ideas: every studio action should be scriptable, visible in the web canvas, and safe to inspect before live tool execution.
