from __future__ import annotations

import json
import math
import os
from pathlib import Path
import sys

import bpy


def main() -> int:
    envelope = read_envelope()
    output_dir = Path(os.environ.get("LABCANVAS_OUTPUT_DIR") or os.environ.get("APPAUTOACTION_OUTPUT_DIR", "output/blender")).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    scene_name = slug(envelope.get("instruction") or "agentic-building")
    blend_path = output_dir / f"{scene_name}.blend"
    render_path = output_dir / f"{scene_name}.png"

    create_building_scene(str(envelope.get("instruction", "")))
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    render_scene(render_path)

    result = {
        "ok": True,
        "target": envelope.get("target", "blender"),
        "instruction": envelope.get("instruction", ""),
        "artifacts": {
            "blend": str(blend_path),
            "render": str(render_path),
        },
        "summary": "Generated a procedural building scene in Blender.",
    }
    write_result(result)
    return 0


def read_envelope() -> dict:
    envelope_file = os.environ.get("LABCANVAS_ENVELOPE_FILE") or os.environ.get("APPAUTOACTION_ENVELOPE_FILE")
    if envelope_file:
        return json.loads(Path(envelope_file).read_text(encoding="utf-8"))
    raw = sys.stdin.read().strip()
    return json.loads(raw) if raw else {"target": "blender", "instruction": "Create a building"}


def write_result(result: dict) -> None:
    result_file = os.environ.get("LABCANVAS_RESULT_FILE") or os.environ.get("APPAUTOACTION_RESULT_FILE")
    payload = json.dumps(result, indent=2, sort_keys=True)
    if result_file:
        Path(result_file).write_text(payload, encoding="utf-8")
    else:
        print(payload)


def create_building_scene(instruction: str) -> None:
    clear_scene()
    materials = make_materials()

    add_cube("ground", (0, 0, -0.04), (10, 8, 0.08), materials["ground"])
    add_cube("street", (0, -3.25, 0.01), (10, 1.1, 0.04), materials["street"])
    add_cube("main_building", (0, 0, 2.5), (3.2, 2.2, 5.0), materials["facade"])
    add_cube("left_wing", (-2.25, 0.25, 1.75), (1.2, 1.7, 3.5), materials["side_facade"])
    add_cube("right_wing", (2.25, 0.25, 1.75), (1.2, 1.7, 3.5), materials["side_facade"])
    add_cube("front_steps", (0, -1.45, 0.18), (1.7, 0.45, 0.36), materials["stone"])
    add_cube("door", (0, -1.13, 0.7), (0.72, 0.08, 1.35), materials["door"])

    add_roof("main_roof", (0, 0, 5.5), 2.65, 1.2, materials["roof"])
    add_roof("left_roof", (-2.25, 0.25, 3.95), 1.35, 0.8, materials["roof"])
    add_roof("right_roof", (2.25, 0.25, 3.95), 1.35, 0.8, materials["roof"])

    for floor_z in (1.25, 2.25, 3.25, 4.25):
        for x in (-1.0, 0.0, 1.0):
            add_cube("front_window", (x, -1.13, floor_z), (0.42, 0.06, 0.48), materials["glass"])
    for x in (-2.55, -1.95, 1.95, 2.55):
        for floor_z in (1.15, 2.15, 3.0):
            add_cube("wing_window", (x, -0.62, floor_z), (0.32, 0.06, 0.42), materials["glass"])

    add_cube("sign", (0, -1.18, 5.08), (1.8, 0.06, 0.34), materials["trim"])
    add_text("APP AUTO ACTION", (0, -1.225, 5.08), 0.18, materials["text"])

    if "tower" in instruction.lower():
        add_cube("small_tower", (0, 0.75, 6.4), (0.75, 0.75, 1.5), materials["side_facade"])
        add_roof("tower_roof", (0, 0.75, 7.35), 0.75, 0.55, materials["roof"])

    add_lighting()
    add_camera()


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def make_materials() -> dict[str, bpy.types.Material]:
    return {
        "facade": material("warm_brick", (0.78, 0.38, 0.24, 1.0)),
        "side_facade": material("muted_stone", (0.60, 0.58, 0.52, 1.0)),
        "roof": material("slate_roof", (0.12, 0.14, 0.18, 1.0)),
        "glass": material("blue_glass", (0.20, 0.55, 0.85, 0.55), metallic=0.0, roughness=0.18, alpha=0.55),
        "door": material("wood_door", (0.33, 0.16, 0.07, 1.0)),
        "ground": material("green_ground", (0.28, 0.47, 0.24, 1.0)),
        "street": material("asphalt", (0.08, 0.08, 0.08, 1.0)),
        "stone": material("step_stone", (0.55, 0.54, 0.50, 1.0)),
        "trim": material("cream_trim", (0.90, 0.82, 0.62, 1.0)),
        "text": material("dark_text", (0.05, 0.05, 0.05, 1.0)),
    }


def material(name: str, color: tuple[float, float, float, float], metallic: float = 0.0, roughness: float = 0.45, alpha: float = 1.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.blend_method = "BLEND" if alpha < 1.0 else "OPAQUE"
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Metallic"].default_value = metallic
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Alpha"].default_value = alpha
    return mat


def add_cube(name: str, location: tuple[float, float, float], dimensions: tuple[float, float, float], mat) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    return obj


def add_roof(name: str, location: tuple[float, float, float], radius: float, depth: float, mat) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=radius, radius2=0, depth=depth, rotation=(0, 0, math.radians(45)), location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    return obj


def add_text(text: str, location: tuple[float, float, float], size: float, mat) -> None:
    bpy.ops.object.text_add(location=location, rotation=(math.radians(90), 0, 0))
    obj = bpy.context.object
    obj.name = "building_sign_text"
    obj.data.body = text
    obj.data.align_x = "CENTER"
    obj.data.align_y = "CENTER"
    obj.data.size = size
    obj.data.materials.append(mat)


def add_lighting() -> None:
    bpy.ops.object.light_add(type="SUN", location=(4, -5, 8))
    bpy.context.object.name = "sun_key"
    bpy.context.object.data.energy = 3.0
    bpy.ops.object.light_add(type="AREA", location=(-3, -4, 6))
    bpy.context.object.name = "soft_fill"
    bpy.context.object.data.energy = 300
    bpy.context.object.data.size = 5


def add_camera() -> None:
    bpy.ops.object.camera_add(location=(5.6, -7.0, 4.2), rotation=(math.radians(62), 0, math.radians(39)))
    bpy.context.scene.camera = bpy.context.object


def render_scene(render_path: Path) -> None:
    scene = bpy.context.scene
    scene.render.filepath = str(render_path)
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 900
    try:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    except TypeError:
        scene.render.engine = "BLENDER_EEVEE"
    bpy.ops.render.render(write_still=True)


def slug(text: str) -> str:
    keep = []
    for char in text.lower():
        if char.isalnum():
            keep.append(char)
        elif keep and keep[-1] != "-":
            keep.append("-")
    value = "".join(keep).strip("-")
    return (value or "agentic-building")[:80]


if __name__ == "__main__":
    raise SystemExit(main())
