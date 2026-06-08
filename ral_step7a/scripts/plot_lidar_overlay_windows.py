#!/usr/bin/env python3
"""Generate top-down LiDAR overlay snapshots at several points in a ROS 2 bag."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message

from physical_annotation_common import open_reader, point_cloud_to_xyz, topic_type


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sample multiple LiDAR windows through a bag and write one top-down overlay per window."
    )
    parser.add_argument("--dataset", required=True, help="Dataset label written in plot titles and summary CSV.")
    parser.add_argument("--bag", required=True, type=Path, help="Input ROS 2 bag directory or MCAP file.")
    parser.add_argument("--output-dir", required=True, type=Path, help="Directory for PNG overlays and summary CSV.")
    parser.add_argument("--topic", default="/velodyne/points")
    parser.add_argument("--num-windows", default=4, type=int)
    parser.add_argument("--window-messages", default=50, type=int)
    parser.add_argument("--point-stride", default=10, type=int)
    parser.add_argument("--min-z", default=-2.0, type=float)
    parser.add_argument("--max-z", default=3.0, type=float)
    parser.add_argument("--max-points-per-window", default=350000, type=int)
    parser.add_argument("--point-size", default=0.22, type=float)
    parser.add_argument("--alpha", default=0.42, type=float)
    parser.add_argument("--xlim", nargs=2, type=float, metavar=("XMIN", "XMAX"))
    parser.add_argument("--ylim", nargs=2, type=float, metavar=("YMIN", "YMAX"))
    return parser.parse_args()


def count_topic_messages(bag_path: Path, topic: str) -> int:
    reader = open_reader(bag_path, topic)
    count = 0
    while reader.has_next():
        reader.read_next()
        count += 1
    if count <= 0:
        raise RuntimeError(f"No messages found on topic {topic}")
    return count


def window_starts(total_messages: int, num_windows: int, window_messages: int) -> list[int]:
    if num_windows <= 0:
        raise ValueError("--num-windows must be positive")
    usable_span = max(0, total_messages - max(1, window_messages))
    if num_windows == 1 or usable_span == 0:
        return [0]
    starts = [round(index * usable_span / (num_windows - 1)) for index in range(num_windows)]
    return sorted(set(int(max(0, min(usable_span, start))) for start in starts))


def sample_window(
    bag_path: Path,
    topic: str,
    start_message: int,
    window_messages: int,
    point_stride: int,
    min_z: float,
    max_z: float,
    max_points: int,
) -> tuple[np.ndarray, int, int, float | None, float | None]:
    reader = open_reader(bag_path, topic)
    message_type = get_message(topic_type(reader, topic))
    clouds: list[np.ndarray] = []
    message_index = 0
    sampled_messages = 0
    first_time_sec: float | None = None
    last_time_sec: float | None = None

    while reader.has_next():
        _, data, timestamp_ns = reader.read_next()
        if message_index < start_message:
            message_index += 1
            continue
        if sampled_messages >= window_messages:
            break

        message = deserialize_message(data, message_type)
        xyz = point_cloud_to_xyz(message)
        xyz = xyz[(xyz[:, 2] >= min_z) & (xyz[:, 2] <= max_z)]
        if point_stride > 1:
            xyz = xyz[::point_stride]
        if xyz.size:
            clouds.append(xyz)
        sampled_messages += 1
        time_sec = float(timestamp_ns) * 1e-9
        first_time_sec = time_sec if first_time_sec is None else first_time_sec
        last_time_sec = time_sec
        message_index += 1

    if not clouds:
        raise RuntimeError(f"No LiDAR points sampled from {topic} at start message {start_message}")
    points = np.concatenate(clouds, axis=0)
    if len(points) > max_points:
        indices = np.linspace(0, len(points) - 1, max_points).astype(np.int64)
        points = points[indices]
    end_message = start_message + sampled_messages - 1
    return points, sampled_messages, end_message, first_time_sec, last_time_sec


def plot_window(
    points: np.ndarray,
    output_png: Path,
    dataset: str,
    window_number: int,
    total_windows: int,
    start_message: int,
    end_message: int,
    first_time_sec: float | None,
    last_time_sec: float | None,
    point_size: float,
    alpha: float,
    xlim: list[float] | None,
    ylim: list[float] | None,
) -> None:
    fig, ax = plt.subplots(figsize=(10.5, 8.0))
    scatter = ax.scatter(
        points[:, 0],
        points[:, 1],
        c=points[:, 2],
        s=point_size,
        cmap="viridis",
        alpha=alpha,
        linewidths=0,
        rasterized=True,
    )
    title = (
        f"{dataset}: LiDAR overlay window {window_number}/{total_windows} "
        f"(messages {start_message}-{end_message})"
    )
    if first_time_sec is not None and last_time_sec is not None:
        title += f"\nROS time {first_time_sec:.3f}-{last_time_sec:.3f} s"
    ax.set_title(title)
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, alpha=0.25)
    if xlim:
        ax.set_xlim(*xlim)
    if ylim:
        ax.set_ylim(*ylim)
    colorbar = fig.colorbar(scatter, ax=ax, shrink=0.82)
    colorbar.set_label("z [m]")
    fig.tight_layout()
    output_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_png, dpi=180)
    plt.close(fig)


def main() -> None:
    args = parse_args()
    total_messages = count_topic_messages(args.bag, args.topic)
    starts = window_starts(total_messages, args.num_windows, args.window_messages)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    summary_rows: list[dict[str, object]] = []
    for index, start in enumerate(starts, start=1):
        points, sampled_messages, end, first_time_sec, last_time_sec = sample_window(
            args.bag,
            args.topic,
            start,
            args.window_messages,
            args.point_stride,
            args.min_z,
            args.max_z,
            args.max_points_per_window,
        )
        output_png = args.output_dir / f"lidar_overlay_window_{index:02d}.png"
        plot_window(
            points,
            output_png,
            args.dataset,
            index,
            len(starts),
            start,
            end,
            first_time_sec,
            last_time_sec,
            args.point_size,
            args.alpha,
            args.xlim,
            args.ylim,
        )
        summary_rows.append(
            {
                "dataset": args.dataset,
                "window_index": index,
                "total_windows": len(starts),
                "topic": args.topic,
                "total_topic_messages": total_messages,
                "start_message": start,
                "end_message": end,
                "sampled_messages": sampled_messages,
                "first_time_sec": "" if first_time_sec is None else f"{first_time_sec:.9f}",
                "last_time_sec": "" if last_time_sec is None else f"{last_time_sec:.9f}",
                "points_plotted": len(points),
                "output_png": str(output_png),
            }
        )
        print(f"Wrote {output_png} ({len(points)} points, messages {start}-{end})")

    summary_csv = args.output_dir / "lidar_overlay_windows_summary.csv"
    with summary_csv.open("w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)
    print(f"Wrote {summary_csv}")


if __name__ == "__main__":
    main()
