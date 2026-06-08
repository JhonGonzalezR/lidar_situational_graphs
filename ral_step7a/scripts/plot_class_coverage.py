#!/usr/bin/env python3
"""Plot persistent-anchor coverage from a Step 7A class_coverage.csv file."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot InGraph/S-Graphs class coverage.")
    parser.add_argument("--csv", required=True, type=Path, help="class_coverage.csv")
    parser.add_argument("--output", required=True, type=Path, help="Output PNG.")
    parser.add_argument("--title", default="Class coverage")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = list(csv.DictReader(args.csv.open()))
    classes = ["wall_like", "pillar_like", "pipe_like"]
    models = ["InGraph", "S-Graphs"]
    values = {model: [] for model in models}
    labels = {model: [] for model in models}

    for model in models:
        for anchor_class in classes:
            row = next(
                (
                    item
                    for item in rows
                    if item.get("model") == model and item.get("class") == anchor_class
                ),
                None,
            )
            if row is None:
                values[model].append(0.0)
                labels[model].append("N/A")
                continue
            if row.get("output_status") == "not_exposed" or not row.get("selected_hypotheses"):
                values[model].append(0.0)
                labels[model].append("N/A" if row.get("output_status") == "not_exposed" else "0")
                continue
            values[model].append(float(row["selected_hypotheses"]))
            labels[model].append(f"{row['selected_hypotheses']}/{row['total_hypotheses']}")

    x_positions = list(range(len(classes)))
    width = 0.36
    colors = {"InGraph": "#1f77b4", "S-Graphs": "#ff7f0e"}
    fig, ax = plt.subplots(figsize=(7.2, 4.2))

    for index, model in enumerate(models):
        offsets = [x + (-width / 2 if index == 0 else width / 2) for x in x_positions]
        bars = ax.bar(offsets, values[model], width=width, label=model, color=colors[model], alpha=0.88)
        for bar, label in zip(bars, labels[model]):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.35,
                label,
                ha="center",
                va="bottom",
                fontsize=9,
            )

    ax.set_xticks(x_positions, ["WallLike", "PillarLike", "PipeLike"])
    ax.set_ylabel("Persistent / mature IDs")
    ax.set_title(args.title)
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=0.25)
    ax.set_ylim(0, max(max(series) for series in values.values()) + 4)
    fig.tight_layout()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=180)
    plt.close(fig)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
