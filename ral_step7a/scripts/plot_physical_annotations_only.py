#!/usr/bin/env python3
"""Plot only the fused LiDAR overlay and physical annotations."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from physical_annotation_common import (
    parse_window_indices,
    read_annotations,
    sample_lidar_points,
    sample_lidar_points_from_summary,
    segment_endpoints,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot LiDAR overlay with physical annotations only.")
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--bag", required=True, type=Path)
    parser.add_argument("--annotations", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--topic", default="/velodyne/points")
    parser.add_argument("--max-messages", default=80, type=int)
    parser.add_argument("--point-stride", default=10, type=int)
    parser.add_argument("--min-z", default=-2.0, type=float)
    parser.add_argument("--max-z", default=3.0, type=float)
    parser.add_argument("--max-points", default=450000, type=int)
    parser.add_argument("--overlay-summary", type=Path)
    parser.add_argument("--overlay-windows", default="")
    parser.add_argument("--max-points-per-window", default=250000, type=int)
    parser.add_argument("--xlim", nargs=2, type=float, metavar=("XMIN", "XMAX"))
    parser.add_argument("--ylim", nargs=2, type=float, metavar=("YMIN", "YMAX"))
    return parser.parse_args()


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
    annotations = read_annotations(args.annotations, args.dataset)

    fig, ax = plt.subplots(figsize=(10.5, 8.0))
    scatter = ax.scatter(
        points[:, 0],
        points[:, 1],
        c=points[:, 2],
        s=0.22,
        cmap="viridis",
        alpha=0.34,
        linewidths=0,
        rasterized=True,
    )
    colorbar = fig.colorbar(scatter, ax=ax, fraction=0.035, pad=0.02)
    colorbar.set_label("z [m]")

    for annotation in annotations:
        if annotation["class"] == "wall":
            start, end = segment_endpoints(annotation)
            is_boundary = annotation.get("annotation_class") != "wall"
            color = "tab:blue" if is_boundary else "black"
            linestyle = "--" if is_boundary else "-"
            ax.plot([start[0], end[0]], [start[1], end[1]], color=color, linewidth=4.0, alpha=0.86, linestyle=linestyle)
            ax.text(annotation["cx"], annotation["cy"], annotation["id"], color=color, fontsize=8, weight="bold")
        else:
            color = "tab:red" if annotation["class"] == "pillar" else "tab:purple"
            marker = "s" if annotation["class"] == "pillar" else "o"
            ax.scatter(
                [annotation["cx"]],
                [annotation["cy"]],
                marker=marker,
                s=92,
                color=color,
                edgecolor="black",
                linewidth=0.7,
                alpha=0.96,
            )
            ax.text(annotation["cx"], annotation["cy"], annotation["id"], color=color, fontsize=8, weight="bold")

    ax.set_title(f"{args.dataset}: LiDAR-derived physical annotations")
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, alpha=0.25)
    if args.xlim:
        ax.set_xlim(*args.xlim)
    if args.ylim:
        ax.set_ylim(*args.ylim)
    fig.tight_layout()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=180)
    plt.close(fig)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
