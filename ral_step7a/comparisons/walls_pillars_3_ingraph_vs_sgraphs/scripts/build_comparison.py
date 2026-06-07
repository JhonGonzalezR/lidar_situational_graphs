#!/usr/bin/env python3
"""Build a reproducible InGraph vs S-Graphs structural comparison.

The direct comparison is limited to wall hypotheses on one shared dataset.
PillarLike and PipeLike are reported as additional InGraph coverage because
S-Graphs does not expose equivalent standalone output classes.
"""

from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import linear_sum_assignment


MATCH_MAX_ANGLE_DEG = 15.0
MATCH_MAX_OFFSET_M = 1.0
MATCH_MAX_SEGMENT_GAP_M = 3.0
SGRAPHS_MIN_OBSERVATIONS = 20


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as csv_file:
        return list(csv.DictReader(csv_file))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(rows[0]) if rows else []
    with path.open("w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def to_float(value: str | None) -> float | None:
    if value in (None, "", "nan"):
        return None
    try:
        result = float(value)
    except ValueError:
        return None
    return result if math.isfinite(result) else None


def to_bool(value: str | None) -> bool:
    return str(value).strip().lower() in ("1", "true", "yes", "on")


def sample_std(values: list[float]) -> float:
    return float(np.std(values, ddof=1)) if len(values) > 1 else 0.0


def median(values: list[float]) -> float:
    return float(np.median(values)) if values else 0.0


def mean(values: list[float]) -> float:
    return float(np.mean(values)) if values else 0.0


def canonical_line(nx: float, ny: float, d: float) -> tuple[float, float, float]:
    norm = math.hypot(nx, ny)
    if norm <= 0.0:
        return (1.0, 0.0, d)
    nx, ny, d = nx / norm, ny / norm, d / norm
    if nx < 0.0 or (abs(nx) < 1e-12 and ny < 0.0):
        return (-nx, -ny, -d)
    return (nx, ny, d)


def line_angle_std(normals: list[tuple[float, float]]) -> float:
    if not normals:
        return 0.0
    mean_x = mean([normal[0] for normal in normals])
    mean_y = mean([normal[1] for normal in normals])
    norm = math.hypot(mean_x, mean_y)
    if norm <= 0.0:
        return 0.0
    mean_x, mean_y = mean_x / norm, mean_y / norm
    angles = []
    for nx, ny in normals:
        dot = max(-1.0, min(1.0, abs(nx * mean_x + ny * mean_y)))
        angles.append(math.degrees(math.acos(dot)))
    return sample_std(angles)


def group_rows(rows: list[dict[str, str]], class_key: str, id_key: str) -> dict[tuple[str, str], list[dict[str, str]]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row[class_key], row[id_key])].append(row)
    return grouped


def ingraph_hypotheses(rows: list[dict[str, str]], dataset: str) -> list[dict[str, Any]]:
    hypotheses: list[dict[str, Any]] = []
    for (anchor_class, track_id), track_rows in group_rows(rows, "anchor_class", "track_id").items():
        track_rows.sort(key=lambda row: float(row["ros_time_sec"]))
        samples = []
        for row in track_rows:
            nx = to_float(row.get("normal_odom_x"))
            ny = to_float(row.get("normal_odom_y"))
            cx = to_float(row.get("centroid_odom_x"))
            cy = to_float(row.get("centroid_odom_y"))
            if None in (nx, ny, cx, cy):
                continue
            norm = math.hypot(float(nx), float(ny))
            if norm <= 0.0:
                continue
            d = -(float(nx) / norm * float(cx) + float(ny) / norm * float(cy))
            cnx, cny, cd = canonical_line(float(nx), float(ny), d)
            length = max(
                1.0,
                abs(to_float(row.get("extent_x")) or 0.0),
                abs(to_float(row.get("extent_y")) or 0.0),
            )
            samples.append(
                {
                    "row": row,
                    "nx": cnx,
                    "ny": cny,
                    "d": cd,
                    "cx": float(cx),
                    "cy": float(cy),
                    "length": length,
                }
            )
        if not samples:
            continue
        strong_samples = [sample for sample in samples if to_bool(sample["row"].get("is_strong"))]
        representative = strong_samples[-1] if strong_samples else samples[-1]
        stamps = [float(row["ros_time_sec"]) for row in track_rows]
        supports = [
            value
            for row in track_rows
            if (value := to_float(row.get("inlier_count"))) is not None
        ]
        hypotheses.append(
            {
                "dataset": dataset,
                "model": "InGraph",
                "class": anchor_class,
                "hypothesis_id": track_id,
                "selection_rule": "ever_strong",
                "selected": bool(strong_samples),
                "observation_count": len(track_rows),
                "duration_s": max(stamps) - min(stamps),
                "support_mean": mean(supports),
                "normal_std_deg": line_angle_std([(sample["nx"], sample["ny"]) for sample in samples]),
                "offset_std_m": sample_std([sample["d"] for sample in samples]),
                "cx": representative["cx"],
                "cy": representative["cy"],
                "nx": representative["nx"],
                "ny": representative["ny"],
                "d": representative["d"],
                "length": representative["length"],
                "latest_state": track_rows[-1].get("lifecycle_state", ""),
                "ever_strong": bool(strong_samples),
            }
        )
    return hypotheses


def sgraphs_hypotheses(rows: list[dict[str, str]], dataset: str) -> list[dict[str, Any]]:
    hypotheses: list[dict[str, Any]] = []
    for (plane_group, plane_id), plane_rows in group_rows(rows, "plane_group", "plane_id").items():
        samples = []
        for row in plane_rows:
            nx = to_float(row.get("nx_odom"))
            ny = to_float(row.get("ny_odom"))
            d = to_float(row.get("d_odom"))
            cx = to_float(row.get("centroid_x_odom"))
            cy = to_float(row.get("centroid_y_odom"))
            if None in (nx, ny, d, cx, cy):
                continue
            cnx, cny, cd = canonical_line(float(nx), float(ny), float(d))
            length = max(
                1.0,
                math.hypot(
                    to_float(row.get("extent_x_map")) or 0.0,
                    to_float(row.get("extent_y_map")) or 0.0,
                ),
            )
            samples.append(
                {
                    "nx": cnx,
                    "ny": cny,
                    "d": cd,
                    "cx": float(cx),
                    "cy": float(cy),
                    "length": length,
                }
            )
        if not samples:
            continue
        stamps = [float(row["stamp"]) for row in plane_rows]
        supports = [
            value
            for row in plane_rows
            if (value := to_float(row.get("point_count"))) is not None
        ]
        mean_nx, mean_ny, mean_d = canonical_line(
            mean([sample["nx"] for sample in samples]),
            mean([sample["ny"] for sample in samples]),
            mean([sample["d"] for sample in samples]),
        )
        hypotheses.append(
            {
                "dataset": dataset,
                "model": "S-Graphs",
                "class": "wall_like",
                "hypothesis_id": f"{plane_group}:{plane_id}",
                "selection_rule": f"observations>={SGRAPHS_MIN_OBSERVATIONS}",
                "selected": len(plane_rows) >= SGRAPHS_MIN_OBSERVATIONS,
                "observation_count": len(plane_rows),
                "duration_s": max(stamps) - min(stamps),
                "support_mean": mean(supports),
                "normal_std_deg": line_angle_std([(sample["nx"], sample["ny"]) for sample in samples]),
                "offset_std_m": sample_std([sample["d"] for sample in samples]),
                "cx": mean([sample["cx"] for sample in samples]),
                "cy": mean([sample["cy"] for sample in samples]),
                "nx": mean_nx,
                "ny": mean_ny,
                "d": mean_d,
                "length": max(sample["length"] for sample in samples),
                "latest_state": "published_plane",
                "ever_strong": "",
            }
        )
    return hypotheses


def class_summary(hypotheses: list[dict[str, Any]], dataset: str, model: str) -> list[dict[str, Any]]:
    rows = []
    classes = ("wall_like", "pillar_like", "pipe_like")
    for structural_class in classes:
        class_rows = [row for row in hypotheses if row["class"] == structural_class]
        if model == "S-Graphs" and structural_class != "wall_like":
            rows.append(
                {
                    "dataset": dataset,
                    "model": model,
                    "class": structural_class,
                    "output_status": "not_exposed",
                    "total_hypotheses": "",
                    "selected_hypotheses": "",
                    "selection_rate": "",
                    "observation_rows": "",
                    "median_duration_s": "",
                }
            )
            continue
        selected = [row for row in class_rows if row["selected"]]
        rows.append(
            {
                "dataset": dataset,
                "model": model,
                "class": structural_class,
                "output_status": "exposed",
                "total_hypotheses": len(class_rows),
                "selected_hypotheses": len(selected),
                "selection_rate": len(selected) / len(class_rows) if class_rows else 0.0,
                "observation_rows": sum(int(row["observation_count"]) for row in class_rows),
                "median_duration_s": median([float(row["duration_s"]) for row in selected]),
            }
        )
    return rows


def class_metric_summary(hypotheses: list[dict[str, Any]], dataset: str, model: str) -> list[dict[str, Any]]:
    rows = []
    for structural_class in ("wall_like", "pillar_like", "pipe_like"):
        class_rows = [row for row in hypotheses if row["class"] == structural_class]
        if model == "S-Graphs" and structural_class != "wall_like":
            rows.append(
                {
                    "dataset": dataset,
                    "model": model,
                    "class": structural_class,
                    "output_status": "not_exposed",
                    "selected_hypotheses": "",
                    "median_observations": "",
                    "median_duration_s": "",
                    "median_support_points": "",
                    "median_normal_std_deg": "",
                    "median_offset_std_m": "",
                }
            )
            continue
        selected = [row for row in class_rows if row["selected"]]
        plane_normal_std = median([float(row["normal_std_deg"]) for row in selected]) if structural_class == "wall_like" else ""
        plane_offset_std = median([float(row["offset_std_m"]) for row in selected]) if structural_class == "wall_like" else ""
        rows.append(
            {
                "dataset": dataset,
                "model": model,
                "class": structural_class,
                "output_status": "exposed",
                "selected_hypotheses": len(selected),
                "median_observations": median([float(row["observation_count"]) for row in selected]),
                "median_duration_s": median([float(row["duration_s"]) for row in selected]),
                "median_support_points": median([float(row["support_mean"]) for row in selected]),
                "median_normal_std_deg": plane_normal_std,
                "median_offset_std_m": plane_offset_std,
            }
        )
    return rows


def wall_model_summary(hypotheses: list[dict[str, Any]], dataset: str, model: str) -> dict[str, Any]:
    walls = [row for row in hypotheses if row["class"] == "wall_like"]
    selected = [row for row in walls if row["selected"]]
    return {
        "dataset": dataset,
        "model": model,
        "selection_rule": selected[0]["selection_rule"] if selected else "",
        "total_wall_hypotheses": len(walls),
        "selected_wall_hypotheses": len(selected),
        "selection_rate": len(selected) / len(walls) if walls else 0.0,
        "selected_observation_rows": sum(int(row["observation_count"]) for row in selected),
        "median_observations_per_selected": median([float(row["observation_count"]) for row in selected]),
        "median_duration_s": median([float(row["duration_s"]) for row in selected]),
        "median_support_points": median([float(row["support_mean"]) for row in selected]),
        "median_normal_std_deg": median([float(row["normal_std_deg"]) for row in selected]),
        "median_offset_std_m": median([float(row["offset_std_m"]) for row in selected]),
    }


def segment_endpoints(row: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    center = np.array([float(row["cx"]), float(row["cy"])])
    direction = np.array([-float(row["ny"]), float(row["nx"])])
    half = 0.5 * float(row["length"])
    return center - half * direction, center + half * direction


def segment_gap(first: dict[str, Any], second: dict[str, Any]) -> float:
    direction = np.array([-float(first["ny"]), float(first["nx"])])
    a0, a1 = segment_endpoints(first)
    b0, b1 = segment_endpoints(second)
    interval_a = sorted([float(np.dot(a0, direction)), float(np.dot(a1, direction))])
    interval_b = sorted([float(np.dot(b0, direction)), float(np.dot(b1, direction))])
    return max(0.0, max(interval_a[0], interval_b[0]) - min(interval_a[1], interval_b[1]))


def pair_metrics(ingraph: dict[str, Any], sgraphs: dict[str, Any]) -> tuple[float, float, float, float]:
    dot = max(-1.0, min(1.0, abs(float(ingraph["nx"]) * float(sgraphs["nx"]) + float(ingraph["ny"]) * float(sgraphs["ny"]))))
    angle = math.degrees(math.acos(dot))
    offset = abs(float(ingraph["d"]) - float(sgraphs["d"]))
    gap = segment_gap(ingraph, sgraphs)
    cost = angle / MATCH_MAX_ANGLE_DEG + offset / MATCH_MAX_OFFSET_M + gap / MATCH_MAX_SEGMENT_GAP_M
    return angle, offset, gap, cost


def match_walls(ingraph_hypotheses_rows: list[dict[str, Any]], sgraphs_hypotheses_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ingraph = [row for row in ingraph_hypotheses_rows if row["class"] == "wall_like" and row["selected"]]
    sgraphs = [row for row in sgraphs_hypotheses_rows if row["class"] == "wall_like" and row["selected"]]
    costs = np.zeros((len(ingraph), len(sgraphs)))
    metrics: dict[tuple[int, int], tuple[float, float, float, float]] = {}
    for i, ingraph_row in enumerate(ingraph):
        for j, sgraphs_row in enumerate(sgraphs):
            metrics[(i, j)] = pair_metrics(ingraph_row, sgraphs_row)
            costs[i, j] = metrics[(i, j)][3]
    row_indices, column_indices = linear_sum_assignment(costs)
    matches = []
    for i, j in zip(row_indices, column_indices):
        angle, offset, gap, cost = metrics[(int(i), int(j))]
        if angle > MATCH_MAX_ANGLE_DEG or offset > MATCH_MAX_OFFSET_M or gap > MATCH_MAX_SEGMENT_GAP_M:
            continue
        ingraph_candidates = sum(
            1
            for candidate_j in range(len(sgraphs))
            if metrics[(int(i), candidate_j)][0] <= MATCH_MAX_ANGLE_DEG
            and metrics[(int(i), candidate_j)][1] <= MATCH_MAX_OFFSET_M
            and metrics[(int(i), candidate_j)][2] <= MATCH_MAX_SEGMENT_GAP_M
        )
        sgraphs_candidates = sum(
            1
            for candidate_i in range(len(ingraph))
            if metrics[(candidate_i, int(j))][0] <= MATCH_MAX_ANGLE_DEG
            and metrics[(candidate_i, int(j))][1] <= MATCH_MAX_OFFSET_M
            and metrics[(candidate_i, int(j))][2] <= MATCH_MAX_SEGMENT_GAP_M
        )
        matches.append(
            {
                "ingraph_wall_id": ingraph[int(i)]["hypothesis_id"],
                "sgraphs_wall_id": sgraphs[int(j)]["hypothesis_id"],
                "angle_difference_deg": angle,
                "plane_offset_difference_m": offset,
                "segment_gap_m": gap,
                "normalized_match_cost": cost,
                "sgraphs_candidates_for_ingraph_wall": ingraph_candidates,
                "ingraph_candidates_for_sgraphs_wall": sgraphs_candidates,
            }
        )
    return sorted(matches, key=lambda row: float(row["normalized_match_cost"]))


def ingraph_operational_summary(path: Path, dataset: str) -> dict[str, Any]:
    rows = read_csv(path)
    processing = [
        value for row in rows if (value := to_float(row.get("last_processing_ms"))) is not None
    ]
    final = rows[-1]
    return {
        "dataset": dataset,
        "model": "InGraph",
        "metric_status": "available",
        "processed_frames": final.get("total_processed_frames", ""),
        "processing_ms_median": median(processing),
        "processing_ms_p95": float(np.percentile(processing, 95)) if processing else "",
        "processing_ms_max": max(processing) if processing else "",
        "final_id_switch_rate": final.get("id_switch_rate", ""),
        "final_normal_variance_per_track": final.get("normal_variance_per_track", ""),
        "wall_observations": final.get("wall_like_total_observations", ""),
        "pillar_observations": final.get("pillar_like_total_observations", ""),
        "pipe_observations": final.get("pipe_like_total_observations", ""),
        "note": "No equivalent S-Graphs runtime metrics are present in the current artifacts.",
    }


def ingraph_association_summary(path: Path, dataset: str) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(path):
        grouped[(row.get("anchor_class", ""), row.get("decision", ""))].append(row)
    result = []
    for (anchor_class, decision), rows in sorted(grouped.items()):
        scores = [value for row in rows if (value := to_float(row.get("score"))) is not None]
        centroid_distances = [
            value for row in rows if (value := to_float(row.get("centroid_distance"))) is not None
        ]
        angles = [
            value for row in rows if (value := to_float(row.get("normal_angle_deg"))) is not None
        ]
        reasons: dict[str, int] = defaultdict(int)
        for row in rows:
            reasons[row.get("reason", "")] += 1
        main_reason = max(reasons, key=reasons.get) if reasons else ""
        result.append(
            {
                "dataset": dataset,
                "model": "InGraph",
                "class": anchor_class,
                "decision": decision,
                "rows": len(rows),
                "mean_score": mean(scores),
                "median_centroid_distance_m": median(centroid_distances),
                "median_normal_angle_deg": median(angles),
                "most_common_reason": main_reason,
                "most_common_reason_rows": reasons.get(main_reason, 0),
            }
        )
    return result


def plot_class_coverage(class_rows: list[dict[str, Any]], output: Path) -> None:
    direct = [row for row in class_rows if row["dataset"] == "walls_pillars_3"]
    classes = ["wall_like", "pillar_like", "pipe_like"]
    labels = ["WallLike", "PillarLike", "PipeLike"]
    fig, ax = plt.subplots(figsize=(9.0, 5.4))
    x = np.arange(len(classes))
    width = 0.34
    for index, model in enumerate(("InGraph", "S-Graphs")):
        values = []
        for structural_class in classes:
            row = next(item for item in direct if item["model"] == model and item["class"] == structural_class)
            values.append(float(row["selected_hypotheses"]) if row["selected_hypotheses"] != "" else 0.0)
        bars = ax.bar(x + (index - 0.5) * width, values, width, label=model)
        for bar, structural_class in zip(bars, classes):
            row = next(item for item in direct if item["model"] == model and item["class"] == structural_class)
            text = "N/A" if row["output_status"] == "not_exposed" else str(int(float(row["selected_hypotheses"])))
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5, text, ha="center", va="bottom", fontsize=9)
    ax.set_xticks(x, labels)
    ax.set_ylabel("Selected persistent hypotheses")
    ax.set_title("Structural class coverage on the matched dataset")
    ax.legend()
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=180)
    plt.close(fig)


def plot_wall_stability(hypotheses: list[dict[str, Any]], output: Path) -> None:
    selected = [row for row in hypotheses if row["class"] == "wall_like" and row["selected"] and row["dataset"] == "walls_pillars_3"]
    metrics = [
        ("observation_count", "Observation rows"),
        ("duration_s", "Duration [s]"),
        ("normal_std_deg", "Normal angular std [deg]"),
        ("offset_std_m", "Plane offset std [m]"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(10.5, 7.5))
    for ax, (key, label) in zip(axes.flat, metrics):
        values = [
            [float(row[key]) for row in selected if row["model"] == model]
            for model in ("InGraph", "S-Graphs")
        ]
        ax.boxplot(values, labels=["InGraph", "S-Graphs"], showmeans=True)
        ax.set_ylabel(label)
        ax.grid(axis="y", alpha=0.25)
    fig.suptitle("Persistence and stability of selected wall hypotheses")
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=180)
    plt.close(fig)


def draw_segment(ax: Any, row: dict[str, Any], color: str, label: str | None = None, alpha: float = 0.85) -> None:
    start, end = segment_endpoints(row)
    ax.plot([start[0], end[0]], [start[1], end[1]], color=color, linewidth=2.6, alpha=alpha, label=label)
    ax.scatter([row["cx"]], [row["cy"]], color=color, s=14, alpha=alpha)


def plot_cross_model_agreement(
    ingraph_hypotheses_rows: list[dict[str, Any]],
    sgraphs_hypotheses_rows: list[dict[str, Any]],
    matches: list[dict[str, Any]],
    output: Path,
) -> None:
    ingraph = {str(row["hypothesis_id"]): row for row in ingraph_hypotheses_rows if row["class"] == "wall_like" and row["selected"]}
    sgraphs = {str(row["hypothesis_id"]): row for row in sgraphs_hypotheses_rows if row["class"] == "wall_like" and row["selected"]}
    fig, ax = plt.subplots(figsize=(9.2, 7.4))
    first = True
    for row in ingraph.values():
        draw_segment(ax, row, "#1f77b4", "InGraph ever-strong WallLike" if first else None, 0.72)
        first = False
    first = True
    for row in sgraphs.values():
        draw_segment(ax, row, "#ff7f0e", "S-Graphs persistent plane" if first else None, 0.72)
        first = False
    for match in matches:
        left = ingraph[str(match["ingraph_wall_id"])]
        right = sgraphs[str(match["sgraphs_wall_id"])]
        ax.plot([left["cx"], right["cx"]], [left["cy"], right["cy"]], color="#555555", linestyle="--", linewidth=1.0, alpha=0.65)
    ax.set_title("Cross-model wall agreement (not ground-truth accuracy)")
    ax.set_xlabel("x_odom [m]")
    ax.set_ylabel("y_odom [m]")
    ax.axis("equal")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=180)
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ingraph-matched-tracks", required=True, type=Path)
    parser.add_argument("--ingraph-matched-metrics", required=True, type=Path)
    parser.add_argument("--ingraph-matched-association", required=True, type=Path)
    parser.add_argument("--ingraph-additional-tracks", required=True, type=Path)
    parser.add_argument("--ingraph-additional-metrics", required=True, type=Path)
    parser.add_argument("--ingraph-additional-association", required=True, type=Path)
    parser.add_argument("--sgraphs-matched-planes", required=True, type=Path)
    parser.add_argument("--sgraphs-additional-planes", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data_dir = args.output / "data"
    plot_dir = args.output / "plots"

    matched_ingraph = ingraph_hypotheses(read_csv(args.ingraph_matched_tracks), "walls_pillars_3")
    additional_ingraph = ingraph_hypotheses(read_csv(args.ingraph_additional_tracks), "unpaired_ingraph_20260603_014722")
    matched_sgraphs = sgraphs_hypotheses(read_csv(args.sgraphs_matched_planes), "walls_pillars_3")
    additional_sgraphs = sgraphs_hypotheses(read_csv(args.sgraphs_additional_planes), "unpaired_sgraphs_walls_pillars_2")
    all_hypotheses = matched_ingraph + matched_sgraphs + additional_ingraph + additional_sgraphs

    hypothesis_fields = [
        "dataset", "model", "class", "hypothesis_id", "selection_rule", "selected",
        "observation_count", "duration_s", "support_mean", "normal_std_deg", "offset_std_m",
        "cx", "cy", "nx", "ny", "d", "length", "latest_state", "ever_strong",
    ]
    write_csv(data_dir / "hypothesis_metrics.csv", all_hypotheses, hypothesis_fields)

    class_rows = []
    class_rows.extend(class_summary(matched_ingraph, "walls_pillars_3", "InGraph"))
    class_rows.extend(class_summary(matched_sgraphs, "walls_pillars_3", "S-Graphs"))
    class_rows.extend(class_summary(additional_ingraph, "unpaired_ingraph_20260603_014722", "InGraph"))
    class_rows.extend(class_summary(additional_sgraphs, "unpaired_sgraphs_walls_pillars_2", "S-Graphs"))
    write_csv(data_dir / "class_coverage.csv", class_rows)

    class_metric_rows = []
    class_metric_rows.extend(class_metric_summary(matched_ingraph, "walls_pillars_3", "InGraph"))
    class_metric_rows.extend(class_metric_summary(matched_sgraphs, "walls_pillars_3", "S-Graphs"))
    class_metric_rows.extend(class_metric_summary(additional_ingraph, "unpaired_ingraph_20260603_014722", "InGraph"))
    class_metric_rows.extend(class_metric_summary(additional_sgraphs, "unpaired_sgraphs_walls_pillars_2", "S-Graphs"))
    write_csv(data_dir / "class_metric_summary.csv", class_metric_rows)

    wall_summary_rows = [
        wall_model_summary(matched_ingraph, "walls_pillars_3", "InGraph"),
        wall_model_summary(matched_sgraphs, "walls_pillars_3", "S-Graphs"),
        wall_model_summary(additional_ingraph, "unpaired_ingraph_20260603_014722", "InGraph"),
        wall_model_summary(additional_sgraphs, "unpaired_sgraphs_walls_pillars_2", "S-Graphs"),
    ]
    write_csv(data_dir / "wall_model_summary.csv", wall_summary_rows)

    matches = match_walls(matched_ingraph, matched_sgraphs)
    write_csv(data_dir / "wall_cross_model_matches.csv", matches)

    matched_ingraph_count = sum(row["class"] == "wall_like" and row["selected"] for row in matched_ingraph)
    matched_sgraphs_count = sum(row["class"] == "wall_like" and row["selected"] for row in matched_sgraphs)
    agreement = [
        {
            "dataset": "walls_pillars_3",
            "matched_pairs": len(matches),
            "ingraph_selected_walls": matched_ingraph_count,
            "sgraphs_selected_walls": matched_sgraphs_count,
            "matched_fraction_of_ingraph": len(matches) / matched_ingraph_count if matched_ingraph_count else 0.0,
            "matched_fraction_of_sgraphs": len(matches) / matched_sgraphs_count if matched_sgraphs_count else 0.0,
            "median_angle_difference_deg": median([float(row["angle_difference_deg"]) for row in matches]),
            "median_plane_offset_difference_m": median([float(row["plane_offset_difference_m"]) for row in matches]),
            "median_segment_gap_m": median([float(row["segment_gap_m"]) for row in matches]),
            "match_max_angle_deg": MATCH_MAX_ANGLE_DEG,
            "match_max_offset_m": MATCH_MAX_OFFSET_M,
            "match_max_segment_gap_m": MATCH_MAX_SEGMENT_GAP_M,
            "interpretation": "cross_model_agreement_not_ground_truth_accuracy",
        }
    ]
    write_csv(data_dir / "wall_agreement_summary.csv", agreement)

    operational_rows = [
        ingraph_operational_summary(args.ingraph_matched_metrics, "walls_pillars_3"),
        {
            "dataset": "walls_pillars_3",
            "model": "S-Graphs",
            "metric_status": "not_available",
            "processed_frames": "",
            "processing_ms_median": "",
            "processing_ms_p95": "",
            "processing_ms_max": "",
            "final_id_switch_rate": "",
            "final_normal_variance_per_track": "",
            "wall_observations": "",
            "pillar_observations": "",
            "pipe_observations": "",
            "note": "The recorded S-Graphs artifacts do not expose equivalent runtime or ID-switch metrics.",
        },
        ingraph_operational_summary(args.ingraph_additional_metrics, "unpaired_ingraph_20260603_014722"),
    ]
    write_csv(data_dir / "operational_metrics.csv", operational_rows)

    association_rows = ingraph_association_summary(args.ingraph_matched_association, "walls_pillars_3")
    association_rows.extend(
        ingraph_association_summary(args.ingraph_additional_association, "unpaired_ingraph_20260603_014722")
    )
    write_csv(data_dir / "ingraph_association_summary.csv", association_rows)

    scope_rows = [
        {
            "item": "direct_comparison",
            "dataset_or_run": "walls_pillars_3",
            "ingraph_source": str(args.ingraph_matched_tracks),
            "sgraphs_source": str(args.sgraphs_matched_planes),
            "status": "comparable",
            "reason": "same dataset timestamps and shared odom frame",
        },
        {
            "item": "additional_ingraph_run",
            "dataset_or_run": "20260603_014722",
            "ingraph_source": str(args.ingraph_additional_tracks),
            "sgraphs_source": "",
            "status": "not_directly_comparable",
            "reason": "no matching ROS bag or S-Graphs run available",
        },
        {
            "item": "additional_sgraphs_run",
            "dataset_or_run": "walls_pillars_2",
            "ingraph_source": "",
            "sgraphs_source": str(args.sgraphs_additional_planes),
            "status": "not_directly_comparable",
            "reason": "no matching InGraph CSV run identified",
        },
        {
            "item": "truncated_input",
            "dataset_or_run": "walls_pillars",
            "ingraph_source": "",
            "sgraphs_source": "",
            "status": "blocked",
            "reason": "original rosbag is truncated and has no recoverable messages",
        },
    ]
    write_csv(data_dir / "comparison_scope.csv", scope_rows)

    plot_class_coverage(class_rows, plot_dir / "class_coverage_matched_dataset.png")
    plot_wall_stability(all_hypotheses, plot_dir / "wall_persistence_stability.png")
    plot_cross_model_agreement(matched_ingraph, matched_sgraphs, matches, plot_dir / "wall_cross_model_agreement.png")

    print(f"Selected InGraph walls: {matched_ingraph_count}")
    print(f"Selected S-Graphs walls: {matched_sgraphs_count}")
    print(f"One-to-one cross-model matches: {len(matches)}")
    print(f"Wrote comparison to {args.output}")


if __name__ == "__main__":
    main()
