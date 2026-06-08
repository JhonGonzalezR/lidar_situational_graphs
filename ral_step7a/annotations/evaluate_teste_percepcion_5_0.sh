#!/usr/bin/env bash
set -euo pipefail

STEP7A_ROOT="${STEP7A_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
REPO_ROOT="${REPO_ROOT:-$(cd "${STEP7A_ROOT}/.." && pwd)}"
BAG_PATH="${BAG_PATH:-/home/jhon/ingraph_ws/src/multi_robot_spatial/data/datasets/rosbags/teste_percepcion_5_0-001.mcap}"
ANNOTATIONS="${ANNOTATIONS:-${STEP7A_ROOT}/annotations/teste_percepcion_5_0_physical_annotations.csv}"
COMPARE_DIR="${COMPARE_DIR:-${STEP7A_ROOT}/comparisons/teste_percepcion_5_0_ingraph_vs_sgraphs}"
PLOTS_OVERLAY_DIR="${PLOTS_OVERLAY_DIR:-${COMPARE_DIR}/plots_overlay}"
MIN_OBS="${MIN_OBS:-5}"
WALL_ANNOTATION_SCOPE="${WALL_ANNOTATION_SCOPE:-walllike_boundary}"
EVALUATION_SCOPE="${EVALUATION_SCOPE:-${WALL_ANNOTATION_SCOPE}}"
PREDICTIONS_CSV="${PREDICTIONS_CSV:-${COMPARE_DIR}/data/physical_annotation_alignment_predictions.csv}"
SUMMARY_CSV="${SUMMARY_CSV:-${COMPARE_DIR}/data/physical_annotation_alignment_summary.csv}"
FRAGMENTATION_CSV="${FRAGMENTATION_CSV:-${COMPARE_DIR}/data/physical_annotation_fragmentation_by_structure.csv}"
ALIGNMENT_PNG="${ALIGNMENT_PNG:-${COMPARE_DIR}/plots/physical_annotation_alignment.png}"
EXCLUDE_BOUNDARY_WALL_PREDICTIONS="${EXCLUDE_BOUNDARY_WALL_PREDICTIONS:-false}"
HIDE_UNLISTED_PREDICTIONS="${HIDE_UNLISTED_PREDICTIONS:-false}"

cd "${REPO_ROOT}"

EVAL_EXTRA_ARGS=()
if [[ "${EXCLUDE_BOUNDARY_WALL_PREDICTIONS}" == "true" ]]; then
  EVAL_EXTRA_ARGS+=(--exclude-boundary-wall-predictions)
fi

"${STEP7A_ROOT}/scripts/evaluate_physical_annotation_alignment.py" \
  --dataset teste_percepcion_5_0 \
  --annotations "${ANNOTATIONS}" \
  --ingraph-tracks "${STEP7A_ROOT}/runs/20260603_014722/structure_anchor_tracks.csv" \
  --sgraphs-planes "${STEP7A_ROOT}/runs/teste_percepcion_5_0_sgraphs_standard_optimized_old_001/sgraphs_wall_planes.csv" \
  --sgraphs-min-observations "${MIN_OBS}" \
  --wall-annotation-scope "${WALL_ANNOTATION_SCOPE}" \
  --evaluation-scope "${EVALUATION_SCOPE}" \
  --output-predictions "${PREDICTIONS_CSV}" \
  --output-summary "${SUMMARY_CSV}" \
  --output-fragmentation "${FRAGMENTATION_CSV}" \
  "${EVAL_EXTRA_ARGS[@]}"

PLOT_EXTRA_ARGS=()
if [[ "${HIDE_UNLISTED_PREDICTIONS}" == "true" ]]; then
  PLOT_EXTRA_ARGS+=(--hide-unlisted-predictions)
fi

"${STEP7A_ROOT}/scripts/plot_physical_annotation_alignment.py" \
  --dataset teste_percepcion_5_0 \
  --bag "${BAG_PATH}" \
  --annotations "${ANNOTATIONS}" \
  --alignment "${PREDICTIONS_CSV}" \
  --ingraph-tracks "${STEP7A_ROOT}/runs/20260603_014722/structure_anchor_tracks.csv" \
  --sgraphs-planes "${STEP7A_ROOT}/runs/teste_percepcion_5_0_sgraphs_standard_optimized_old_001/sgraphs_wall_planes.csv" \
  --sgraphs-min-observations "${MIN_OBS}" \
  --output "${ALIGNMENT_PNG}" \
  --overlay-summary "${PLOTS_OVERLAY_DIR}/lidar_overlay_windows_summary.csv" \
  --overlay-windows "1 2 3" \
  --xlim -14 18 \
  --ylim -14 8 \
  "${PLOT_EXTRA_ARGS[@]}"

printf '\nSummary:\n'
cat "${SUMMARY_CSV}"
