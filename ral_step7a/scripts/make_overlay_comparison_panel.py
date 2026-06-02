#!/usr/bin/env python3
"""Create a side-by-side panel from two overlay PNG files."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.image as mpimg
import matplotlib.pyplot as plt


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a comparison panel from overlay PNGs.")
    parser.add_argument("--left", required=True, type=Path)
    parser.add_argument("--right", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--left-title", default="S-Graphs")
    parser.add_argument("--right-title", default="InGraph")
    parser.add_argument("--title", default="Step 7A wall-plane overlay comparison")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    left = mpimg.imread(args.left)
    right = mpimg.imread(args.right)

    fig, axes = plt.subplots(1, 2, figsize=(14.5, 7.2))
    for ax, image, title in (
        (axes[0], left, args.left_title),
        (axes[1], right, args.right_title),
    ):
        ax.imshow(image)
        ax.set_title(title)
        ax.axis("off")

    fig.suptitle(args.title)
    fig.tight_layout()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=180)
    plt.close(fig)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
