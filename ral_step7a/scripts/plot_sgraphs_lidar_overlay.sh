#!/usr/bin/env bash
set -euo pipefail

# Generate a top-down overlay of the sampled input LiDAR cloud and persistent
# S-Graphs wall-plane hypotheses. This is the recommended visual sanity check
# before making paper claims about wall recovery.

RUN_ID="${RUN_ID:-spot_dinamicaStaticV0_sgraphs_step7a_old_002}"
STEP7A_ROOT="${STEP7A_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
OUTPUT_ROOT="${OUTPUT_ROOT:-${STEP7A_ROOT}/runs}"
RESULTS_DIR="${RESULTS_DIR:-${OUTPUT_ROOT}/${RUN_ID}}"
INPUT_CSV="${INPUT_CSV:-${RESULTS_DIR}/sgraphs_wall_planes.csv}"
OUTPUT_PNG="${OUTPUT_PNG:-${RESULTS_DIR}/plots/sgraphs_lidar_wall_overlay_odom.png}"
LIDAR_TOPIC="${LIDAR_TOPIC:-/velodyne/points}"
MAX_MESSAGES="${MAX_MESSAGES:-60}"
POINT_STRIDE="${POINT_STRIDE:-12}"
MIN_Z="${MIN_Z:--2.0}"
MAX_Z="${MAX_Z:-3.0}"
MAX_POINTS="${MAX_POINTS:-350000}"
MIN_OBSERVATIONS="${MIN_OBSERVATIONS:-20}"
SEGMENT_FRAME="${SEGMENT_FRAME:-auto}"
TITLE="${TITLE:-S-Graphs persistent wall planes}"
PAPER="${PAPER:-true}"
SHOW_IDS="${SHOW_IDS:-true}"
PAPER_XLIM="${PAPER_XLIM:--35 10}"
PAPER_YLIM="${PAPER_YLIM:--20 20}"
OVERLAY_SUMMARY="${OVERLAY_SUMMARY:-}"
OVERLAY_WINDOWS="${OVERLAY_WINDOWS:-}"
MAX_POINTS_PER_WINDOW="${MAX_POINTS_PER_WINDOW:-250000}"
MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/mplconfig}"

mkdir -p "${MPLCONFIGDIR}"
export MPLCONFIGDIR

if [[ -z "${BAG_PATH:-}" ]]; then
  echo "ERROR: BAG_PATH is required. Example:" >&2
  echo "  export BAG_PATH=/absolute/path/to/rosbag_directory" >&2
  exit 2
fi

ARGS=(
  --bag "${BAG_PATH}" \
  --topic "${LIDAR_TOPIC}" \
  --csv "${INPUT_CSV}" \
  --output "${OUTPUT_PNG}" \
  --max-messages "${MAX_MESSAGES}" \
  --point-stride "${POINT_STRIDE}" \
  --min-z "${MIN_Z}" \
  --max-z "${MAX_Z}" \
  --max-points "${MAX_POINTS}" \
  --min-observations "${MIN_OBSERVATIONS}" \
  --segment-frame "${SEGMENT_FRAME}" \
  --title "${TITLE}"
)

if [[ -n "${OVERLAY_SUMMARY}" && -n "${OVERLAY_WINDOWS}" ]]; then
  ARGS+=(--overlay-summary "${OVERLAY_SUMMARY}" --overlay-windows "${OVERLAY_WINDOWS}" --max-points-per-window "${MAX_POINTS_PER_WINDOW}")
fi

if [[ "${PAPER}" == "true" || "${PAPER}" == "1" ]]; then
  ARGS+=(--paper --xlim ${PAPER_XLIM} --ylim ${PAPER_YLIM})
fi

if [[ "${SHOW_IDS}" == "true" || "${SHOW_IDS}" == "1" ]]; then
  ARGS+=(--show-ids)
fi

exec python3 "$(dirname "$0")/plot_sgraphs_lidar_overlay.py" "${ARGS[@]}"
