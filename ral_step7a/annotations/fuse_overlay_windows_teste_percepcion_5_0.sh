#!/usr/bin/env bash
set -euo pipefail

STEP7A_ROOT="${STEP7A_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
REPO_ROOT="${REPO_ROOT:-$(cd "${STEP7A_ROOT}/.." && pwd)}"
BAG_PATH="${BAG_PATH:-/home/jhon/ingraph_ws/src/multi_robot_spatial/data/datasets/rosbags/teste_percepcion_5_0-001.mcap}"
PLOTS_DIR="${PLOTS_DIR:-${STEP7A_ROOT}/comparisons/teste_percepcion_5_0_ingraph_vs_sgraphs/plots_overlay}"
OUTPUT="${OUTPUT:-${PLOTS_DIR}/lidar_overlay_fusion_windows_01_02_03.png}"
WINDOWS="${WINDOWS:-1 2 3}"

cd "${REPO_ROOT}"

"${STEP7A_ROOT}/scripts/plot_lidar_overlay_fusion.py" \
  --dataset teste_percepcion_5_0 \
  --bag "${BAG_PATH}" \
  --summary "${PLOTS_DIR}/lidar_overlay_windows_summary.csv" \
  --output "${OUTPUT}" \
  --windows ${WINDOWS} \
  --point-stride 10 \
  --min-z -2.0 \
  --max-z 3.0 \
  --point-size 0.24 \
  --alpha 0.42 \
  --xlim -14 18 \
  --ylim -14 8
