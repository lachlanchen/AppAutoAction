"""Render the two-part threaded reflector assembly with Blender."""

from pathlib import Path
from mathutils import Vector
import bpy


ROOT = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts" / "v2_15mm_threads_print_fit" / "2026-06-09_v2_printable_assembly"
TUBE_STL = ARTIFACTS / "male_male_cmount_tube.stl"
HOLDER_STL = ARTIFACTS / "top_open_reflector_holder.stl"
PNG = ARTIFACTS / "threaded_reflector_assembly_render.png"
EXPLODED_PNG = ARTIFACTS / "threaded_reflector_exploded_thread_detail.png"
BLEND = ARTIFACTS / "threaded_reflector_assembly.blend"

HOLDER_X = 35.0
EXPLODED_HOLDER_X = 69.0


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def import_stl(path: Path, name: str):
    if hasattr(bpy.ops.wm, "stl_import"):
        bpy.ops.wm.stl_import(filepath=str(path))
    else:
        bpy.ops.import_mesh.stl(filepath=str(path))
    obj = bpy.context.object
    obj.name = name
    return obj


def material(name: str, color):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = 0.62
    return mat


def look_at(camera, target: Vector) -> None:
    direction = target - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def setup_scene(holder_x: float, center: Vector, ortho_scale: float):
    clear_scene()
    tube = import_stl(TUBE_STL, "50 mm male-male C-mount tube")
    holder = import_stl(HOLDER_STL, "top-open reflector holder")
    holder.location.x = holder_x

    tube.data.materials.append(material("printed blue tube", (0.12, 0.62, 1.0, 1)))
    holder.data.materials.append(material("printed green holder", (0.24, 0.92, 0.52, 1)))

    bpy.ops.mesh.primitive_plane_add(size=120, location=(38, 0, -0.04))
    floor = bpy.context.object
    floor.name = "matte floor"
    floor.data.materials.append(material("floor", (0.88, 0.90, 0.92, 1)))

    bpy.ops.object.light_add(type="AREA", location=(28, -42, 78))
    key = bpy.context.object
    key.name = "large softbox"
    key.data.energy = 1550
    key.data.size = 10

    bpy.ops.object.light_add(type="AREA", location=(-25, 36, 52))
    fill = bpy.context.object
    fill.name = "fill"
    fill.data.energy = 650
    fill.data.size = 11

    bpy.ops.object.camera_add(location=(center.x + 64, -92, 86))
    camera = bpy.context.object
    look_at(camera, center)
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = ortho_scale
    bpy.context.scene.camera = camera

    bpy.context.scene.render.engine = "BLENDER_EEVEE"
    bpy.context.scene.eevee.taa_render_samples = 64
    if hasattr(bpy.context.scene.eevee, "use_gtao"):
        bpy.context.scene.eevee.use_gtao = True
    bpy.context.scene.view_settings.view_transform = "Standard"
    bpy.context.scene.view_settings.exposure = 0.65
    bpy.context.scene.render.resolution_x = 1800
    bpy.context.scene.render.resolution_y = 1200
    bpy.context.scene.world.color = (0.98, 0.99, 1.0)


def render_to(path: Path) -> None:
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    print(f"Rendered {path}")


def main() -> None:
    setup_scene(HOLDER_X, Vector((42, 0, 14.2)), 100)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    render_to(PNG)

    setup_scene(EXPLODED_HOLDER_X, Vector((61, 0, 14.2)), 128)
    render_to(EXPLODED_PNG)


if __name__ == "__main__":
    main()
