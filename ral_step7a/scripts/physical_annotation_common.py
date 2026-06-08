#!/usr/bin/env python3
"""Shared geometry helpers for Step 7A physical-structure annotation metrics."""

from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import rosbag2_py
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message
from sensor_msgs_py import point_cloud2


ANNOTATION_FIELDS = [
    "dataset",
    "structure_id",
    "structure_class",
    "x0",
    "y0",
    "x1",
    "y1",
    "cx",
    "cy",
    "radius_m",
    "notes",
]

WALL_ANNOTATION_CLASSES = {"wall", "wall_like_boundary", "lidar_boundary", "mesh_boundary"}


def to_float(value: str | float | None, default: float | None = None) -> float | None:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def to_bool(value: str | bool | None) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in ("1", "true", "yes", "on")


def normalize_xy(x: float, y: float) -> tuple[float, float]:
    norm = math.hypot(x, y)
    if norm <= 1e-12:
        return (1.0, 0.0)
    return (x / norm, y / norm)


def canonical_line_from_normal(nx: float, ny: float, d: float) -> tuple[float, float, float]:
    nx, ny = normalize_xy(nx, ny)
    if nx < 0.0 or (abs(nx) < 1e-12 and ny < 0.0):
        return (-nx, -ny, -d)
    return (nx, ny, d)


def line_from_segment(x0: float, y0: float, x1: float, y1: float) -> dict[str, float]:
    dx, dy = normalize_xy(x1 - x0, y1 - y0)
    nx, ny = normalize_xy(-dy, dx)
    cx = 0.5 * (x0 + x1)
    cy = 0.5 * (y0 + y1)
    d = -(nx * cx + ny * cy)
    nx, ny, d = canonical_line_from_normal(nx, ny, d)
    return {
        "cx": cx,
        "cy": cy,
        "dx": dx,
        "dy": dy,
        "nx": nx,
        "ny": ny,
        "d": d,
        "length": math.hypot(x1 - x0, y1 - y0),
    }


def segment_endpoints(item: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    center = np.array([float(item["cx"]), float(item["cy"])])
    direction = np.array([float(item["dx"]), float(item["dy"])])
    half = 0.5 * float(item["length"])
    return center - half * direction, center + half * direction


def segment_overlap_metrics(pred: dict[str, Any], ref: dict[str, Any]) -> tuple[float, float, float]:
    ref_direction = np.array([float(ref["dx"]), float(ref["dy"])])
    pred_start, pred_end = segment_endpoints(pred)
    ref_start, ref_end = segment_endpoints(ref)
    pred_interval = sorted([float(np.dot(pred_start, ref_direction)), float(np.dot(pred_end, ref_direction))])
    ref_interval = sorted([float(np.dot(ref_start, ref_direction)), float(np.dot(ref_end, ref_direction))])
    overlap = max(0.0, min(pred_interval[1], ref_interval[1]) - max(pred_interval[0], ref_interval[0]))
    gap = max(0.0, max(pred_interval[0], ref_interval[0]) - min(pred_interval[1], ref_interval[1]))
    denom = max(1e-9, min(float(pred["length"]), float(ref["length"])))
    return overlap, overlap / denom, gap


def angle_difference_deg(a: dict[str, Any], b: dict[str, Any]) -> float:
    dot = abs(float(a["nx"]) * float(b["nx"]) + float(a["ny"]) * float(b["ny"]))
    dot = max(-1.0, min(1.0, dot))
    return math.degrees(math.acos(dot))


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


def sample_lidar_window(
    bag_path: Path,
    topic: str,
    start_message: int,
    window_messages: int,
    point_stride: int,
    min_z: float,
    max_z: float,
    max_points: int,
) -> np.ndarray:
    reader = open_reader(bag_path, topic)
    message_type = get_message(topic_type(reader, topic))
    clouds = []
    message_index = 0
    sampled_messages = 0
    while reader.has_next():
        _, data, _ = reader.read_next()
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
        message_index += 1
    if not clouds:
        raise RuntimeError(f"No LiDAR points sampled from {topic} at start message {start_message}")
    points = np.concatenate(clouds, axis=0)
    if len(points) > max_points:
        indices = np.linspace(0, len(points) - 1, max_points).astype(np.int64)
        points = points[indices]
    return points


def sample_lidar_points_from_summary(
    bag_path: Path,
    topic: str,
    summary_csv: Path,
    window_indices: list[int],
    point_stride: int,
    min_z: float,
    max_z: float,
    max_points_per_window: int,
    max_points: int,
) -> np.ndarray:
    rows = {int(row["window_index"]): row for row in read_csv_rows(summary_csv)}
    clouds = []
    for window_index in window_indices:
        if window_index not in rows:
            raise RuntimeError(f"Window {window_index} not found in {summary_csv}")
        row = rows[window_index]
        clouds.append(
            sample_lidar_window(
                bag_path,
                topic,
                int(row["start_message"]),
                int(row["sampled_messages"]),
                point_stride,
                min_z,
                max_z,
                max_points_per_window,
            )
        )
    points = np.concatenate(clouds, axis=0)
    if len(points) > max_points:
        indices = np.linspace(0, len(points) - 1, max_points).astype(np.int64)
        points = points[indices]
    return points


def parse_window_indices(value: str | None) -> list[int]:
    if not value:
        return []
    return [int(item) for item in value.replace(",", " ").split() if item.strip()]


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as csv_file:
        return list(csv.DictReader(csv_file))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def read_annotations(path: Path, dataset: str | None = None) -> list[dict[str, Any]]:
    annotations: list[dict[str, Any]] = []
    for row in read_csv_rows(path):
        if dataset and row.get("dataset") not in ("", dataset):
            continue
        cls = row.get("structure_class", "").strip().lower()
        item: dict[str, Any] = {
            "dataset": row.get("dataset", dataset or ""),
            "id": row.get("structure_id", ""),
            "class": "wall" if cls in WALL_ANNOTATION_CLASSES else cls,
            "annotation_class": cls,
            "notes": row.get("notes", ""),
        }
        if cls in WALL_ANNOTATION_CLASSES or (row.get("x0") and row.get("x1")):
            x0 = to_float(row.get("x0"))
            y0 = to_float(row.get("y0"))
            x1 = to_float(row.get("x1"))
            y1 = to_float(row.get("y1"))
            if None in (x0, y0, x1, y1):
                continue
            item.update(line_from_segment(float(x0), float(y0), float(x1), float(y1)))
            item.update({"x0": x0, "y0": y0, "x1": x1, "y1": y1})
        else:
            cx = to_float(row.get("cx"))
            cy = to_float(row.get("cy"))
            if cx is None or cy is None:
                continue
            item.update({"cx": cx, "cy": cy, "radius_m": to_float(row.get("radius_m"), 0.0) or 0.0})
        annotations.append(item)
    return annotations


def read_ingraph_predictions(
    path: Path,
    dataset: str,
    snapshot: str,
    mode: str,
    min_age: int,
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in read_csv_rows(path):
        grouped[(row["anchor_class"], row["track_id"])].append(row)
    predictions: list[dict[str, Any]] = []
    for (anchor_class, track_id), rows in grouped.items():
        rows.sort(key=lambda item: float(item["ros_time_sec"]))
        if snapshot == "latest_strong":
            candidates = [row for row in rows if to_bool(row.get("is_strong"))]
            if not candidates:
                continue
            row = candidates[-1]
        else:
            row = rows[-1]
        age = int(to_float(row.get("track_age"), 0) or 0)
        if age < min_age:
            continue
        state = row.get("lifecycle_state", "")
        is_strong = to_bool(row.get("is_strong"))
        if mode == "strong" and not is_strong:
            continue
        if mode == "confirmed" and not (state in ("confirmed", "stale") or is_strong):
            continue

        cx = to_float(row.get("centroid_odom_x"))
        cy = to_float(row.get("centroid_odom_y"))
        if cx is None or cy is None:
            continue
        item: dict[str, Any] = {
            "dataset": dataset,
            "model": "InGraph",
            "id": track_id,
            "raw_class": anchor_class,
            "state": state,
            "age": age,
            "cx": cx,
            "cy": cy,
            "is_strong": is_strong,
        }
        if anchor_class == "wall_like":
            nx = to_float(row.get("normal_odom_x"))
            ny = to_float(row.get("normal_odom_y"))
            if nx is None or ny is None:
                continue
            nx, ny = normalize_xy(float(nx), float(ny))
            dx, dy = normalize_xy(-ny, nx)
            d = -(nx * float(cx) + ny * float(cy))
            nx, ny, d = canonical_line_from_normal(nx, ny, d)
            length = max(
                1.0,
                abs(to_float(row.get("extent_x"), 1.0) or 1.0),
                abs(to_float(row.get("extent_y"), 1.0) or 1.0),
            )
            item.update({"class": "wall", "nx": nx, "ny": ny, "d": d, "dx": dx, "dy": dy, "length": length})
        elif anchor_class == "pillar_like":
            item.update({
                "class": "pillar",
                "radius_m": 0.5 * (to_float(row.get("footprint_max"), 0.0) or 0.0),
            })
        elif anchor_class == "pipe_like":
            item.update({
                "class": "pipe",
                "radius_m": to_float(row.get("fitted_radius"), 0.0) or 0.0,
                "axis_z": to_float(row.get("normal_odom_z"), 1.0) or 1.0,
            })
        else:
            continue
        predictions.append(item)
    return predictions


def read_sgraphs_wall_predictions(path: Path, dataset: str, min_observations: int) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in read_csv_rows(path):
        grouped[(row["plane_group"], row["plane_id"])].append(row)
    predictions: list[dict[str, Any]] = []
    for (plane_group, plane_id), rows in grouped.items():
        if len(rows) < min_observations:
            continue
        cx = [value for row in rows if (value := to_float(row.get("centroid_x_odom"))) is not None]
        cy = [value for row in rows if (value := to_float(row.get("centroid_y_odom"))) is not None]
        nx = [value for row in rows if (value := to_float(row.get("nx_odom"))) is not None]
        ny = [value for row in rows if (value := to_float(row.get("ny_odom"))) is not None]
        ex = [value for row in rows if (value := to_float(row.get("extent_x_map"))) is not None]
        ey = [value for row in rows if (value := to_float(row.get("extent_y_map"))) is not None]
        if not (cx and cy and nx and ny):
            continue
        mean_cx = float(np.mean(cx))
        mean_cy = float(np.mean(cy))
        mean_nx, mean_ny = normalize_xy(float(np.mean(nx)), float(np.mean(ny)))
        dx, dy = normalize_xy(-mean_ny, mean_nx)
        d = -(mean_nx * mean_cx + mean_ny * mean_cy)
        mean_nx, mean_ny, d = canonical_line_from_normal(mean_nx, mean_ny, d)
        support_lengths = [math.hypot(x_extent, y_extent) for x_extent, y_extent in zip(ex, ey)]
        predictions.append({
            "dataset": dataset,
            "model": "S-Graphs",
            "id": f"{plane_group}:{plane_id}",
            "class": "wall",
            "raw_class": "wall_like",
            "selection_rule": f"observations>={min_observations}",
            "age": len(rows),
            "cx": mean_cx,
            "cy": mean_cy,
            "nx": mean_nx,
            "ny": mean_ny,
            "d": d,
            "dx": dx,
            "dy": dy,
            "length": max(1.0, max(support_lengths) if support_lengths else 1.0),
        })
    return predictions
