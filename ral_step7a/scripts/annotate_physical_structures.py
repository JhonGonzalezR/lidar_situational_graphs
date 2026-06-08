#!/usr/bin/env python3
"""Interactively annotate visible physical structures on a top-down LiDAR plot."""

from __future__ import annotations

import argparse
import itertools
import re
from pathlib import Path

import matplotlib.pyplot as plt

from physical_annotation_common import (
    ANNOTATION_FIELDS,
    parse_window_indices,
    read_csv_rows,
    sample_lidar_points,
    sample_lidar_points_from_summary,
    write_csv,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Annotate physical walls, pillars, and pipes from a LiDAR overlay.")
    parser.add_argument("--dataset", required=True, help="Dataset/run label written to the annotation CSV.")
    parser.add_argument("--bag", required=True, type=Path, help="Input ROS 2 bag directory or MCAP file.")
    parser.add_argument("--output", required=True, type=Path, help="Output physical-structure annotation CSV.")
    parser.add_argument("--topic", default="/velodyne/points")
    parser.add_argument("--max-messages", default=80, type=int)
    parser.add_argument("--point-stride", default=10, type=int)
    parser.add_argument("--min-z", default=-2.0, type=float)
    parser.add_argument("--max-z", default=3.0, type=float)
    parser.add_argument("--max-points", default=450000, type=int)
    parser.add_argument("--overlay-summary", type=Path, help="Optional lidar_overlay_windows_summary.csv for fused overlays.")
    parser.add_argument("--overlay-windows", default="", help="Window indices to fuse, e.g. '1 2 3' or '1,2,3'.")
    parser.add_argument("--max-points-per-window", default=250000, type=int)
    parser.add_argument("--xlim", nargs=2, type=float, metavar=("XMIN", "XMAX"))
    parser.add_argument("--ylim", nargs=2, type=float, metavar=("YMIN", "YMAX"))
    return parser.parse_args()


def next_id(prefix: str, counter: itertools.count) -> str:
    return f"{prefix}_{next(counter):02d}"


def next_counter_start(rows: list[dict[str, str]], prefix: str) -> int:
    pattern = re.compile(rf"^{re.escape(prefix)}_(\d+)$")
    values = []
    for row in rows:
        match = pattern.match(row.get("structure_id", ""))
        if match:
            values.append(int(match.group(1)))
    return max(values, default=0) + 1


def main() -> None:
    args = parse_args()
    overlay_windows = parse_window_indices(args.overlay_windows)
    if args.overlay_summary and overlay_windows:
        points = sample_lidar_points_from_summary(
            args.bag,
            args.topic,
            args.overlay_summary,
            overlay_windows,
            args.point_stride,
            args.min_z,
            args.max_z,
            args.max_points_per_window,
            args.max_points,
        )
    else:
        points = sample_lidar_points(
            args.bag,
            args.topic,
            args.max_messages,
            args.point_stride,
            args.min_z,
            args.max_z,
            args.max_points,
        )

    fig, ax = plt.subplots(figsize=(10.5, 8.0))
    ax.scatter(points[:, 0], points[:, 1], c=points[:, 2], s=0.25, cmap="viridis", alpha=0.42, linewidths=0)
    ax.set_title(
        "Physical annotation: w=solid wall, b=WallLike boundary/mesh, "
        "p=pillar, i=pipe, u=undo, q=finish. Walls/boundaries use 2 clicks."
    )
    ax.set_xlabel("x_odom [m]")
    ax.set_ylabel("y_odom [m]")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, alpha=0.25)
    if args.xlim:
        ax.set_xlim(*args.xlim)
    if args.ylim:
        ax.set_ylim(*args.ylim)

    rows: list[dict[str, str]] = read_csv_rows(args.output) if args.output.exists() else []
    drawn_annotations: list[list[object]] = []
    counters = {
        "wall": itertools.count(next_counter_start(rows, "wall")),
        "wall_like_boundary": itertools.count(next_counter_start(rows, "boundary")),
        "pillar": itertools.count(next_counter_start(rows, "pillar")),
        "pipe": itertools.count(next_counter_start(rows, "pipe")),
    }

    def draw_row(row: dict[str, str]) -> list[object]:
        structure_class = row.get("structure_class", "").strip().lower()
        structure_id = row.get("structure_id", "")
        if structure_class in ("wall", "wall_like_boundary", "lidar_boundary", "mesh_boundary"):
            x0 = float(row["x0"])
            y0 = float(row["y0"])
            x1 = float(row["x1"])
            y1 = float(row["y1"])
            color = "tab:blue" if structure_class != "wall" else "black"
            linestyle = "--" if structure_class != "wall" else "-"
            line = ax.plot([x0, x1], [y0, y1], color=color, linewidth=2.8, linestyle=linestyle)[0]
            text = ax.text((x0 + x1) / 2, (y0 + y1) / 2, structure_id, color=color, fontsize=9)
            return [line, text]
        cx = float(row["cx"])
        cy = float(row["cy"])
        color = "tab:red" if structure_class == "pillar" else "tab:purple"
        marker = ax.scatter([cx], [cy], marker="o", s=70, color=color)
        text = ax.text(cx, cy, structure_id, color=color, fontsize=9)
        return [marker, text]

    for row in rows:
        try:
            drawn_annotations.append(draw_row(row))
        except (KeyError, ValueError):
            continue

    print("Annotation controls:")
    print("  w: annotate wall with 2 clicks")
    print("  b: annotate LiDAR-observable WallLike boundary/mesh with 2 clicks")
    print("  p: annotate pillar with 1 click")
    print("  i: annotate pipe with 1 click")
    print("  u: undo last annotation")
    print("  q: finish and write CSV")
    if rows:
        print(f"Loaded {len(rows)} existing annotations from {args.output}.")

    while True:
        key = input("Next annotation [w/p/i/u/q]: ").strip().lower()
        if key in ("q", "quit", "done"):
            break
        if key in ("u", "undo"):
            if not rows:
                print("Nothing to undo.")
                continue
            removed = rows.pop()
            for artist in drawn_annotations.pop():
                artist.remove()
            print(f"Removed {removed['structure_id']}.")
            fig.canvas.draw_idle()
            continue
        if key not in ("w", "b", "p", "i"):
            print("Unknown option. Use w, b, p, i, u, or q.")
            continue
        if key in ("w", "b"):
            structure_class = "wall" if key == "w" else "wall_like_boundary"
            prefix = "wall" if key == "w" else "boundary"
            print(f"Click {structure_class} endpoints in the figure.")
            clicks = plt.ginput(2, timeout=0)
            if len(clicks) != 2:
                print("Wall annotation cancelled.")
                continue
            (x0, y0), (x1, y1) = clicks
            structure_id = next_id(prefix, counters[structure_class])
            rows.append({
                "dataset": args.dataset,
                "structure_id": structure_id,
                "structure_class": structure_class,
                "x0": f"{x0:.6f}",
                "y0": f"{y0:.6f}",
                "x1": f"{x1:.6f}",
                "y1": f"{y1:.6f}",
                "cx": "",
                "cy": "",
                "radius_m": "",
                "notes": "lidar_observable_boundary" if structure_class == "wall_like_boundary" else "",
            })
            color = "tab:blue" if structure_class == "wall_like_boundary" else "black"
            linestyle = "--" if structure_class == "wall_like_boundary" else "-"
            line = ax.plot([x0, x1], [y0, y1], color=color, linewidth=2.8, linestyle=linestyle)[0]
            text = ax.text((x0 + x1) / 2, (y0 + y1) / 2, structure_id, color=color, fontsize=9)
            drawn_annotations.append([line, text])
        else:
            structure_class = "pillar" if key == "p" else "pipe"
            print(f"Click {structure_class} center in the figure.")
            clicks = plt.ginput(1, timeout=0)
            if len(clicks) != 1:
                print(f"{structure_class} annotation cancelled.")
                continue
            cx, cy = clicks[0]
            structure_id = next_id(structure_class, counters[structure_class])
            rows.append({
                "dataset": args.dataset,
                "structure_id": structure_id,
                "structure_class": structure_class,
                "x0": "",
                "y0": "",
                "x1": "",
                "y1": "",
                "cx": f"{cx:.6f}",
                "cy": f"{cy:.6f}",
                "radius_m": "",
                "notes": "",
            })
            color = "tab:red" if structure_class == "pillar" else "tab:purple"
            marker = ax.scatter([cx], [cy], marker="o", s=70, color=color)
            text = ax.text(cx, cy, structure_id, color=color, fontsize=9)
            drawn_annotations.append([marker, text])
        fig.canvas.draw_idle()

    write_csv(args.output, rows, ANNOTATION_FIELDS)
    print(f"Wrote {args.output} with {len(rows)} annotations.")


if __name__ == "__main__":
    main()
