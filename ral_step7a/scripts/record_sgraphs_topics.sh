#!/usr/bin/env bash
set -euo pipefail

# Record S-Graphs comparison topics from inside the Humble Docker container.
# This avoids host-side Jazzy/Humble message-type issues for
# situational_graphs_msgs/msg/PlanesData.

CONTAINER_NAME="${CONTAINER_NAME:-sgraphs_step7a}"
RUN_ID="${RUN_ID:-spot_dinamicaStaticV0_sgraphs_step7a_$(date +%Y%m%d_%H%M%S)}"
STEP7A_ROOT="${STEP7A_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
OUTPUT_ROOT="${OUTPUT_ROOT:-${STEP7A_ROOT}/runs}"
CONTAINER_OUTPUT_ROOT="${CONTAINER_OUTPUT_ROOT:-${OUTPUT_ROOT}}"

mkdir -p "${OUTPUT_ROOT}"
chmod a+rwX "${OUTPUT_ROOT}"

echo "Recording S-Graphs topics"
echo "  container: ${CONTAINER_NAME}"
echo "  run_id:    ${RUN_ID}"
echo "  output:    ${OUTPUT_ROOT}/${RUN_ID}/sgraphs_topics"

exec docker exec -it "${CONTAINER_NAME}" bash -lc "
  source /opt/ros/humble/setup.bash
  source /workspace/install/setup.bash
  umask 000
  mkdir -p '${CONTAINER_OUTPUT_ROOT}/${RUN_ID}'
  ros2 bag record \
    /s_graphs/all_map_planes \
    /s_graphs/map_planes \
    /s_graphs/graph_keyframes \
    /s_graphs/markers \
    /s_graphs/odom2map \
    /s_graphs/odom_pose_corrected \
    /s_graphs/odom_path_corrected \
    /tf \
    /tf_static \
    -o '${CONTAINER_OUTPUT_ROOT}/${RUN_ID}/sgraphs_topics'
"
