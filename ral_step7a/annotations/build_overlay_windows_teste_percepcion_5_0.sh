#!/usr/bin/env bash
set -euo pipefail

STEP7A_ROOT="${STEP7A_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
REPO_ROOT="${REPO_ROOT:-$(cd "${STEP7A_ROOT}/.." && pwd)}"
BAG_PATH="${BAG_PATH:-/home/jhon/ingraph_ws/src/multi_robot_spatial/data/datasets/rosbags/teste_percepcion_5_0-001.mcap}"
OUTPUT_DIR="${OUTPUT_DIR:-${STEP7A_ROOT}/comparisons/teste_percepcion_5_0_ingraph_vs_sgraphs/plots_overlay}"
NUM_WINDOWS="${NUM_WINDOWS:-4}"
WINDOW_MESSAGES="${WINDOW_MESSAGES:-40}"
POINT_STRIDE="${POINT_STRIDE:-10}"

cd "${REPO_ROOT}"

"${STEP7A_ROOT}/scripts/plot_lidar_overlay_windows.py" \
  --dataset teste_percepcion_5_0 \
  --bag "${BAG_PATH}" \
  --output-dir "${OUTPUT_DIR}" \
  --num-windows "${NUM_WINDOWS}" \
  --window-messages "${WINDOW_MESSAGES}" \
  --point-stride "${POINT_STRIDE}" \
  --xlim -14 18 \
  --ylim -14 8
