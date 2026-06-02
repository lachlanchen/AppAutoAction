from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .scene_spec import slugify, validate_scene_spec


@dataclass(frozen=True)
class OpenScadExportResult:
    path: Path
    title: str
    element_count: int

    def to_dict(self) -> dict[str, Any]:
        return {"path": str(self.path), "title": self.title, "element_count": self.element_count}


def export_scene_to_openscad(spec: dict[str, Any], output_dir: str | Path) -> OpenScadExportResult:
    validate_scene_spec(spec)
    slug = slugify(str(spec.get("slug") or spec.get("title") or "scene"))
    path = Path(output_dir) / f"{slug}.scad"
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"// AppAutoAction OpenSCAD export: {str(spec.get('title') or slug)}",
        "// This is a simplified CAD proxy for planning mechanical layout.",
        "$fn = 48;",
        "",
        "module rounded_box(size=[10,10,10], radius=2) {",
        "  minkowski() {",
        "    cube([max(size[0]-2*radius, 0.1), max(size[1]-2*radius, 0.1), max(size[2]-2*radius, 0.1)], center=true);",
        "    sphere(r=radius);",
        "  }",
        "}",
        "",
        "union() {",
    ]
    for element in spec.get("elements", []):
        lines.extend(scad_for_element(element))
    lines.append("}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return OpenScadExportResult(path=path, title=str(spec["title"]), element_count=len(spec["elements"]))


def scad_for_element(element: dict[str, Any]) -> list[str]:
    kind = str(element.get("type") or "")
    name = str(element.get("name") or kind or "element").replace("\n", " ")
    if kind == "baseplate":
        size = number_list(element.get("size"), [420, 180, 8], 3)
        return [
            f"  // {name}",
            f"  color([0.18,0.21,0.25]) translate([0,0,{size[2] / 2:g}]) cube([{size[0]:g},{size[1]:g},{size[2]:g}], center=true);",
        ]
    if kind == "rail_pair":
        length = float_value(element.get("length"), 360)
        z = float_value(element.get("z"), 13)
        y_offsets = number_list(element.get("y_offsets"), [-18, 18], 2)
        lines = [f"  // {name}"]
        for y in y_offsets:
            lines.append(f"  color([0.72,0.76,0.8]) translate([0,{y:g},{z:g}]) rotate([0,90,0]) cylinder(h={length:g}, r=3.2, center=true);")
        return lines
    if kind in {"optic", "lcd_light_valve"}:
        x = float_value(element.get("x"), 0)
        label = str(element.get("label") or name).replace("\n", " ")
        return [
            f"  // {label}",
            f"  color([0.35,0.68,0.92,0.45]) translate([{x:g},0,70]) cube([8,46,52], center=true);",
            f"  color([0.1,0.1,0.1]) translate([{x:g},0,39]) cylinder(h=24, r=7, center=true);",
        ]
    if kind == "led_source":
        x = float_value(element.get("x"), -160)
        return [
            f"  // {name}",
            f"  color([1,0.55,0.1]) translate([{x:g},0,70]) rotate([0,90,0]) cylinder(h=34, r=14, center=true);",
        ]
    if kind == "event_camera":
        x = float_value(element.get("x"), 160)
        return [
            f"  // {name}",
            f"  color([0.08,0.1,0.13]) translate([{x:g},0,70]) cube([34,44,34], center=true);",
            f"  color([0.02,0.03,0.04]) translate([{x - 20:g},0,70]) rotate([0,90,0]) cylinder(h=16, r=12, center=true);",
        ]
    if kind == "electronics_board":
        location = number_list(element.get("location"), [0, 60, 20], 3)
        size = number_list(element.get("size"), [60, 36, 8], 3)
        return [
            f"  // {name}",
            f"  color([0.05,0.45,0.34]) translate([{location[0]:g},{location[1]:g},{location[2]:g}]) cube([{size[0]:g},{size[1]:g},{size[2]:g}], center=true);",
        ]
    if kind == "beam":
        start = number_list(element.get("start"), [-160, 0, 70], 3)
        end = number_list(element.get("end"), [160, 0, 70], 3)
        length = max(abs(end[0] - start[0]), 1)
        x = (start[0] + end[0]) / 2
        radius = float_value(element.get("radius"), 2.4)
        return [
            f"  // {name}",
            f"  color([1,0.3,0.05,0.35]) translate([{x:g},0,{start[2]:g}]) rotate([0,90,0]) cylinder(h={length:g}, r={radius:g}, center=true);",
        ]
    return [f"  // skipped unsupported element: {name} ({kind})"]


def number_list(value: Any, default: list[float], length: int) -> list[float]:
    if not isinstance(value, list):
        return default[:length]
    result = []
    for index in range(length):
        result.append(float_value(value[index] if index < len(value) else default[index], default[index]))
    return result


def float_value(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)
