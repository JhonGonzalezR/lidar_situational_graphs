#!/usr/bin/env python3
"""Summarize S-Graphs wall-plane observations by persistent plane ID."""

from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict
from pathlib import Path


SUMMARY_FIELDS = [
    "plane_group",
    "plane_id",
    "observation_count",
    "first_stamp",
    "last_stamp",
    "duration_s",
    "point_count_mean",
    "point_count_min",
    "point_count_max",
    "normal_angle_std_map_deg",
    "normal_angle_std_odom_deg",
    "d_map_mean",
    "d_map_std",
    "d_odom_mean",
    "d_odom_std",
    "centroid_x_odom_mean",
    "centroid_y_odom_mean",
    "centroid_z_odom_mean",
    "map_to_odom_ratio",
]


def to_float(value: str) -> float | None:
    if value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def mean(values: list[float]) -> float | str:
    if not values:
        return ""
    return sum(values) / len(values)


def std(values: list[float]) -> float | str:
    if len(values) < 2:
        return 0.0 if values else ""
    avg = sum(values) / len(values)
    return math.sqrt(sum((value - avg) ** 2 for value in values) / (len(values) - 1))


def normalize(vector: tuple[float, float, float]) -> tuple[float, float, float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm <= 0.0:
        return vector
    return tuple(value / norm for value in vector)  # type: ignore[return-value]


def angle_std_deg(normals: list[tuple[float, float, float]]) -> float | str:
    if not normals:
        return ""
    mean_normal = normalize(
        (
            sum(n[0] for n in normals),
            sum(n[1] for n in normals),
            sum(n[2] for n in normals),
        )
    )
    angles = []
    for normal in normals:
        dot = max(-1.0, min(1.0, sum(a * b for a, b in zip(normal, mean_normal))))
        angles.append(math.degrees(math.acos(abs(dot))))
    return std(angles)


def collect_normals(
    rows: list[dict[str, str]],
    prefix: str,
) -> list[tuple[float, float, float]]:
    normals = []
    for row in rows:
        nx = to_float(row[f"nx_{prefix}"])
        ny = to_float(row[f"ny_{prefix}"])
        nz = to_float(row[f"nz_{prefix}"])
        if nx is None or ny is None or nz is None:
            continue
        normals.append(normalize((nx, ny, nz)))
    return normals


def summarize(csv_path: Path, output_csv: Path) -> list[dict[str, object]]:
    with csv_path.open(newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))

    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row["plane_group"], row["plane_id"])].append(row)

    summaries = []
    for (plane_group, plane_id), group_rows in sorted(
        grouped.items(),
        key=lambda item: (item[0][0], int(item[0][1])),
    ):
        stamps = [float(row["stamp"]) for row in group_rows]
        point_counts = [float(row["point_count"]) for row in group_rows]
        d_map = [value for row in group_rows if (value := to_float(row["d_map"])) is not None]
        d_odom = [value for row in group_rows if (value := to_float(row["d_odom"])) is not None]
        cx_odom = [
            value for row in group_rows if (value := to_float(row["centroid_x_odom"])) is not None
        ]
        cy_odom = [
            value for row in group_rows if (value := to_float(row["centroid_y_odom"])) is not None
        ]
        cz_odom = [
            value for row in group_rows if (value := to_float(row["centroid_z_odom"])) is not None
        ]
        transformed = sum(row["map_to_odom_available"] == "true" for row in group_rows)

        summaries.append(
            {
                "plane_group": plane_group,
                "plane_id": plane_id,
                "observation_count": len(group_rows),
                "first_stamp": min(stamps),
                "last_stamp": max(stamps),
                "duration_s": max(stamps) - min(stamps),
                "point_count_mean": mean(point_counts),
                "point_count_min": min(point_counts),
                "point_count_max": max(point_counts),
                "normal_angle_std_map_deg": angle_std_deg(collect_normals(group_rows, "map")),
                "normal_angle_std_odom_deg": angle_std_deg(collect_normals(group_rows, "odom")),
                "d_map_mean": mean(d_map),
                "d_map_std": std(d_map),
                "d_odom_mean": mean(d_odom),
                "d_odom_std": std(d_odom),
                "centroid_x_odom_mean": mean(cx_odom),
                "centroid_y_odom_mean": mean(cy_odom),
                "centroid_z_odom_mean": mean(cz_odom),
                "map_to_odom_ratio": transformed / len(group_rows),
            }
        )

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        writer.writerows(summaries)

    return summaries


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize S-Graphs wall-plane CSV.")
    parser.add_argument("--csv", required=True, type=Path, help="Input wall-plane CSV.")
    parser.add_argument("--output", required=True, type=Path, help="Output summary CSV.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summaries = summarize(args.csv, args.output)
    print(f"Plane IDs: {len(summaries)}")
    print(f"Summary CSV: {args.output}")
    for row in sorted(summaries, key=lambda item: int(item["observation_count"]), reverse=True)[:5]:
        print(
            f"{row['plane_group']}:{row['plane_id']} "
            f"obs={row['observation_count']} "
            f"d_odom_std={row['d_odom_std']} "
            f"normal_std_deg={row['normal_angle_std_odom_deg']}"
        )


if __name__ == "__main__":
    main()
