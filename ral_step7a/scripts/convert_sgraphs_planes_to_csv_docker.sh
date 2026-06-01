#!/usr/bin/env bash
set -euo pipefail

# Run the S-Graphs plane CSV converter inside the official Humble Docker image.

IMAGE="${IMAGE:-sntarg/s_graphs:latest}"
RUN_ID="${RUN_ID:-spot_dinamicaStaticV0_sgraphs_step7a_old_002}"
STEP7A_ROOT="${STEP7A_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
OUTPUT_ROOT="${OUTPUT_ROOT:-${STEP7A_ROOT}/runs}"
SCRIPT_ROOT="${SCRIPT_ROOT:-${STEP7A_ROOT}}"
BAG_DIR="${BAG_DIR:-${OUTPUT_ROOT}/${RUN_ID}/sgraphs_topics}"
OUTPUT_CSV="${OUTPUT_CSV:-${OUTPUT_ROOT}/${RUN_ID}/sgraphs_wall_planes.csv}"

mkdir -p "${OUTPUT_ROOT}/${RUN_ID}"
chmod a+rwX "${OUTPUT_ROOT}" "${OUTPUT_ROOT}/${RUN_ID}"

exec docker run --rm \
  -v "${OUTPUT_ROOT}:${OUTPUT_ROOT}:rw" \
  -v "${SCRIPT_ROOT}:/ral_step7a:ro" \
  "${IMAGE}" \
  bash -lc "
    source /opt/ros/humble/setup.bash
    source /workspace/install/setup.bash
    umask 000
    python3 /ral_step7a/scripts/convert_sgraphs_planes_to_csv.py \
      --bag '${BAG_DIR}' \
      --output '${OUTPUT_CSV}'
  "
