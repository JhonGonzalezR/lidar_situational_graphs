#!/usr/bin/env python3
"""Plot S-Graphs wall-plane hypotheses as top-down 2D wall segments.

This diagnostic figure is easier to interpret than centroid-only plots. It
uses the per-plane summary table and renders each persistent S-Graphs plane ID
as a finite line segment in the odom frame.

The segment is an approximation for visual interpretation:

- center: mean support centroid in odom
- orientation: mean plane normal in odom, with segment direction perpendicular
  to that normal in XY
- length: derived from the observed support extents in the raw plane CSV

It should not be treated as a metric by itself. The formal comparison should
still use the CSV fields and documented matching rules.
"""

from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt


def to_float(value: str) -> float | None:
    if value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as csv_file:
        return list(csv.DictReader(csv_file))


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def normalize_xy(x: float, y: float) -> tuple[float, float]:
    norm = math.hypot(x, y)
    if norm <= 0.0:
        return (1.0, 0.0)
    return (x / norm, y / norm)


def build_segments(
    plane_rows: list[dict[str, str]],
    min_observations: int,
    frame: str,
) -> tuple[list[dict[str, float | str | int]], str]:
    if frame == "auto":
        has_odom = any(
            row.get("centroid_x_odom")
            and row.get("centroid_y_odom")
            and row.get("nx_odom")
            and row.get("ny_odom")
            for row in plane_rows
        )
        frame = "odom" if has_odom else "map"

    if frame not in ("odom", "map"):
        raise ValueError(f"Unsupported frame: {frame}")

    centroid_x_key = f"centroid_x_{frame}"
    centroid_y_key = f"centroid_y_{frame}"
    normal_x_key = f"nx_{frame}"
    normal_y_key = f"ny_{frame}"

    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in plane_rows:
        grouped[(row["plane_group"], row["plane_id"])].append(row)

    segments = []
    for (plane_group, plane_id), rows in grouped.items():
        if len(rows) < min_observations:
            continue

        cx = [value for row in rows if (value := to_float(row[centroid_x_key])) is not None]
        cy = [value for row in rows if (value := to_float(row[centroid_y_key])) is not None]
        nx = [value for row in rows if (value := to_float(row[normal_x_key])) is not None]
        ny = [value for row in rows if (value := to_float(row[normal_y_key])) is not None]
        ext_x = [value for row in rows if (value := to_float(row["extent_x_map"])) is not None]
        ext_y = [value for row in rows if (value := to_float(row["extent_y_map"])) is not None]

        if not (cx and cy and nx and ny):
            continue

        normal_x, normal_y = normalize_xy(mean(nx), mean(ny))
        direction_x, direction_y = normalize_xy(-normal_y, normal_x)

        # Use the larger observed XY support extent as approximate segment length.
        # Clamp to avoid tiny unreadable segments when S-Graphs publishes compact support.
        support_lengths = [
            math.hypot(x_extent, y_extent)
            for x_extent, y_extent in zip(ext_x, ext_y)
        ]
        length = max(support_lengths) if support_lengths else 2.0
        length = max(length, 1.0)

        segments.append(
            {
                "label": f"{plane_group}:{plane_id}",
                "plane_group": plane_group,
                "plane_id": int(plane_id),
                "observations": len(rows),
                "cx": mean(cx),
                "cy": mean(cy),
                "dx": direction_x,
                "dy": direction_y,
                "length": length,
            }
        )

    return sorted(segments, key=lambda item: int(item["observations"]), reverse=True), frame


def plot_segments(
    segments: list[dict[str, float | str | int]],
    output: Path,
    frame: str,
) -> None:
    fig, ax = plt.subplots(figsize=(8.0, 7.0))

    for segment in segments:
        cx = float(segment["cx"])
        cy = float(segment["cy"])
        dx = float(segment["dx"])
        dy = float(segment["dy"])
        half = 0.5 * float(segment["length"])
        obs = int(segment["observations"])

        x0 = cx - half * dx
        y0 = cy - half * dy
        x1 = cx + half * dx
        y1 = cy + half * dy

        linewidth = 1.5 + 3.0 * min(obs / max(int(segments[0]["observations"]), 1), 1.0)
        ax.plot([x0, x1], [y0, y1], linewidth=linewidth, alpha=0.82)
        ax.scatter([cx], [cy], s=18, color="black", alpha=0.7)
        ax.text(cx, cy, str(segment["label"]), fontsize=8, ha="left", va="bottom")

    ax.set_title(f"S-Graphs persistent wall-plane hypotheses in {frame} frame")
    ax.set_xlabel(f"x_{frame} [m]")
    ax.set_ylabel(f"y_{frame} [m]")
    ax.axis("equal")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=180)
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plot S-Graphs wall-plane IDs as top-down odom-frame segments."
    )
    parser.add_argument("--csv", required=True, type=Path, help="Input wall-plane CSV.")
    parser.add_argument("--output", required=True, type=Path, help="Output PNG.")
    parser.add_argument(
        "--min-observations",
        default=20,
        type=int,
        help="Minimum observations required to plot a plane ID.",
    )
    parser.add_argument(
        "--segment-frame",
        default="auto",
        choices=("auto", "odom", "map"),
        help="Frame used for S-Graphs segments. Auto uses odom if available, otherwise map.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = read_csv(args.csv)
    segments, frame = build_segments(rows, args.min_observations, args.segment_frame)
    plot_segments(segments, args.output, frame)
    print(f"Segments plotted: {len(segments)}")
    print(f"S-Graphs segment frame: {frame}")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
