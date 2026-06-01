#!/usr/bin/env bash
set -euo pipefail

# Replay a recorded S-Graphs visual bag from inside the Humble Docker image.

IMAGE="${IMAGE:-sntarg/s_graphs:latest}"
RUN_ID="${RUN_ID:-spot_dinamicaStaticV0_sgraphs_step7a_old_visual_001}"
OUTPUT_ROOT="${OUTPUT_ROOT:-/tmp/ral_step7a_sgraphs_runs}"
BAG_DIR="${BAG_DIR:-${OUTPUT_ROOT}/${RUN_ID}/sgraphs_visual_topics}"
RATE="${RATE:-1.0}"

exec docker run --rm -it --net=host \
  -v "${OUTPUT_ROOT}:${OUTPUT_ROOT}:ro" \
  "${IMAGE}" \
  bash -lc "
    source /opt/ros/humble/setup.bash
    source /workspace/install/setup.bash
    ros2 bag play '${BAG_DIR}' --clock --rate '${RATE}'
  "
