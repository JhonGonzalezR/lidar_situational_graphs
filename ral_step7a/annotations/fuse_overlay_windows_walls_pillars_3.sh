#!/usr/bin/env bash
set -euo pipefail

STEP7A_ROOT="${STEP7A_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
REPO_ROOT="${REPO_ROOT:-$(cd "${STEP7A_ROOT}/.." && pwd)}"
BAG_PATH="${BAG_PATH:-/home/jhon/ingraph_ws/src/multi_robot_spatial/data/datasets/rosbags/bags_articulo/walls_pillars_3}"
PLOTS_DIR="${PLOTS_DIR:-${STEP7A_ROOT}/comparisons/walls_pillars_3_ingraph_vs_sgraphs/plots_overlay}"
OUTPUT="${OUTPUT:-${PLOTS_DIR}/lidar_overlay_fusion_windows_02_03.png}"
WINDOWS="${WINDOWS:-2 3}"

cd "${REPO_ROOT}"

"${STEP7A_ROOT}/scripts/plot_lidar_overlay_fusion.py" \
  --dataset walls_pillars_3 \
  --bag "${BAG_PATH}" \
  --summary "${PLOTS_DIR}/lidar_overlay_windows_summary.csv" \
  --output "${OUTPUT}" \
  --windows ${WINDOWS} \
  --point-stride 8 \
  --min-z -6.5 \
  --max-z 1.0 \
  --point-size 0.26 \
  --alpha 0.36 \
  --xlim -30 5 \
  --ylim -15 15
