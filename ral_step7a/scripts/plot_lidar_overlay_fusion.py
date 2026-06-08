#!/usr/bin/env python3
"""Fuse selected LiDAR overlay windows into a single top-down plot."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from plot_lidar_overlay_windows import sample_window


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fuse selected LiDAR overlay windows using their summary CSV.")
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--bag", required=True, type=Path)
    parser.add_argument("--summary", required=True, type=Path, help="lidar_overlay_windows_summary.csv")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--windows", nargs="+", type=int, required=True, help="Window indices to fuse, e.g. 1 2 3.")
    parser.add_argument("--topic", default="/velodyne/points")
    parser.add_argument("--point-stride", default=10, type=int)
    parser.add_argument("--min-z", default=-2.0, type=float)
    parser.add_argument("--max-z", default=3.0, type=float)
    parser.add_argument("--max-points-per-window", default=250000, type=int)
    parser.add_argument("--point-size", default=0.22, type=float)
    parser.add_argument("--alpha", default=0.42, type=float)
    parser.add_argument("--xlim", nargs=2, type=float, metavar=("XMIN", "XMAX"))
    parser.add_argument("--ylim", nargs=2, type=float, metavar=("YMIN", "YMAX"))
    return parser.parse_args()


def read_summary(path: Path) -> dict[int, dict[str, str]]:
    with path.open(newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))
    if not rows:
        raise RuntimeError(f"Empty overlay summary: {path}")
    return {int(row["window_index"]): row for row in rows}


def main() -> None:
    args = parse_args()
    summary = read_summary(args.summary)
    colors = ["#2563eb", "#f97316", "#16a34a", "#dc2626", "#7c3aed", "#0891b2"]

    fig, ax = plt.subplots(figsize=(10.8, 8.0))
    legend_handles: list[Line2D] = []
    total_points = 0
    fused_ranges: list[str] = []

    for color_index, window_index in enumerate(args.windows):
        if window_index not in summary:
            raise RuntimeError(f"Window {window_index} not found in {args.summary}")
        row = summary[window_index]
        start = int(row["start_message"])
        sampled_messages = int(row["sampled_messages"])
        points, _, end, first_time_sec, last_time_sec = sample_window(
            args.bag,
            args.topic,
            start,
            sampled_messages,
            args.point_stride,
            args.min_z,
            args.max_z,
            args.max_points_per_window,
        )
        color = colors[color_index % len(colors)]
        ax.scatter(
            points[:, 0],
            points[:, 1],
            s=args.point_size,
            color=color,
            alpha=args.alpha,
            linewidths=0,
            rasterized=True,
        )
        total_points += len(points)
        time_label = ""
        if first_time_sec is not None and last_time_sec is not None:
            time_label = f", {first_time_sec:.1f}-{last_time_sec:.1f}s"
        label = f"window {window_index}: msg {start}-{end}{time_label}"
        fused_ranges.append(f"W{window_index} {start}-{end}")
        legend_handles.append(
            Line2D([0], [0], marker="o", color="none", markerfacecolor=color, markersize=7, label=label)
        )

    ax.set_title(f"{args.dataset}: fused LiDAR overlay ({', '.join(fused_ranges)})\n{total_points} points")
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, alpha=0.25)
    if args.xlim:
        ax.set_xlim(*args.xlim)
    if args.ylim:
        ax.set_ylim(*args.ylim)
    ax.legend(handles=legend_handles, loc="upper right", fontsize=8, framealpha=0.88)
    fig.tight_layout()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=180)
    plt.close(fig)
    print(f"Wrote {args.output} ({total_points} fused points)")


if __name__ == "__main__":
    main()
