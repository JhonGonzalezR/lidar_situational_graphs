#!/usr/bin/env python3
"""Summarize physical-annotation precision metrics for the RA-L results folder."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from physical_annotation_common import read_annotations, read_csv_rows, segment_endpoints, write_csv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize physical annotation alignment metrics.")
    parser.add_argument("--step7a-root", type=Path, default=Path("ral_step7a"))
    parser.add_argument("--output-dir", type=Path, default=Path("ral_step7a/results"))
    return parser.parse_args()


def to_float(value: str | float | None, default: float = 0.0) -> float:
    if value in ("", None):
        return default
    return float(value)


def copy_rows_with_source(path: Path, source: str) -> list[dict[str, Any]]:
    rows = read_csv_rows(path)
    for row in rows:
        row["source_file"] = str(path)
        row["source_dataset"] = source
    return rows


def point_segment_distance(px: float, py: float, segment: dict[str, Any]) -> float:
    start, end = segment_endpoints(segment)
    point = np.array([px, py], dtype=float)
    vector = end - start
    denom = float(np.dot(vector, vector))
    if denom <= 1e-12:
        return float(np.linalg.norm(point - start))
    t = float(np.dot(point - start, vector) / denom)
    t = max(0.0, min(1.0, t))
    closest = start + t * vector
    return float(np.linalg.norm(point - closest))


def build_precision_plot(summary_rows: list[dict[str, Any]], output: Path) -> None:
    filtered = [
        row for row in summary_rows
        if row["model"] in ("InGraph", "S-Graphs") and row["structure_class"] in ("wall", "pillar", "pipe")
    ]
    labels = [
        f"{row['dataset']}\n{row.get('evaluation_scope', '')}\n{row['model']}\n{row['structure_class']}"
        for row in filtered
    ]
    alignment = [to_float(row["alignment_precision"]) for row in filtered]
    instance = [to_float(row["instance_precision"]) for row in filtered]
    recall = [to_float(row["physical_recall"]) for row in filtered]

    x = np.arange(len(labels))
    width = 0.26
    fig, ax = plt.subplots(figsize=(max(10.5, 0.75 * len(labels)), 5.6))
    ax.bar(x - width, alignment, width, label="alignment precision")
    ax.bar(x, instance, width, label="instance precision")
    ax.bar(x + width, recall, width, label="physical recall")
    ax.set_ylim(0.0, 1.05)
    ax.set_ylabel("score")
    ax.set_title("Physical annotation metrics by frontend and structural class")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(loc="upper right")
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=180)
    plt.close(fig)


def build_pillar_proximity(
    annotations_path: Path,
    fragmentation_rows: list[dict[str, Any]],
    output_csv: Path,
    output_png: Path,
) -> list[dict[str, Any]]:
    annotations = read_annotations(annotations_path, "walls_pillars_3")
    walls = [item for item in annotations if item["class"] == "wall"]
    pillars = [item for item in annotations if item["class"] == "pillar"]
    aligned_by_pillar = {
        row["annotation_id"]: int(row["aligned_predictions"])
        for row in fragmentation_rows
        if row["dataset"] == "walls_pillars_3"
        and row["model"] == "InGraph"
        and row["structure_class"] == "pillar"
    }
    nearest_by_pillar = {
        row["annotation_id"]: int(row["nearest_predictions"])
        for row in fragmentation_rows
        if row["dataset"] == "walls_pillars_3"
        and row["model"] == "InGraph"
        and row["structure_class"] == "pillar"
    }
    rows: list[dict[str, Any]] = []
    for pillar in pillars:
        nearest_wall_distance = min(
            (point_segment_distance(float(pillar["cx"]), float(pillar["cy"]), wall) for wall in walls),
            default=float("nan"),
        )
        aligned = aligned_by_pillar.get(pillar["id"], 0)
        rows.append({
            "dataset": "walls_pillars_3",
            "annotation_id": pillar["id"],
            "cx": f"{float(pillar['cx']):.6f}",
            "cy": f"{float(pillar['cy']):.6f}",
            "nearest_wall_distance_m": f"{nearest_wall_distance:.6f}",
            "nearest_predictions": nearest_by_pillar.get(pillar["id"], 0),
            "aligned_predictions": aligned,
            "detected": str(aligned > 0).lower(),
            "proximity_bin": "near_or_embedded_wall" if nearest_wall_distance <= 0.75 else "open_or_separated",
        })
    write_csv(
        output_csv,
        rows,
        [
            "dataset",
            "annotation_id",
            "cx",
            "cy",
            "nearest_wall_distance_m",
            "nearest_predictions",
            "aligned_predictions",
            "detected",
            "proximity_bin",
        ],
    )

    if rows:
        distances = [to_float(row["nearest_wall_distance_m"]) for row in rows]
        detected = [row["detected"] == "true" for row in rows]
        colors = ["tab:green" if item else "tab:red" for item in detected]
        fig, ax = plt.subplots(figsize=(9.5, 4.8))
        ax.scatter(range(len(rows)), distances, c=colors, s=72, edgecolor="black", linewidth=0.5)
        ax.axhline(0.75, color="tab:orange", linestyle="--", linewidth=1.6, label="near-wall threshold: 0.75 m")
        ax.set_xticks(range(len(rows)))
        ax.set_xticklabels([row["annotation_id"] for row in rows], rotation=45, ha="right")
        ax.set_ylabel("distance to nearest annotated wall [m]")
        ax.set_title("Pillar GT proximity to walls vs InGraph aligned detections")
        ax.grid(axis="y", alpha=0.25)
        ax.legend(loc="upper right")
        fig.tight_layout()
        output_png.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_png, dpi=180)
        plt.close(fig)
    return rows


def write_markdown(
    output: Path,
    summary_rows: list[dict[str, Any]],
    fragmentation_rows: list[dict[str, Any]],
    pillar_rows: list[dict[str, Any]],
) -> None:
    def pct(value: str) -> str:
        return f"{100.0 * to_float(value):.1f}%"

    lines = [
        "# Physical Annotation Precision Metrics",
        "",
        "These metrics compare frontend hypotheses against manually annotated structures in the fused LiDAR overlays.",
        "The annotations are a LiDAR-derived physical reference, not a survey-grade ground-truth map.",
        "",
        "Definitions:",
        "",
        "- `alignment_precision`: fraction of predictions that pass the geometric gate against their nearest same-class physical annotation.",
        "- `instance_precision`: unique physical structures recovered divided by number of predictions; this penalizes duplicate IDs on the same structure.",
        "- `physical_recall`: fraction of annotated physical structures recovered by at least one aligned prediction.",
        "- `fragmentation_index`: number of aligned predictions per recovered physical structure.",
        "",
        "Alignment gates used in this report:",
        "",
        "- walls: normal angle <= 8 deg, plane offset <= 0.40 m, projected gap <= 1.00 m, projected overlap ratio >= 0.25.",
        "- pillars: XY distance <= 0.55 m.",
        "- pipes: XY distance <= 0.35 m.",
        "",
        "Every prediction is assigned to its nearest same-class physical annotation before the alignment gate is evaluated. Therefore, failed predictions still appear in `physical_annotation_prediction_matches_all.csv` with their nearest annotation and error values.",
        "",
        "The `solid_wall_only_excluding_boundary_predictions` scope evaluates solid-wall precision after removing WallLike predictions that were already aligned with LiDAR-observable boundary annotations. This avoids counting useful boundary detections as false solid-wall detections.",
        "",
        "## Summary",
        "",
        "| Dataset | Scope | Model | Class | Predictions | GT annotations | Alignment precision | Instance precision | Physical recall | Fragmentation mean | Fragmentation max | Median wall angle | Median wall offset | Median XY error |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary_rows:
        lines.append(
            "| "
            + " | ".join([
                row["dataset"],
                row.get("evaluation_scope", ""),
                row["model"],
                row["structure_class"],
                row["total_predictions"],
                row["total_annotations"],
                pct(row["alignment_precision"]),
                pct(row["instance_precision"]),
                pct(row["physical_recall"]),
                row.get("fragmentation_index_mean", "") or "-",
                str(row.get("fragmentation_index_max", "") or "-"),
                row.get("median_angle_error_deg", "") or "-",
                row.get("median_offset_error_m", "") or "-",
                row.get("median_xy_error_m", "") or "-",
            ])
            + " |"
        )

    lines.extend([
        "",
        "## Per-Structure Fragmentation",
        "",
        "The file `physical_annotation_fragmentation_all.csv` reports, for every annotated structure, how many predictions selected it as nearest and how many passed the alignment gate.",
        "",
        "## Non-Annotated Structural-Like Cases",
        "",
        "In `walls_pillars_3`, one PipeLike track (`ID 5`) reached `confirmed`/`strong` even though no physical pipe was annotated in the scene; it is therefore counted as a PipeLike false positive under the current reference. The same run also contains PillarLike `ID 63`, which reached `confirmed`/`strong` but did not align with a physical pillar annotation (`6.83 m` XY error to the nearest annotated pillar). This detection is visually explainable as a protruding/glass-adjacent vertical structure, but remains a non-match for literal-pillar precision.",
        "",
        "## Pillar Proximity Note",
        "",
        "For `walls_pillars_3`, `walls_pillars_3_pillar_wall_proximity.csv` estimates how close each physical pillar annotation is to the nearest annotated wall segment. This helps separate open pillars from pillars that are very close to, or visually embedded in, wall returns.",
    ])

    if pillar_rows:
        near = [row for row in pillar_rows if row["proximity_bin"] == "near_or_embedded_wall"]
        open_rows = [row for row in pillar_rows if row["proximity_bin"] == "open_or_separated"]
        near_detected = sum(row["detected"] == "true" for row in near)
        open_detected = sum(row["detected"] == "true" for row in open_rows)
        lines.extend([
            "",
            "| Pillar subset | GT pillars | Detected by aligned InGraph PillarLike | Detection rate |",
            "|---|---:|---:|---:|",
            f"| near_or_embedded_wall | {len(near)} | {near_detected} | {(100.0 * near_detected / len(near)) if near else 0.0:.1f}% |",
            f"| open_or_separated | {len(open_rows)} | {open_detected} | {(100.0 * open_detected / len(open_rows)) if open_rows else 0.0:.1f}% |",
        ])

    lines.extend([
        "",
        "## Figures",
        "",
        "- `physical_annotation_precision_recall.png`: alignment precision, instance precision, and physical recall by dataset/model/class.",
        "- `walls_pillars_3_pillar_wall_proximity.png`: physical pillar distance to nearest wall and whether the pillar was aligned with an InGraph PillarLike prediction.",
        "",
    ])

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines))


def main() -> None:
    args = parse_args()
    step = args.step7a_root
    output = args.output_dir

    comparison_specs = [
        ("walls_pillars_3", step / "comparisons/walls_pillars_3_ingraph_vs_sgraphs", ""),
        ("teste_percepcion_5_0", step / "comparisons/teste_percepcion_5_0_ingraph_vs_sgraphs", ""),
        ("teste_percepcion_5_0", step / "comparisons/teste_percepcion_5_0_ingraph_vs_sgraphs", "_solid_wall_only"),
        ("teste_percepcion_5_0", step / "comparisons/teste_percepcion_5_0_ingraph_vs_sgraphs", "_solid_wall_only_no_boundaries"),
    ]

    summary_rows: list[dict[str, Any]] = []
    fragmentation_rows: list[dict[str, Any]] = []
    prediction_rows: list[dict[str, Any]] = []
    for dataset, comparison_dir, suffix in comparison_specs:
        data_dir = comparison_dir / "data"
        summary_path = data_dir / f"physical_annotation_alignment_summary{suffix}.csv"
        fragmentation_path = data_dir / f"physical_annotation_fragmentation_by_structure{suffix}.csv"
        predictions_path = data_dir / f"physical_annotation_alignment_predictions{suffix}.csv"
        if not summary_path.exists():
            continue
        summary_rows.extend(copy_rows_with_source(summary_path, dataset))
        fragmentation_rows.extend(copy_rows_with_source(fragmentation_path, dataset))
        prediction_rows.extend(copy_rows_with_source(predictions_path, dataset))

    write_csv(output / "physical_annotation_metrics_summary.csv", summary_rows, list(summary_rows[0].keys()))
    write_csv(output / "physical_annotation_fragmentation_all.csv", fragmentation_rows, list(fragmentation_rows[0].keys()))
    write_csv(output / "physical_annotation_prediction_matches_all.csv", prediction_rows, list(prediction_rows[0].keys()))
    build_precision_plot(summary_rows, output / "physical_annotation_precision_recall.png")
    pillar_rows = build_pillar_proximity(
        step / "annotations/walls_pillars_3_physical_annotations.csv",
        fragmentation_rows,
        output / "walls_pillars_3_pillar_wall_proximity.csv",
        output / "walls_pillars_3_pillar_wall_proximity.png",
    )
    write_markdown(output / "PHYSICAL_ANNOTATION_METRICS.md", summary_rows, fragmentation_rows, pillar_rows)
    print(f"Wrote {output / 'PHYSICAL_ANNOTATION_METRICS.md'}")


if __name__ == "__main__":
    main()
