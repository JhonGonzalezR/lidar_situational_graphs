#!/usr/bin/env python3
"""Overlay S-Graphs wall-plane hypotheses on the input LiDAR cloud.

This figure is a visual sanity check for the RA-L Step 7A baseline. It does
not score the method by itself; it shows whether persistent S-Graphs plane
hypotheses are geometrically plausible with respect to the observed cloud.

For the Spot `dinamicaStaticV0` bag, `/velodyne/points` is emitted in an
odom-aligned sensor frame by the driver. Therefore this script plots raw cloud
XY coordinates directly with the S-Graphs odom-frame wall hypotheses exported
by `convert_sgraphs_planes_to_csv.py`.
"""

from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import rosbag2_py
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message
from sensor_msgs_py import point_cloud2


def to_float(value: str) -> float | None:
    if value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def normalize_xy(x: float, y: float) -> tuple[float, float]:
    norm = math.hypot(x, y)
    if norm <= 0.0:
        return (1.0, 0.0)
    return (x / norm, y / norm)


def read_plane_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as csv_file:
        return list(csv.DictReader(csv_file))


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
        support_lengths = [
            math.hypot(x_extent, y_extent)
            for x_extent, y_extent in zip(ext_x, ext_y)
        ]
        length = max(support_lengths) if support_lengths else 2.0
        length = max(length, 1.0)

        segments.append(
            {
                "label": f"{plane_group}:{plane_id}",
                "observations": len(rows),
                "cx": mean(cx),
                "cy": mean(cy),
                "dx": direction_x,
                "dy": direction_y,
                "length": length,
            }
        )

    return sorted(segments, key=lambda item: int(item["observations"]), reverse=True), frame


def open_reader(bag_path: Path, topic: str) -> rosbag2_py.SequentialReader:
    reader = rosbag2_py.SequentialReader()
    storage_options = rosbag2_py.StorageOptions(uri=str(bag_path), storage_id="sqlite3")
    converter_options = rosbag2_py.ConverterOptions(
        input_serialization_format="cdr",
        output_serialization_format="cdr",
    )
    reader.open(storage_options, converter_options)
    reader.set_filter(rosbag2_py.StorageFilter(topics=[topic]))
    return reader


def topic_type(reader: rosbag2_py.SequentialReader, topic: str) -> str:
    for item in reader.get_all_topics_and_types():
        if item.name == topic:
            return item.type
    raise RuntimeError(f"Topic not found in bag: {topic}")


def point_cloud_to_xyz(message: object) -> np.ndarray:
    points = point_cloud2.read_points_numpy(
        message,
        field_names=("x", "y", "z"),
        skip_nans=True,
    )
    if points.dtype.names:
        return np.column_stack([points["x"], points["y"], points["z"]])
    return np.asarray(points, dtype=np.float32).reshape((-1, 3))


def sample_lidar_points(
    bag_path: Path,
    topic: str,
    max_messages: int,
    point_stride: int,
    min_z: float,
    max_z: float,
    max_points: int,
) -> np.ndarray:
    reader = open_reader(bag_path, topic)
    message_type = get_message(topic_type(reader, topic))

    clouds = []
    message_count = 0
    while reader.has_next() and message_count < max_messages:
        _, data, _ = reader.read_next()
        message = deserialize_message(data, message_type)
        xyz = point_cloud_to_xyz(message)
        if xyz.size == 0:
            continue

        xyz = xyz[(xyz[:, 2] >= min_z) & (xyz[:, 2] <= max_z)]
        if point_stride > 1:
            xyz = xyz[::point_stride]
        if xyz.size:
            clouds.append(xyz)
        message_count += 1

    if not clouds:
        raise RuntimeError(f"No LiDAR points sampled from {topic}")

    points = np.concatenate(clouds, axis=0)
    if len(points) > max_points:
        indices = np.linspace(0, len(points) - 1, max_points).astype(np.int64)
        points = points[indices]
    return points


def plot_overlay(
    points: np.ndarray,
    segments: list[dict[str, float | str | int]],
    output: Path,
    title: str,
    segment_frame: str,
) -> None:
    fig, ax = plt.subplots(figsize=(9.0, 8.0))

    scatter = ax.scatter(
        points[:, 0],
        points[:, 1],
        c=points[:, 2],
        s=0.18,
        cmap="viridis",
        alpha=0.35,
        linewidths=0,
        rasterized=True,
    )
    colorbar = fig.colorbar(scatter, ax=ax, fraction=0.035, pad=0.02)
    colorbar.set_label("z [m]")

    max_observations = max((int(segment["observations"]) for segment in segments), default=1)
    for segment in segments:
        cx = float(segment["cx"])
        cy = float(segment["cy"])
        dx = float(segment["dx"])
        dy = float(segment["dy"])
        half = 0.5 * float(segment["length"])
        observations = int(segment["observations"])

        x0 = cx - half * dx
        y0 = cy - half * dy
        x1 = cx + half * dx
        y1 = cy + half * dy
        linewidth = 1.8 + 3.2 * min(observations / max_observations, 1.0)

        ax.plot([x0, x1], [y0, y1], linewidth=linewidth, alpha=0.92)
        ax.scatter([cx], [cy], s=18, color="black", alpha=0.78)
        ax.text(cx, cy, str(segment["label"]), fontsize=8, ha="left", va="bottom")

    ax.set_title(title)
    ax.set_xlabel(f"x_{segment_frame} / odom-aligned LiDAR x [m]")
    ax.set_ylabel(f"y_{segment_frame} / odom-aligned LiDAR y [m]")
    ax.axis("equal")
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=180)
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Overlay S-Graphs wall-plane hypotheses on a sampled LiDAR cloud."
    )
    parser.add_argument("--bag", required=True, type=Path, help="Input ROS 2 bag directory.")
    parser.add_argument("--topic", default="/velodyne/points", help="PointCloud2 topic.")
    parser.add_argument("--csv", required=True, type=Path, help="S-Graphs wall-plane CSV.")
    parser.add_argument("--output", required=True, type=Path, help="Output PNG.")
    parser.add_argument("--max-messages", default=60, type=int, help="Maximum cloud messages to sample.")
    parser.add_argument("--point-stride", default=12, type=int, help="Keep one point every N points.")
    parser.add_argument("--min-z", default=-2.0, type=float, help="Minimum z to plot.")
    parser.add_argument("--max-z", default=3.0, type=float, help="Maximum z to plot.")
    parser.add_argument("--max-points", default=350000, type=int, help="Maximum plotted points.")
    parser.add_argument(
        "--min-observations",
        default=20,
        type=int,
        help="Minimum S-Graphs observations required to plot a plane ID.",
    )
    parser.add_argument(
        "--segment-frame",
        default="auto",
        choices=("auto", "odom", "map"),
        help="Frame used for S-Graphs segments. Auto uses odom if available, otherwise map.",
    )
    parser.add_argument(
        "--title",
        default="LiDAR cloud with S-Graphs wall-plane hypotheses in odom frame",
        help="Figure title.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = read_plane_rows(args.csv)
    segments, segment_frame = build_segments(rows, args.min_observations, args.segment_frame)
    points = sample_lidar_points(
        bag_path=args.bag,
        topic=args.topic,
        max_messages=args.max_messages,
        point_stride=max(args.point_stride, 1),
        min_z=args.min_z,
        max_z=args.max_z,
        max_points=args.max_points,
    )
    title = args.title
    if segment_frame == "map":
        title = f"{title} (S-Graphs segments in map frame)"
    plot_overlay(points, segments, args.output, title, segment_frame)
    print(f"LiDAR points plotted: {len(points)}")
    print(f"S-Graphs segments plotted: {len(segments)}")
    print(f"S-Graphs segment frame: {segment_frame}")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
