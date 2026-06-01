#!/usr/bin/env bash
set -euo pipefail

# Summarize S-Graphs wall-plane observations by persistent plane ID.

RUN_ID="${RUN_ID:-spot_dinamicaStaticV0_sgraphs_step7a_old_002}"
STEP7A_ROOT="${STEP7A_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
OUTPUT_ROOT="${OUTPUT_ROOT:-${STEP7A_ROOT}/runs}"
INPUT_CSV="${INPUT_CSV:-${OUTPUT_ROOT}/${RUN_ID}/sgraphs_wall_planes.csv}"
OUTPUT_CSV="${OUTPUT_CSV:-${OUTPUT_ROOT}/${RUN_ID}/sgraphs_wall_plane_summary.csv}"

exec python3 "$(dirname "$0")/summarize_sgraphs_wall_planes.py" \
  --csv "${INPUT_CSV}" \
  --output "${OUTPUT_CSV}"
