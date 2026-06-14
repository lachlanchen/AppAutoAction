# Editable Figure Pipeline

This is the product rule for AgInTi LabCanvas paper figures: figure generation must be editable, atomic, and maintainable. A single generated bitmap is allowed only as an overview concept, never as the final source of truth.

## Core Principle

The studio should generate an overview first, then decompose the figure into small named parts. Each part keeps its own source, prompt, tool metadata, preview, and edit history. The final paper figure is assembled from these parts so the user can revise one panel, icon, device, label, or diagram element without regenerating everything.

## Workflow

1. Generate an overview concept with AgInTi or image generation.
2. Split the overview into atomic figure parts: panels, icons, labels, arrows, device modules, BioRender assets, OpenSCAD parts, Blender renders, and TeX layers.
3. Route each part to the best tool:
   - BioRender for academic icon/template assets.
   - Image generation for concept art, visual style exploration, and raster backgrounds.
   - OpenSCAD for editable mechanical/device geometry.
   - Blender for 3D device setup, optics, lighting, and rendered perspective.
   - TeX for clipping, panel composition, labels, callouts, and final paper-safe assembly.
4. Register every source and output as an artifact.
5. Assemble the figure from part manifests, not from a flattened image.
6. Let chat edit the full figure or any atomic part.

## Figure Project Shape

Future figure projects should follow a structure like:

```text
output/webapp/figures/<figure-id>/
  figure.json              # graph of panels, parts, tools, and assembly order
  overview/                # generated concept image and notes
  parts/<part-id>/         # prompt, source, preview, metadata, edit history
  biorender/               # BioRender asset references and exports
  openscad/                # .scad source and generated previews
  blender/                 # .blend files, scene specs, renders
  tex/                     # clipping and assembly source
  exports/                 # final SVG/PDF/PNG outputs
```

## UI Contract

The canvas should show both:

- Overview: the whole figure or experiment setup.
- Editable version: selectable panels, parts, and source layers.

Use a game-style minimap in the top-right corner, similar to a LoL overview map. The minimap should show the entire figure, highlight the current viewport/selection, and allow clicking to jump to a panel or part. Selecting a part opens its source, tool settings, prompt, preview, and edit actions.

## Chat Editing

Chat commands should target either the whole figure or a part:

```text
Make the overview clearer and split panel B into device, sample, and detector parts.
Replace the cell icon in panel A with BioRender style.
Regenerate only the detector icon with AgInTi image generation.
Update the OpenSCAD mount and rerender the Blender device setup.
Use TeX to clip the microscopy inset and align labels across all panels.
```

Codex should manage source files, manifests, TeX assembly, and deterministic transforms. AgInTi should provide backend agent orchestration and image-generation calls. Neither backend should silently discard editable part sources.

## Maintainability Rules

- Preserve part IDs across edits.
- Store prompts and tool settings beside each part.
- Prefer vector, CAD, TeX, or scene-spec sources when possible.
- Use raster image generation for overview and visual assets, not as the only final representation.
- Rebuild final exports from the manifest and TeX assembly.
- Publish overview and editable-part artifacts together in the canvas.
