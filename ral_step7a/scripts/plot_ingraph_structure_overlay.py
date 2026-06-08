#!/usr/bin/env python3
"""Plot InGraph structural anchors on the input LiDAR cloud.

The script reads `structure_anchor_tracks.csv` and renders top-down structural
anchors in `odom`. It can use either the latest row of each track or the latest
row in which a track was marked strong.
"""

from __future__ import annotations

import argparse
import csv
import math
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import rosbag2_py
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message
from sensor_msgs_py import point_cloud2

from physical_annotation_common import parse_window_indices, sample_lidar_points_from_summary


def to_float(value: str, default: float | None = None) -> float | None:
    if value == "":
        return default
    try:
        return float(value)
    except ValueError:
        return default


def to_bool(value: str) -> bool:
    return value.strip().lower() in ("1", "true", "yes", "on")


def normalize_xy(x: float, y: float) -> tuple[float, float]:
    norm = math.hypot(x, y)
    if norm <= 0.0:
        return (1.0, 0.0)
    return (x / norm, y / norm)


def read_track_groups(path: Path) -> dict[tuple[str, str], list[dict[str, str]]]:
    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    with path.open(newline="") as csv_file:
        for row in csv.DictReader(csv_file):
            key = (row["anchor_class"], row["track_id"])
            groups[key].append(row)
    for rows in groups.values():
        rows.sort(key=lambda item: float(item["ros_time_sec"]))
    return groups


def select_tracks(
    groups: dict[tuple[str, str], list[dict[str, str]]],
    snapshot: str,
) -> dict[tuple[str, str], dict[str, str]]:
    selected: dict[tuple[str, str], dict[str, str]] = {}
    for key, rows in groups.items():
        if snapshot == "latest":
            selected[key] = rows[-1]
        elif snapshot == "latest_strong":
            strong_rows = [row for row in rows if to_bool(row.get("is_strong", ""))]
            if strong_rows:
                selected[key] = strong_rows[-1]
        else:
            raise ValueError(f"Unsupported snapshot: {snapshot}")
    return selected


def include_track(row: dict[str, str], mode: str, min_age: int) -> bool:
    age = int(to_float(row.get("track_age", ""), 0) or 0)
    if age < min_age:
        return False
    state = row.get("lifecycle_state", "")
    if mode == "all":
        return True
    if mode == "tracked":
        return state in ("weak_tracked", "confirmed", "stale") or to_bool(row.get("is_strong", ""))
    if mode == "confirmed":
        return state in ("confirmed", "stale") or to_bool(row.get("is_strong", ""))
    if mode == "strong":
        return to_bool(row.get("is_strong", ""))
    raise ValueError(f"Unsupported mode: {mode}")


def build_wall_segments(
    tracks: dict[tuple[str, str], dict[str, str]],
    mode: str,
    min_age: int,
    classes: set[str],
) -> list[dict[str, float | str | int | bool]]:
    segments = []
    for (anchor_class, track_id), row in tracks.items():
        if anchor_class != "wall_like" or anchor_class not in classes or not include_track(row, mode, min_age):
            continue
        cx = to_float(row["centroid_odom_x"])
        cy = to_float(row["centroid_odom_y"])
        nx = to_float(row["normal_odom_x"])
        ny = to_float(row["normal_odom_y"])
        if cx is None or cy is None or nx is None or ny is None:
            continue

        normal_x, normal_y = normalize_xy(nx, ny)
        direction_x, direction_y = normalize_xy(-normal_y, normal_x)
        extent_x = abs(to_float(row.get("extent_x", ""), 1.0) or 1.0)
        extent_y = abs(to_float(row.get("extent_y", ""), 1.0) or 1.0)
        length = max(1.0, extent_x, extent_y)

        segments.append(
            {
                "track_id": track_id,
                "state": row.get("lifecycle_state", ""),
                "strong": to_bool(row.get("is_strong", "")),
                "age": int(to_float(row.get("track_age", ""), 0) or 0),
                "inliers": int(to_float(row.get("inlier_count", ""), 0) or 0),
                "cx": cx,
                "cy": cy,
                "dx": direction_x,
                "dy": direction_y,
                "length": length,
            }
        )
    return sorted(segments, key=lambda item: (bool(item["strong"]), int(item["age"]), int(item["inliers"])), reverse=True)


def build_point_anchors(
    tracks: dict[tuple[str, str], dict[str, str]],
    anchor_class: str,
    mode: str,
    min_age: int,
    classes: set[str],
) -> list[dict[str, float | str | int | bool]]:
    anchors = []
    for (cls, track_id), row in tracks.items():
        if cls != anchor_class or anchor_class not in classes or not include_track(row, mode, min_age):
            continue
        cx = to_float(row["centroid_odom_x"])
        cy = to_float(row["centroid_odom_y"])
        if cx is None or cy is None:
            continue
        anchors.append(
            {
                "track_id": track_id,
                "state": row.get("lifecycle_state", ""),
                "strong": to_bool(row.get("is_strong", "")),
                "age": int(to_float(row.get("track_age", ""), 0) or 0),
                "cx": cx,
                "cy": cy,
            }
        )
    return sorted(anchors, key=lambda item: (bool(item["strong"]), int(item["age"])), reverse=True)


def open_reader(bag_path: Path, topic: str) -> rosbag2_py.SequentialReader:
    storage_id = "mcap" if bag_path.is_file() and bag_path.suffix == ".mcap" else "sqlite3"
    reader = rosbag2_py.SequentialReader()
    reader.open(
        rosbag2_py.StorageOptions(uri=str(bag_path), storage_id=storage_id),
        rosbag2_py.ConverterOptions("cdr", "cdr"),
    )
    reader.set_filter(rosbag2_py.StorageFilter(topics=[topic]))
    return reader


def topic_type(reader: rosbag2_py.SequentialReader, topic: str) -> str:
    for item in reader.get_all_topics_and_types():
        if item.name == topic:
            return item.type
    raise RuntimeError(f"Topic not found in bag: {topic}")


def point_cloud_to_xyz(message: object) -> np.ndarray:
    points = point_cloud2.read_points_numpy(message, field_names=("x", "y", "z"), skip_nans=True)
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
    count = 0
    while reader.has_next() and count < max_messages:
        _, data, _ = reader.read_next()
        message = deserialize_message(data, message_type)
        xyz = point_cloud_to_xyz(message)
        xyz = xyz[(xyz[:, 2] >= min_z) & (xyz[:, 2] <= max_z)]
        if point_stride > 1:
            xyz = xyz[::point_stride]
        if xyz.size:
            clouds.append(xyz)
        count += 1
    if not clouds:
        raise RuntimeError(f"No LiDAR points sampled from {topic}")
    points = np.concatenate(clouds, axis=0)
    if len(points) > max_points:
        indices = np.linspace(0, len(points) - 1, max_points).astype(np.int64)
        points = points[indices]
    return points


def plot_scene(
    points: np.ndarray | None,
    wall_segments: list[dict[str, float | str | int | bool]],
    pillars: list[dict[str, float | str | int | bool]],
    pipes: list[dict[str, float | str | int | bool]],
    output: Path,
    title: str,
    xlim: tuple[float, float] | None,
    ylim: tuple[float, float] | None,
    paper: bool,
    show_ids: bool,
) -> None:
    fig, ax = plt.subplots(figsize=(9.4, 7.2))
    if points is not None:
        scatter = ax.scatter(
            points[:, 0],
            points[:, 1],
            c=points[:, 2],
            s=0.22,
            cmap="viridis",
            alpha=0.38,
            linewidths=0,
            rasterized=True,
        )
        if not paper:
            colorbar = fig.colorbar(scatter, ax=ax, fraction=0.035, pad=0.02)
            colorbar.set_label("z [m]")

    max_age = max((int(segment["age"]) for segment in wall_segments), default=1)
    for segment in wall_segments:
        cx = float(segment["cx"])
        cy = float(segment["cy"])
        dx = float(segment["dx"])
        dy = float(segment["dy"])
        half = 0.5 * float(segment["length"])
        linewidth = 2.2 + 4.0 * min(int(segment["age"]) / max(max_age, 1), 1.0)
        alpha = 0.95 if bool(segment["strong"]) else 0.55
        ax.plot([cx - half * dx, cx + half * dx], [cy - half * dy, cy + half * dy], linewidth=linewidth, alpha=alpha)
        if show_ids:
            ax.scatter([cx], [cy], s=18, color="black", alpha=0.75)
            label = f"W:{segment['track_id']}"
            if bool(segment["strong"]):
                label += "*"
            ax.text(cx, cy, label, fontsize=7, ha="left", va="bottom")

    if pillars:
        ax.scatter([float(a["cx"]) for a in pillars], [float(a["cy"]) for a in pillars], marker="s", s=72, color="#d62728", alpha=0.9, label="PillarLike")
    if pipes:
        ax.scatter([float(a["cx"]) for a in pipes], [float(a["cy"]) for a in pipes], marker="x", s=54, color="#111111", alpha=0.85, label="PipeLike")
    if (pillars or pipes) and not paper:
        ax.legend(loc="best")

    ax.set_title(title, fontsize=15)
    if xlim:
        ax.set_xlim(*xlim)
    if ylim:
        ax.set_ylim(*ylim)
    ax.set_aspect("equal", adjustable="box")
    if paper:
        ax.axis("off")
    else:
        ax.set_xlabel("x_odom [m]")
        ax.set_ylabel("y_odom [m]")
        ax.grid(True, alpha=0.25)
    fig.tight_layout(pad=0.15)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=180)
    plt.close(fig)


def write_summary(
    groups: dict[tuple[str, str], list[dict[str, str]]],
    tracks: dict[tuple[str, str], dict[str, str]],
    wall_segments: list[dict[str, float | str | int | bool]],
    pillars: list[dict[str, float | str | int | bool]],
    pipes: list[dict[str, float | str | int | bool]],
    output: Path,
    mode: str,
    min_age: int,
    snapshot: str,
    classes: set[str],
) -> None:
    class_counts = Counter(cls for cls, _ in tracks if cls in classes)
    state_counts: dict[str, Counter[str]] = defaultdict(Counter)
    strong_counts = Counter()
    for (cls, _), row in tracks.items():
        if cls not in classes:
            continue
        state_counts[cls][row.get("lifecycle_state", "")] += 1
        if to_bool(row.get("is_strong", "")):
            strong_counts[cls] += 1
    ever_strong_counts = Counter()
    for (cls, _), rows in groups.items():
        if cls not in classes:
            continue
        if any(to_bool(row.get("is_strong", "")) for row in rows):
            ever_strong_counts[cls] += 1
    with output.open("w") as f:
        f.write("# InGraph Step 7A visual summary\n\n")
        f.write(f"filter_mode: {mode}\n\n")
        f.write(f"min_age: {min_age}\n\n")
        f.write(f"snapshot: {snapshot}\n\n")
        f.write(f"classes: {', '.join(sorted(classes))}\n\n")
        f.write("## Selected Track Counts\n\n")
        for cls in sorted(class_counts):
            f.write(
                f"- {cls}: ids={class_counts[cls]}, "
                f"selected_strong_ids={strong_counts[cls]}, "
                f"ever_strong_ids={ever_strong_counts[cls]}, "
                f"states={dict(state_counts[cls])}\n"
            )
        f.write("\n## Plotted Anchors\n\n")
        f.write(f"- WallLike segments: {len(wall_segments)}\n")
        f.write(f"- PillarLike markers: {len(pillars)}\n")
        f.write(f"- PipeLike markers: {len(pipes)}\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot InGraph structural anchors.")
    parser.add_argument("--tracks", required=True, type=Path, help="structure_anchor_tracks.csv")
    parser.add_argument("--output", required=True, type=Path, help="Output PNG.")
    parser.add_argument("--summary", type=Path, help="Optional Markdown summary.")
    parser.add_argument("--bag", type=Path, help="Input ROS 2 bag directory for LiDAR overlay.")
    parser.add_argument("--topic", default="/velodyne/points", help="PointCloud2 topic.")
    parser.add_argument("--mode", default="confirmed", choices=("all", "tracked", "confirmed", "strong"))
    parser.add_argument("--snapshot", default="latest", choices=("latest", "latest_strong"))
    parser.add_argument(
        "--classes",
        default="wall_like,pillar_like,pipe_like",
        help="Comma-separated classes to plot: wall_like,pillar_like,pipe_like.",
    )
    parser.add_argument("--min-age", default=1, type=int)
    parser.add_argument("--hide-non-wall", action="store_true")
    parser.add_argument("--max-messages", default=80, type=int)
    parser.add_argument("--point-stride", default=10, type=int)
    parser.add_argument("--min-z", default=-2.0, type=float)
    parser.add_argument("--max-z", default=3.0, type=float)
    parser.add_argument("--max-points", default=450000, type=int)
    parser.add_argument("--overlay-summary", type=Path, help="Optional lidar_overlay_windows_summary.csv for fused overlays.")
    parser.add_argument("--overlay-windows", default="", help="Window indices to fuse, e.g. '1 2 3' or '1,2,3'.")
    parser.add_argument("--max-points-per-window", default=250000, type=int)
    parser.add_argument("--title", default="")
    parser.add_argument("--xlim", nargs=2, type=float, metavar=("XMIN", "XMAX"))
    parser.add_argument("--ylim", nargs=2, type=float, metavar=("YMIN", "YMAX"))
    parser.add_argument("--paper", action="store_true", help="Hide axes, grid, and colorbar for article figures.")
    parser.add_argument("--show-ids", action="store_true", help="Show track IDs next to anchors.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    groups = read_track_groups(args.tracks)
    tracks = select_tracks(groups, args.snapshot)
    classes = {item.strip() for item in args.classes.split(",") if item.strip()}
    if args.hide_non_wall:
        classes = {"wall_like"}
    unknown_classes = classes - {"wall_like", "pillar_like", "pipe_like"}
    if unknown_classes:
        raise ValueError(f"Unsupported classes: {sorted(unknown_classes)}")
    walls = build_wall_segments(tracks, args.mode, args.min_age, classes)
    pillars = build_point_anchors(tracks, "pillar_like", args.mode, args.min_age, classes)
    pipes = build_point_anchors(tracks, "pipe_like", args.mode, args.min_age, classes)
    points = None
    if args.bag:
        overlay_windows = parse_window_indices(args.overlay_windows)
        if args.overlay_summary and overlay_windows:
            points = sample_lidar_points_from_summary(
                args.bag,
                args.topic,
                args.overlay_summary,
                overlay_windows,
                max(args.point_stride, 1),
                args.min_z,
                args.max_z,
                args.max_points_per_window,
                args.max_points,
            )
        else:
            points = sample_lidar_points(args.bag, args.topic, args.max_messages, max(args.point_stride, 1), args.min_z, args.max_z, args.max_points)
    title = args.title
    if not title:
        class_label = " + ".join(
            label
            for cls, label in (
                ("wall_like", "WallLike"),
                ("pillar_like", "PillarLike"),
                ("pipe_like", "PipeLike"),
            )
            if cls in classes
        )
        mode_label = "ever-strong" if args.snapshot == "latest_strong" else args.mode
        title = f"InGraph {mode_label} {class_label}"
    plot_scene(
        points,
        walls,
        pillars,
        pipes,
        args.output,
        title,
        tuple(args.xlim) if args.xlim else None,
        tuple(args.ylim) if args.ylim else None,
        args.paper,
        args.show_ids,
    )
    if args.summary:
        write_summary(groups, tracks, walls, pillars, pipes, args.summary, args.mode, args.min_age, args.snapshot, classes)
    print(f"WallLike plotted: {len(walls)}")
    print(f"PillarLike plotted: {len(pillars)}")
    print(f"PipeLike plotted: {len(pipes)}")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
