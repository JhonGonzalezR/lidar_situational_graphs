#!/usr/bin/env bash
set -euo pipefail

STEP7A_ROOT="${STEP7A_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
REPO_ROOT="${REPO_ROOT:-$(cd "${STEP7A_ROOT}/.." && pwd)}"
BAG_PATH="${BAG_PATH:-/home/jhon/ingraph_ws/src/multi_robot_spatial/data/datasets/rosbags/bags_articulo/walls_pillars_3}"
ANNOTATIONS="${ANNOTATIONS:-${STEP7A_ROOT}/annotations/walls_pillars_3_physical_annotations.csv}"
COMPARE_DIR="${COMPARE_DIR:-${STEP7A_ROOT}/comparisons/walls_pillars_3_ingraph_vs_sgraphs}"
PLOTS_OVERLAY_DIR="${PLOTS_OVERLAY_DIR:-${COMPARE_DIR}/plots_overlay}"
MIN_OBS="${MIN_OBS:-1}"
WALL_ANNOTATION_SCOPE="${WALL_ANNOTATION_SCOPE:-walllike_boundary}"
EVALUATION_SCOPE="${EVALUATION_SCOPE:-${WALL_ANNOTATION_SCOPE}}"
PREDICTIONS_CSV="${PREDICTIONS_CSV:-${COMPARE_DIR}/data/physical_annotation_alignment_predictions.csv}"
SUMMARY_CSV="${SUMMARY_CSV:-${COMPARE_DIR}/data/physical_annotation_alignment_summary.csv}"
FRAGMENTATION_CSV="${FRAGMENTATION_CSV:-${COMPARE_DIR}/data/physical_annotation_fragmentation_by_structure.csv}"
ALIGNMENT_PNG="${ALIGNMENT_PNG:-${COMPARE_DIR}/plots/physical_annotation_alignment.png}"

cd "${REPO_ROOT}"

"${STEP7A_ROOT}/scripts/evaluate_physical_annotation_alignment.py" \
  --dataset walls_pillars_3 \
  --annotations "${ANNOTATIONS}" \
  --ingraph-tracks "${STEP7A_ROOT}/runs/20260602_233151/structure_anchor_tracks.csv" \
  --sgraphs-planes "${STEP7A_ROOT}/runs/walls_pillars_3_sgraphs_standard_optimized_old_001/sgraphs_wall_planes.csv" \
  --sgraphs-min-observations "${MIN_OBS}" \
  --wall-annotation-scope "${WALL_ANNOTATION_SCOPE}" \
  --evaluation-scope "${EVALUATION_SCOPE}" \
  --output-predictions "${PREDICTIONS_CSV}" \
  --output-summary "${SUMMARY_CSV}" \
  --output-fragmentation "${FRAGMENTATION_CSV}"

"${STEP7A_ROOT}/scripts/plot_physical_annotation_alignment.py" \
  --dataset walls_pillars_3 \
  --bag "${BAG_PATH}" \
  --annotations "${ANNOTATIONS}" \
  --alignment "${PREDICTIONS_CSV}" \
  --ingraph-tracks "${STEP7A_ROOT}/runs/20260602_233151/structure_anchor_tracks.csv" \
  --sgraphs-planes "${STEP7A_ROOT}/runs/walls_pillars_3_sgraphs_standard_optimized_old_001/sgraphs_wall_planes.csv" \
  --sgraphs-min-observations "${MIN_OBS}" \
  --output "${ALIGNMENT_PNG}" \
  --overlay-summary "${PLOTS_OVERLAY_DIR}/lidar_overlay_windows_summary.csv" \
  --overlay-windows "2 3" \
  --point-stride 8 \
  --min-z -6.5 \
  --max-z 1.0 \
  --xlim -30 5 \
  --ylim -15 15

printf '\nSummary:\n'
cat "${SUMMARY_CSV}"
