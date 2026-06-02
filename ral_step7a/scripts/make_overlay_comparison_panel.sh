#!/usr/bin/env bash
set -euo pipefail

STEP7A_ROOT="${STEP7A_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
SGRAPHS_RUN_ID="${SGRAPHS_RUN_ID:-spot_dinamicaStaticV0_sgraphs_standard_optimized_old_002}"
INGRAPH_RUN_ID="${INGRAPH_RUN_ID:-ingraph_20260601_195923}"
LEFT_PNG="${LEFT_PNG:-${STEP7A_ROOT}/runs/${SGRAPHS_RUN_ID}/plots/sgraphs_lidar_wall_overlay_odom.png}"
RIGHT_PNG="${RIGHT_PNG:-${STEP7A_ROOT}/runs/${INGRAPH_RUN_ID}/plots/ingraph_lidar_overlay_ever_strong_wall_only.png}"
OUTPUT_PNG="${OUTPUT_PNG:-${STEP7A_ROOT}/runs/${INGRAPH_RUN_ID}/plots/step7a_sgraphs_vs_ingraph_ever_strong_overlay_panel.png}"
MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/mplconfig}"

mkdir -p "$(dirname "${OUTPUT_PNG}")" "${MPLCONFIGDIR}"
export MPLCONFIGDIR

exec python3 "$(dirname "$0")/make_overlay_comparison_panel.py" \
  --left "${LEFT_PNG}" \
  --right "${RIGHT_PNG}" \
  --output "${OUTPUT_PNG}" \
  --left-title "" \
  --right-title "" \
  --title "Step 7A frontend overlay comparison on spot/dinamicaStaticV0"
