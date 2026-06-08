#!/usr/bin/env bash
set -euo pipefail

# Rebuild the perception-bag visual evidence bundle used in the RA-L Step 7A
# comparison. This bag is the current real-pipe evidence sequence.

STEP7A_ROOT="${STEP7A_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
BAG_PATH="${BAG_PATH:-/home/jhon/ingraph_ws/src/multi_robot_spatial/data/datasets/rosbags/teste_percepcion_5_0-001.mcap}"
INGRAPH_RUN_DIR="${INGRAPH_RUN_DIR:-${STEP7A_ROOT}/runs/20260603_014722}"
SGRAPHS_RUN_DIR="${SGRAPHS_RUN_DIR:-${STEP7A_ROOT}/runs/teste_percepcion_5_0_sgraphs_standard_optimized_old_001}"
COMPARISON_DIR="${COMPARISON_DIR:-${STEP7A_ROOT}/comparisons/teste_percepcion_5_0_ingraph_vs_sgraphs}"
PLOTS_DIR="${PLOTS_DIR:-${COMPARISON_DIR}/plots}"
PLOTS_OVERLAY_DIR="${PLOTS_OVERLAY_DIR:-${COMPARISON_DIR}/plots_overlay}"
PAPER_XLIM="${PAPER_XLIM:--14 18}"
PAPER_YLIM="${PAPER_YLIM:--14 8}"
MIN_OBSERVATIONS="${MIN_OBSERVATIONS:-5}"
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
  OVERLAY_WINDOWS="1 2 3"
)

env "${COMMON_ENV[@]}" \
  RUN_ID=20260603_014722 \
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
  RUN_ID=20260603_014722 \
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
  RUN_ID=20260603_014722 \
  INGRAPH_OUTPUT_RUN_DIR="${INGRAPH_RUN_DIR}" \
  TRACKS_CSV="${INGRAPH_RUN_DIR}/structure_anchor_tracks.csv" \
  OUTPUT_DIR="${PLOTS_DIR}" \
  MODE=strong \
  SNAPSHOT=latest_strong \
  CLASSES=pipe_like \
  MIN_AGE=1 \
  OUTPUT_PNG="${PLOTS_DIR}/evidence_ingraph_ever_strong_pipes.png" \
  SUMMARY_MD="${PLOTS_DIR}/summary_evidence_ingraph_ever_strong_pipes.md" \
  TITLE="InGraph ever-Strong PipeLike anchors" \
  "${STEP7A_ROOT}/scripts/plot_ingraph_structure_overlay.sh"

env "${COMMON_ENV[@]}" \
  RUN_ID=teste_percepcion_5_0_sgraphs_standard_optimized_old_001 \
  MIN_OBSERVATIONS="${MIN_OBSERVATIONS}" \
  INPUT_CSV="${SGRAPHS_RUN_DIR}/sgraphs_wall_planes.csv" \
  OUTPUT_PNG="${PLOTS_DIR}/evidence_sgraphs_persistent_walls_min5.png" \
  TITLE="S-Graphs wall planes, observations >= ${MIN_OBSERVATIONS}" \
  "${STEP7A_ROOT}/scripts/plot_sgraphs_lidar_overlay.sh"

python3 "${STEP7A_ROOT}/scripts/plot_class_coverage.py" \
  --csv "${COMPARISON_DIR}/data/class_coverage.csv" \
  --output "${PLOTS_DIR}/class_coverage_matched_dataset.png" \
  --title "Class coverage on teste_percepcion_5_0"

python3 "${STEP7A_ROOT}/scripts/make_overlay_comparison_panel.py" \
  --left "${PLOTS_DIR}/evidence_sgraphs_persistent_walls_min5.png" \
  --right "${PLOTS_DIR}/evidence_ingraph_ever_strong_all.png" \
  --output "${PLOTS_DIR}/evidence_side_by_side_panel.png" \
  --left-title "S-Graphs wall planes (min ${MIN_OBSERVATIONS} obs.)" \
  --right-title "InGraph Wall/Pillar/Pipe anchors" \
  --title "teste_percepcion_5_0 frontend evidence"

(
  cd "${COMPARISON_DIR}"
  find data plots -type f | sort | xargs sha256sum > CHECKSUMS.sha256
  sha256sum MANIFEST.md >> CHECKSUMS.sha256
)
