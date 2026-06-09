"""Generate STEP envelope files and support drawings for the reflector assembly."""

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


def tube_envelope() -> cq.Workplane:
    left = x_cylinder(MALE_CREST_D, THREAD_LEN, 0)
    body = x_cylinder(BODY_D, BODY_LEN, THREAD_LEN)
    right = x_cylinder(MALE_CREST_D, THREAD_LEN, THREAD_LEN + BODY_LEN)
    tube = left.union(body).union(right)
    return tube.cut(x_cylinder(BORE_D, TUBE_TOTAL + 2, -1))


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
    right_x = THREAD_LEN + BODY_LEN
    tube = (
        x_cylinder(MALE_ROOT_D, THREAD_LEN + 0.2, 0)
        .union(x_cylinder(BODY_D, BODY_LEN + 0.4, THREAD_LEN - 0.2))
        .union(x_cylinder(MALE_ROOT_D, THREAD_LEN + 0.2, right_x - 0.2))
        .union(external_thread_brep(0, THREAD_LEN, MALE_ROOT_D, lefthand=False))
        .union(external_thread_brep(right_x, THREAD_LEN, MALE_ROOT_D, lefthand=True))
    )
    return tube.cut(x_cylinder(BORE_D, TUBE_TOTAL + 2, -1))


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
    cutter = x_cylinder(FEMALE_ROOT_D, HOLDER_SOCKET + 1, socket_left - 0.5).union(
        external_thread_brep(socket_left - 0.5, FEMALE_THREAD_LEN, FEMALE_ROOT_D, lefthand=True)
    )
    return holder.cut(cutter)


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
    svgs = [write_side_svg(), write_top_svg()]
    write_dxf()
    for svg in svgs:
        svg_to_pdf_and_png(svg)


if __name__ == "__main__":
    main()
