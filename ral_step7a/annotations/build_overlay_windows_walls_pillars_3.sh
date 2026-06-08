#!/usr/bin/env bash
set -euo pipefail

STEP7A_ROOT="${STEP7A_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
REPO_ROOT="${REPO_ROOT:-$(cd "${STEP7A_ROOT}/.." && pwd)}"
BAG_PATH="${BAG_PATH:-/home/jhon/ingraph_ws/src/multi_robot_spatial/data/datasets/rosbags/bags_articulo/walls_pillars_3}"
OUTPUT_DIR="${OUTPUT_DIR:-${STEP7A_ROOT}/comparisons/walls_pillars_3_ingraph_vs_sgraphs/plots_overlay}"
NUM_WINDOWS="${NUM_WINDOWS:-4}"
WINDOW_MESSAGES="${WINDOW_MESSAGES:-50}"
POINT_STRIDE="${POINT_STRIDE:-8}"
MIN_Z="${MIN_Z:--6.5}"
MAX_Z="${MAX_Z:-1.0}"
POINT_SIZE="${POINT_SIZE:-0.32}"
ALPHA="${ALPHA:-0.55}"

cd "${REPO_ROOT}"

"${STEP7A_ROOT}/scripts/plot_lidar_overlay_windows.py" \
  --dataset walls_pillars_3 \
  --bag "${BAG_PATH}" \
  --output-dir "${OUTPUT_DIR}" \
  --num-windows "${NUM_WINDOWS}" \
  --window-messages "${WINDOW_MESSAGES}" \
  --point-stride "${POINT_STRIDE}" \
  --min-z "${MIN_Z}" \
  --max-z "${MAX_Z}" \
  --point-size "${POINT_SIZE}" \
  --alpha "${ALPHA}" \
  --xlim -50 8 \
  --ylim -55 15
