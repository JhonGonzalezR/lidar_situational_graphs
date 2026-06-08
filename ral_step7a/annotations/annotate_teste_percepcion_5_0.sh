#!/usr/bin/env bash
set -euo pipefail

STEP7A_ROOT="${STEP7A_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
REPO_ROOT="${REPO_ROOT:-$(cd "${STEP7A_ROOT}/.." && pwd)}"
BAG_PATH="${BAG_PATH:-/home/jhon/ingraph_ws/src/multi_robot_spatial/data/datasets/rosbags/teste_percepcion_5_0-001.mcap}"
OUTPUT="${OUTPUT:-${STEP7A_ROOT}/annotations/teste_percepcion_5_0_physical_annotations.csv}"
PLOTS_OVERLAY_DIR="${PLOTS_OVERLAY_DIR:-${STEP7A_ROOT}/comparisons/teste_percepcion_5_0_ingraph_vs_sgraphs/plots_overlay}"

cd "${REPO_ROOT}"

"${STEP7A_ROOT}/scripts/annotate_physical_structures.py" \
  --dataset teste_percepcion_5_0 \
  --bag "${BAG_PATH}" \
  --output "${OUTPUT}" \
  --overlay-summary "${PLOTS_OVERLAY_DIR}/lidar_overlay_windows_summary.csv" \
  --overlay-windows "1 2 3" \
  --xlim -14 18 \
  --ylim -14 8
