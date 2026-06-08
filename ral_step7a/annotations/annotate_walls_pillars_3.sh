#!/usr/bin/env bash
set -euo pipefail

STEP7A_ROOT="${STEP7A_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
REPO_ROOT="${REPO_ROOT:-$(cd "${STEP7A_ROOT}/.." && pwd)}"
BAG_PATH="${BAG_PATH:-/home/jhon/ingraph_ws/src/multi_robot_spatial/data/datasets/rosbags/bags_articulo/walls_pillars_3}"
OUTPUT="${OUTPUT:-${STEP7A_ROOT}/annotations/walls_pillars_3_physical_annotations.csv}"
PLOTS_OVERLAY_DIR="${PLOTS_OVERLAY_DIR:-${STEP7A_ROOT}/comparisons/walls_pillars_3_ingraph_vs_sgraphs/plots_overlay}"

cd "${REPO_ROOT}"

"${STEP7A_ROOT}/scripts/annotate_physical_structures.py" \
  --dataset walls_pillars_3 \
  --bag "${BAG_PATH}" \
  --output "${OUTPUT}" \
  --overlay-summary "${PLOTS_OVERLAY_DIR}/lidar_overlay_windows_summary.csv" \
  --overlay-windows "2 3" \
  --point-stride 8 \
  --min-z -6.5 \
  --max-z 1.0 \
  --xlim -30 5 \
  --ylim -15 15
