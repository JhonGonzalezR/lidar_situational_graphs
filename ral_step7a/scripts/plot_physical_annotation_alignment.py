#!/usr/bin/env python3
"""Plot physical annotations and annotation-matched predictions on LiDAR."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt

from physical_annotation_common import (
    read_annotations,
    read_csv_rows,
    read_ingraph_predictions,
    read_sgraphs_wall_predictions,
    parse_window_indices,
    sample_lidar_points,
    sample_lidar_points_from_summary,
    segment_endpoints,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot annotation alignment results.")
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--bag", required=True, type=Path)
    parser.add_argument("--annotations", required=True, type=Path)
    parser.add_argument("--alignment", required=True, type=Path, help="Per-prediction alignment CSV.")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--ingraph-tracks", type=Path)
    parser.add_argument("--sgraphs-planes", type=Path)
    parser.add_argument("--sgraphs-min-observations", default=20, type=int)
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
    parser.add_argument(
        "--hide-unlisted-predictions",
        action="store_true",
        help="Only draw predictions that appear in the alignment CSV.",
    )
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
        points = sample_lidar_points(args.bag, args.topic, args.max_messages, args.point_stride, args.min_z, args.max_z, args.max_points)
    annotations = read_annotations(args.annotations, args.dataset)
    alignment_rows = read_csv_rows(args.alignment)
    status = {(row["model"], row["structure_class"], row["prediction_id"]): row["matched"] == "true" for row in alignment_rows}

    predictions = []
    if args.ingraph_tracks:
        predictions.extend(read_ingraph_predictions(args.ingraph_tracks, args.dataset, "latest_strong", "strong", 1))
    if args.sgraphs_planes:
        predictions.extend(read_sgraphs_wall_predictions(args.sgraphs_planes, args.dataset, args.sgraphs_min_observations))

    fig, ax = plt.subplots(figsize=(10.5, 8.0))
    ax.scatter(points[:, 0], points[:, 1], c=points[:, 2], s=0.22, cmap="viridis", alpha=0.35, linewidths=0, rasterized=True)

    for annotation in annotations:
        if annotation["class"] == "wall":
            start, end = segment_endpoints(annotation)
            is_boundary = annotation.get("annotation_class") != "wall"
            color = "tab:blue" if is_boundary else "black"
            linestyle = "--" if is_boundary else "-"
            ax.plot([start[0], end[0]], [start[1], end[1]], color=color, linewidth=4.0, alpha=0.70, linestyle=linestyle)
            ax.text(annotation["cx"], annotation["cy"], annotation["id"], color=color, fontsize=9, weight="bold")
        else:
            color = "tab:red" if annotation["class"] == "pillar" else "tab:purple"
            ax.scatter([annotation["cx"]], [annotation["cy"]], marker="o", s=90, color=color, edgecolor="black", linewidth=0.7)
            ax.text(annotation["cx"], annotation["cy"], annotation["id"], color=color, fontsize=9, weight="bold")

    for prediction in predictions:
        key = (prediction["model"], prediction["class"], str(prediction["id"]))
        if args.hide_unlisted_predictions and key not in status:
            continue
        matched = status.get(key, False)
        color = "tab:green" if matched else "tab:red"
        alpha = 0.80 if matched else 0.45
        linestyle = "-" if matched else "--"
        label_prefix = "IG" if prediction["model"] == "InGraph" else "SG"
        if prediction["class"] == "wall":
            start, end = segment_endpoints(prediction)
            ax.plot([start[0], end[0]], [start[1], end[1]], color=color, linewidth=1.8, alpha=alpha, linestyle=linestyle)
            ax.text(prediction["cx"], prediction["cy"], f"{label_prefix}:{prediction['id']}", color=color, fontsize=7)
        else:
            marker = "s" if prediction["class"] == "pillar" else "x"
            ax.scatter([prediction["cx"]], [prediction["cy"]], marker=marker, s=48, color=color, alpha=alpha)
            ax.text(prediction["cx"], prediction["cy"], f"{label_prefix}:{prediction['id']}", color=color, fontsize=7)

    ax.set_title(f"{args.dataset}: physical annotation alignment")
    ax.set_xlabel("x_odom [m]")
    ax.set_ylabel("y_odom [m]")
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
