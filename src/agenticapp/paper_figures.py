from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path
import re
from typing import Any

from .scene_spec import slugify


DEFAULT_TOPICS = (
    "Light source",
    "Polarizer",
    "Sample",
    "Detector",
    "Controller",
    "Waveform",
    "Culture",
    "Microscope",
    "Protein",
    "Cell",
    "Chip",
    "Analysis",
)


@dataclass(frozen=True)
class PaperFigureResult:
    path: Path
    rows: int
    cols: int
    title: str
    prompt: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "rows": self.rows,
            "cols": self.cols,
            "title": self.title,
            "prompt": self.prompt,
        }


def parse_grid_size(text: str, default_rows: int = 2, default_cols: int = 3) -> tuple[int, int]:
    match = re.search(r"\b([1-9]\d?)\s*[xX]\s*([1-9]\d?)\b", text)
    if match:
        return _clamp_dimension(int(match.group(1))), _clamp_dimension(int(match.group(2)))
    rows = re.search(r"\brows?\s*[:= ]\s*([1-9]\d?)\b", text, re.I)
    cols = re.search(r"\bcols?(?:umns?)?\s*[:= ]\s*([1-9]\d?)\b", text, re.I)
    return (
        _clamp_dimension(int(rows.group(1))) if rows else default_rows,
        _clamp_dimension(int(cols.group(1))) if cols else default_cols,
    )


def generate_icon_grid(
    prompt: str,
    output_dir: str | Path,
    *,
    rows: int = 2,
    cols: int = 3,
    cell_size: int = 240,
    border: int = 4,
    labels: list[str] | None = None,
) -> PaperFigureResult:
    rows = _clamp_dimension(rows)
    cols = _clamp_dimension(cols)
    cell_size = max(120, min(int(cell_size), 420))
    border = max(1, min(int(border), 10))
    title = figure_title(prompt)
    slug = slugify(f"{title}-{rows}x{cols}")
    path = Path(output_dir) / f"{slug}.svg"
    path.parent.mkdir(parents=True, exist_ok=True)
    topics = labels or choose_topics(prompt, rows * cols)
    width = cols * cell_size + border
    height = rows * cell_size + border

    pieces = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">',
        "<defs>",
        '<style><![CDATA[text{font-family:Inter,Arial,sans-serif}.label{font-size:18px;font-weight:700;fill:#111827}.caption{font-size:12px;font-weight:600;fill:#374151}.icon{fill:none;stroke:#111827;stroke-width:5;stroke-linecap:round;stroke-linejoin:round}.accent-a{stroke:#0f766e}.accent-b{stroke:#c2410c}.accent-c{stroke:#2563eb}.fill-a{fill:#d1fae5}.fill-b{fill:#ffedd5}.fill-c{fill:#dbeafe}]]></style>',
        "</defs>",
        '<rect x="0" y="0" width="100%" height="100%" fill="#ffffff"/>',
    ]

    for row in range(rows):
        for col in range(cols):
            index = row * cols + col
            x = border + col * cell_size
            y = border + row * cell_size
            topic = topics[index % len(topics)]
            pieces.append(cell_group(topic, x, y, cell_size - border, index))

    for col in range(cols + 1):
        x = col * cell_size + border / 2
        pieces.append(f'<line x1="{x:g}" y1="0" x2="{x:g}" y2="{height}" stroke="#000" stroke-width="{border}"/>')
    for row in range(rows + 1):
        y = row * cell_size + border / 2
        pieces.append(f'<line x1="0" y1="{y:g}" x2="{width}" y2="{y:g}" stroke="#000" stroke-width="{border}"/>')

    pieces.append("</svg>")
    path.write_text("\n".join(pieces) + "\n", encoding="utf-8")
    return PaperFigureResult(path=path, rows=rows, cols=cols, title=title, prompt=prompt)


def figure_title(prompt: str) -> str:
    text = re.sub(r"\s+", " ", prompt.strip())
    if not text:
        return "Paper figure grid"
    text = re.sub(r"\b[1-9]\d?\s*[xX]\s*[1-9]\d?\b", "", text)
    text = re.sub(r"\b(make|draw|generate|create|paper|figure|grid|icons?)\b", "", text, flags=re.I)
    text = re.sub(r"\s+", " ", text).strip(" -:,.")
    return text[:72].strip() or "Paper figure grid"


def choose_topics(prompt: str, count: int) -> list[str]:
    text = prompt.lower()
    if any(word in text for word in ("bio", "cell", "protein", "biorender", "assay", "tissue")):
        topics = ["Cell", "Protein", "Microscope", "Culture", "Assay", "Analysis", "Reagent", "Tissue"]
    elif any(word in text for word in ("optic", "vspice", "laser", "camera", "polar")):
        topics = ["Light source", "Polarizer", "Retarder", "Sample", "Detector", "Waveform", "Controller", "Analysis"]
    elif any(word in text for word in ("device", "chip", "cad", "blender", "openscad")):
        topics = ["Device", "Chip", "Actuator", "Sensor", "Mount", "Signal", "Housing", "Render"]
    else:
        topics = list(DEFAULT_TOPICS)
    while len(topics) < count:
        topics.extend(DEFAULT_TOPICS)
    return topics[:count]


def cell_group(topic: str, x: int, y: int, size: int, index: int) -> str:
    palette = (("fill-a", "accent-a"), ("fill-b", "accent-b"), ("fill-c", "accent-c"))[index % 3]
    center_x = x + size / 2
    icon_y = y + size * 0.43
    label_y = y + size - 34
    caption_y = y + size - 15
    icon = icon_shape(topic, center_x, icon_y, size * 0.34, palette[1])
    return "\n".join(
        [
            f'<g data-topic="{escape(topic)}">',
            f'<rect x="{x}" y="{y}" width="{size}" height="{size}" fill="#fff" />',
            f'<circle class="{palette[0]}" cx="{center_x:g}" cy="{icon_y:g}" r="{size * 0.28:g}" opacity="0.92"/>',
            icon,
            f'<text class="label" x="{center_x:g}" y="{label_y:g}" text-anchor="middle">{escape(short_label(topic))}</text>',
            f'<text class="caption" x="{center_x:g}" y="{caption_y:g}" text-anchor="middle">panel {index + 1}</text>',
            "</g>",
        ]
    )


def icon_shape(topic: str, cx: float, cy: float, radius: float, accent_class: str) -> str:
    key = topic.lower()
    if any(word in key for word in ("light", "laser", "source")):
        return f'<g class="icon {accent_class}"><circle cx="{cx - radius * 0.42:g}" cy="{cy:g}" r="{radius * 0.18:g}"/><path d="M {cx - radius * 0.2:g} {cy:g} L {cx + radius * 0.42:g} {cy - radius * 0.28:g} L {cx + radius * 0.42:g} {cy + radius * 0.28:g} Z"/><path d="M {cx + radius * 0.58:g} {cy - radius * 0.42:g} L {cx + radius * 0.88:g} {cy - radius * 0.62:g} M {cx + radius * 0.62:g} {cy:g} H {cx + radius:g} M {cx + radius * 0.58:g} {cy + radius * 0.42:g} L {cx + radius * 0.88:g} {cy + radius * 0.62:g}"/></g>'
    if any(word in key for word in ("polar", "retarder", "filter", "sample")):
        return f'<g class="icon {accent_class}"><rect x="{cx - radius * 0.48:g}" y="{cy - radius * 0.5:g}" width="{radius * 0.96:g}" height="{radius:g}" rx="10"/><path d="M {cx - radius * 0.42:g} {cy + radius * 0.34:g} L {cx + radius * 0.36:g} {cy - radius * 0.44:g} M {cx - radius * 0.18:g} {cy + radius * 0.48:g} L {cx + radius * 0.48:g} {cy - radius * 0.18:g}"/></g>'
    if any(word in key for word in ("detector", "camera", "sensor")):
        return f'<g class="icon {accent_class}"><rect x="{cx - radius * 0.58:g}" y="{cy - radius * 0.36:g}" width="{radius * 1.16:g}" height="{radius * 0.78:g}" rx="12"/><circle cx="{cx:g}" cy="{cy:g}" r="{radius * 0.25:g}"/><path d="M {cx - radius * 0.38:g} {cy - radius * 0.5:g} H {cx + radius * 0.1:g}"/></g>'
    if any(word in key for word in ("wave", "signal", "analysis")):
        return f'<g class="icon {accent_class}"><path d="M {cx - radius:g} {cy:g} C {cx - radius * 0.72:g} {cy - radius * 0.8:g}, {cx - radius * 0.38:g} {cy - radius * 0.8:g}, {cx - radius * 0.1:g} {cy:g} S {cx + radius * 0.54:g} {cy + radius * 0.8:g}, {cx + radius:g} {cy:g}"/><path d="M {cx - radius:g} {cy + radius * 0.52:g} H {cx + radius:g}"/></g>'
    if any(word in key for word in ("cell", "culture", "tissue")):
        return f'<g class="icon {accent_class}"><circle cx="{cx - radius * 0.22:g}" cy="{cy - radius * 0.06:g}" r="{radius * 0.42:g}"/><circle cx="{cx + radius * 0.34:g}" cy="{cy + radius * 0.24:g}" r="{radius * 0.28:g}"/><circle cx="{cx - radius * 0.2:g}" cy="{cy - radius * 0.06:g}" r="{radius * 0.12:g}"/></g>'
    if any(word in key for word in ("protein", "assay", "reagent")):
        return f'<g class="icon {accent_class}"><circle cx="{cx - radius * 0.46:g}" cy="{cy:g}" r="{radius * 0.16:g}"/><circle cx="{cx:g}" cy="{cy - radius * 0.34:g}" r="{radius * 0.16:g}"/><circle cx="{cx + radius * 0.46:g}" cy="{cy:g}" r="{radius * 0.16:g}"/><circle cx="{cx:g}" cy="{cy + radius * 0.36:g}" r="{radius * 0.16:g}"/><path d="M {cx - radius * 0.32:g} {cy - radius * 0.1:g} L {cx - radius * 0.12:g} {cy - radius * 0.24:g} M {cx + radius * 0.12:g} {cy - radius * 0.24:g} L {cx + radius * 0.32:g} {cy - radius * 0.1:g} M {cx + radius * 0.3:g} {cy + radius * 0.12:g} L {cx + radius * 0.12:g} {cy + radius * 0.26:g} M {cx - radius * 0.12:g} {cy + radius * 0.26:g} L {cx - radius * 0.32:g} {cy + radius * 0.12:g}"/></g>'
    if any(word in key for word in ("chip", "controller", "device", "mount", "housing")):
        return f'<g class="icon {accent_class}"><rect x="{cx - radius * 0.52:g}" y="{cy - radius * 0.52:g}" width="{radius * 1.04:g}" height="{radius * 1.04:g}" rx="12"/><path d="M {cx - radius * 0.2:g} {cy - radius * 0.52:g} V {cy - radius * 0.8:g} M {cx + radius * 0.2:g} {cy - radius * 0.52:g} V {cy - radius * 0.8:g} M {cx - radius * 0.2:g} {cy + radius * 0.52:g} V {cy + radius * 0.8:g} M {cx + radius * 0.2:g} {cy + radius * 0.52:g} V {cy + radius * 0.8:g} M {cx - radius * 0.52:g} {cy - radius * 0.2:g} H {cx - radius * 0.8:g} M {cx - radius * 0.52:g} {cy + radius * 0.2:g} H {cx - radius * 0.8:g} M {cx + radius * 0.52:g} {cy - radius * 0.2:g} H {cx + radius * 0.8:g} M {cx + radius * 0.52:g} {cy + radius * 0.2:g} H {cx + radius * 0.8:g}"/></g>'
    return f'<g class="icon {accent_class}"><path d="M {cx - radius * 0.54:g} {cy + radius * 0.5:g} L {cx:g} {cy - radius * 0.64:g} L {cx + radius * 0.54:g} {cy + radius * 0.5:g} Z"/><path d="M {cx - radius * 0.22:g} {cy + radius * 0.05:g} H {cx + radius * 0.22:g}"/></g>'


def short_label(topic: str) -> str:
    return re.sub(r"\s+", " ", topic.strip())[:24]


def _clamp_dimension(value: int) -> int:
    return max(1, min(int(value), 8))
