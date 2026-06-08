#!/usr/bin/env bash
set -euo pipefail

STEP7A_ROOT="${STEP7A_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
REPO_ROOT="${REPO_ROOT:-$(cd "${STEP7A_ROOT}/.." && pwd)}"
MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/mplconfig}"

cd "${REPO_ROOT}"
mkdir -p "${MPLCONFIGDIR}"
export MPLCONFIGDIR

"${STEP7A_ROOT}/scripts/plot_physical_annotations_only.py" \
  --dataset walls_pillars_3 \
  --bag /home/jhon/ingraph_ws/src/multi_robot_spatial/data/datasets/rosbags/bags_articulo/walls_pillars_3 \
  --annotations "${STEP7A_ROOT}/annotations/walls_pillars_3_physical_annotations.csv" \
  --output "${STEP7A_ROOT}/comparisons/walls_pillars_3_ingraph_vs_sgraphs/plots/physical_annotations_ground_truth.png" \
  --overlay-summary "${STEP7A_ROOT}/comparisons/walls_pillars_3_ingraph_vs_sgraphs/plots_overlay/lidar_overlay_windows_summary.csv" \
  --overlay-windows "2 3" \
  --point-stride 8 \
  --min-z -6.5 \
  --max-z 1.0 \
  --xlim -30 5 \
  --ylim -15 15

"${STEP7A_ROOT}/scripts/plot_physical_annotations_only.py" \
  --dataset teste_percepcion_5_0 \
  --bag /home/jhon/ingraph_ws/src/multi_robot_spatial/data/datasets/rosbags/teste_percepcion_5_0-001.mcap \
  --annotations "${STEP7A_ROOT}/annotations/teste_percepcion_5_0_physical_annotations.csv" \
  --output "${STEP7A_ROOT}/comparisons/teste_percepcion_5_0_ingraph_vs_sgraphs/plots/physical_annotations_ground_truth.png" \
  --overlay-summary "${STEP7A_ROOT}/comparisons/teste_percepcion_5_0_ingraph_vs_sgraphs/plots_overlay/lidar_overlay_windows_summary.csv" \
  --overlay-windows "1 2 3" \
  --xlim -14 18 \
  --ylim -14 8

"${STEP7A_ROOT}/annotations/evaluate_walls_pillars_3.sh"
"${STEP7A_ROOT}/annotations/evaluate_teste_percepcion_5_0.sh"

WALL_ANNOTATION_SCOPE=solid_wall_only \
EVALUATION_SCOPE=solid_wall_only \
PREDICTIONS_CSV="${STEP7A_ROOT}/comparisons/teste_percepcion_5_0_ingraph_vs_sgraphs/data/physical_annotation_alignment_predictions_solid_wall_only.csv" \
SUMMARY_CSV="${STEP7A_ROOT}/comparisons/teste_percepcion_5_0_ingraph_vs_sgraphs/data/physical_annotation_alignment_summary_solid_wall_only.csv" \
FRAGMENTATION_CSV="${STEP7A_ROOT}/comparisons/teste_percepcion_5_0_ingraph_vs_sgraphs/data/physical_annotation_fragmentation_by_structure_solid_wall_only.csv" \
ALIGNMENT_PNG="${STEP7A_ROOT}/comparisons/teste_percepcion_5_0_ingraph_vs_sgraphs/plots/physical_annotation_alignment_solid_wall_only.png" \
"${STEP7A_ROOT}/annotations/evaluate_teste_percepcion_5_0.sh"

WALL_ANNOTATION_SCOPE=solid_wall_only \
EVALUATION_SCOPE=solid_wall_only_excluding_boundary_predictions \
EXCLUDE_BOUNDARY_WALL_PREDICTIONS=true \
HIDE_UNLISTED_PREDICTIONS=true \
PREDICTIONS_CSV="${STEP7A_ROOT}/comparisons/teste_percepcion_5_0_ingraph_vs_sgraphs/data/physical_annotation_alignment_predictions_solid_wall_only_no_boundaries.csv" \
SUMMARY_CSV="${STEP7A_ROOT}/comparisons/teste_percepcion_5_0_ingraph_vs_sgraphs/data/physical_annotation_alignment_summary_solid_wall_only_no_boundaries.csv" \
FRAGMENTATION_CSV="${STEP7A_ROOT}/comparisons/teste_percepcion_5_0_ingraph_vs_sgraphs/data/physical_annotation_fragmentation_by_structure_solid_wall_only_no_boundaries.csv" \
ALIGNMENT_PNG="${STEP7A_ROOT}/comparisons/teste_percepcion_5_0_ingraph_vs_sgraphs/plots/physical_annotation_alignment_solid_wall_only_no_boundaries.png" \
"${STEP7A_ROOT}/annotations/evaluate_teste_percepcion_5_0.sh"

"${STEP7A_ROOT}/scripts/summarize_physical_annotation_results.py" \
  --step7a-root "${STEP7A_ROOT}" \
  --output-dir "${STEP7A_ROOT}/results"
