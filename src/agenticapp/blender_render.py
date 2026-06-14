from __future__ import annotations

from pathlib import Path
import json
import os
import shutil
import subprocess
from typing import Any

from .scene_spec import SceneRenderPlan, create_render_plan


class BlenderRenderError(RuntimeError):
    """Raised when Blender cannot render a scene spec."""


def find_blender(explicit: str | None = None) -> str | None:
    candidates = [
        explicit,
        os.environ.get("BLENDER_BIN"),
        shutil.which("blender"),
        str(Path.home() / ".local/share/labcanvas/blender/blender-4.0.2-linux-x64/blender"),
        str(Path.home() / ".local/share/appautoaction/blender/blender-4.0.2-linux-x64/blender"),
    ]
    for candidate in candidates:
        if candidate and Path(candidate).expanduser().is_file() and os.access(Path(candidate).expanduser(), os.X_OK):
            return str(Path(candidate).expanduser())
    return None


def render_scene_spec(
    spec_path: str | Path,
    output_dir: str | Path | None = None,
    *,
    blender_bin: str | None = None,
    dry_run: bool = False,
    timeout: float = 180,
) -> dict[str, Any]:
    plan = create_render_plan(spec_path, output_dir)
    blender = find_blender(blender_bin)
    result: dict[str, Any] = {"ok": True, "plan": plan.to_dict(), "blender": blender}
    if dry_run:
        result["status"] = "dry-run"
        return result
    if not blender:
        raise BlenderRenderError("Blender executable not found. Set BLENDER_BIN or run scripts/install_blender_portable.sh")

    plan.output_dir.mkdir(parents=True, exist_ok=True)
    renderer = Path(__file__).resolve().parent / "blender" / "scene_renderer.py"
    command = [
        blender,
        "-b",
        "--python",
        str(renderer),
        "--",
        "--spec",
        str(plan.spec_path),
        "--output-dir",
        str(plan.output_dir),
    ]
    proc = subprocess.run(command, text=True, capture_output=True, timeout=timeout, check=False)
    result.update(
        {
            "status": str(proc.returncode),
            "returncode": proc.returncode,
            "stdout_tail": tail(proc.stdout),
            "stderr_tail": tail(proc.stderr),
        }
    )
    if proc.returncode != 0:
        result["ok"] = False
        raise BlenderRenderError(json.dumps(result, indent=2, sort_keys=True))
    return result


def tail(text: str, max_lines: int = 25) -> str:
    lines = text.splitlines()
    return "\n".join(lines[-max_lines:])
