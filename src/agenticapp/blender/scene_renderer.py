from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

import bpy
import mathutils


DEFAULT_MATERIALS = {
    "base": {"color": [0.12, 0.14, 0.16, 1.0], "metallic": 0.25, "roughness": 0.55},
    "rail": {"color": [0.55, 0.58, 0.61, 1.0], "metallic": 0.55, "roughness": 0.25},
    "post": {"color": [0.70, 0.72, 0.74, 1.0], "metallic": 0.7, "roughness": 0.2},
    "black": {"color": [0.02, 0.025, 0.03, 1.0], "metallic": 0.25, "roughness": 0.4},
    "glass": {"color": [0.18, 0.55, 0.90, 0.45], "roughness": 0.08, "alpha": 0.45},
    "diffuser": {"color": [0.95, 0.90, 0.72, 0.7], "roughness": 0.25, "alpha": 0.7},
    "lcd": {"color": [0.12, 0.24, 0.32, 0.62], "roughness": 0.12, "alpha": 0.62},
    "sample": {"color": [0.86, 0.55, 0.18, 0.58], "roughness": 0.18, "alpha": 0.58},
    "beam": {"color": [1.0, 0.32, 0.05, 0.36], "roughness": 0.08, "alpha": 0.36},
    "led": {"color": [1.0, 0.78, 0.18, 1.0], "roughness": 0.18},
    "controller": {"color": [0.02, 0.25, 0.45, 1.0], "roughness": 0.4},
    "dac": {"color": [0.02, 0.42, 0.32, 1.0], "roughness": 0.4},
    "driver": {"color": [0.40, 0.08, 0.50, 1.0], "roughness": 0.4},
    "wire": {"color": [0.03, 0.03, 0.035, 1.0], "roughness": 0.5},
    "red": {"color": [0.85, 0.08, 0.04, 1.0], "roughness": 0.35},
    "blue": {"color": [0.05, 0.20, 0.85, 1.0], "roughness": 0.35},
    "text": {"color": [0.01, 0.01, 0.01, 1.0], "roughness": 0.5},
    "white": {"color": [0.92, 0.92, 0.88, 1.0], "roughness": 0.45},
    "floor": {"color": [0.91, 0.94, 0.97, 1.0], "roughness": 0.62},
}


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    render_spec(spec, output_dir)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    raw = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else argv
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True)
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args(raw)


def render_spec(spec: dict, output_dir: Path) -> None:
    clear_scene()
    mats = make_materials(spec.get("materials") or {})
    for element in spec.get("elements", []):
        add_element(element, mats)
    render = spec.get("render", {})
    if render.get("floor", True):
        add_studio_floor(mats)
    add_default_lighting()
    configure_camera(spec.get("render", {}).get("camera") or {})
    save_outputs(spec, output_dir)


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def make_materials(overrides: dict) -> dict[str, bpy.types.Material]:
    merged = {**DEFAULT_MATERIALS}
    for name, value in overrides.items():
        if isinstance(value, list):
            merged[name] = {"color": value}
        elif isinstance(value, dict):
            merged[name] = {**merged.get(name, {}), **value}
    return {name: create_material(name, config) for name, config in merged.items()}


def create_material(name: str, config: dict) -> bpy.types.Material:
    color = config.get("color", [0.8, 0.8, 0.8, 1.0])
    alpha = float(config.get("alpha", color[3] if len(color) > 3 else 1.0))
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    material.blend_method = "BLEND" if alpha < 1.0 else "OPAQUE"
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = tuple(color)
        bsdf.inputs["Metallic"].default_value = float(config.get("metallic", 0.0))
        bsdf.inputs["Roughness"].default_value = float(config.get("roughness", 0.35))
        bsdf.inputs["Alpha"].default_value = alpha
    return material


def add_element(element: dict, mats: dict[str, bpy.types.Material]) -> None:
    element_type = element["type"]
    if element_type == "baseplate":
        add_baseplate(element, mats)
    elif element_type == "rail_pair":
        add_rail_pair(element, mats)
    elif element_type == "beam":
        add_beam(element, mats)
    elif element_type == "led_source":
        add_led_source(element, mats)
    elif element_type == "optic":
        add_optic(element, mats)
    elif element_type == "lcd_light_valve":
        add_lcd_light_valve(element, mats)
    elif element_type == "event_camera":
        add_event_camera(element, mats)
    elif element_type == "electronics_board":
        add_electronics_board(element, mats)
    elif element_type == "wire":
        add_wire(element, mats)
    elif element_type == "label":
        add_label(element, mats)
    elif element_type == "box":
        add_box(element.get("name", "box"), element["location"], element["size"], material_for(element, mats))
    elif element_type == "cylinder":
        add_cylinder(
            element.get("name", "cylinder"),
            element["location"],
            float(element.get("radius", 1)),
            float(element.get("depth", 1)),
            material_for(element, mats),
            rotation=euler_rotation(element.get("rotation")),
        )
    else:
        raise ValueError(f"Unsupported scene element type: {element_type}")


def add_baseplate(element: dict, mats) -> None:
    size = element.get("size", [420, 180, 8])
    add_box(element.get("name", "baseplate"), [0, 0, size[2] / 2], size, material_for(element, mats, "base"))
    if element.get("holes", False):
        spacing = int(element.get("hole_spacing", 20))
        for x in range(-int(size[0] / 2) + 20, int(size[0] / 2), spacing):
            for y in range(-int(size[1] / 2) + 20, int(size[1] / 2), spacing):
                add_cylinder(f"hole_{x}_{y}", [x, y, size[2] + 0.35], 1.5, 0.5, mats["rail"])


def add_rail_pair(element: dict, mats) -> None:
    length = float(element.get("length", 380))
    z = float(element.get("z", 13))
    rail_size = element.get("rail_size", [length, 7, 7])
    for y in element.get("y_offsets", [-18, 18]):
        add_box(f"{element.get('name', 'rail')}_{y}", [0, y, z], [length, rail_size[1], rail_size[2]], material_for(element, mats, "rail"))


def add_beam(element: dict, mats) -> None:
    start = vector(element.get("start", [-170, 0, 70]))
    end = vector(element.get("end", [170, 0, 70]))
    midpoint = (start + end) / 2
    length = (end - start).length
    obj = add_cylinder(element.get("name", "beam"), midpoint, float(element.get("radius", 2.2)), length, material_for(element, mats, "beam"))
    direction = end - start
    obj.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()


def add_led_source(element: dict, mats) -> None:
    x = float(element.get("x", 0))
    add_post(x, mats)
    add_box(element.get("name", "led_mount"), [x, 0, 70], [24, 42, 38], mats["black"])
    add_cylinder("led_emitter", [x + 14, 0, 70], 12, 4, mats["led"], rotation=euler_rotation([0, 90, 0]))
    add_auto_label(element.get("label", "LED"), [x, -34, 96], mats)


def add_optic(element: dict, mats) -> None:
    x = float(element.get("x", 0))
    add_post(x, mats)
    add_box(f"{element.get('name', 'optic')}_frame", [x, 0, 70], element.get("frame_size", [9, 48, 50]), mats["black"])
    add_cylinder(
        f"{element.get('name', 'optic')}_optic",
        [x, 0, 70],
        float(element.get("radius", 18)),
        float(element.get("depth", 4)),
        material_for(element, mats, "glass"),
        rotation=euler_rotation([0, 90, 0]),
    )
    add_auto_label(element.get("label", element.get("name", "optic")), [x, -38, 96], mats)


def add_lcd_light_valve(element: dict, mats) -> None:
    x = float(element.get("x", 0))
    add_post(x, mats)
    add_box("lcd_frame", [x, 0, 70], [10, 56, 56], mats["black"])
    add_box("lcd_cell", [x, 0, 70], [4, 40, 34], mats["lcd"])
    add_box("lcd_contact_a", [x, 24, 88], [8, 12, 4], mats["red"])
    add_box("lcd_contact_b", [x, 24, 52], [8, 12, 4], mats["blue"])
    add_auto_label(element.get("label", "LCD\nlight valve"), [x, -44, 101], mats)


def add_event_camera(element: dict, mats) -> None:
    x = float(element.get("x", 0))
    add_post(x, mats)
    add_box("event_camera_body", [x, 0, 70], [38, 50, 36], mats["black"])
    add_cylinder("camera_lens", [x - 24, 0, 70], 16, 22, mats["black"], rotation=euler_rotation([0, 90, 0]))
    add_cylinder("camera_glass", [x - 36, 0, 70], 10, 2, mats["glass"], rotation=euler_rotation([0, 90, 0]))
    add_box("camera_sensor_back", [x + 22, 0, 70], [4, 42, 28], mats["controller"])
    add_auto_label(element.get("label", "Camera"), [x, -42, 98], mats)


def add_electronics_board(element: dict, mats) -> None:
    location = element.get("location", [0, 62, 20])
    size = element.get("size", [50, 30, 7])
    add_box(element.get("name", "electronics_board"), location, size, material_for(element, mats, "controller"))
    add_label(
        {
            "text": element.get("label", element.get("name", "board")),
            "location": [location[0], location[1], location[2] + size[2] + 4],
            "size": element.get("label_size", 4.6),
            "material": "white",
        },
        mats,
    )


def add_wire(element: dict, mats) -> None:
    add_curve(element.get("name", "wire"), element.get("points", []), material_for(element, mats, "wire"), float(element.get("bevel", 1.2)))


def add_auto_label(text: str, location: list[float], mats) -> None:
    add_label({"text": text, "location": location, "size": 5.8, "rotation": [72, 0, 0], "material": "white"}, mats)


def add_label(element: dict, mats) -> None:
    text = str(element.get("text", element.get("name", "label")))
    bpy.ops.object.text_add(location=element.get("location", [0, 0, 0]), rotation=euler_rotation(element.get("rotation")))
    obj = bpy.context.object
    obj.name = "label_" + text.replace("\n", "_").replace(" ", "_")[:32]
    obj.data.body = text
    obj.data.align_x = "CENTER"
    obj.data.align_y = "CENTER"
    obj.data.size = float(element.get("size", 6))
    obj.data.extrude = float(element.get("extrude", 0.08))
    obj.data.materials.append(material_for(element, mats, "text"))


def add_post(x: float, mats) -> None:
    add_cylinder(f"post_{x}", [x, 0, 37], 4.5, 58, mats["post"])


def add_box(name: str, location, size, material) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    add_bevel(obj, size)
    return obj


def add_cylinder(name: str, location, radius: float, depth: float, material, rotation=None) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=radius, depth=depth, location=location, rotation=rotation or (0, 0, 0))
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    return obj


def add_bevel(obj: bpy.types.Object, size) -> None:
    try:
        amount = max(0.35, min(float(min(size)) * 0.08, 2.4))
    except (TypeError, ValueError):
        amount = 0.7
    bevel = obj.modifiers.new("soft_edges", "BEVEL")
    bevel.width = amount
    bevel.segments = 2
    bevel.affect = "EDGES"
    normals = obj.modifiers.new("weighted_normals", "WEIGHTED_NORMAL")
    normals.keep_sharp = True


def add_curve(name: str, points, material, bevel: float) -> bpy.types.Object:
    if len(points) < 2:
        raise ValueError(f"Wire {name!r} needs at least two points")
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 16
    curve.bevel_depth = bevel
    curve.bevel_resolution = 4
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for point, coords in zip(spline.points, points):
        point.co = (coords[0], coords[1], coords[2], 1)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    return obj


def add_default_lighting() -> None:
    bpy.ops.object.light_add(type="AREA", location=(-70, -210, 260))
    key = bpy.context.object
    key.name = "large_softbox"
    key.data.energy = 1650
    key.data.size = 420
    bpy.ops.object.light_add(type="AREA", location=(230, 120, 160))
    fill = bpy.context.object
    fill.name = "cool_fill"
    fill.data.energy = 260
    fill.data.size = 260
    bpy.ops.object.light_add(type="SUN", location=(80, -120, 220), rotation=(math.radians(45), 0, math.radians(25)))
    sun = bpy.context.object
    sun.name = "sun_rim"
    sun.data.energy = 1.15


def add_studio_floor(mats) -> None:
    floor = add_box("studio_floor", [0, 0, -1.2], [620, 300, 1.0], mats["floor"])
    floor.modifiers.clear()


def configure_camera(config: dict) -> None:
    location = config.get("location", [270, -290, 210])
    target = config.get("target", [0, 0, 48])
    bpy.ops.object.camera_add(location=location)
    camera = bpy.context.object
    bpy.context.scene.camera = camera
    look_at(camera, target)
    if config.get("type", "ortho") == "ortho":
        camera.data.type = "ORTHO"
        camera.data.ortho_scale = float(config.get("ortho_scale", 440))
    else:
        camera.data.lens = float(config.get("lens", 38))


def save_outputs(spec: dict, output_dir: Path) -> None:
    render = spec.get("render", {})
    slug = slugify(spec.get("slug") or spec.get("title", "scene"))
    scene = bpy.context.scene
    scene.render.resolution_x = int(render.get("width", 1800))
    scene.render.resolution_y = int(render.get("height", 1200))
    scene.render.filepath = str(output_dir / f"{slug}.png")
    configure_world(scene, render.get("world_color", [0.88, 0.91, 0.94]))
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "Medium High Contrast"
    scene.view_settings.exposure = float(render.get("exposure", 0.05))
    scene.view_settings.gamma = float(render.get("gamma", 1.0))
    try:
        scene.render.engine = render.get("engine", "BLENDER_EEVEE_NEXT")
    except TypeError:
        scene.render.engine = "BLENDER_EEVEE"
    configure_render_quality(scene, render)
    bpy.ops.wm.save_as_mainfile(filepath=str(output_dir / f"{slug}.blend"))
    bpy.ops.render.render(write_still=True)


def configure_world(scene, color) -> None:
    if scene.world is None:
        scene.world = bpy.data.worlds.new("World")
    rgba = tuple(color if len(color) == 4 else [*color, 1.0])
    scene.world.color = rgba[:3]
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get("Background")
    if background:
        background.inputs["Color"].default_value = rgba
        background.inputs["Strength"].default_value = 0.82


def configure_render_quality(scene, render: dict) -> None:
    scene.render.film_transparent = False
    scene.render.use_persistent_data = True
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.compression = 15
    if not hasattr(scene, "eevee"):
        return
    eevee = scene.eevee
    for name, value in (
        ("taa_render_samples", int(render.get("samples", 96))),
        ("use_gtao", True),
        ("gtao_distance", 4),
        ("gtao_factor", 1.25),
        ("use_soft_shadows", True),
    ):
        if hasattr(eevee, name):
            setattr(eevee, name, value)


def material_for(element: dict, mats: dict[str, bpy.types.Material], default: str = "black") -> bpy.types.Material:
    return mats.get(str(element.get("material", default)), mats[default])


def euler_rotation(values) -> tuple[float, float, float]:
    if not values:
        return (0, 0, 0)
    return tuple(math.radians(float(value)) for value in values)


def vector(values) -> mathutils.Vector:
    return mathutils.Vector((float(values[0]), float(values[1]), float(values[2])))


def look_at(obj: bpy.types.Object, target) -> None:
    direction = vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def slugify(text: str) -> str:
    keep = []
    for char in str(text).lower():
        if char.isalnum():
            keep.append(char)
        elif keep and keep[-1] != "-":
            keep.append("-")
    return ("".join(keep).strip("-") or "scene")[:96]


if __name__ == "__main__":
    raise SystemExit(main())
