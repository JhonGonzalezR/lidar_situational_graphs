#!/usr/bin/env python3
"""Create quick-look plots for S-Graphs wall plane CSV exports.

The plots are diagnostic, not final paper figures. They help answer:

- Did S-Graphs publish persistent plane IDs?
- Are centroids and support extents finite?
- Which plane IDs dominate the run?
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt


def read_rows(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open(newline="") as csv_file:
        return list(csv.DictReader(csv_file))


def to_float(value: str) -> float | None:
    if value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def plot_centroids(
    rows: list[dict[str, str]],
    output_path: Path,
    x_field: str,
    y_field: str,
    frame_label: str,
) -> None:
    groups = sorted({row["plane_group"] for row in rows})
    markers = {"x": "o", "y": "s"}

    fig, ax = plt.subplots(figsize=(7.0, 6.0))
    for group in groups:
        group_rows = [row for row in rows if row["plane_group"] == group]
        xs = [to_float(row[x_field]) for row in group_rows]
        ys = [to_float(row[y_field]) for row in group_rows]
        ids = [int(row["plane_id"]) for row in group_rows]

        clean = [
            (x, y, plane_id)
            for x, y, plane_id in zip(xs, ys, ids)
            if x is not None and y is not None
        ]
        if not clean:
            continue

        ax.scatter(
            [item[0] for item in clean],
            [item[1] for item in clean],
            c=[item[2] for item in clean],
            marker=markers.get(group, "o"),
            s=32,
            alpha=0.8,
            label=f"{group}-planes",
        )

    ax.set_title(f"S-Graphs wall plane centroids in {frame_label} frame")
    ax.set_xlabel(f"{x_field} [m]")
    ax.set_ylabel(f"{y_field} [m]")
    ax.axis("equal")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def plot_id_counts(rows: list[dict[str, str]], output_path: Path) -> None:
    counts = Counter(f"{row['plane_group']}:{row['plane_id']}" for row in rows)
    labels, values = zip(*counts.most_common()) if counts else ([], [])

    fig, ax = plt.subplots(figsize=(9.0, 4.5))
    ax.bar(range(len(values)), values)
    ax.set_title("S-Graphs plane observation count by plane ID")
    ax.set_xlabel("plane group:id")
    ax.set_ylabel("observations")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=60, ha="right")
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot S-Graphs wall plane CSV.")
    parser.add_argument("--csv", required=True, type=Path, help="Input CSV path.")
    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Directory for diagnostic plot PNGs.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = read_rows(args.csv)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    centroid_map_png = args.output_dir / "sgraphs_wall_plane_centroids_map.png"
    centroid_odom_png = args.output_dir / "sgraphs_wall_plane_centroids_odom.png"
    counts_png = args.output_dir / "sgraphs_wall_plane_id_counts.png"

    plot_centroids(rows, centroid_map_png, "centroid_x_map", "centroid_y_map", "native map")
    if any(row.get("centroid_x_odom") for row in rows):
        plot_centroids(
            rows,
            centroid_odom_png,
            "centroid_x_odom",
            "centroid_y_odom",
            "odom",
        )
    plot_id_counts(rows, counts_png)

    print(f"Rows: {len(rows)}")
    print(f"Wrote {centroid_map_png}")
    if centroid_odom_png.exists():
        print(f"Wrote {centroid_odom_png}")
    print(f"Wrote {counts_png}")


if __name__ == "__main__":
    main()
