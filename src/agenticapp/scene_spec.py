from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any


class SceneSpecError(ValueError):
    """Raised when a scene spec is not valid enough to render."""


@dataclass(frozen=True)
class SceneRenderPlan:
    spec_path: Path
    output_dir: Path
    slug: str
    png_path: Path
    blend_path: Path
    title: str
    element_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "spec": str(self.spec_path),
            "output_dir": str(self.output_dir),
            "slug": self.slug,
            "png": str(self.png_path),
            "blend": str(self.blend_path),
            "title": self.title,
            "element_count": self.element_count,
        }


def load_scene_spec(path: str | Path) -> dict[str, Any]:
    spec_path = Path(path)
    data = json.loads(spec_path.read_text(encoding="utf-8"))
    validate_scene_spec(data)
    return data


def validate_scene_spec(spec: dict[str, Any]) -> None:
    if not isinstance(spec, dict):
        raise SceneSpecError("Scene spec must be a JSON object")
    title = spec.get("title")
    if not isinstance(title, str) or not title.strip():
        raise SceneSpecError("Scene spec requires a non-empty string 'title'")

    elements = spec.get("elements")
    if not isinstance(elements, list) or not elements:
        raise SceneSpecError("Scene spec requires a non-empty 'elements' list")
    for index, element in enumerate(elements):
        if not isinstance(element, dict):
            raise SceneSpecError(f"Element {index} must be an object")
        element_type = element.get("type")
        if not isinstance(element_type, str) or not element_type.strip():
            raise SceneSpecError(f"Element {index} requires a non-empty string 'type'")

    materials = spec.get("materials", {})
    if not isinstance(materials, dict):
        raise SceneSpecError("'materials' must be an object when provided")

    render = spec.get("render", {})
    if render and not isinstance(render, dict):
        raise SceneSpecError("'render' must be an object when provided")


def create_render_plan(spec_path: str | Path, output_dir: str | Path | None = None) -> SceneRenderPlan:
    path = Path(spec_path).resolve()
    spec = load_scene_spec(path)
    slug = slugify(str(spec.get("slug") or spec.get("title") or path.stem))
    resolved_output = Path(output_dir).resolve() if output_dir else path.parent / "renders"
    return SceneRenderPlan(
        spec_path=path,
        output_dir=resolved_output,
        slug=slug,
        png_path=resolved_output / f"{slug}.png",
        blend_path=resolved_output / f"{slug}.blend",
        title=str(spec["title"]),
        element_count=len(spec["elements"]),
    )


def built_in_scene_template(name: str) -> dict[str, Any]:
    if name != "experiment-setup":
        raise SceneSpecError(f"Unknown template {name!r}. Available templates: experiment-setup")
    return {
        "title": "Paper-ready experiment setup",
        "slug": "paper-experiment-setup",
        "description": "A reusable optical-bench style setup for papers and experiment design notes.",
        "render": {
            "width": 1800,
            "height": 1200,
            "camera": {
                "type": "ortho",
                "location": [270, -290, 210],
                "target": [0, 0, 48],
                "ortho_scale": 440,
            },
        },
        "materials": {
            "beam": {"color": [1.0, 0.35, 0.05, 0.38], "alpha": 0.38},
            "sample": {"color": [0.8, 0.55, 0.16, 0.58], "alpha": 0.58},
        },
        "elements": [
            {"type": "baseplate", "name": "breadboard", "size": [420, 180, 8], "holes": True},
            {"type": "rail_pair", "name": "optical rails", "length": 380, "y_offsets": [-18, 18], "z": 13},
            {"type": "beam", "name": "coded optical path", "start": [-170, 0, 70], "end": [170, 0, 70], "radius": 2.4},
            {"type": "led_source", "name": "broadband LED", "x": -178, "label": "LED"},
            {"type": "optic", "name": "diffuser", "x": -126, "label": "Diffuser", "material": "diffuser"},
            {"type": "optic", "name": "input polarizer", "x": -74, "label": "P0 0 deg", "material": "glass"},
            {"type": "lcd_light_valve", "name": "programmable retarder", "x": -18, "label": "Bare LCD\nlight valve"},
            {"type": "optic", "name": "sample slide", "x": 42, "label": "Sample", "material": "sample"},
            {"type": "optic", "name": "analyzer", "x": 94, "label": "Analyzer 45 deg", "material": "glass"},
            {"type": "event_camera", "name": "event camera", "x": 178, "label": "Event\ncamera"},
            {"type": "electronics_board", "name": "controller", "location": [-92, 62, 21], "size": [76, 46, 8], "label": "Controller"},
            {"type": "electronics_board", "name": "dac", "location": [8, 62, 20], "size": [58, 34, 7], "material": "dac", "label": "DAC / waveform"},
            {"type": "electronics_board", "name": "driver", "location": [84, 62, 20], "size": [58, 34, 7], "material": "driver", "label": "Analog drive"},
            {"type": "wire", "name": "drive channel a", "points": [[8, 52, 28], [84, 52, 28], [-18, 25, 88]], "material": "red"},
            {"type": "wire", "name": "drive channel b", "points": [[8, 70, 28], [84, 70, 28], [-18, 25, 52]], "material": "blue"},
            {
                "type": "label",
                "name": "title",
                "text": "Paper-ready experiment setup",
                "location": [0, -78, 22],
                "size": 9,
                "rotation": [75, 0, 0],
                "material": "white",
            },
        ],
    }


def slugify(text: str) -> str:
    value = re.sub(r"[^A-Za-z0-9]+", "-", text.strip().lower()).strip("-")
    return value or "scene"
