"""Generate STEP envelope/decomposition files and support drawings."""

from __future__ import annotations

from pathlib import Path
import subprocess

import cadquery as cq
import ezdxf


ROOT = Path(__file__).resolve().parent
DESIGN_VERSION = "v2_15mm_threads_print_fit"
ARTIFACTS_ROOT = ROOT / "artifacts"
ARTIFACTS = ARTIFACTS_ROOT / DESIGN_VERSION

TUBE_TOTAL = 50.0
THREAD_LEN = 15.0
BODY_LEN = TUBE_TOTAL - 2.0 * THREAD_LEN
MALE_ROOT_D = 24.4
THREAD_HEIGHT = 0.4
THREAD_OVERLAP = 0.08
MALE_CREST_D = MALE_ROOT_D + 2.0 * THREAD_HEIGHT
BORE_D = 20.0

WALL = 4.0
REFLECTOR_NOMINAL = 20.0
REFLECTOR_CLEARANCE = 0.4
INNER = REFLECTOR_NOMINAL + REFLECTOR_CLEARANCE
AXIS_Z = WALL + INNER / 2.0
BODY_D = 2.0 * AXIS_Z
HOLDER_SOCKET = 24.0
FEMALE_THREAD_LEN = 20.0
HOLDER_BOX_X = INNER + WALL
HOLDER_Y = INNER + 2.0 * WALL
HOLDER_Z = INNER + WALL
SOCKET_OD = 34.0
FEMALE_ROOT_D = 24.8
FEMALE_CREST_D = FEMALE_ROOT_D + 2.0 * THREAD_HEIGHT
ASSEMBLY_HOLDER_X = TUBE_TOTAL - THREAD_LEN
THREAD_PITCH = 0.8
THREAD_TOOTH_W = 0.8


def x_cylinder(d: float, length: float, x0: float) -> cq.Workplane:
    return cq.Workplane("YZ").workplane(offset=x0).center(0, AXIS_Z).circle(d / 2).extrude(length)


def box(x0: float, y0: float, z0: float, dx: float, dy: float, dz: float) -> cq.Workplane:
    return cq.Workplane("XY").box(dx, dy, dz, centered=(False, False, False)).translate((x0, y0, z0))


def centered_y_box(x0: float, z0: float, dx: float, dy: float, dz: float) -> cq.Workplane:
    return cq.Workplane("XY").box(dx, dy, dz, centered=(False, True, False)).translate((x0, 0, z0))


def x_clip_box(x0: float, length: float, y_span: float, z0: float, height: float) -> cq.Workplane:
    return cq.Workplane("XY").box(length, y_span, height, centered=(False, True, False)).translate((x0, 0, z0))


def external_thread_brep(x0: float, length: float, root_d: float, lefthand: bool = False) -> cq.Workplane:
    root_r = root_d / 2 - THREAD_OVERLAP
    crest_d = root_d + 2.0 * THREAD_HEIGHT
    path = cq.Wire.makeHelix(
        THREAD_PITCH,
        length,
        root_r,
        center=(x0, 0, AXIS_Z),
        dir=(1, 0, 0),
        lefthand=lefthand,
    )
    profile = (
        cq.Workplane("XY")
        .workplane(offset=AXIS_Z)
        .center(x0, root_r)
        .polyline([(0, 0), (THREAD_TOOTH_W / 2, THREAD_HEIGHT + THREAD_OVERLAP), (THREAD_TOOTH_W, 0)])
        .close()
    )
    thread = profile.sweep(path, isFrenet=True, combine=False)
    return thread.intersect(x_clip_box(x0, length, crest_d + 3, AXIS_Z - crest_d / 2 - 2, crest_d + 4))


def tube_base_no_threads() -> cq.Workplane:
    right_x = THREAD_LEN + BODY_LEN
    tube = (
        x_cylinder(MALE_ROOT_D, THREAD_LEN + 0.2, 0)
        .union(x_cylinder(BODY_D, BODY_LEN + 0.4, THREAD_LEN - 0.2))
        .union(x_cylinder(MALE_ROOT_D, THREAD_LEN + 0.2, right_x - 0.2))
    )
    return tube.cut(x_cylinder(BORE_D, TUBE_TOTAL + 2, -1))


def left_male_thread() -> cq.Workplane:
    return external_thread_brep(0, THREAD_LEN, MALE_ROOT_D, lefthand=False)


def right_male_thread() -> cq.Workplane:
    return external_thread_brep(THREAD_LEN + BODY_LEN, THREAD_LEN, MALE_ROOT_D, lefthand=True)


def tube_envelope() -> cq.Workplane:
    left = x_cylinder(MALE_CREST_D, THREAD_LEN, 0)
    body = x_cylinder(BODY_D, BODY_LEN, THREAD_LEN)
    right = x_cylinder(MALE_CREST_D, THREAD_LEN, THREAD_LEN + BODY_LEN)
    tube = left.union(body).union(right)
    return tube.cut(x_cylinder(BORE_D, TUBE_TOTAL + 2, -1))


def holder_cube_shell(x0: float = 0) -> cq.Workplane:
    box_left = x0 + HOLDER_SOCKET
    bottom = centered_y_box(box_left, 0, HOLDER_BOX_X, HOLDER_Y, WALL)
    side_a = box(box_left, -HOLDER_Y / 2, WALL, HOLDER_BOX_X, WALL, INNER)
    side_b = box(box_left, HOLDER_Y / 2 - WALL, WALL, HOLDER_BOX_X, WALL, INNER)
    right = box(box_left + INNER, -HOLDER_Y / 2, WALL, WALL, HOLDER_Y, INNER)
    return bottom.union(side_a).union(side_b).union(right)


def holder_socket_outer(x0: float = 0) -> cq.Workplane:
    socket = x_cylinder(SOCKET_OD, HOLDER_SOCKET, x0)
    clip = box(x0 - 0.1, -SOCKET_OD / 2 - 0.5, 0, HOLDER_SOCKET + 0.2, SOCKET_OD + 1, SOCKET_OD)
    return socket.intersect(clip)


def holder_reinforcement(x0: float = 0) -> cq.Workplane:
    return centered_y_box(x0, 0, HOLDER_SOCKET + WALL, HOLDER_Y, WALL)


def holder_base_solid(x0: float = 0) -> cq.Workplane:
    return holder_cube_shell(x0).union(holder_socket_outer(x0)).union(holder_reinforcement(x0))


def holder_bore_cutter(x0: float = 0) -> cq.Workplane:
    return x_cylinder(FEMALE_ROOT_D, HOLDER_SOCKET + 1, x0 - 0.5)


def holder_female_thread_cutter(x0: float = 0) -> cq.Workplane:
    return external_thread_brep(x0 - 0.5, FEMALE_THREAD_LEN, FEMALE_ROOT_D, lefthand=True)


def holder_full_thread_cutter(x0: float = 0) -> cq.Workplane:
    return holder_bore_cutter(x0).union(holder_female_thread_cutter(x0))


def holder_smooth_bore_base(x0: float = 0) -> cq.Workplane:
    return holder_base_solid(x0).cut(holder_bore_cutter(x0))


def holder_envelope(x0: float = 0) -> cq.Workplane:
    socket_left = x0
    box_left = x0 + HOLDER_SOCKET
    bottom = centered_y_box(box_left, 0, HOLDER_BOX_X, HOLDER_Y, WALL)
    side_a = box(box_left, -HOLDER_Y / 2, WALL, HOLDER_BOX_X, WALL, INNER)
    side_b = box(box_left, HOLDER_Y / 2 - WALL, WALL, HOLDER_BOX_X, WALL, INNER)
    right = box(box_left + INNER, -HOLDER_Y / 2, WALL, WALL, HOLDER_Y, INNER)

    socket = x_cylinder(SOCKET_OD, HOLDER_SOCKET, socket_left)
    clip = box(socket_left - 0.1, -SOCKET_OD / 2 - 0.5, 0, HOLDER_SOCKET + 0.2, SOCKET_OD + 1, SOCKET_OD)
    socket = socket.intersect(clip)
    reinforce = centered_y_box(socket_left, 0, HOLDER_SOCKET + WALL, HOLDER_Y, WALL)

    holder = bottom.union(side_a).union(side_b).union(right).union(socket).union(reinforce)
    return holder.cut(x_cylinder(FEMALE_ROOT_D, HOLDER_SOCKET + 1, socket_left - 0.5))


def threaded_tube() -> cq.Workplane:
    tube = (
        tube_base_no_threads()
        .union(left_male_thread())
        .union(right_male_thread())
    )
    return tube


def threaded_holder(x0: float = 0) -> cq.Workplane:
    socket_left = x0
    box_left = x0 + HOLDER_SOCKET
    bottom = centered_y_box(box_left, 0, HOLDER_BOX_X, HOLDER_Y, WALL)
    side_a = box(box_left, -HOLDER_Y / 2, WALL, HOLDER_BOX_X, WALL, INNER)
    side_b = box(box_left, HOLDER_Y / 2 - WALL, WALL, HOLDER_BOX_X, WALL, INNER)
    right = box(box_left + INNER, -HOLDER_Y / 2, WALL, WALL, HOLDER_Y, INNER)

    socket = x_cylinder(SOCKET_OD, HOLDER_SOCKET, socket_left)
    clip = box(socket_left - 0.1, -SOCKET_OD / 2 - 0.5, 0, HOLDER_SOCKET + 0.2, SOCKET_OD + 1, SOCKET_OD)
    socket = socket.intersect(clip)
    reinforce = centered_y_box(socket_left, 0, HOLDER_SOCKET + WALL, HOLDER_Y, WALL)

    holder = bottom.union(side_a).union(side_b).union(right).union(socket).union(reinforce)
    return holder.cut(holder_full_thread_cutter(socket_left))


def export_individual(path: Path, shape: cq.Workplane) -> None:
    cq.exporters.export(shape, str(path.with_suffix(".step")))
    cq.exporters.export(shape, str(path.with_suffix(".stl")))


def export_openscad_part(part_name: str, output_name: str) -> None:
    source = ROOT / "threaded_reflector_assembly.scad"
    output = ARTIFACTS / output_name
    subprocess.run(
        ["openscad", "-D", f'part="{part_name}"', "-o", str(output), str(source)],
        check=True,
    )


def export_decomposed_steps() -> None:
    tube_base = tube_base_no_threads()
    tube_left_thread = left_male_thread()
    tube_right_thread = right_male_thread()

    export_individual(ARTIFACTS / "tube_base_no_threads", tube_base)
    export_individual(ARTIFACTS / "tube_left_male_thread", tube_left_thread)
    export_individual(ARTIFACTS / "tube_right_male_thread", tube_right_thread)
    # CadQuery STEP is useful for named CAD solids; OpenSCAD produces closed STL caps
    # for the standalone twisted thread bodies.
    export_openscad_part("tube_left_thread", "tube_left_male_thread.stl")
    export_openscad_part("tube_right_thread", "tube_right_male_thread.stl")

    tube_recipe = cq.Assembly(name="male_male_cmount_tube_decomposed")
    tube_recipe.add(tube_base, name="tube_base_no_threads")
    tube_recipe.add(tube_left_thread, name="left_male_thread_add")
    tube_recipe.add(tube_right_thread, name="right_male_thread_add")
    tube_recipe.save(str(ARTIFACTS / "male_male_cmount_tube_decomposed.step"))

    tube_exploded = cq.Assembly(name="male_male_cmount_tube_decomposed_exploded")
    tube_exploded.add(tube_base, name="tube_base_no_threads")
    tube_exploded.add(tube_left_thread.translate((0, -34, 0)), name="left_male_thread_add_offset")
    tube_exploded.add(tube_right_thread.translate((0, 34, 0)), name="right_male_thread_add_offset")
    tube_exploded.save(str(ARTIFACTS / "male_male_cmount_tube_decomposed_exploded.step"))

    cube_shell = holder_cube_shell(0)
    socket_outer = holder_socket_outer(0)
    reinforcement = holder_reinforcement(0)
    smooth_bore = holder_smooth_bore_base(0)
    bore_cutter = holder_bore_cutter(0)
    thread_cutter = holder_female_thread_cutter(0)
    full_cutter = holder_full_thread_cutter(0)

    export_individual(ARTIFACTS / "holder_cube_shell", cube_shell)
    export_individual(ARTIFACTS / "holder_socket_outer", socket_outer)
    export_individual(ARTIFACTS / "holder_bottom_reinforcement", reinforcement)
    export_individual(ARTIFACTS / "holder_smooth_bore_base", smooth_bore)
    export_individual(ARTIFACTS / "holder_female_bore_cutter", bore_cutter)
    export_individual(ARTIFACTS / "holder_female_thread_cutter", thread_cutter)
    export_individual(ARTIFACTS / "holder_full_thread_cutter", full_cutter)

    holder_recipe = cq.Assembly(name="top_open_reflector_holder_boolean_recipe")
    holder_recipe.add(holder_base_solid(0), name="holder_base_solid_before_subtraction")
    holder_recipe.add(smooth_bore, name="holder_smooth_bore_base")
    holder_recipe.add(thread_cutter, name="female_thread_cutter_subtract")
    holder_recipe.add(threaded_holder(0), name="threaded_holder_result")
    holder_recipe.save(str(ARTIFACTS / "top_open_reflector_holder_boolean_recipe.step"))

    holder_decomp = cq.Assembly(name="top_open_reflector_holder_decomposed_objects")
    holder_decomp.add(cube_shell, name="reflector_cube_shell")
    holder_decomp.add(socket_outer, name="female_socket_outer_cylinder")
    holder_decomp.add(reinforcement, name="bottom_reinforcement")
    holder_decomp.add(bore_cutter, name="bore_cutter_subtract")
    holder_decomp.add(thread_cutter, name="female_thread_cutter_subtract")
    holder_decomp.save(str(ARTIFACTS / "top_open_reflector_holder_decomposed.step"))

    holder_exploded = cq.Assembly(name="top_open_reflector_holder_decomposed_exploded")
    holder_exploded.add(cube_shell, name="reflector_cube_shell")
    holder_exploded.add(socket_outer.translate((0, -42, 0)), name="female_socket_outer_cylinder_offset")
    holder_exploded.add(reinforcement.translate((0, 42, 0)), name="bottom_reinforcement_offset")
    holder_exploded.add(bore_cutter.translate((0, -76, 0)), name="bore_cutter_subtract_offset")
    holder_exploded.add(thread_cutter.translate((0, 76, 0)), name="female_thread_cutter_subtract_offset")
    holder_exploded.save(str(ARTIFACTS / "top_open_reflector_holder_decomposed_exploded.step"))

    full_recipe = cq.Assembly(name="threaded_reflector_full_decomposition")
    full_recipe.add(tube_base, name="tube_base_no_threads")
    full_recipe.add(tube_left_thread, name="tube_left_male_thread")
    full_recipe.add(tube_right_thread, name="tube_right_male_thread")
    full_recipe.add(cube_shell.translate((ASSEMBLY_HOLDER_X, 0, 0)), name="holder_cube_shell")
    full_recipe.add(socket_outer.translate((ASSEMBLY_HOLDER_X, 0, 0)), name="holder_socket_outer")
    full_recipe.add(reinforcement.translate((ASSEMBLY_HOLDER_X, 0, 0)), name="holder_bottom_reinforcement")
    full_recipe.add(bore_cutter.translate((ASSEMBLY_HOLDER_X, 0, 0)), name="holder_bore_cutter_subtract")
    full_recipe.add(thread_cutter.translate((ASSEMBLY_HOLDER_X, 0, 0)), name="holder_female_thread_cutter_subtract")
    full_recipe.save(str(ARTIFACTS / "threaded_reflector_full_decomposition.step"))


def export_steps() -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    tube = tube_envelope()
    holder = holder_envelope(0)
    cq.exporters.export(tube, str(ARTIFACTS / "male_male_cmount_tube_envelope.step"))
    cq.exporters.export(holder, str(ARTIFACTS / "top_open_reflector_holder_envelope.step"))

    assembly = cq.Assembly(name="threaded_reflector_assembly")
    assembly.add(tube, name="male_male_cmount_tube")
    assembly.add(holder_envelope(ASSEMBLY_HOLDER_X), name="top_open_reflector_holder")
    assembly.save(str(ARTIFACTS / "threaded_reflector_assembly_envelope.step"))

    threaded_tube_part = threaded_tube()
    threaded_holder_part = threaded_holder(0)
    cq.exporters.export(threaded_tube_part, str(ARTIFACTS / "male_male_cmount_tube_threaded.step"))
    cq.exporters.export(threaded_holder_part, str(ARTIFACTS / "top_open_reflector_holder_threaded.step"))
    threaded_assembly = cq.Assembly(name="threaded_reflector_assembly_with_modeled_threads")
    threaded_assembly.add(threaded_tube_part, name="male_male_cmount_tube_threaded")
    threaded_assembly.add(threaded_holder(ASSEMBLY_HOLDER_X), name="top_open_reflector_holder_female_threaded")
    threaded_assembly.save(str(ARTIFACTS / "threaded_reflector_assembly_threaded.step"))
    export_decomposed_steps()


def svg_header(width: int, height: int) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#f8fafc"/>',
        '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#111827"/></marker></defs>',
    ]


def line(x1, y1, x2, y2, stroke="#111827", width=2, dash=None) -> str:
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{width}"{dash_attr}/>'


def rect(x, y, w, h, fill, stroke="#111827", width=2, dash=None) -> str:
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"{dash_attr}/>'


def text(x, y, value, size=16, fill="#111827") -> str:
    return f'<text x="{x}" y="{y}" font-family="Arial, sans-serif" font-size="{size}" fill="{fill}">{value}</text>'


def dim(x1, y1, x2, y2, label, tx, ty) -> list[str]:
    return [
        line(x1, y1, x2, y2, width=1.6),
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#111827" stroke-width="1.6" marker-start="url(#arrow)" marker-end="url(#arrow)"/>',
        text(tx, ty, label, 14),
    ]


def write_side_svg() -> Path:
    scale = 8
    x0 = 60
    z_base = 270
    tube_y = z_base - 26 * scale
    holder_x = x0 + ASSEMBLY_HOLDER_X * scale
    holder_box_x = holder_x + HOLDER_SOCKET * scale
    out = svg_header(900, 380)
    out += [
        text(60, 36, "Side section: 50 mm male-male C-mount tube into top-open reflector holder", 18),
        line(45, z_base, 840, z_base, "#94a3b8", 1),
        rect(x0, tube_y + 0.8 * scale, THREAD_LEN * scale, MALE_CREST_D * scale, "#bfdbfe", width=2),
        rect(x0 + THREAD_LEN * scale, z_base - BODY_D * scale, BODY_LEN * scale, BODY_D * scale, "#93c5fd", width=2),
        rect(x0 + (THREAD_LEN + BODY_LEN) * scale, tube_y + 0.8 * scale, THREAD_LEN * scale, MALE_CREST_D * scale, "#bfdbfe", width=2),
        rect(holder_x, z_base - SOCKET_OD * scale, HOLDER_SOCKET * scale, SOCKET_OD * scale, "#bbf7d0", width=2),
        rect(holder_box_x, z_base - HOLDER_Z * scale, HOLDER_BOX_X * scale, HOLDER_Z * scale, "#dcfce7", width=2),
        rect(holder_box_x, z_base - (WALL + INNER) * scale, INNER * scale, INNER * scale, "#f8fafc", "#16a34a", 2, "7 6"),
        rect(holder_box_x + INNER * scale, z_base - HOLDER_Z * scale, WALL * scale, HOLDER_Z * scale, "#86efac", width=2),
        line(x0, z_base - AXIS_Z * scale, 820, z_base - AXIS_Z * scale, "#ef4444", 1.5, "8 6"),
        text(x0 + 16, tube_y + 34, "left 15 mm thread", 13, "#1e40af"),
        text(x0 + 144, tube_y + 34, "body 20 mm", 12, "#1e40af"),
        text(x0 + 296, tube_y + 34, "right 15 mm thread", 13, "#1e40af"),
        text(holder_box_x + 14, z_base - 190, "20.4 x 20.4 x 20.4 mm reflector pocket, top open", 13, "#166534"),
    ]
    out += dim(x0, z_base + 28, x0 + TUBE_TOTAL * scale, z_base + 28, "tube total 50 mm", x0 + 150, z_base + 52)
    out += dim(x0, z_base + 58, x0 + THREAD_LEN * scale, z_base + 58, "15 mm", x0 + 45, z_base + 82)
    out += dim(x0 + (THREAD_LEN + BODY_LEN) * scale, z_base + 58, x0 + TUBE_TOTAL * scale, z_base + 58, "15 mm", x0 + 315, z_base + 82)
    out.append("</svg>")
    path = ARTIFACTS / "assembly_side_section.svg"
    path.write_text("\n".join(out), encoding="utf-8")
    return path


def write_top_svg() -> Path:
    scale = 8
    x0 = 60
    y0 = 190
    holder_x = x0 + ASSEMBLY_HOLDER_X * scale
    holder_box_x = holder_x + HOLDER_SOCKET * scale
    out = svg_header(900, 360)
    out += [
        text(60, 36, "Top view: holder is top-open and left-open through the threaded socket", 18),
        rect(x0, y0 - 12.2 * scale, THREAD_LEN * scale, MALE_CREST_D * scale, "#bfdbfe"),
        rect(x0 + THREAD_LEN * scale, y0 - BODY_D / 2 * scale, BODY_LEN * scale, BODY_D * scale, "#93c5fd"),
        rect(x0 + (THREAD_LEN + BODY_LEN) * scale, y0 - 12.2 * scale, THREAD_LEN * scale, MALE_CREST_D * scale, "#bfdbfe"),
        rect(holder_x, y0 - SOCKET_OD / 2 * scale, HOLDER_SOCKET * scale, SOCKET_OD * scale, "#bbf7d0"),
        rect(holder_box_x, y0 - HOLDER_Y / 2 * scale, HOLDER_BOX_X * scale, HOLDER_Y * scale, "#dcfce7"),
        rect(holder_box_x, y0 - INNER / 2 * scale, INNER * scale, INNER * scale, "#f8fafc", "#16a34a", 2, "7 6"),
        rect(holder_box_x + INNER * scale, y0 - HOLDER_Y / 2 * scale, WALL * scale, HOLDER_Y * scale, "#86efac"),
        line(x0, y0, 830, y0, "#ef4444", 1.5, "8 6"),
        text(holder_box_x + 14, y0 - 96, "left side opens to tube", 13, "#166534"),
        text(holder_box_x + 14, y0 + 116, "top is open; no lid modeled", 13, "#166534"),
    ]
    out += dim(holder_box_x, y0 + 134, holder_box_x + INNER * scale, y0 + 134, "inner 20.4 mm", holder_box_x + 45, y0 + 158)
    out += dim(holder_x, y0 - 136, holder_x + HOLDER_SOCKET * scale, y0 - 136, "female socket 24 mm", holder_x + 35, y0 - 148)
    out.append("</svg>")
    path = ARTIFACTS / "assembly_top_view.svg"
    path.write_text("\n".join(out), encoding="utf-8")
    return path


def write_thread_profile_svg() -> Path:
    out = svg_header(900, 430)
    base_x = 210
    base_y = 260
    scale = 220
    tooth_base = THREAD_TOOTH_W * scale
    tooth_height = THREAD_HEIGHT * scale
    out += [
        text(60, 40, "Thread profile: old-reference triangular tooth used for v2", 18),
        line(140, base_y, 760, base_y, "#475569", 2),
        line(base_x, base_y, base_x + tooth_base, base_y, "#111827", 3),
        line(base_x, base_y, base_x + tooth_base / 2, base_y - tooth_height, "#111827", 3),
        line(base_x + tooth_base / 2, base_y - tooth_height, base_x + tooth_base, base_y, "#111827", 3),
        text(base_x + 32, base_y + 34, "base / pitch = 0.8 mm", 14),
        text(base_x + tooth_base / 2 + 20, base_y - tooth_height / 2, "height = 0.4 mm", 14),
        rect(120, 312, 650, 54, "#ffffff", "#cbd5e1", 1),
        text(145, 344, "Male: root OD 24.4 mm, crest OD 25.2 mm", 15, "#1e40af"),
        text(145, 366, "Female cutter: root/bore 24.8 mm, cutter crest 25.6 mm", 15, "#166534"),
    ]
    out += dim(base_x, base_y + 18, base_x + tooth_base, base_y + 18, "0.8 mm", base_x + 70, base_y + 58)
    out += [
        line(base_x + tooth_base / 2 + 14, base_y, base_x + tooth_base / 2 + 14, base_y - tooth_height, width=1.6),
        f'<line x1="{base_x + tooth_base / 2 + 14}" y1="{base_y}" x2="{base_x + tooth_base / 2 + 14}" y2="{base_y - tooth_height}" stroke="#111827" stroke-width="1.6" marker-start="url(#arrow)" marker-end="url(#arrow)"/>',
    ]
    out.append("</svg>")
    path = ARTIFACTS / "thread_profile_sketch.svg"
    path.write_text("\n".join(out), encoding="utf-8")
    return path


def write_decomposition_svg() -> Path:
    out = svg_header(980, 520)
    out += [
        text(50, 40, "Decomposition / Boolean recipe for editable CAD", 18),
        text(60, 82, "Tube: base + left male thread + right male thread", 15, "#1e40af"),
        rect(90, 135, 320, 60, "#bfdbfe"),
        rect(90, 120, 70, 90, "#dbeafe", "#1e40af", 2, "8 5"),
        rect(340, 120, 70, 90, "#dbeafe", "#1e40af", 2, "8 5"),
        text(185, 170, "tube_base_no_threads", 14, "#1e3a8a"),
        text(102, 112, "left_male_thread", 12, "#1e3a8a"),
        text(330, 112, "right_male_thread", 12, "#1e3a8a"),
        text(60, 270, "Holder: smooth-bore base - female thread cutter = threaded holder", 15, "#166534"),
        rect(90, 325, 190, 74, "#dcfce7"),
        rect(60, 300, 110, 124, "#bbf7d0"),
        rect(390, 310, 112, 104, "#fee2e2", "#991b1b", 2, "8 5"),
        text(98, 362, "holder_smooth_bore_base", 13, "#14532d"),
        text(398, 360, "female_thread_cutter", 13, "#7f1d1d"),
        text(320, 362, "-", 28, "#111827"),
        text(535, 362, "=", 28, "#111827"),
        rect(610, 325, 190, 74, "#bbf7d0"),
        rect(580, 300, 110, 124, "#86efac"),
        text(608, 362, "top_open_reflector_holder", 13, "#14532d"),
        text(58, 468, "STEP assemblies keep same-coordinate Boolean parts; exploded STEP files offset parts for inspection.", 13, "#334155"),
    ]
    out.append("</svg>")
    path = ARTIFACTS / "decomposition_recipe_sketch.svg"
    path.write_text("\n".join(out), encoding="utf-8")
    return path


def write_dxf() -> Path:
    doc = ezdxf.new("R2010")
    doc.units = ezdxf.units.MM
    msp = doc.modelspace()
    holder_x = ASSEMBLY_HOLDER_X
    holder_box_x = holder_x + HOLDER_SOCKET
    msp.add_lwpolyline([(0, -13), (TUBE_TOTAL, -13), (TUBE_TOTAL, 13), (0, 13), (0, -13)], close=True)
    msp.add_line((THREAD_LEN, -13), (THREAD_LEN, 13))
    msp.add_line((THREAD_LEN + BODY_LEN, -13), (THREAD_LEN + BODY_LEN, 13))
    msp.add_lwpolyline(
        [(holder_x, -SOCKET_OD / 2), (holder_box_x, -SOCKET_OD / 2), (holder_box_x, SOCKET_OD / 2), (holder_x, SOCKET_OD / 2), (holder_x, -SOCKET_OD / 2)],
        close=True,
    )
    msp.add_lwpolyline(
        [
            (holder_box_x, -HOLDER_Y / 2),
            (holder_box_x + HOLDER_BOX_X, -HOLDER_Y / 2),
            (holder_box_x + HOLDER_BOX_X, HOLDER_Y / 2),
            (holder_box_x, HOLDER_Y / 2),
            (holder_box_x, -HOLDER_Y / 2),
        ],
        close=True,
    )
    msp.add_lwpolyline(
        [
            (holder_box_x, -INNER / 2),
            (holder_box_x + INNER, -INNER / 2),
            (holder_box_x + INNER, INNER / 2),
            (holder_box_x, INNER / 2),
            (holder_box_x, -INNER / 2),
        ],
        close=True,
    )
    msp.add_text("Top view, units mm: tube 50 mm, threads 15 mm each, holder pocket 20.4x20.4", height=2.5).set_placement((0, 25))
    path = ARTIFACTS / "threaded_reflector_assembly_top_sketch.dxf"
    doc.saveas(path)
    return path


def svg_to_pdf_and_png(svg: Path) -> None:
    pdf = svg.with_suffix(".pdf")
    png = svg.with_suffix(".png")
    try:
        subprocess.run(["convert", str(svg), str(pdf)], check=True)
    except Exception as exc:
        print(f"PDF conversion skipped for {svg.name}: {exc}")
    try:
        subprocess.run(["convert", str(svg), str(png)], check=True)
    except Exception as exc:
        print(f"PNG conversion skipped for {svg.name}: {exc}")


def main() -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    export_steps()
    svgs = [write_side_svg(), write_top_svg(), write_thread_profile_svg(), write_decomposition_svg()]
    write_dxf()
    for svg in svgs:
        svg_to_pdf_and_png(svg)


if __name__ == "__main__":
    main()
