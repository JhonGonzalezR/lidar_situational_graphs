#!/usr/bin/env bash
set -euo pipefail

# Rebuild the walls_pillars_3 visual evidence bundle using the fused overlay
# windows selected for physical annotation.

STEP7A_ROOT="${STEP7A_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
BAG_PATH="${BAG_PATH:-/home/jhon/ingraph_ws/src/multi_robot_spatial/data/datasets/rosbags/bags_articulo/walls_pillars_3}"
INGRAPH_RUN_DIR="${INGRAPH_RUN_DIR:-${STEP7A_ROOT}/runs/20260602_233151}"
SGRAPHS_RUN_DIR="${SGRAPHS_RUN_DIR:-${STEP7A_ROOT}/runs/walls_pillars_3_sgraphs_standard_optimized_old_001}"
COMPARISON_DIR="${COMPARISON_DIR:-${STEP7A_ROOT}/comparisons/walls_pillars_3_ingraph_vs_sgraphs}"
PLOTS_DIR="${PLOTS_DIR:-${COMPARISON_DIR}/plots}"
PLOTS_OVERLAY_DIR="${PLOTS_OVERLAY_DIR:-${COMPARISON_DIR}/plots_overlay}"
PAPER_XLIM="${PAPER_XLIM:--30 5}"
PAPER_YLIM="${PAPER_YLIM:--15 15}"
MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/mplconfig}"

mkdir -p "${PLOTS_DIR}" "${MPLCONFIGDIR}"
export MPLCONFIGDIR

COMMON_ENV=(
  STEP7A_ROOT="${STEP7A_ROOT}"
  BAG_PATH="${BAG_PATH}"
  LIDAR_TOPIC="/velodyne/points"
  PAPER=true
  SHOW_IDS=true
  PAPER_XLIM="${PAPER_XLIM}"
  PAPER_YLIM="${PAPER_YLIM}"
  OVERLAY_SUMMARY="${PLOTS_OVERLAY_DIR}/lidar_overlay_windows_summary.csv"
  OVERLAY_WINDOWS="2 3"
  POINT_STRIDE=8
  MIN_Z=-6.5
  MAX_Z=1.0
  MAX_POINTS=450000
)

env "${COMMON_ENV[@]}" \
  RUN_ID=20260602_233151 \
  INGRAPH_OUTPUT_RUN_DIR="${INGRAPH_RUN_DIR}" \
  TRACKS_CSV="${INGRAPH_RUN_DIR}/structure_anchor_tracks.csv" \
  OUTPUT_DIR="${PLOTS_DIR}" \
  MODE=strong \
  SNAPSHOT=latest_strong \
  CLASSES=wall_like,pillar_like,pipe_like \
  MIN_AGE=1 \
  OUTPUT_PNG="${PLOTS_DIR}/evidence_ingraph_ever_strong_all.png" \
  SUMMARY_MD="${PLOTS_DIR}/summary_evidence_ingraph_ever_strong_all.md" \
  TITLE="InGraph ever-Strong structural anchors" \
  "${STEP7A_ROOT}/scripts/plot_ingraph_structure_overlay.sh"

env "${COMMON_ENV[@]}" \
  RUN_ID=20260602_233151 \
  INGRAPH_OUTPUT_RUN_DIR="${INGRAPH_RUN_DIR}" \
  TRACKS_CSV="${INGRAPH_RUN_DIR}/structure_anchor_tracks.csv" \
  OUTPUT_DIR="${PLOTS_DIR}" \
  MODE=strong \
  SNAPSHOT=latest_strong \
  CLASSES=wall_like \
  HIDE_NON_WALL=true \
  MIN_AGE=1 \
  OUTPUT_PNG="${PLOTS_DIR}/evidence_ingraph_ever_strong_walls.png" \
  SUMMARY_MD="${PLOTS_DIR}/summary_evidence_ingraph_ever_strong_walls.md" \
  TITLE="InGraph ever-Strong WallLike anchors" \
  "${STEP7A_ROOT}/scripts/plot_ingraph_structure_overlay.sh"

env "${COMMON_ENV[@]}" \
  RUN_ID=walls_pillars_3_sgraphs_standard_optimized_old_001 \
  MIN_OBSERVATIONS=20 \
  INPUT_CSV="${SGRAPHS_RUN_DIR}/sgraphs_wall_planes.csv" \
  OUTPUT_PNG="${PLOTS_DIR}/evidence_sgraphs_persistent_walls.png" \
  TITLE="S-Graphs wall planes, observations >= 20" \
  "${STEP7A_ROOT}/scripts/plot_sgraphs_lidar_overlay.sh"

env "${COMMON_ENV[@]}" \
  RUN_ID=walls_pillars_3_sgraphs_standard_optimized_old_001 \
  MIN_OBSERVATIONS=1 \
  INPUT_CSV="${SGRAPHS_RUN_DIR}/sgraphs_wall_planes.csv" \
  OUTPUT_PNG="${PLOTS_DIR}/evidence_sgraphs_all_walls.png" \
  TITLE="S-Graphs all published wall planes" \
  "${STEP7A_ROOT}/scripts/plot_sgraphs_lidar_overlay.sh"

python3 "${STEP7A_ROOT}/scripts/make_overlay_comparison_panel.py" \
  --left "${PLOTS_DIR}/evidence_sgraphs_persistent_walls.png" \
  --right "${PLOTS_DIR}/evidence_ingraph_ever_strong_all.png" \
  --output "${PLOTS_DIR}/evidence_side_by_side_panel.png" \
  --left-title "S-Graphs wall planes (min 20 obs.)" \
  --right-title "InGraph Wall/Pillar/Pipe anchors" \
  --title "walls_pillars_3 frontend evidence"

python3 "${STEP7A_ROOT}/scripts/make_overlay_comparison_panel.py" \
  --left "${PLOTS_DIR}/evidence_sgraphs_all_walls.png" \
  --right "${PLOTS_DIR}/evidence_ingraph_ever_strong_all.png" \
  --output "${PLOTS_DIR}/evidence_side_by_side_panel_sgraphs_all.png" \
  --left-title "S-Graphs all published walls" \
  --right-title "InGraph Wall/Pillar/Pipe anchors" \
  --title "walls_pillars_3 frontend evidence"

(
  cd "${COMPARISON_DIR}"
  find data plots plots_overlay -type f | sort | xargs sha256sum > CHECKSUMS.sha256
  sha256sum MANIFEST.md >> CHECKSUMS.sha256
)
