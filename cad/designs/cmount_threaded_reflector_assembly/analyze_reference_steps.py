"""Measure named solids in the local OpenHI/Nature STEP references.

The raw STEP dumps are intentionally ignored by git. Run this helper from the
repo root after unpacking the reference archives under cad/extracted/.
"""

from __future__ import annotations

from pathlib import Path
import re

from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.STEPControl import STEPControl_Reader
from OCP.TopAbs import TopAbs_SOLID
from OCP.TopExp import TopExp_Explorer


ROOT = Path(__file__).resolve().parents[3]
TARGETS = [
    ROOT / "cad/extracted/OpenHI_STEP/A.step",
    ROOT / "cad/extracted/OpenHI_STEP/B.step",
    ROOT / "cad/extracted/OpenHI_STEP/C.step",
    ROOT / "cad/extracted/OpenHI_STEP/Collimator tube.step",
    ROOT / "cad/extracted/OpenHI_STEP/Collimator cap.step",
    ROOT / "cad/extracted/OpenHI_STEP/Lens C holder.step",
]


def step_labels(path: Path) -> list[str]:
    text = path.read_text(errors="ignore")
    return re.findall(r"MANIFOLD_SOLID_BREP\('([^']*)'", text)


def solid_bounds(path: Path) -> list[tuple[float, float, float]]:
    reader = STEPControl_Reader()
    status = reader.ReadFile(str(path))
    if "RetDone" not in str(status):
        raise RuntimeError(f"could not read STEP file: {path}")
    reader.TransferRoots()

    rows: list[tuple[float, float, float]] = []
    explorer = TopExp_Explorer(reader.OneShape(), TopAbs_SOLID)
    while explorer.More():
        box = Bnd_Box()
        BRepBndLib.Add_s(explorer.Current(), box)
        values = box.Get()
        rows.append((values[3] - values[0], values[4] - values[1], values[5] - values[2]))
        explorer.Next()
    return rows


def main() -> None:
    print("| File | Solid label | Bounding box |")
    print("| --- | --- | ---: |")
    for path in TARGETS:
        if not path.exists():
            print(f"| {path.name} | missing local file | n/a |")
            continue
        labels = step_labels(path)
        for index, dims in enumerate(solid_bounds(path)):
            label = labels[index] if index < len(labels) else f"solid {index + 1}"
            box = f"{dims[0]:.3f} x {dims[1]:.3f} x {dims[2]:.3f} mm"
            print(f"| `{path.name}` | `{label}` | `{box}` |")


if __name__ == "__main__":
    main()
