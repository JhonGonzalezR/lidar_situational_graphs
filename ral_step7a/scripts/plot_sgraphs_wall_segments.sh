#!/usr/bin/env bash
set -euo pipefail

# Generate a top-down diagnostic figure of persistent S-Graphs wall-plane IDs as
# finite odom-frame wall segments.

RUN_ID="${RUN_ID:-spot_dinamicaStaticV0_sgraphs_step7a_old_002}"
STEP7A_ROOT="${STEP7A_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
OUTPUT_ROOT="${OUTPUT_ROOT:-${STEP7A_ROOT}/runs}"
INPUT_CSV="${INPUT_CSV:-${OUTPUT_ROOT}/${RUN_ID}/sgraphs_wall_planes.csv}"
OUTPUT_PNG="${OUTPUT_PNG:-${OUTPUT_ROOT}/${RUN_ID}/plots/sgraphs_wall_plane_segments_odom.png}"
MIN_OBSERVATIONS="${MIN_OBSERVATIONS:-20}"
SEGMENT_FRAME="${SEGMENT_FRAME:-auto}"
MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/mplconfig}"

mkdir -p "${MPLCONFIGDIR}"
export MPLCONFIGDIR

exec python3 "$(dirname "$0")/plot_sgraphs_wall_segments.py" \
  --csv "${INPUT_CSV}" \
  --output "${OUTPUT_PNG}" \
  --min-observations "${MIN_OBSERVATIONS}" \
  --segment-frame "${SEGMENT_FRAME}"
