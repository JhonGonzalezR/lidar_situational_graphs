#!/usr/bin/env bash
set -euo pipefail

# Generate quick-look diagnostic plots from the S-Graphs wall-plane CSV.

RUN_ID="${RUN_ID:-spot_dinamicaStaticV0_sgraphs_step7a_old_002}"
STEP7A_ROOT="${STEP7A_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
OUTPUT_ROOT="${OUTPUT_ROOT:-${STEP7A_ROOT}/runs}"
INPUT_CSV="${INPUT_CSV:-${OUTPUT_ROOT}/${RUN_ID}/sgraphs_wall_planes.csv}"
PLOT_DIR="${PLOT_DIR:-${OUTPUT_ROOT}/${RUN_ID}/plots}"
MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/mplconfig}"

mkdir -p "${MPLCONFIGDIR}"
export MPLCONFIGDIR

exec python3 "$(dirname "$0")/plot_sgraphs_wall_planes.py" \
  --csv "${INPUT_CSV}" \
  --output-dir "${PLOT_DIR}"
