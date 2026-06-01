#!/usr/bin/env bash
set -euo pipefail

# Record visual S-Graphs topics for RViz replay. This is heavier than
# record_sgraphs_topics.sh because it includes PointCloud2 topics.

CONTAINER_NAME="${CONTAINER_NAME:-sgraphs_step7a}"
RUN_ID="${RUN_ID:-spot_dinamicaStaticV0_sgraphs_step7a_old_visual_001}"
OUTPUT_ROOT="${OUTPUT_ROOT:-/tmp/ral_step7a_sgraphs_runs}"
CONTAINER_OUTPUT_ROOT="${CONTAINER_OUTPUT_ROOT:-/tmp/ral_step7a_sgraphs_runs}"

mkdir -p "${OUTPUT_ROOT}"

echo "Recording S-Graphs visual topics"
echo "  container: ${CONTAINER_NAME}"
echo "  run_id:    ${RUN_ID}"
echo "  output:    ${OUTPUT_ROOT}/${RUN_ID}/sgraphs_visual_topics"

exec docker exec -it "${CONTAINER_NAME}" bash -lc "
  source /opt/ros/humble/setup.bash
  source /workspace/install/setup.bash
  mkdir -p '${CONTAINER_OUTPUT_ROOT}/${RUN_ID}'
  ros2 bag record \
    /s_graphs/markers \
    /s_graphs/map_points \
    /s_graphs/wall_points \
    /s_graphs/lidar_points \
    /filtered_points \
    /s_graphs/odom2map \
    /s_graphs/odom_pose_corrected \
    /s_graphs/odom_path_corrected \
    /tf \
    /tf_static \
    -o '${CONTAINER_OUTPUT_ROOT}/${RUN_ID}/sgraphs_visual_topics'
"
