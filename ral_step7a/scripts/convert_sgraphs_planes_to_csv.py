#!/usr/bin/env python3
"""Convert S-Graphs /s_graphs/all_map_planes messages to CSV.

This script is intended to run inside the S-Graphs Humble Docker environment,
because the host ROS environment may not have the custom S-Graphs message
definitions.

Input:
  A rosbag2 directory recorded by `record_sgraphs_topics.sh`.

Output:
  One CSV row per S-Graphs plane observation, split by x/y vertical plane group.

Frame note:
  The exported `*_map` fields are the native values published by S-Graphs.
  When `/s_graphs/odom2map` is available, the script also exports `*_odom`
  fields. S-Graphs publishes `odom2map` as a TransformStamped with
  `header.frame_id=map` and `child_frame_id=odom`, representing T_map_odom.

Plane conversion:
  For a map-frame plane n_map^T x_map + d_map = 0 and
  x_map = R_map_odom x_odom + t_map_odom:

      n_odom = R_map_odom^T n_map
      d_odom = d_map + n_map^T t_map_odom

  Centroids/support points are converted as:

      x_odom = R_map_odom^T (x_map - t_map_odom)
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from bisect import bisect_right
from typing import Iterable, NamedTuple

import rosbag2_py
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message


TOPIC = "/s_graphs/all_map_planes"
ODOM2MAP_TOPIC = "/s_graphs/odom2map"


CSV_FIELDS = [
    "stamp_sec",
    "stamp_nanosec",
    "stamp",
    "message_frame_id",
    "plane_group",
    "plane_id",
    "plane_frame_id",
    "nx_map",
    "ny_map",
    "nz_map",
    "d_map",
    "nx_odom",
    "ny_odom",
    "nz_odom",
    "d_odom",
    "point_count",
    "centroid_x_map",
    "centroid_y_map",
    "centroid_z_map",
    "centroid_x_odom",
    "centroid_y_odom",
    "centroid_z_odom",
    "extent_x_map",
    "extent_y_map",
    "extent_z_map",
    "data_source",
    "map_to_odom_available",
    "odom2map_stamp",
    "odom2map_dt",
    "odom2map_frame_id",
    "odom2map_child_frame_id",
]


class Transform(NamedTuple):
    stamp: float
    frame_id: str
    child_frame_id: str
    rotation: tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]
    translation: tuple[float, float, float]


def stamp_to_float(sec: int, nanosec: int) -> float:
    return float(sec) + float(nanosec) * 1e-9


def finite_or_empty(value: float) -> float | str:
    if value is None:
        return ""
    if isinstance(value, float) and not math.isfinite(value):
        return ""
    return value


def dot(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def mat_transpose_vec(
    matrix: tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]],
    vector: tuple[float, float, float],
) -> tuple[float, float, float]:
    return (
        matrix[0][0] * vector[0] + matrix[1][0] * vector[1] + matrix[2][0] * vector[2],
        matrix[0][1] * vector[0] + matrix[1][1] * vector[1] + matrix[2][1] * vector[2],
        matrix[0][2] * vector[0] + matrix[1][2] * vector[1] + matrix[2][2] * vector[2],
    )


def normalize(vector: tuple[float, float, float]) -> tuple[float, float, float]:
    norm = math.sqrt(dot(vector, vector))
    if norm <= 0.0:
        return vector
    return (vector[0] / norm, vector[1] / norm, vector[2] / norm)


def quaternion_to_matrix(
    x: float,
    y: float,
    z: float,
    w: float,
) -> tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]:
    norm = math.sqrt(x * x + y * y + z * z + w * w)
    if norm <= 0.0:
        return ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))

    x /= norm
    y /= norm
    z /= norm
    w /= norm

    xx = x * x
    yy = y * y
    zz = z * z
    xy = x * y
    xz = x * z
    yz = y * z
    wx = w * x
    wy = w * y
    wz = w * z

    return (
        (1.0 - 2.0 * (yy + zz), 2.0 * (xy - wz), 2.0 * (xz + wy)),
        (2.0 * (xy + wz), 1.0 - 2.0 * (xx + zz), 2.0 * (yz - wx)),
        (2.0 * (xz - wy), 2.0 * (yz + wx), 1.0 - 2.0 * (xx + yy)),
    )


def transform_point_map_to_odom(
    point_map: tuple[float, float, float],
    transform: Transform,
) -> tuple[float, float, float]:
    translated = (
        point_map[0] - transform.translation[0],
        point_map[1] - transform.translation[1],
        point_map[2] - transform.translation[2],
    )
    return mat_transpose_vec(transform.rotation, translated)


def transform_plane_map_to_odom(
    normal_map: tuple[float, float, float],
    d_map: float,
    transform: Transform,
) -> tuple[tuple[float, float, float], float]:
    normal_odom = mat_transpose_vec(transform.rotation, normal_map)
    d_odom = d_map + dot(normal_map, transform.translation)

    normal_norm = math.sqrt(dot(normal_odom, normal_odom))
    if normal_norm > 0.0:
        normal_odom = (
            normal_odom[0] / normal_norm,
            normal_odom[1] / normal_norm,
            normal_odom[2] / normal_norm,
        )
        d_odom /= normal_norm

    return normal_odom, d_odom


def summarize_points(points: Iterable[object]) -> dict[str, float | int | str]:
    pts = list(points)
    if not pts:
        return {
            "point_count": 0,
            "centroid_x_map": "",
            "centroid_y_map": "",
            "centroid_z_map": "",
            "extent_x_map": "",
            "extent_y_map": "",
            "extent_z_map": "",
        }

    xs = [float(p.x) for p in pts]
    ys = [float(p.y) for p in pts]
    zs = [float(p.z) for p in pts]

    return {
        "point_count": len(pts),
        "centroid_x_map": sum(xs) / len(xs),
        "centroid_y_map": sum(ys) / len(ys),
        "centroid_z_map": sum(zs) / len(zs),
        "extent_x_map": max(xs) - min(xs),
        "extent_y_map": max(ys) - min(ys),
        "extent_z_map": max(zs) - min(zs),
    }


def plane_to_row(
    message: object,
    plane: object,
    plane_group: str,
    transform: Transform | None,
    transform_dt: float | None,
) -> dict[str, object]:
    stamp = message.header.stamp
    point_summary = summarize_points(plane.plane_points)
    normal_map = normalize((float(plane.nx), float(plane.ny), float(plane.nz)))
    d_map = float(plane.d)

    normal_odom: tuple[float, float, float] | None = None
    d_odom: float | None = None
    centroid_odom: tuple[float, float, float] | None = None

    if transform is not None:
        normal_odom, d_odom = transform_plane_map_to_odom(
            normal_map,
            d_map,
            transform,
        )
        if point_summary["centroid_x_map"] != "":
            centroid_odom = transform_point_map_to_odom(
                (
                    float(point_summary["centroid_x_map"]),
                    float(point_summary["centroid_y_map"]),
                    float(point_summary["centroid_z_map"]),
                ),
                transform,
            )

    row: dict[str, object] = {
        "stamp_sec": int(stamp.sec),
        "stamp_nanosec": int(stamp.nanosec),
        "stamp": stamp_to_float(stamp.sec, stamp.nanosec),
        "message_frame_id": message.header.frame_id,
        "plane_group": plane_group,
        "plane_id": int(plane.id),
        "plane_frame_id": plane.header.frame_id,
        "nx_map": finite_or_empty(normal_map[0]),
        "ny_map": finite_or_empty(normal_map[1]),
        "nz_map": finite_or_empty(normal_map[2]),
        "d_map": finite_or_empty(d_map),
        "nx_odom": "" if normal_odom is None else finite_or_empty(normal_odom[0]),
        "ny_odom": "" if normal_odom is None else finite_or_empty(normal_odom[1]),
        "nz_odom": "" if normal_odom is None else finite_or_empty(normal_odom[2]),
        "d_odom": "" if d_odom is None else finite_or_empty(d_odom),
        "centroid_x_odom": "" if centroid_odom is None else finite_or_empty(centroid_odom[0]),
        "centroid_y_odom": "" if centroid_odom is None else finite_or_empty(centroid_odom[1]),
        "centroid_z_odom": "" if centroid_odom is None else finite_or_empty(centroid_odom[2]),
        "data_source": plane.data_source,
        "map_to_odom_available": "true" if transform is not None else "false",
        "odom2map_stamp": "" if transform is None else transform.stamp,
        "odom2map_dt": "" if transform_dt is None else transform_dt,
        "odom2map_frame_id": "" if transform is None else transform.frame_id,
        "odom2map_child_frame_id": "" if transform is None else transform.child_frame_id,
    }
    row.update(point_summary)
    return row


def load_transforms(
    bag_dir: Path,
    topic: str = ODOM2MAP_TOPIC,
) -> list[Transform]:
    reader = open_reader(bag_dir)
    topic_types = {
        topic_metadata.name: topic_metadata.type
        for topic_metadata in reader.get_all_topics_and_types()
    }
    if topic not in topic_types:
        return []

    msg_type = get_message(topic_types[topic])
    transforms: list[Transform] = []

    while reader.has_next():
        current_topic, data, _timestamp = reader.read_next()
        if current_topic != topic:
            continue

        message = deserialize_message(data, msg_type)
        stamp = stamp_to_float(message.header.stamp.sec, message.header.stamp.nanosec)
        q = message.transform.rotation
        t = message.transform.translation
        transforms.append(
            Transform(
                stamp=stamp,
                frame_id=message.header.frame_id,
                child_frame_id=message.child_frame_id,
                rotation=quaternion_to_matrix(float(q.x), float(q.y), float(q.z), float(q.w)),
                translation=(float(t.x), float(t.y), float(t.z)),
            )
        )

    transforms.sort(key=lambda item: item.stamp)
    return transforms


def find_transform(
    transforms: list[Transform],
    stamp: float,
    max_dt: float,
) -> tuple[Transform | None, float | None]:
    if not transforms:
        return None, None

    stamps = [item.stamp for item in transforms]
    index = bisect_right(stamps, stamp) - 1
    candidates: list[Transform] = []
    if index >= 0:
        candidates.append(transforms[index])
    if index + 1 < len(transforms):
        candidates.append(transforms[index + 1])
    if not candidates:
        return None, None

    best = min(candidates, key=lambda item: abs(item.stamp - stamp))
    dt = stamp - best.stamp
    if abs(dt) > max_dt:
        return None, dt
    return best, dt


def open_reader(bag_dir: Path) -> rosbag2_py.SequentialReader:
    storage_options = rosbag2_py.StorageOptions(uri=str(bag_dir), storage_id="sqlite3")
    converter_options = rosbag2_py.ConverterOptions(
        input_serialization_format="cdr",
        output_serialization_format="cdr",
    )
    reader = rosbag2_py.SequentialReader()
    reader.open(storage_options, converter_options)
    return reader


def convert(
    bag_dir: Path,
    output_csv: Path,
    max_transform_dt: float,
) -> tuple[int, int, int, int]:
    transforms = load_transforms(bag_dir)
    reader = open_reader(bag_dir)
    topic_types = {
        topic_metadata.name: topic_metadata.type
        for topic_metadata in reader.get_all_topics_and_types()
    }

    if TOPIC not in topic_types:
        raise RuntimeError(f"Topic {TOPIC} not found in bag {bag_dir}")

    msg_type = get_message(topic_types[TOPIC])
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    message_count = 0
    plane_row_count = 0
    transformed_row_count = 0

    with output_csv.open("w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_FIELDS)
        writer.writeheader()

        while reader.has_next():
            topic, data, _timestamp = reader.read_next()
            if topic != TOPIC:
                continue

            message = deserialize_message(data, msg_type)
            message_count += 1
            stamp = stamp_to_float(message.header.stamp.sec, message.header.stamp.nanosec)
            transform, transform_dt = find_transform(transforms, stamp, max_transform_dt)

            for plane in message.x_planes:
                writer.writerow(plane_to_row(message, plane, "x", transform, transform_dt))
                plane_row_count += 1
                transformed_row_count += 1 if transform is not None else 0

            for plane in message.y_planes:
                writer.writerow(plane_to_row(message, plane, "y", transform, transform_dt))
                plane_row_count += 1
                transformed_row_count += 1 if transform is not None else 0

    return message_count, plane_row_count, transformed_row_count, len(transforms)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert /s_graphs/all_map_planes from rosbag2 to CSV."
    )
    parser.add_argument(
        "--bag",
        required=True,
        type=Path,
        help="Path to the recorded rosbag2 directory.",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Path to the output CSV file.",
    )
    parser.add_argument(
        "--max-transform-dt",
        default=10.0,
        type=float,
        help="Maximum absolute time difference in seconds for matching /s_graphs/odom2map.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    message_count, plane_row_count, transformed_row_count, transform_count = convert(
        args.bag,
        args.output,
        args.max_transform_dt,
    )
    print(f"Converted {message_count} {TOPIC} messages")
    print(f"Wrote {plane_row_count} plane observation rows")
    print(f"Loaded {transform_count} {ODOM2MAP_TOPIC} transforms")
    print(f"Rows with odom-frame conversion: {transformed_row_count}")
    print(f"CSV: {args.output}")


if __name__ == "__main__":
    main()
