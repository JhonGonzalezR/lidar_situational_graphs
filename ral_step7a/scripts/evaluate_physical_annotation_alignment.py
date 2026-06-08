#!/usr/bin/env python3
"""Evaluate InGraph/S-Graphs predictions against physical annotations."""

from __future__ import annotations

import argparse
import math
from collections import defaultdict
from pathlib import Path
from statistics import median
from typing import Any

import numpy as np

from physical_annotation_common import (
    angle_difference_deg,
    read_annotations,
    read_ingraph_predictions,
    read_sgraphs_wall_predictions,
    segment_overlap_metrics,
    write_csv,
)


PREDICTION_FIELDS = [
    "evaluation_scope",
    "dataset",
    "model",
    "structure_class",
    "prediction_id",
    "annotation_id",
    "annotation_class",
    "matched",
    "match_cost",
    "angle_error_deg",
    "offset_error_m",
    "segment_gap_m",
    "overlap_ratio",
    "xy_error_m",
    "prediction_age",
    "match_reason",
]

FRAGMENTATION_FIELDS = [
    "evaluation_scope",
    "dataset",
    "model",
    "structure_class",
    "annotation_id",
    "annotation_class",
    "nearest_predictions",
    "aligned_predictions",
    "best_prediction_id",
    "best_match_cost",
    "best_angle_error_deg",
    "best_offset_error_m",
    "best_segment_gap_m",
    "best_overlap_ratio",
    "best_xy_error_m",
]

SUMMARY_FIELDS = [
    "evaluation_scope",
    "dataset",
    "model",
    "structure_class",
    "total_predictions",
    "total_annotations",
    "aligned_predictions",
    "matched_annotations",
    "alignment_precision",
    "instance_precision",
    "physical_recall",
    "fragmentation_index_mean",
    "fragmentation_index_max",
    "median_angle_error_deg",
    "median_offset_error_m",
    "median_segment_gap_m",
    "median_overlap_ratio",
    "median_xy_error_m",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate structural predictions against physical annotations.")
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--annotations", required=True, type=Path)
    parser.add_argument("--ingraph-tracks", type=Path, help="structure_anchor_tracks.csv")
    parser.add_argument("--sgraphs-planes", type=Path, help="sgraphs_wall_planes.csv")
    parser.add_argument("--sgraphs-min-observations", default=20, type=int)
    parser.add_argument("--output-predictions", required=True, type=Path)
    parser.add_argument("--output-summary", required=True, type=Path)
    parser.add_argument("--output-fragmentation", type=Path)
    parser.add_argument(
        "--wall-annotation-scope",
        default="walllike_boundary",
        choices=("solid_wall_only", "walllike_boundary"),
        help="solid_wall_only uses only structure_class=wall; walllike_boundary also includes wall_like_boundary annotations.",
    )
    parser.add_argument(
        "--exclude-boundary-wall-predictions",
        action="store_true",
        help=(
            "Before evaluating solid walls, remove wall predictions that align with "
            "wall_like_boundary annotations under the walllike_boundary scope."
        ),
    )
    parser.add_argument("--evaluation-scope", default="", help="Label written to output CSVs.")
    parser.add_argument("--ingraph-snapshot", default="latest_strong", choices=("latest", "latest_strong"))
    parser.add_argument("--ingraph-mode", default="strong", choices=("all", "confirmed", "strong"))
    parser.add_argument("--min-age", default=1, type=int)
    parser.add_argument("--wall-max-angle-deg", default=8.0, type=float)
    parser.add_argument("--wall-max-offset-m", default=0.40, type=float)
    parser.add_argument("--wall-max-gap-m", default=1.00, type=float)
    parser.add_argument("--wall-min-overlap-ratio", default=0.25, type=float)
    parser.add_argument("--pillar-max-xy-error-m", default=0.55, type=float)
    parser.add_argument("--pipe-max-xy-error-m", default=0.35, type=float)
    return parser.parse_args()


def wall_pair(prediction: dict[str, Any], annotation: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    angle = angle_difference_deg(prediction, annotation)
    offset = abs(float(prediction["d"]) - float(annotation["d"]))
    overlap, overlap_ratio, gap = segment_overlap_metrics(prediction, annotation)
    matched = (
        angle <= args.wall_max_angle_deg
        and offset <= args.wall_max_offset_m
        and gap <= args.wall_max_gap_m
        and overlap_ratio >= args.wall_min_overlap_ratio
    )
    cost = (
        angle / max(args.wall_max_angle_deg, 1e-9)
        + offset / max(args.wall_max_offset_m, 1e-9)
        + gap / max(args.wall_max_gap_m, 1e-9)
        + max(0.0, args.wall_min_overlap_ratio - overlap_ratio) / max(args.wall_min_overlap_ratio, 1e-9)
    )
    return {
        "matched": matched,
        "match_cost": cost,
        "angle_error_deg": angle,
        "offset_error_m": offset,
        "segment_gap_m": gap,
        "overlap_ratio": overlap_ratio,
        "xy_error_m": "",
        "match_reason": "nearest_wall_aligned" if matched else "nearest_wall_gate_failed",
    }


def point_pair(prediction: dict[str, Any], annotation: dict[str, Any], max_xy_error: float) -> dict[str, Any]:
    dx = float(prediction["cx"]) - float(annotation["cx"])
    dy = float(prediction["cy"]) - float(annotation["cy"])
    dist = math.hypot(dx, dy)
    matched = dist <= max_xy_error
    return {
        "matched": matched,
        "match_cost": dist / max(max_xy_error, 1e-9),
        "angle_error_deg": "",
        "offset_error_m": "",
        "segment_gap_m": "",
        "overlap_ratio": "",
        "xy_error_m": dist,
        "match_reason": "nearest_xy_aligned" if matched else "nearest_xy_gate_failed",
    }


def best_matches(
    predictions: list[dict[str, Any]],
    annotations: list[dict[str, Any]],
    structure_class: str,
    args: argparse.Namespace,
) -> list[dict[str, Any]]:
    class_annotations = [item for item in annotations if item["class"] == structure_class]
    class_predictions = [item for item in predictions if item["class"] == structure_class]
    candidate_rows: list[dict[str, Any]] = []

    for prediction in class_predictions:
        for annotation in class_annotations:
            if structure_class == "wall":
                metrics = wall_pair(prediction, annotation, args)
            else:
                threshold = args.pillar_max_xy_error_m if structure_class == "pillar" else args.pipe_max_xy_error_m
                metrics = point_pair(prediction, annotation, threshold)
            candidate_rows.append({
                "prediction": prediction,
                "annotation": annotation,
                **metrics,
            })

    # One prediction can only claim one annotated structure. Multiple predictions
    # may match the same structure; that is measured as fragmentation.
    selected_by_prediction: dict[str, dict[str, Any]] = {}
    for candidate in sorted(candidate_rows, key=lambda item: float(item["match_cost"])):
        key = str(candidate["prediction"]["id"])
        if key not in selected_by_prediction:
            selected_by_prediction[key] = candidate

    rows: list[dict[str, Any]] = []
    for prediction in class_predictions:
        candidate = selected_by_prediction.get(str(prediction["id"]))
        if candidate is None:
            rows.append(output_row(args.dataset, prediction, structure_class, None, None))
            continue
        rows.append(output_row(args.dataset, prediction, structure_class, candidate["annotation"], candidate))
    return rows


def output_row(
    dataset: str,
    prediction: dict[str, Any],
    structure_class: str,
    annotation: dict[str, Any] | None,
    metrics: dict[str, Any] | None,
) -> dict[str, Any]:
    matched = bool(metrics and metrics["matched"])
    return {
        "evaluation_scope": "",
        "dataset": dataset,
        "model": prediction.get("model", ""),
        "structure_class": structure_class,
        "prediction_id": prediction.get("id", ""),
        "annotation_id": annotation.get("id", "") if annotation else "",
        "annotation_class": annotation.get("annotation_class", "") if annotation else "",
        "matched": str(matched).lower(),
        "match_cost": fmt(metrics.get("match_cost")) if metrics else "",
        "angle_error_deg": fmt(metrics.get("angle_error_deg")) if metrics else "",
        "offset_error_m": fmt(metrics.get("offset_error_m")) if metrics else "",
        "segment_gap_m": fmt(metrics.get("segment_gap_m")) if metrics else "",
        "overlap_ratio": fmt(metrics.get("overlap_ratio")) if metrics else "",
        "xy_error_m": fmt(metrics.get("xy_error_m")) if metrics else "",
        "prediction_age": prediction.get("age", ""),
        "match_reason": metrics.get("match_reason", "no_annotation_candidate") if metrics else "no_annotation_candidate",
    }


def fmt(value: Any) -> str:
    if value in ("", None):
        return ""
    try:
        return f"{float(value):.6f}"
    except (TypeError, ValueError):
        return str(value)


def finite_values(rows: list[dict[str, Any]], key: str) -> list[float]:
    values = []
    for row in rows:
        if row.get("matched") != "true":
            continue
        value = row.get(key, "")
        if value == "":
            continue
        values.append(float(value))
    return values


def summarize(rows: list[dict[str, Any]], annotations: list[dict[str, Any]], dataset: str, evaluation_scope: str) -> list[dict[str, Any]]:
    summary_rows: list[dict[str, Any]] = []
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["model"], row["structure_class"])].append(row)

    for model in sorted({row["model"] for row in rows}):
        for structure_class in ("wall", "pillar", "pipe"):
            class_rows = grouped.get((model, structure_class), [])
            if not class_rows:
                continue
            class_annotations = [item for item in annotations if item["class"] == structure_class]
            aligned_rows = [row for row in class_rows if row["matched"] == "true"]
            matched_annotations = {row["annotation_id"] for row in aligned_rows if row["annotation_id"]}
            per_annotation = defaultdict(int)
            for row in aligned_rows:
                per_annotation[row["annotation_id"]] += 1
            alignment_precision = len(aligned_rows) / len(class_rows) if class_rows else 0.0
            instance_precision = len(matched_annotations) / len(class_rows) if class_rows else 0.0
            physical_recall = len(matched_annotations) / len(class_annotations) if class_annotations else 0.0
            frag_values = list(per_annotation.values())
            summary_rows.append({
                "evaluation_scope": evaluation_scope,
                "dataset": dataset,
                "model": model,
                "structure_class": structure_class,
                "total_predictions": len(class_rows),
                "total_annotations": len(class_annotations),
                "aligned_predictions": len(aligned_rows),
                "matched_annotations": len(matched_annotations),
                "alignment_precision": f"{alignment_precision:.6f}",
                "instance_precision": f"{instance_precision:.6f}",
                "physical_recall": f"{physical_recall:.6f}",
                "fragmentation_index_mean": f"{float(np.mean(frag_values)):.6f}" if frag_values else "",
                "fragmentation_index_max": max(frag_values) if frag_values else "",
                "median_angle_error_deg": median_or_blank(finite_values(class_rows, "angle_error_deg")),
                "median_offset_error_m": median_or_blank(finite_values(class_rows, "offset_error_m")),
                "median_segment_gap_m": median_or_blank(finite_values(class_rows, "segment_gap_m")),
                "median_overlap_ratio": median_or_blank(finite_values(class_rows, "overlap_ratio")),
                "median_xy_error_m": median_or_blank(finite_values(class_rows, "xy_error_m")),
            })
    return summary_rows


def summarize_fragmentation(
    rows: list[dict[str, Any]],
    annotations: list[dict[str, Any]],
    dataset: str,
    evaluation_scope: str,
) -> list[dict[str, Any]]:
    output_rows: list[dict[str, Any]] = []
    models = sorted({row["model"] for row in rows})
    for model in models:
        for structure_class in ("wall", "pillar", "pipe"):
            class_annotations = [item for item in annotations if item["class"] == structure_class]
            class_rows = [row for row in rows if row["model"] == model and row["structure_class"] == structure_class]
            if not class_rows and not class_annotations:
                continue
            rows_by_annotation: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for row in class_rows:
                if row.get("annotation_id"):
                    rows_by_annotation[row["annotation_id"]].append(row)
            for annotation in class_annotations:
                annotation_rows = rows_by_annotation.get(annotation["id"], [])
                aligned_rows = [row for row in annotation_rows if row["matched"] == "true"]
                best_row = min(
                    annotation_rows,
                    key=lambda item: float(item["match_cost"]) if item.get("match_cost") else float("inf"),
                    default=None,
                )
                output_rows.append({
                    "evaluation_scope": evaluation_scope,
                    "dataset": dataset,
                    "model": model,
                    "structure_class": structure_class,
                    "annotation_id": annotation["id"],
                    "annotation_class": annotation.get("annotation_class", ""),
                    "nearest_predictions": len(annotation_rows),
                    "aligned_predictions": len(aligned_rows),
                    "best_prediction_id": best_row.get("prediction_id", "") if best_row else "",
                    "best_match_cost": best_row.get("match_cost", "") if best_row else "",
                    "best_angle_error_deg": best_row.get("angle_error_deg", "") if best_row else "",
                    "best_offset_error_m": best_row.get("offset_error_m", "") if best_row else "",
                    "best_segment_gap_m": best_row.get("segment_gap_m", "") if best_row else "",
                    "best_overlap_ratio": best_row.get("overlap_ratio", "") if best_row else "",
                    "best_xy_error_m": best_row.get("xy_error_m", "") if best_row else "",
                })
    return output_rows


def filter_annotations_for_scope(annotations: list[dict[str, Any]], wall_annotation_scope: str) -> list[dict[str, Any]]:
    if wall_annotation_scope == "walllike_boundary":
        return annotations
    filtered = []
    for annotation in annotations:
        if annotation["class"] != "wall":
            filtered.append(annotation)
            continue
        if annotation.get("annotation_class") == "wall":
            filtered.append(annotation)
    return filtered


def boundary_aligned_wall_prediction_keys(
    predictions: list[dict[str, Any]],
    annotations: list[dict[str, Any]],
    args: argparse.Namespace,
) -> set[tuple[str, str]]:
    """Find wall predictions already explained by LiDAR-observable boundaries."""
    keys: set[tuple[str, str]] = set()
    wall_rows: list[dict[str, Any]] = []
    for model in sorted({prediction["model"] for prediction in predictions}):
        model_predictions = [prediction for prediction in predictions if prediction["model"] == model]
        wall_rows.extend(best_matches(model_predictions, annotations, "wall", args))
    for row in wall_rows:
        if row["matched"] != "true":
            continue
        if row.get("annotation_class") == "wall":
            continue
        keys.add((row["model"], row["prediction_id"]))
    return keys


def median_or_blank(values: list[float]) -> str:
    return f"{median(values):.6f}" if values else ""


def main() -> None:
    args = parse_args()
    evaluation_scope = args.evaluation_scope or args.wall_annotation_scope
    all_annotations = read_annotations(args.annotations, args.dataset)
    annotations = filter_annotations_for_scope(all_annotations, args.wall_annotation_scope)
    predictions: list[dict[str, Any]] = []
    if args.ingraph_tracks:
        predictions.extend(
            read_ingraph_predictions(
                args.ingraph_tracks,
                args.dataset,
                args.ingraph_snapshot,
                args.ingraph_mode,
                args.min_age,
            )
        )
    if args.sgraphs_planes:
        predictions.extend(read_sgraphs_wall_predictions(args.sgraphs_planes, args.dataset, args.sgraphs_min_observations))

    if args.exclude_boundary_wall_predictions:
        boundary_keys = boundary_aligned_wall_prediction_keys(predictions, all_annotations, args)
        predictions = [
            prediction for prediction in predictions
            if not (
                prediction.get("class") == "wall"
                and (prediction.get("model", ""), str(prediction.get("id", ""))) in boundary_keys
            )
        ]

    output_rows: list[dict[str, Any]] = []
    for model in sorted({prediction["model"] for prediction in predictions}):
        model_predictions = [prediction for prediction in predictions if prediction["model"] == model]
        for structure_class in ("wall", "pillar", "pipe"):
            output_rows.extend(best_matches(model_predictions, annotations, structure_class, args))
    for row in output_rows:
        row["evaluation_scope"] = evaluation_scope

    summary_rows = summarize(output_rows, annotations, args.dataset, evaluation_scope)
    write_csv(args.output_predictions, output_rows, PREDICTION_FIELDS)
    write_csv(args.output_summary, summary_rows, SUMMARY_FIELDS)
    if args.output_fragmentation:
        write_csv(args.output_fragmentation, summarize_fragmentation(output_rows, annotations, args.dataset, evaluation_scope), FRAGMENTATION_FIELDS)
        print(f"Wrote {args.output_fragmentation}")
    print(f"Wrote {args.output_predictions}")
    print(f"Wrote {args.output_summary}")


if __name__ == "__main__":
    main()
