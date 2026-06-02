# Scene Specs For 3D Experiment Design

AppAutoAction can render paper-ready 3D setup diagrams from JSON scene specs. This turns an agent workflow such as "draw my optical bench" into a repeatable file-based process:

```text
scene spec JSON -> AppAutoAction CLI -> Blender headless -> PNG + .blend
```

## Commands

Create a starter spec:

```bash
app-auto-action scene-template experiment-setup --output my-setup.scene.json
```

Preview the render plan without launching Blender:

```bash
app-auto-action render-scene examples/paper-optics-setup.scene.json --dry-run
```

Render the scene:

```bash
app-auto-action render-scene examples/paper-optics-setup.scene.json --output-dir examples/renders
```

The renderer looks for Blender in this order:

1. `--blender-bin`
2. `BLENDER_BIN`
3. `blender` on `PATH`
4. `~/.local/share/appautoaction/blender/blender-4.0.2-linux-x64/blender`

Use `scripts/install_blender_portable.sh` for a no-sudo local Blender install.

## Spec Structure

```json
{
  "title": "Paper-ready optical experiment setup",
  "slug": "paper-optics-setup",
  "render": {
    "width": 1800,
    "height": 1200,
    "camera": {
      "type": "ortho",
      "location": [270, -290, 210],
      "target": [0, 0, 48],
      "ortho_scale": 440
    }
  },
  "materials": {
    "beam": {"color": [1.0, 0.32, 0.05, 0.38], "alpha": 0.38}
  },
  "elements": []
}
```

`title` and `elements` are required. `slug` controls output filenames. Coordinates are in a millimeter-like scene scale.

## Supported Elements

| Type | Purpose |
|---|---|
| `baseplate` | Breadboard-style base, optionally with a hole grid. |
| `rail_pair` | Two parallel optical rails. |
| `beam` | Cylindrical optical path or signal path. |
| `led_source` | LED source block with emitter. |
| `optic` | Generic mounted optic, such as diffuser, polarizer, sample, filter, or analyzer. |
| `lcd_light_valve` | Mounted programmable retarder / LCD light valve component. |
| `event_camera` | Camera body with lens. |
| `electronics_board` | Controller, DAC, driver, regulator, or acquisition board. |
| `wire` | 3D polyline cable or signal route. |
| `label` | Text label. |
| `box` | Generic rectangular component. |
| `cylinder` | Generic cylindrical component. |

## Recommended Workflow

1. Generate a starter scene with `scene-template`.
2. Ask an agent to edit the JSON spec, not the generated `.blend`.
3. Run `render-scene --dry-run` to verify output paths.
4. Render with Blender.
5. Use the PNG in a README, paper methods figure, grant figure, or experiment setup note.
6. Keep the JSON spec as the source of truth for repeatable edits.

## Limitations

This is a concept-design renderer, not a mechanical CAD solver. Use it for clear communication, paper setup figures, and early experiment design. Export exact dimensions to OpenSCAD, FreeCAD, or a mechanical CAD workflow before fabrication.
